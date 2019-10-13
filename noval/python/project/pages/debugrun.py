# -*- coding: utf-8 -*-
from noval import _,GetApp
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
import os
import noval.util.fileutils as fileutils
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.project.variables as variablesutils
import noval.python.project.runconfiguration as runconfiguration
from noval.util import utils
import noval.consts as consts
import noval.ui_utils as ui_utils
import noval.project.property as projectproperty
import noval.ui_base as ui_base
import noval.imageutils as imageutils
import noval.editor.text as texteditor
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.ttkwidgets.listboxframe as listboxframe
import noval.ttkwidgets.textframe as textframe
import noval.python.pyutils as pyutils
import noval.constants as constants
import copy
import noval.ui_utils as ui_utils
      
class BasePage(ui_utils.BaseConfigurationPanel):
    
    def __init__(self,parent,run_configuration):
        ui_utils.BaseConfigurationPanel.__init__(self, parent)
        self.run_configuration = run_configuration
        
    def GetConfiguration(self):
        return None
        
    @property
    def ProjectDocument(self):
        return self.run_configuration.ProjectDocument
        
    @property
    def MainModuleFile(self):
        return self.run_configuration.MainModuleFile

class StartupPage(BasePage):
    def __init__(self,parent,run_configuration):
        BasePage.__init__(self,parent,run_configuration)
        sbox = ttk.LabelFrame(self, text= _("Project") + ":")
        row = ttk.Frame(sbox)
        ttk.Label(row, text= _('Project Name:')).pack(side=tk.LEFT)
        self.projectVar = tk.StringVar(value=self.ProjectDocument.GetModel().Name)
        projectNameControl = ttk.Entry(row, textvariable=self.projectVar)
        projectNameControl.pack(side=tk.LEFT,fill="x",expand=1,padx=(0,consts.DEFAUT_HALF_CONTRL_PAD_X))
        projectNameControl['state'] = "readonly"
        row.pack(fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y)
        sbox.pack(fill="x")
        sbox = ttk.LabelFrame(self, text= _("Startup Module:"))
        row = ttk.Frame(sbox)
        ttk.Label(row, text=_('Main Module:')).pack(side=tk.LEFT)
        self.main_module_var = tk.StringVar()
        main_module_Control = ttk.Entry(row,textvariable=self.main_module_var)
        
        main_module_Control.pack(side=tk.LEFT,fill="x",expand=1)
        if self.MainModuleFile is not None:
            main_module_path = self.ProjectDocument.GetModel()\
                            .GetRelativePath(self.MainModuleFile)
            main_module_path = os.path.join(variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE) , \
                                            main_module_path)
            self.main_module_var.set(main_module_path)
            ttk.Button(row, text= _("Browse..."),command=self.BrowseMainModule).pack(side=tk.LEFT,padx=consts.DEFAUT_HALF_CONTRL_PAD_X)
        row.pack(fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y)
        sbox.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        sbox = ttk.LabelFrame(self, text=_("Startup Directory:"))
        self._defaultVar = tk.IntVar(value=0)
        row = ttk.Frame(sbox)
        defaultRadioBtn = ttk.Radiobutton(row, text=_("Default:"),variable=self._defaultVar,command=self.CheckDefaultPath,value=0)
        defaultRadioBtn.pack(side=tk.LEFT)
        self.default_var = tk.StringVar(value=variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE))
        self.default_dirControl = ttk.Entry(row, textvariable=self.default_var)
        self.default_dirControl.pack(side=tk.LEFT,fill="x",expand=1,padx=(0,consts.DEFAUT_HALF_CONTRL_PAD_X))
        row.pack(fill="x",expand=1,pady=consts.DEFAUT_CONTRL_PAD_Y)
        row = ttk.Frame(sbox) 
        self._otherRadioBtn = ttk.Radiobutton(row, text=_("Other:"),value=1,variable=self._defaultVar,command=self.CheckOtherPath)
        self._otherRadioBtn.pack(side=tk.LEFT)
        self.other_var = tk.StringVar()
        self.other_dirControl = ttk.Entry(row,textvariable=self.other_var)
        self.other_dirControl.pack(side=tk.LEFT,fill="x",expand=1,padx=(0,consts.DEFAUT_HALF_CONTRL_PAD_X))
        row.pack(fill="x",expand=1,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        row = ttk.Frame(sbox)
        ttk.Label(row).pack(side=tk.LEFT,fill="x",expand=1)
        self.project_folder_btn = ttk.Button(row,text= _("Project Folder"),command=self.BrowseProjectFolder)
        self.project_folder_btn.pack(side=tk.LEFT)
        self.file_system_btn = ttk.Button(row, text=_("Local File System"),command=self.BrowseLocalPath)
        self.file_system_btn.pack(side=tk.LEFT,padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0))
        self.variables_btn = ttk.Button(row, text=_("Variables"),command=self.BrowseVariables)
        self.variables_btn.pack(side=tk.LEFT,padx=consts.DEFAUT_HALF_CONTRL_PAD_X)
        row.pack(fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        startup_configuration = run_configuration.GetChildConfiguration(runconfiguration.StartupConfiguration.CONFIGURATION_NAME)
        self._startup_path_pattern = startup_configuration.StartupPathPattern
        if self._startup_path_pattern == runconfiguration.StartupConfiguration.DEFAULT_PROJECT_DIR_PATH:
            self._defaultVar.set(0)
        else:
            self._defaultVar.set(1)
            self.other_var.set(startup_configuration.StartupPath)
        
        sbox.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.UpdateButtonUI()
        
    def CheckDefaultPath(self):
        self._defaultVar.set(0)
        self.UpdateButtonUI()
        
    def CheckOtherPath(self):
        self._defaultVar.set(1)
        self.UpdateButtonUI()
        
    def UpdateButtonUI(self):
        if self._defaultVar.get() == 0:
            self.default_dirControl['state'] = tk.NORMAL
            self.other_dirControl['state'] = tk.DISABLED
            self.project_folder_btn['state'] = tk.DISABLED
            self.file_system_btn['state'] = tk.DISABLED
            self.variables_btn['state'] = tk.DISABLED
            self._startup_path_pattern = runconfiguration.StartupConfiguration.DEFAULT_PROJECT_DIR_PATH
        else:
            self.other_dirControl['state'] = tk.NORMAL
            self.default_dirControl['state'] = tk.DISABLED
            self.project_folder_btn['state'] = tk.NORMAL
            self.file_system_btn['state'] = tk.NORMAL
            self.variables_btn['state'] = tk.NORMAL
            self._startup_path_pattern = runconfiguration.StartupConfiguration.LOCAL_FILE_SYSTEM_PATH
            
    def BrowseLocalPath(self):
        path = filedialog.askdirectory(title=_("Select the startup path"))
        if not path:
            return
        self._startup_path_pattern = runconfiguration.StartupConfiguration.LOCAL_FILE_SYSTEM_PATH
        self.other_var.set(fileutils.opj(path))
        
    def BrowseProjectFolder(self):
        dlg = pyutils.ProjectFolderPathDialog(self,_("Select Project Folder"),self.ProjectDocument.GetModel())
        if dlg.ShowModal() == constants.ID_OK:
            selected_path = dlg.selected_path
            if selected_path is not None:
                selected_path = os.path.join(variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE) , selected_path)
            else:
                selected_path = variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE)
            self.other_var.set(selected_path)
            self._startup_path_pattern = runconfiguration.StartupConfiguration.PROJECT_CHILD_FOLDER_PATH
        
    def BrowseVariables(self):
        variable_dlg = variablesutils.VariablesDialog(self,_("Select Variable"),self.ProjectDocument)
        if variable_dlg.ShowModal() == constants.ID_OK:
            self.other_var.set(variable_dlg.selected_variable_name)
            self._startup_path_pattern = runconfiguration.StartupConfiguration.EXPRESSION_VALIABLE_PATH
            
    def BrowseMainModule(self):
        dlg = pyutils.SelectModuleFileDialog(self,_("Select Main Module"),self.ProjectDocument.GetModel())
        if dlg.ShowModal() == constants.ID_OK:
            main_module_path = os.path.join(variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE) , self.ProjectDocument.\
                    GetModel().GetRelativePath(dlg.module_file))
            self.main_module_var.set(main_module_path)
            self.run_configuration.MainModuleFile = dlg.module_file
        
    def OnOK(self):
        try:
            main_module_path = self.main_module_var.get().strip()
            python_variable_manager = variablesutils.GetProjectVariableManager(self.ProjectDocument)
            main_module_path = python_variable_manager.EvalulateValue(main_module_path)
            
            other_startup_path = self.other_var.get().strip()
            other_startup_path = python_variable_manager.EvalulateValue(other_startup_path)
            
        except RuntimeError as e:
            messagebox.showerror(_("Error"),str(e),parent=self)
            return False
            
        main_module_file = self.ProjectDocument.GetModel().FindFile(main_module_path)
        if not main_module_file:
            messagebox.showinfo(GetApp().GetAppName(),_("Module file \"%s\" is not in project") % main_module_path)
            return False
        return True
        
    def GetConfiguration(self):
        return runconfiguration.StartupConfiguration(self.ProjectDocument,self.MainModuleFile,\
                       self._startup_path_pattern, self.other_var.get().strip())
        
class ArgumentsPage(BasePage):
    def __init__(self,parent,run_configuration):
        BasePage.__init__(self,parent,run_configuration)
        arguments_configuration = run_configuration.GetChildConfiguration(runconfiguration.AugumentsConfiguration.CONFIGURATION_NAME)
        
        sbox = ttk.LabelFrame(self, text=_("Program Arguments:"))
        text_frame = textframe.TextFrame(sbox,borderwidth=1,relief="solid",text_class=texteditor.TextCtrl,height=7,width=10,show_scrollbar=False)
        self.program_argument_textctrl = text_frame.text
        self.program_argument_textctrl.insert(tk.END,arguments_configuration.ProgramArgs)
        text_frame.pack(fill="both",expand=1)
        variables_btn = ttk.Button(sbox, text=_("Variables"),command=self.BrowseVariables)
        ttk.Label(sbox).pack(side=tk.LEFT,fill="x",expand=1)
        variables_btn.pack(side=tk.LEFT,fill="x",padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=consts.DEFAUT_HALF_CONTRL_PAD_Y)
        sbox.pack(fill="both",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        sbox = ttk.LabelFrame(self, text=_("Interpreter Options:"))
        text_frame = textframe.TextFrame(sbox,borderwidth=1,relief="solid",text_class=texteditor.TextCtrl,height=7,width=10,show_scrollbar=False)
        self.interpreter_option_textctrl = text_frame.text
        # text=arguments_configuration.InterpreterOption
        self.interpreter_option_textctrl.insert(tk.END,arguments_configuration.InterpreterOption)
        text_frame.pack(fill="both",expand=1)
        sbox.pack(fill="both",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
    def BrowseVariables(self):
        variable_dlg = variablesutils.VariablesDialog(self,_("Select Variable"),self.ProjectDocument)
        if variable_dlg.ShowModal() == constants.ID_OK:
            self.program_argument_textctrl.insert("insert",variable_dlg.selected_variable_name)
        
    def OnOK(self):
        try:
            self.GetArgumentsText()
        except RuntimeError as e:
            messagebox.showerror(_("Error"),str(e),parent=self)
            return False
        return True

    def GetArgumentsText(self):
        python_variable_manager = variablesutils.GetProjectVariableManager(self.ProjectDocument)
        arguments_text = python_variable_manager.EvalulateValue(self.program_argument_textctrl.GetValue())
        return arguments_text
        
    def GetConfiguration(self):
        main_module_file = self.master.master.master.GetMainModuleFile()
        return runconfiguration.AugumentsConfiguration(self.ProjectDocument,main_module_file,\
                       self.interpreter_option_textctrl.GetValue(),self.program_argument_textctrl.GetValue())
        
class InterpreterConfigurationPage(BasePage):
    def __init__(self,parent,run_configuration):
        BasePage.__init__(self,parent,run_configuration)
        interpreter_configuration = run_configuration.GetChildConfiguration(runconfiguration.InterpreterConfiguration.CONFIGURATION_NAME)
        ttk.Label(self, text=_("Interpreter:")).pack(fill="x")
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        self.interpreter_var = tk.StringVar()
        interpretersCombo = ttk.Combobox(self, values=choices,textvariable=self.interpreter_var)
        interpretersCombo.pack(fill="x")
        if len(choices) > 0:
            interpretersCombo.current(default_selection)
        
        ttk.Label(self, text=_("PYTHONPATH that will be used in the run:")).pack(fill="x")
        self.list_var = tk.StringVar()
        listbox_view = listboxframe.ListboxFrame(self,listbox_class=ui_utils.ThemedListbox,show_scrollbar=False,listvariable=self.list_var)
        self.listbox = listbox_view.listbox
        listbox_view.pack(fill="both",expand=1)
        #必须放在SetCurrentInterpreterName方法前面
        self.interpreter_var.trace("w", self.GetInterpreterPythonPath)
        #这里会触发上面的事件
        self.SetCurrentInterpreterName(interpreter_configuration)
        
    def SetCurrentInterpreterName(self,interpreter_configuration):
        interpreter_name = interpreter_configuration.InterpreterName
        if interpreter_name:
            self.interpreter_var.set(interpreter_name)
        
    def GetInterpreterPythonPath(self,*GetInterpreterPythonPath):
        self.list_var.set(tuple())
        interpreter_name = self.interpreter_var.get()
        self.AppendInterpreterPythonPath(interpreter_name)
    
    def AppendInterpreterPythonPath(self,interpreter_name):
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_name)
        if interpreter is None:
            return
        #拷贝一份列表否则会修改原列表
        values = copy.copy(interpreter.PythonPathList)
        proprty_dlg = self.master.master.master.master.master.master.master.master
        if proprty_dlg.HasPanel("Project References"):
            project_reference_panel = proprty_dlg.GetOptionPanel("Project References")
            for project_filename in project_reference_panel.GetReferenceProjects():
                values.append(os.path.dirname(project_filename))
            python_path_panel = proprty_dlg.GetOptionPanel('PythonPath')
            values.extend(python_path_panel.GetPythonPathList())
        else:
            project_configuration = runconfiguration.ProjectConfiguration(self.ProjectDocument)
            values.extend(project_configuration.LoadPythonPath())
        self.list_var.set(tuple(set(values)))
        
    def GetConfiguration(self):
        main_module_file = self.master.master.master.GetMainModuleFile()
        return runconfiguration.InterpreterConfiguration(self.ProjectDocument,main_module_file,\
                       self.interpreter_var.get().strip())
    
    def CheckInterpreterExist(self):
        interpreter_name = self.interpreter_var.get().strip()
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_name)
        if interpreter is None:
            raise InterpreterNotExistError(interpreter_name)
        return True
        
    def OnOK(self):
        try:
            return self.CheckInterpreterExist()
        except RuntimeError as e:
            wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
            return False
        
class InputOutputPage(ui_utils.BaseConfigurationPanel):
    def __init__(self,parent,dlg_id,size):
        ui_utils.BaseConfigurationPanel.__init__(self, parent)
        
class EnvironmentPage(BasePage,ui_utils.BaseEnvironmentUI):
    def __init__(self,parent,run_configuration):
        BasePage.__init__(self,parent,run_configuration)
        self.InitUI()
        self.LoadEnvironments()
        self.UpdateUI()
            
    def LoadEnvironments(self,):
        environs = self.run_configuration.GetChildConfiguration(runconfiguration.EnvironmentConfiguration.CONFIGURATION_NAME).Environ
        self.RemoveRowVariable(self.listview.tree.get_children())
        for env in environs:
            self.AddVariable(env,environs[env])
        self.UpdateUI(None)
        
    def GetConfiguration(self):
        environ = self.GetEnviron()
        main_module_file = self.master.master.master.GetMainModuleFile()
        return runconfiguration.EnvironmentConfiguration(self.ProjectDocument,main_module_file,\
                       environ)
                       
    def OnOK(self):
        return True
        
class RunConfigurationDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title,run_configuration):
        ui_base.CommonModaldialog.__init__(self, parent)
        self.title(title)
        self.current_project_document = run_configuration.ProjectDocument
        self.selected_project_file = run_configuration.MainModuleFile
        sizer_frame = ttk.Frame(self.main_frame)
        if run_configuration.IsNewConfiguration:
            st_text = ttk.Label(sizer_frame,text = _("New Debug/Run Configuration"),font="BoldEditorFont")
        else:
            st_text = ttk.Label(sizer_frame,text = _("Edit Debug/Run Configuration"),font="BoldEditorFont")
        st_text.pack(side=tk.LEFT,fill="x",expand=1)
        self.show_img = imageutils.load_image("","project/run_wizard.png")
        ttk.Label(sizer_frame,image = self.show_img).pack(side=tk.LEFT,fill="x")
 
        sizer_frame.pack(fill="x")       
        separator = ttk.Separator(self.main_frame, orient = tk.HORIZONTAL)
        separator.pack(fill="x") 
        
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_('Name:')).pack(side=tk.LEFT,fill="x")

        self.nameVar = tk.StringVar(value=run_configuration.Name)
        nameControl = ttk.Entry(row, textvariable=self.nameVar)
        nameControl.pack(side=tk.LEFT,fill="x",expand=1)
        row.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.nb = ttk.Notebook(self.main_frame)
        self.startup_icon = imageutils.load_image("","project/python/startup.png")
        self.arguments_icon = imageutils.load_image("","project/python/parameter.png")
        self.interpreter_icon = imageutils.load_image("","python/interpreter.ico")
        self.environment_icon = imageutils.load_image("","environment.png")

        self.startup_panel = StartupPage(self.nb,run_configuration)
        self.nb.add(self.startup_panel, text=_("Startup"),image=self.startup_icon,compound=tk.LEFT)
    
        self.arguments_panel = ArgumentsPage(self.nb,run_configuration)
        self.nb.add(self.arguments_panel, text=_("Arguments"),image=self.arguments_icon,compound=tk.LEFT)

        self.interpreter_panel = InterpreterConfigurationPage(self.nb,run_configuration)
        self.nb.add(self.interpreter_panel, text=_("Interpreter"),image=self.interpreter_icon,compound=tk.LEFT)

        self.environment_panel = EnvironmentPage(self.nb,run_configuration)
        self.nb.add(self.environment_panel, text=_("Environment"),image=self.environment_icon,compound=tk.LEFT)
        self.nb.pack(fill="both",expand=1,padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AddokcancelButton()
        
    def _ok(self):
        if self.nameVar.get().strip() == "":
            messagebox.showerror(GetApp().GetAppName(),_("A name is required for the configuration"))
            return
        for panel in self.nb.winfo_children():
            if hasattr(panel,"OnOK") and not panel.OnOK():
                return
        args = {
            runconfiguration.StartupConfiguration.CONFIGURATION_NAME:self.startup_panel.GetConfiguration(),
            runconfiguration.AugumentsConfiguration.CONFIGURATION_NAME:self.arguments_panel.GetConfiguration(),
            runconfiguration.InterpreterConfiguration.CONFIGURATION_NAME:self.interpreter_panel.GetConfiguration(),
            runconfiguration.EnvironmentConfiguration.CONFIGURATION_NAME:self.environment_panel.GetConfiguration(),
        }
        self.run_configuration = runconfiguration.RunConfiguration(self.nameVar.get().strip(),**args)
        ui_base.CommonModaldialog._ok(self)
        
    def GetMainModuleFile(self):
        return self.startup_panel.MainModuleFile

class DebugRunPanel(ui_utils.BaseConfigurationPanel):
    """description of class"""
    def __init__(self,parent,item,current_project):
        ui_utils.BaseConfigurationPanel.__init__(self,parent)

        self._configuration_list = []
        self.current_project_document = current_project
        project_view = self.current_project_document.GetFirstView()
        self.select_project_file = None
        self.is_folder = False
        if item == project_view._treeCtrl.GetRootItem():
            ttk.Label(self, text=_("Set the default startup file when run project.")).pack(fill="x")
            startup_file_path = ''
            startup_file = self.current_project_document.GetModel().StartupFile
            if startup_file is not None:
                startup_file_path = self.current_project_document.GetModel()\
                            .GetRelativePath(startup_file)
                startup_file_path = os.path.join(variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE) , startup_file_path)
            row = ttk.Frame(self)
            self.startup_path_var = tk.StringVar(value=startup_file_path)
            ttk.Combobox(row,textvariable=self.startup_path_var).pack(side=tk.LEFT,fill="x",expand=1)
            ttk.Button(row, text= _("Select the startup file"),command=self.SetStartupFile).pack(side=tk.LEFT,padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0))
            row.pack(fill="x")
        elif project_view._IsItemFile(item):
            self.select_project_file = project_view._GetItemFile(item)
        else:
            self.is_folder = True
            
        manage_configuration_staticLabel = ttk.Label(self,text= _("You can manage launch run configurations and set default configuration as belows.\n"))
        manage_configuration_staticLabel.pack(fill="x")
        configuration_staticLabel = ttk.Label(self, text= _("Set run configurations for project '%s':") % self.GetProjectName())
        configuration_staticLabel.pack(fill="x")
        row = ttk.Frame(self)
        
        listbox_view =treeviewframe.TreeViewFrame(row,borderwidth=1,relief="solid",show_scrollbar=False)
        self.configuration_ListCtrl = listbox_view.tree
        listbox_view.pack(side=tk.LEFT,fill="both",expand=1)
        self.configuration_ListCtrl.bind("<<TreeviewSelect>>", self.UpdateUI, True)
        self.configuration_ListCtrl.bind("<Double-Button-1>", self.EditRunConfiguration, "+")
        right = ttk.Frame(row)
        self.run_config_img = imageutils.load_image("","project/python/runconfig.png")
        self.new_configuration_btn = ttk.Button(right,text= _("New"),command=self.NewRunConfiguration)
        self.edit_configuration_btn = ttk.Button(right, text=_("Edit"),command=self.EditRunConfiguration)
        self.remove_configuration_btn = ttk.Button(right, text=_("Remove"),command=self.RemoveConfiguration)
        self.copy_configuration_btn = ttk.Button(right, text=_("Copy"),command=self.CopyConfiguration)
        self.new_configuration_btn.pack(padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.edit_configuration_btn.pack(padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0),pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.remove_configuration_btn.pack(padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0),pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.copy_configuration_btn.pack(padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0),pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        right.pack(side=tk.LEFT,fill="y")
        row.pack(fill="both",expand=1)
        
        #windows系统添加一个选项,如果是windows程序,则调用解释器可执行程序pythonw.exe
        if utils.is_windows():
            end = ttk.Frame(self)
            self._isWindowsApplicationVar = tk.IntVar(value=utils.profile_get_int(self.current_project_document.GetKey('IsWindowsApplication'), False))
            isWindowsApplicationCheckBox = ttk.Checkbutton(end,text=_("Windows Application"),variable=self._isWindowsApplicationVar)
            isWindowsApplicationCheckBox.pack(fill="x")
            end.pack(fill="x")

        #should use Layout ,could not use Fit method
        #disable all buttons when file is not python file or is folder
        if not self.IsPythonFile() or self.is_folder:
            self.edit_configuration_btn['state'] = tk.DISABLED
            self.remove_configuration_btn['state'] = tk.DISABLED
            self.new_configuration_btn['state'] = tk.DISABLED
            self.copy_configuration_btn['state'] = tk.DISABLED
        self.UpdateUI()
        #folder or package folder has no run configurations
        if not self.is_folder:
            self.LoadConfigurations()

    def GetProjectName(self):
        return os.path.basename(self.current_project_document.GetFilename())
        
    def IsPythonFile(self):
        if self.select_project_file is not None and \
                    not fileutils.is_python_file(self.select_project_file):
            return False
        return True
        
    def GetStartupFile(self,prompt_error=True):
        try:
            startup_file_path = self.startup_path_var.get()
            python_variable_manager = variablesutils.GetProjectVariableManager(self.current_project_document)
            startup_file_path = python_variable_manager.EvalulateValue(startup_file_path)
        except RuntimeError as e:
            if prompt_error:
                wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
            return None
        startup_file = self.current_project_document.GetModel().FindFile(startup_file_path)
        if not startup_file:
            if prompt_error:
                messagebox.showerror(GetApp().GetAppName(),_("File \"%s\" is not in project") % startup_file_path)
            return None
        return startup_file
        
    def RemoveFileConfigurations(self,project_file):
        if project_file is None:
            key_path = self.current_project_document.GetKey()
            utils.profile_set(key_path + "/ConfigurationList",[].__repr__())
            utils.profile_set(key_path + "/RunConfigurationName","")
            return
        config = GetApp().GetConfig()
        key_path = self.current_project_document.GetFileKey(project_file)
        names = []
        config.GetGroups(key_path,names)
        for name in names:
            group_path = key_path + "/" + name
            config.DeleteGroup(group_path)
        utils.profile_set(key_path + "/ConfigurationList",[].__repr__())
        utils.profile_set(key_path + "/RunConfigurationName","")

    def OnOK(self,optionsDialog):
        '''
            保存运行配置列表
        '''
        #when is the property of project,check the startup file
        #folder item will not get startup file
        if self.select_project_file is None and not self.is_folder:
            startup_file = self.GetStartupFile()
            if not startup_file:
                return False
            if not startup_file.IsStartup:
                item = self.current_project_document.GetFirstView()._treeCtrl.FindItem(startup_file.filePath)
                self.current_project_document.GetFirstView().SetProjectStartupFileItem(item)
        #remove all configurations first
        self.RemoveFileConfigurations(self.select_project_file)
        for run_configuration in self._configuration_list:
            run_configuration.SaveConfiguration()

        selected_item_index = self.GetSelectIndex()
        selected_configuration_name = ""
        if -1 != selected_item_index:
            selected_configuration_name = self._configuration_list[selected_item_index].Name
        if self.configuration_ListCtrl.selection():
            if self.select_project_file is None:
                pj_key = self._configuration_list[0].ProjectDocument.GetKey()
                new_configuration_names = []
                for i, run_configuration in enumerate(self._configuration_list):
                    last_part = run_configuration.GetRootKeyPath().split("/")[-1]
                    #项目运行配置名称是脚本名称加上文件的运行配置名称,中间以斜杆分割
                    new_configuration_names.append(last_part + "/" + self._configuration_list[i].Name)
                    file_configuration = runconfiguration.FileConfiguration(self.current_project_document,run_configuration.MainModuleFile)
                    file_configuration_sets = set(file_configuration.LoadConfigurationNames())
                    #use sets to avoid repeat add configuration_name
                    file_configuration_sets.add(self._configuration_list[i].Name)
                    file_configuration_list = list(file_configuration_sets)
                    pj_file_key = run_configuration.GetRootKeyPath()
                    #先保存脚本文件的运行配置列表
                    utils.profile_set(pj_file_key + "/ConfigurationList",file_configuration_list)
                    if selected_configuration_name == self._configuration_list[i].Name:
                        selected_configuration_name = last_part + "/" + selected_configuration_name
                #再保存项目的运行配置列表
                utils.profile_set(pj_key + "/ConfigurationList",new_configuration_names)
                utils.profile_set(pj_key + "/RunConfigurationName",selected_configuration_name)
            else:
                pj_file_key = self._configuration_list[0].GetRootKeyPath()
                configuration_names = [run_configuration.Name for run_configuration in self._configuration_list]
                utils.profile_set(pj_file_key + "/ConfigurationList",configuration_names)
                utils.profile_set(pj_file_key + "/RunConfigurationName",selected_configuration_name)
        if utils.is_windows():
            utils.profile_set(self.current_project_document.GetKey('IsWindowsApplication'),self._isWindowsApplicationVar.get())
        return True
        
    def SetStartupFile(self):
        dlg = pyutils.SelectModuleFileDialog(self,_("Select the startup file"),self.current_project_document.GetModel(),True)
        if constants.ID_OK == dlg.ShowModal():
            startup_path = os.path.join(variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE) , self.current_project_document.\
                    GetModel().GetRelativePath(dlg.module_file))
            self.startup_path_var.set(startup_path)
        
    def GetConfigurationName(self,default_configuration_name = None):
        if default_configuration_name is None:
            default_configuration_name = runconfiguration.RunConfiguration.DEFAULT_CONFIGURATION_NAME
        configuration_name = default_configuration_name
        i = 2
        while True:
            for run_configuration in self._configuration_list:
                if run_configuration.Name == configuration_name:
                    configuration_name = default_configuration_name + "(" + str(i)+ ")"
                    i += 1
            break
        return configuration_name
        
    def IsConfigurationNameExist(self,configuration_name,prompt_msg = True):
        for run_configuration in self._configuration_list:
            if run_configuration.Name == configuration_name:
                if prompt_msg:
                    wx.MessageBox(_("configuration name is already in used!"))
                return True
        return False
        
    def NewRunConfiguration(self):
        '''
            新建运行配置
        '''
        run_file = self.select_project_file
        if not run_file:
            run_file = self.GetStartupFile(False)
        current_interpreter = interpretermanager.InterpreterManager().GetCurrentInterpreter()
        if self.master.master.master.master.HasPanel("Interpreter"):
            interpreter_panel = self.master.master.master.master.GetOptionPanel("Interpreter")
            current_interpreter = interpreter_panel.GetInterpreter()
        run_configuration = runconfiguration.RunConfiguration.CreateNewConfiguration(self.current_project_document,current_interpreter,run_file,self.GetConfigurationName())
        init_configuration_name = run_configuration.Name
        if self.select_project_file is None:
            run_configuration.Name = "%s %s" % (self.GetProjectName(),init_configuration_name)
            if run_file is not None:
                run_configuration.Name = "%s %s" % (self.GetProjectName(),os.path.basename(run_file.filePath))
            run_configuration.Name = self.GetConfigurationName(run_configuration.Name)
            
        dlg = RunConfigurationDialog(self,_("New Configuration"),run_configuration)
        status = dlg.ShowModal()
        if constants.ID_OK == status:
            if not self.IsConfigurationNameExist(dlg.run_configuration.Name):
                item = self.configuration_ListCtrl.insert("","end",text=dlg.run_configuration.Name,image=self.run_config_img)
                self.configuration_ListCtrl.selection_set(item)
                self._configuration_list.append(dlg.run_configuration)
        
    def EditRunConfiguration(self,event=None):
        '''
            编辑运行配置
        '''
        index = self.GetSelectIndex()
        if index == -1:
            return
        run_configuration = self._configuration_list[index]
        run_configuration.IsNewConfiguration = False
        dlg = RunConfigurationDialog(self,_("Edit Configuration"),run_configuration)
        if constants.ID_OK == dlg.ShowModal():
            select_item = self.configuration_ListCtrl.selection()[0]
            self._configuration_list[index] = dlg.run_configuration
            #如果配置名称修改,更改节点名称
            if self.configuration_ListCtrl.item(select_item,"text") != dlg.run_configuration.Name:
                self.configuration_ListCtrl.item(select_item,text=dlg.run_configuration.Name)
        
    def RemoveConfiguration(self): 
        '''
            删除运行配置
        '''
        selections = self.configuration_ListCtrl.selection()
        if not selections:
            return
        item = selections[0]
        select_index = self.GetSelectIndex(item)
        self._configuration_list.remove(self._configuration_list[select_index])
        self.configuration_ListCtrl.delete(item)
        self.UpdateUI()

    def GetSelectIndex(self,item=None):
        if item is None:
            selections = self.configuration_ListCtrl.selection()
            if not selections:
                return -1
            item = selections[0]
        for i,child in enumerate(self.configuration_ListCtrl.get_children()):
            if item == child:
                return i
        return -1
        
    def CopyConfiguration(self):
        '''
            复制运行配置
        '''
        index = self.GetSelectIndex()
        if -1 == index:
            return
        run_configuration = self._configuration_list[index]
        copy_run_configuration = run_configuration.Clone()
        copy_run_configuration_name = copy_run_configuration.Name + "(copy)"
        i = 2
        while self.IsConfigurationNameExist(copy_run_configuration_name,prompt_msg=False):
            copy_run_configuration_name = copy_run_configuration.Name + "(copy%d)" % (i,)
            i += 1
        copy_run_configuration.Name = copy_run_configuration_name
        item = self.configuration_ListCtrl.insert("","end",text=copy_run_configuration.Name,image=self.run_config_img)
        self.configuration_ListCtrl.selection_set(item)
        self._configuration_list.append(copy_run_configuration)
        
    def UpdateUI(self,event=None):
        selections = self.configuration_ListCtrl.selection()
        if not selections:
            self.remove_configuration_btn["state"] = tk.DISABLED
            self.edit_configuration_btn["state"] = tk.DISABLED
            self.copy_configuration_btn["state"] = tk.DISABLED
        else:
            self.remove_configuration_btn["state"] = "normal"
            self.edit_configuration_btn["state"] = "normal"
            self.copy_configuration_btn["state"] = "normal"
            
    def LoadConfigurations(self):
        '''
            加载运行配置列表
        '''
        if self.select_project_file is not None:
            file_configuration = runconfiguration.FileConfiguration(self.current_project_document,self.select_project_file)
            self._configuration_list = file_configuration.LoadConfigurations()
            selected_configuration_name = self.current_project_document.GetRunConfiguration(self.select_project_file)
        else:
            project_configuration = runconfiguration.ProjectConfiguration(self.current_project_document)
            self._configuration_list = project_configuration.LoadConfigurations()
            selected_configuration_name = project_configuration.GetRunConfigurationName()
            
        #设置默认运行配置
        for configuration in self._configuration_list:
            item = self.configuration_ListCtrl.insert("","end",text=configuration.Name,image=self.run_config_img)
            if selected_configuration_name == configuration.Name:
                self.configuration_ListCtrl.selection_set(item)
            

