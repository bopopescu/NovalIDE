from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants


class CodeSnippetPlugin(plugin.Plugin):
    """Simple Programmer's Calculator"""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing CodeSnippet plugin")
        

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """

    def InstallHook(self):
        """Override in subclasses to allow the plugin to be loaded
        dynamically.
        @return: None

        """
        pass

    def UninstallHook(self):
        ''''''

    def EnableHook(self):
        ''''''
        
    def DisableHook(self):
        ''''''
        
    def GetFree(self):
        return True
        
    def GetPrice(self):
        ''''''
    