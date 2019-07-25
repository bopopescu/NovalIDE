__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: calc.py 850 2009-05-01 00:24:27Z CodyPrecord $"
__revision__ = "$Revision: 850 $"

#--------------------------------------------------------------------------#
# Dependancies
import tkinter as tk
from tkinter import ttk
from noval import _
import noval.util.utils as utils
import noval.project.wizard as projectwizard
from noval.project.baseconfig import *
from noval.python.project.viewer import *
from noval.python.project.model import *
import noval.consts as consts
import noval.imageutils as imageutils
import os
#--------------------------------------------------------------------------#
#ID_CALC = wx.NewId()

#-----------------------------------------------------------------------------#
#ID_CHAR_DSP = wx.NewId()

SPEC_FILE_TEMPLATE = '''
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None
datas = []
a = Analysis(['{SOURCE_FILEN_NAME}'],
             pathex=['{SOURCE_PATH}'],
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
    def __init__(self,interpreter,file_path,arg='',env=None,start_up=None,is_console=True,icon_path='',project=None):
        self.file_path = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.is_console = is_console
        self.icon_path = icon_path
        spec_path = self.GetSpecfilePath()
        pyinstaller_tool_path = self.GetPyinstallerToolPath(interpreter)
        BaseRunconfig.__init__(self,pyinstaller_tool_path,spec_path,None,None,project)

    def GetPyinstallerToolPath(self,interpreter):
        interpreter_path = interpreter.InstallPath()
        pyinstaller_tool_path = os.path.join(interpreter_path,"Scripts","pyinstaller.exe")
        if not os.path.exists(pyinstaller_tool_path):
            raise RuntimeError('ggggg')
        return pyinstaller_tool_path

    def GetSpecfilePath(self,file_name=None):
        spec_path = os.path.join(utils.get_user_data_path(),"pyinstaller",self.Project.GetModel().Id)
        spec_file_name = "noval.python.%s.%s.spec" %(self.Project.GetModel().Name,strutils.get_filename_without_ext(file_name))
        spec_file_path = os.path.join(spec_path,spec_file_name)
        if not os.path.exists(spec_file_path):
            self.GenerateSepcFile(spec_file_path)
        return spec_file_path

    def GenerateSepcFile(self,spec_file_path):
        exe_name = strutils.get_filename_without_ext(self.file_name)
        content = SPEC_FILE_TEMPLATE.format(SOURCE_FILEN_NAME=self.file_name,SOURCE_PATH=self.file_path,TARGET_EXE_NAME=exe_name,\
                IS_CONSOLE=self.is_console,ICON_PATH=self.icon_path,TARGET_FOLDER_NAME=self.Project.GetModel().Name)
        
        with open(spec_file_path) as f:
            f.write(content)

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

        self._runinfo.RunConfig = "pyinstaller.PyinstallerRunconfig"
        self._runinfo.DocumentTemplate = "pyinstaller.PyinstallerProjectTemplate"

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
        
    def GetRunParameter(self,start_up_file):
        #check the run configuration first,if exist,use run configuration
        run_configuration_name = self.GetRunConfiguration(start_up_file)
        if run_configuration_name:
            file_configuration = RunConfiguration.FileConfiguration(self,start_up_file)
            run_configuration = file_configuration.LoadConfiguration(run_configuration_name)
            try:
                return run_configuration.GetRunParameter()
            except PromptErrorException as e:
                wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR)
                return None
            

        use_argument = utils.profile_get_int(self.GetFileKey(start_up_file,"UseArgument"),True)
        if use_argument:
            initialArgs = utils.profile_get(self.GetFileKey(start_up_file,"RunArguments"),"")
        else:
            initialArgs = ''
        python_path = utils.profile_get(self.GetFileKey(start_up_file,"PythonPath"),"")
        startIn = utils.profile_get(self.GetFileKey(start_up_file,"RunStartIn"),"")
        if startIn == '':
            startIn = os.path.dirname(self.GetFilename())
        env = {}
        paths = set()
        path_post_end = utils.profile_get_int(self.GetKey("PythonPathPostpend"), True)
        if path_post_end:
            paths.add(str(os.path.dirname(self.GetFilename())))
        #should avoid environment contain unicode string,such as u'xxx'
        if len(python_path) > 0:
            paths.add(str(python_path))
        env[consts.PYTHON_PATH_NAME] = os.pathsep.join(list(paths))
        #获取项目的运行配置类
        return self.GetRunconfigClass()(GetApp().GetCurrentInterpreter(),start_up_file.filePath,initialArgs,env,startIn,project=self)

    def Run(self):
        self.RunTarget()

    def Debug(self):
        pass

    def GetRunConfiguration(self):
        pass

    def RunTarget(self,run_parameter):
        target_exe_path = self.GetTargetPath()
        
    def DebugRunTarget(self,run_parameter):
        target_exe_path = self.GetTargetPath()
        
    def GetTargetPath(self,file_name):
        project_path = self.GetPath()
        dist_path = os.path.join(project_path,'dist')
        dist_project_path = os.path.join(dist_path,self.GetModel().Name)
        target_exe_path = os.path.join(dist_project_path,"%s.exe"%strutils.get_filename_without_ext(file_name))
        

class PyinstallerProjectTemplate(PythonProjectTemplate):
    pass

class PyinstallerProjectNameLocationPage(PythonProjectNameLocationPage):

    def __init__(self,master,**kwargs):
        PythonProjectNameLocationPage.__init__(self,master,**kwargs)

    def GetProjectTemplate(self):
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

class PyinstallerDubugrunConfigurationPage(projectwizard.BitmapTitledWizardPage):
    """Creates the calculators interface
    @todo: Dissable << and >> when floating values are present
    @todo: When integer values overflow display convert to scientific notation
    @todo: Keybindings to numpad and enter key

    """
    def __init__(self, parent):
        """Initialiases the calculators main interface"""
        projectwizard.BitmapTitledWizardPage.__init__(self, parent,("Set the Configuration of Pyinstaller project"),_("Set General Debug/Run Options"),"python_logo.png")
        self.can_finish = True
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=1, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        row = ttk.Frame(sizer_frame)
        ttk.Label(row,text=_('Target name:')).pack(fill="x",side=tk.LEFT)
        self.target_name_var = tk.StringVar()
        target_entry = ttk.Entry(row,textvariable=self.target_name_var)
        target_entry.pack(fill="x",side=tk.LEFT,expand=1)
        row.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        row = ttk.Frame(sizer_frame)
        ttk.Label(row, text=_('Icon path:')).pack(side=tk.LEFT)
        self.icon_path_var = tk.StringVar()
        icon_path_entry = ttk.Entry(row,textvariable=self.icon_path_var)
        
        icon_path_entry.pack(side=tk.LEFT,fill="x",expand=1)
        ttk.Button(row, text= _("Browse..."),command=None).pack(side=tk.LEFT,padx=consts.DEFAUT_HALF_CONTRL_PAD_X)
        row.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        ttk.Checkbutton(sizer_frame,text=_('Make a single exetuable file')).pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

    def Finish(self):
        return True
