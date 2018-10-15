import wx
from noval.tool.consts import SPACE,HALF_SPACE,_,PROJECT_REFERENCE_ITEM_NAME,PYTHONPATH_ITEM_NAME
import noval.tool.images as images
import os
import noval.util.fileutils as fileutils
import wx.dataview as dataview
import noval.tool.interpreter.InterpreterManager as interpretermanager
import noval.tool.project.PythonVariables as PythonVariables
import ProjectDialog
import noval.tool.project.RunConfiguration as RunConfiguration
from noval.util import utils
import BasePanel
from noval.util.exceptions import PromptErrorException,InterpreterNotExistError
import EnvironmentMixin
      
class BasePage(wx.Panel):
    
    def __init__(self,parent,run_configuration):
        wx.Panel.__init__(self, parent)
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
        super(StartupPage,self).__init__(parent,run_configuration)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        sbox = wx.StaticBox(self, -1, _("Project") + ":")
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        projectLabelText = wx.StaticText(self, -1, _('Project Name:'))
        lineSizer.Add(projectLabelText,0,flag=wx.LEFT,border=HALF_SPACE)
        self._projectNameControl = wx.TextCtrl(self, -1,style=wx.TE_READONLY,value=self.ProjectDocument.GetModel().Name)
        lineSizer.Add(self._projectNameControl,1,flag=wx.LEFT|wx.EXPAND|wx.RIGHT|wx.BOTTOM,border=HALF_SPACE) 
        
        sboxSizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=SPACE)
        box_sizer.Add(sboxSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.BOTTOM,border = HALF_SPACE)
        
        sbox = wx.StaticBox(self, -1, _("Startup Module:"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
     
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        main_module_LabelText = wx.StaticText(self, -1, _('Main Module:'))
        lineSizer.Add(main_module_LabelText,0,flag=wx.LEFT,border=HALF_SPACE)
        self.main_module_Control = wx.TextCtrl(self, -1)
        if self.MainModuleFile is not None:
            main_module_path = self.ProjectDocument.GetModel()\
                            .GetRelativePath(self.MainModuleFile)
            main_module_path = os.path.join(PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE) , \
                                            main_module_path)
            self.main_module_Control.SetValue(main_module_path)
        lineSizer.Add(self.main_module_Control,1,flag=wx.LEFT|wx.EXPAND|wx.BOTTOM,border=HALF_SPACE) 
        self.main_module_btn = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(self.main_module_btn, -1, self.BrowseMainModule)
        lineSizer.Add(self.main_module_btn, 0,flag=wx.LEFT|wx.RIGHT, border=HALF_SPACE) 
        sboxSizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=SPACE)
        box_sizer.Add(sboxSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.BOTTOM|wx.TOP,border = HALF_SPACE)
        
        sbox = wx.StaticBox(self, -1, _("Startup Directory:"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._defaultRadioBtn = wx.RadioButton(self, -1,_("Default:"),style = wx.RB_GROUP)
        ref_radio_btn_width = self._defaultRadioBtn.GetSize().GetWidth()
        self.Bind(wx.EVT_RADIOBUTTON,self.CheckEnableStartupPath)
        lineSizer.Add(self._defaultRadioBtn,0,flag=wx.LEFT,border=HALF_SPACE)
        self.default_dirControl = wx.TextCtrl(self, -1,style=wx.TE_READONLY,value=PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE))
        lineSizer.Add(self.default_dirControl,1,flag=wx.EXPAND|wx.RIGHT,border=HALF_SPACE) 
        sboxSizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP, border=HALF_SPACE) 
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._otherRadioBtn = wx.RadioButton(self, -1,_("Other:"),size=(ref_radio_btn_width,-1))
        lineSizer.Add(self._otherRadioBtn,0,flag=wx.LEFT,border=HALF_SPACE)
        self.other_dirControl = wx.TextCtrl(self, -1)
        lineSizer.Add(self.other_dirControl,1,flag=wx.EXPAND|wx.RIGHT,border=HALF_SPACE) 
        sboxSizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP, border=HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.project_folder_btn = wx.Button(self, -1, _("Project Folder"))
        wx.EVT_BUTTON(self.project_folder_btn, -1, self.BrowseProjectFolder)
        lineSizer.Add(self.project_folder_btn, 0,flag=wx.LEFT, border=SPACE) 
        
        self.file_system_btn = wx.Button(self, -1, _("Local File System"))
        wx.EVT_BUTTON(self.file_system_btn, -1, self.BrowseLocalPath)
        lineSizer.Add(self.file_system_btn, 0,flag=wx.LEFT, border=SPACE) 
        
        self.variables_btn = wx.Button(self, -1, _("Variables"))
        wx.EVT_BUTTON(self.variables_btn, -1, self.BrowseVariables)
        lineSizer.Add(self.variables_btn, 0,flag=wx.LEFT, border=SPACE) 
        
        sboxSizer.Add(lineSizer,0,flag = wx.RIGHT|wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM,border = HALF_SPACE)
        box_sizer.Add(sboxSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)

        self.SetSizer(box_sizer)
        self.Fit()
        startup_configuration = run_configuration.GetChildConfiguration(RunConfiguration.StartupConfiguration.CONFIGURATION_NAME)
        self._startup_path_pattern = startup_configuration.StartupPathPattern
        if self._startup_path_pattern == RunConfiguration.StartupConfiguration.DEFAULT_PROJECT_DIR_PATH:
            self._defaultRadioBtn.SetValue(True)
        else:
            self._otherRadioBtn.SetValue(True)
            self.other_dirControl.SetValue(startup_configuration.StartupPath)
        self.CheckEnableStartupPath(None)
        
    def CheckEnableStartupPath(self,event):
        if self._defaultRadioBtn.GetValue():
            self.other_dirControl.Enable(False)
            self.project_folder_btn.Enable(False)
            self.file_system_btn.Enable(False)
            self.variables_btn.Enable(False)
            self._startup_path_pattern = RunConfiguration.StartupConfiguration.DEFAULT_PROJECT_DIR_PATH
        else:
            self.other_dirControl.Enable(True)
            self.project_folder_btn.Enable(True)
            self.file_system_btn.Enable(True)
            self.variables_btn.Enable(True)
            self._startup_path_pattern = RunConfiguration.StartupConfiguration.LOCAL_FILE_SYSTEM_PATH
            
    def BrowseLocalPath(self,event):
        
        dlg = wx.DirDialog(self,
                        _("Select the startup path"), 
                        style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        self._startup_path_pattern = RunConfiguration.StartupConfiguration.LOCAL_FILE_SYSTEM_PATH
        self.other_dirControl.SetValue(path)
        
    def BrowseProjectFolder(self,event):
        dlg = ProjectDialog.ProjectFolderPathDialog(self,-1,_("Select Project Folder"),self.ProjectDocument.GetModel())
        if dlg.ShowModal() == wx.ID_OK:
            selected_path = dlg.selected_path
            if selected_path is not None:
                selected_path = os.path.join(PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE) , selected_path)
            else:
                selected_path = PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE)
            self.other_dirControl.SetValue(selected_path)
            self._startup_path_pattern = RunConfiguration.StartupConfiguration.PROJECT_CHILD_FOLDER_PATH
        dlg.Destroy()
        
    def BrowseVariables(self,event):
        variable_dlg = PythonVariables.VariablesDialog(self,-1,_("Select Variable"),self.ProjectDocument)
        if variable_dlg.ShowModal() == wx.ID_OK:
            self.other_dirControl.WriteText(variable_dlg.selected_variable_name)
            self._startup_path_pattern = RunConfiguration.StartupConfiguration.EXPRESSION_VALIABLE_PATH
        variable_dlg.Destroy()
            
    def BrowseMainModule(self,event):
        dlg = ProjectDialog.SelectModuleFileDialog(self,-1,_("Select Main Module"),self.ProjectDocument.GetModel())
        if dlg.ShowModal() == wx.ID_OK:
            main_module_path = os.path.join(PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE) , self.ProjectDocument.\
                    GetModel().GetRelativePath(dlg.module_file))
            self.main_module_Control.SetValue(main_module_path)
            self.run_configuration.MainModuleFile = dlg.module_file
        dlg.Destroy()
        
    def OnOK(self):
        try:
            main_module_path = self.main_module_Control.GetValue().strip()
            python_variable_manager = PythonVariables.ProjectVariablesManager(self.ProjectDocument)
            main_module_path = python_variable_manager.EvalulateValue(main_module_path)
            
            other_startup_path = self.other_dirControl.GetValue().strip()
            other_startup_path = python_variable_manager.EvalulateValue(other_startup_path)
            
        except PromptErrorException,e:
            wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
            return False
            
        main_module_file = self.ProjectDocument.GetModel().FindFile(main_module_path)
        if not main_module_file:
            wx.MessageBox(_("Module file \"%s\" is not in project") % main_module_path)
            return False
        return True
        
    def GetConfiguration(self):
        return RunConfiguration.StartupConfiguration(self.ProjectDocument,self.MainModuleFile,\
                       self._startup_path_pattern, self.other_dirControl.GetValue().strip())
        
class ArgumentsPage(BasePage):
    def __init__(self,parent,run_configuration):
        super(ArgumentsPage,self).__init__(parent,run_configuration)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        arguments_configuration = run_configuration.GetChildConfiguration(RunConfiguration.AugumentsConfiguration.CONFIGURATION_NAME)
        
        sbox = wx.StaticBox(self, -1, _("Program Arguments:"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        linesizer = wx.BoxSizer(wx.HORIZONTAL)
        self.program_argument_textctrl = wx.TextCtrl(self, -1, value=arguments_configuration.ProgramArgs, style = wx.TE_MULTILINE,size=(-1,150))
        linesizer.Add(self.program_argument_textctrl, 1, wx.LEFT|wx.EXPAND, 0)
        sboxSizer.Add(linesizer,0,flag=wx.EXPAND|wx.ALL, border=HALF_SPACE)
        
        linesizer = wx.BoxSizer(wx.HORIZONTAL)
        self.variables_btn = wx.Button(self, -1, _("Variables"))
        wx.EVT_BUTTON(self.variables_btn, -1, self.BrowseVariables)
        linesizer.Add(self.variables_btn, 0,flag=wx.LEFT, border=SPACE) 
        sboxSizer.Add(linesizer,0,flag = wx.RIGHT|wx.ALIGN_RIGHT|wx.BOTTOM,border = HALF_SPACE)
        
        box_sizer.Add(sboxSizer,0,flag = wx.EXPAND|wx.RIGHT,border = HALF_SPACE)  

        sbox = wx.StaticBox(self, -1, _("Interpreter Options:"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        linesizer = wx.BoxSizer(wx.HORIZONTAL)
        self.interpreter_option_textctrl = wx.TextCtrl(self, -1, value=arguments_configuration.InterpreterOption, style = wx.TE_MULTILINE,size=(-1,150))
        linesizer.Add(self.interpreter_option_textctrl, 1, wx.LEFT|wx.EXPAND, 0)
        sboxSizer.Add(linesizer,0,flag=wx.EXPAND|wx.ALL, border=HALF_SPACE)
        box_sizer.Add(sboxSizer,0,flag = wx.EXPAND|wx.RIGHT,border = HALF_SPACE) 
        
        self.SetSizer(box_sizer)
        self.Fit()
        
    def BrowseVariables(self,event):
        variable_dlg = PythonVariables.VariablesDialog(self,-1,_("Select Variable"),self.ProjectDocument)
        if variable_dlg.ShowModal() == wx.ID_OK:
            self.program_argument_textctrl.WriteText(variable_dlg.selected_variable_name)
        variable_dlg.Destroy()
        
    def OnOK(self):
        try:
            arguments_text = self.program_argument_textctrl.GetValue().strip()
            python_variable_manager = PythonVariables.ProjectVariablesManager(self.ProjectDocument)
            arguments_text = python_variable_manager.EvalulateValue(arguments_text)
        except PromptErrorException,e:
            wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
            return False
        return True
        
    def GetConfiguration(self):
        main_module_file = self.GetParent().GetParent().GetMainModuleFile()
        return RunConfiguration.AugumentsConfiguration(self.ProjectDocument,main_module_file,\
                       self.interpreter_option_textctrl.GetValue(),self.program_argument_textctrl.GetValue())
        
class InterpreterConfigurationPage(BasePage):
    def __init__(self,parent,run_configuration):
        super(InterpreterConfigurationPage,self).__init__(parent,run_configuration)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.VERTICAL)
        interpreter_configuration = run_configuration.GetChildConfiguration(RunConfiguration.InterpreterConfiguration.CONFIGURATION_NAME)
        interpreter_staticLabel = wx.StaticText(self, -1, _("Interpreter:"))
        lineSizer.Add(interpreter_staticLabel, 0, wx.BOTTOM|wx.EXPAND,HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = SPACE)
        lineSizer = wx.BoxSizer(wx.VERTICAL)
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        self.interpretersCombo = wx.ComboBox(self, -1,size=(-1,-1),\
                        choices=choices, value="",style = wx.CB_DROPDOWN)
        self.Bind(wx.EVT_TEXT,self.GetInterpreterPythonPath)
        if len(choices) > 0:
            self.interpretersCombo.SetSelection(default_selection)
        
        lineSizer.Add(self.interpretersCombo, 0, wx.LEFT|wx.EXPAND,0)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT,border = SPACE)
        lineSizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer.Add(wx.StaticText(self, -1, _("PYTHONPATH that will be used in the run:")), 0, wx.BOTTOM|wx.EXPAND,HALF_SPACE)
        self.listbox = wx.ListBox(self,-1,size=(-1,300))
        lineSizer.Add(self.listbox, 1,  wx.EXPAND)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = SPACE)
        self.SetSizer(box_sizer)
        self.Fit()
        if interpreter_configuration.InterpreterName:
            self.interpretersCombo.SetValue(interpreter_configuration.InterpreterName)
        self.GetInterpreterPythonPath(None)
        
    def GetInterpreterPythonPath(self,event):
        self.listbox.Clear()
        interpreter_name = self.interpretersCombo.GetValue().strip()
        self.AppendInterpreterPythonPath(interpreter_name)
    
    def AppendInterpreterPythonPath(self,interpreter_name):
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_name)
        if interpreter is None:
            return
        self.listbox.AppendItems(interpreter.PythonPathList)
        proprty_dlg = self.GetParent().GetParent().GetParent().GetParent()
        if proprty_dlg.HasPanel(PROJECT_REFERENCE_ITEM_NAME):
            project_reference_panel = proprty_dlg.GetPanel(PROJECT_REFERENCE_ITEM_NAME)
            for reference_project in project_reference_panel.GetReferenceProjects():
                self.listbox.Append(os.path.dirname(reference_project.GetFilename()))
            python_path_panel = proprty_dlg.GetPanel(PYTHONPATH_ITEM_NAME)
            self.listbox.AppendItems(python_path_panel.GetPythonPathList())
        else:
            project_configuration = RunConfiguration.ProjectConfiguration(self.ProjectDocument)
            self.listbox.AppendItems(project_configuration.LoadProjectPythonPath())
        
    def GetConfiguration(self):
        main_module_file = self.GetParent().GetParent().GetMainModuleFile()
        return RunConfiguration.InterpreterConfiguration(self.ProjectDocument,main_module_file,\
                       self.interpretersCombo.GetValue().strip())
    
    def CheckInterpreterExist(self):
        interpreter_name = self.interpretersCombo.GetValue().strip()
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_name)
        if interpreter is None:
            raise InterpreterNotExistError(interpreter_name)
        return True
        
    def OnOK(self):
        try:
            return self.CheckInterpreterExist()
        except PromptErrorException,e:
            wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
            return False
        
class InputOutputPage(wx.Panel):
    def __init__(self,parent,dlg_id,size):
        wx.Panel.__init__(self, parent)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
class EnvironmentPage(BasePage,EnvironmentMixin.BaseEnvironmentUI):
    def __init__(self,parent,run_configuration):
        BasePage.__init__(self,parent,run_configuration)
        self.InitUI()
        self.LoadEnvironments()
        self.UpdateUI(None)
            
    def LoadEnvironments(self,):
        environs = self.run_configuration.GetChildConfiguration(RunConfiguration.EnvironmentConfiguration.CONFIGURATION_NAME).Environ
        self.dvlc.DeleteAllItems()
        for env in environs:
            self.dvlc.AppendItem([env,environs[env]])
        self.UpdateUI(None)
        
    def GetConfiguration(self):
        environ = self.GetEnviron()
        main_module_file = self.GetParent().GetParent().GetMainModuleFile()
        return RunConfiguration.EnvironmentConfiguration(self.ProjectDocument,main_module_file,\
                       environ)
        
class RunConfigurationDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,run_configuration):
        wx.Dialog.__init__(self, parent, dlg_id,title)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.current_project_document = run_configuration.ProjectDocument
        self.selected_project_file = run_configuration.MainModuleFile
        if run_configuration.IsNewConfiguration:
            st_text = wx.StaticText(self,label = _("New Debug/Run Configuration"))
        else:
            st_text = wx.StaticText(self,label = _("Edit Debug/Run Configuration"))
        st_text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        top_sizer.Add(st_text, 1,flag=wx.LEFT|wx.EXPAND,border = SPACE)  
          
        icon = wx.StaticBitmap(self,bitmap = images.load("run_wizard.png"))  
        top_sizer.Add(icon,0,flag=wx.TOP|wx.RIGHT,border = HALF_SPACE)
        box_sizer.Add(top_sizer,0,flag=wx.EXPAND|wx.ALL,border = HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        line = wx.StaticLine(self)
        lineSizer.Add(line,1,flag = wx.LEFT|wx.EXPAND,border = 0)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.BOTTOM,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        dirLabelText = wx.StaticText(self, -1, _('Name:'))
        lineSizer.Add(dirLabelText,0,flag=wx.LEFT,border=SPACE)
        self.nameControl = wx.TextCtrl(self, -1,value=run_configuration.Name)
        lineSizer.Add(self.nameControl,1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE) 
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT,border = SPACE) 
        
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.nb = wx.Notebook(self,-1,size = (600,400))
        iconList = wx.ImageList(16, 16, 4)
        
        startup_icon = images.load_icon("startup.png")
        StartupIconIndex = iconList.AddIcon(startup_icon)
        arguments_icon = images.load_icon("parameter.png")
        ArgumentsIconIndex = iconList.AddIcon(arguments_icon)
        interpreter_icon = images.load_icon("interpreter.ico")
        InterpreterIconIndex = iconList.AddIcon(interpreter_icon)
        environment_icon = images.load_icon("environment.png")
        EnvironmentIconIndex = iconList.AddIcon(environment_icon)
        self.nb.AssignImageList(iconList)
                
        count = self.nb.GetPageCount()
        self.startup_panel = StartupPage(self.nb,run_configuration)
        self.nb.AddPage(self.startup_panel, _("Startup"))
        self.nb.SetPageImage(count,StartupIconIndex)
        count = self.nb.GetPageCount()
        self.arguments_panel = ArgumentsPage(self.nb,run_configuration)
        self.nb.AddPage(self.arguments_panel, _("Arguments"))
        self.nb.SetPageImage(count,ArgumentsIconIndex)
        count = self.nb.GetPageCount()
        self.interpreter_panel = InterpreterConfigurationPage(self.nb,run_configuration)
        self.nb.AddPage(self.interpreter_panel, _("Interpreter"))
        self.nb.SetPageImage(count,InterpreterIconIndex)
        count = self.nb.GetPageCount()
        self.environment_panel = EnvironmentPage(self.nb,run_configuration)
        self.nb.AddPage(self.environment_panel, _("Environment"))
        self.nb.SetPageImage(count,EnvironmentIconIndex)
        bottom_sizer.Add(self.nb, 1, wx.ALL|wx.EXPAND, 0)
        
##        self.environment_panel = environment.EnvironmentPanel(nb)
##        nb.AddPage(self.environment_panel, _("Redirect"))
        
      ###  box_sizer.Add(top_sizer, 0, flag=wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND, border=SPACE)
        box_sizer.Add(bottom_sizer, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND,SPACE)

        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        box_sizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP,SPACE)

        self.SetSizer(box_sizer)
        self.Fit()
        
    def OnOKClick(self,event):
        if self.nameControl.GetValue().strip() == "":
            wx.MessageBox(_("A name is required for the configuration"),style = wx.OK|wx.ICON_ERROR)
            return
        for index in range(self.nb.GetPageCount()):
            panel = self.nb.GetPage(index)
            if hasattr(panel,"OnOK") and not panel.OnOK():
                return
        args = {
            RunConfiguration.StartupConfiguration.CONFIGURATION_NAME:self.startup_panel.GetConfiguration(),
            RunConfiguration.AugumentsConfiguration.CONFIGURATION_NAME:self.arguments_panel.GetConfiguration(),
            RunConfiguration.InterpreterConfiguration.CONFIGURATION_NAME:self.interpreter_panel.GetConfiguration(),
            RunConfiguration.EnvironmentConfiguration.CONFIGURATION_NAME:self.environment_panel.GetConfiguration(),
        }
        self.run_configuration = RunConfiguration.RunConfiguration(self.\
                    nameControl.GetValue().strip(),**args)
        self.EndModal(wx.ID_OK)
        
    def GetMainModuleFile(self):
        return self.startup_panel.MainModuleFile

class PyDebugRunProertyPanel(BasePanel.BasePanel):
    """description of class"""
    def __init__(self,filePropertiesService,parent,dlg_id,size,selected_item):
        BasePanel.BasePanel.__init__(self,filePropertiesService, parent, dlg_id,size,selected_item)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        self._configuration_list = []
        project_view = self.current_project_document.GetFirstView()
        self.select_project_file = None
        self.is_folder = False
        if selected_item == project_view._treeCtrl.GetRootItem():
            
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            lineSizer.Add(wx.StaticText(self, -1, _("Set the default startup file when run project.")), 0, wx.LEFT|wx.EXPAND,0)
            box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.TOP|wx.LEFT,border = SPACE)
            
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            startup_file_path = ''
            startup_file = self.current_project_document.GetModel().StartupFile
            if startup_file is not None:
                startup_file_path = self.current_project_document.GetModel()\
                            .GetRelativePath(startup_file)
                startup_file_path = os.path.join(PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE) , startup_file_path)
            self.filesCombo = wx.ComboBox(self, -1,size=(-1,-1),\
                        choices=[], value=startup_file_path,style = wx.CB_DROPDOWN)
            lineSizer.Add(self.filesCombo,1,flag=wx.LEFT|wx.EXPAND,border=SPACE)
            self.set_startup_btn = wx.Button(self, -1, _("Select the startup file"))
            lineSizer.Add(self.set_startup_btn,0,flag=wx.LEFT|wx.EXPAND|wx.RIGHT,border=HALF_SPACE)
            wx.EVT_BUTTON(self.set_startup_btn, -1, self.SetStartupFile)
            box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.TOP,border = HALF_SPACE)
        elif project_view._IsItemFile(selected_item):
            self.select_project_file = project_view._GetItemFile(selected_item)
        else:
            self.is_folder = True
            
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        manage_configuration_staticLabel = wx.StaticText(self, -1, _("You can manage launch run configurations and set default configuration as belows.\n"))
        lineSizer.Add(manage_configuration_staticLabel, 0,wx.EXPAND, 0)
        box_sizer.Add(lineSizer, 0, wx.TOP|wx.LEFT,SPACE)
            
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        configuration_staticLabel = wx.StaticText(self, -1, _("Set run configurations for project '%s':") % self.GetProjectName())
        left_sizer.Add(configuration_staticLabel, 0, wx.EXPAND,0)
        self.configuration_ListCtrl = wx.ListCtrl(self, -1, size=(-1,300),style = wx.LC_LIST)
        wx.EVT_LIST_ITEM_SELECTED(self.configuration_ListCtrl, self.configuration_ListCtrl.GetId(), self.UpdateUI)
        wx.EVT_LIST_ITEM_DESELECTED(self.configuration_ListCtrl, self.configuration_ListCtrl.GetId(), self.UpdateUI)
        wx.EVT_LIST_ITEM_ACTIVATED(self.configuration_ListCtrl, self.configuration_ListCtrl.GetId(), self.EditRunConfiguration)
        iconList = wx.ImageList(16, 16, initialCount = 1)
        run_config_bmp = images.load("runconfig.png")
        self.ConfigurationIconIndex = iconList.Add(run_config_bmp)
        self.configuration_ListCtrl.AssignImageList(iconList,wx.IMAGE_LIST_SMALL)
        left_sizer.Add(self.configuration_ListCtrl, 1, wx.TOP|wx.EXPAND,HALF_SPACE)
        lineSizer.Add(left_sizer, 1, wx.LEFT|wx.EXPAND,SPACE)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.new_configuration_btn = wx.Button(self, -1, _("New"))
        wx.EVT_BUTTON(self.new_configuration_btn, -1, self.NewRunConfiguration)
        right_sizer.Add(self.new_configuration_btn, 0, wx.TOP|wx.EXPAND, configuration_staticLabel.GetSize().GetHeight()+HALF_SPACE)
        
        self.edit_configuration_btn = wx.Button(self, -1, _("Edit"))
        wx.EVT_BUTTON(self.edit_configuration_btn, -1, self.EditRunConfiguration)
        right_sizer.Add(self.edit_configuration_btn, 0, wx.TOP|wx.EXPAND, HALF_SPACE)
        
        self.remove_configuration_btn = wx.Button(self, -1, _("Remove"))
        wx.EVT_BUTTON(self.remove_configuration_btn, -1, self.RemoveConfiguration)
        right_sizer.Add(self.remove_configuration_btn, 0, wx.TOP|wx.EXPAND, HALF_SPACE)
        
        self.copy_configuration_btn = wx.Button(self, -1, _("Copy"))
        wx.EVT_BUTTON(self.copy_configuration_btn, -1, self.CopyConfiguration)
        right_sizer.Add(self.copy_configuration_btn, 0, wx.TOP|wx.EXPAND, HALF_SPACE)
        lineSizer.Add(right_sizer, 0, wx.LEFT|wx.EXPAND,SPACE)
        box_sizer.Add(lineSizer,1,flag = wx.EXPAND|wx.RIGHT,border = HALF_SPACE)
        self.SetSizer(box_sizer)
        #should use Layout ,could not use Fit method
        #disable all buttons when file is not python file or is folder
        if not self.IsPythonFile() or self.is_folder:
            self.edit_configuration_btn.Enable(False)
            self.remove_configuration_btn.Enable(False)
            self.new_configuration_btn.Enable(False)
            self.copy_configuration_btn.Enable(False)
        self.Layout()
        self.UpdateUI(None)
        #folder or package folder has no run configurations
        if not self.is_folder:
            self.LoadConfigurations()
        
    def IsPythonFile(self):
        if self.select_project_file is not None and \
                    not fileutils.is_python_file(self.select_project_file.filePath):
            return False
        return True
        
    def GetStartupFile(self,prompt_error=True):
        try:
            startup_file_path = self.filesCombo.GetValue().strip()
            python_variable_manager = PythonVariables.ProjectVariablesManager(self.current_project_document)
            startup_file_path = python_variable_manager.EvalulateValue(startup_file_path)
        except PromptErrorException,e:
            if prompt_error:
                wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
            return None
        startup_file = self.current_project_document.GetModel().FindFile(startup_file_path)
        if not startup_file:
            if prompt_error:
                wx.MessageBox(_("File \"%s\" is not in project") % startup_file_path)
            return None
        return startup_file
        
    def RemoveFileConfigurations(self,project_file):
        if project_file is None:
            key_path = self.current_project_document.GetKey()
            utils.ProfileSet(key_path + "/ConfigurationList",[].__repr__())
            utils.ProfileSet(key_path + "/RunConfigurationName","")
            return
        config = wx.ConfigBase_Get()
        key_path = self.current_project_document.GetFileKey(project_file)
        config.SetPath(key_path)
        more, value, index = config.GetFirstGroup()
        names = []
        while more:
            names.append(value)
            more, value, index = wx.ConfigBase_Get().GetNextGroup(index)
        for name in names:
            group_path = key_path + "/" + name
            config.DeleteGroup(group_path)
        utils.ProfileSet(key_path + "/ConfigurationList",[].__repr__())
        utils.ProfileSet(key_path + "/RunConfigurationName","")

    def OnOK(self,optionsDialog):
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
        #then save new configurations
        configuration_names = []
        for run_configuration in self._configuration_list:
            run_configuration.SaveConfiguration()
            configuration_names.append(run_configuration.Name)
            
        selected_item_index = self.configuration_ListCtrl.GetFirstSelected()
        selected_configuration_name = ""
        if -1 != selected_item_index:
            selected_configuration_name = configuration_names[selected_item_index]
            
        if len(configuration_names) > 0:
            if self.select_project_file is None:
                pj_key = self._configuration_list[0].ProjectDocument.GetKey()
                new_configuration_names = []
                for i, run_configuration in enumerate(self._configuration_list):
                    last_part = run_configuration.GetRootKeyPath().split("/")[-1]
                    new_configuration_names.append(last_part + "/" + configuration_names[i])
                    
                    file_configuration = RunConfiguration.FileConfiguration(self.current_project_document,run_configuration.MainModuleFile)
                    file_configuration_sets = set(file_configuration.LoadConfigurationNames())
                    #use sets to avoid repeat add configuration_name
                    file_configuration_sets.add(configuration_names[i])
                    file_configuration_list = list(file_configuration_sets)
                    pj_file_key = run_configuration.GetRootKeyPath()
                    #update file configuration list
                    utils.ProfileSet(pj_file_key + "/ConfigurationList",file_configuration_list.__repr__())
                    if selected_configuration_name == configuration_names[i]:
                        selected_configuration_name = last_part + "/" + selected_configuration_name
                utils.ProfileSet(pj_key + "/ConfigurationList",new_configuration_names.__repr__())
                utils.ProfileSet(pj_key + "/RunConfigurationName",selected_configuration_name)
            else:
                pj_file_key = self._configuration_list[0].GetRootKeyPath()
                utils.ProfileSet(pj_file_key + "/ConfigurationList",configuration_names.__repr__())
                utils.ProfileSet(pj_file_key + "/RunConfigurationName",selected_configuration_name)
        return True
        
    def SetStartupFile(self,event):
        dlg = ProjectDialog.SelectModuleFileDialog(self,-1,_("Select the startup file"),\
                    self.current_project_document.GetModel(),True)
        if wx.ID_OK == dlg.ShowModal():
            startup_path = os.path.join(PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE) , self.current_project_document.\
                    GetModel().GetRelativePath(dlg.module_file))
            self.filesCombo.SetValue(startup_path)
        dlg.Destroy()
        
    def GetConfigurationName(self,default_configuration_name = None):
        if default_configuration_name is None:
            default_configuration_name = RunConfiguration.RunConfiguration.DEFAULT_CONFIGURATION_NAME
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
        
    def NewRunConfiguration(self,event):
        run_file = self.select_project_file
        if not run_file:
            run_file = self.GetStartupFile(False)
        run_configuration = RunConfiguration.RunConfiguration.CreateNewConfiguration(self.current_project_document,run_file,self.GetConfigurationName())
        init_configuration_name = run_configuration.Name
        if self.select_project_file is None:
            run_configuration.Name = "%s %s" % (self.GetProjectName(),init_configuration_name)
            if run_file is not None:
                run_configuration.Name = "%s %s" % (self.GetProjectName(),self.GetProjectFilename(run_file))
            run_configuration.Name = self.GetConfigurationName(run_configuration.Name)
            
        dlg = RunConfigurationDialog(self,-1,_("New Configuration"),run_configuration)
        status = dlg.ShowModal()
        passedCheck = False
        while wx.ID_OK == status and not passedCheck:
            if not self.IsConfigurationNameExist(dlg.run_configuration.Name):
                index = self.configuration_ListCtrl.GetItemCount()
                self.configuration_ListCtrl.InsertImageStringItem( index,dlg.run_configuration.Name,self.ConfigurationIconIndex)
                self.configuration_ListCtrl.SetItemData(index,index)
                self._configuration_list.append(dlg.run_configuration)
                passedCheck = True
            else:
                status = dlg.ShowModal()
        dlg.Destroy()
        
    def EditRunConfiguration(self,event):
        select_item = self.configuration_ListCtrl.GetFirstSelected()
        index = self.configuration_ListCtrl.GetItemData(select_item)
        run_configuration = self._configuration_list[index]
        dlg = RunConfigurationDialog(self,-1,_("Edit Configuration"),run_configuration)
        if wx.ID_OK == dlg.ShowModal():
            self._configuration_list[index] = dlg.run_configuration
            if self.configuration_ListCtrl.GetItemText(select_item,0) != dlg.run_configuration.Name:
                self.configuration_ListCtrl.SetItemText(select_item,dlg.run_configuration.Name)
        dlg.Destroy()
        
    def RemoveConfiguration(self,event):
        select_index = self.configuration_ListCtrl.GetFirstSelected()
        self.configuration_ListCtrl.DeleteItem(select_index)
        self._configuration_list.remove(self._configuration_list[select_index])
        self.UpdateItemData()
        self.UpdateUI(None)
        
    def UpdateItemData(self):
        assert(self.configuration_ListCtrl.GetItemCount() == len(self._configuration_list))
        for i in range(self.configuration_ListCtrl.GetItemCount()):
            self.configuration_ListCtrl.SetItemData(i,i)
        
    def CopyConfiguration(self,event):
        select_item = self.configuration_ListCtrl.GetFirstSelected()
        index = self.configuration_ListCtrl.GetItemData(select_item)
        run_configuration = self._configuration_list[index]
        copy_run_configuration = run_configuration.Clone()
        copy_run_configuration_name = copy_run_configuration.Name + "(copy)"
        i = 2
        while self.IsConfigurationNameExist(copy_run_configuration_name,prompt_msg=False):
            copy_run_configuration_name = copy_run_configuration.Name + "(copy%d)" % (i,)
            i += 1
        copy_run_configuration.Name = copy_run_configuration_name
        index = self.configuration_ListCtrl.GetItemCount()
        self.configuration_ListCtrl.InsertImageStringItem( index,copy_run_configuration.Name,self.ConfigurationIconIndex)
        self.configuration_ListCtrl.SetItemData(index,index)
        self._configuration_list.append(copy_run_configuration)
        
    def UpdateUI(self,event):
        select_item = self.configuration_ListCtrl.GetFirstSelected()
        if select_item == -1:
            self.remove_configuration_btn.Enable(False)
            self.edit_configuration_btn.Enable(False)
            self.copy_configuration_btn.Enable(False)
        else:
            self.remove_configuration_btn.Enable(True)
            self.edit_configuration_btn.Enable(True)
            self.copy_configuration_btn.Enable(True)
            
    def LoadConfigurations(self):
        if self.select_project_file is not None:
            file_configuration = RunConfiguration.FileConfiguration(self.current_project_document,self.select_project_file)
            self._configuration_list = file_configuration.LoadConfigurations()
            selected_configuration_name = self.current_project_document.GetRunConfiguration(self.select_project_file)
        else:
            project_configuration = RunConfiguration.ProjectConfiguration(self.current_project_document)
            self._configuration_list = project_configuration.LoadConfigurations()
            selected_configuration_name = project_configuration.GetRunConfigurationName()
            
        for configuration in self._configuration_list:
            index = self.configuration_ListCtrl.GetItemCount()
            self.configuration_ListCtrl.InsertImageStringItem( index,configuration.Name,self.ConfigurationIconIndex)
            self.configuration_ListCtrl.SetItemData(index,index)
            if selected_configuration_name == configuration.Name:
                self.configuration_ListCtrl.Select(index)
            