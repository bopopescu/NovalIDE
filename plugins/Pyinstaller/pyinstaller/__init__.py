###############################################################################
# Name: __init__.py                                                           #
# Purpose: Simple Calculator Plugin                                           #
# Author: Cody Precord <cprecord@editra.org>                                  #

"""Simple Programmer's Calculator"""
__author__ = "Cody Precord"
__version__ = "0.6"

#-----------------------------------------------------------------------------#
from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from noval.project.templatemanager import ProjectTemplateManager
from noval.project.debugger import OutputRunCommandUI
from noval.python.debugger.output import *
from noval.project.baseconfig import *
import noval.python.debugger.debugger as pythondebugger
import noval.consts as consts
import noval.util.fileutils as fileutils
import noval.menu as tkmenu

# Local imports
import pyinstaller.pyinstall as pyinstall
#-----------------------------------------------------------------------------#

# Try and add this plugins message catalogs to the app

#wx.GetApp().AddMessageCatalog('calculator', __name__)
#-----------------------------------------------------------------------------#

class OutputView(OutputRunCommandUI):
    
  #  ID_PYINSTALLER_DEBUG = NewId()
  #  ID_PYINSTALLER_CONFIG = NewId()
    def __init__(self,master):
        GetApp()._debugger_class = pythondebugger.PythonDebugger
        OutputRunCommandUI.__init__(self,master,GetApp().GetDebugger())
        GetApp().bind(constants.PROJECTVIEW_POPUP_FILE_MENU_EVT, self.AppenFileMenu,True)
        GetApp().bind(constants.PROJECTVIEW_POPUP_ROOT_MENU_EVT, self.AppenRootMenu,True)
        
    def AppenRootMenu(self, event):
        menu = event.get('menu')
        if self.GetProjectDocument().__class__.__name__ != "PyinstallerProjectDocument":
            submenu = menu.GetMenuByname(_("Convert to"))
            if not submenu:
                menu.add_separator()
                submenu = tkmenu.PopupMenu()
                menu.AppendMenu(NewId(),_("Convert to"),submenu)
            submenu.Append(NewId(),_("Pyinstaller Project"),handler=self.Convertto) 
        else:
            submenu = tkmenu.PopupMenu()
            menu.AppendMenu(NewId(),_("Pyinstaller"),submenu)
            submenu.Append(NewId(),_("Build"),handler=self.Build) 
            submenu.Append(NewId(),_("Rebuild"),handler=self.Rebuild)
            submenu.Append(NewId(),_("Clean temporary files"),handler=self.Clean)
            submenu.Append(NewId(),_("Run in debugger"),handler=self.Run)
            submenu.Append(NewId(),_("Run in terminal"),handler=None)
            submenu.Append(NewId(),_("Configuration"),handler=None)
            
    def Convertto(self):
        project_doc = self.GetProjectDocument()
        project_doc.GetModel()._runinfo.DocumentTemplate = "pyinstaller.pyinstall.PyinstallerProjectTemplate"
        project_doc.Modify(True)
        project_doc.Save()
        assert(project_doc.NeedConvertto(project_doc.GetModel()))
        project_doc.ConvertTo(project_doc.GetModel(),project_doc.GetFilename())
        self.GetProjectFrame().GetView().SetDocument(project_doc)
        self.GetProjectFrame().CloseProject()

    def AppenFileMenu(self, event):
        if self.GetProjectDocument().__class__.__name__ != "PyinstallerProjectDocument":
            return
        menu = event.get('menu')
        tree_item = event.get('item')
        project_browser = GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME)
        filePath = project_browser.GetView()._GetItemFilePath(tree_item)
        if project_browser.GetView()._IsItemFile(tree_item) and fileutils.is_python_file(filePath):
            menu.add_separator()
            submenu = tkmenu.PopupMenu()
            menu.AppendMenu(NewId(),_("Pyinstaller"),submenu)
            submenu.Append(NewId(),_("Build"),handler=self.Build) 
            submenu.Append(NewId(),_("Rebuild"),handler=self.Rebuild)
            submenu.Append(NewId(),_("Clean temporary files"),handler=self.Clean)
            submenu.Append(NewId(),_("Run in debugger"),handler=self.RunIndebugger)
            submenu.Append(NewId(),_("Run in terminal"),handler=self.RunInterminal)
            submenu.Append(NewId(),_("Configuration"),handler=self.ShowPyinstallerConfiguration)

    def ExecutorFinished(self,stopped=True):
        OutputRunCommandUI.ExecutorFinished(self,stopped=stopped)
        if not self._stopped:
            target_exe_path = self.GetProjectDocument().GetTargetPath(self._run_parameter)[0]
            print ('target exe path is',target_exe_path)
            view = GetApp().MainFrame.GetCommonView("Output")
            view.GetOutputview().SetTraceLog(True)
            run_parameter = BaseRunconfig(target_exe_path)
            view._textCtrl.ClearOutput()
            view.SetRunParameter(run_parameter)
            view.CreateExecutor()
            view.Execute()

    def GetOuputctrlClass(self):
        return DebugOutputctrl

    def Build(self):
        ''''''
        self.GetProjectDocument().Build()
        
    def Rebuild(self):
        ''''''
        self.GetProjectDocument().Rebuild()
        
    def RunIndebugger(self):
        ''''''
        self.GetProjectDocument().RunIndebugger()
        
    def RunInterminal(self):
        ''''''
        self.GetProjectDocument().RunInterminal()
        
    def ShowPyinstallerConfiguration(self):
        ''''''
        self.GetProjectFrame().OnProperties()
        
    def GetProjectDocument(self):
        project_browser = self.GetProjectFrame()
        return project_browser.GetView().GetDocument()
        
    def GetProjectFrame(self):
        return GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME)
        
    def Clean(self):
        ''''''
        self.GetProjectDocument().CleanBuilddir()
        self.GetProjectDocument().CleanOutput()
        GetApp().GetTopWindow().PushStatusText(_("Clean Completed."))


class Pyinstaller(plugin.Plugin):
    """Simple Programmer's Calculator"""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing pyinstaller plugin")
        ProjectTemplateManager().AddProjectTemplate("Python/Pyinstaller",_("Console Application"),[pyinstall.PyinstallerProjectNameLocationPage,(pyinstall.PyinstallerBaseInformationPage,{'is_windows_application':False}),pyinstall.PyinstallSpecOptionPage,\
                        pyinstall.PyinstallDatafilesPage,("noval.project.importfiles.ImportfilesPage",{'rejects':[]})])
        ProjectTemplateManager().AddProjectTemplate("Python/Pyinstaller",_("Windows Application"),[pyinstall.PyinstallerProjectNameLocationPage,(pyinstall.PyinstallerBaseInformationPage,{'is_windows_application':True}),pyinstall.PyinstallSpecOptionPage,\
                        pyinstall.PyinstallDatafilesPage,("noval.project.importfiles.ImportfilesPage",{'rejects':[]})])
        ProjectTemplateManager().AddProjectTemplate("Python/Pyinstaller",_("A simple Pyinstaller demo"),[pyinstall.PyinstallerSimpleDemoNameLocationPage,pyinstall.PyinstallerBaseInformationPage,pyinstall.PyinstallSpecOptionPage])

 
        GetApp().MainFrame.AddView("Output",OutputView, _("Output"), "s",image_file="writeout.png")
        
    def GetMinVersion(self):
        return '1.1.9'