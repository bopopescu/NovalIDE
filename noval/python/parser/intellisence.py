from noval import _,GetApp
import noval.util.appdirs as appdirs
import noval.python.interpreter.Interpreter as Interpreter
import noval.python.interpreter.InterpreterManager as interpretermanager
import subprocess
import noval.util.apputils as apputils
from noval.util import singleton 
import os
import threading
import time
from noval.python.parser import fileparser
from noval.python.parser import config
from noval.python.parser import builtinmodule
from noval.python.parser.utils import CmpMember,py_sorted
import glob
from noval.python.parser import nodeast
from noval.python.parser import scope
import pickle
import signal
from dummy.userdb import UserDataDb
import noval.util.utils as utils
from noval.python.parser import run
import datetime
import copy
import noval.consts as consts

class ModuleLoader(object):
    CHILD_KEY = "childs"
    NAME_KEY = "name"
    TYPE_KEY = "type"
    LINE_KEY = "line"
    COL_KEY = "col"
    PATH_KEY = "path"
    MEMBERS_KEY = "members"
    MEMBER_LIST_KEY = "member_list"
    FULL_NAME_KEY = "full_name"
    BUILTIN_KEY = "is_builtin"
    def __init__(self,name,members_file,member_list_file,mananger):
        self._name = name
        self._members_file = members_file
        self._member_list_file = member_list_file
        self._manager = mananger
        self._path = None
        self._is_builtin = False
        self._data = None
        self._doc = None
    @property
    def Name(self):
        return self._name

    def LoadMembers(self):
        if self._data is None:
            with open(self._members_file,'rb') as f:
                self._data = pickle.load(f)
                self._is_builtin = self._data.get(self._is_builtin,False)
                self._path = self._data.get(self.PATH_KEY)
                self._doc = self._data.get('doc',None)
        return self._data

    def GetDoc(self):
        self.LoadMembers()
        return self._doc

    def LoadMembeList(self):
        member_list = []
        with open(self._member_list_file) as f:
            for line in f.readlines():
                if -1 == line.find("/"):
                    member_list.append(line.strip())
                else:
                    names = line.strip().split("/")
                    module_name = names[0]
                    ref_name = names[1]
                    if ref_name != "*":
                        member_list.append(ref_name)
                    else:
                        ref_module = self._manager.GetModule(module_name)
                        if ref_module is None:
                            continue
                        else:
                            member_list.extend(ref_module.GetMemberList())
            ##return map(lambda s:s.strip(),f.readlines())
        return member_list

    def GetMemberList(self):
        member_list = self.LoadMembeList()
        member_list.sort(CmpMember)
        return member_list

    def GetMembersWithName(self,name):
        strip_name = name.strip()
        if strip_name == "":
            names = []
        else:
            names = strip_name.split(".")
        return self.GetMembers(names)

    def GetMembers(self,names):
        if len(names) == 0:
            return self.GetMemberList()
        data = self.LoadMembers()
        member = self.GetMember(data[self.CHILD_KEY],names)
        member_list = []
        if member is not None:
            if member[self.TYPE_KEY] == config.NODE_MODULE_TYPE:
                child_module = self._manager.GetModule(member[self.FULL_NAME_KEY])
                member_list = child_module.GetMemberList()
            else:
                if member.has_key(self.CHILD_KEY):
                    for child in member[self.CHILD_KEY]:
                        member_list.append(child[self.NAME_KEY])
                ##get members in parent inherited classes
                if member[self.TYPE_KEY] == config.NODE_CLASSDEF_TYPE:
                    member_list.extend(self.GetBaseMembers(member,names))                    
        return member_list

    def GetBaseMembers(self,member,names):
        base_members = []
        bases = member.get('bases',[])
        for base in bases:
            base_members.extend(self.GetMembers(names[0:(len(names) -1)] + [base]))
        return base_members

    def FindChildDefinitionInBases(self,bases,names):
        for base in bases:
            for child in self._data[self.CHILD_KEY]:
                if child[self.NAME_KEY] == base:
                    return self.FindChildDefinition(child[self.CHILD_KEY],names)
        return None
        
    def GetMember(self,childs,names):
        for child in childs:
            if child[self.NAME_KEY] == (names[0].strip()):
                if len(names) == 1:
                    return child
                else:
                    if child[self.TYPE_KEY] != config.NODE_MODULE_TYPE:
                        return self.GetMember(child[self.CHILD_KEY],names[1:])
                    else:
                        child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
                        data = child_module.LoadMembers()
                        return self.GetMember(data[self.CHILD_KEY],names[1:])
        return None

    def FindDefinitionWithName(self,name):
        strip_name = name.strip()
        if strip_name == "":
            names = []
        else:
            names = strip_name.split(".")
        return self.FindDefinition(names)

    def FindDefinition(self,names):
        data = self.LoadMembers()
        if self._is_builtin:
            return None
        if len(names) == 0:
            return self.MakeModuleScope()
        child_definition =  self.FindChildDefinition(data[self.CHILD_KEY],names)
        if child_definition is None:
            return self.FindInRefModule(data.get('refs',[]),names)
        return child_definition

    def FindInRefModule(self,refs,names):
        for ref in refs:
            ref_module_name = ref['module']
            ref_module = self._manager.GetModule(ref_module_name)
            if ref_module is None:
                continue
            for ref_name in ref['names']:
                if ref_name['name'] == '*' or ref_name['name'] == names[0]:
                    member_definition = ref_module.FindDefinition(names)
                    if member_definition is not None:
                        return member_definition
        return None

    def MakeModuleScope(self):
        module = nodeast.Module(self._name,self._path,self._doc)
        module_scope = scope.ModuleScope(module,-1)
        return module_scope

    def MakeDefinitionScope(self,child):
        if child.get(self.TYPE_KEY) == config.NODE_MODULE_TYPE:
            child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
            child_module._path = child[self.PATH_KEY]
            child_module.GetDoc()
            return child_module.MakeModuleScope()
        module_scope = self.MakeModuleScope()
        self.MakeChildScope(child,module_scope.Module)
        module_scope.MakeModuleScopes()
        return module_scope.ChildScopes[0]
        
    def MakeChildScope(self,child,parent):
        name = child[self.NAME_KEY]
        line_no = child.get(self.LINE_KEY,-1)
        col = child.get(self.COL_KEY,-1)
        doc = child.get('doc',None)
        if child[self.TYPE_KEY] == config.NODE_FUNCDEF_TYPE:
            datas = child.get('args',[])
            args = []
            for arg_data in datas:
                arg = nodeast.ArgNode(name=arg_data.get('name'),line=arg_data.get('line'),\
                        col=arg_data.get('col'),is_default=arg_data.get('is_default'),\
                        is_var=arg_data.get('is_var',False),is_kw=arg_data.get('is_kw',False),parent=None)
                args.append(arg)
            node = nodeast.FuncDef(name,line_no,col,parent,doc,is_method=child.get('is_method',False),\
                    is_class_method=child.get('is_class_method',False),args=args)
        elif child[self.TYPE_KEY] == config.NODE_CLASSDEF_TYPE:
            bases = child.get('bases',[])
            for i,base in enumerate(bases):
                bases[i] = parent.Name + "." + base
            #print (bases)
            node = nodeast.ClassDef(name,line_no,col,parent,doc,bases=bases)
            for class_child in child.get(self.CHILD_KEY,[]):
                self.MakeChildScope(class_child,node)
        elif child[self.TYPE_KEY] == config.NODE_OBJECT_PROPERTY or \
                child[self.TYPE_KEY] == config.NODE_CLASS_PROPERTY:
            node = nodeast.PropertyDef(name,line_no,col,config.ASSIGN_TYPE_UNKNOWN,"",parent)
        elif child[self.TYPE_KEY] == config.NODE_UNKNOWN_TYPE:
            node = nodeast.UnknownNode(line_no,col,parent)
                
    def FindChildDefinition(self,childs,names):
        for child in childs:
            if child[self.NAME_KEY] == (names[0].strip()):
                if len(names) == 1:
                    return self.MakeDefinitionScope(child)
                else:
                    if child[self.TYPE_KEY] != config.NODE_MODULE_TYPE:
                        child_definition = self.FindChildDefinition(child.get(self.CHILD_KEY,[]),names[1:])
                        if child_definition is None and child[self.TYPE_KEY] == config.NODE_CLASSDEF_TYPE:
                            bases = child.get('bases',[])
                            #search member definition in parent inherited classes
                            child_definition = self.FindChildDefinitionInBases(bases,names[1:])
                        return child_definition
                    else:
                        child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
                        data = child_module.LoadMembers()
                        return child_module.FindChildDefinition(data[self.CHILD_KEY],names[1:])
        return None
        
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
        if not os.path.exists(builtin_data_path):
            utils.get_logger().error('builtin data path:%s is not exist',builtin_data_path)
            return
        self.LoadIntellisenceDirData(builtin_data_path)
    
    def LoadIntellisenceDirData(self,data_path):
        name_sets = set()
        for filepath in glob.glob(os.path.join(data_path,"*.$members")):
            filename = os.path.basename(filepath)
            module_name = '.'.join(filename.split(".")[0:-1])
            name_sets.add(module_name)
        for name in name_sets:
            d = dict(members=os.path.join(data_path,name +".$members"),\
                     member_list=os.path.join(data_path,name +".$memberlist"))
            self.module_dicts[name] = d

    def Load(self,interpreter,share_user_data=False):
        t = threading.Thread(target=self.LoadInterperterData,args=(interpreter,share_user_data))
        t.start()
        
    def LoadInterperterData(self,interpreter,share_user_data):
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
        if share_user_data:
            self._manager.ShareUserData()
        
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
            utils.get_logger().error("could not find builtin module %s, builtin database is not success loaded",interpreter.BuiltinModuleName)
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
            self._builtin_data_path = os.path.join(appdirs.get_app_path(), "noval", "tool", "data","intellisence","builtins")
        self.module_dicts = {}
        self._loader = IntellisenceDataLoader(self.data_root_path,self._builtin_data_path,self)
        self._is_running = False
        self._process_obj = None
        self._is_stopped = False
        
    def Stop(self):
        self._is_stopped = True
        if self._process_obj != None and self.IsRunning:
            for pid in utils.get_child_pids(self._process_obj.pid):
                os.kill(pid,signal.SIGTERM)
            self._process_obj.kill()
           # self._process_obj.terminate(gracePeriod=2.0)
            #os.killpg( p.pid,signal.SIGUSR1)
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
                    database_version]
        if apputils.is_windows():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None
        env = os.environ.update(dict(PYTHONPATH=utils.get_app_path()))
        self._process_obj = subprocess.Popen(cmd_list,startupinfo=startupinfo,cwd=os.path.join(utils.get_app_path(), "noval", "python","parser"),env=env)
        interpreter.Analysing = True
        utils.update_statusbar(_("Updating interpreter %s intellisence database") % interpreter.Name)
        self._is_running = interpreter.Analysing
        #if current interpreter is analysing,load data at end
        if interpreter == interpretermanager.InterpreterManager().GetCurrentInterpreter():
            load_data_end = True
        self.Wait(interpreter,progress_dlg,load_data_end)
        
    def Wait(self,interpreter,progress_dlg,load_data_end):
        t = threading.Thread(target=self.WaitProcessEnd,args=(interpreter,progress_dlg,load_data_end))
        t.start()
        
    def WaitProcessEnd(self,interpreter,progress_dlg,load_data_end):
        self._process_obj.wait()
        interpreter.Analysing = False
        interpreter.IsAnalysed = True
        self._is_running = interpreter.Analysing
        if progress_dlg != None:
            progress_dlg.KeepGoing = False
        if load_data_end and not self._is_stopped:
            self.load_intellisence_data(interpreter) 
        if progress_dlg == None:
            self.ShareUserData()
        if not self._is_stopped:
            utils.update_statusbar(_("Intellisence database has been updated"))
        else:
            utils.get_logger().warn("smart intellisence analyse has been stopped by user")
    
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
            last_update_time = factory.GetLastUpdateTime(intellisence_data_path)
            last_datetime = datetime.datetime.strptime(last_update_time, factory.ISO_8601_DATETIME_FORMAT)
        except:
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
        if not self.IsInterpreterNeedUpdateDatabase(current_interpreter):
            utils.GetLogger().info("interpreter %s is no need to update database" % current_interpreter.Name)
            self.load_intellisence_data(current_interpreter,True)
            return
        try:
            self.generate_intellisence_data(current_interpreter,load_data_end=True)
        except Exception as e:
            utils.get_logger().error('load interpreter name %s path %s version %s intellisence data path %s error: %s',current_interpreter.Name,\
                                    current_interpreter.Path,current_interpreter.Version,\
                                        os.path.join(self.data_root_path,str(current_interpreter.Id)),e)
            utils.get_logger().exception("")
        
    def load_intellisence_data(self,interpreter,share_user_data=False):
        self._loader.Load(interpreter,share_user_data)
        
    def GetImportList(self):
        return self._loader.ImportList
        
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
        if name in self._loader.module_dicts:
            return ModuleLoader(name,self._loader.module_dicts[name][ModuleLoader.MEMBERS_KEY],\
                        self._loader.module_dicts[name][ModuleLoader.MEMBER_LIST_KEY],self)
        return None

    def HasModule(self,name):
        return self._loader.module_dicts.has_key(name)

    def GetModuleMembers(self,module_name,child_name):
        module = self.GetModule(module_name)
        if module is None:
            return []
        return module.GetMembersWithName(child_name)

    def GetModuleMember(self,module_name,child_name):
        module = self.GetModule(module_name)
        if module is None:
            return None
        return module.FindDefinitionWithName(child_name)

    def GetBuiltinModuleMembers(self):
        if self.GetBuiltinModule() is None:
            return
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
        scope = module.FindDefinitionWithName(child_name)
        if scope is None:
            return ''
        return scope.GetArgTip()