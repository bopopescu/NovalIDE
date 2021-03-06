# -*- coding: utf-8 -*-
from noval import _,GetApp
import noval.util.appdirs as appdirs
import noval.python.interpreter.interpreter as pythoninterpreter
import noval.python.interpreter.interpretermanager as interpretermanager
import subprocess
import noval.util.apputils as apputils
from noval.util import singleton 
import os
import threading
import time
from noval.python.parser import config
from noval.python.parser import builtinmodule
from noval.python.parser.utils import CmpMember,py_sorted,NeedRenewDatabase
import glob
import signal
from dummy.userdb import UserDataDb
import noval.util.utils as utils
import datetime
import copy
import noval.consts as consts
from moduleloader import *

        
class IntellisenceDataLoader(object):
    def __init__(self,data_location,_builtin_data_location,manager):
        self._data_location = data_location
        self.__builtin_data_location = _builtin_data_location
        self.module_dicts = {}
        self.import_list = []
        self._builtin_module = None
        self._manager = manager
      
    def LodBuiltInData(self,interpreter):
        if interpreter.IsV2():
            builtin_data_path = os.path.join(self.__builtin_data_location,"2")
        else:
            builtin_data_path = os.path.join(self.__builtin_data_location,"3")

        utils.get_logger().debug('load builtin data path:%s',builtin_data_path)
        if not os.path.exists(builtin_data_path) or NeedRenewDatabase(builtin_data_path,config.DATABASE_VERSION):
            utils.get_logger().debug('builtin data path:%s is not exist',builtin_data_path)
            self.GenerateBuiltinData(interpreter,builtin_data_path)
        self.LoadIntellisenceDirData(builtin_data_path)
        
    def GenerateBuiltinData(self,interpreter,builtin_data_path):
        script_path = os.path.join(utils.get_app_path(), "noval", "python","parser", "run_builtin.py")
        cmd_list = [interpreter.Path,script_path,builtin_data_path, config.DATABASE_VERSION]
        if apputils.is_windows():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None
        work_dir = os.path.join(utils.get_app_path(), "noval", "python","parser")
        subprocess.Popen(cmd_list,startupinfo=startupinfo,cwd=work_dir)
    
    def LoadIntellisenceDirData(self,data_path):
        name_sets = set()
        for filepath in glob.glob(os.path.join(data_path,"*" + config.MEMBERS_FILE_EXTENSION)):
            filename = os.path.basename(filepath)
            module_name = '.'.join(filename.split(".")[0:-1])
            name_sets.add(module_name)

        for name in name_sets:
            d = dict(members=os.path.join(data_path,name +config.MEMBERS_FILE_EXTENSION),\
                     member_list=os.path.join(data_path,name +config.MEMBERLIST_FILE_EXTENSION))
            self.module_dicts[name] = d

    def Load(self,interpreter):
        t = threading.Thread(target=self.LoadInterperterData,args=(interpreter,))
        t.start()
        
    def LoadInterperterData(self,interpreter):
        utils.update_statusbar(_("Loading intellisence database"))
        self.module_dicts.clear()
        #should copy builtin list to import_list,otherwise it will change
        #the interpreter.Builtins when load import list
        self.import_list = copy.copy(interpreter.Builtins)
        root_path = os.path.join(self._data_location,str(interpreter.Id))
        intellisence_data_path = os.path.join(root_path,interpreter.Version)
        if not os.path.exists(intellisence_data_path):
            utils.update_statusbar(_("Finish load Intellisence database"))
            return
        self.LoadIntellisenceDirData(intellisence_data_path)
        self.LodBuiltInData(interpreter)
        self.LoadImportList()
        self.LoadBuiltinModule(interpreter)
        utils.update_statusbar(_("Finish load Intellisence database"))
        
    def LoadImportList(self):
        for key in self.module_dicts.keys():
            if key.find(".") == -1:
                if key not in self.import_list:
                    self.import_list.append(key)
        self.import_list = py_sorted(self.import_list,CmpMember)
        
    @property
    def ImportList(self):
        return self.import_list
        
    def LoadBuiltinModule(self,interpreter):
        utils.get_logger().debug('current interpreter builtin module name is:%s',interpreter.BuiltinModuleName)
        builtin_module_loader = self._manager.GetModule(interpreter.BuiltinModuleName)
        if builtin_module_loader is None:
            utils.get_logger().debug("could not find builtin module %s, builtin database is not success loaded",interpreter.BuiltinModuleName)
            return
        data = builtin_module_loader.LoadMembers()
        self._builtin_module = builtinmodule.BuiltinModule(builtin_module_loader.Name)
        self._builtin_module.load(data)
        
    @property
    def BuiltinModule(self):
        return self._builtin_module

@singleton.Singleton
class IntellisenceManager(object):
    def __init__(self):
        self.data_root_path = os.path.join(appdirs.get_user_data_path(),"intellisence")
        if apputils.is_windows():
            self._builtin_data_path = os.path.join(self.data_root_path,"builtins")
        else:
            self._builtin_data_path = os.path.join(appdirs.get_app_path(), "noval", "data","intellisence","builtins")
        self.module_dicts = {}
        self._loader = IntellisenceDataLoader(self.data_root_path,self._builtin_data_path,self)
        self._is_running = False
        self._process_obj = None
        self._is_stopped = False
        self.unfinish_files = {}
        
    def Stop(self):
        self.WriteUnfinishFiles()
        self._is_stopped = True
        
    @property
    def IsRunning(self):
        return self._is_running
        
    def GetInterpreterDatabasePath(self,interpreter):
        return os.path.join(self.data_root_path,str(interpreter.Id))

    def GetInterpreterIntellisenceDataPath(self,interpreter):
        return os.path.join(self.GetInterpreterDatabasePath(interpreter),interpreter.Version)
        
    def generate_intellisence_data(self,interpreter,progress_dlg = None,load_data_end=False):
        if interpreter.IsBuiltIn:
            return
        sys_path_list = interpreter.SysPathList
        script_path = os.path.join(utils.get_app_path(), "noval", "python","parser", "run.py")
        database_version = config.DATABASE_VERSION
        cmd_list = [interpreter.Path,script_path,self.GetInterpreterDatabasePath(interpreter),\
                    database_version,str(int(GetApp().GetDebug()))]
        if apputils.is_windows():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None
        work_dir = os.path.join(utils.get_app_path(), "noval", "python","parser")
        self._process_obj = subprocess.Popen(cmd_list,startupinfo=startupinfo,cwd=work_dir)
        interpreter.Analysing = True
        utils.update_statusbar(_("Updating interpreter %s intellisence database") % interpreter.Name)
        self._is_running = interpreter.Analysing
        #if current interpreter is analysing,load data at end
        if interpreter == interpretermanager.InterpreterManager().GetCurrentInterpreter():
            load_data_end = True
        self.Wait(interpreter,progress_dlg,load_data_end)
        
    def Wait(self,interpreter,progress_dlg,load_data_end):
        #设置为后台线程,防止退出程序时卡死
        t = threading.Thread(target=self.WaitProcessEnd,daemon=True,args=(interpreter,progress_dlg,load_data_end))
        t.start()
        
    def WaitProcessEnd(self,interpreter,progress_dlg,load_data_end):
        self._process_obj.wait()
        interpreter.Analysing = False
        interpreter.IsAnalysed = True
        self._is_running = interpreter.Analysing
        if progress_dlg != None:
            progress_dlg.KeepGoing = False
            progress_dlg.destroy()
        if load_data_end and not self._is_stopped:
            self.load_intellisence_data(interpreter)
        if not self._is_stopped:
            utils.update_statusbar(_("Intellisence database has been updated"))
        else:
            utils.get_logger().warn("smart intellisence analyse has been stopped by user")
            
    def GetLastUpdateTime(self,database_location):
        with open(os.path.join(database_location,config.UPDATE_FILE)) as f:
            return f.read()
            
    def AsyncShareUserData(self):
        t = threading.Thread(target=self.ShareUserData)
        t.start()
    
    def ShareUserData(self):
        if GetApp().GetDebug():
            return
        UserDataDb().ShareUserData()
        UserDataDb().RecordStart()
        
    def IsInterpreterNeedUpdateDatabase(self,interpreter):
        update_interval_option = utils.profile_get_int("DatabaseUpdateInterval",consts.UPDATE_ONCE_STARTUP)
        if update_interval_option == consts.UPDATE_ONCE_STARTUP:
            return True
            
        try:
            #if could not find last update time,update database force
            intellisence_data_path = self.GetInterpreterIntellisenceDataPath(interpreter)
            last_update_time = self.GetLastUpdateTime(intellisence_data_path)
            last_datetime = datetime.datetime.strptime(last_update_time, config.ISO_8601_DATETIME_FORMAT)
        except:
            utils.get_logger().exception('')
            return True
        now_datetime = datetime.datetime.now()
        if update_interval_option == consts.UPDATE_ONCE_DAY:
            return now_datetime >  last_datetime + datetime.timedelta(hours=24)
        elif update_interval_option == consts.UPDATE_ONCE_WEEK:
            return now_datetime >  last_datetime + datetime.timedelta(days=7)
        elif update_interval_option == consts.UPDATE_ONCE_MONTH:
            return now_datetime >  last_datetime + datetime.timedelta(days=30)
        elif update_interval_option == consts.NEVER_UPDATE_ONCE:
            return False

    def generate_default_intellisence_data(self):
        current_interpreter = interpretermanager.InterpreterManager().GetCurrentInterpreter()
        if current_interpreter is None:
            return
        self.AsyncShareUserData()
        if not self.IsInterpreterNeedUpdateDatabase(current_interpreter):
            utils.get_logger().info("interpreter %s is no need to update database" % current_interpreter.Name)
            self.load_intellisence_data(current_interpreter)
            return
        utils.get_logger().info("interpreter %s is need to update database" % current_interpreter.Name)
        try:
            self.generate_intellisence_data(current_interpreter,load_data_end=True)
        except Exception as e:
            utils.get_logger().error('load interpreter name %s path %s version %s intellisence data path %s error: %s',current_interpreter.Name,\
                                    current_interpreter.Path,current_interpreter.Version,\
                                        os.path.join(self.data_root_path,str(current_interpreter.Id)),e)
            utils.get_logger().exception("")
        
    def load_intellisence_data(self,interpreter):
        self._loader.Load(interpreter)
        
    def GetImportList(self):
        #全局加载的导入模块列表
        import_list = self._loader.ImportList
        current_project = GetApp().MainFrame.GetProjectView(False).GetCurrentProject()
        if current_project is not None:
            #当前项目里面的导入模块列表
            try:
                l = copy.copy(current_project.db_loader.import_list)
                l.extend(import_list)
                import_list = l
            except:
                pass
        return import_list
        
    def GetBuiltinMemberList(self,name):
        if self._loader.BuiltinModule is None:
            return False,[]
        return self._loader.BuiltinModule.GetBuiltInTypeMembers(name)
        
    def GetMemberList(self,name):
        names = name.split(".")
        name_count = len(names)
        i = 1
        module_name = ""
        while i <= name_count:
            fit_name = ".".join(names[:i])
            if self.HasModule(fit_name):
                module_name = fit_name
            else:
                break
            i += 1
        if not self.HasModule(module_name):
            return []
        module = self.GetModule(module_name)
        child_names = names[i:]
        return module.GetMembers(child_names)
        
    def GetBuiltinModule(self):
        return self._loader.BuiltinModule
        
    def GetTypeObjectMembers(self,obj_type):
        if self._loader.BuiltinModule is None or obj_type == config.ASSIGN_TYPE_UNKNOWN:
            return []
        type_obj = self._loader.BuiltinModule.GetTypeNode(obj_type)
        return type_obj.GetMemberList()

    def GetModule(self,name):
        d = self.GetModules()
        if name in d:
            return ModuleLoader(name,d[name][ModuleLoader.MEMBERS_KEY],d[name][ModuleLoader.MEMBER_LIST_KEY],self)
        return None

    def HasModule(self,name):
        return name in self.GetModules()
        
    def GetModules(self):
        #所有模块为当前项目的所有模块加上全局模块
        current_project = GetApp().MainFrame.GetProjectView(False).GetCurrentProject()
        if current_project is None:
            return self._loader.module_dicts
        try:
            d = copy.copy(self._loader.module_dicts)
            d.update(current_project.db_loader.module_dicts)
            return d
        except:
            return self._loader.module_dicts

    def GetModuleMembers(self,module_name,child_name):
        module = self.GetModule(module_name)
        if module is None:
            return []
        return module.GetMembersWithName(child_name)

    def GetModuleMember(self,module_name,child_name):
        module = self.GetModule(module_name)
        if module is None:
            return []
        return module.FindDefinitionWithName(child_name)

    def GetBuiltinModuleMembers(self):
        if self.GetBuiltinModule() is None:
            return []
        utils.GetLogger().debug('get builtin module name is:%s',self.GetBuiltinModule().Name)
        return self.GetModuleMembers(self.GetBuiltinModule().Name,"")

    def GetModuleDoc(self,module_name):
        module = self.GetModule(module_name)
        if module is None:
            return None
        return module.GetDoc()
        
    def GetModuleMemberArgmentTip(self,module_name,child_name):
        module = self.GetModule(module_name)
        if module is None:
            return None
        scopes = module.FindDefinitionWithName(child_name)
        if not scopes:
            return ''
        return scopes[0].GetArgTip()
        
    def AddUnfinishModuleFile(self,module_file):
        '''
            将需要再次分析的模块添加到unfinish列表当中
        '''
        interpreter = GetApp().GetCurrentInterpreter()
        if not interpreter.Path in self.unfinish_files:
            self.unfinish_files[interpreter.Path] = set([module_file])
        else:
            self.unfinish_files[interpreter.Path].add(module_file)
        
    def WriteUnfinishFiles(self):
        '''
            保存unfinish列表,以便下次运行run.py时强制分析这些模块并重新生成数据库
        '''
        if len(self.unfinish_files) > 0:
            unfinished_file_name = "unfinish.txt"
            for interpreter_path in self.unfinish_files:
                interpreter = interpretermanager.InterpreterManager().GetInterpreterByPath(interpreter_path)
                database_path = self.GetInterpreterDatabasePath(interpreter)
                unfinished_file_path = os.path.join(database_path,unfinished_file_name)
                with open(unfinished_file_path,"w") as f:
                    unfinish_file_paths = list(self.unfinish_files[interpreter_path])
                    for path in unfinish_file_paths:
                        f.write(path + "\n")