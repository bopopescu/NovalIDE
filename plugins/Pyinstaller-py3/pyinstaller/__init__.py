###############################################################################
# Name: __init__.py                                                           #
# Purpose: Simple Calculator Plugin                                           #
# Author: Cody Precord <cprecord@editra.org>                                  #

"""Simple Programmer's Calculator"""
__author__ = "Cody Precord"
__version__ = "0.6"

#-----------------------------------------------------------------------------#
from noval import _,GetApp
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from noval.project.templatemanager import ProjectTemplateManager
from noval.project.debugger import CommonRunCommandUI
from noval.python.debugger.output import *
from noval.project.baseconfig import *

# Local imports
import pyinstaller.pyinstall as pyinstall
#-----------------------------------------------------------------------------#

# Try and add this plugins message catalogs to the app

#wx.GetApp().AddMessageCatalog('calculator', __name__)
#-----------------------------------------------------------------------------#

class OutputView(CommonRunCommandUI):
    def __init__(self,master):
        CommonRunCommandUI.__init__(self,master,GetApp().GetDebugger(),None)


    def ExecutorFinished(self,stopped=True):
        CommonRunCommandUI.ExecutorFinished(self,stopped=stopped)
        if not self._stopped:
            target_exe_path = self._run_parameter.GetTargetPath()
            print ('target exe path is',target_exe_path)
            view = GetApp().MainFrame.GetCommonView("Output")
            run_parameter = BaseRunconfig(target_exe_path)
            view._textCtrl.ClearOutput()
            view.SetRunParameter(run_parameter)
            view.CreateExecutor()
            view.Execute()

    def GetOuputctrlClass(self):
        return DebugOutputctrl

class Pyinstaller(plugin.Plugin):
    """Simple Programmer's Calculator"""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing pyinstaller plugin")
        ProjectTemplateManager().AddProjectTemplate("Python/Pyinstaller",_("Console Application"),[pyinstall.PyinstallerProjectNameLocationPage,pyinstall.PyinstallerDubugrunConfigurationPage,\
                        ("noval.project.importfiles.ImportfilesPage",{'rejects':[]})])
        ProjectTemplateManager().AddProjectTemplate("Python/Pyinstaller",_("Windows Application"),[pyinstall.PyinstallerProjectNameLocationPage,pyinstall.PyinstallerDubugrunConfigurationPage,\
                        ("noval.project.importfiles.ImportfilesPage",{'rejects':[]})])
        ProjectTemplateManager().AddProjectTemplate("Python/Pyinstaller",_("A simple helloworld demo"),[pyinstall.PyinstallerProjectNameLocationPage,pyinstall.PyinstallerDubugrunConfigurationPage,"noval.xx"])

 
        GetApp().MainFrame.AddView("Output",OutputView, _("Output"), "s",image_file="search.ico")