from noval import _,GetApp,NewId
import os
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from noval.project.templatemanager import ProjectTemplateManager
import gittool.gitui as gitui
import noval.consts as consts
import noval.menu as tkmenu
import subprocess
import noval.util.strutils as strutils
from tkinter import messagebox
import noval.ui_base as ui_base
import noval.ttkwidgets.checklistbox as checklistbox
import noval.ttkwidgets.treeviewframe as treeviewframe
import tkinter as tk
import noval.editor.text as texteditor
import noval.ttkwidgets.textframe as textframe
from tkinter import ttk,messagebox
import copy

class RepositoryAddrDialog(ui_base.CommonModaldialog):
    def __init__(self,master,face_ui):
        ui_base.CommonModaldialog.__init__(self,master)
        self.title(_('Set repository remote addr'))
        self.ui = face_ui
        row = ttk.Frame(self.main_frame)
        row.columnconfigure(1,weight=1)
        ttk.Label(row,text=_('Repository addr:')).grid(column=0, row=0, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.addr_var = tk.StringVar(value=self.GetRepositoryAddr())
        name_entry = ttk.Entry(row,textvariable=self.addr_var)
        name_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        row.pack(fill="x",expand=1)
        self.AddokcancelButton()
        
    def GetRepositoryAddr(self):
        output = utils.GetCommandOutput("git remote -v",cwd=self.ui.GetProjectDocument().GetPath())
        addr = ''
        for line in output.splitlines():
            if line.find('(push)') != -1:
                addr = line.replace('(push)',"").replace('origin',"").strip()
        return addr
        
    def _ok(self,event=None):
        if self.addr_var.get().strip() == "":
            messagebox.showinfo(self,_('Please set repository addr'))
            return       
        command = "git remote add origin %s"%(self.addr_var.get())
        self.ui.CallGitProcess(command)
        ui_base.CommonModaldialog._ok(self,event)

class GitConfigurationDialog(ui_base.CommonModaldialog):
    def __init__(self,master,face_ui):
        ui_base.CommonModaldialog.__init__(self,master)
        self.ui = face_ui
        self.title(_('Git Global Configuration'))
        sizer_frame = ttk.Frame(self.main_frame)
        sizer_frame.pack(fill="both",expand=1)
        sizer_frame.columnconfigure(1,weight=1)
        configs = {}
        self.GetConfigs(configs)
        ttk.Label(sizer_frame,text=_('User name:')).grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        self.user_name_var = tk.StringVar(value=configs['user_name'])
        user_name_entry = ttk.Entry(sizer_frame,textvariable=self.user_name_var)
        user_name_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=consts.DEFAUT_CONTRL_PAD_X)
        ttk.Label(sizer_frame,text=_('User email:')).grid(column=0, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        self.user_email_var = tk.StringVar(value=configs['user_email'])
        user_email_entry = ttk.Entry(sizer_frame,textvariable=self.user_email_var)
        user_email_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=consts.DEFAUT_CONTRL_PAD_X)
        self.AddokcancelButton()
        
        self.quote_path_var = tk.BooleanVar(value=configs.get('quotepath',True))
        ttk.Checkbutton(sizer_frame,text=("Use Quote Path"),variable=self.quote_path_var).grid(column=0, row=2, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        self.golbal_chk_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sizer_frame,text=("Apply to global domain"),variable=self.golbal_chk_var).grid(column=0, row=3, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        
    def _ok(self,event=None):
        if self.user_name_var.get().strip() == "":
            messagebox.showinfo(self,_('Please set git user name'))
            return
        if self.user_email_var.get().strip() == "":
            messagebox.showinfo(self,_('Please set git user email'))
            return
        command = "git config "
        if self.golbal_chk_var.get():
            command += "--global "
        command += "user.name \"%s\""%self.user_name_var.get()
        self.ui.CallGitProcess(command)
        
        command = "git config "
        if self.golbal_chk_var.get():
            command += "--global "
        command += "user.email \"%s\""%self.user_email_var.get()
        self.ui.CallGitProcess(command)
        
        if self.quote_path_var.get():
            quote_path = "true"
        else:
            quote_path = "false"
        self.ui.CallGitProcess('git config --global core.quotepath %s'%quote_path)
        ui_base.CommonModaldialog._ok(self,event)
        
    def GetConfigs(self,configs = {}):
        output = utils.GetCommandOutput("git config -l")
        for line in output.splitlines():
            if line.find('user.name') != -1:
                user_name = line.replace('user.name=',"").strip()
                configs['user_name'] = user_name
            elif line.find('user.email') != -1:
                user_email = line.replace('user.email=',"").strip()
                configs['user_email'] = user_email
            elif line.find('core.quotepath') != -1:
                quotepath = line.replace('core.quotepath=',"").strip()
                configs['quotepath'] = True if quotepath=="true" else False
        
class CommitDialog(ui_base.CommonModaldialog):
    def __init__(self,master,branch,content,single_file=False,commit=True):
        ui_base.CommonModaldialog.__init__(self,master,width=1000)
        if commit:
            self.title(_('Commit-[%s]'%branch))
        else:
            self.title(_('Checkout-[%s]'%branch))
        commit_file_label = ttk.Label(self.main_frame)
        commit_file_label.pack(fill="x")
        check_listbox_view = treeviewframe.TreeViewFrame(self.main_frame,treeview_class=checklistbox.CheckListbox,borderwidth=1,relief="solid",height=10)
        self.listbox = check_listbox_view.tree
        check_listbox_view.pack(fill="x",expand=1)
        
        sizer_frame = ttk.Frame(self.main_frame)
        sizer_frame.pack(fill="x",expand=1)
        select_all_btn = ttk.Button(
            sizer_frame, text=_("Select All"), command=self.SelectAll
        )
        select_all_btn.grid(column=0, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        unselect_all_btn = ttk.Button(
            sizer_frame, text=_("UnSelect All"), command=self.UnselectAll
        )
        unselect_all_btn.grid(column=1, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        modify_flag = 'modified:'
        delete_flag = 'deleted:'
        unstaged_file = False
        self.is_commit = commit

        commit_file_count = 0
        unstaged_file_count = 0
        encoding = utils.get_default_encoding()
        if not single_file:
            for line in content.splitlines():
                try:
                    line = line.encode(encoding,'ignore').decode('utf-8')
                except:
                    line = line
                if line.find(modify_flag) != -1:
                    i = self.listbox.Append(line.replace(modify_flag,"").strip())
                    self.listbox.Check(i)
                    commit_file_count += 1
                elif line.find(delete_flag) != -1:
                    i = self.listbox.Append(line.replace(delete_flag,"").strip())
                    self.listbox.Check(i)
                    commit_file_count += 1
                elif line.find('Untracked files:') != -1:
                    unstaged_file = True
                elif unstaged_file and line.find('git add <file>...') == -1 and line.find('no changes added to commit') == -1 and line.find('nothing added to commit') == -1 and commit:
                    if line.strip():
                        self.listbox.Append(line.strip())
                        unstaged_file_count += 1
        else:
            i = self.listbox.Append(content)
            self.listbox.Check(i)
            commit_file_count += 1
        
        if self.is_commit:
            commit_file_label.configure(text=_('Commit files %d,Unstaged files %d')%(commit_file_count,unstaged_file_count))
            ttk.Label(self.main_frame,text=_('Commit message')).pack(fill="x")
            text_frame = textframe.TextFrame(self.main_frame,borderwidth=1,relief="solid",text_class=texteditor.TextCtrl,height=12)
            text_frame.pack(fill="x",expand=1)
            self.text = text_frame.text
            ttk.Button(self.main_frame, text=_("Commit and Push"), command=self.CommitAndPush).pack(side=tk.LEFT)
            self.AddokcancelButton(side=tk.LEFT)
            self.ok_button.configure(text=_('Commit'),default="active")
        else:
            commit_file_label.configure(text=_('Commit files %d')%(commit_file_count))
            self.AddokcancelButton()
            self.ok_button.configure(text=_('Checkout'),default="active")
            
        self.files = []
        self.msg = ''
        self.push = False
        
    def SelectAll(self):
        self.CheckListbox(True)
        
    def CheckListbox(self,check=True):
        for i in range(self.listbox.GetCount()):
            self.listbox.Check(i,check)
        
    def UnselectAll(self):
        self.CheckListbox(False)
        
    def CommitAndPush(self):
        self.push = True
        self._ok()
        
    def GetFiles(self):
        files = []
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
               files.append(self.listbox.GetString(i))
        return files
       
    def _ok(self,event=None):
        self.files = self.GetFiles()
        if 0 == len(self.files):
            messagebox.showinfo(self,_('Please select at least one file'))
            return
        if self.is_commit:
            self.msg = self.text.GetValue()
            if self.msg.strip() == '':
                messagebox.showinfo(self,_('commit message could not be empty'))
                return
        ui_base.CommonModaldialog._ok(self,event)
       
class GitToolPlugin(plugin.Plugin):
    """plugin description here..."""
    plugin.Implements(iface.MainWindowI)
    
    MAX_COMMAND_LINE_LENGTH = 10000
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing GitTool plugin")
        
        ProjectTemplateManager().AddProjectTemplate("General",_("New Project From Git Server"),[(gitui.GitProjectNameLocationPage,{'project_dir_checked':False,'enable_create_project_dir':False}),gitui.LocationSelectionPage,gitui.RepositorySourcePage,\
                                                        gitui.BranchSelectionPage,gitui.LocalDestinationPage,gitui.ImportGitfilesPage]) 
        GetApp().bind(constants.PROJECTVIEW_POPUP_FILE_MENU_EVT, self.AppenFileMenu,True)
        GetApp().bind(constants.PROJECTVIEW_POPUP_ROOT_MENU_EVT, self.AppenRootMenu,True)
        self.project_browser = GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME)
        GetApp().AddMessageCatalog('gittool', __name__)
        self.current_branch = None

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """
        return "1.2.2"

    def InstallHook(self):
        """Override in subclasses to allow the plugin to be loaded
        dynamically.
        @return: None

        """
        pass

    def UninstallHook(self):
        pass

    def EnableHook(self):
        pass
        
    def DisableHook(self):
        pass
        
    def GetFree(self):
        return True
        
    def GetPrice(self):
        pass
        
    def MatchPlatform(self):
        '''
            这里插件需要区分windows版本和linux版本
            windows版本把adkpass.exe包需要打包进去
            linux版本把可执行脚本adkpass.py包需要打包进去
        '''
        return True
    
    def AppenRootMenu(self, event):
        self.current_branch = self.GetBranch()
        print ('current branch is ',self.current_branch)
        menu = event.get('menu')
        submenu = tkmenu.PopupMenu()
        menu.AppendMenu(NewId(),_("Version Control"),submenu)
        if self.current_branch is None:
            submenu.Append(NewId(),_("Init"),handler=self.Init) 
        else:
            submenu.Append(NewId(),_("Checkout files"),handler=self.CheckoutCommitFiles) 
            submenu.Append(NewId(),_("Ignore files"),handler=self.AddIgnoreFiles)
            
            submenu.Append(NewId(),_("Pull"),handler=self.Pull)
            submenu.Append(NewId(),_("Commit"),handler=self.Commit)
            submenu.Append(NewId(),_("Push"),handler=self.Push)
            
            branch_menu = tkmenu.PopupMenu()
            submenu.AppendMenu(NewId(),_("Branch"),branch_menu)
            branch_menu.Append(NewId(),_("Checkout branch"),handler=self.CheckoutBranch)
            branch_menu.Append(NewId(),_("New branch"),handler=self.NewBranch)
            branch_menu.Append(NewId(),_("Delete branch"),handler=self.NewBranch)
            
            remote_menu = tkmenu.PopupMenu()
            submenu.AppendMenu(NewId(),_("Remote"),remote_menu)
            remote_menu.Append(NewId(),_("Set Remote Url"),handler=self.SetRemoteUrl)
            submenu.Append(NewId(),_("Configuration"),handler=self.Configuration)
            
    def SetRemoteUrl(self):
        RepositoryAddrDialog(GetApp().MainFrame,self).ShowModal()
            
    def Configuration(self):
        GitConfigurationDialog(GetApp().MainFrame,self).ShowModal()
            
    def Init(self):
        command = "git init"
        error,output,returncode = self.CallGitProcess(command)
        
    def CheckoutBranch(self):
        pass
        
    def GetCommandOutput(self,command):
        output = utils.GetCommandOutput('git status',cwd=self.GetProjectDocument().GetPath())
        if output == '':
            output = utils.GetCommandOutput('git status',cwd=self.GetProjectDocument().GetPath(),encoding='utf-8')
        return output
        
    def CheckoutCommitFiles(self):
        output = self.GetCommandOutput('git status')
        dlg = CommitDialog(GetApp().MainFrame,self.current_branch,output,commit=False)
        if dlg.ShowModal() == constants.ID_CANCEL:
            return
        self.Checkoutfiles(dlg.files)
        
    def AddIgnoreFiles(self):
        pass
        
    def NewBranch(self):
        pass
        
    def Pull(self):
        command = "git pull"
        error,output,returncode = self.CallGitProcess(command)
        if returncode == 0:
            messagebox.showinfo(GetApp().GetAppName(),_('pull success'))
        else:
            messagebox.showinfo(_('Error'),_('pull fail:%s')%(error))
        
    def Push(self):
        error,output,returncode = self.CallGitProcess("git push origin %s"%self.current_branch,ask_pass=True)
        if returncode != 0:
            messagebox.showerror(_('Push fail'),error)
            return
        messagebox.showinfo(GetApp().GetAppName(),_('Push success'))
        
    def Commit(self):
        output = self.GetCommandOutput('git status')
        dlg = CommitDialog(GetApp().MainFrame,self.current_branch,output)
        if dlg.ShowModal() == constants.ID_CANCEL:
            return
        files = dlg.files
        command = 'git add'
        for commit_file in files:
            command += ' ' + commit_file
        error,output,returncode = self.CallGitProcess(command)
        if returncode != 0:
            messagebox.showerror(_('Commit fail'),error)
            return
            
        command = 'git commit -m %s'%dlg.msg
        error,output,returncode = self.CallGitProcess(command)
        if returncode != 0:
            messagebox.showerror(_('Commit fail'),error)
            return
        if dlg.push:
            self.Push()
        else:
            messagebox.showinfo(GetApp().GetAppName(),_('Commit success'))
        
    def AppenFileMenu(self, event):
        self.current_branch = self.GetBranch()
        menu = event.get('menu')
        tree_item = event.get('item')
        project_browser = self.GetProjectFrame()
        filePath = project_browser.GetView()._GetItemFilePath(tree_item)
        submenu = tkmenu.PopupMenu()
        menu.AppendMenu(NewId(),_("Version Control"),submenu)
        submenu.Append(NewId(),_("Commit"),handler=lambda:self.Commitfile(filePath)) 
        submenu.Append(NewId(),_("Checkout"),handler=lambda:self.Checkoutfile(filePath))
        submenu.Append(NewId(),_("Push"),handler=self.Pushfile)
        submenu.Append(NewId(),_("Add to ignore"),handler=self.AddIgnoreFile)
        submenu.Append(NewId(),_("Add"),handler=lambda:self.AddFile(filePath))
        submenu.Append(NewId(),_("Remove"),handler=lambda:self.RemoveFile(filePath))
        submenu.Append(NewId(),_("Delete"),handler=lambda:self.DeleteFile(filePath))

    def Checkoutfile(self,filepath):
        self.Checkoutfiles([filepath])
        
    def Checkoutfiles(self,files):
        ret = messagebox.askquestion(GetApp().GetAppName(),_('Checkout file will overwrite current file content,Are you sure to checkout?'))
        if not ret:
            return
        for filepath in files:
            error,output,returncode = self.CallGitProcess("git checkout %s"%strutils.emphasis_path(filepath))
        if returncode == 0:
            messagebox.showinfo(GetApp().GetAppName(),_('checkout success'))
        else:
            messagebox.showinfo(_('Error'),_('checkout fail:%s')%(error))
            
    def AddIgnoreFile(self):
        pass
        
    def AddFile(self,filePath):
        error,output,returncode = self.CallGitProcess("git add %s"%strutils.emphasis_path(filePath))
        if returncode == 0:
            messagebox.showinfo(GetApp().GetAppName(),_('add success'))
        else:
            messagebox.showinfo(_('Error'),_('add fail:%s')%(error))
        return returncode
        
    def RemoveFile(self,filePath):
        self.GetProjectDocument().GetFirstView().RemoveFromProject()
        
    def DeleteFile(self,filePath):
        error,output,returncode = self.CallGitProcess('git rm %s'%strutils.emphasis_path(filePath))
        if returncode == 0:
            messagebox.showinfo(GetApp().GetAppName(),_('delete success'))
        else:
            messagebox.showinfo(_('Error'),_('delete fail:%s')%(error))
            return
        self.RemoveFile(filePath)
        
    def Commitfile(self,filePath):
        dlg = CommitDialog(GetApp().MainFrame,self.current_branch,filePath,single_file=True)
        if dlg.ShowModal() == constants.ID_CANCEL:
            return
        returncode = self.AddFile(filePath)
        if returncode != 0:
            return
        command = 'git commit -m %s'%dlg.msg
        error,output,returncode = self.CallGitProcess(command)
        if returncode != 0:
            messagebox.showerror(_('Commit fail'),error)
            return
        else:
            messagebox.showinfo(GetApp().GetAppName(),_('commit success'))
        
    def Pushfile(self):
        self.Push()
        
    def CallGitProcess(self,command,ask_pass=False):
        utils.get_logger().debug('git command is %s,length is:%d',command,len(command))
        if len(command) >= self.MAX_COMMAND_LINE_LENGTH:
            return "command line length exceed limit....","",-1
        env = copy.copy(os.environ)
        if ask_pass:
            ask_pass_path = gitui.GetAskPassPath()
            env.update(dict(GIT_ASKPASS=ask_pass_path))
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,\
                            cwd=self.GetProjectDocument().GetPath(),env=env)
        error = str(p.stderr.read(),encoding = utils.get_default_encoding())
        try:
            output = str(p.stdout.read(),encoding = utils.get_default_encoding())
        except:
            output = str(p.stdout.read(),encoding = 'utf-8')
        p.wait()
        return error,output,p.returncode
        
    def GetBranch(self):
        error,output,returncode = self.CallGitProcess("git branch")
        print (error,output,returncode,"============================")
        if error and error.lower().find('fatal: not a git repository') != -1:
            return None
        else:
            for line in output.splitlines():
                if line.find('*') != -1:
                    return line.lstrip('*').strip()
        return ''

    def GetProjectDocument(self):
        project_browser = self.GetProjectFrame()
        return project_browser.GetView().GetDocument()
        
    def GetProjectFrame(self):
        return GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME)
