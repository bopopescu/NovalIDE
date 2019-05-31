from noval import _
        

class InterpreterNotExistError(RuntimeError):
    def __init__(self,interpter_name):
        msg = _("Interpreter \"%s\" is not exist") % interpter_name
        RuntimeError.__init__(self,msg)


class StartupPathNotExistError(RuntimeError):
    
    def __init__(self,startup_path):
        msg = _("Startup path \"%s\" is not exist") % startup_path
        RuntimeError.__init__(self,msg)
        
class MenuBarMenuNotExistError(RuntimeError):
    
    def __init__(self,menu_name):
        msg = _("Could not find menu '%s' at menubar") % menu_name
        RuntimeError.__init__(self,msg)