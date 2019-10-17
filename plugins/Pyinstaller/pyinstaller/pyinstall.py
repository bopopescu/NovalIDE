__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: calc.py 850 2009-05-01 00:24:27Z CodyPrecord $"
__revision__ = "$Revision: 850 $"

#--------------------------------------------------------------------------#
# Dependancies
import tkinter as tk
from tkinter import ttk,messagebox
from noval import _
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
import noval.python.parser.utils as parserutils
from noval.project.executor import *
import noval.terminal as terminal

SINGLE_SPEC_FILE_TEMPLATE = '''
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None
datas = []
a = Analysis([r'{SOURCE_FILEN_PATH}'],
             pathex=[r'{SOURCE_PATH}'],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='{TARGET_EXE_NAME}',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console={IS_CONSOLE} , icon='{ICON_PATH}')
'''

SPEC_FILE_TEMPLATE = SINGLE_SPEC_FILE_TEMPLATE + '''
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='{TARGET_FOLDER_NAME}')

'''

class PyinstallerRunconfig(BaseRunconfig):
    def __init__(self,interpreter,file_path,arg='',env=None,start_up=None,project=None,is_console=True,icon_path=''):
        self._interpreter = interpreter
        self._project = project
        self.filepath = file_path
        self.file_name = os.path.basename(file_path)
        self.is_console = is_console
        self.icon_path = icon_path
        pyinstaller_tool_path = self.GetPyinstallerToolPath(interpreter)
        spec_path = self.GetSpecfilePath()
        BaseRunconfig.__init__(self,pyinstaller_tool_path,spec_path,env,start_up,project)

    @property
    def Interpreter(self):
        return self._interpreter

    def GetPyinstallerToolPath(self,interpreter):
        interpreter_path = interpreter.InstallPath
        pyinstaller_tool_path = os.path.join(interpreter_path,"Scripts","pyinstaller.exe")
        if not os.path.exists(pyinstaller_tool_path):
            raise RuntimeError('ggggg')
        return pyinstaller_tool_path

    def GetSpecfilePath(self,file_name=None):
        spec_path = os.path.join(utils.get_user_data_path(),"pyinstaller",self.Project.GetModel().Id)
        if file_name is None:
            file_name = os.path.basename(self.Project.GetStartupFile().filePath)
        spec_file_name = "noval.python.%s.%s.spec" %(self.Project.GetModel().Name,strutils.get_filename_without_ext(file_name))
        spec_file_path = os.path.join(spec_path,spec_file_name)
        #if not os.path.exists(spec_file_path):
        self.GenerateSepcFile(spec_file_path)
        return spec_file_path

    def GenerateSepcFile(self,spec_file_path):
        exe_name = strutils.get_filename_without_ext(self.file_name)
        content = SPEC_FILE_TEMPLATE.format(SOURCE_FILEN_PATH=self.filepath,SOURCE_PATH=os.path.dirname(self.filepath),TARGET_EXE_NAME=exe_name,\
                IS_CONSOLE=self.is_console,ICON_PATH=self.icon_path,TARGET_FOLDER_NAME=self.Project.GetModel().Name)
        spec_dir_path = os.path.dirname(spec_file_path)
        if not os.path.exists(spec_dir_path):
            parserutils.MakeDirs(spec_dir_path)
        with open(spec_file_path,"w") as f:
            f.write(content)

    def GetTargetPath(self):
        project_path = self.Project.GetPath()
        dist_path = os.path.join(project_path,'dist')
        dist_project_path = os.path.join(dist_path,self.Project.GetModel().Name)
        target_exe_path = os.path.join(dist_project_path,"%s.exe"%strutils.get_filename_without_ext(self.file_name))
        return target_exe_path

class PyinstallerProject(PythonProject):
    def __init__(self):
        super(PyinstallerProject,self).__init__()
        self._properties._pages = []
        self._properties.AddPage("Resource","root","noval.project.resource.ResourcePanel")
        self._properties.AddPage("Debug/Run","root","noval.python.project.debugrun.DebugRunPanel")
        self._properties.AddPage("PythonPath","root","noval.python.project.pythonpath.PythonPathPanel")
        self._properties.AddPage("Interpreter","root","noval.python.project.pythoninterpreter.PythonInterpreterPanel")
        self._properties.AddPage("Project References","root","noval.python.project.projectreferrence.ProjectReferrencePanel")

        self._properties.AddPage("Resource","file","noval.project.resource.ResourcePanel")
        self._properties.AddPage("Debug/Run","file","noval.python.project.debugrun.DebugRunPanel")

        self._properties.AddPage("Resource","folder","noval.project.resource.ResourcePanel")
        self._properties.AddPage("Debug/Run","folder","noval.python.project.debugrun.DebugRunPanel")

        self._runinfo.RunConfig = "pyinstaller.pyinstall.PyinstallerRunconfig"
        self._runinfo.DocumentTemplate = "pyinstaller.pyinstall.PyinstallerProjectTemplate"

class PyinstallerProjectDocument(PythonProjectDocument):

    def __init__(self, model=None):
        ProjectDocument.__init__(self,model)
        
    @staticmethod
    def GetProjectModel():
        return PyinstallerProject()

    def GetRunConfiguration(self,start_up_file):
        file_key = self.GetFileKey(start_up_file)
        run_configuration_name = utils.profile_get(file_key + "/RunConfigurationName","")
        return run_configuration_name

    def CheckIsbuiltinInterpreter(self,run_parameter):
        if run_parameter.Interpreter.IsBuiltIn:
            raise RuntimeError(_('Builtin Interpreter is not support to run pyinstaller project'))      

    def RunScript(self,run_parameter):
        self.CheckIsbuiltinInterpreter(run_parameter)
        executor = TerminalExecutor(run_parameter)
        command1 = executor.GetExecuteCommand()
        target_exe_path = run_parameter.GetTargetPath()
        print ('run target exe path',target_exe_path,'in terminal')
        run_parameter = BaseRunconfig(target_exe_path)
        executor = TerminalExecutor(run_parameter)
        command2 = executor.GetExecuteCommand()

        command = command1 + " && " +  command2
        
        utils.get_logger().debug("start run executable: %s in terminal",command)
        startIn = executor.GetStartupPath()
        terminal.run_in_terminal(command,startIn,os.environ,keep_open=False,pause=True,title="abc")

    def Debug(self):
        run_parameter = self.GetRunParameter()
        if run_parameter is None:
            return
        self.DebugRunScript(run_parameter)

    def GetRunConfiguration(self):
        pass

    def RunTarget(self,run_parameter):
        target_exe_path = self.GetTargetPath()
        
    def DebugRunTarget(self,run_parameter):
        target_exe_path = self.GetTargetPath()

    def DebugRunScript(self,run_parameter):
        self.CheckIsbuiltinInterpreter(run_parameter)
        fileToRun = run_parameter.filepath
        shortFile = os.path.basename(fileToRun)
        view = GetApp().MainFrame.GetCommonView("Output")
        view.SetRunParameter(run_parameter)
        view.GetOutputview().SetTraceLog(True)
        view.CreateExecutor(source="Build",finish_stopped=False)
        view.Execute()
        GetApp().GetDocumentManager().ActivateView(self.GetDebugger().GetView())
        

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
        return projectTemplate
    

class PyinstallerProjectNameLocationPage(PythonProjectNameLocationPage):

    def __init__(self,master,**kwargs):
        PythonProjectNameLocationPage.__init__(self,master,**kwargs)

    def GetProjectTemplate(self):
        return PyinstallerProjectTemplate.CreateProjectTemplate()

class PyinstallerDubugrunConfigurationPage(projectwizard.BitmapTitledContainerWizardPage):
    """Creates the calculators interface
    @todo: Dissable << and >> when floating values are present
    @todo: When integer values overflow display convert to scientific notation
    @todo: Keybindings to numpad and enter key

    """
    def __init__(self, parent):
        """Initialiases the calculators main interface"""
        projectwizard.BitmapTitledContainerWizardPage.__init__(self, parent,("Pyinstaller Project Wizard"),_("Pyinstaller Application Information\nPlease Set Base Information of Application"),"python_logo.png")
        self.can_finish = True
        
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        row = ttk.Frame(sizer_frame)
        ttk.Label(row,text=_('Application Target name:')).pack(fill="x",side=tk.LEFT)
        self.target_name_var = tk.StringVar()
        target_entry = ttk.Entry(row,textvariable=self.target_name_var)
        target_entry.pack(fill="x",side=tk.LEFT,expand=1)
        row.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        row = ttk.Frame(sizer_frame)
        ttk.Label(row, text=_('Application Icon path:')).pack(side=tk.LEFT)
        self.icon_path_var = tk.StringVar()
        icon_path_entry = ttk.Entry(row,textvariable=self.icon_path_var)
        
        icon_path_entry.pack(side=tk.LEFT,fill="x",expand=1)
        ttk.Button(row, text= _("Browse..."),command=None).pack(side=tk.LEFT,padx=consts.DEFAUT_HALF_CONTRL_PAD_X)
        row.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        ttk.Checkbutton(sizer_frame,text=_('Make a single exetuable file')).pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

    def Finish(self):
        return True
