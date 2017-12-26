import os
import sys
import subprocess
from Singleton import *

class Interpreter(object):
    
    def __init__(self,name,executable_path):
        self._path = executable_path
        self._install_path = os.path.dirname(self._path)
        self._name = name
        
    @property
    def Path(self):
        return self._path
        
    @property
    def InstallPath(self):
        return self._install_path
        
    @property
    def Version(self):
        pass
        
    @property
    def Name(self):
        return self._name
 
    @Name.setter
    def Name(self,name):
        self._name = name
        

def GetCommandOutput(command,read_error=False):
    p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if read_error:
        return p.stderr.read()
    return p.stdout.read()
        
class PythonInterpreter(Interpreter):
    
    CONSOLE_EXECUTABLE_NAME = "python.exe"
    WINDOW_EXECUTABLE_NAME = "pythonw.exe"
    def __init__(self,name,executable_path):
        if sys.platform == "win32":
            if os.path.basename(executable_path) == PythonInterpreter.WINDOW_EXECUTABLE_NAME:
                self._window_path = executable_path
                console_path = os.path.join(os.path.dirname(executable_path),PythonInterpreter.CONSOLE_EXECUTABLE_NAME)
                self._console_path = console_path
                executable_path = self._console_path
            elif os.path.basename(executable_path) == PythonInterpreter.CONSOLE_EXECUTABLE_NAME:
                self._console_path = executable_path
                window_path = os.path.join(os.path.dirname(executable_path),PythonInterpreter.WINDOW_EXECUTABLE_NAME)
                self._window_path = window_path
                
        super(PythonInterpreter,self).__init__(name,executable_path)
        self._is_valid_interpreter = False
        self.GetVersion()
        
    def GetVersion(self):
        output = GetCommandOutput("%s -V" % self.Path,True).strip().lower()
        version_flag = "python "
        if output.find(version_flag) == -1:
            return
        self._version = output.replace(version_flag,"").strip()
        self._is_valid_interpreter = True
        
    def CheckSyntax(self,script_path):
        check_cmd ="%s -c \"%s\"" % (self.Path,script_path)
        output = GetCommandOutput(check_cmd)
        return output
        
    @property
    def Version(self):
        return self._version
         
    @property
    def ConsolePath(self):
         return self._console_path
    @property
    def WindowPath(self):
         return self._window_path
    @property
    def IsValidInterpreter(self):
         return self._is_valid_interpreter
         

class InterpreterManager(Singleton):
    
    interpreters = []
    DefaultInterpreter = None
    
    def GetDefaultInterpreter(self):
        
        self.LoadPythonInterpreters()
        if [] == self.interpreters:
            return None
        self.SetDefault()
   
    def LoadPythonInterpreters(self):
        if sys.platform == "win32":
            import _winreg
            ROOT_KEY_LIST = [_winreg.HKEY_LOCAL_MACHINE,_winreg.HKEY_CURRENT_USER]
            for root_key in ROOT_KEY_LIST:
                try:
                    open_key = _winreg.OpenKey(root_key, r"SOFTWARE\Python\Pythoncore")  
                    countkey=_winreg.QueryInfoKey(open_key)[0]  
                    keylist = []  
                    for i in range(int(countkey)):  
                        name = _winreg.EnumKey(open_key,i)  
                        child_key = _winreg.OpenKey(root_key, r"SOFTWARE\Python\Pythoncore\%s" % name)
                        install_path = _winreg.QueryValue(child_key,"InstallPath")
                        interpreter = PythonInterpreter(name,os.path.join(install_path,PythonInterpreter.CONSOLE_EXECUTABLE_NAME))
                        self.interpreters.append(interpreter)
                except:
                    pass
            
        elif sys.platform.find('linux') != -1:
            executable_path = sys.executable
            install_path = os.path.dirname(executable_path)
            interpreter = PythonInterpreter("default",executable_path)
            self.interpreters.append(interpreter)
        
    def AddPythonInterpreter(self,interpreter_path):
        interpreter = PythonInterpreter("",interpreter_path)
        if not interpreter.IsValidInterpreter:
            raise "%s is not a valid interpreter path" % interpreter_path
        interpreter.Name = interpreter.Version
        interpreters.append(interpreter)
        
    def RemovePythonInterpreter(self,interpreter):
        self.interpreters.remove(interpreter)
        
    def SetDefaultInterpreter(self,interpreter):
        self.DefaultInterpreter = interpreter
        
    def SetDefault(self):
        self.DefaultInterpreter = self.interpreters[0]
        
    def GetDefault(self):
        return self.DefaultInterpreter
