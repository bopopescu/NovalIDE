from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from noval.project.templatemanager import ProjectTemplateManager
import gittool.gitui as gitui
import noval.consts as consts

class GitToolPlugin(plugin.Plugin):
    """plugin description here..."""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing GitTool plugin")
        
        ProjectTemplateManager().AddProjectTemplate("General",_("New Project From Git Server"),[(gitui.GitProjectNameLocationPage),gitui.LocationSelectionPage,gitui.RepositorySourcePage,\
                                                        gitui.BranchSelectionPage,gitui.LocalDestinationPage,gitui.ImportGitfilesPage]) 
        GetApp().bind(constants.PROJECTVIEW_POPUP_FILE_MENU_EVT, self.AppenFileMenu,True)
        self.project_browser = GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME)
        GetApp().AddMessageCatalog('gittool', __name__)
        GetApp().bind(constants.PROJECTVIEW_POPUP_ROOT_MENU_EVT, self.AppenRootMenu,True)
        

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """
        return "1.2.0"

    def InstallHook(self):
        """Override in subclasses to allow the plugin to be loaded
        dynamically.
        @return: None

        """
        pass

    def UninstallHook(self):
        pass

    def EnableHook(self):
        pass
        
    def DisableHook(self):
        pass
        
    def GetFree(self):
        return True
        
    def GetPrice(self):
        pass
    
    def AppenRootMenu(self, event):
        pass
        
    def AppenFileMenu(self, event):
        pass