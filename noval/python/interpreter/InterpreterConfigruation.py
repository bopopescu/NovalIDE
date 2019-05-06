from noval import NewId,_
import tkinter as tk
from tkinter import ttk
import noval.python.interpreter.Interpreter as Interpreter
import noval.python.parser.intellisence as intellisence
import noval.util.apputils as sysutils
import os
import noval.python.interpreter.PythonBuiltins as PythonBuiltins
import noval.python.interpreter.Environment as Environment
import noval.python.interpreter.PythonPackages as PythonPackages
import noval.python.interpreter.PythonPath as PythonPath
import noval.python.interpreter.InterpreterManager as interpretermanager
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
    def __init__(self,parent,interpreter,dlg_id,title):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        flexGridSizer = wx.FlexGridSizer(cols = 3, vgap = HALF_SPACE, hgap = HALF_SPACE)
        flexGridSizer.AddGrowableCol(1,1)
        
        flexGridSizer.Add(wx.StaticText(self, -1, _("Name:")), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        self.name_ctrl = wx.TextCtrl(self, -1, "", size=(-1,-1))
        flexGridSizer.Add(self.name_ctrl, 2, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        flexGridSizer.Add(wx.StaticText(parent, -1, ""), 0)

        flexGridSizer.Add(wx.StaticText(self, -1, _("Location:")), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        self.path_ctrl = wx.TextCtrl(self, -1, "", size=(-1,-1))
        self.path_ctrl.SetToolTipString(_("set the location of virtual env"))
        flexGridSizer.Add(self.path_ctrl, 2, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        self.browser_btn = wx.Button(self, -1, _("..."),size=(40,-1))
        wx.EVT_BUTTON(self.browser_btn, -1, self.ChooseVirtualEnvPath)
        flexGridSizer.Add(self.browser_btn, flag=wx.ALIGN_RIGHT|wx.RIGHT, border=HALF_SPACE)  
        
        flexGridSizer.Add(wx.StaticText(self, -1, _("Base Interpreter:")), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        self._interprterChoice = wx.combo.BitmapComboBox(self, -1, "",choices = self.GetChoices(),size=(-1,-1), style=wx.CB_READONLY)
        flexGridSizer.Add(self._interprterChoice, 2, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        flexGridSizer.Add(wx.StaticText(parent, -1, ""), 0)
        
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._includeSitePackgaes = wx.CheckBox(self, -1, _("Inherited system site-packages from base interpreter"))
        line_sizer.Add(self._includeSitePackgaes, 0, wx.LEFT|wx.BOTTOM,SPACE)
        
        contentSizer.Add(flexGridSizer, 1, flag=wx.EXPAND|wx.ALL,border=SPACE)
        contentSizer.Add(line_sizer, 0, wx.RIGHT|wx.BOTTOM,HALF_SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        self.SetSizer(contentSizer)
        self.Fit()
        
        self._interpreter = interpreter
        self.LoadInterpreters()
       
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
    def __init__(self,parent,dlg_id,title):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Interpreter Path:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.path_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        if sysutils.isWindows():
            self.path_ctrl.SetToolTipString(_("set the location of python.exe or pythonw.exe"))
        else:
            self.path_ctrl.SetToolTipString(_("set the location of python interpreter"))
        lineSizer.Add(self.path_ctrl, 0, wx.LEFT|wx.ALIGN_BOTTOM, HALF_SPACE)
        
        self.browser_btn = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(self.browser_btn, -1, self.ChooseExecutablePath)
        lineSizer.Add(self.browser_btn, 0, wx.LEFT|wx.ALIGN_BOTTOM, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.ALL, HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Interpreter Name:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.name_ctrl = wx.TextCtrl(self, -1, "", size=(190,-1))
        self.name_ctrl.SetToolTipString(_("set the name of python interpreter"))
        lineSizer.Add(self.name_ctrl, 0, wx.LEFT, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.ALL, HALF_SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        self.SetSizer(contentSizer)
        self.Fit()
        
    def ChooseExecutablePath(self,event):
        if sysutils.isWindows():
            descr = _("Executable (*.exe) |*.exe")
        else:
            descr = "All Files (*)|*"
        dlg = wx.FileDialog(self,_("Select Executable Path"),
                            wildcard=descr,style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.path_ctrl.SetValue(path)
            self.name_ctrl.SetValue(path)
            self.path_ctrl.SetInsertionPointEnd()
        dlg.Destroy()  
        
class InterpreterConfigurationPanel(ttk.Frame):
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        interpreter_staticText = ttk.Label(self, text=_("Python interpreters(eg.:such as python.exe, pythonw.exe). Double or right click to rename."))
        interpreter_staticText.grid(row=0, column=0, sticky=tk.NSEW)
        columns = ['id','Name','Version','Path','Default']
        self.listview = ui_base.TreeFrame(self, columns=columns,displaycolumns=(1,2,3,4))
        self.listview.grid(row=1, column=0, sticky=tk.NSEW)
        for column in columns[1:]:
            self.listview.tree.heading(column, text=_(column))

        # set single-cell frame
        self.columnconfigure(0, weight=1)
      #  self.rowconfigure(0, weight=1)

   #     dataview.EVT_DATAVIEW_ITEM_ACTIVATED(self.dvlc, -1, self.ModifyInterpreterNameDlg)
    #    dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU(self.dvlc, -1,self.OnContextMenu)
        right_frame = ttk.Frame(self)
        padx = consts.DEFAUT_CONTRL_PAD_X/2
        pady = consts.DEFAUT_CONTRL_PAD_Y/2
        add_btn = ttk.Button(right_frame, text=_("Add"),command=self.AddInterpreter)
        add_btn.pack(padx=padx,pady=(pady))
        self.remove_btn = ttk.Button(right_frame, text=_("Remove"),command=self.RemoveInterpreter)
        self.remove_btn.pack(padx=padx,pady=(pady))    
        self.smart_analyse_btn = ttk.Button(right_frame, text=_("Smart Analyse"),command=self.SmartAnalyseIntreprter)
        self.smart_analyse_btn.pack(padx=padx,pady=(pady))
        self.set_default_btn = ttk.Button(right_frame,text=_("Set Default"),command=self.SetDefaultInterpreter)
        self.set_default_btn.pack(padx=padx,pady=(pady))
        right_frame.grid(row=0, column=1, rowspan=2,sticky=tk.NSEW)
     #   wx.EVT_BUTTON(self.set_default_btn, -1, self.SetDefaultInterpreter)
        nb = ttk.Notebook(self,style="ButtonNotebook.TNotebook")
        nb.grid(row=2, column=0, rowspan=2,sticky=tk.NSEW)
        
        self.package_icon = imageutils.load_image("","project/python/package_obj.gif")

        self.search_path_icon = imageutils.load_image("","python/jar_l_obj.gif")
        self.builtin_icon = imageutils.load_image("","python/builtin.png")
        self.environment_icon = imageutils.load_image("","environment.png")

        self.package_panel = PythonPackages.PackagePanel(nb)
        nb.add(self.package_panel, text=_("Package"),image=self.package_icon,compound=tk.LEFT)
        self.path_panel = PythonPath.PythonPathPanel(nb)
        nb.add(self.path_panel,text=_("Search Path"),image=self.search_path_icon,compound=tk.LEFT)
        self.builtin_panel = PythonBuiltins.PythonBuiltinsPanel(nb)
        nb.add(self.builtin_panel, text=_("Builtin Modules"),image=self.builtin_icon,compound=tk.LEFT)
        self.environment_panel = Environment.EnvironmentPanel(nb)
        nb.add(self.environment_panel, text=_("Environment Variable"),image=self.environment_icon,compound=tk.LEFT)
        self._interprter_configuration_changed = False
        self._interpreters = []
        #current selected interpreter
        self._current_interpreter = None
        self.ScanAllInterpreters()
        self.UpdateUI()
        
    def OnContextMenu(self, event):
        menu = wx.Menu()
        x, y = event.GetPosition().x,event.GetPosition().y
        menu.Append(ID_COPY_INTERPRETER_NAME,_("Copy Name"))
        wx.EVT_MENU(self, ID_COPY_INTERPRETER_NAME, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_COPY_INTERPRETER_NAME, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_COPY_INTERPRETER_VERSION,_("Copy Version"))
        wx.EVT_MENU(self, ID_COPY_INTERPRETER_VERSION, self.ProcessEvent) 
        wx.EVT_UPDATE_UI(self, ID_COPY_INTERPRETER_VERSION, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_COPY_INTERPRETER_PATH,_("Copy Path"))
        wx.EVT_MENU(self, ID_COPY_INTERPRETER_PATH, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_COPY_INTERPRETER_PATH, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_MODIFY_INTERPRETER_NAME,_("Modify Name"))
        wx.EVT_MENU(self, ID_MODIFY_INTERPRETER_NAME, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_MODIFY_INTERPRETER_NAME, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_REMOVE_INTERPRETER,_("Remove"))
        wx.EVT_MENU(self, ID_REMOVE_INTERPRETER, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_REMOVE_INTERPRETER, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_NEW_INTERPRETER_VIRTUALENV,_("New VirtualEnv"))
        wx.EVT_MENU(self, ID_NEW_INTERPRETER_VIRTUALENV, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_NEW_INTERPRETER_VIRTUALENV, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_GOTO_INTERPRETER_PATH,_("Open Path in Explorer"))
        wx.EVT_MENU(self, ID_GOTO_INTERPRETER_PATH, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_GOTO_INTERPRETER_PATH, self.ProcessUpdateUIEvent)
        
        self.dvlc.PopupMenu(menu,wx.Point(x, y))
        menu.Destroy()
        
    def ProcessEvent(self, event): 
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = interpretermanager.InterpreterAdmin(self._interpreters).GetInterpreterById(id)   
        id = event.GetId()
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
            self.ModifyInterpreterNameDlg(None)
            return True
        elif id == ID_REMOVE_INTERPRETER:
            self.RemoveInterpreter(None)
            return True
        elif id == ID_NEW_INTERPRETER_VIRTUALENV:
            dlg = NewVirtualEnvDialog(self,interpreter,-1,_("New Virtual Env"))
            dlg.CenterOnParent()
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
                    self._interprter_configuration_changed = True
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
        
    def ModifyInterpreterNameDlg(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            self.UpdateUI()
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        dlg = AddInterpreterDialog(self,-1,_("Modify Interpreter Name"))
        interpreter_path = self.dvlc.GetTextValue(index,2)
        dlg.path_ctrl.SetValue(interpreter_path)
        dlg.path_ctrl.Enable(False)
        dlg.browser_btn.Enable(False)
        interpreter_name = self.dvlc.GetTextValue(index,0)
        dlg.name_ctrl.SetValue(interpreter_name)
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        passedCheck = False
        while status == wx.ID_OK and not passedCheck:
            if 0 == len(dlg.name_ctrl.GetValue()):
                wx.MessageBox(_("Interpreter Name is empty"),_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            else:
                name = dlg.name_ctrl.GetValue()
                if interpreter_name != name:
                    self._interprter_configuration_changed = True
                    self.dvlc.SetTextValue(name,index,0)
                passedCheck = True
        dlg.Destroy()
        
    def AddInterpreter(self):
        dlg = AddInterpreterDialog(self,-1,_("Add Interpreter"))
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        passedCheck = False
        while status == wx.ID_OK and not passedCheck:
            if 0 == len(dlg.path_ctrl.GetValue()):
                wx.MessageBox(_("Interpreter Path is empty"),_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            elif 0 == len(dlg.name_ctrl.GetValue()):
                wx.MessageBox(_("Interpreter Name is empty"),_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            elif not os.path.exists(dlg.path_ctrl.GetValue()):
                wx.MessageBox(_("Interpreter Path is not exist"),_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            else:
                try:
                    interpreter = interpretermanager.InterpreterAdmin(self._interpreters).AddPythonInterpreter(dlg.path_ctrl.GetValue(),dlg.name_ctrl.GetValue())
                    self.AddOneInterpreter(interpreter)
                    self._interprter_configuration_changed = True
                    auto_generate_database = self.GetParent().GetOptionPanel(INTERPRETER_OPTION_NAME,GENERAL_ITEM_NAME).IsAutoGenerateDatabase()
                    self.SmartAnalyse(interpreter,auto_generate_database)
                    passedCheck = True
                except RuntimeError as e:
                    wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
                    status = dlg.ShowModal()     
        self.UpdateUI(None)
        dlg.Destroy()
        
    def AddOneInterpreter(self,interpreter):
        def GetDefaultFlag(is_default):
            if is_default:
                return _(YES_FLAG)
            else:
                return _(NO_FLAG)
        path = interpreter.Path
        if utils.is_py2():
            path = path.decode(utils.get_default_encoding())
        self.listview.tree.insert("",0,values=(interpreter.Id,interpreter.Name,interpreter.Version,path,GetDefaultFlag(interpreter.Default)))
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.environment_panel.SetVariables(interpreter)
        self.package_panel.LoadPackages(interpreter)
    
    def RemoveInterpreter(self):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
            
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        if self.dvlc.GetTextValue(index,3) == _(YES_FLAG):
            wx.MessageBox(_("Default Interpreter cannot be remove"),_("Warning"),wx.OK|wx.ICON_WARNING,self)
            return
        ret = wx.MessageBox(_("Interpreter remove action cannot be recover,Do you want to continue remove this interpreter?"),_("Warning"),wx.YES_NO|wx.ICON_QUESTION,self)
        if ret == wx.YES:
            interpreter = interpretermanager.InterpreterAdmin(self._interpreters).GetInterpreterById(id)
            self._interpreters.remove(interpreter)
            self.dvlc.DeleteItem(index)
            self._interprter_configuration_changed = True
            
        self.UpdateUI(None)
        
    def SetDefaultInterpreter(self):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
            
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        if self.dvlc.GetTextValue(index,3) == _(YES_FLAG):
            return
        for row in range(self.dvlc.GetStore().GetCount()):
            if row == index:
                self.dvlc.SetTextValue(_(YES_FLAG),row,3)
            else:
                self.dvlc.SetTextValue(_(NO_FLAG),row,3)
        self._interprter_configuration_changed = True
        
    def SmartAnalyseIntreprter(self):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = interpretermanager.InterpreterAdmin(self._interpreters).GetInterpreterById(id)
        self.SmartAnalyse(interpreter)
        self._interprter_configuration_changed = True

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
            
    def on_select(self):
        self.UpdateUI()
        
    def UpdateUI(self):
        selections = self.listview.tree.selection()
        print selections,"===================="
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
        self._interprter_configuration_changed = self._interprter_configuration_changed or is_pythonpath_changed
        try:
            is_environment_changed = self.environment_panel.GetEnviron()
            self._interprter_configuration_changed = self._interprter_configuration_changed or is_environment_changed
        except PromptErrorException as e:
            wx.MessageBox(e.msg,_("Environment Variable Error"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
            return False
        if self._interprter_configuration_changed:
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
        self._interprter_configuration_changed = self._interprter_configuration_changed or self.path_panel.CheckPythonPath()
        self._interprter_configuration_changed = self._interprter_configuration_changed or self.environment_panel.CheckEnviron()
        if self._interprter_configuration_changed:
            ret = wx.MessageBox(_("Interpreter configuration has already been modified outside,Do you want to save?"), _("Save interpreter configuration"),
                           wx.YES_NO  | wx.ICON_QUESTION,self)
            if ret == wx.YES:
                self.OnOK(optionsDialog)
        return True
        
    def NotifyConfigurationChange(self):
        self._interprter_configuration_changed = True
        
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
        