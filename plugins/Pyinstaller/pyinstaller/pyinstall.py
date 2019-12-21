
__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: calc.py 850 2009-05-01 00:24:27Z CodyPrecord $"
__revision__ = "$Revision: 850 $"

#--------------------------------------------------------------------------#
# Dependancies
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from noval import _,NewId
import noval.util.utils as utils
import noval.project.wizard as projectwizard
from noval.project.baseconfig import *
from noval.python.project.viewer import *
from noval.python.project.model import *
from noval.python.project.rundocument import *
import noval.consts as consts
import noval.imageutils as imageutils
import os
import noval.util.strutils as strutils
import noval.util.fileutils as fileutils
import noval.python.parser.utils as parserutils
from noval.project.executor import *
import noval.terminal as terminal
import noval.misc as misc
import noval.python.interpreter.pythonpackages as pythonpackages
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.ui_utils as ui_utils
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.toolbar as toolbar
import noval.ui_base as ui_base
import noval.python.project.runconfiguration as runconfiguration
import noval.project.command as command
import noval.python.pyutils as pyutils
from pkg_resources import resource_filename
import datetime


if utils.is_py2():
    from noval.util.which import which
elif utils.is_py3_plus():
    from shutil import which

def SetVariablevar(variable):
    path = filedialog.askdirectory()
    if path:
        path = fileutils.opj(path)
        variable.set(path)
        
def GetInterpreterScriptPath(interpreter,is_user_site=False):
    if is_user_site:
        interpreter_path = os.path.dirname(interpreter.GetUserLibPath())
    else:
        interpreter_path = interpreter.InstallPath
    return os.path.join(interpreter_path,"Scripts")
    
def GetToolPath(interpreter,name,is_user_site=False):
    if utils.is_windows():
        return os.path.join(GetInterpreterScriptPath(interpreter,is_user_site),name + ".exe")
    return which(name)

def GetPyinstallerToolPath(interpreter):
    pyinstaller_tool_path = GetToolPath(interpreter,"pyinstaller")
    if not os.path.exists(pyinstaller_tool_path):
        print (interpreter.GetUserLibPath(),"=========")
        pyinstaller_tool_path = GetToolPath(interpreter,"pyinstaller",is_user_site=True)
        if not os.path.exists(pyinstaller_tool_path): 
            raise RuntimeError(_("interpreter %s need to install package \"pyinstaller\"")%interpreter.Name)
    return pyinstaller_tool_path

def GetPyinstallerMakeToolPath(interpreter):
    pyinstallermake_tool_path = GetToolPath(interpreter,"pyi-makespec")
    if not os.path.exists(pyinstallermake_tool_path):
        pyinstallermake_tool_path = GetToolPath(interpreter,"pyi-makespec",is_user_site=True)
    return pyinstallermake_tool_path

def CheckPyinstaller(interpreter,parent=None):
    try:
        GetPyinstallerToolPath(interpreter)
    except RuntimeError as e:
        messagebox.showinfo(GetApp().GetAppName(),str(e),parent=parent)
        dlg = pythonpackages.InstallPackagesDialog(parent,interpreter,pkg_name='pyinstaller',install_args='--user pyinstaller',autorun=True)
        status = dlg.ShowModal()
        if status == constants.ID_CANCEL:
            return False
    return True

class ApplicationInformationConfiguration(runconfiguration.BaseConfiguration):
    """description of class"""
    CONFIGURATION_NAME = 'ApplicationInformation'
    
    def __init__(self,project_doc,main_module_file=None,**kwargs):
        super(ApplicationInformationConfiguration,self).__init__(project_doc,main_module_file)
        self.args = kwargs
        
    def SaveConfiguration(self,config_key,configuration_name):
        configuration_key = self.GetConfigurationKey(configuration_name,config_key)


class SpecOptionConfiguration(runconfiguration.BaseConfiguration):
    """description of class"""
    CONFIGURATION_NAME = 'SpecOption'
    
    def __init__(self,project_doc,main_module_file=None,**kwargs):
        super(SpecOptionConfiguration,self).__init__(project_doc,main_module_file)
        self.args = kwargs
        
    def SaveConfiguration(self,**kwargs):
        file_key_path = self.GetRootKeyPath()
        for key,value in kwargs.items():
            utils.profile_set(file_key_path + "/" + key,value)

class DatafilesConfiguration(runconfiguration.BaseConfiguration):
    """description of class"""
    CONFIGURATION_NAME = 'Datafiles'
    
    def __init__(self,project_doc,main_module_file=None,data_files=[]):
        super(DatafilesConfiguration,self).__init__(project_doc,main_module_file)
        
    def SaveConfiguration(self,config_key,configuration_name):
        configuration_key = self.GetConfigurationKey(configuration_name,config_key)
        utils.profile_set(configuration_key + "/Datafiles",self._startup_path_pattern)

class PyinstallerRunconfig(BaseRunconfig):
    def __init__(self,interpreter,file_path,arg='',env=None,start_up=None,project=None):
        self._interpreter = interpreter
        self._project = project
        self.filepath = file_path
        self.file_name = os.path.basename(file_path)
        self._interpreter = self._project.GetandSetProjectDocInterpreter()
        CheckPyinstaller(interpreter)
        pyinstaller_tool_path = GetPyinstallerToolPath(self._interpreter)
        spec_path = self.GetSpecfilePath(file_path)
        args = spec_path
        main_module_file = self._project.GetModel().FindFile(file_path)
        clean = utils.profile_get_int(self._project.GetFileKey(main_module_file) + "/CleanBuild",False)
        ask = utils.profile_get_int(self._project.GetFileKey(main_module_file) + "/AskReplace",False)
        log_level = utils.profile_get(self._project.GetFileKey(main_module_file) + "/LogLevel","INFO")
        make_single = utils.profile_get_int(self._project.GetFileKey(main_module_file) + "/MakeSingleExe",False)
        if clean:
            args += " --clean"
            
        if not ask:
            args += " -y"
        if log_level:
            args += " --log-level " + log_level
        
        if make_single:
            args += " -F"
        else:
            args += " -D"
            
        if utils.profile_get_int(self._project.GetKey('IsWindowsApplication'),False):
            args += " -w"
        else:
            args += " -c"
            
        character_set = utils.profile_get_int(self._project.GetFileKey(main_module_file) + "/Character",PyinstallerBaseInformationPanel.CHARACTER_NOTSET)
        if PyinstallerBaseInformationPanel.CHARACTER_ASCII == character_set:
            args += " -a"
        BaseRunconfig.__init__(self,pyinstaller_tool_path,args,env,start_up,project)

    @property
    def Interpreter(self):
        return self._interpreter

    def GetSpecfilePath(self,file_name=None):
        if file_name is None:
            file_name = os.path.basename(self.Project.GetStartupFile().filePath)
        main_module_file = self._project.GetModel().FindFile(file_name)
        default_spec_filepath = self._project.GetDefaultSpecfilePath(file_name)
        spec_file_path = utils.profile_get(self._project.GetFileKey(main_module_file) + "/SpecFilePath",default_spec_filepath)
        if not os.path.exists(default_spec_filepath):
            self.GenerateSepcFile(file_name)
        return spec_file_path

    def GenerateSepcFile(self,file_name):
        pyinstallermake_tool_path = GetPyinstallerMakeToolPath(self._interpreter)
        args = " %s"%file_name
        project_path = self._project.GetPath()
        utils.create_process(pyinstallermake_tool_path,args,cwd=project_path)

class PyinstallerProject(PythonProject):
    def __init__(self):
        super(PyinstallerProject,self).__init__()
        self._runinfo.DocumentTemplate = "pyinstaller.pyinstall.PyinstallerProjectTemplate"

class PyinstallerProjectDocument(PythonProjectDocument):

    def __init__(self, model=None):
        ProjectDocument.__init__(self,model)
        
    @staticmethod
    def GetProjectModel():
        return PyinstallerProject()

    def CheckIsbuiltinInterpreter(self,run_parameter):
        if run_parameter.Interpreter.IsBuiltIn:
            raise RuntimeError(_('Builtin Interpreter is not support to run pyinstaller project'))

    def Build(self):
        ''''''
        pyinstaller_run_parameter = self.GetPyinstallerRunParameter()
        if pyinstaller_run_parameter is None:
            return
        self.BuildDebugIndebugger(pyinstaller_run_parameter,finish_stopped=True)
        
    def Rebuild(self):
        ''''''
        pyinstaller_run_parameter = self.GetPyinstallerRunParameter()
        if pyinstaller_run_parameter is None:
            return
        if pyinstaller_run_parameter.Arg.find(" --clean") == -1:
            pyinstaller_run_parameter.Arg += " --clean"
        self.BuildDebugIndebugger(pyinstaller_run_parameter,finish_stopped=True)

    def GetDefaultSpecfilePath(self,file_path):
        spec_file_path = os.path.join(self.GetPath(),strutils.get_filename_without_ext(os.path.basename(file_path)) + ".spec")
        return spec_file_path

    def GetTargetDir(self,pyinstaller_run_parameter):
        return os.path.dirname(self.GetTargetPath(pyinstaller_run_parameter)[0])
        
    def GetTargetPath(self,pyinstaller_run_parameter):
        project_path = self.GetPath()
        dist_path = os.path.join(project_path,'dist')
        main_module_file = self.GetModel().FindFile(pyinstaller_run_parameter.filepath)
        make_single = utils.profile_get_int(self.GetFileKey(main_module_file) + "/MakeSingleExe",False)
        if utils.is_windows():
            target_name = "%s.exe"%strutils.get_filename_without_ext(pyinstaller_run_parameter.file_name)
        else:
            target_name = "%s"%strutils.get_filename_without_ext(pyinstaller_run_parameter.file_name)
        if not make_single:
            dist_project_path = os.path.join(dist_path,strutils.get_filename_without_ext(pyinstaller_run_parameter.file_name))
            target_exe_path = os.path.join(dist_project_path,target_name)
        else:
            target_exe_path = os.path.join(dist_path,target_name)
        return target_exe_path,make_single
    
    def BuildRunterminal(self,run_parameter):
        self.CheckIsbuiltinInterpreter(run_parameter)
        executor = TerminalExecutor(run_parameter)
        command1 = executor.GetExecuteCommand()
        target_exe_path = self.GetTargetPath(run_parameter)[0]
        print ('run target exe path',target_exe_path,'in terminal')
        run_parameter = BaseRunconfig(target_exe_path)
        executor = TerminalExecutor(run_parameter)
        command2 = executor.GetExecuteCommand()

        command = command1 + " && " +  command2
        
        utils.get_logger().debug("start run executable: %s in terminal",command)
        startIn = executor.GetStartupPath()
        terminal.run_in_terminal(command,startIn,os.environ,keep_open=False,pause=True,title="abc")

    def GetPyinstallerRunParameter(self,filetoRun=None):
        python_run_parameter = PythonProjectDocument.GetRunParameter(self,filetoRun)
        if python_run_parameter is None:
            return None
            
        pyinstaller_run_parameter = PyinstallerRunconfig(python_run_parameter.Interpreter,python_run_parameter.FilePath,'',python_run_parameter.Environment,python_run_parameter.StartupPath,python_run_parameter.Project)
        return pyinstaller_run_parameter

    def RunIndebugger(self):
        pyinstaller_run_parameter = self.GetPyinstallerRunParameter()
        if pyinstaller_run_parameter is None:
            return
        self.BuildDebugIndebugger(pyinstaller_run_parameter)

    def RunInterminal(self,filetoRun=None):
        pyinstaller_run_parameter = self.GetPyinstallerRunParameter(filetoRun)
        if pyinstaller_run_parameter is None:
            return
        self.BuildRunterminal(pyinstaller_run_parameter)

    def RunTarget(self,run_parameter):
        target_exe_path = self.GetTargetPath()
        
    def DebugRunTarget(self,run_parameter):
        target_exe_path = self.GetTargetPath()

    def BuildDebugIndebugger(self,run_parameter,finish_stopped=False):
        self.CheckIsbuiltinInterpreter(run_parameter)
        fileToRun = run_parameter.filepath
        shortFile = os.path.basename(fileToRun)
        view = GetApp().MainFrame.GetCommonView("Output")
        view.SetRunParameter(run_parameter)
        view.GetOutputview().SetTraceLog(True)
        view.CreateExecutor(source="Build",finish_stopped=finish_stopped)
        view.EnableToolbar()
        view.Execute()
        
    def CleanBuilddir(self):
        project_path = self.GetPath()
        build_dir = os.path.join(project_path,'build')
        self.Cleandir(build_dir)
        
    def CleanOutput(self):
        pyinstaller_run_parameter = self.GetPyinstallerRunParameter()
        target_exe_path,make_single = self.GetTargetPath(pyinstaller_run_parameter)
        utils.get_logger().info('target path is %s----------',target_exe_path)
        if make_single:
            self.Cleanfile(target_exe_path)
        else:
            self.Cleandir(self.GetTargetDir(pyinstaller_run_parameter))

    def CleanProject(self):
        PythonProjectDocument.CleanProject(self)
        self.CleanBuilddir()
        self.CleanOutput()

class PyinstallerProjectTemplate(PythonProjectTemplate):
    
    @staticmethod
    def CreateProjectTemplate():
        projectTemplate = PyinstallerProjectTemplate(GetApp().GetDocumentManager(),
                _("Project File"),
                "*%s" % consts.PROJECT_EXTENSION,
                os.getcwd(),
                consts.PROJECT_EXTENSION,
                "PyinstallerProject Document",
                _("PyinstallerProject Viewer"),
                PyinstallerProjectDocument,
                PythonProjectView,
                icon = imageutils.getProjectIcon())
        GetApp().GetDocumentManager().DisassociateTemplate(projectTemplate)
        return projectTemplate
        
    def GetPropertiPages(self):
        return PythonProjectTemplate.GetPropertiPages(self) + [("Application information","file","pyinstaller.pyinstall.PyinstallerBaseInformationPanel"),\
                ("Spec option","file","pyinstaller.pyinstall.PyinstallSpecOptionPanel"),("Data files","file","pyinstaller.pyinstall.PyinstallDatafilesPanel")]

class PyinstallerProjectNameLocationPage(BasePythonProjectNameLocationPage):

    def __init__(self,master,**kwargs):
        BasePythonProjectNameLocationPage.__init__(self,master,**kwargs)
        self.can_finish = False

    def GetProjectTemplate(self):
        return PyinstallerProjectTemplate.CreateProjectTemplate()
        

class PyinstallerSimpleDemoNameLocationPage(PyinstallerProjectNameLocationPage):
    
    demo_code = '''import argparse

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

if __name__ == "__main__":
    main()

'''
    def __init__(self,master,**kwargs):
        PyinstallerProjectNameLocationPage.__init__(self,master,**kwargs)
        self.name_var.trace("w", self.SetPyinstallProjectStartuppath)
        
    def SetPyinstallProjectStartuppath(self,*args):
        self.startup_path_var.set("${ProjectDir}/%s.py"%self.name_var.get().strip())
        
    def Finish(self):
        if not PyinstallerProjectNameLocationPage.Finish(self):
            return False
        dirName = self.GetProjectLocation()
        view = GetApp().MainFrame.GetProjectView().GetView()
        startup_file_path = fileutils.opj(self.GetStartupfile())
        with open(startup_file_path,"w") as f:
            f.write(self.demo_code)
        self.new_project_doc.GetCommandProcessor().Submit(command.ProjectAddFilesCommand(self.new_project_doc,[startup_file_path],None))
        view.SetProjectStartupFile()
        return True
    
class PyinstallerBaseInformationPanel(pyutils.PythonBaseConfigurationPanel):
    
    CHARACTER_NOTSET = 0
    CHARACTER_ASCII = 1
    CHARACTER_UNICODE = 2
    def __init__(self,parent,item,current_project,**kwargs):
        pyutils.PythonBaseConfigurationPanel.__init__(self,parent,current_project)
        self.columnconfigure(1, weight=1)
        self.current_project = current_project
        self.item = item
        self.is_windows = kwargs.get('is_windows',False)
        row_index = 0
        if item is None:
             root_file_key = "xxxxxxxx..."
        else:
            main_module_file = self.GetItemFile(item)
            root_file_key = self.GetCurrentProject().GetFileKey(main_module_file)
        
        ttk.Label(self,text=_('Application target name:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.target_name_var = tk.StringVar(value=utils.profile_get(root_file_key + "/TargetName"))
        target_entry = ttk.Entry(self,textvariable=self.target_name_var)
        misc.create_tooltip(target_entry,_("The executable name of application (default: script's basename)"))
        target_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))

        row_index += 1
        ttk.Label(self, text=_('Application icon path:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.icon_path_var = tk.StringVar(value=utils.profile_get(root_file_key + "/IconPath"))
        icon_path_entry = ttk.Entry(self,textvariable=self.icon_path_var)
        icon_path_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        ttk.Button(self, text= _("Browse..."),command=self.SetIconPath).grid(column=2, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))

        row_index += 1 
        ttk.Label(self,text=_('Output folder name:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.output_folder_var = tk.StringVar(value=utils.profile_get(root_file_key + "/OutputFolder"))
        self.output_folder_entry = ttk.Entry(self,textvariable=self.output_folder_var)
        misc.create_tooltip(self.output_folder_entry,_("Specify the folder name when create a one-folder bundle containing an executable (default: script's basename)"))
        self.output_folder_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        
        row_index += 1 
        ttk.Label(self,text=_('Character Set:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.character_sets = ('Not Set','Use Ascii Character Set','Use Unicode Character Set')
        self.character_var = tk.StringVar(value=self.character_sets[utils.profile_get_int(root_file_key + "/Character",self.CHARACTER_NOTSET)])
        character_entry = ttk.Combobox(self,textvariable=self.character_var,values=self.character_sets,state="readonly")
        misc.create_tooltip(character_entry,"The unicode encoding support (default: included if available)")
        character_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        
        row_index += 1 
        frame = ttk.Frame(self)
        frame.grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=3)
        
        self.work_default_var = tk.BooleanVar(value=utils.profile_get_int(root_file_key + "/UseDefaultWork",True))
        sbox = ttk.LabelFrame(frame, text=_("Work directory:"))
        ttk.Checkbutton(sbox,text=_('Use Default'),variable=self.work_default_var,command=self.SetDefaultWorkpath).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        
        ttk.Label(sbox, text=_('Path:')).pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.work_path_var = tk.StringVar(value="./build")
        self.work_path_entry = ttk.Entry(sbox,textvariable=self.work_path_var)
        self.work_path_entry.pack(side=tk.LEFT,fill="x",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        misc.create_tooltip(self.work_path_entry,_('Where to put all the temporary work files, .log, .pyz and etc. (default: ./build)'))
        self.work_default_btn = ttk.Button(sbox, text= _("Browse..."),command=self.SetWorkPath)
        self.work_default_btn.pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        sbox.pack(fill="x")
        
        self.output_default_var = tk.BooleanVar(value=utils.profile_get_int(root_file_key + "/UseDefaultDist",True))
        sbox = ttk.LabelFrame(frame, text=_("Dist directory:"))
        ttk.Checkbutton(sbox,text=_('Use Default'),variable=self.output_default_var,command=self.SetDefaultDistpath).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        ttk.Label(sbox, text=_('Path:')).pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.dist_path_var = tk.StringVar(value="./dist")
        self.dist_path_entry = ttk.Entry(sbox,textvariable=self.dist_path_var)
        self.dist_path_entry.pack(side=tk.LEFT,fill="x",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        misc.create_tooltip(self.dist_path_entry,_('Where to put the bundled app (default: ./dist)'))
        self.dist_default_btn = ttk.Button(sbox, text= _("Browse..."),command=self.SetDistPath)
        self.dist_default_btn.pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        sbox.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        row_index += 1 
        self.make_single_var = tk.BooleanVar(value=utils.profile_get_int(root_file_key + "/MakeSingleExe",False))
        check_single_btn = ttk.Checkbutton(self,text=_('Make a single exetuable file'),variable=self.make_single_var,command=self.SetSingleFile)
        check_single_btn.grid(column=0, row=row_index, sticky="nsew",columnspan=2,pady=consts.DEFAUT_CONTRL_PAD_Y)
        self.SetDefaultWorkpath()
        self.SetDefaultDistpath()
        self.DisableNoPythonfile(item)
        
    def SetIconPath(self):
        descr = (_("Icon File"),'.ico')
        path = filedialog.askopenfilename(
                master=self,
                filetypes=[descr]
        )
        if not path:
            return
        self.icon_path_var.set(fileutils.opj(path))
        
    def SetWorkPath(self):
        SetVariablevar(self.work_path_var)
        
    def SetDistPath(self):
        SetVariablevar(self.dist_path_var)
        
    def SetDefaultWorkpath(self):
        if self.work_default_var.get():
            self.work_path_entry['state'] = tk.DISABLED
            self.work_default_btn['state'] = tk.DISABLED
        else:
            self.work_path_entry['state'] = tk.NORMAL
            self.work_default_btn['state'] = tk.NORMAL
        
    def SetDefaultDistpath(self):
        if self.output_default_var.get():
            self.dist_path_entry['state'] = tk.DISABLED
            self.dist_default_btn['state'] = tk.DISABLED
        else:
            self.dist_path_entry['state'] = tk.NORMAL
            self.dist_default_btn['state'] = tk.NORMAL
            
    def SetSingleFile(self):
        if self.make_single_var.get():
            self.output_folder_entry['state'] = tk.DISABLED
        else:
            self.output_folder_entry['state'] = tk.NORMAL
            
    def OnOK(self,optionsDialog=None):
        interpreter = self.GetInterpreter()
        if not CheckPyinstaller(interpreter,parent=self) or interpreter is None:
            return False
        target_name = self.target_name_var.get()
        output_folder = self.output_folder_var.get()
        character = self.character_var.get()
        self.work_default_var.get()
        self.dist_path_var.get()
        pyinstallermake_tool_path = GetPyinstallerMakeToolPath(interpreter)
        icon_path = self.icon_path_var.get().strip()
        args = ""
        if icon_path:
            args += " -i %s"%icon_path
            
        option_panel = self.GetOptionPanel()
        spec_name = option_panel.spec_name_var.get()
        if spec_name:
            args += " -n %s"%spec_name
            
        spec_path = option_panel.spec_path_var.get()
        if spec_path:
            args += " --specpath %s"%spec_path
            
        if self.IsSpecExist():
            ret = messagebox.askyesno(_("Spec file exist"),_("Spec file already exist in spec path,Do you want to replace it?"),parent=self)
            if not ret:
                utils.profile_set(self.GetCurrentProject().GetFileKey(self.GetStartupfile(),'SpecFilePath'),self.GetSpecfilePath())
                return True
            
        if option_panel.hidden_imports_var.get().strip():
            hidden_imports = option_panel.hidden_imports_var.get().split(",")
            for hidden_import in hidden_imports:
                args += " --hidden-import %s"%hidden_import
        if self.make_single_var.get():
            args += " -F"
        else:
            args += " -D"
            
        if not option_panel.upx_var.get():
            args += " --noupx"
            
        if self.is_windows:
            args += " -w"
        else:
            args += " -c"
            
        if option_panel.debug_var.get():
            args += " -d all"
            
        log_level = option_panel.log_level_var.get()
        args += " --log-level %s"%log_level
        version_file = self.GetVersionFile()
        if version_file:
            args += " --version-file %s"%version_file
        
        datafiles_panel = self.GetDatafilesPanel()
        if datafiles_panel is not None:
            data_files = datafiles_panel.GetFiles()
            for data_file in data_files:
                args += " --add-data %s;%s"%(data_file[0],data_file[1])
                    
        startup_file_path = self.GetStartupfile()
        args += " %s"%os.path.basename(startup_file_path)
        project_path = self.GetProjectPath()
        utils.create_process(pyinstallermake_tool_path,args,cwd=project_path)
        self.SaveSettings()
        return True
        
    def SaveSettings(self):
        current_project = self.GetCurrentProject()
        startup_file_path = self.GetStartupfile()
        option_panel = self.GetOptionPanel()
        startup_file = current_project.GetModel().FindFile(startup_file_path)
        config = SpecOptionConfiguration(current_project,startup_file)
        options = {
            'TargetName':self.target_name_var.get(),
            'IconPath':self.icon_path_var.get(),
            'OutputFolder':self.output_folder_var.get(),
            'Character':self.character_sets.index(self.character_var.get()),
            'UseDefaultWork':self.work_default_var.get(),
            'UseDefaultDist':self.output_default_var.get(),
            'WorkPath':self.work_path_var.get(),
            'DistPath':self.dist_path_var.get(),
            'MakeSingleExe':self.make_single_var.get(),
            'HiddenImports':option_panel.hidden_imports_var.get(),
            'FileVersion':option_panel.file_version_var.get(),
            'ProductVersion':option_panel.product_version_var.get(),
            'LogLevel':option_panel.log_level_var.get(),
         #   'UpxPath':option_panel.upx_var.get(),
            'UseUpx':option_panel.upx_var.get(),
            'Debug':option_panel.debug_var.get(),
            'CleanBuild':option_panel.clean_var.get(),
            'AskReplace':option_panel.ask_var.get(),
            'SpecName':option_panel.spec_name_var.get(),
            'SpecPath':option_panel.spec_path_var.get(),
            'SpecFilePath':self.GetSpecfilePath(),
        }
        config.SaveConfiguration(**options)
        utils.profile_set(current_project.GetKey('IsWindowsApplication'),self.is_windows)
        
    def GetCurrentProject(self):
        if self.current_project is None:
            prev_page = self.master.master.GetPrev()
            self.current_project = prev_page.new_project_doc
        return self.current_project

    def GetOptionPanel(self):
        if self.item is None:
            return self.master.master.GetNext().option_panel
        else:
            return self.master.master.master.master.GetOptionPanel("Spec option")
        
    def GetDatafilesPanel(self):
        if self.item is None:
            if self.master.master.GetNext().GetNext() is None:
                return None
            return self.master.master.GetNext().GetNext().datafiles_panel
        else:
            return self.master.master.master.master.GetOptionPanel("Data files")
            
    def GetInterpreter(self):
        if self.item is None:
            prev_page = self.master.master.GetPrev()
            interpreter_name = prev_page.GetNewPojectConfiguration().Interpreter
            interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_name)
            return interpreter
        else:
            return self.current_project.GetandSetProjectDocInterpreter()
            
    def GetStartupfile(self):
        if self.item is None:
            prev_page = self.master.master.GetPrev()
            startup_path = prev_page.GetStartupfile()
            return startup_path
        else:
            return self.GetItemFile(self.item).filePath
            
    def GetProjectPath(self):
        if self.item is None:
            prev_page = self.master.master.GetPrev()
            project_path = prev_page.GetProjectLocation()
            return project_path
        else:
            return self.current_project.GetPath()
        
    def GetSpecPath(self):
        spec_path = self.GetOptionPanel().spec_path_var.get()
        if not spec_path:
            spec_path = self.GetProjectPath()
        return spec_path
        
    def GetSpecName(self):
        spec_name = self.GetOptionPanel().spec_name_var.get()
        if not spec_name:
            spec_name = strutils.get_filename_without_ext(os.path.basename(self.GetStartupfile()))
        return strutils.MakeNameEndInExtension(spec_name,".spec")
        
    def GetSpecfilePath(self):
        spec_name = self.GetSpecName()
        spec_path = self.GetSpecPath()
        return os.path.join(spec_path,spec_name)
        
    def IsSpecExist(self):
        return os.path.exists(self.GetSpecfilePath())

    def GetVersionFile(self):
        startup_file_path = self.GetStartupfile()
        option_panel = self.GetOptionPanel()
        file_version = option_panel.file_version_var.get().strip()
        product_version = option_panel.product_version_var.get().strip()
        if file_version or product_version:
            path = resource_filename(__name__,'')
            version_info_path = os.path.join(path,"file_version_info.txt")
            with open(version_info_path) as f:
                content = f.read()
            new_content = content.replace('{FileVersion}',file_version)
            new_content = new_content.replace('{ProductVersion}',product_version)
            new_content = new_content.replace('{ProductName}',self.target_name_var.get())
            new_content = new_content.replace('{YEAR}',str(datetime.datetime.now().year))
            try:
                if file_version:
                    filevers = tuple(map(lambda x:int(x),file_version.split(".")))
                else:
                    filevers = (0,0,0,0)
                    
                if product_version:
                    prodvers = tuple(map(lambda x:int(x),product_version.split(".")))
                else:
                    prodvers = (0,0,0,0)
            except:
                messagebox.showinfo(GetApp().GetAppName(),"analyze file or product version error!")
                return None
                
            new_content = new_content.replace('{filevers}',str(filevers))
            new_content = new_content.replace('{prodvers}',str(prodvers))
            version_file_nane = "%s_verison_files.txt"%strutils.get_filename_without_ext(os.path.basename(startup_file_path))
            version_file_path = os.path.join(self.GetProjectPath(),version_file_nane)
            with open(version_file_path,"w") as f:
                    f.write(new_content)
            return version_file_path
        return None

class PyinstallerBaseInformationPage(projectwizard.BitmapTitledContainerWizardPage):
    """Creates the calculators interface
    @todo: Dissable << and >> when floating values are present
    @todo: When integer values overflow display convert to scientific notation
    @todo: Keybindings to numpad and enter key

    """
    def __init__(self, parent,**kwargs):
        """Initialiases the calculators main interface"""
        self.is_windows = kwargs.get('is_windows_application',False)
        assert(type(self.is_windows) == bool)
        projectwizard.BitmapTitledContainerWizardPage.__init__(self, parent,("Pyinstaller Project Wizard"),_("Pyinstaller Project Information\nPlease Set Base Information of Application"),"python_logo.png")
        self.can_finish = True
        
    def CreateContent(self,content_frame,**kwargs):
        self.information_panel = PyinstallerBaseInformationPanel(content_frame,None,None,**{"is_windows":self.is_windows})
        self.information_panel.grid(column=0, row=1, sticky="nsew")

    def Finish(self):
        return self.information_panel.OnOK()

class PyinstallSpecOptionPanel(pyutils.PythonBaseConfigurationPanel):
    
    def __init__(self,parent,item,current_project):
        pyutils.PythonBaseConfigurationPanel.__init__(self,parent,current_project)
        self.columnconfigure(1, weight=1)
        if item is None:
            root_file_key = "xxxxxxxx..."
        else:
            main_module_file = self.GetItemFile(item)
            root_file_key = self.GetCurrentProject().GetFileKey(main_module_file)
        
        row_index = 0
        ttk.Label(self, text=_('Spec name:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.spec_name_var = tk.StringVar(value=utils.profile_get(root_file_key + "/SpecName"))
        spec_name_entry = ttk.Entry(self,textvariable=self.spec_name_var)
        misc.create_tooltip(spec_name_entry,_("Name to assign to the bundled app and spec file (default: script's basename)"))
        spec_name_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))

        row_index += 1
        ttk.Label(self, text=_('Spec path:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.spec_path_var = tk.StringVar(value=utils.profile_get(root_file_key + "/SpecPath"))
        spec_path_entry = ttk.Entry(self,textvariable=self.spec_path_var)
        misc.create_tooltip(spec_path_entry,_('Folder to store the generated spec file (default: project directory)'))
        spec_path_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        ttk.Button(self, text= _("Browse..."),command=self.SetSpecPath).grid(column=2, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))

        row_index += 1
        ttk.Label(self,text=_('Hidden imports:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.hidden_imports_var = tk.StringVar(value=utils.profile_get(root_file_key + "/HiddenImports"))
        hidden_imports_entry = ttk.Entry(self,textvariable=self.hidden_imports_var)
        misc.create_tooltip(hidden_imports_entry,_('multi imports seperated by comma'))
        hidden_imports_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        
        if utils.is_windows():
            row_index += 1
            ttk.Label(self,text=_('File version:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
            self.file_version_var = tk.StringVar(value=utils.profile_get(root_file_key + "/FileVersion"))
            file_version_entry = ttk.Entry(self,textvariable=self.file_version_var)
            misc.create_tooltip(file_version_entry,_('The Value identifies the version of this file. For example,Value could be "3.00A" or "5.00.RC2".'))
            file_version_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
            
            row_index += 1
            ttk.Label(self,text=_('Product version:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
            self.product_version_var = tk.StringVar(value=utils.profile_get(root_file_key + "/ProductVersion"))
            product_version_entry = ttk.Entry(self,textvariable=self.product_version_var)
            misc.create_tooltip(product_version_entry,_('The Value identifies the version of the product with which this file is distributed.For example, Value could be "3.00A" or "5.00.RC2".'))
            product_version_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        
        row_index += 1
        ttk.Label(self,text=_('Log level:')).grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        levels = ('DEBUG','INFO','WARN','ERROR','CRITICAL')
        self.log_level_var = tk.StringVar(value=utils.profile_get(root_file_key + "/LogLevel",levels[1]))
        log_level_entry = ttk.Combobox(self,textvariable=self.log_level_var,values=levels,state="readonly")
        misc.create_tooltip(log_level_entry,_('Amount of detail in build-time console messages'))
        log_level_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))

        row_index += 1 
        frame = ttk.Frame(self)
        frame.grid(column=0, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=3)
        
        sbox = ttk.LabelFrame(frame, text=_("Upx settings:"))
        self.upx_var = tk.BooleanVar(value=utils.profile_get_int(root_file_key + "/UseUpx",False))
        ttk.Checkbutton(sbox,text=_('Use upx'),variable=self.upx_var,command=self.SetUpx).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        ttk.Label(sbox, text=_('Path:')).pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.upx_path_var = tk.StringVar()
        self.upx_path_entry = ttk.Entry(sbox,textvariable=self.upx_path_var)
        self.upx_path_entry.pack(side=tk.LEFT,fill="x",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        misc.create_tooltip(self.upx_path_entry,_('Path to UPX utility (default: search the execution path)'))
        self.upx_btn = ttk.Button(sbox, text= _("Browse..."),command=self.SetUpxPath)
        self.upx_btn.pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        sbox.pack(fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
        self.debug_var = tk.BooleanVar(value=utils.profile_get_int(root_file_key + "/Debug",False))
        self.ask_var = tk.BooleanVar(value=utils.profile_get_int(root_file_key + "/AskReplace",False))
        self.clean_var = tk.BooleanVar(value=utils.profile_get_int(root_file_key + "/CleanBuild",False))
        
        ttk.Checkbutton(frame,text=_('Use debug mode'),variable=self.debug_var).pack(fill="x")
        ttk.Checkbutton(frame,text=_('Ask when replace output directory'),variable=self.ask_var).pack(fill="x",)
        ttk.Checkbutton(frame,text=_('Clean before building'),variable=self.clean_var).pack(fill="x")
        self.SetUpx()
        self.DisableNoPythonfile(item)
        
    def GetCurrentProject(self):
        if self.current_project_document is None:
            prev_page = self.master.master.GetPrev().GetPrev()
            self.current_project = prev_page.new_project_doc
        return self.current_project_document
        
    def SetUpx(self):
        if not self.upx_var.get():
            self.upx_path_entry['state'] = tk.DISABLED
            self.upx_btn['state'] = tk.DISABLED
        else:
            self.upx_path_entry['state'] = tk.NORMAL
            self.upx_btn['state'] = tk.NORMAL
            
    def SetUpxPath(self):
        SetVariablevar(self.upx_path_var)
        
    def SetSpecPath(self):
        SetVariablevar(self.spec_path_var)

class PyinstallSpecOptionPage(projectwizard.BitmapTitledContainerWizardPage):
    """Creates the calculators interface
    @todo: Dissable << and >> when floating values are present
    @todo: When integer values overflow display convert to scientific notation
    @todo: Keybindings to numpad and enter key

    """
    def __init__(self, parent):
        """Initialiases the calculators main interface"""
        projectwizard.BitmapTitledContainerWizardPage.__init__(self, parent,("Pyinstaller Project Wizard"),_("Spec Options\nPlease Specify option of your spec file"),"python_logo.png")
        self.can_finish = True
        
    def CreateContent(self,content_frame,**kwargs):
        self.option_panel = PyinstallSpecOptionPanel(content_frame,None,None)
        self.option_panel.grid(column=0, row=1, sticky="nsew")
        
class CommonAddDatafilesDlg(ui_base.CommonModaldialog):
    
    def __init__(self, parent,title,label,**kwargs):
        ui_base.CommonModaldialog.__init__(self, parent)
        self.title(title)
        ttk.Label(self.main_frame, text=label).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        row = ttk.Frame(self.main_frame)
        self.file_var = tk.StringVar(value=kwargs.get('path',''))
        fileCtrl = ttk.Entry(row, textvariable=self.file_var)
        fileCtrl.pack(side=tk.LEFT,fill="x",expand=1)
        findDirButton = ttk.Button(row,text=_("Browse..."),command=self.OnBrowseButton)
        findDirButton.pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        choices = ['./']
        ttk.Label(self.main_frame,text=_("Destination directory:")).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        row = ttk.Frame(self.main_frame)
        self.dest_directory_var = tk.StringVar()
        self.dest_directoryChoice = ttk.Combobox(row,  values=choices,textvariable=self.dest_directory_var)
        self.dest_directoryChoice.current(0)
        self.dest_directoryChoice.pack(side=tk.LEFT,fill="x",expand=1)
        row.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        

    def OnBrowseButton(self):
        ''''''        

class AddSourcefilesDlg(CommonAddDatafilesDlg):
    
    def __init__(self, parent,title,**kwargs):
        CommonAddDatafilesDlg.__init__(self, parent,title,_("Source file:"),**kwargs)
        self.AddokcancelButton()
        
    def OnBrowseButton(self):
        descrs = strutils.gen_file_filters()
        path = filedialog.askopenfilename(
                master=self,
                filetypes=descrs
        )
        if not path:
            return
        self.file_var.set(fileutils.opj(path))

class AddSourceDirectoryDlg(CommonAddDatafilesDlg):
    
    def __init__(self, parent,title,**kwargs):
        CommonAddDatafilesDlg.__init__(self, parent,title,_("Source directory:"),**kwargs)
        self.visibleTemplates = []
        for template in GetApp().GetDocumentManager()._templates:
            if template.IsVisible() and not isinstance(template,ProjectTemplate):
                self.visibleTemplates.append(template)
        filters = self.InitFilters()
        filters.insert(0,"*.*")
        ttk.Label(self.main_frame,text=_("Files of type:")).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        row = ttk.Frame(self.main_frame)
        self.filter_var = tk.StringVar(value=filters[0])
        self.filterChoice = ttk.Combobox(row,values=filters,textvariable=self.filter_var)
        self.filterChoice.current(0)
        self.filterChoice.pack(side=tk.LEFT,fill="x",expand=1)
        row.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AddokcancelButton()
        
    def OnBrowseButton(self):
        SetVariablevar(self.file_var)

    def InitFilters(self):
        file_filters = []
        for temp in GetApp().GetDocumentManager().GetTemplates():
            if temp.IsVisible() and temp.GetDocumentName() != 'Project Document':
                filters = temp.GetFileFilter().split(";")
                file_filters.extend(filters)
        return file_filters

class PyinstallDatafilesPanel(pyutils.PythonBaseConfigurationPanel):
    
    SOURCE_FILE = 0
    SOURCE_DIRECTORY = 1
    
    def __init__(self,parent,item,current_project):
        pyutils.PythonBaseConfigurationPanel.__init__(self,parent,current_project)
        
        self._tb = toolbar.ToolBar(self,orient=tk.HORIZONTAL)
        self._tb.pack(fill="x",expand=0)
        self._tb.AddButton(NewId(),None,("Add file"),handler=self.Addfile,style=None)
        self._tb.AddButton(NewId(),None,("Add directory tree"),handler=self.Adddirectory,style=None)
        self._tb.AddButton(NewId(),None,("Edit file entry"),handler=self.Editfile,style=None)
        self._tb.AddButton(NewId(),None,("Remove file"),handler=self.Removefile,style=None)
        
        columns = ['type','Source File','Destination directory']
        self.listview = treeviewframe.TreeViewFrame(self, columns=columns,displaycolumns=(1,2),show="headings",height=10,borderwidth=1,relief="solid")
        self.listview.tree.bind("<Double-Button-1>", self.ShowEditDatafilesDlg, "+")
        self.listview.pack(fill="both",expand=1,pady=(0,consts.DEFAUT_HALF_CONTRL_PAD_Y))
        for column in columns[1:]:
            self.listview.tree.heading(column, text=_(column))
        self.listview.tree.column('1',width=100,anchor='w')
        self.listview.tree.column('2',width=100,anchor='w')
        self.DisableNoPythonfile(item)
        
    def ShowEditDatafilesDlg(self,event):
        self.Editfile()

    def Addfile(self):
        dlg = AddSourcefilesDlg(self,_("Add file"))
        if dlg.ShowModal() == constants.ID_OK:
            if dlg.file_var.get() and dlg.dest_directory_var.get():
                item = self.listview.tree.insert("","end",values=(self.SOURCE_FILE,dlg.file_var.get(),dlg.dest_directory_var.get()))
                self.listview.tree.selection_set(item)
        
    def Adddirectory(self):
        dlg = AddSourceDirectoryDlg(self,_("Add directory"))
        if dlg.ShowModal() == constants.ID_OK:
            if dlg.file_var.get() and dlg.dest_directory_var.get():
                file_path = os.path.join(dlg.file_var.get(),dlg.filter_var.get())
                item = self.listview.tree.insert("","end",values=(self.SOURCE_DIRECTORY,file_path,dlg.dest_directory_var.get()))
                self.listview.tree.selection_set(item)
        
    def Editfile(self):
        selections = self.listview.tree.selection()
        if not selections:
            return
        item = selections[0]
        values = self.listview.tree.item(item)['values']
        if values[0] == self.SOURCE_FILE:
            dlg = AddSourcefilesDlg(self,_("Edit file"),**{'path':values[1]})
        else:
            dlg = AddSourceDirectoryDlg(self,_("Edit directory"),**{'path':values[1]})
        dlg.ShowModal()
        
    def Removefile(self):
        selections = self.listview.tree.selection()
        if not selections:
            return
        item = selections[0]
        self.listview.tree.delete(item)
        
    def GetFiles(self):
        data_files = []
        for item in self.listview.tree.get_children():
             values = self.listview.tree.item(item)['values']
             data_files.append(values[1:])
        return data_files

class PyinstallDatafilesPage(projectwizard.BitmapTitledContainerWizardPage):
    """Creates the calculators interface
    @todo: Dissable << and >> when floating values are present
    @todo: When integer values overflow display convert to scientific notation
    @todo: Keybindings to numpad and enter key

    """
    def __init__(self, parent):
        """Initialiases the calculators main interface"""
        projectwizard.BitmapTitledContainerWizardPage.__init__(self, parent,("Pyinstaller Project Wizard"),_("Data Files\nPlease add data files of your application"),"python_logo.png")
        self.can_finish = True

    def CreateContent(self,content_frame,**kwargs):
        self.datafiles_panel = PyinstallDatafilesPanel(content_frame,None,None)
        self.datafiles_panel.grid(column=0, row=1, sticky="nsew")