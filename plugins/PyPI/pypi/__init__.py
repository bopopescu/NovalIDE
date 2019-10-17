# -*- coding: utf-8 -*-
###############################################################################
# Name: __init__.py                                                           #
# Purpose: Simple Calculator Plugin                                           #
# Author: Cody Precord <cprecord@editra.org>                                  #

"""Simple Programmer's Calculator"""
__author__ = "Cody Precord"
__version__ = "0.6"

#-----------------------------------------------------------------------------#
from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
from tkinter import ttk,messagebox
import noval.util.utils as utils
import noval.constants as constants 
from noval.project.templatemanager import ProjectTemplateManager
from noval.project.debugger import OutputRunCommandUI
from noval.python.debugger.output import *
from noval.project.baseconfig import *
import noval.python.debugger.debugger as pythondebugger
import noval.consts as consts
import noval.util.fileutils as fileutils
import pypi.pypi as pypi
import noval.python.project.runconfiguration as runconfiguration
import os
import noval.python.interpreter.interpretermanager as interpretermanager
import shutil
import noval.python.parser.utils as dirutils
import noval.terminal as terminal
import noval.ui_utils as ui_utils
import noval.python.pyutils as pyutils
from dummy.userdb import UserDataDb
import noval.python.interpreter.pythonpackages as pythonpackages
# Local imports
#-----------------------------------------------------------------------------#

# Try and add this plugins message catalogs to the app


#-----------------------------------------------------------------------------#

pypyrc_template = '''[distutils]
index-servers = pypi

[pypi]
repository: https://pypi.python.org/pypi
username: {username}
password: {password}
'''

class PypiAccountDialog(ui_utils.CommonAccountDialog):
    def __init__(self,parent):
        ui_utils.CommonAccountDialog.__init__(self,parent,_("PyPI Account"),_("Please input PyPI account:"))

class PyPi(plugin.Plugin):
    """Simple Programmer's Calculator"""
    plugin.Implements(iface.MainWindowI)
    ID_PUBLISH_SERVER = NewId()
    ID_PUBLISH_LOCAL = NewId()
    def PlugIt(self, parent):
        self.parent = parent
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing PyPi plugin")
        ProjectTemplateManager().AddProjectTemplate("Python/PyPI",_("PyPI Package"),[pypi.PypiProjectNameLocationPage,pypi.PypiPackageInformationPage,pypi.PypiOptionPage]) 
        ProjectTemplateManager().AddProjectTemplate("Python/PyPI",_("PyPI Package Tool"),[pypi.PypiProjectNameLocationPage,pypi.PypiPackageToolInformationPage,pypi.PypiOptionPage])
        if GetApp().GetDebug(): 
            ProjectTemplateManager().AddProjectTemplate("Python/PyPI",_("Noval Plugin"),[pypi.PypiProjectNameLocationPage,pypi.NovalPluginInformationPage]) 
        GetApp().bind(constants.PROJECTVIEW_POPUP_FILE_MENU_EVT, self.AppenFileMenu,True)
        self.project_browser = GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME)
        GetApp().AddMessageCatalog('pypi', __name__)

    def AppenFileMenu(self, event):
         menu = event.get('menu')
         tree_item = event.get('item')
         view = self.project_browser.GetView()
         filePath = view._GetItemFilePath(tree_item)
         if view._IsItemFile(tree_item) and fileutils.is_python_file(filePath):
            item_file = view.GetDocument().GetModel().FindFile(filePath)
            file_configuration = runconfiguration.FileConfiguration(view.GetDocument(),item_file)
            file_configuration_list = file_configuration.LoadConfigurationNames()
            utils.get_logger().info("%s======================",file_configuration_list)
            if file_configuration_list:
                if file_configuration_list[0] == 'bdist_egg':
                    menu.add_separator()
                    menu.Append(self.ID_PUBLISH_LOCAL,_("&Publish to Application Install Path"),handler=self.PublishToInstallPath)
                    menu.Append(self.ID_PUBLISH_SERVER,_("&Publish to Web Server"),handler=self.PublishToServer)
                elif file_configuration_list[0] == 'sdist':
                    menu.add_separator()
                    menu.Append(self.ID_PUBLISH_LOCAL,_("&Publish to Local site-packages"),handler=self.PublishToSitePackages)
                    menu.Append(self.ID_PUBLISH_SERVER,_("&Publish to PyPI Server"),handler=self.PublishToPypi)
                    
    def GetDistPath(self):
        view = self.project_browser.GetView()
        project_path  = os.path.dirname(view.GetDocument().GetFilename())
        dist_path = os.path.join(project_path,'dist')
        return dist_path
        
    def GetInstallPluginPath(self,plugin_name):
        dist = GetApp().GetPluginManager().GetPluginDistro(plugin_name)
        #如果插件未安装则选择2种插件目录中的一种
        if not dist:
            #软件安装目录
            plugin_path = utils.get_sys_plugin_path()
        else:
            plugin_path = os.path.dirname(dist.location)
        utils.get_logger().info("plugin %s install path is %s",plugin_name,plugin_path)
        dirutils.MakeDirs(plugin_path)
        return plugin_path
        
    def PublishToServer(self):
        '''
            发布并上传插件到web服务器
        '''
        def get_key_value(line,key,flag,data):
            if line.find(flag) != -1:
                data[key] = line.replace(flag,"").strip()
        interpreter = self.GetProjectDocInterpreter()
        startup_file = self.GetProjectStartupFile()
        project_path = self.GetProjectPath()
        args1 = "%s egg_info --egg-base %s" % (startup_file.filePath,project_path)
        pyutils.create_python_interpreter_process(interpreter,args1)
        egg_path,plugin_name,version = self.GetEgg()
        if not os.path.exists(egg_path):
            messagebox.showerror(_('Pulish to Server'),_("egg file %s is not exist")%egg_path,parent=self.parent)
            return
        pkg_file_path = os.path.join(project_path,"%s.egg-info/PKG-INFO"%(plugin_name))
        if not os.path.exists(pkg_file_path):
            messagebox.showerror(_('Pulish to Server'),_("pkg file %s is not exist")%pkg_file_path,parent=self.parent)
            return
            
        data = {}
        dist_path = self.GetDistPath()
        #获取插件源数据信息,必须先实例化插件
        dist_env = GetApp().GetPluginManager().CreateEnvironment([dist_path])
        for name in dist_env:
            egg = dist_env[name][0]  # egg is of type Distribution
            assert(egg.project_name == plugin_name)
            if egg.version != version:
                continue
            egg.activate()
            for name in egg.get_entry_map(plugin.ENTRYPOINT):
                entry_point = egg.get_entry_info(plugin.ENTRYPOINT, name)
                cls = entry_point.load()
                #实例化插件对象
                instance = cls(GetApp().GetPluginManager())
                free = instance.GetFree()
                assert(type(free) == bool)
                data['free'] = int(free)
                price = None
                if not free:
                    price = instance.GetPrice()
                    assert(type(price) == int or type(price) == float)
                data['price'] = price
                data['app_version'] = instance.GetMinVersion()
        
        with open(pkg_file_path) as f:
            for line in f:
                line = line.strip()
                get_key_value(line,'name',"Name:",data)
                get_key_value(line,'version',"Version:",data)
                get_key_value(line,"summary","Summary:",data)
                get_key_value(line,"homepage","Home-page:",data)
                get_key_value(line,"author","Author:",data)
                get_key_value(line,"author_mail","Author-email:",data)
          #      get_key_value(line,"Platform:",data)
        api_addr = '%s/member/publish' % (UserDataDb.HOST_SERVER_ADDR)
        #如果版本已经存在,先不要强制替换
        data['force_update'] = 0
        user_id = UserDataDb().GetUserId()
        if user_id is None:
            UserDataDb().GetUser()
            user_id = UserDataDb().GetUserId()
        data['member_id'] = user_id
        data['egg_name'] = os.path.basename(egg_path)
        ret = utils.upload_file(api_addr,file=egg_path,arg=data)
        if not ret:
            utils.get_logger().error('upload plugin %s fail',data['name'])
            messagebox.showerror(_('Publish to Server'),_("Publish fail"),parent=self.parent)
            return
        utils.get_logger().debug('ret is %s',ret)
        #已有版本已经存在,提示用户是否强制替换
        if ret['code'] == 1:
            result = messagebox.askyesno(_('Publish to Server'),ret['message'].format(version=data['version'],name=data['name']),parent=self.parent)
            if result == False:
                return
            #强制更新版本
            data['force_update'] = 1
            ret = utils.upload_file(api_addr,file=egg_path,arg=data)
            if not ret:
                utils.get_logger().error('upload plugin %s fail',data['name'])
                messagebox.showerror(_('Publish to Server'),_("Publish fail"),parent=self.parent)
                return
    
        if ret['code'] == 0:
            messagebox.showinfo(_('Publish to Server'),_("Publish success"),parent=self.parent)
        else:
            messagebox.showerror(_('Publish to Server'),_("Publish fail"),parent=self.parent)
            
    def GetEgg(self):
        dist_path = self.GetDistPath()
        startup_file = self.GetProjectStartupFile()
        interpreter = self.GetProjectDocInterpreter()
        cmd = "%s %s --help --fullname"%(interpreter.Path,startup_file.filePath)
        output = utils.GetCommandOutput(cmd)
        fullname = output.strip()
        utils.get_logger().info("interpreter %s minorversion is %s--------------",interpreter.Name,interpreter.MinorVersion)
        if not interpreter.MinorVersion:
            interpreter.GetMinorVersion()
            interpretermanager.InterpreterManager().SavePythonInterpretersConfig()
        egg_path = "%s/%s-py%s.egg"%(dist_path,fullname,interpreter.MinorVersion)
        plugin_name = fullname.split("-")[0]
        version = fullname.split("-")[1]
        return egg_path,plugin_name,version
        
    def PublishToInstallPath(self):
        '''
            发布插件到本地
        '''
        egg_path,plugin_name,_v = self.GetEgg()
        if not os.path.exists(egg_path):
            messagebox.showerror(_('Publish to local'),_("egg file %s is not exist")%egg_path,parent=self.parent)
        else:
            plugin_path = self.GetInstallPluginPath(plugin_name)
            shutil.copy(egg_path,plugin_path)
            GetApp().GetPluginManager().EnablePlugin(plugin_name)
            messagebox.showinfo(_('Publish to local'),_("Publish success"),parent=self.parent)
            
    def GetProjectDocInterpreter(self):
        doc = self.project_browser.GetView().GetDocument()
        interpreter_info = doc.GetModel().interpreter
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_info.name)
        return interpreter
        
    def GetProjectStartupFile(self):
        doc = self.project_browser.GetView().GetDocument()
        startup_file = doc.GetModel().StartupFile
        return startup_file
        
    def GetProjectPath(self):
        doc = self.project_browser.GetView().GetDocument()
        return os.path.dirname(doc.GetFilename())

    def PublishToSitePackages(self):
        '''
            发布pypi包到本地解释器
        '''
        view = self.project_browser.GetView()
        dist_path = self.GetDistPath()
        filePath = view.GetSelectedFile()
        interpreter = self.GetProjectDocInterpreter()
        command = "%s %s install"%(interpreter.Path,filePath)
        utils.get_logger().info("start run setup install command: %s in terminal",command)
        terminal.run_in_terminal(command,self.GetProjectPath(),keep_open=False,pause=True,title="abc",overwrite_env=False)

    def PublishToPypi(self):
        '''
            发布pypi包到pypi服务器
        '''
        ret = messagebox.askyesno(GetApp().GetAppName(),_("Are you sure to publish to PyPI?"),parent=self.parent)
        if ret == False:
            return
        view = self.project_browser.GetView()
        dist_path = self.GetDistPath()
        filePath = view.GetSelectedFile()
        interpreter = self.GetProjectDocInterpreter()
        cmd = "%s %s --help --fullname"%(interpreter.Path,filePath)
        output = utils.GetCommandOutput(cmd)
        fullname = output.strip()
        
        zip_path = "%s/%s.zip"%(dist_path,fullname)
        gz_path = "%s/%s.tar.gz"%(dist_path,fullname)
        if os.path.exists(zip_path):
            upload_path = zip_path
        elif os.path.exists(gz_path):
            upload_path = gz_path
        else:
            messagebox.showerror(GetApp().GetAppName(),_("zip file '%s' or gz file '%s' are not exist")%(zip_path,gz_path),parent=self.parent)
            return
            
        home_path = utils.get_home_dir()
        pypirc_filepath = os.path.join(home_path,".pypirc")
        utils.get_logger().info("pypirc path is %s",pypirc_filepath)
        if not interpreter.GetInstallPackage("twine"):
            messagebox.showinfo(GetApp().GetAppName(),_("interpreter %s need to install package \"twine\"")%interpreter.Name,parent=self.parent)
            dlg = pythonpackages.InstallPackagesDialog(self.parent,interpreter,pkg_name='twine',install_args='twine',autorun=True)
            status = dlg.ShowModal()
            if status == constants.ID_CANCEL:
                return
        if not os.path.exists(pypirc_filepath):
            account_dlg = PypiAccountDialog(self.parent)
            if constants.ID_OK == account_dlg.ShowModal():
                with open(pypirc_filepath,"w") as f:
                    content = pypyrc_template.format(username=account_dlg.name_var.get(),password=account_dlg.password_var.get())
                    f.write(content)
            else:
                return
        if utils.is_windows():
            interpreter_path = interpreter.InstallPath
            twine_tool_path = os.path.join(interpreter_path,"Scripts","twine.exe")
            command = "%s upload %s"%(twine_tool_path,upload_path)
        else:
            command = "twine upload %s"%(upload_path)
        utils.get_logger().info("start run twine upload command: %s in terminal",command)
        terminal.run_in_terminal(command,os.path.dirname(doc.GetFilename()),keep_open=False,pause=True,title="abc",overwrite_env=False)