# -*- coding: utf-8 -*-
from noval import GetApp,_
import threading
import noval.util.appdirs as appdirs
import noval.python.parser.utils as dirutils
import os
import noval.util.utils as utils
import noval.util.apputils as apputils
import time
from dummy.userdb import UserDataDb
import noval.ui_base as ui_base
from tkinter import messagebox
import noval.util.urlutils as urlutils
import sys
import requests
import noval.iface as iface
import noval.plugin as plugin
import noval.constants as constants
import noval.consts as consts

class DownloadProgressDialog(ui_base.GenericProgressDialog):
    
    def __init__(self,parent,file_sie,file_name):
        welcome_msg = _("Please wait a minute for Downloading")
        ui_base.GenericProgressDialog.__init__(self,parent,_("Downloading %s") % file_name,info=welcome_msg,maximum = file_sie)

class FileDownloader(object):
    
    def __init__(self,file_length,file_name,req,call_back=None):
        self._file_size = file_length
        self._file_name = file_name
        self._req = req
        self._call_back = call_back
    
    def StartDownloadApp(self):
        
        def DownloadCallBack():
            download_progress_dlg.keep_going = False
            download_progress_dlg.destroy()
            if self._call_back is not None and not download_progress_dlg.is_cancel:
                GetApp().MainFrame.after(300,self._call_back,download_file_path)
            
        download_progress_dlg = DownloadProgressDialog(GetApp().GetTopWindow(),int(self._file_size),self._file_name)
        download_tmp_path = os.path.join(appdirs.get_user_data_path(),"download")
        if not os.path.exists(download_tmp_path):
            dirutils.MakeDirs(download_tmp_path)
        download_file_path = os.path.join(download_tmp_path,self._file_name)
        try:
            self.DownloadFile(download_file_path,download_progress_dlg,callback=DownloadCallBack,err_callback=download_progress_dlg.destroy)
        except:
            return

    def DownloadFile(self,download_file_path,progress_ui,callback,err_callback=None):
        t = threading.Thread(target=self.DownloadFileContent,args=(download_file_path,self._req,progress_ui,callback,err_callback))
        t.start()
        
    def DownloadFileContent(self,download_file_path,req,progress_ui,callback,err_callback=None):
        f = open(download_file_path, "wb")
        try:
            ammount = 0
            for chunk in req.iter_content(chunk_size=512):
                if chunk:
                    if progress_ui.is_cancel:
                        break
                    f.write(chunk)
                    ammount += len(chunk)
                    progress_ui.SetValue(ammount)
        except Exception as e:
            messagebox.showerror("",_("Download fail:%s") % e)
            if err_callback:
                err_callback()
            f.close()
            return
        f.close()
        callback()


def CheckAppUpdate(ignore_error = False):
    api_addr = '%s/member/get_update' % (UserDataDb.HOST_SERVER_ADDR)
    #获取语言的类似en_US,zh_CN这样的名称
    lang = GetApp().locale.GetLanguageCanonicalName()
    app_version = apputils.get_app_version()
    data = urlutils.RequestData(api_addr,arg = {'app_version':app_version,'lang':lang})
    if data is None:
        if not ignore_error:
            messagebox.showerror(GetApp().GetAppName(),_("could not connect to server"))
        return
    #no update
    if data['code'] == 0:
        if not ignore_error:
            messagebox.showinfo(GetApp().GetAppName(),data['message'])
    #have update
    elif data['code'] == 1:
        ret = messagebox.askyesno(_("Update Available"),data['message'])
        if ret:
            new_version = data['new_version']
            download_url = '%s/member/download_app' % (UserDataDb.HOST_SERVER_ADDR)
            payload = dict(new_version = new_version,lang = lang,os_name=sys.platform)
            user_id = UserDataDb().GetUserId()
            if user_id:
                payload.update({'member_id':user_id})
            req = requests.get(download_url,params=payload, stream=True)
            if 'Content-Length' not in req.headers:
                data = req.json()
                if data['code'] != 0:
                    messagebox.showerror(GetApp().GetAppName(),data['message'])
            else:
                file_length = req.headers['Content-Length']
                content_disposition = req.headers['Content-Disposition']
                file_name = content_disposition[content_disposition.find(";") + 1:].replace("filename=","").replace("\"","")
                file_downloader = FileDownloader(file_length,file_name,req,Install)
                file_downloader.StartDownloadApp()
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
        python_lib_path = Interpreter.GetCommandOutput(cmd).strip()
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
                    handler=lambda:self.CheckUpdate(ignore_error=False),pos="before")
        if utils.profile_get_int(consts.CHECK_UPDATE_ATSTARTUP_KEY, True):
            GetApp().after(1000,self.CheckUpdate)

    def CheckUpdate(self,ignore_error=True):
        CheckAppUpdate(ignore_error)
