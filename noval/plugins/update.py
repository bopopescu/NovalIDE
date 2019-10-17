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
import threading
import shutil

def check_plugins(ignore_error = False):
    '''
        检查插件更新信息
    '''
    def pop_error(data):
        if data is None:
            if not ignore_error:
                messagebox.showerror(GetApp().GetAppName(),_("could not connect to server"))
                
    def after_update_download(egg_path):
        '''
            插件更新下载后回调函数
        '''
        plugin_path = os.path.dirname(dist.location)
        #删除已经存在的旧版本否则会和新版本混在一起,有可能加载的是老版本
        try:
            os.remove(dist.location)
            utils.get_logger().info("remove plugin %s old version %s file %s success",plugin_name,plugin_version,dist.location)
            dest_egg_path = os.path.join(plugin_path,plugin_data['path'])
            if os.path.exists(dest_egg_path):
                logger.error("plugin %s version %s dist egg path is exist when update it",plugin_name,plugin_data['version'],dest_egg_path)
                os.remove(dest_egg_path)
        except:
            messagebox.showerror(GetApp().GetAppName(),_("Remove faile:%s fail") % dist.location)
            return
        #将下载的插件文件移至插件目录下
        shutil.move(egg_path,plugin_path)
        #执行插件的安装操作,需要在插件里面执行
        GetApp().GetPluginManager().LoadPluginByName(plugin_name)
        messagebox.showinfo(GetApp().GetAppName(),_("Update plugin '%s' success") % plugin_name)
        
    user_id = UserDataDb().GetUserId()
    check_plugin_update = utils.profile_get_int("CheckPluginUpdate", True)
    for plugin_class,dist in GetApp().GetPluginManager().GetPluginDistros().items():
        plugin_version = dist.version
        plugin_name = dist.key
        api_addr = '%s/member/get_plugin' % (UserDataDb.HOST_SERVER_ADDR)
        plugin_data = utils.RequestData(api_addr,method='get',arg={'name':plugin_name})
        if not plugin_data:
            pop_error(plugin_data)
            return
        elif 'id' not in plugin_data:
            logger.warn("could not find plugin %s on server",plugin_name)
            continue
        plugin_name = plugin_data['name']
        plugin_id = plugin_data['id']
        free = int(plugin_data['free'])
        if GetApp().GetDebug():
            log = utils.get_logger().debug
        else:
            log = utils.get_logger().info
        log("plugin %s version is %s latest verison is %s",plugin_name,plugin_version,plugin_data['version'])
        #插件是否免费
        if not free:
            #查询用户是否付款
            api_addr = '%s/member/get_payment' % (UserDataDb.HOST_SERVER_ADDR)
            data = urlutils.RequestData(api_addr,arg = {'member_id':user_id,'plugin_id':plugin_id})
            if not data:
                pop_error(data)
                return
            payed = int(data['payed'])
            #如果服务器插件收费而且用户未付费,强制检查更新
            if not payed:
                check_plugin_update = True
            price = plugin_data.get('price',None)
            #用户没有付款而且插件存在价格,弹出付款二维码
            if not payed and price:
                #这里弹出付款二维码
                pass
        #比较安装插件版本和服务器上的插件版本是否一致
        if check_plugin_update  and parserutils.CompareCommonVersion(plugin_data['version'],plugin_version):
            ret = messagebox.askyesno(_("Plugin Update Available"),_("Plugin '%s' latest version '%s' is available,do you want to download and update it?")%(plugin_name,plugin_data['version']))
            if ret:
                new_version = plugin_data['version']
                download_url = '%s/member/download_plugin' % (UserDataDb.HOST_SERVER_ADDR)
                payload = dict(app_version = apputils.get_app_version(),\
                    lang = GetApp().locale.GetLanguageCanonicalName(),os_name=sys.platform,plugin_id=plugin_id)
                #下载插件文件
                downutils.download_file(download_url,call_back=after_update_download,**payload)
            #插件更新太多,每次只提示一个更新即可
            break

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
            #下载程序文件
            downutils.download_file(download_url,call_back=Install,**payload)
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
    

def CheckForceupdate():
    '''
        某些版本太老了,需要强制更新
    '''
    app_version = apputils.get_app_version()
    check_url = '%s/member/check_force_update' % (UserDataDb.HOST_SERVER_ADDR)
    try:
        req = urlutils.RequestData(check_url,arg={'app_version':app_version})
        return req.get('force_update',False)
    except:
        return False

class UpdateLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        #是否需要强制更新
        force_update = CheckForceupdate()
        GetApp().InsertCommand(constants.ID_GOTO_OFFICIAL_WEB,constants.ID_CHECK_UPDATE,_("&Help"),_("&Check for Updates"),\
                    handler=lambda:self.CheckUpdate(ignore_error=False,check_plugin_update=False),pos="before")
        if utils.profile_get_int(consts.CHECK_UPDATE_ATSTARTUP_KEY, True) or force_update:
            self.CheckUpdateAfter()
            
    @utils.call_after
    def CheckUpdateAfter(self,ignore_error=True,check_plugin_update=True):
        #tkinter不支持多线程,要想试用多线程必须设置函数或方法为after模式
        t = threading.Thread(target=self.CheckUpdate,args=(ignore_error,check_plugin_update))
        t.start()

    def CheckUpdate(self,ignore_error=True,check_plugin_update=True):
        CheckAppUpdate(ignore_error)
        if check_plugin_update:
            check_plugins(ignore_error)
