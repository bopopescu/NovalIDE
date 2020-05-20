# -*- coding: utf-8 -*-
from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from dummy.userdb import UserDataDb
import os
from noval.python.plugins.pip_gui import *
import threading
import noval.util.downutils as downutils
import time
import shutil
import noval.util.urlutils as urlutils

class PipManagerPlugin(plugin.Plugin):
    """Simple Programmer's Calculator"""
    plugin.Implements(iface.MainWindowI)
    
    DEFAULT_UPDATE_INTERVAL = 1
    PACKAGE_FILE_NAME = "pypi_packages.txt"
    PACKAGE_COUNT_FILE_NAME = "pypi_packages_count.txt"
    ID_PIP_GUI = NewId()
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing PipManager plugin")
        self.parent = parent
        self.message = {'msg':_("fetching package from PyPI..")}
        self.pip_dlg = None
        if self.NeedUpdatePackages():
            utils.get_logger().info("pipmanager need update pypi packages")
            self.UpdatePypiPackages()
        else:
            utils.get_logger().info("pipmanager no need update pypi packages")

        GetApp().InsertCommand(constants.ID_OPEN_TERMINAL,self.ID_PIP_GUI,_("&Tools"),_("Manage packages..."),handler=self.ShowPipDlg,pos="before")
        
    def UpdatePypiPackages(self):
        t = threading.Thread(target=self.UpdatePackages)
        #daemon表示后台线程,即程序不用等待子线程才退出
        t.daemon = True
        t.start()

    def UpdatePackages(self):
        api_addr = '%s/api/update/packages' % (UserDataDb.HOST_SERVER_ADDR)
        
        def end_get_packages(data):
            if data is None:
                self.message = {'msg':_("can't fetch package from PyPI")}
                count = self.GetAllPackagesCount()
            else:
                utils.update_statusbar(_('update pypi packages success...'))
                count = data['count']
                package_data_count_path = self.GetPacakgeDataPath()[1]
                with open(package_data_count_path,"w") as f:
                    f.write(str(count))
            if count > 0:
                self.message = {'msg':_("There is total %d packages on PyPI")%count}
            if self.pip_dlg:
                self.pip_dlg.label_var.set(self.message['msg'])
        def end_find(data_path):
            cache_path = utils.get_cache_path()
            dest_path = os.path.join(cache_path,self.PACKAGE_FILE_NAME)
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except:
                    pass
            try:
                shutil.move(data_path,cache_path)
            except:
                pass
            api_addr2 = '%s/api/packages/count' % (UserDataDb.HOST_SERVER_ADDR)
            urlutils.fetch_url_future(api_addr2,callback=end_get_packages)   
        try:
            utils.update_statusbar(_('updateing pypi packages...'))
            downutils.download_file(api_addr,call_back=end_find,show_progress_dlg=False)
        except:
            utils.update_statusbar(_('update pypi packages fail...'))
            end_get_packages(None)
    
    def GetPacakgeDataPath(self):
        cache_path = utils.get_cache_path()
        package_data_path = os.path.join(cache_path,self.PACKAGE_FILE_NAME)
        return package_data_path,os.path.join(cache_path,self.PACKAGE_COUNT_FILE_NAME)
        
    def GetAllPackagesCount(self):
        package_data_path,package_data_count_path = self.GetPacakgeDataPath()
        if not os.path.exists(package_data_count_path) or not os.path.exists(package_data_path):
            return 0
        with open(package_data_count_path) as f:
            return int(f.read())
        return 0
        
    def NeedUpdatePackages(self):
        package_count = self.GetAllPackagesCount()
        if 0 == package_count:
            return True
        package_data_path,_ = self.GetPacakgeDataPath()
        mk_time = os.path.getmtime(package_data_path)
        now_time = time.time()
        if now_time - mk_time > self.DEFAULT_UPDATE_INTERVAL*24*3600:
            return True
        return False

    def ShowPipDlg(self):
        package_count = self.GetAllPackagesCount()
        self.pip_dlg = PyPiPipDialog(self.parent,package_count=package_count,message=self.message)
        self.pip_dlg.ShowModal()
        self.pip_dlg = None
        
    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """
        return "1.2.3"