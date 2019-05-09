# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Interpreter.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-10
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp
import os
import subprocess
import locale
import noval.util.apputils as apputils
import noval.util.strutils as strutils
try:
    import __builtin__
except ImportError:
    import builtins as __builtin__
import threading
from noval.util import utils
import glob
import sys
try:
    import cStringIO
except:
    import io as cStringIO

import py_compile
import getpass
import noval.util.fileutils as fileutils
import noval.util.utils as utils
from noval.executable import Executable,UNKNOWN_VERSION_NAME

def GetCommandOutput(command,read_error=False):
    output = ''
    try:
        p = subprocess.Popen(command,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if read_error:
            output = p.stderr.read()
        else:
            output = p.stdout.read()
        #PY3输出类型为bytes,需要转换为str类型
        if utils.is_py3():
            output = str(output,encoding = utils.get_default_encoding())
    except Exception as e:
        utils.get_logger().error("get command %s output error:%s",command,e)
    return output
    
#this class should inherit from object class
#otherwise the property definition will not valid
class PythonEnvironment(object):
    def __init__(self):
        self._include_system_environ = True
        self.environ = {}
        
    def Exist(self,key):
        return self.environ.has_key(key)
        
    def GetEnviron(self):
        environ = {}
        environ.update(self.environ)
        if self._include_system_environ:
            environ.update(os.environ)
        return environ
        
    def SetEnviron(self,dct):
        self.environ = {}
        for key in dct:
            #should avoid environment contain unicode string,such as u'xxx'
            if len(key) != len(str(key)) or len(dct[key]) != len(str(dct[key])):
                raise PromptErrorException(_("Environment variable contains invalid character"))
            self.environ[str(key)] = str(dct[key])
        #must use this environment variable to unbuffered binary stdout and stderr
        #environment value must be a string,not a digit,which linux os does not support a digit value
        self.environ['PYTHONUNBUFFERED'] = '1'
            
    @property
    def IncludeSystemEnviron(self):
        return self._include_system_environ
        
    @IncludeSystemEnviron.setter
    def IncludeSystemEnviron(self,v):
        self._include_system_environ = v
        
    def __next__(self):
        '''
            python3迭代方法
        '''
        return self.next()
        
    def __iter__(self):
        self.iter = iter(self.environ)
        return self
        
    def next(self):
        '''
            python2迭代方法
        '''
        return __builtin__.next(self.iter)
        
    def GetCount(self):
        return len(self.environ)
        
    def __getitem__(self,name):
        return self.environ[name]
        

class PythonPackage():
    def __init__(self,**kwargs):        
        for arg in kwargs:
            attr = arg
            if arg == 'name':
                arg = 'Name'
            elif arg == 'version':
                arg = 'Version'
            setattr(self,arg,kwargs[attr])
        

class BuiltinPythonInterpreter(Executable):
    def __init__(self,name,executable_path,id=None,is_builtin = True):
        super(BuiltinPythonInterpreter,self).__init__(name,executable_path)
        self._is_builtin = is_builtin
        if id is None:
            self._id = GetApp().GetInterpreterManager().GenerateId()
        else:
            self._id = int(id)
        self._is_default = False
        self._sys_path_list = sys.path
        self._python_path_list = []
        self._version = ".".join([str(sys.version_info.major),str(sys.version_info.minor),str(sys.version_info.micro)])
        self._builtins = list(sys.builtin_module_names)
        self.Environ = PythonEnvironment()
        self._packages = {}
        self._help_path = ""
        #builtin module name which python2 is __builtin__ and python3 is builtins
        self._builtin_module_name = "__builtin__"
        
    @property
    def IsBuiltIn(self):
        return self._is_builtin
        
    @property
    def Version(self):
        return self._version

    @property
    def HelpPath(self):
        return self._help_path
        
    @HelpPath.setter
    def HelpPath(self,help_path):
        self._help_path = help_path
        
    @property
    def Default(self):
        return self._is_default
        
    @Default.setter
    def Default(self,is_default):
        self._is_default = is_default
        
    @property
    def SysPathList(self):
        return self._sys_path_list
        
    @property
    def PythonPathList(self):
        return self._python_path_list 
        
    @PythonPathList.setter
    def PythonPathList(self,path_list):
        self._python_path_list = path_list
        
    @property    
    def Builtins(self):
        return self._builtins
        
    @property
    def Id(self):
        return self._id
        
    @property
    def BuiltinModuleName(self):
        return self._builtin_module_name
        
    @property
    def Packages(self):
        return self._packages
        
    @Packages.setter
    def Packages(self,packages):
        self._packages = packages
        
    def LoadPackages(self,ui_panel,force):
        ui_panel.LoadPackageEnd(self)
        
    @property
    def IsLoadingPackage(self):
        return False
        
    def SetInterpreter(self,**kwargs):
        self._version = kwargs.get('version')
        if self._version == UNKNOWN_VERSION_NAME:
            return
        if self.IsV3():
            self._builtin_module_name = self.PYTHON3_BUILTIN_MODULE_NAME
        self._builtins = kwargs.get('builtins')
        self._sys_path_list = kwargs.get('sys_path_list')
        python_path_list = kwargs.get('python_path_list')
        self._python_path_list = [pythonpath for pythonpath in python_path_list if str(pythonpath) != '']
        self._is_builtin = kwargs.get('is_builtin')
        
    def IsV2(self):
        return True
        
    def IsV3(self):
        return False
        
    @property
    def Analysing(self):
        return False
    
    @property
    def IsValidInterpreter(self):
         return True
         
    def CheckSyntax(self,script_path):
        origin_stderr = sys.stderr
        sys.stderr = cStringIO.StringIO()
        py_compile.compile(script_path)
        output = sys.stderr.getvalue().strip()
        sys.stderr = origin_stderr
        if 0 == len(output):
            return True,-1,''
        lower_output = output.lower()
        lines = output.splitlines()
        fileBegin = lines[0].find("File \"")
        fileEnd = lines[0].find("\", line ")
        if -1 != lower_output.find('permission denied:'):
            line = lines[-1]
            pos = line.find(']')
            msg = line[pos+1:].replace("'","").strip()
            msg += ",Perhaps you need to delete it first!"
            return False,-1,msg
        elif fileBegin != -1 and fileEnd != -1:
            lineNum = int(lines[0][fileEnd + 8:].strip())
            return False,lineNum,'\n'.join(lines[1:])

        i = lines[0].find('(')
        j = lines[0].find(')')
        msg = lines[0][0:i].strip()
        lineNum = int(lines[0][i+1:j].split()[-1])
        return False,lineNum,msg
        
    def IsPackageExist(self,package_name):
        if package_name in self.Packages:
            return True
        return False
        
    def LoaPackagesFromDict(self,package_dct):
        return {}
        
    def DumpPackages(self):
        return {}
        
    def GetExedirs(self):
        return [self.InstallPath,]
        
class PythonInterpreter(BuiltinPythonInterpreter):
    
    CONSOLE_EXECUTABLE_NAME = "python.exe"
    WINDOW_EXECUTABLE_NAME = "pythonw.exe"
    PYTHON3_BUILTIN_MODULE_NAME = 'builtins'
    def __init__(self,name,executable_path,id=None,is_valid_interpreter = False):
        if apputils.is_windows():
            if os.path.basename(executable_path) == PythonInterpreter.WINDOW_EXECUTABLE_NAME:
                self._window_path = executable_path
                console_path = os.path.join(os.path.dirname(executable_path),PythonInterpreter.CONSOLE_EXECUTABLE_NAME)
                self._console_path = console_path
                executable_path = self._console_path
            elif os.path.basename(executable_path) == PythonInterpreter.CONSOLE_EXECUTABLE_NAME:
                self._console_path = executable_path
                window_path = os.path.join(os.path.dirname(executable_path),PythonInterpreter.WINDOW_EXECUTABLE_NAME)
                self._window_path = window_path
                
        super(PythonInterpreter,self).__init__(name,executable_path,id,False)
        self._is_valid_interpreter = is_valid_interpreter
        self._version = UNKNOWN_VERSION_NAME
        self._is_analysing = False
        self._is_analysed = False
        self._is_loading_package = False
        if not is_valid_interpreter:
            self.GetVersion()
        if not is_valid_interpreter and self._is_valid_interpreter:
            self.GetSysPathList()
            self.GetBuiltins()
            
    def GetVersion(self):
        output = GetCommandOutput("%s -V" % strutils.emphasis_path(self.Path),True).strip().lower()
        version_flag = "python "
        if output.find(version_flag) == -1:
            output = GetCommandOutput("%s -V" % strutils.emphasis_path(self.Path),False).strip().lower()
            if output.find(version_flag) == -1:
                utils.get_logger().error("get version stdout output is *****%s****",output)
                return
        self._version = output.replace(version_flag,"").strip()
        self._is_valid_interpreter = True
        if self.IsV3():
            self._builtin_module_name = self.PYTHON3_BUILTIN_MODULE_NAME

    def IsV27(self):
        versions = self.Version.split('.')
        if int(versions[0]) == 2 and int(versions[1]) == 7:
            return True
        return False

    def IsV26(self):
        versions = self.Version.split('.')
        if int(versions[0]) == 2 and int(versions[1]) == 6:
            return True
        return False

    def IsV2(self):
        versions = self.Version.split('.')
        if not versions[0].isdigit():
            return False
        if int(versions[0]) == 2:
            return True
        return False

    def IsV3(self):
        versions = self.Version.split('.')
        if not versions[0].isdigit():
            return False
        if int(versions[0]) >= 3:
            return True
        return False
        
    def CheckSyntax(self,script_path):
        check_cmd ="\"%s\" -c \"import py_compile;py_compile.compile(r'%s')\"" % (self.Path,script_path)
        sys_encoding = locale.getdefaultlocale()[1]
        output = GetCommandOutput(check_cmd.encode(sys_encoding),True).strip()
        if 0 == len(output):
            return True,-1,''
        lower_output = output.lower()
        lines = output.splitlines()
        fileBegin = lines[0].find("File \"")
        fileEnd = lines[0].find("\", line ")
        if -1 != lower_output.find('permission denied:'):
            line = lines[-1]
            pos = line.find(']')
            msg = line[pos+1:].replace("'","").strip()
            msg += ",Perhaps you need to delete it first!"
            return False,-1,msg
        elif fileBegin != -1 and fileEnd != -1:
            lineNum = int(lines[0][fileEnd + 8:].strip())
            return False,lineNum,'\n'.join(lines[1:])

        if self.IsV26():
            '''
            parse such error text:
            Sorry: IndentationError: ('unexpected indent', ('D:\\env\\Noval\\noval\\test\\run_test_input.py', 106, 16, '                ddd\n'))
            '''
            i = lines[0].find(", ('")
            j = lines[0].find(')')
            msg = lines[0][0:i].strip()
            lineNum = int(lines[0][i+1:j].split(',')[1].strip())
        else:
            '''
            parse such error text:
            Sorry: IndentationError: unexpected indent (run_test_input.py, line 106)
            '''
            i = lines[0].find('(')
            j = lines[0].find(')')
            msg = lines[0][0:i].strip()
            lineNum = int(lines[0][i+1:j].split()[-1])
        return False,lineNum,msg
         
    @property
    def ConsolePath(self):
         return self._console_path
    @property
    def WindowPath(self):
         return self._window_path
    @property
    def IsValidInterpreter(self):
         return self._is_valid_interpreter
        
    def GetSysPathList(self):
        if self.IsV2():
            run_cmd ="%s -c \"import sys;print sys.path\"" % (strutils.emphasis_path(self.Path))
        elif self.IsV3():
            run_cmd ="%s -c \"import sys;print (sys.path)\"" % (strutils.emphasis_path(self.Path))
        else:
            utils.get_logger().warn("interpreter path %s could not get python version" % self.Path)
            self._is_valid_interpreter = False
            return
        output = GetCommandOutput(run_cmd).strip()
        lst = eval(output)
        self._sys_path_list = lst
        
    def GetBuiltins(self):
        if not self._is_valid_interpreter :
            return
        if self.IsV2():
            run_cmd ="%s -c \"import sys;print sys.builtin_module_names\"" % (strutils.emphasis_path(self.Path))
        elif self.IsV3():
            run_cmd ="%s -c \"import sys;print (sys.builtin_module_names)\"" % (strutils.emphasis_path(self.Path))
        output = GetCommandOutput(run_cmd).strip()
        lst = eval(output)
        #should convert tuple type to list
        self._builtins = list(lst)
        
    def GetPythonLibPath(self):
        if self.IsV2():
            cmd = "%s  -c \"from distutils.sysconfig import get_python_lib; print get_python_lib()\"" % \
                        (strutils.emphasis_path(self.Path),)
        elif self.IsV3():
            cmd = "%s  -c \"from distutils.sysconfig import get_python_lib; print (get_python_lib())\"" % \
                        (strutils.emphasis_path(self.Path),)
        python_lib_path = GetCommandOutput(cmd).strip()
        return python_lib_path
        
    def IsPythonlibWritable(self):
        python_lib_path = self.GetPythonLibPath()
        user = getpass.getuser()
        return fileutils.is_writable(python_lib_path,user)
        
    @property
    def Analysing(self):
        return self._is_analysing
        
    @Analysing.setter
    def Analysing(self,is_analysing):
        self._is_analysing = is_analysing

    @property
    def IsAnalysed(self):
        return self._is_analysed

    @IsAnalysed.setter
    def IsAnalysed(self,is_analysed):
        self._is_analysed = is_analysed
        
    def GetPipPath(self):
        if apputils.is_windows():
            pip_name = "pip.exe"
            pip3_name = "pip3.exe"
        else:
            pip_name = "pip"
            pip3_name = "pip3"
        python_location = os.path.dirname(self.Path)
        pip_path_list = []
        #linux python3 pip tool name is pip3
        if self.IsV2() or apputils.is_windows():
            pip_path_list = [os.path.join(python_location,"Scripts",pip_name),os.path.join(python_location,pip_name)]
        if self.IsV3():
            #py3 may get pip3 as the pip tool
            pip_path_list.extend([os.path.join(python_location,"Scripts",pip3_name),os.path.join(python_location,pip3_name)])
        for pip_path in pip_path_list:
            if os.path.exists(pip_path):
                return pip_path
        return None
        
    def GetDocPath(self):
        if self._help_path == "":
            if sysutils.isWindows():
                python_location = os.path.dirname(self.Path)
                doc_location = os.path.join(python_location,"Doc")
                file_list = glob.glob(os.path.join(doc_location,"*.chm"))
                if len(file_list) > 0 :
                   self._help_path =  file_list[0]
        
    def LoadPackages(self,ui_panel,force):
        if (not self._is_loading_package and 0 == len(self._packages)) or force:
            t = threading.Thread(target=self.LoadPackageList,args=(ui_panel,))
            t.start()
            
    def LoadPackageList(self,ui_panel):
        #clear all packages first
        self._packages = {}
        self._is_loading_package = True
        pip_path = self.GetPipPath()
        if pip_path is not None:
            command = "%s list" % strutils.emphasis_path(pip_path)
            output = GetCommandOutput(command)
            for line in output.split('\n'):
                if line.strip() == "":
                    continue
                name,raw_version = line.split()[0:2]
                #filter output lines like
                '''
                    Package                      Version
                    ---------------------------- ---------
                '''
                if raw_version.startswith("-----") or raw_version.strip() == "Version":
                    continue
                version = raw_version.replace("(","").replace(")","")
                python_package = PythonPackage(**{'Name':name,'Version':version})
                self._packages[name] = python_package
        
        if self._is_loading_package:
            ui_panel.LoadPackageEnd(self)
            self._is_loading_package = False
        else:
            utils.get_logger().warn("user stop loading interpreter %s package....." % self.Name)
        
    @property
    def IsLoadingPackage(self):
        return self._is_loading_package
        
    def SetInterpreter(self,**kwargs):
        BuiltinPythonInterpreter.SetInterpreter(self,**kwargs)
        #if self.IsV3():
         #   self._builtin_module_name = self.PYTHON3_BUILTIN_MODULE_NAME
         
    def StopLoadingPackage(self):
        self._is_loading_package = False

    def GetInstallPackage(self,package_name):
        command = "%s show %s" % (strutils.emphasis_path(self.GetPipPath()),package_name)
        output = GetCommandOutput(command)
        if output.strip() == "":
            return None
        name = package_name
        version = 'Unknown'
        name_flag = 'Name:'
        ver_flag = 'Version:'
        for line in output.splitlines():
            if line.find(name_flag) != -1:
                name = line.replace(name_flag,"").strip()
            elif line.find(ver_flag) != -1:
                version = line.replace(ver_flag,"").strip()
        python_package = PythonPackage(**{'Name':name,'Version':version})
        return python_package

    def DumpPackages(self):
        packages = {}
        for name in self._packages:
            package = self._packages[name]
            attrs = dir(package)
            dct = {}
            for attr in attrs:
                if attr == '__module__' or attr == "__init__" or attr == "__doc__":
                    continue
                dct[attr] = getattr(package,attr)
            packages[name] = dct
        return packages
        
    def LoadPackagesFromDict(self,package_dct):
        packages = {}
        for package_name in package_dct:
            dct = package_dct[package_name]
            #to git the old packages structure
            if isinstance(dct,basestring):
                dct = {'Name':package_name,'Version':dct}
            python_package = PythonPackage(**dct)
            packages[package_name] = python_package
        return packages
        
    def GetExedirs(self):
        result = []
        main_scripts = os.path.join(self.InstallPath, "Scripts")
        if os.path.isdir(main_scripts) and main_scripts not in result:
            result.append(main_scripts)
        
        if os.path.dirname(self.Path) not in result:
            result.append(os.path.dirname(self.Path))
        return result
        
                