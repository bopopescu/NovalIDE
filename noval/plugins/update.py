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
import noval.ui_utils as ui_utils

#一次性获取所有插件信息的方式,只需调用一次api接口
QUERY_ALL_PLUGINS = 0
#依次查询每个插件的信息,需要调用多次api接口
QUERY_PLUGIN_SEQUENCE = 1

@utils.compute_run_time
def get_server_plugins():
    api_addr = '%s/api/plugin' % (UserDataDb.HOST_SERVER_ADDR)
    return utils.RequestData(api_addr,method='get')    

def check_plugins(ignore_error = False,query_plugin_way = QUERY_ALL_PLUGINS):
    '''
        检查插件更新信息
        query_plugin_way:查询插件信息的方式
        QUERY_ALL_PLUGINS:表示一次性获取所有插件的信息,优点是只需查询一次api接口,
        缺点是如果插件比较多的时候,会导致返回信息量很大
        QUERY_PLUGIN_SEQUENCE:表示依次查询单个插件的信息,优点是返回的数据信息量比较小,
        缺点是要多次查询api接口
        默认使用QUERY_ALL_PLUGINS方式,后续如果插件很多的话,考虑切换第二种方式
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
        
    check_plugin_update = utils.profile_get_int("CheckPluginUpdate", True)
    plugin_datas = {}
    #获取所有插件信息
    if query_plugin_way == QUERY_ALL_PLUGINS:
        ret_data = get_server_plugins()
        if ret_data:
            plugin_datas = ret_data.get('plugins')
    for plugin_class,dist in GetApp().GetPluginManager().GetPluginDistros().items():
        plugin_version = dist.version
        plugin_name = dist.key
        if not plugin_datas:
            #调用api接口查询每个插件的信息
            api_addr = '%s/member/get_plugin' % (UserDataDb.HOST_SERVER_ADDR)
            plugin_data = utils.RequestData(api_addr,method='get',arg={'name':plugin_name})
        else:
            plugin_data = plugin_datas.get(plugin_name,{})
        if not plugin_data:
            pop_error(plugin_data)
            return
        elif 'id' not in plugin_data:
            continue
        plugin_name = plugin_data['name']
        plugin_id = plugin_data['id']
        free = int(plugin_data['free'])
        if GetApp().GetDebug():
            log = utils.get_logger().debug
        else:
            log = utils.get_logger().info
        log("plugin %s version is %s latest verison is %s",plugin_name,plugin_version,plugin_data['version'])
        #如果服务器插件收费而且用户未付费,强制检查更新
        if GetApp().GetPluginManager().GetPlugin(plugin_name).IsEnabled() and not ui_utils.check_plugin_free_or_payed(plugin_data,installed=True):
            check_plugin_update = True
        #比较安装插件版本和服务器上的插件版本是否一致
        if check_plugin_update  and parserutils.CompareCommonVersion(plugin_data['version'],plugin_version):
            ret = messagebox.askyesno(_("Plugin Update Available"),_("Plugin '%s' latest version '%s' is available,do you want to download and update it?")%(plugin_name,plugin_data['version']))
            if ret:
                new_version = plugin_data['version']
                app_version = apputils.get_app_version()
                #检查更新插件要求的软件版本是否大于当前版本,如果是则提示用户是否更新软件
                if parserutils.CompareCommonVersion(plugin_data['app_version'],app_version):
                    ret = messagebox.askyesno(GetApp().GetAppName(),_("Plugin '%s' requires application version at least '%s',Do you want to update your application?"%(plugin_name,plugin_data['app_version'])))
                    if ret == False:
                        break
                    #更新软件,如果用户执行更新安装,则程序会退出,不会执行下面的语句
                    CheckAppUpdate()
                    break
                download_url = '%s/member/download_plugin' % (UserDataDb.HOST_SERVER_ADDR)
                payload = dict(app_version = app_version,\
                    lang = GetApp().locale.GetLanguageCanonicalName(),os_name=sys.platform,plugin_id=plugin_id)
                #下载插件文件
                downutils.download_file(download_url,call_back=after_update_download,**payload)
            #插件更新太多,每次只提示一个更新即可
            break
          
@utils.call_after_with_arg(1)  
def UpdateApp(app_version):
    download_url = '%s/member/download_app' % (UserDataDb.HOST_SERVER_ADDR)
    payload = dict(new_version = app_version,lang = GetApp().locale.GetLanguageCanonicalName(),os_name=sys.platform)
    #下载程序文件
    downutils.download_file(download_url,call_back=Install,**payload)
    
def CheckAppUpdate(ignore_error = False):
    api_addr = '%s/api/update/app' % (UserDataDb.HOST_SERVER_ADDR)
    app_version = apputils.get_app_version()
    data = urlutils.RequestData(api_addr,arg = {'app_version':app_version})
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
        self.CheckPluginUpdateAfter()
            
    @utils.call_after_with_arg(1000)
    def CheckPluginUpdateAfter(self,ignore_error=True):
        #tkinter不支持多线程,要想试用多线程必须设置函数或方法为after模式
        t = threading.Thread(target=self.CheckPluginUpdate,args=(ignore_error,))
        #设置为后台线程,防止退出程序时卡死
        t.daemon = True
        t.start()

    def CheckAppUpdate(self,ignore_error=True):
        CheckAppUpdate(ignore_error)
            
    def CheckPluginUpdate(self,ignore_error=True):
        check_plugins(ignore_error)
