from noval.tool.consts import _

class PromptErrorException(Exception):
    def __init__(self, error_msg):
        self.msg = error_msg
        
    def __str__(self):
        return repr(self.msg)
        

class InterpreterNotExistError(PromptErrorException):
    def __init__(self,interpter_name):
        msg = _("Interpreter \"%s\" is not exist") % interpter_name
        super(InterpreterNotExistError,self).__init__(msg)


class StartupPathNotExistError(PromptErrorException):
    
    def __init__(self,startup_path):
        msg = _("Startup path \"%s\" is not exist") % startup_path
        super(StartupPathNotExistError,self).__init__(msg)
        
class MenuBarMenuNotExistError(PromptErrorException):
    
    def __init__(self,menu_name):
        msg = _("Could not find menu '%s' at menubar") % menu_name
        super(MenuBarMenuNotExistError,self).__init__(msg)