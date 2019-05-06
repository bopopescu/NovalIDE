import noval.project.basemodel as basemodel
import noval.python.interpreter.InterpreterManager as interpretermanager
import noval.util.xmlutils as xmlutils
from noval.consts import PROJECT_NAMESPACE_URL


class PythonProject(basemodel.BaseProject):
    def __init__(self):
        super(PythonProject,self).__init__()
        self.interpreter = None
        self.python_path_list = []
        
    def SetInterpreter(self,name):
        self.interpreter = ProjectInterpreter(self,name)
        
    @property
    def PythonPathList(self):
        return self.python_path_list
        
    @property
    def Interpreter(self):
        return self.interpreter
        
class ProjectInterpreter(object):
    __xmlexclude__ = ('_parentProj',)
    __xmlname__ = "interpreter"
    __xmlattributes__ = ["name",'version','path']
    __xmldefaultnamespace__ = xmlutils.AG_NS_URL
    
    def __init__(self,parent=None,name=''):
        self._parentProj = parent
        self.name = name
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(self.name)
        if interpreter is None:
            return
        self.version = interpreter.Version
        self.path = interpreter.Path
        
    @property
    def Path(self):
        return self.path
        
    @property
    def Version(self):
        return self.version
        

basemodel.KNOWNTYPES = {"%s:project" % PROJECT_NAMESPACE_URL : PythonProject, "%s:file" % PROJECT_NAMESPACE_URL : basemodel.ProjectFile,\
                        "%s:interpreter" % PROJECT_NAMESPACE_URL:ProjectInterpreter}
