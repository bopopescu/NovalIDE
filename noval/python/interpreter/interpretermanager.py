# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        InterpreterManager.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-10
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------

import sys
import os
from noval import GetApp,_,NewId
from noval.util.singleton import Singleton
import noval.util.apputils as apputils
import pickle
from noval.python.interpreter import interpreter as pythoninterpreter
import json
import noval.util.utils as utils
from tkinter import messagebox
from noval.ui_base import GetSingleChoiceIndex
import noval.constants as constants
import noval.python.explain_environment as explain_environment

BUILTIN_INTERPRETER_NAME = "Builtin_Interpreter"

@Singleton
class InterpreterManager:

    KEY_PREFIX = "interpreters"
    def __init__(self):
        self.interpreters = []
        self.DefaultInterpreter = None
        self.CurrentInterpreter = None

    def LoadDefaultInterpreter(self):
        if self.LoadPythonInterpretersFromConfig():
            self.SetCurrentInterpreter(self.DefaultInterpreter)
            return
        self.LoadPythonInterpreters()
        if 0 == len(self.interpreters):
            if apputils.is_windows():
                messagebox.showwarning(_("Python interpreter not found"),_("No python interpreter found in your computer,will use the builtin interpreter instead"))
            else:
                messagebox.showwarning( _("No Interpreter"),_("Python interpreter not found!"))

        if apputils.is_windows() and None == self.GetInterpreterByName(BUILTIN_INTERPRETER_NAME):
            self.LoadBuiltinInterpreter()
        self.interpreters = InterpreterManager().interpreters
        if 1 == len(self.interpreters):
            self.MakeDefaultInterpreter()
        elif 1 < len(self.interpreters):
            self.ChooseDefaultInterpreter()
        self.SetCurrentInterpreter(self.DefaultInterpreter)
        #when load interpreter first,save the interpreter info to config
        self.SavePythonInterpretersConfig()
        
    def ShowChooseInterpreterDlg(self,parent=None):
        choices = []
        for interpreter in self.interpreters:
            choices.append(interpreter.Name)
        result = GetSingleChoiceIndex(parent , _("Choose Interpreter"),_("Please Choose Default Interpreter:"),choices,default_selection=0)
        if result != -1:
            name = choices[result]
            interpreter = self.GetInterpreterByName(name)
            return interpreter
        return None

    def ChooseDefaultInterpreter(self):
        interpreter = self.ShowChooseInterpreterDlg()
        if interpreter:
            self.SetDefaultInterpreter(interpreter)
        else:
            messagebox.showwarning(_("Choose Interpreter"),_("No default interpreter selected, application may not run normal!"))
            del self.interpreters[:]
            self.SetDefaultInterpreter(None)

    def GetInterpreterByName(self,name):
        for interpreter in self.interpreters:
            if name == interpreter.Name:
                return interpreter
        return None

    def GetInterpreterByPath(self,path):
        for interpreter in self.interpreters:
            if path == interpreter.Path:
                return interpreter
        return None

    def LoadPythonInterpreters(self):
        if apputils.is_windows():
            import noval.util.registry as registry
            ROOT_KEY_LIST = [registry.HKEY_LOCAL_MACHINE,registry.HKEY_CURRENT_USER]
            ROOT_KEY_NAMES = ['LOCAL_MACHINE','CURRENT_USER']
            for k,root_key in enumerate(ROOT_KEY_LIST):
                try:
                    with registry.Registry(root_key).Open(r"SOFTWARE\Python\Pythoncore") as open_key:
                        for name in open_key.EnumChildKeyNames():
                            try:
                                child_key = open_key.Open(name)
                                install_path = child_key.Read("InstallPath")
                                interpreter = pythoninterpreter.PythonInterpreter(name,os.path.join(install_path,pythoninterpreter.PythonInterpreter.CONSOLE_EXECUTABLE_NAME))
                                if not interpreter.IsValidInterpreter:
                                    utils.get_logger().error("load interpreter name %s path %s version %s is not a valid interpreter",interpreter.Name,interpreter.Path,interpreter.Version)
                                    continue
                                self.interpreters.insert(0,interpreter)
                                help_key = child_key.Open("Help")
                                help_path = help_key.Read("Main Python Documentation")
                                interpreter.HelpPath = help_path
                                help_key.CloseKey()
                                child_key.CloseKey()
                                utils.get_logger().debug("load python interpreter name:%s path:%s version:%s help path:%s",interpreter.Name,interpreter.Path,interpreter.Version,interpreter.HelpPath)
                            except Exception as e:
                                utils.get_logger().warn("read python child regkey %s\\xxx\\%s error:%s",ROOT_KEY_NAMES[k],name,e)
                                utils.get_logger().exception("")
                                continue
                except Exception as e:
                    utils.get_logger().warn("load python interpreter from regkey %s error:%s",ROOT_KEY_NAMES[k],e)
                    ####utils.get_logger().exception("")
                    continue
        else:
            targets = explain_environment.get_targets("python")
            target_executables = [target[1] for target in targets]
            executable_path = sys.executable
            if executable_path not in target_executables:
                targets.append(("default",executable_path))
                    
            for cmd,target in targets:
                interpreter = pythoninterpreter.PythonInterpreter(cmd,target)
                self.interpreters.append(interpreter)

    def LoadPythonInterpretersFromConfig(self):
        '''
            从配置文件或者注册表中读取python解释器信息
        '''
        config = GetApp().GetConfig()
        #windows从注册吧中读取
        if apputils.is_windows():
            data = config.Read(self.KEY_PREFIX)
            if not data:
                return False
            has_builtin_interpreter = False
            if utils.is_py2():
                try:
                    lst = pickle.loads(data.encode('ascii'))
                except Exception as e:
                    lst = []
            elif utils.is_py3():
                #python3存储的是binary类型
                if type(data) == bytes:
                    lst = pickle.loads(data)
                else:
                    #兼容python2存储类型
                    lst = pickle.loads(bytes(data,encoding = utils.get_default_encoding()),encoding=utils.get_default_encoding())
            for l in lst:
                is_builtin = l.get('is_builtin',False)
                if is_builtin:
                    interpreter = pythoninterpreter.BuiltinPythonInterpreter(l['name'],l['path'],l['id'])
                    has_builtin_interpreter = True
                else:
                    interpreter = pythoninterpreter.PythonInterpreter(l['name'],l['path'],l['id'],True)
                interpreter.Default = l['default']
                if interpreter.Default:
                    self.SetDefaultInterpreter(interpreter)
                data = {
                    'version': l['version'],
                    'minor_version':l.get('minor_version',''),
                    #should convert tuple type to list
                    'builtins': list(l['builtins']),
                    #'path_list' is the old key name of sys_path_list,we should make compatible of old version
                    'sys_path_list': l.get('sys_path_list',l.get('path_list')),
                    'python_path_list': l.get('python_path_list',[]),
                    'is_builtin':is_builtin
                }
                interpreter.SetInterpreter(**data)
                interpreter.HelpPath = l.get('help_path','')
                interpreter.Environ.SetEnviron(l.get('environ',{}))
                interpreter.Packages = interpreter.LoaPackagesFromDict(l.get('packages',{}))
                self.interpreters.append(interpreter)
                if utils.is_py2():
                    path = interpreter.Path.decode(apputils.get_default_encoding())
                else:
                    path = interpreter.Path
                utils.get_logger().debug('load python interpreter from app config name:%s path:%s,version:%s,builtin:%s',\
                                     interpreter.Name,path,interpreter.Version,interpreter.IsBuiltIn)
            if len(self.interpreters) > 1 or (len(self.interpreters) == 1 and not has_builtin_interpreter):
                return True
        else:
            #Linux从配置文件中读取
            prefix = self.KEY_PREFIX
            data = config.Read(prefix)
            if not data:
                return False
            ids = data.split(os.pathsep)
            for id in ids:
                name = config.Read("%s/%s/Name" % (prefix,id))
                path = config.Read("%s/%s/Path" % (prefix,id))
                is_default = config.ReadInt("%s/%s/Default" % (prefix,id))
                version = config.Read("%s/%s/Version" % (prefix,id))
                minor_version = config.Read("%s/%s/MinorVersion" % (prefix,id),"")
                sys_paths = config.Read("%s/%s/SysPathList" % (prefix,id))
                python_path_list = config.Read("%s/%s/PythonPathList" % (prefix,id),"")
                builtins = config.Read("%s/%s/Builtins" % (prefix,id))
                environ = json.loads(config.Read("%s/%s/Environ" % (prefix,id),"{}"))
                packages = json.loads(config.Read("%s/%s/Packages" % (prefix,id),"{}"))
                interpreter = pythoninterpreter.PythonInterpreter(name,path,id,True)
                interpreter.Default = is_default
                interpreter.Environ.SetEnviron(environ)
                interpreter.Packages = interpreter.LoaPackagesFromDict(packages)
                if interpreter.Default:
                    self.SetDefaultInterpreter(interpreter)
                data = {
                    'version': version,
                    'minor_version':minor_version,
                    'builtins': builtins.split(os.pathsep),
                    'sys_path_list': sys_paths.split(os.pathsep),
                    'python_path_list':python_path_list.split(os.pathsep)
                }
                interpreter.SetInterpreter(**data)
                self.interpreters.append(interpreter)
            if len(self.interpreters) > 0:
                return True

        return False

    def ConvertInterpretersToDictList(self):
        lst = []
        for interpreter in self.interpreters:
            d = dict(id=interpreter.Id,name=interpreter.Name,version=interpreter.Version,path=interpreter.Path,\
                        default=interpreter.Default,sys_path_list=interpreter.SysPathList,python_path_list=interpreter.PythonPathList,\
                        builtins=interpreter.Builtins,help_path=interpreter.HelpPath,\
                        environ=interpreter.Environ.environ,packages=interpreter.DumpPackages(),is_builtin=interpreter.IsBuiltIn,
                        minor_version=interpreter.MinorVersion)
            lst.append(d)
        return lst

    def SavePythonInterpretersConfig(self):
        '''
            保存解释器配置信息
        '''
        config = GetApp().GetConfig()
        #windows写入注册表
        if apputils.is_windows():
            dct = self.ConvertInterpretersToDictList()
            if dct == []:
                return
            config.Write(self.KEY_PREFIX ,pickle.dumps(dct))
        #Linux写入配置文件
        else:
            prefix = self.KEY_PREFIX
            id_list = [ str(kl.Id) for kl in self.interpreters ]
            config.Write(prefix,os.pathsep.join(id_list))
            for kl in self.interpreters:
                config.WriteInt("%s/%d/Id"%(prefix,kl.Id),kl.Id)
                config.Write("%s/%d/Name"%(prefix,kl.Id),kl.Name)
                config.Write("%s/%d/Version"%(prefix,kl.Id),kl.Version)
                config.Write("%s/%d/MinorVersion"%(prefix,kl.Id),kl.MinorVersion)
                config.Write("%s/%d/Path"%(prefix,kl.Id),kl.Path)
                config.WriteInt("%s/%d/Default"%(prefix,kl.Id),kl.Default)
                config.Write("%s/%d/SysPathList"%(prefix,kl.Id),os.pathsep.join(kl.SysPathList))
                config.Write("%s/%d/PythonPathList"%(prefix,kl.Id),os.pathsep.join(kl.PythonPathList))
                config.Write("%s/%d/Builtins"%(prefix,kl.Id),os.pathsep.join(kl.Builtins))
                config.Write("%s/%d/Environ"%(prefix,kl.Id),json.dumps(kl.Environ.environ))
                config.Write("%s/%d/Packages"%(prefix,kl.Id),json.dumps(kl.DumpPackages()))

    def RemovePythonInterpreter(self,interpreter):
        #if current interpreter has been removed,choose default interpreter as current interpreter
        if interpreter == self.CurrentInterpreter:
            self.SetCurrentInterpreter(self.GetDefaultInterpreter())
        self.interpreters.remove(interpreter)

    def SetDefaultInterpreter(self,interpreter):
        '''
            设置默认解释器
        '''
        self.DefaultInterpreter = interpreter
        for kl in self.interpreters:
            if kl.Id == interpreter.Id:
                interpreter.Default = True
            else:
                kl.Default = False

    def MakeDefaultInterpreter(self):
        self.DefaultInterpreter = self.interpreters[0]
        self.DefaultInterpreter.Default = True

    def GetDefaultInterpreter(self):
        return self.DefaultInterpreter

    def GetChoices(self):
        choices = []
        default_index = -1
        for i,interpreter in enumerate(self.interpreters):
            #set current interpreter index as default index
            if interpreter == self.CurrentInterpreter:
                default_index = i
            choices.append(interpreter.Name)
        return choices,default_index

    def CheckIdExist(self,id):
        for kb in self.interpreters:
            if kb.Id == id:
                return True
        return False

    def GenerateId(self):
        id = NewId()
        while self.CheckIdExist(id):
            id = NewId()
        return id

    def IsInterpreterAnalysing(self):
        for kb in self.interpreters:
            if kb.Analysing:
                return True
        return False

    def SetCurrentInterpreter(self,interpreter):
        '''
            设置当前正在使用的解释器
        '''
        self.CurrentInterpreter = interpreter
        if interpreter is None:
            return

    def GetCurrentInterpreter(self):
        return self.CurrentInterpreter

    def LoadBuiltinInterpreter(self):
        builtin_interpreter = pythoninterpreter.BuiltinPythonInterpreter(BUILTIN_INTERPRETER_NAME,sys.executable)
        self.interpreters.append(builtin_interpreter)
        
    def GetInterpreterNames(self):
        names = []
        for interpreter in self.interpreters:
            names.append(interpreter.Name)
        return names
        
class InterpreterAdmin():
    def __init__(self,interpreters):
        self.interpreters = interpreters

    def CheckInterpreterExist(self,interpreter):
        for kb in self.interpreters:
            if kb.Name.lower() == interpreter.Name.lower():
                return True
            elif kb.Path.lower() == interpreter.Path.lower():
                return True
        return False

    def AddPythonInterpreter(self,interpreter_path,name):
        interpreter = pythoninterpreter.PythonInterpreter(name,interpreter_path)
        if not interpreter.IsValidInterpreter:
            raise RuntimeError(_("%s is not a valid interpreter path") % interpreter_path)
        interpreter.Name = name
        if self.CheckInterpreterExist(interpreter):
            raise RuntimeError(_("interpreter have already exist"))
        self.interpreters.append(interpreter)
        #first interpreter should be the default interpreter by default
        if 1 == len(self.interpreters):
            self.MakeDefaultInterpreter()
        return interpreter

    def GetInterpreterById(self,id):
        for interpreter in self.interpreters:
            if interpreter.Id == id:
                return interpreter
        return None

    def MakeDefaultInterpreter(self):
        self.interpreters[0].Default = True


