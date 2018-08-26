import os
class ProjectConfiguration(object):
    
    PROJECT_SRC_PATH_ADD_TO_PYTHONPATH = 1
    PROJECT_PATH_ADD_TO_PYTHONPATH = 2
    NONE_PATH_ADD_TO_PYTHONPATH = 3
    DEFAULT_PROJECT_SRC_PATH = 'Src'
    def __init__(self,name,location,interpreter,is_project_dir_created,pythonpath_pattern):
        self._name = name
        self._location = location
        self._interpreter = interpreter
        self._is_project_dir_created = is_project_dir_created
        self._pythonpath_pattern = pythonpath_pattern
        
    @property
    def Name(self):
        return self._name
        
    @property
    def Location(self):
        return self._location
        
    @property
    def Interpreter(self):
        return self._interpreter
        
    @property
    def IsProjectDirCreated(self):
        return self._is_project_dir_created
        
    @property
    def PythonPathPattern(self):
        return self._pythonpath_pattern
        
class RunParameter():
    def __init__(self,interpreter,file_path,arg='',env=None,start_up=None,is_debug_breakpoint=False,project=None):
        self._interpreter = interpreter
        self._file_path = file_path
        self._arg = arg
        self._env = env
        self._start_up_path = start_up
        self._is_debug_breakpoint = is_debug_breakpoint
        self._project = project
        
    @property
    def Interpreter(self):
        return self._interpreter
        
    @property
    def FilePath(self):
        return self._file_path
        
    @property
    def Arg(self):
        return self._arg
        
    @property
    def Environment(self):
        return self._env
        
    @property
    def StartupPath(self):
        if not self._start_up_path:
            return os.path.dirname(self.FilePath)
        return self._start_up_path
        
    @property
    def IsBreakPointDebug(self):
        return self._is_debug_breakpoint
        
    @IsBreakPointDebug.setter
    def IsBreakPointDebug(self,is_debug_breakpoint):
        self._is_debug_breakpoint = is_debug_breakpoint

    @property
    def Project(self):
        return self._project
    