
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
import noval.ui_utils as ui_utils
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.toolbar as toolbar
import noval.ui_base as ui_base
import noval.python.project.runconfiguration as runconfiguration
import noval.project.command as command
import noval.python.pyutils as pyutils
from pkg_resources import resource_filename
import datetime
from shutil import which
import noval.python.interpreter.pythonpackages as pythonpackages
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.project.variables as variablesutils
import threading
import time
import noval.util.urlutils as urlutils
import random
        
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
    

def GetDjangoToolPath(interpreter):
    django_tool_path = GetToolPath(interpreter,"django-admin")
    if not os.path.exists(django_tool_path):
        django_tool_path = GetToolPath(interpreter,"django-admin",is_user_site=True)
        if not os.path.exists(django_tool_path): 
            raise RuntimeError(_("interpreter %s need to install package \"django\"")%interpreter.Name)
    return django_tool_path


def CheckDjango(interpreter,parent=None):
    try:
        GetDjangoToolPath(interpreter)
    except RuntimeError as e:
        messagebox.showinfo(GetApp().GetAppName(),str(e),parent=parent)
        dlg = pythonpackages.InstallPackagesDialog(parent,interpreter,pkg_name='django',install_args='--user django',autorun=True)
        status = dlg.ShowModal()
        if status == constants.ID_CANCEL:
            return False
    return True

class DjangoProject(PythonProject):
    def __init__(self):
        super(DjangoProject,self).__init__()
        self._runinfo.DocumentTemplate = "djangokit.django.DjangoProjectTemplate"

class DjangoProjectDocument(PythonProjectDocument):

    def __init__(self, model=None):
        PythonProjectDocument.__init__(self,model)
        
    @staticmethod
    def GetProjectModel():
        return DjangoProject()

    def CheckIsbuiltinInterpreter(self,run_parameter):
        if run_parameter.Interpreter.IsBuiltIn:
            raise RuntimeError(_('Builtin Interpreter is not support to run django project'))

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

    def NewRunConfiguration(self,main_module_file,configuration_name,build_args,interpreter_name,file_configuration_list=[]):
        file_configuration = runconfiguration.FileConfiguration(self,main_module_file)
        file_configuration_list.append(configuration_name)
        pj_file_key = file_configuration.GetRootKeyPath()
        #update file configuration list
        utils.profile_set(pj_file_key + "/ConfigurationList",file_configuration_list)
        args = {
            runconfiguration.StartupConfiguration.CONFIGURATION_NAME:runconfiguration.StartupConfiguration(self,main_module_file, 0, ''),
            runconfiguration.AugumentsConfiguration.CONFIGURATION_NAME:runconfiguration.AugumentsConfiguration(self,main_module_file,'',build_args),
            runconfiguration.InterpreterConfiguration.CONFIGURATION_NAME:runconfiguration.InterpreterConfiguration(self,main_module_file,interpreter_name),
            runconfiguration.EnvironmentConfiguration.CONFIGURATION_NAME:runconfiguration.EnvironmentConfiguration(self,main_module_file,{}),
        }
        
        run_configuration = runconfiguration.RunConfiguration(configuration_name,**args)
        run_configuration.SaveConfiguration()
        
    def SaveRunConfiguration(self,file_configuration_list,prefix=""):
        configuration_list = [prefix + "manage.py/" + configuration_name for configuration_name in file_configuration_list]
        utils.profile_set(self.GetKey() + "/ConfigurationList",configuration_list)
        utils.profile_set(self.GetKey()  + "/RunConfigurationName",configuration_list[-1])
        

    def Debug(self):
        available_port = random.randint(40000,60000)
        variablesutils.GetProjectVariableManager().AddVariable('SERVER_PORT',available_port,replace_exist=True)
        threading.Thread(target=self.StartWeb,args=(available_port,),daemon=True).start()
        PythonProjectDocument.Debug(self)
        
    def StartWeb(self,available_port):
        st = time.time()
        while True:
            end = time.time()
            if end - st > 60:
                break
            time.sleep(0.5)
            url_addr = "http://127.0.0.1:%d"%available_port
            if urlutils.RequestData(url_addr,to_json=False) is None:
                print ('web url',url_addr,'is not available.....')
                continue
            fileutils.startfile(url_addr)
            break
            
    def GetRunConfiguration(self,run_file=None,is_debug=False):
        project_configuration = runconfiguration.ProjectConfiguration(self)
        configuration_name_list = project_configuration.LoadConfigurationNames()
        if is_debug:
            return configuration_name_list[1]
        else:
            return configuration_name_list[0]
        
        
class DjangoProjectTemplate(PythonProjectTemplate):
    
    @staticmethod
    def CreateProjectTemplate():
        projectTemplate = DjangoProjectTemplate(GetApp().GetDocumentManager(),
                _("Project File"),
                "*%s" % consts.PROJECT_EXTENSION,
                os.getcwd(),
                consts.PROJECT_EXTENSION,
                "DjangoProject Document",
                _("DjangoProject Viewer"),
                DjangoProjectDocument,
                PythonProjectView,
                icon = imageutils.getProjectIcon())
        GetApp().GetDocumentManager().DisassociateTemplate(projectTemplate)
        return projectTemplate

class DjangoProjectNameLocationPage(BasePythonProjectNameLocationPage):

    def __init__(self,master,**kwargs):
        BasePythonProjectNameLocationPage.__init__(self,master,**kwargs)
        self.can_finish = False

    def GetProjectTemplate(self):
        return DjangoProjectTemplate.CreateProjectTemplate()
        
    def SaveProject(self,path):
        return True
        
    def SaveDjangoProject(self,path):
        return BasePythonProjectNameLocationPage.SaveProject(self,path)
        

class DjangoInformationPanel(pyutils.PythonBaseConfigurationPanel):
    
    def __init__(self,parent,item,current_project,**kwargs):
        pyutils.PythonBaseConfigurationPanel.__init__(self,parent,current_project)
        self.columnconfigure(1, weight=1)
        self.current_project = current_project
        self.item = item
            
    def OnOK(self,optionsDialog=None):
        return True
        
    def GetCurrentProject(self):
        if self.current_project is None:
            prev_page = self.master.master.GetPrev()
            self.current_project = prev_page.new_project_doc
        return self.current_project


class DjangoInformationPage(projectwizard.BitmapTitledContainerWizardPage):
    """Creates the calculators interface
    @todo: Dissable << and >> when floating values are present
    @todo: When integer values overflow display convert to scientific notation
    @todo: Keybindings to numpad and enter key

    """
    def __init__(self, parent,**kwargs):
        """Initialiases the calculators main interface"""
        projectwizard.BitmapTitledContainerWizardPage.__init__(self, parent,("Django Project Wizard"),_("Django Project Information\nPlease Set Information of Django Project"),"python_logo.png")
        self.can_finish = True
        
    def CreateContent(self,content_frame,**kwargs):
        self.information_panel = DjangoInformationPanel(content_frame,None,None)
        self.information_panel.grid(column=0, row=1, sticky="nsew")

    def Finish(self):
        interpreter = self.GetInterpreter()
        if not CheckDjango(interpreter,parent=self) or interpreter is None:
            return False
        django_tool_path = GetDjangoToolPath(interpreter)
        projName = self.GetPrev().name_var.get().strip()
        args = "startproject %s"%projName
        work_dir = self.GetWorkDir()
        p = utils.create_process(django_tool_path,args,cwd=work_dir)
        p.wait()
        
        project_path = self.GetProjectPath()
        fullProjectPath = os.path.join(project_path, strutils.MakeNameEndInExtension(projName, consts.PROJECT_EXTENSION))
        if not self.GetPrev().SaveDjangoProject(fullProjectPath):
            return False
            
        startup_path = os.path.join(project_path,'manage.py')
        app_path = os.path.join(project_path,projName)
        settings_path = os.path.join(app_path,'settings.py')
        urls_path = os.path.join(app_path,'urls.py')
        wsgi_path = os.path.join(app_path,'wsgi.py')
        init_path = os.path.join(app_path,'__init__.py')
        view = GetApp().MainFrame.GetProjectView().GetView()
        doc = view.GetDocument()
        doc.GetCommandProcessor().Submit(command.ProjectAddFilesCommand(doc,[urls_path,settings_path,wsgi_path,init_path],projName))
        doc.GetCommandProcessor().Submit(command.ProjectAddFilesCommand(doc,[startup_path],None))
        view.SetProjectStartupFile()
        startup_file = doc.GetModel().StartupFile
        configuration_list = []
        doc.NewRunConfiguration(startup_file,"run_web_server",'runserver 0.0.0.0:8000',doc.GetModel().interpreter.name,configuration_list)
        doc.NewRunConfiguration(startup_file,"debug_web_server",'runserver 127.0.0.1:${SERVER_PORT} --noreload',doc.GetModel().interpreter.name,configuration_list)
        doc.SaveRunConfiguration(configuration_list)
        return True

    def GetInterpreter(self):
        prev_page = self.GetPrev()
        interpreter_name = prev_page.GetNewPojectConfiguration().Interpreter
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_name)
        return interpreter

    def GetProjectPath(self):
        prev_page = self.GetPrev()
        project_path = prev_page.GetProjectLocation()
        return os.path.join(project_path,prev_page.name_var.get().strip())
 

    def GetWorkDir(self):
        prev_page = self.GetPrev()
        project_path = prev_page.GetProjectLocation()
        return project_path
