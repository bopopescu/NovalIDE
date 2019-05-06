import noval.util.appdirs as appdirs
import os
import psutil
import noval.util.utils as utils
import noval.python.parser.utils as parserutils

class SingleInstanceChecker(object):
    """description of class"""

    def __init__(self):
        user_data_path = appdirs.get_user_data_path()
        if not os.path.exists(user_data_path):
            parserutils.MakeDirs(user_data_path)
        self.lock = os.path.join(user_data_path,"lock")
        self.pid = None
        self.Create()

    def Create(self):
        if not os.path.exists(self.lock):
            self.SetPid()
        else:
            self.GetPid()

    def IsAnotherRunning(self):
        if self.pid is None:
            return False
        try:
            psutil.Process(int(self.pid))
        except:
            utils.get_logger().info("app process id %s is not run again",self.pid)
            self.SetPid()
            return False
        return True
        
    def GetPid(self):
        with open(self.lock) as f:
            self.pid = f.read()
        
    def SetPid(self):
        with open(self.lock,"w") as f:
            f.write(str(os.getpid()))
        
