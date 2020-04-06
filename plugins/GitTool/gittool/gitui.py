from noval.python.project.viewer import *
import os
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from noval import _
import noval.util.utils as utils
import noval.project.wizard as projectwizard
import threading
import noval.outputthread as outputthread
import subprocess
import noval.ui_base as ui_base
import noval.util.compat as compat
import copy
from pkg_resources import resource_filename
import noval.ttkwidgets.checklistbox as checklistbox
import shutil
import noval.project.importfiles as importfiles
import noval.util.strutils as strutils

def GetAskPassPath():
    path = resource_filename(__name__,'')
    if utils.is_windows():
        ask_pass_path = os.path.join(path,"askpass/dist/askpass.exe")
    else:
        ask_pass_path = os.path.join(path,"askpass/askpass.py")
    return ask_pass_path

def SetVariablevar(prefix,variable):
    path = filedialog.askdirectory()
    if path:
        path = fileutils.opj(path)
        variable.set(prefix + path)

class CloneProgressDialog(ui_base.GenericProgressDialog):
    def __init__(self,parent):
        ui_base.GenericProgressDialog.__init__(self,parent,_("Clone project"),
                               mode="indeterminate",info=_("Please wait a minute for end clone...")
                                )
        self.KeepGoing = True
        
    def AppendMsg(self,msg):
        print (msg,'=================')
        if utils.is_py3_plus():
            msg = compat.ensure_string(msg)
        if not msg:
            return
        for message in msg.split('\r'):
            self.label_var.set(message.strip())

    def Pulse(self):
        self.mpb.start()
        
    def Cancel(self):
        self.mpb.stop()
        ui_base.GenericProgressDialog.Cancel(self)
        



class OutputReader:
    branch_flag = 0
    Repositoryes = {}
    CURRENT_REPOSITORY = None
    def __init__(self):
        self.last_msg = ''
    def Read(self,msg):
        if utils.is_py3_plus():
            msg = compat.ensure_string(msg)
       # print (msg,"-------------------")
        if not msg:
            return
        self.last_msg = msg
        default_branch_flag = 'HEAD branch:'
        head_zn_flag = 'HEAD 分支：'
        if msg.find(default_branch_flag) != -1:
            default_branch = msg.replace(default_branch_flag,"").strip()
            OutputReader.Repositoryes[OutputReader.CURRENT_REPOSITORY]['default_branch'] = default_branch
            print ('default branch is',default_branch)
            
        elif msg.find(head_zn_flag) != -1:
            default_branch = msg.replace(head_zn_flag,"").strip()
            OutputReader.Repositoryes[OutputReader.CURRENT_REPOSITORY]['default_branch'] = default_branch
            print ('default branch is',default_branch)
            
        elif msg.find('Remote branches:') != -1 or msg.find('Remote branch:') != -1 or msg.find('远程分支：') != -1:
            OutputReader.branch_flag = 1
        elif OutputReader.branch_flag:
            branch_name = msg.split()[0].strip()
            print ('branch is',branch_name)
            OutputReader.Repositoryes[OutputReader.CURRENT_REPOSITORY]['branches'].append(branch_name)

class GitProjectNameLocationPage(BasePythonProjectNameLocationPage):

    def __init__(self,master,**kwargs):
        BasePythonProjectNameLocationPage.__init__(self,master,**kwargs)
        self.can_finish = False
        
    def SaveProject(self,path):
        return True
        
    def SaveGitProject(self,path):
        return BasePythonProjectNameLocationPage.SaveProject(self,path)

class LocationSelectionPage(projectwizard.BitmapTitledContainerWizardPage):
    def __init__(self,master):
        projectwizard.BitmapTitledContainerWizardPage.__init__(self,master,_("Import codes from Git Server"),_("Select Repository Source\nSelect a location of the source repository."),"python_logo.png")
        self.can_finish = False
        
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        #设置path列存储模板路径,并隐藏改列 
        treeview = treeviewframe.TreeViewFrame(sizer_frame,show_scrollbar=False,borderwidth=1,relief="solid")
        self.tree = treeview.tree
        treeview.pack(side=tk.LEFT,fill="both",expand=1)
        path = resource_filename(__name__,'')
        clone_local_img_path = os.path.join(path,"res","repository_rep.gif")
        clone_uri_img_path = os.path.join(path,"res","editconfig.png")
        self.clone_local_img = GetApp().GetImage(clone_local_img_path)
        self.clone_uri_img = GetApp().GetImage(clone_uri_img_path)
        #鼠标双击Tree控件事件
        self.tree.bind("<Double-Button-1>", self.on_double_click, "+")
        item1 = self.tree.insert('', "end", text=_("Existing local repository"),image=self.clone_local_img,values=("file",))
        item2 = self.tree.insert('', "end", text=_("Clone URI"),image=self.clone_uri_img,values=("uri",))
        self.tree.selection_set(item1)
        
    def on_double_click(self,event):
        self.master.master.GotoNextPage()

class RepositorySourcePage(projectwizard.BitmapTitledContainerWizardPage):
    def __init__(self,master):
        projectwizard.BitmapTitledContainerWizardPage.__init__(self,master,_("Import codes from Git Server"),_("Source Git Repository\nEnter the location of the source repository."),"python_logo.png")
        self.can_finish = False

    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        
        sizer_frame.columnconfigure(1, weight=1)

        ttk.Label(sizer_frame,text=_('Repository addr:')).grid(column=0, row=0, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.addr_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.addr_var)
        name_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.addr_var.trace("w", self.ParseURL)
        ttk.Button(sizer_frame, text= _("Local File..."),command=self.OpenLocal).grid(column=2, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))

        ttk.Label(sizer_frame,text=_('Protocol:')).grid(column=0, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        protocols = ('git','http','https','ssh','file')
        self.protocol_var = tk.StringVar(value=protocols[0])
        protocol_combox = ttk.Combobox(sizer_frame,textvariable=self.protocol_var,values=protocols,state="readonly")
        protocol_combox.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        protocol_combox.bind("<<ComboboxSelected>>",self.SelectProtocol)

        ttk.Label(sizer_frame,text=_('Username:')).grid(column=0, row=2, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(sizer_frame,textvariable=self.name_var)
        self.name_entry.grid(column=1, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        ttk.Label(sizer_frame,text=_('Password:')).grid(column=0, row=3, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(sizer_frame,textvariable=self.password_var,show='*')
        self.password_entry.grid(column=1, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        self.store_secure_var = tk.BooleanVar(value=False)
        self.store_secure_btn = ttk.Checkbutton(sizer_frame,text=_('Store in Secure Store'),variable=self.store_secure_var)
        self.store_secure_btn.grid(column=0, row=4, sticky="nsew",columnspan=2,pady=consts.DEFAUT_CONTRL_PAD_Y)
        
        return sizer_frame
        
    def ParseURL(self,*args):
        addr = self.addr_var.get().strip()
        if addr.startswith("file://"):
            self.protocol_var.set("file")
            self.UpdateUI("file")
        elif addr.startswith("https://"):
            self.protocol_var.set("https")
            self.UpdateUI("https")
        elif addr.startswith("git@"):
            self.protocol_var.set("ssh")
            self.UpdateUI("ssh")
            
    def SelectProtocol(self,event):
        self.UpdateUI(self.protocol_var.get())
            
    def UpdateUI(self,protocol):
        if protocol == "file":
            self.name_entry['state'] = tk.DISABLED
            self.password_entry['state'] = tk.DISABLED
            self.store_secure_btn['state'] = tk.DISABLED
        else:
            self.name_entry['state'] = tk.NORMAL
            self.password_entry['state'] = tk.NORMAL
            self.store_secure_btn['state'] = tk.NORMAL
        
    def OpenLocal(self):
        SetVariablevar("file://",self.addr_var)
        
    def Validate(self):
        if self.addr_var.get().strip() == "":
            messagebox.showinfo(GetApp().GetAppName(),_("The repository addr could not be empty!"))
            return False
        if self.store_secure_var.get():
            if utils.is_windows():
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            else:
                startupinfo = None
            subprocess.Popen("git config --global credential.helper store",shell=True,startupinfo=startupinfo)
        self.GetGitBraches()
        return True
        
    def Init(self):
        items = self.GetPrev().tree.selection()
        if items:
            value = self.GetPrev().tree.item(items[0])["values"][0]
            self.UpdateUI(value)
            if value == "file":
                self.protocol_var.set(value)
            else:
                self.protocol_var.set("git")
        
    def ExecCommandAndOutput(self,command,progress_dlg,env=None):
        #shell must be True on linux
        project_path = self.GetAndEnsureProjectPath()
        print ('git cmd is %s'%command)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=project_path,env=env)
        stdout_thread = outputthread.SynchronizeOutputThread(p.stdout,p,progress_dlg)
        stdout_thread.start()
        stderr_thread = outputthread.SynchronizeOutputThread(p.stderr,p,progress_dlg)
        stderr_thread.start()
        p.wait()
        return p.returncode
        
    def GetAddr(self):
        raw_addr = self.addr_var.get().strip()
        name = self.name_var.get().strip()
        if self.protocol_var.get() == "https":
            if name != "":
                r_addr = raw_addr.replace( "https://","")
                addr = "https://" + "%s:%s@"%(name,self.password_var.get().strip()) + r_addr
                return addr
        return raw_addr
        
    def GetAndEnsureProjectPath(self):
        project_path = self.GetPrev().GetPrev().GetProjectLocation()
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        return project_path

    def GetGitBraches(self):
        OutputReader.CURRENT_REPOSITORY = self.addr_var.get().strip()
        if OutputReader.CURRENT_REPOSITORY in OutputReader.Repositoryes and len(OutputReader.Repositoryes[OutputReader.CURRENT_REPOSITORY]['branches']) >0:
            return
        project_path = self.GetAndEnsureProjectPath()
        command = "git init"
        utils.create_process(command,'',cwd=project_path)
        git_dir = os.path.join(project_path,".git")
        if os.path.exists(git_dir):
            shutil.rmtree(git_dir)
        command = "git remote add origin %s"%self.GetAddr()
        utils.create_process(command,'',cwd=project_path)
        command = "git remote show origin"
        env = copy.copy(os.environ)
        ask_pass_path = GetAskPassPath()
        env.update(dict(GIT_ASKPASS=ask_pass_path))
        reader = OutputReader()
        reader.call_back = reader.Read
        OutputReader.branch_flag = 0
        OutputReader.Repositoryes[OutputReader.CURRENT_REPOSITORY] = {}
        OutputReader.Repositoryes[OutputReader.CURRENT_REPOSITORY]['branches'] = []
        ret_code = self.ExecCommandAndOutput(command,reader,env=env)
        if ret_code != 0:
            messagebox.showerror(_("Error"),_("%s")%reader.last_msg,parent=self)
        try:
            shutil.rmtree(git_dir)
        except:
            pass

class BranchSelectionPage(projectwizard.BitmapTitledContainerWizardPage):
    def __init__(self,master):
        projectwizard.BitmapTitledContainerWizardPage.__init__(self,master,_("Import codes from Git Server"),_("Branch Selection\nSelect branches to clone from the remote repository."),"python_logo.png")
        self.can_finish = False

    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        #设置path列存储模板路径,并隐藏改列 
        check_listbox_view = treeviewframe.TreeViewFrame(sizer_frame,treeview_class=checklistbox.CheckListbox,borderwidth=1,relief="solid",height=4)
        self.listbox = check_listbox_view.tree
        check_listbox_view.pack(side=tk.LEFT,fill="both",expand=1)
        path = resource_filename(__name__,'')
        branch_img_path = os.path.join(path,"res","branches_obj.png")
        self.branch_img = GetApp().GetImage(branch_img_path)
            
    def Init(self):
        self.listbox.Clear()
        for branch in OutputReader.Repositoryes[OutputReader.CURRENT_REPOSITORY]['branches']:
            self.listbox.Append(branch)
            
    def Validate(self):
        self.branches = self.GetBranches()
        if 0 == len(self.branches):
            messagebox.showinfo(GetApp().GetAppName(),_("You must select at least one branch!"),parent=self)
            return False
        return True
        
    def GetBranches(self):
        branches = []
        for index in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(index):
                branches.append(self.listbox.GetString(index))
        return branches

class LocalDestinationPage(projectwizard.BitmapTitledContainerWizardPage):
    def __init__(self,master):
        projectwizard.BitmapTitledContainerWizardPage.__init__(self,master,_("Import codes from Git Server"),_("Local Destination\nConfigure the local storage location for project."),"python_logo.png")
        self.can_finish = False
        
    def CreateContent(self,content_frame,**kwargs):
        sbox = ttk.LabelFrame(content_frame, text=_("Destination:"))
        
        frame = ttk.Frame(sbox)
        ttk.Label(frame, text=_('Directory:')).pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.dest_path_var = tk.StringVar()
        dest_path_entry = ttk.Entry(frame,textvariable=self.dest_path_var)
        dest_path_entry.pack(side=tk.LEFT,fill="x",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        dest_default_btn = ttk.Button(frame, text= _("Browse..."),command=self.SetDestPath)
        dest_default_btn.pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        frame.pack(fill="x")
        
        frame = ttk.Frame(sbox)
        ttk.Label(frame,text=_('Initial branch:')).pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.branch_var = tk.StringVar()
        self.branch_entry = ttk.Combobox(frame,textvariable=self.branch_var,values=[],state="readonly")
        self.branch_entry.pack(side=tk.LEFT,fill="x",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        frame.pack(fill="x")
        
        frame = ttk.Frame(sbox)
        self.clone_submodules_var = tk.BooleanVar(value=False)
        clone_submodules_btn = ttk.Checkbutton(frame,text=_('Clone submodules'),variable=self.clone_submodules_var)
        clone_submodules_btn.pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        frame.pack(fill="x")
        
        sbox.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
    def Init(self):
        self.dest_path_var.set(self.GetPrev().GetPrev().GetAndEnsureProjectPath())
        self.branch_entry['values'] = self.GetPrev().GetBranches()
        self.branch_var.set(OutputReader.Repositoryes[OutputReader.CURRENT_REPOSITORY]['default_branch'])
        
    def SetDestPath(self):
        SetVariablevar("",self.dest_path_var)
        
    def CloneProject(self,progress_dlg):
        progress_dlg.call_back = progress_dlg.AppendMsg
        command = "git clone --progress %s"%self.GetPrev().GetPrev().GetAddr()
        ret_code = self.GetPrev().GetPrev().ExecCommandAndOutput(command,progress_dlg)
        msg = progress_dlg.label_var.get()
        progress_dlg.destroy()
        if ret_code != 0:
            messagebox.showerror(_("Clone project error"),_("%s")%msg,parent=self)
            
    def Validate(self):
        progress_dlg = CloneProgressDialog(self)
        self.CloneGitProject(progress_dlg)
        progress_dlg.Pulse()
        progress_dlg.ShowModal()
        return True

    def CloneGitProject(self,progress_dlg):
        t = threading.Thread(target=self.CloneProject,args=(progress_dlg,))
        t.start()

class ImportGitfilesPage(importfiles.ImportfilesPage):
    def __init__(self,master):
        importfiles.ImportfilesPage.__init__(self,master)
        self.can_finish = True
        self.rejects += [consts.PROJECT_SHORT_EXTENSION]
        
    def Init(self):
        dest_path = os.path.join(self.GetPrev().dest_path_var.get(),strutils.get_filename_without_ext(self.GetPrev().GetPrev().GetPrev().addr_var.get().strip()))
        self.dir_entry_var.set(dest_path)
        
    def Finish(self):
        project_name_page = self.GetPrev().GetPrev().GetPrev().GetPrev().GetPrev()
        projName = project_name_page.name_var.get().strip()
        project_path = self.GetProjectPath()
        fullProjectPath = os.path.join(project_path, strutils.MakeNameEndInExtension(projName, consts.PROJECT_EXTENSION))
        if not project_name_page.SaveGitProject(fullProjectPath):
            return False
        return importfiles.ImportfilesPage.Finish(self)
        
    def GetProjectPath(self):
        project_name_page = self.GetPrev().GetPrev().GetPrev().GetPrev().GetPrev()
        project_path = project_name_page.GetProjectLocation()
        return os.path.join(project_path,strutils.get_filename_without_ext(self.GetPrev().GetPrev().GetPrev().addr_var.get().strip()))
