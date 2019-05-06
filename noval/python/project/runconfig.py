from noval.project.baserun import *

class PythonProjectConfiguration(BaseProjectConfiguration):
    
    PROJECT_SRC_PATH_ADD_TO_PYTHONPATH = BaseProjectConfiguration.PROJECT_ADD_SRC_PATH
    PROJECT_PATH_ADD_TO_PYTHONPATH = 2
    NONE_PATH_ADD_TO_PYTHONPATH = 3
    
    def __init__(self,name,location,interpreter,is_project_dir_created,pythonpath_mode):
        BaseProjectConfiguration.__init__(self,name,location,is_project_dir_created)
        self._interpreter = interpreter
        self._pythonpath_mode = pythonpath_mode
        
    @property
    def Interpreter(self):
        return self._interpreter
        
    @property
    def PythonpathMode(self):
        return self._pythonpath_mode
        
class PythonRunconfig(BaseRunconfig):
    def __init__(self,interpreter,file_path,arg='',env=None,start_up=None,is_debug_breakpoint=False,project=None,interpreter_option=""):
        BaseRunconfig.__init__(self,interpreter,file_path,arg,env,start_up,project)
        self._is_debug_breakpoint = is_debug_breakpoint
        self._interpreter_option = interpreter_option
        
    @property
    def Interpreter(self):
        return self.ExePath
        
    @property
    def IsBreakPointDebug(self):
        return self._is_debug_breakpoint
        
    @IsBreakPointDebug.setter
    def IsBreakPointDebug(self,is_debug_breakpoint):
        self._is_debug_breakpoint = is_debug_breakpoint
        
    @property
    def InterpreterOption(self):
        return self._interpreter_option
    