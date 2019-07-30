import noval.project.basemodel as basemodel
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.util.xmlutils as xmlutils
from noval.consts import PROJECT_NAMESPACE_URL


class PythonProject(basemodel.BaseProject):
    def __init__(self):
        super(PythonProject,self).__init__()
        self.interpreter = None
        self.python_path_list = []
        self._properties.AddPage("Resource","root","noval.project.resource.ResourcePanel")
        self._properties.AddPage("Debug/Run","root","noval.python.project.pages.debugrun.DebugRunPanel")
        self._properties.AddPage("PythonPath","root","noval.python.project.pages.pythonpath.PythonPathPanel")
        self._properties.AddPage("Interpreter","root","noval.python.project.pages.pythoninterpreter.PythonInterpreterPanel")
        self._properties.AddPage("Project References","root","noval.python.project.pages.projectreferrence.ProjectReferrencePanel")

        self._properties.AddPage("Resource","file","noval.project.resource.ResourcePanel")
        self._properties.AddPage("Debug/Run","file","noval.python.project.pages.debugrun.DebugRunPanel")

        self._properties.AddPage("Resource","folder","noval.project.resource.ResourcePanel")
        self._properties.AddPage("Debug/Run","folder","noval.python.project.pages.debugrun.DebugRunPanel")

        self._runinfo.RunConfig = "noval.python.project.runconfig.PythonRunconfig"
        self._runinfo.DocumentTemplate = "noval.python.project.viewer.PythonProjectTemplate"
        
        
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
                        "%s:interpreter" % PROJECT_NAMESPACE_URL:ProjectInterpreter,"%s:_properties" % PROJECT_NAMESPACE_URL:basemodel.ProjectProperty\
                ,"%s:_runinfo" % PROJECT_NAMESPACE_URL:basemodel.RunInfo,"%s:page" % PROJECT_NAMESPACE_URL:basemodel.PropertyPage}
