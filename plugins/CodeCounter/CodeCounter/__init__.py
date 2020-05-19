#coding=utf-8
from noval import _,GetApp,NewId
GetApp().AddMessageCatalog('codecounter', __name__)
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from codecounter import GUI
import os

class CodeCounterPlugin(plugin.Plugin):
    """plugin description here..."""
    plugin.Implements(iface.MainWindowI)
    ID_CODE_COUNTER = NewId()
    def PlugIt(self, parent):
        """Hook the plugin into the menu and bind the event"""
        utils.get_logger().info("Installing CodeCounter plugin")
        
        

        from pkg_resources import resource_filename
        path = resource_filename(__name__,'')  
        clone_local_img_path = os.path.join(path,"codecounter.png") # 导入同一个包下的文件.
#         cloneLocaleEn=os.path.join(path,'en_US.po')
#         cloneLocaleZh=os.path.join(path,'zh_CN.po')
        

        

        
        GetApp().InsertCommand(constants.ID_UNITTEST,self.ID_CODE_COUNTER,_("&Tools"),
                                   _("Code Counter"),handler=self.open_code_counter,
                                   pos="before",image=clone_local_img_path)

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """
        return '1.2.3'

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
    def open_code_counter(self):
        from pkg_resources import resource_filename
        path = resource_filename(__name__,'')  
        clone_local_img_path = os.path.join(path,"codecounter.png") # 导入同一个包下的文件.
        GUI.main(clone_local_img_path)
        pass

    