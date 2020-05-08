# -*- coding: utf-8 -*-
from noval import GetApp,_
import os
import noval.util.utils as utils
import noval.util.apputils as apputils
import time
from dummy.userdb import UserDataDb
from tkinter import messagebox
import noval.util.urlutils as urlutils
import sys
import noval.iface as iface
import noval.plugin as plugin
import noval.constants as constants
import noval.consts as consts
import noval.util.downutils as downutils
import noval.python.parser.utils as parserutils
import shutil
import noval.ui_utils as ui_utils


          
@utils.call_after_with_arg(1)  
def UpdateApp(app_version):
    download_url = '%s/member/download_app' % (UserDataDb.HOST_SERVER_ADDR)
    payload = dict(new_version = app_version,lang = GetApp().locale.GetLanguageCanonicalName(),os_name=sys.platform)
    #下载程序文件
    downutils.download_file(download_url,call_back=Install,**payload)
    
def CheckAppUpdate(ignore_error = False):
    api_addr = '%s/api/update/app' % (UserDataDb.HOST_SERVER_ADDR)
    app_version = apputils.get_app_version()
    #检查更新app时需要向服务器传递本地版本是否是开发版本的参数
    #如果是开发版本,则在本地版本和服务器版本号一致时仍需要提示更新,否则不提示更新
    data = urlutils.RequestData(api_addr,arg = {'app_version':app_version,'is_dev':int(utils.is_dev())})
    if data is None:
        if not ignore_error:
            messagebox.showerror(GetApp().GetAppName(),_("could not connect to server"))
        return
    CheckAppupdateInfo(data,ignore_error)
    
def CheckAppupdateInfo(data,ignore_error=False):
    #no update
    if data['code'] == 0:
        if not ignore_error:
            messagebox.showinfo(GetApp().GetAppName(),_("this is the lastest version"))
    #have update
    elif data['code'] == 1:
        new_version = data['new_version']
        ret = messagebox.askyesno(_("Update Available"),_("this lastest version '%s' is available,do you want to download and update it?") % new_version)
        if ret:
            UpdateApp(new_version)
    #other error
    else:
        if not ignore_error:
            messagebox.showerror(GetApp().GetAppName(),data['message'])

def Install(app_path):
    if utils.is_windows():
        os.startfile(app_path)
    else:
        path = os.path.dirname(sys.executable)
        pip_path = os.path.join(path,"pip")
        cmd = "%s  -c \"from distutils.sysconfig import get_python_lib; print get_python_lib()\"" % (sys.executable,)
        python_lib_path = utils.GetCommandOutput(cmd).strip()
        user = getpass.getuser()
        should_root = not fileutils.is_writable(python_lib_path,user)
        if should_root:
            cmd = "pkexec " + "%s install %s" % (pip_path,app_path)
        else:
            cmd = "%s install %s" % (pip_path,app_path)
        subprocess.call(cmd,shell=True)
        app_startup_path = whichpath.GuessPath("NovalIDE")
        #wait a moment to avoid single instance limit
        subprocess.Popen("/bin/sleep 2;%s" % app_startup_path,shell=True)
    GetApp().Quit()

class UpdateLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().InsertCommand(constants.ID_GOTO_OFFICIAL_WEB,constants.ID_CHECK_UPDATE,_("&Help"),_("&Check for Updates"),\
                    handler=lambda:self.CheckAppUpdate(ignore_error=False),pos="before")
            
    def CheckAppUpdate(self,ignore_error=True):
        CheckAppUpdate(ignore_error)

