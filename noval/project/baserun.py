import os

class BaseProjectConfiguration:
    PROJECT_ADD_SRC_PATH = 1
    DEFAULT_PROJECT_SRC_PATH = 'Src'
    def __init__(self,name,location,is_project_dir_created):
        self._name = name
        self._location = location
        self._is_project_dir_created = is_project_dir_created
        
    @property
    def Name(self):
        return self._name
        
    @property
    def Location(self):
        return self._location

    @property
    def ProjectDirCreated(self):
        return self._is_project_dir_created
        
class BaseRunconfig():
    def __init__(self,exe_path,run_file_path,arg='',env=None,start_up=None,project=None):
        self._exe = exe_path
        self._file_path = run_file_path
        self._arg = arg
        self._env = env
        self._start_up_path = start_up
        self._project = project
        
    @property
    def ExePath(self):
        return self._exe
        
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
    def Project(self):
        return self._project
    