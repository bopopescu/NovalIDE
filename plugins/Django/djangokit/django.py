# -*- coding: utf-8 -*-

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
import noval.python.project.runconfig as runconfig
        
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
        
    def SaveDebugRunConfiguration(self,debug_argument='runserver 127.0.0.1:${SERVER_PORT} --noreload',run_arguments='runserver 0.0.0.0:8000'):
        configuration_list = []
        self.NewRunConfiguration(self.GetModel().StartupFile,"run_web_server",run_arguments,self.GetModel().interpreter.name,configuration_list)
        self.NewRunConfiguration(self.GetModel().StartupFile,"debug_web_server",debug_argument,self.GetModel().interpreter.name,configuration_list)
        startup_dir = os.path.dirname(self.GetModel().StartupFile.filePath)
        prefix = startup_dir.replace(self.GetPath(),"").lstrip(os.sep)
        if prefix != "":
           prefix =  prefix + "|"
        self.SaveRunConfiguration(configuration_list,prefix=prefix)
        
    def SaveRunConfiguration(self,file_configuration_list,prefix=""):
        configuration_list = [prefix + "manage.py/" + configuration_name for configuration_name in file_configuration_list]
        utils.profile_set(self.GetKey() + "/ConfigurationList",configuration_list)
        utils.profile_set(self.GetKey()  + "/RunConfigurationName",configuration_list[-1])

    def Debug(self):
        self.DebugWeb()
        PythonProjectDocument.Debug(self)
        
    def RunWithoutDebug(self,filetoRun=None):
        self.DebugWeb()
        PythonProjectDocument.RunWithoutDebug(self)
        
    def DebugWeb(self,break_debug=False):
        available_port = random.randint(40000,60000)
        variablesutils.GetProjectVariableManager().AddVariable('SERVER_PORT',available_port,replace_exist=True)
        threading.Thread(target=self.StartWeb,args=(available_port,break_debug),daemon=True).start()
        
    def BreakintoDebugger(self,filetoRun=None):
        self.DebugWeb(break_debug=True)
        PythonProjectDocument.BreakintoDebugger(self,filetoRun)
        
    def StartWeb(self,available_port,break_debug):
        st = time.time()
        while True:
            end = time.time()
            if end - st > 60 and not break_debug:
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
            

    def NewApp(self,app_name):
        interpreter = self.GetandSetProjectDocInterpreter()
        if not interpreter:
            return
        startup_file = self.GetandSetProjectStartupfile()
        work_dir = self.GetPath()
        p = utils.create_process(interpreter.Path,'%s startapp %s'%(startup_file.filePath,app_name),cwd=work_dir)
        p.wait()
        app_path = os.path.join(work_dir,app_name)
        view_path = os.path.join(app_path,'views.py')
        models_path = os.path.join(app_path,'models.py')
        apps_path = os.path.join(app_path,'apps.py')
        admin_path = os.path.join(app_path,'admin.py')
        test_path = os.path.join(app_path,'tests.py')
        init_path = os.path.join(app_path,'__init__.py')
        self.GetCommandProcessor().Submit(command.ProjectAddFilesCommand(self,[view_path,models_path,apps_path,admin_path,test_path,init_path],app_name))
        

    def RunIndebugger(self):
        django_run_parameter = self.GetDjangoRunconfig(is_debug=True)
        self.DebugIndebugger(django_run_parameter)

    def RunInterminal(self,filetoRun=None):
        django_run_parameter = self.GetDjangoRunconfig()
        self.Runterminal(django_run_parameter)
        
    def Runterminal(self,run_parameter):
        self.CheckIsbuiltinInterpreter(run_parameter)
        self.RunScript(run_parameter)

    def DebugIndebugger(self,run_parameter):
        self.CheckIsbuiltinInterpreter(run_parameter)
        self.DebugRunScript(run_parameter)
        
    def GetDjangoRunconfig(self,is_debug=False):
        interpreter = self.GetandSetProjectDocInterpreter()
        self.GetandSetProjectStartupfile()
        startup_file = self.GetModel().StartupFile
        port = utils.profile_get_int(self.GetFileKey(startup_file) + "/WebDefaultPort",8000)
        if not is_debug:
            arg = "runserver 0.0.0.0:%d"%port
        else:
            arg = "runserver 127.0.0.1:%d --noreload"%port
        return runconfig.PythonRunconfig(interpreter,startup_file.filePath,arg,project=self)
        
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
        
    def GetPropertiPages(self):
        return PythonProjectTemplate.GetPropertiPages(self) + [("Django option","root","djangokit.django.DjangoInformationPanel")]


class DjangoProjectNameLocationPage(BasePythonProjectNameLocationPage):

    def __init__(self,main,**kwargs):
        BasePythonProjectNameLocationPage.__init__(self,main,**kwargs)
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
        self.columnconfigure(0, weight=1)
        self.current_project = current_project
        self.item = item
        self.is_wizard = kwargs.get('is_wizard',False)
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        
        sizer_frame.columnconfigure(1, weight=1)
        if self.is_wizard:
            ttk.Label(sizer_frame,text=_('Default app:')).grid(column=0, row=0, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
            self.default_app_var = tk.StringVar()
            self.app_entry = ttk.Entry(sizer_frame,textvariable=self.default_app_var)
            self.app_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
            row_index = 1
        else:
            row_index = 0
        ttk.Label(sizer_frame,text=_('Web Default Port:')).grid(column=0, row=row_index, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.port_var = tk.IntVar(value=8000)
        
        #验证端口文本控件输入是否合法,端口只能输入数字
        validate_cmd = self.register(self.validatePortInput)
        self.port_entry = ttk.Entry(sizer_frame,validate = 'key', validatecommand = (validate_cmd, '%P'),textvariable=self.port_var)
        self.port_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        row_index += 1
        ttk.Label(sizer_frame,text=_('Debug server arguments:')).grid(column=0, row=row_index, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.debug_arguments_var = tk.StringVar(value='runserver 127.0.0.1:${SERVER_PORT} --noreload')
        self.debug_arguments_entry = ttk.Entry(sizer_frame,textvariable=self.debug_arguments_var)
        self.debug_arguments_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        row_index += 1
        ttk.Label(sizer_frame,text=_('Run server arguments:')).grid(column=0, row=row_index, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.run_arguments_var = tk.StringVar(value='runserver 0.0.0.0:8000')
        self.run_arguments_entry = ttk.Entry(sizer_frame,textvariable=self.run_arguments_var)
        self.run_arguments_entry.grid(column=1, row=row_index, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
    def validatePortInput(self,contents):
        if not contents.isdigit():
            self.port_entry.bell()
            return False
        return True
        
            
    def OnOK(self,optionsDialog=None):
        if self.port_var.get() >= 1 and self.port_var.get() <= 65535:
            doc = self.GetCurrentProject()
            startup_file = doc.GetModel().StartupFile
            doc.SaveDebugRunConfiguration(self.debug_arguments_var.get(),self.run_arguments_var.get())
            utils.profile_set(doc.GetFileKey(startup_file) + "/WebDefaultPort",self.port_var.get())
            return True
        messagebox.showerror(_('Error'),_('invalid port'))
        return False
        
    def GetCurrentProject(self):
        if self.current_project is None:
            prev_page = self.main.main.GetPrev()
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
        self.information_panel = DjangoInformationPanel(content_frame,None,None,**{'is_wizard':True})
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
        
        if not self.information_panel.OnOK():
            return False
        default_app = self.information_panel.default_app_var.get().strip()
        if default_app != "":
            doc.NewApp(default_app)
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
