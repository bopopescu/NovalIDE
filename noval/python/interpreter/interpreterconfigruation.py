from noval import NewId,_
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox,filedialog
import noval.python.interpreter.interpreter as pythoninterpreter
import noval.python.parser.intellisence as intellisence
import noval.util.apputils as sysutils
import os
import noval.python.interpreter.pythonbuiltins as pythonbuiltins
import noval.python.interpreter.environment as pythonenvironment
import noval.python.interpreter.pythonpackages as pythonpackages
import noval.python.interpreter.pythonpath as pythonpath
import noval.python.interpreter.interpretermanager as interpretermanager
import threading
#import noval.tool.OutputThread as OutputThread
import subprocess
import noval.util.which as whichpath
import noval.util.strutils as strutils
import getpass
import noval.util.fileutils as fileutils
import noval.util.utils as utils
import noval.ui_base as ui_base
import noval.imageutils as imageutils
import noval.consts as consts
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.misc as misc
import noval.constants as constants
import noval.menu as tkmenu
import noval.ui_utils as ui_utils

ID_COPY_INTERPRETER_NAME = NewId()
ID_COPY_INTERPRETER_VERSION = NewId()
ID_COPY_INTERPRETER_PATH = NewId()
ID_MODIFY_INTERPRETER_NAME = NewId()
ID_REMOVE_INTERPRETER = NewId()
ID_NEW_INTERPRETER_VIRTUALENV = NewId()
ID_GOTO_INTERPRETER_PATH = NewId()

YES_FLAG = "Yes"
NO_FLAG = "No"


class NewVirtualEnvProgressDialog(ui_base.GenericProgressDialog):
    
    def __init__(self,parent):
        wx.ProgressDialog.__init__(self,_("New Virtual Env"),
                               _("Please wait a minute for end New Virtual Env"),
                               maximum = 100,
                               parent = parent,
                               style = 0
                                | wx.PD_APP_MODAL
                                | wx.PD_SMOOTH
                                )
        self.KeepGoing = True
        self.msg = ""
        
    def AppendMsg(self,msg):
        self.msg = msg.strip()

class NewVirtualEnvDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,interpreter,title):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
        self.main_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.main_frame, text=_("Name:")).grid(row=0,column=0,sticky=tk.NSEW,padx=consts.DEFAUT_CONTRL_PAD_X, pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_var = tk.StringVar()
        name_ctrl = ttk.Entry(self.main_frame,textvariable=self.name_var)
        name_ctrl.grid(row=0,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text= _("Location:")).grid(row=1,column=0,sticky=tk.NSEW,padx=consts.DEFAUT_CONTRL_PAD_X, pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.path_var = tk.StringVar()
        path_ctrl = ttk.Entry(self.main_frame,textvariable=self.path_var)
        path_ctrl.grid(row=1,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        misc.create_tooltip(path_ctrl,_("set the location of virtual env"))
        browser_btn = ttk.Button(self.main_frame, text= "...",command=self.ChooseVirtualEnvPath)
        browser_btn.grid(row=1,column=2,sticky=tk.NSEW,padx=consts.DEFAUT_CONTRL_PAD_X, pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        interprterChoice = ttk.Combobox(self.main_frame,values = self.GetChoices(),state="readonly")
        ttk.Label(self.main_frame, text= _("Base Interpreter:")).grid(row=2,column=0,sticky=tk.NSEW,padx=consts.DEFAUT_CONTRL_PAD_X, pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        interprterChoice.grid(row=2,column=1,sticky=tk.NSEW, pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        includeSitePackgaes = ttk.Checkbutton(self.main_frame, text=_("Inherited system site-packages from base interpreter"))
        includeSitePackgaes.grid(row=3,column=0,sticky=tk.NSEW,columnspan=2,padx=consts.DEFAUT_CONTRL_PAD_X, pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.grid(row=4,column=0,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=3)
        self.AppendokcancelButton(bottom_frame)

        self._interpreter = interpreter
     #   self.LoadInterpreters()
       
    def GetChoices(self):
        choices = []
        for i,interpreter in enumerate(interpretermanager.InterpreterManager.interpreters):
            display_name = "%s (%s)" % (interpreter.Version,interpreter.Path)
            choices.append(display_name)
        return choices
        
    def LoadInterpreters(self):
        self._interprterChoice.Clear()
        interpreter_image_path = os.path.join(sysutils.mainModuleDir, "noval", "tool", "bmp_source", "python_nature.png")
        interpreter_image = wx.Image(interpreter_image_path,wx.BITMAP_TYPE_ANY)
        interpreter_bmp = wx.BitmapFromImage(interpreter_image)
        i = 0
        for interpreter in interpretermanager.InterpreterManager.interpreters:
            if interpreter.IsBuiltIn:
                continue
            display_name = "%s (%s)" % (interpreter.Version,interpreter.Path)
            self._interprterChoice.Append(display_name,interpreter_bmp,interpreter.Path)
            if interpreter.Path == self._interpreter.Path:
                self._interprterChoice.SetSelection(i)
            i += 1
        
    def ChooseVirtualEnvPath(self,event):
        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(),
                _("Choose the location of Virtual Env"), 
                style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        self.path_ctrl.SetValue(path)
        
    def OnOKClick(self, event):
        name = self.name_ctrl.GetValue().strip()
        location = self.path_ctrl.GetValue().strip()
        if name == "":
            wx.MessageBox(_("name cann't be empty"))
            return
        if location == "":
            wx.MessageBox(_("location cann't be empty"))
            return
        self.EndModal(wx.ID_OK)

class AddInterpreterDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title,id_modify_dlg=False):
        ui_base.CommonModaldialog.__init__(self,parent)
        self._id_modify_dlg = id_modify_dlg
        self.title(title)
        row = ttk.Frame(self.main_frame)
        ttk.Label(row,text=_("Interpreter Path:")).pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        self.path_var = tk.StringVar()
        self.path_ctrl = ttk.Entry(row,text="",textvariable=self.path_var)
        if sysutils.is_windows():
            misc.create_tooltip(self.path_ctrl,_("set the location of python.exe or pythonw.exe"))
        else:
            misc.create_tooltip(self.path_ctrl,_("set the location of python interpreter"))
        self.path_ctrl.pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        self.browser_btn = ttk.Button(row, text=_("Browse..."),command=self.ChooseExecutablePath)
        self.browser_btn.pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        row.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_("Interpreter Name:")).pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        self.name_var = tk.StringVar()
        self.name_ctrl = ttk.Entry(row,textvariable=self.name_var)
        self.name_ctrl.pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        misc.create_tooltip(self.name_ctrl,_("set the name of python interpreter"))
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AddokcancelButton()
        
    def ChooseExecutablePath(self):
        if sysutils.is_windows():
            descrs = [(_("Executable"),".exe"),]
        else:
            descrs = [(_("All Files"),".*"),]
        path = filedialog.askopenfilename(
            master=self,
            filetypes=descrs,
            title=_("Select Executable Path")
        )
        if not path:
            return
        self.path_var.set(path)
        self.name_var.set(path)
        
    def _ok(self, event=None):
        if 0 == len(self.name_var.get()):
            messagebox.showerror(_("Error"),_("Interpreter Name is empty"),parent=self)
            return
        if not self._id_modify_dlg:
            if 0 == len(self.path_var.get()):
                messagebox.showerror(_("Error"),_("Interpreter Path is empty"),parent=self)
                return
            elif not os.path.exists(self.path_ctrl.get()):
                messagebox.showerror(_("Error"),_("Interpreter Path is not exist"),parent=self)
                return
        ui_base.CommonModaldialog._ok(self,event)
        
class InterpreterConfigurationPanel(ui_utils.BaseConfigurationPanel):
    def __init__(self,parent):
        ui_utils.BaseConfigurationPanel.__init__(self, parent)
        interpreter_staticText = ttk.Label(self, text=_("Python interpreters(eg.:such as python.exe, pythonw.exe). Double or right click to rename."))
        interpreter_staticText.grid(row=0, column=0, sticky=tk.NSEW,padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        columns = ['id','Name','Version','Path','Default']
        self.listview = treeviewframe.TreeViewFrame(self, columns=columns,displaycolumns=(1,2,3,4),show="headings",height=8)
        self.listview.tree.bind("<<TreeviewSelect>>", self.on_select, "+")
        self.listview.tree.bind("<Double-Button-1>", self.ModifyInterpreterNameDlg, "+")
        self.listview.tree.bind("<3>", self.OnContextMenu, True)
        self.listview.grid(row=1, column=0, sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        for column in columns[1:]:
            self.listview.tree.heading(column, text=_(column))
        self.listview.tree.column('1',width=100,anchor='w')
        self.listview.tree.column('2',width=70,anchor='w')
        self.listview.tree.column('4',width=70,anchor='w')

        # set single-cell frame
        self.columnconfigure(0, weight=1)
        right_frame = ttk.Frame(self)
        add_btn = ttk.Button(right_frame, text=_("Add"),command=self.AddInterpreter)
        add_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y*3,consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.remove_btn = ttk.Button(right_frame, text=_("Remove"),command=self.RemoveInterpreter)
        self.remove_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))    
        self.smart_analyse_btn = ttk.Button(right_frame, text=_("Smart Analyse"),command=self.SmartAnalyseIntreprter)
        self.smart_analyse_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.set_default_btn = ttk.Button(right_frame,text=_("Set Default"),command=self.SetDefaultInterpreter)
        self.set_default_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        right_frame.grid(row=0, column=1, rowspan=2,sticky=tk.NSEW)
        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, columnspan=2,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        self.rowconfigure(2, weight=1)
        
        self.package_icon = imageutils.load_image("","project/python/package_obj.gif")

        self.search_path_icon = imageutils.load_image("","python/jar_l_obj.gif")
        self.builtin_icon = imageutils.load_image("","python/builtin.png")
        self.environment_icon = imageutils.load_image("","environment.png")

        self.package_panel = pythonpackages.PackagePanel(nb)
        nb.add(self.package_panel, text=_("Package"),image=self.package_icon,compound=tk.LEFT)
        self.path_panel = pythonpath.PythonPathPanel(nb)
        nb.add(self.path_panel,text=_("Search Path"),image=self.search_path_icon,compound=tk.LEFT)
        self.builtin_panel = pythonbuiltins.PythonBuiltinsPanel(nb)
        nb.add(self.builtin_panel, text=_("Builtin Modules"),image=self.builtin_icon,compound=tk.LEFT)
        self.environment_panel = pythonenvironment.EnvironmentPanel(nb)
        nb.add(self.environment_panel, text=_("Environment Variable"),image=self.environment_icon,compound=tk.LEFT)
        self._interpreters = []
        self._current_interpreter = None
        self.ScanAllInterpreters()
        self.UpdateUI()
        self.menu = None
        
    def OnContextMenu(self, event):
        if self.menu is None:
            self.menu = tkmenu.PopupMenu()
            self.menu.Append(ID_COPY_INTERPRETER_NAME,_("Copy Name"),handler=lambda:self.ProcessEvent(ID_COPY_INTERPRETER_NAME))
            self.menu.Append(ID_COPY_INTERPRETER_VERSION,_("Copy Version"),handler=lambda:self.ProcessEvent(ID_COPY_INTERPRETER_VERSION))
            self.menu.Append(ID_COPY_INTERPRETER_PATH,_("Copy Path"),handler=lambda:self.ProcessEvent(ID_COPY_INTERPRETER_PATH))
            self.menu.Append(ID_MODIFY_INTERPRETER_NAME,_("Modify Name"),handler=lambda:self.ProcessEvent(ID_MODIFY_INTERPRETER_NAME))
            self.menu.Append(ID_REMOVE_INTERPRETER,_("Remove"),handler=lambda:self.ProcessEvent(ID_REMOVE_INTERPRETER))
            self.menu.Append(ID_NEW_INTERPRETER_VIRTUALENV,_("New VirtualEnv"),handler=lambda:self.ProcessEvent(ID_NEW_INTERPRETER_VIRTUALENV))
            self.menu.Append(ID_GOTO_INTERPRETER_PATH,_("Open Path in Explorer"),handler=lambda:self.ProcessEvent(ID_GOTO_INTERPRETER_PATH))
        self.menu.tk_popup(event.x_root, event.y_root)
        
    def ProcessEvent(self,id): 
        selections = self.listview.tree.selection()
        if not selections:
            return
        item = selections[0]
        interpreter_id = self.listview.tree.item(item)['values'][0]
        interpreter = interpretermanager.InterpreterAdmin(self._interpreters).GetInterpreterById(interpreter_id)   
        if id == ID_COPY_INTERPRETER_NAME:
            sysutils.CopyToClipboard(interpreter.Name)
            return True
        elif id == ID_COPY_INTERPRETER_VERSION:
            sysutils.CopyToClipboard(interpreter.Version)
            return True
        elif id == ID_COPY_INTERPRETER_PATH:
            sysutils.CopyToClipboard(interpreter.Path)
            return True
        elif id == ID_MODIFY_INTERPRETER_NAME:
            self.ModifyInterpreterNameDlg()
            return True
        elif id == ID_REMOVE_INTERPRETER:
            self.RemoveInterpreter()
            return True
        elif id == ID_NEW_INTERPRETER_VIRTUALENV:
            dlg = NewVirtualEnvDialog(self,interpreter,_("New Virtual Env"))
            python_path = dlg._interprterChoice.GetClientData(dlg._interprterChoice.GetSelection())
            interpreter = interpretermanager.InterpreterManager().GetInterpreterByPath(python_path)
            status = dlg.ShowModal()
            if status == wx.ID_OK:
                name = dlg.name_ctrl.GetValue().strip()
                location = dlg.path_ctrl.GetValue().strip()
                include_site_packages = dlg._includeSitePackgaes.GetValue()
                dlg.Destroy()
                progress_dlg = NewVirtualEnvProgressDialog(self)
                try:
                    self.CreateVirtualEnv(name,location,include_site_packages,interpreter,progress_dlg)
                except:
                    return
                while True:
                    if not progress_dlg.KeepGoing:
                        break
                    wx.MilliSleep(250)
                    wx.Yield()
                    progress_dlg.Pulse(progress_dlg.msg)
                progress_dlg.Destroy()
                if sysutils.isWindows():
                    python_path = os.path.join(location,"Scripts\\python.exe")
                else:
                    python_path = os.path.join(location,"bin/python")
                try:
                    interpreter = interpretermanager.InterpreterAdmin(self._interpreters).AddPythonInterpreter(python_path,name)
                    self.AddOneInterpreter(interpreter)
                    auto_generate_database = self.GetParent().GetOptionPanel(INTERPRETER_OPTION_NAME,GENERAL_ITEM_NAME).IsAutoGenerateDatabase()
                    self.SmartAnalyse(interpreter,auto_generate_database)
                    self.NotifyConfigurationChanged()
                except RuntimeError as e:
                    wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
            return True
        elif id == ID_GOTO_INTERPRETER_PATH:
            self.GotoPath(interpreter)
            return True
            
    def GotoPath(self,interpreter):
        err_code,msg = fileutils.open_file_directory(interpreter.Path)
        if err_code != ERROR_OK:
            wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
            
    def CreateVirtualEnv(self,name,location,include_site_packages,interpreter,progress_dlg):
        t = threading.Thread(target=self.CreatePythonVirtualEnv,args=(name,location,include_site_packages,interpreter,progress_dlg))
        t.start()
        
    def ExecCommandAndOutput(self,command,progress_dlg):
        #shell must be True on linux
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout_thread = OutputThread.OutputThread(p.stdout,p,progress_dlg)
        stdout_thread.start()
        p.wait()
        
    def GetVirtualEnvPath(self,interpreter):
        if sysutils.isWindows():
            virtualenv_name = "virtualenv.exe"
        else:
            virtualenv_name = "virtualenv"
        python_location = os.path.dirname(interpreter.Path)
        virtualenv_path_list = [os.path.join(python_location,"Scripts",virtualenv_name),os.path.join(python_location,virtualenv_name)]
        for virtualenv_path in virtualenv_path_list:
            if os.path.exists(virtualenv_path):
                return virtualenv_path
        virtualenv_path = whichpath.GuessPath(virtualenv_name)
        return virtualenv_path
        
    def IsLocationWritable(self,location):
        user = getpass.getuser()
        path = location
        while not os.path.exists(path):
            path = os.path.dirname(path)
        return fileutils.is_writable(path,user)
        
    def CreatePythonVirtualEnv(self,name,location,include_site_packages,interpreter,progress_dlg):
        progress_dlg.call_back = progress_dlg.AppendMsg
        if not interpreter.Packages.has_key('virtualenv'):
            progress_dlg.msg = "install virtualenv package..."
            should_root = False
            if not sysutils.isWindows():
                should_root = not interpreter.IsPythonlibWritable(interpreter)
            if not sysutils.isWindows() and should_root:
                command = "pkexec " + strutils.emphasis_path(interpreter.GetPipPath()) + " install virtualenv"
            else:
                command = strutils.emphasis_path(interpreter.GetPipPath()) + " install virtualenv"
            self.ExecCommandAndOutput(command,progress_dlg)
        should_root = not self.IsLocationWritable(location)
        if not sysutils.isWindows() and should_root:
            command = "pkexec " + strutils.emphasis_path(self.GetVirtualEnvPath(interpreter)) + " " + strutils.emphasis_path(location)
        else:
            command = strutils.emphasis_path(self.GetVirtualEnvPath(interpreter)) + " " + strutils.emphasis_path(location)
        if include_site_packages:
            command += " --system-site-packages"
        self.ExecCommandAndOutput(command,progress_dlg)
        progress_dlg.KeepGoing = False
            
    def ProcessUpdateUIEvent(self, event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            event.Enable(False)
            return False
        if event.GetId() == ID_NEW_INTERPRETER_VIRTUALENV:
            item = self.dvlc.RowToItem(index)
            id = self.dvlc.GetItemData(item)
            interpreter = interpretermanager.InterpreterAdmin(self._interpreters).GetInterpreterById(id)
            if interpreter.IsBuiltIn:
                event.Enable(False)
                return True
            
        event.Enable(True)
        return True
        
    def ModifyInterpreterNameDlg(self,event=None):
        selections = self.listview.tree.selection()
        if not selections:
            return
        item = selections[0]
        dlg = AddInterpreterDialog(self,_("Modify Interpreter Name"))
        interpreter_path = self.listview.tree.item(item)['values'][3]
        dlg.path_ctrl.insert('insert',interpreter_path)
        dlg.path_ctrl["state"] = tk.DISABLED
        dlg.browser_btn["state"] = tk.DISABLED
        interpreter_name = self.listview.tree.item(item)['values'][1]
        dlg.name_ctrl.insert('insert',interpreter_name)
        status = dlg.ShowModal()
        if status == constants.ID_OK:
            name = dlg.name_ctrl.get()
            if interpreter_name != name:
                self.NotifyConfigurationChanged()
                self.dvlc.SetTextValue(name,index,0)
        
    def AddInterpreter(self):
        dlg = AddInterpreterDialog(self,_("Add Interpreter"))
        status = dlg.ShowModal()
        if status == constants.ID_OK:
            try:
                interpreter = interpretermanager.InterpreterAdmin(self._interpreters).AddPythonInterpreter(dlg.path_var.get(),dlg.name_var.get())
                self.AddOneInterpreter(interpreter)
                self.NotifyConfigurationChanged()
                auto_generate_database = self.GetParent().GetOptionPanel(INTERPRETER_OPTION_NAME,GENERAL_ITEM_NAME).IsAutoGenerateDatabase()
                self.SmartAnalyse(interpreter,auto_generate_database)
                passedCheck = True
            except RuntimeError as e:
                messagebox.showerror(_("Error"),e.msg,parent=self)
        self.UpdateUI()
        
    def AddOneInterpreter(self,interpreter):
        def GetDefaultFlag(is_default):
            if is_default:
                return _(YES_FLAG)
            else:
                return _(NO_FLAG)
        path = interpreter.Path
        if utils.is_py2():
            path = path.decode(utils.get_default_encoding())
        item = self.listview.tree.insert("",0,values=(interpreter.Id,interpreter.Name,interpreter.Version,path,GetDefaultFlag(interpreter.Default)))
        self.listview.tree.selection_set(item)
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.environment_panel.SetVariables(interpreter)
        self.package_panel.LoadPackages(interpreter)
    
    def RemoveInterpreter(self):
        selections = self.listview.tree.selection()
        if not selections:
            return
        item = selections[0]
        if self.listview.tree.item(item)['values'][4] == _(YES_FLAG):
            messagebox.showwarning(_("Warning"),_("Default Interpreter cannot be remove"),parent=self)
            return
        ret = messagebox.askyesno(_("Warning"),_("Interpreter remove action cannot be recover,Do you want to continue remove this interpreter?"),parent=self)
        if ret == True:
            id = self.listview.tree.item(item)['values'][0]
            interpreter = interpretermanager.InterpreterAdmin(self._interpreters).GetInterpreterById(id)
            self._interpreters.remove(interpreter)
            self.listview.tree.delete(item)
            self.NotifyConfigurationChanged()
            
        self.UpdateUI()
        
    def SetDefaultInterpreter(self):
        selections = self.listview.tree.selection()
        if not selections:
            return
            
        item = selections[0]
        text = self.listview.tree.item(item)['values'][4]
        if text == _(YES_FLAG):
            return
        for child in self.listview.tree.get_children():
            if child == item:
                self.listview.tree.set(item, column=4, value=_(YES_FLAG))
            else:
                self.listview.tree.set(child, column=4, value=_(NO_FLAG))
        self.NotifyConfigurationChanged()
        
    def SmartAnalyseIntreprter(self):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = interpretermanager.InterpreterAdmin(self._interpreters).GetInterpreterById(id)
        self.SmartAnalyse(interpreter)
        self.NotifyConfigurationChanged()

    def SmartAnalyse(self,interpreter,auto_generate_database=True):
        if interpreter.IsBuiltIn:
            return
        try:
            interpreter.GetDocPath()
            interpreter.GetSysPathList()
            interpreter.GetBuiltins()
            self.package_panel.LoadPackages(interpreter,True)
        except Exception as e:
            wx.MessageBox(str(e),style = wx.OK|wx.ICON_ERROR)
            return
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.smart_analyse_btn.Enable(False)
        if not auto_generate_database:
            return
        dlg = AnalyseProgressDialog(self)
        try:
            intellisence.IntellisenceManager().generate_intellisence_data(interpreter,dlg)
        except:
            return
        while True:
            if not dlg.KeepGoing:
                break
            wx.MilliSleep(250)
            wx.Yield()
            dlg.Pulse()
            
        dlg.Destroy()
        self.smart_analyse_btn.Enable(True)
          
    def ScanAllInterpreters(self):
        for interpreter in interpretermanager.InterpreterManager.interpreters:
            self.AddOneInterpreter(interpreter)
            self._interpreters.append(interpreter)
            
    def on_select(self,event):
        self.UpdateUI()
        
    def UpdateUI(self):
        selections = self.listview.tree.selection()
        if not selections:
            self._current_interpreter = None
            self.smart_analyse_btn["state"] = tk.DISABLED
            self.remove_btn["state"] = tk.DISABLED
            self.set_default_btn["state"] = tk.DISABLED
        else:
            self.remove_btn["state"] = "normal"
            self.set_default_btn["state"] = "normal"
            id = self.listview.tree.item(selections[0])['values'][0]
            self._current_interpreter = interpretermanager.InterpreterAdmin(self._interpreters).GetInterpreterById(id)
            if interpretermanager.InterpreterManager().IsInterpreterAnalysing() or not self._current_interpreter.IsValidInterpreter:
                self.smart_analyse_btn["state"] = tk.DISABLED
            else:
                self.smart_analyse_btn["state"] = "normal"
        self.path_panel.AppendSysPath(self._current_interpreter)
        self.builtin_panel.SetBuiltiins(self._current_interpreter)
        self.environment_panel.SetVariables(self._current_interpreter)
        self.package_panel.LoadPackages(self._current_interpreter)
            
    def OnOK(self,optionsDialog):
        
        is_pythonpath_changed = self.path_panel.GetPythonPathList()
        self._configuration_changed = self._configuration_changed or is_pythonpath_changed
        try:
            is_environment_changed = self.environment_panel.GetEnviron()
            self._configuration_changed = self._configuration_changed or is_environment_changed
        except PromptErrorException as e:
            wx.MessageBox(e.msg,_("Environment Variable Error"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
            return False
        if self._configuration_changed:
            self.SaveInterpreterConfiguration()
            
        current_interpreter = interpretermanager.InterpreterManager.GetCurrentInterpreter()
        if current_interpreter is not None:
            #if current interpreter has been removed,use the default interprter as current interpreter
            interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(current_interpreter.Name)
        else:
            #set default interpreter as current interpreter
            interpreter = interpretermanager.InterpreterManager().GetDefaultInterpreter()
        if current_interpreter != interpreter:
            interpretermanager.InterpreterManager.SetCurrentInterpreter(interpretermanager.InterpreterManager().GetDefaultInterpreter())

        return True

    def SaveInterpreterConfiguration(self):
        #update latest interpreters
        interpretermanager.InterpreterManager.interpreters = self._interpreters
        for row in range(self.dvlc.GetStore().GetCount()):
            interpreter = self._interpreters[row]
            interpreter.Name = self.dvlc.GetTextValue(row,0)
            if self.dvlc.GetTextValue(row,3) == _(YES_FLAG) and interpreter != interpretermanager.InterpreterManager().GetDefaultInterpreter():
                interpretermanager.InterpreterManager().SetDefaultInterpreter(interpreter)
        interpretermanager.InterpreterManager().SavePythonInterpretersConfig()
        
    def OnCancel(self,optionsDialog):
        for interpreter in interpretermanager.InterpreterManager.interpreters:
            if interpreter.IsLoadingPackage:
                interpreter.StopLoadingPackage()
        self._configuration_changed = self._configuration_changed or self.path_panel.CheckPythonPath()
        self._configuration_changed = self._configuration_changed or self.environment_panel.CheckEnviron()
        if self._configuration_changed:
            ret = messagebox.askyesno(_("Save interpreter configuration"),_("Interpreter configuration has already been modified outside,Do you want to save?"),parent=self)
            if ret == True:
                self.OnOK(optionsDialog)
        return True
        
class AnalyseProgressDialog(ui_base.GenericProgressDialog):
    
    def __init__(self,parent):
        wx.ProgressDialog.__init__(self,_("Interpreter Smart Analyse"),
                               _("Please wait a minute for end analysing"),
                               maximum = 100,
                               parent=parent,
                               style = 0
                                | wx.PD_APP_MODAL
                                | wx.PD_SMOOTH
                                )
        self.KeepGoing = True                                
        