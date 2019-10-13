from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from dummy.userdb import UserDataDb
import os
from noval.python.plugins.pip_gui import *

class PipManagerPlugin(plugin.Plugin):
    """Simple Programmer's Calculator"""
    plugin.Implements(iface.MainWindowI)
    
    PACKAGE_FILE_NAME = "pypi_packages.txt"
    ID_PIP_GUI = NewId()
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing PipManager plugin")
        self.parent = parent
        self.GetAllPackages()
        GetApp().InsertCommand(constants.ID_OPEN_TERMINAL,self.ID_PIP_GUI,_("&Tools"),_("Manage packages..."),handler=self.ShowPipDlg,pos="before")

    def GetAllPackages(self):
        api_addr = '%s/member/get_pypi_packages' % (UserDataDb.HOST_SERVER_ADDR)
        data = utils.RequestData(api_addr,method='get')
        if data is None:
            return
        names = data['names']
        utils.get_logger().info('get total %d packages from server',len(names))
        package_data_path = self.GetPacakgeDataPath()
        with open(package_data_path,"w") as f:
            f.write('\n'.join(names))

    def GetPacakgeDataPath(self):
        app_data_path = utils.get_user_data_path()
        package_data_path = os.path.join(app_data_path,"cache",self.PACKAGE_FILE_NAME)
        return package_data_path

    def ShowPipDlg(self):
        names = GetAllPackages()
        pip_dlg = PyPiPipDialog(self.parent,package_count=len(names))
        pip_dlg.ShowModal()