# -*- coding: utf-8 -*-
from noval import GetApp,_
from noval.util import utils
import noval.python.interpreter.interpretermanager as interpretermanager
import os
import noval.project.basemodel as projectmodel
import noval.project.variables as variablesutils
import noval.consts as consts
import noval.python.project.runconfig as runconfig

class BaseConfiguration(object):
    
    DEFAULT_PROJECT_DIR_PATH = 1
    PROJECT_CHILD_FOLDER_PATH = 2
    LOCAL_FILE_SYSTEM_PATH = 3
    EXPRESSION_VALIABLE_PATH = 4
    
    def __init__(self,project_doc,main_module_file):
        self._project_document = project_doc
        self._main_module_file = main_module_file
        
    @property
    def ProjectDocument(self):
        return self._project_document
        
    @property
    def MainModuleFile(self):
        return self._main_module_file
        
    @MainModuleFile.setter
    def MainModuleFile(self,main_module_file):
        self._main_module_file = main_module_file
      
    @property
    def MainModulePath(self):
        return self._main_module_file.filePath
        
    def GetRootKeyPath(self):
        return self._project_document.GetFileKey(self._main_module_file)
        
    def GetConfigurationKey(self,configuration_name,config_key):
        return "%s/%s/%s" % (self.GetRootKeyPath(),configuration_name,config_key)

class StartupConfiguration(BaseConfiguration):
    """description of class"""
    CONFIGURATION_NAME = 'Startup'
    
    def __init__(self,project_doc,main_module_file=None,startup_path_pattern=\
            BaseConfiguration.DEFAULT_PROJECT_DIR_PATH,startup_path=""):
        super(StartupConfiguration,self).__init__(project_doc,main_module_file)
        self._startup_path = startup_path
        self._startup_path_pattern = startup_path_pattern
        
    @property
    def StartupPathPattern(self):
        return self._startup_path_pattern
        
    @property
    def StartupPath(self):
        return self._startup_path

    def SaveConfiguration(self,config_key,configuration_name):
        configuration_key = self.GetConfigurationKey(configuration_name,config_key)
        utils.profile_set(configuration_key + "/StartupPathPattern",self._startup_path_pattern)
        if self._startup_path_pattern != self.DEFAULT_PROJECT_DIR_PATH:
            utils.profile_set(configuration_key + "/StartupPath",self._startup_path)
        
class AugumentsConfiguration(BaseConfiguration):
    
    CONFIGURATION_NAME = 'Arguments'
    def __init__(self,project_doc,main_module_file = None,interpreter_option = "",\
                    program_args=""):
        super(AugumentsConfiguration,self).__init__(project_doc,main_module_file)
        self._interpreter_option = interpreter_option
        self._program_args = program_args
    
    @property
    def ProgramArgs(self):
        return self._program_args
        
    def GetArgs(self):
        arg_list = self._program_args.split('\n')
        return ' '.join(arg_list)
        
    @property
    def InterpreterOption(self):
        return self._interpreter_option
        
    def GetInterpreterOption(self):
        arg_list = self._interpreter_option.split('\n')
        return ' '.join(arg_list)

    def SaveConfiguration(self,config_key,configuration_name):
        configuration_key = self.GetConfigurationKey(configuration_name,config_key)
        utils.profile_set(configuration_key + "/ProgramArgs",self._program_args)
        utils.profile_set(configuration_key + "/InterpreterOptions",self._interpreter_option)

class InterpreterConfiguration(BaseConfiguration):
    
    CONFIGURATION_NAME = 'Interpreter'
    
    def __init__(self,project_doc,main_module_file=None,interpreter_name=""):
        super(InterpreterConfiguration,self).__init__(project_doc,main_module_file)
        self._interpreter_name = interpreter_name
        
    @property
    def InterpreterName(self):
        return self._interpreter_name

    def SaveConfiguration(self,config_key,configuration_name):
        configuration_key = self.GetConfigurationKey(configuration_name,config_key)
        utils.profile_set(configuration_key + "/InterpreterName",self._interpreter_name)

class EnvironmentConfiguration(BaseConfiguration):
    
    CONFIGURATION_NAME = 'Environment'
    def __init__(self,project_doc,main_module_file=None,environ={}):
        super(EnvironmentConfiguration,self).__init__(project_doc,main_module_file)
        self.environ = environ
        
    def SaveConfiguration(self,config_key,configuration_name):
        configuration_key = self.GetConfigurationKey(configuration_name,config_key)
        utils.profile_set(configuration_key + "/Environment",self.environ)
      
    @property
    def Environ(self):
        return self.environ
        
    def GetEnviron(self):
        environ = {}
        #enviroment must not contain unicode,so should convert to str
        for env in self.environ:
            environ[str(env)] = str(self.environ[env])
        return environ
        
class RunConfiguration():
    
    DEFAULT_CONFIGURATION_NAME = "NewConfiguration"
    
    def __init__(self,configuration_name,**kw_configurations):
        self._configuration_name = configuration_name
        self._configurations = kw_configurations
        self._is_new_configuration = True
        
    @property
    def IsNewConfiguration(self):
        return self._is_new_configuration
        
    @IsNewConfiguration.setter
    def IsNewConfiguration(self,is_new):
        self._is_new_configuration = is_new

    def SaveConfiguration(self):
        for key in self._configurations:
            self._configurations[key].SaveConfiguration(key,self._configuration_name)
            
    @property
    def Name(self):
        return self._configuration_name
        
    @Name.setter
    def Name(self,name):
        self._configuration_name = name
        
    def GetRootKeyPath(self):
        #python3字典items方法返回dict_items对象,必须转换为list对象
        return list(self._configurations.items())[0][1].GetRootKeyPath()
    
    @classmethod
    def CreateNewConfiguration(cls,project_doc,default_interpreter,main_module_file=None,configuration_name=""):
        interpreter_name = default_interpreter.Name
        args = {
            StartupConfiguration.CONFIGURATION_NAME:StartupConfiguration(project_doc,main_module_file),
            AugumentsConfiguration.CONFIGURATION_NAME:AugumentsConfiguration(project_doc,main_module_file),
            InterpreterConfiguration.CONFIGURATION_NAME:InterpreterConfiguration(project_doc,main_module_file,interpreter_name),
            EnvironmentConfiguration.CONFIGURATION_NAME:EnvironmentConfiguration(project_doc,main_module_file,{})
        }
        run_configuration = RunConfiguration(configuration_name,**args)
        return run_configuration
        
    def GetChildConfiguration(self,child_configuration_name):
        return self._configurations.get(child_configuration_name)
        
    @property
    def ProjectDocument(self):
        return list(self._configurations.items())[0][1].ProjectDocument
        
    @property
    def MainModuleFile(self):
        return list(self._configurations.items())[0][1].MainModuleFile
        
    def Clone(self):
        args = {
            StartupConfiguration.CONFIGURATION_NAME:self.GetChildConfiguration(StartupConfiguration.CONFIGURATION_NAME),
            AugumentsConfiguration.CONFIGURATION_NAME:self.GetChildConfiguration(AugumentsConfiguration.CONFIGURATION_NAME),
            InterpreterConfiguration.CONFIGURATION_NAME:self.GetChildConfiguration(InterpreterConfiguration.CONFIGURATION_NAME),
            EnvironmentConfiguration.CONFIGURATION_NAME:self.GetChildConfiguration(EnvironmentConfiguration.CONFIGURATION_NAME)
        }
        run_configuration = RunConfiguration(self.Name,**args)
        return run_configuration
        
    def GetRunParameter(self):
        startup_configuration = self.GetChildConfiguration(StartupConfiguration.CONFIGURATION_NAME)
        arguments_configuration = self.GetChildConfiguration(AugumentsConfiguration.CONFIGURATION_NAME)
        interpreter_configuration = self.GetChildConfiguration(InterpreterConfiguration.CONFIGURATION_NAME)
        environment_configuration = self.GetChildConfiguration(EnvironmentConfiguration.CONFIGURATION_NAME)
        
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_configuration.InterpreterName)
        if interpreter is None:
            raise RuntimeError(_("Interpreter \"%s\" is not exist") % interpreter_configuration.InterpreterName)
            
        fileToRun = self.MainModuleFile.filePath
        initialArgs = arguments_configuration.GetArgs()
        #参数里面可能有一些变量,需要将这些变量转换成实际值
        if initialArgs:
            initialArgs = variablesutils.VariablesManager(self.ProjectDocument).EvalulateValue(initialArgs)
        startIn = startup_configuration.StartupPath
        #路径里面可能有一些变量,需要将这些变量转换成变量对应的值
        if startup_configuration.StartupPathPattern != StartupConfiguration.DEFAULT_PROJECT_DIR_PATH:
            startIn = variablesutils.VariablesManager(self.ProjectDocument).EvalulateValue(startIn)
        interpreter_option = arguments_configuration.GetInterpreterOption()
        env = environment_configuration.GetEnviron()
        project_configuration = ProjectConfiguration(self.ProjectDocument)
        python_path_list = project_configuration.LoadPythonPath()
        project_environ = project_configuration.LoadEnviron()
        env.update(project_environ)
        env[consts.PYTHON_PATH_NAME] = str(os.pathsep.join(python_path_list))
        return runconfig.PythonRunconfig(interpreter,fileToRun,initialArgs,env,startIn,project=self.ProjectDocument,interpreter_option=interpreter_option)

class FileConfiguration(BaseConfiguration):
    def __init__(self,project_doc,main_module_file):
        super(FileConfiguration,self).__init__(project_doc,main_module_file)
        self._configuration_list = []
        
    def LoadConfigurationNames(self):
        file_key = self.GetRootKeyPath()
        configuration_name_list = utils.profile_get(file_key + "/" + "ConfigurationList",[])
        return configuration_name_list
        
    def LoadConfigurations(self):
        configuration_name_list = self.LoadConfigurationNames()
        for configuration_name in configuration_name_list:
            run_configuration = self.LoadConfiguration(configuration_name)
            self._configuration_list.append(run_configuration)
        return self._configuration_list
        
    def LoadConfiguration(self,configuration_name):
        
        startup_key = self.GetConfigurationKey(configuration_name,StartupConfiguration.CONFIGURATION_NAME)
        startup_path_pattern = utils.profile_get_int(startup_key + "/StartupPathPattern",StartupConfiguration.DEFAULT_PROJECT_DIR_PATH)
        #如果是默认路径,不能读取注册表的值
        if startup_path_pattern == StartupConfiguration.DEFAULT_PROJECT_DIR_PATH:
            startup_path = ''
        else:
            startup_path = utils.profile_get(startup_key + "/StartupPath","")
        
        arguments_key = self.GetConfigurationKey(configuration_name,AugumentsConfiguration.CONFIGURATION_NAME)
        interpreter_option = utils.profile_get(arguments_key + "/InterpreterOptions","")
        program_args = utils.profile_get(arguments_key + "/ProgramArgs","")
        
        interpreter_key = self.GetConfigurationKey(configuration_name,InterpreterConfiguration.CONFIGURATION_NAME)
        default_interpreter_name = utils.profile_get(self.ProjectDocument.GetKey() + "/Interpreter",interpretermanager.InterpreterManager().GetCurrentInterpreter().Name)
        interpreter_name = utils.profile_get(interpreter_key + "/InterpreterName",default_interpreter_name)
        
        environment_key = self.GetConfigurationKey(configuration_name,EnvironmentConfiguration.CONFIGURATION_NAME)
        environ_str = utils.profile_get(environment_key + "/Environment","{}")
        environs = eval(environ_str)
        
        args = {
            StartupConfiguration.CONFIGURATION_NAME:StartupConfiguration(self.ProjectDocument,self.MainModuleFile,startup_path_pattern,startup_path),
            AugumentsConfiguration.CONFIGURATION_NAME:AugumentsConfiguration(self.ProjectDocument,self.MainModuleFile,interpreter_option,program_args),
            InterpreterConfiguration.CONFIGURATION_NAME:InterpreterConfiguration(self.ProjectDocument,self.MainModuleFile,interpreter_name),
            EnvironmentConfiguration.CONFIGURATION_NAME:EnvironmentConfiguration(self.ProjectDocument,self.MainModuleFile,environs)
        }
        run_configuration = RunConfiguration(configuration_name,**args)
        run_configuration.IsNewConfiguration = False
        return run_configuration
        

class ProjectConfiguration(BaseConfiguration):
    def __init__(self,project_doc):
        super(ProjectConfiguration,self).__init__(project_doc,None)
        self._configuration_list = []
        
    def LoadConfigurations(self):
        pj_key = self._project_document.GetKey()
        configuration_name_list = utils.profile_get(pj_key + "/" + "ConfigurationList",[])
        for name in configuration_name_list:
            run_configuration = self.LoadConfiguration(name)
            if run_configuration:
                self._configuration_list.append(run_configuration)
            else:
                utils.get_logger().warn("run configuration name %s is not exist",name)
        return self._configuration_list
        
    def LoadConfiguration(self,name):
        file_key,configuration_name = name.split("/")
        relative_file_path = file_key.replace("|",os.sep)
        file_path = os.path.join(self.ProjectDocument.GetPath(),relative_file_path)
        main_module_file = self.ProjectDocument.GetModel().FindFile(file_path)
        file_configuration = FileConfiguration(self.ProjectDocument,main_module_file)
        file_configuration_list = file_configuration.LoadConfigurations()
        for run_configuration in file_configuration_list:
            #项目运行配置名称必须在文件运行配置列表里面存在
            if run_configuration.Name == configuration_name:
                return run_configuration
        utils.get_logger().warn("run configuration name %s is not exist",name)
        return None
        
    def LoadReferenceProjects(self):
        ref_project_names = utils.profile_get(self.ProjectDocument.GetKey() + "/ReferenceProjects",[])
        return ref_project_names
        
    def GetProjectPath(self,project_name):
        for document in GetApp().MainFrame.GetProjectView(generate_event=False).GetOpenProjects():
            if project_name == document.GetModel().Name:
                return document.GetPath()
        return None
        
    def GetReferenceProjectPythonPath(self):
        project_path_list = []
        ref_project_names = self.LoadReferenceProjects()
        for ref_project_name in ref_project_names:
            project_path = self.GetProjectPath(ref_project_name)
            if project_path is not None:
                project_path_list.append(project_path)
            else:
                utils.get_logger().warn("project %s is not exist",ref_project_name)
        return project_path_list
        
    def LoadPythonPath(self):
        python_path_list = self.LoadProjectInternalPath(self.ProjectDocument.GetKey())
        for i,python_path in enumerate(python_path_list):
            python_variable_manager = variablesutils.VariablesManager(self.ProjectDocument)
            path = python_variable_manager.EvalulateValue(python_path)
            python_path_list[i] = path
        if self.IsAppendProjectPath(self.ProjectDocument.GetKey()):
            python_path_list.append(self.ProjectDocument.GetPath())
        external_python_path_list = self.LoadProjectExternalPath(self.ProjectDocument.GetKey())
        reference_path_list = self.GetReferenceProjectPythonPath()
        python_path_list.extend(external_python_path_list)
        python_path_list.extend(reference_path_list)
        return python_path_list

    def GetRunConfigurationName(self):
        pj_key = self.ProjectDocument.GetKey()
        run_configuration_name = utils.profile_get(pj_key + "/RunConfigurationName","")
        if run_configuration_name == "":
            return run_configuration_name
        return run_configuration_name.split('/')[1]

    def LoadEnviron(self):
        return self.LoadProjectEnviron(self.ProjectDocument.GetKey())
    
    @staticmethod
    def LoadProjectEnviron(pj_key):
        environ = utils.profile_get(pj_key + "/Environment",{})
        return environ
        
    @classmethod
    def LoadProjectInternalPath(cls,pj_key):
        return cls.LoadProjectPythonPath(pj_key,"InternalPath")
        
    @classmethod
    def LoadProjectExternalPath(cls,pj_key):
        return cls.LoadProjectPythonPath(pj_key,"ExternalPath")
        
    @staticmethod
    def LoadProjectPythonPath(pj_key,last_part):
        python_path_list = utils.profile_get(pj_key + "/" + last_part,[])
        return python_path_list
        
    @staticmethod
    def LoadProjectInterpreter(pj_key):
        current_interpreter = interpretermanager.InterpreterManager().GetCurrentInterpreter()
        if current_interpreter is None:
            return None
        interpreter_name = utils.profile_get(pj_key + "/Interpreter",current_interpreter.Name)
        return interpreter_name
    
    @staticmethod
    def IsAppendProjectPath(pj_key):
        return utils.profile_get_int(pj_key + "/AppendProjectPath",1)
        
