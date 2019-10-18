# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        plugin.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-22
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp,_
import os
import sys
import shutil
import noval.util.strutils as strutils
import noval.python.parser.utils as parserutils
import noval.util.utils as utils
import noval.consts as consts
import six
import pkg_resources
try:
    from ConfigParser import ConfigParser
except:
    from configparser import ConfigParser
#--------------------------------------------------------------------------#
# Globals
ENTRYPOINT = 'Noval.plugins'
PLUGIN_CONFIG = "plugin.cfg"
_implements = []


#--------------------------------------------------------------------------#

class Interface(object):
    """Base class for defining interfaces. Interface classes are
    used to define the method/contract from which the plugin must
    conform to.
    
    """
    pass

#-----------------------------------------------------------------------------#

class ExtensionPoint(property):
    """Declares what L{Interface} a plugin is extending"""
    def __init__(self, interface):
        """Initializes the extension point
        @param interface: interface object that the extension point extends

        """
        property.__init__(self, self.Extensions)
        self.interface = interface

    def __repr__(self):
        """@return: string representation of the object"""
        return '<ExtensionPoint %s>' % self.interface.__name__

    def Extensions(self, component):
        """The exensions that extend this extention point
        @param component: The component to get the exensions for
        @return: a list of plugins that declare to impliment the
        given extension point.

        """
        component = GetApp().GetPluginManager()
        #加载所有插件,包括启用和禁止加载的插件
        extensions = PluginMeta._registry.get(self.interface, [])
        #过滤掉被禁止的插件
        return filter(None, [component[cls] for cls in extensions])

#-----------------------------------------------------------------------------#

class PluginMeta(type):
    """Acts as the registration point for plugin entrypoint objects.
    It makes sure that only a single instance of any particular entry
    point is active at one time per plugin manager.

    """
    _plugins = list()
    _registry = dict()

    def __new__(mcs, name, bases, d):
        """Initialize the MetaClass
        @param mcs: Class instance
        @param name: Name of object
        @param bases: Plugin base classes
        @param d: Items dictionary

        """
        d['_implements'] = _implements[:]
        del _implements[:]
        new_obj = type.__new__(mcs, name, bases, d)
        if name == 'Plugin':
            return new_obj

        init = d.get("__init__")
        if not init:
            for init in [b.__init__._original for b in new_obj.mro()
                         if issubclass(b, Plugin) and '__init__' in b.__dict__]:
                break

        PluginMeta._plugins.append(new_obj)
        for interface in d.get('_implements', []):
            PluginMeta._registry.setdefault(interface, []).append(new_obj)

        for base in [base for base in bases if hasattr(base, '_implements')]:
            for interface in base._implements:
                PluginMeta._registry.setdefault(interface, []).append(new_obj)
                
        return new_obj

#-----------------------------------------------------------------------------#

class Plugin(six.with_metaclass(PluginMeta, object)):
    """Base class for all plugin type objects"""
  #  __metaclass__ = PluginMeta
    __name__ = 'NovalPlugin'

    def __new__(cls, pluginmgr):
        """Only one instance of each plugin is allowed to exist
        per manager. If an instance of this plugin has already be
        initialized, that instance will be returned. If not this will
        initialize a new instance of the plugin.
        @param cls: Class object
        @keyword pluginmgr: Plugin Manager instance
        @return: a new class object or an existing instance if one
                 exists.

        """
        # Case for a pluginmanager being managed by a plugin manager
        if issubclass(cls, PluginManager):
            self = super(Plugin, cls).__new__(cls)
            self.pluginmgr = self
            return self

        plugins = pluginmgr.GetPlugins()
        self = plugins.get(cls)

        # Check if it is a default plugin
        if self is None:
            defaults = pluginmgr.GetDefaultPlugins()
            self = defaults.get(cls)

        if self is None:
            self = super(Plugin, cls).__new__(cls)
            self.pluginmgr = pluginmgr
        return self

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of Editra that
        the plugin is compatible with. By default it will return the current
        version of Editra.
        @return: version str

        """
        return utils.get_app_version()

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
        
    def IsInstalled(self):
        """Return whether the plugins L{InstallHook} method has been called
        or not already.
        @return: bool

        """
        return False

#-----------------------------------------------------------------------------#

class PluginConfigObject(object):
    """Plugin configuration object. Plugins that wish to provide a
    configuration panel should implement a subclass of this object
    in their __init__ module. The __init__ module must also have a
    function 'GetConfigObject' that returns an instance of this
    class.

    """
    def GetConfigPanel(self, parent):
        """Get the configuration panel for this plugin
        @param parent: parent window for the panel
        @return: wxPanel

        """
        raise NotImplementedError

    def GetBitmap(self):
        """Get the 32x32 bitmap to show in the config dialog
        @return: wx.Bitmap
        @note: Optional if not implemented default icon will be used

        """
        return wx.NullBitmap

    def GetLabel(self):
        """Get the display label for the configuration
        @return: string

        """
        raise NotImplementedError

#-----------------------------------------------------------------------------#

class PluginData(object):
    """A storage class for representing data about a Plugin
    @see: L{Plugin}

    """
    def __init__(self, name=u'', descript=u'', author=u'', ver=u''):
        """Create the plugin data object
        @keyword name: Name of the plugin
        @keyword descript: Short description of plugin
        @keyword author: Who made the plugin
        @keyword ver: Version of the plugin (Unicode)

        """
        super(PluginData, self).__init__()

        # Attributes
        self._name = name
        self._description = descript
        self._author = author
        self._version = ver

        self._enabled = False
        self._installed = True

        self._inst = None
        self._cls = None
        self._distro = None

    @property
    def Distribution(self):
        """Distrobution object"""
        return self.GetDist()

    @property
    def Class(self):
        """Class Reference"""
        return self.GetClass()

    def Enable(self, enabled=True):
        """Enable the plugin
        @param enable: bool

        """
        self._enabled = enabled

    def GetAuthor(self):
        """@return: Author of the plugin"""
        return self._author

    def GetClass(self):
        """@return class object of the plugin"""
        return self._cls

    def GetDescription(self):
        """@return: Plugins description string"""
        return self._description

    def GetDist(self):
        """Return the dist object associated with this plugin
        @return: Distribution

        """
        return self._distro

    def GetInstance(self):
        """Get the plugin instance
        @return: Plugin

        """
        return self._inst

    def GetName(self):
        """@return: Plugin's name string"""
        return self._name

    def GetVersion(self):
        """@return: Plugin's version string"""
        return self._version

    @property
    def Instance(self):
        """Plugin Instance"""
        return self.GetInstance()

    def IsEnabled(self):
        """Is the plugin enabled
        @return: bool

        """
        return self._enabled

    @property
    def Module(self):
        """Plugin Module Reference"""
        return getattr(self.GetInstance(), '__module__', None)

    def SetAuthor(self, author):
        """Sets the author attribute
        @param author: New Authors name string
        @postcondition: Author attribute is set to new value

        """
        if not isinstance(author, basestring):
            try:
                author = str(author)
            except (ValueError, TypeError):
                author = u''
        self._author = author

    def SetClass(self, cls):
        """Set the class used to create this plugins instance
        @param cls: class

        """
        self._cls = cls

    def SetDescription(self, descript):
        """@return: Plugins description string"""
        if not isinstance(descript, basestring):
            try:
                descript = str(descript)
            except (ValueError, TypeError):
                descript = u''
        self._description = descript

    def SetDist(self, distro):
        """Set the distribution object
        @param distro: Distribution

        """
        self._distro = distro

    def SetInstance(self, inst):
        """Set the plugin instance
        @param inst: Plugin instance

        """
        self._inst = inst

    def SetName(self, name):
        """Sets the plugins name string
        @param name: String to name plugin with
        @postcondition: Plugins name string is set

        """
        if not isinstance(name, basestring):
            try:
                name = str(name)
            except (ValueError, TypeError):
                name = u''
        self._name = name

    def SetVersion(self, ver):
        """Sets the version attribute of the plugin.
        @param ver: Version string
        @postcondition: Plugins version attribute is set to new value

        """
        if not isinstance(ver, basestring):
            try:
                ver = str(ver)
            except (ValueError, TypeError):
                ver = u''
        self._version = ver

#-----------------------------------------------------------------------------#

def Implements(*interfaces):
    """Used by L{Plugin}s to declare the interface that they
    implment/extend.
    @param interfaces: list of interfaces the plugin implements

    """
    _implements.extend(interfaces)

#--------------------------------------------------------------------------#

class PluginManager(object):
    """The PluginManger keeps track of the active plugins. It
    also provides an interface into loading and unloading plugins.
    @todo: Allow loaded but inactive plugins to be initiated without 
           needing to restart the editor.

    """
    CFG_PLUGIN_SECTION = 'Plugins'
    def __init__(self,pi_path=None):
        """Initializes a PluginManager object.
        @postcondition: Plugin manager and plugins are initialized

        """
        object.__init__(self)
        self.LOG = utils.get_logger("noval.plugin.manager")
        self.RemoveUninstalled()
        #插件配置文件对象
        self.cfg = None
        #插件加载路径列表
        self._pi_path = []
        self._config = self.LoadPluginConfig() # Enabled/Disabled Plugins
        if not pi_path:
            #加载默认插件路径,分别是用户路径以及应用程序路径
            #必须保证插件路径存在,如果不存在是不能加载到python资源环境中
            self.LoadDefaultPluginPath()
        else:
            self.AppendPath(pi_path)
        sys.path.extend(self._pi_path)
        self._env = self.CreateEnvironment(self._pi_path)

        # TODO: Combine enabled into pdata
        self._pdata = dict()        # Plugin data
        self._defaults = dict()     # Default plugins
        self._enabled = dict()      # Set of enabled plugins
        self._loaded = list()       # List of 
        self._obsolete = dict()     # Obsolete plugins list
        self.InitPlugins(self._env)
        self.RefreshConfig()

        # Enable/Disable plugins based on config data
        self.UpdateConfig()
        
    def LoadDefaultPluginPath(self):
        '''
            加载默认插件路径
        '''
        #加载用户路径
        self.AppendPath(utils.get_user_plugin_path())
        #加载应用程序路径
        self.AppendPath(utils.get_sys_plugin_path())

    def __contains__(self, cobj):
        """Returns True if a plugin is currently loaded and being
        managed by this manager.
        @param cobj: object to look for in loaded plugins

        """
        return cobj in [obj.GetClass() for obj in self._pdata]

    def __getitem__(self, cls):
        """Gets and returns the instance of given class if it has
        already been activated.
        @param cls: class object to get from metaregistery
        @return: returns either None or the intialiazed class object

        """
        nspace = cls.__module__ + "." + cls.__name__
        #默认插件默认启用
        if nspace in consts.DEFAULT_PLUGINS:
            self._enabled[cls] = True
        
        #新插件默认禁止
        if cls not in self._enabled:
            self._enabled[cls] = False # If its a new plugin disable by default

        #禁止的插件不会被加载
        if not self._enabled[cls]:
            return None

#        plugin = self._plugins.get(cls)
        plugin = None
        pdata = self._pdata.get(cls, None)
        if pdata is not None:
            plugin = pdata.GetInstance()
        else:
            # Check defaults
            plugin = self._defaults.get(cls, None)

        # Plugin not instantiated yet
        if plugin is None:
            if cls not in PluginMeta._plugins:
                self.LOG.error("[pluginmgr][err] %s Not Registered" % cls.__name__)
            try:
                plugin = cls(self)
            except (AttributeError, TypeError) as e:
                self.LOG.error("[pluginmgr][err] Unable in initialize plugin")
                self.LOG.error("[pluginmgr][err] %s" % str(e))

        return plugin

    #---- End Private Members ----#

    #---- Public Class Functions ----#
    def AppendPath(self, path):
        """Append a path to the environment path for the plugin manager 
        to look for plugins on. The path is only added to the environment
        in order for it to be used you must call RefreshEnvironment afterwards
        to re-initialize the running environment.

        @param path: path to append to environment
        @return: True if path was successfully added or False otherwise

        """
        if os.path.exists(path):
            if path not in self._pi_path:
                self._pi_path.append(path)
            return True
        else:
            return False

    def CreateEnvironment(self, path):
        """Creates the environment based on the passed
        in path list
        @param path: path(s) to scan for extension points
        @note: pkgutils does not like Unicode! only send encoded strings

        """
        if pkg_resources != None:
            if utils.is_py2():
                paths = [ strutils.EncodeString(pname, sys.getfilesystemencoding())
                         for pname in path ]
            elif utils.is_py3_plus():
                paths = path
            try:
                env = pkg_resources.Environment(paths)
            except UnicodeDecodeError as e:
                self.LOG("[pluginmgr][err] %s" % e)
        else:
            self.LOG("[pluginmgr][warn] setuptools is not installed")
            env = dict()
        return env

    def DisablePlugin(self, plugin):
        """Disables a named plugin. Is a convenience function for
        EnablePlugin(plugin, False).

        @param plugin: plugin to disable
        @precondition: plugin must be managed by this manager instance
        @postcondition: plugin is disabled and will not be activated on 
                        next reload.

        """
        self.EnablePlugin(plugin, False)

    def EnablePlugin(self, plugin_name, enable=True):
        """Enables a named plugin.
        @param plugin: plugin to enable/disable (case insensitive)
        @param enable: should plugin be enabled or disabled
        @precondition: plugin must be managed by this manager instance
        @postcondition: plugin is added to activate list for activation on
                        next program start.

        """
        for name in self._config:
            if name.lower() == plugin_name.lower():
                plugin_name = name
                break

        self._config[plugin_name] = enable
        for cls in self._enabled:
            if cls.__module__ == plugin_name:
                self._enabled[cls] = enable
        
    def GetConfig(self):
        """Returns a dictionary of plugins and there configuration state.
        @return: the mapped set of available plugins (dict)

        """
        self.RefreshConfig()
        return self._config

    def GetDefaultPlugins(self):
        """Get the loaded default plugins
        @return: dict(cls=instance)

        """
        return self._defaults

    def GetEnvironment(self):
        """Returns the environment that the plugin manager is currently
        running with.
        @return: the managers environment

        """
        return self._env

    def GetIncompatible(self):
        """Get the list of loaded plugins that are incompatible with the
        current running version of Editra.
        return: dict(name=module)

        """
        return self._obsolete

    def GetPlugins(self):
        """Returns a the dictionary of plugins managed by this manager
        @return: all plugins managed by this manger (dict)

        """
        plugins = dict()
        for pdata in self._pdata.values():
            plugins[pdata.GetClass()] = pdata.GetInstance()
        return plugins

    def FindPluginByegg(self,egg_path):
        '''
            从egg文件路径查找是否加载插件
        '''
        for pdata in self._pdata.values():
            dist =  pdata.GetDist()
            if not strutils.caseInsensitiveCompare(strutils.normpath_with_actual_case(egg_path),strutils.normpath_with_actual_case(dist.location)):
                return pdata
        return None
        
    def GetPluginDistro(self, pname):
        """Get the distrobution object for a given plugin name
        @param pname: plugin name
        @return: Distrobution

        """
        for pdata in self._pdata.values():
            if pname.lower() == pdata.GetName().lower():
                return pdata.GetDist()
        else:
            return None

    def GetPluginDistros(self):
        """Get the plugin distrobution objects
        @return: dict(name=Distrobution)

        """
        distros = dict()
        for name, pdata in self._pdata.items():
            distros[name] = pdata.GetDist()
        return distros

    def InitPlugins(self, env):
        """Initializes the plugins that are contained in the given
        environment. After calling this the list of available plugins
        can be obtained by calling GetPlugins.
        @note: plugins must emit the ENTRY_POINT defined in this file in order
               to be recognized and initialized.
        @postcondition: all plugins in the environment are initialized

        """
        if pkg_resources is None:
            return

        pkg_env = env
        tmploaded = [ name.lower() for name in self._loaded ]
        for name in pkg_env:
            self.LOG.info("Found plugin: %s" % name)
            if name.lower() in tmploaded:
                self.LOG.info("[pluginmgr][info] %s is already loaded" % name)
                continue

            egg = pkg_env[name][0]  # egg is of type Distribution
            egg.activate()
            for name in egg.get_entry_map(ENTRYPOINT):
                try:
                    # Only load a given entrypoint once
                    if name not in self._loaded:
                        entry_point = egg.get_entry_info(ENTRYPOINT, name)
                        cls = entry_point.load()
                        self._loaded.append(name)
                    else:
                        #一些插件由于版本号不同重复加载了,重复只加载一次
                        self.LOG.info("[pluginmgr][info] Skip reloading: %s" % name)
                        continue
                except Exception as e:
                    self.LOG.error("[pluginmgr][err] Couldn't Load %s: %s" % (name, e))
                else:
                    try:
                        # Only initialize plugins that haven't already been
                        # initialized
                        if cls not in self._pdata:
                            self.LOG.info("Creating Instance of %s" % name)
                            instance = cls(self)
                            minv = instance.GetMinVersion()
                            #检查插件要求的软件版本号是否小于等于当前版本号
                            #如果版本号为空,则说明对软件版本号没有限制
                            if not minv or not parserutils.CompareCommonVersion(minv,utils.get_app_version()):
                                mod = instance.__module__
                                desc = getattr(mod, '__doc__', _("No Description Available"))
                                auth = getattr(mod, '__author__', _("Unknown"))
                                pdata = PluginData(egg.project_name,
                                                   desc.strip(),
                                                   auth.strip(),
                                                   egg.version)
                                pdata.SetDist(egg)
                                pdata.SetInstance(instance)
                                pdata.SetClass(cls)
                                if name.lower() in self._config:
                                    pdata.Enable(self._config[name.lower()])
                                self._pdata[cls] = pdata
                                self.LOG.info("[pluginmgr][info] Cached Plugin: %s" % egg.project_name)
                            else:
                                # Save plugins that are not compatible with
                                # this version to use for notifications.
                                self._obsolete[name] = cls.__module__
                        else:
                            self.LOG("[pluginmgr][info] Skip re-init of %s" % cls)
                    finally:
                        pass
                        

        # Activate all default plugins
        for d_pi in consts.DEFAULT_PLUGINS:
            obj = d_pi.split(".")
            mod = ".".join(obj[:-1])
            entry = __import__(mod, globals(), globals(), ['__name__'])
            if hasattr(entry, obj[-1]) and entry not in self._defaults:
                entry = getattr(entry, obj[-1])
                self._defaults[entry] = entry(self)

        return True

    def LoadPluginByName(self, name):
        """Loads a named plugin.
        @todo: Implement this method

        """
        #安装插件后加载插件时必须重新初始化
        self.ReInit()
        for pdata in self._pdata.values():
            if name.lower() == pdata.GetName().lower():
                plugin_instance = pdata.GetInstance()
                plugin_instance.InstallHook()
        
    def LoadPluginConfig(self):
        """Loads the plugin config file for the current user if
        it exists. The configuration file contains which plugins
        are active and which ones are not.
        @return: configuration dictionary

        """
        config = dict()
        plugin_config_path = self.GetPlugincfgPath()
        try:
            self.cfg = ConfigParser()
            self.cfg.read(plugin_config_path)
            options = self.cfg.options(self.CFG_PLUGIN_SECTION)
            for option in options:
                config[option] = bool(self.cfg.getint(self.CFG_PLUGIN_SECTION,option))
            self.LOG.info("load plugin config file %s success" % plugin_config_path)
        except:
            self.LOG.info("Failed to read plugin config file %s " % plugin_config_path)
        return config

    def RefreshConfig(self):
        """Refreshes the config data comparing the loadable
        plugins against the config data and removing any entries
        that dont exist in both from the configuration data.
        @postcondition: entries that could not be loaded or do not
                        exist any longer are removed from the config

        """
        plugins = [ plugin.GetInstance().__module__
                    for plugin in self._pdata.values() ]

        config = dict()
        for item in self._config:
            if item in plugins:
                config[item] = self._config[item]
        self._config = config

    def RefreshEnvironment(self):
        """Refreshes the current environment to include any
        plugins that may have been added since init.
        @postcondition: environment is refreshed

        """
        self._env = self.CreateEnvironment(self._pi_path)

    def ReInit(self):
        """Reinitializes the plugin environment and all plugins
        in the environment as well as the configuration data.
        @postcondition: the manager is reinitialized to reflect
                        any configuration or environment changes
                        that may have occured.

        """
        #重新初始化时重新加载默认插件路径
        self.LoadDefaultPluginPath()
        self.RefreshEnvironment()
        self.InitPlugins(self.GetEnvironment())
        self.RefreshConfig()
        self.UpdateConfig()

    def RemoveUninstalled(self):
        """Remove all uninstalled plugins
        @todo: need error reporting and handling file permissions
        @todo: handle multiple older versions that are installed
        @todo: handle when installed in multiple locations

        """
        plist = utils.profile_get('UNINSTALL_PLUGINS', default_value=list())
        for path in list(plist):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except OSError:
                # TODO: don't delete from list, so it can be kept to report
                #       removal errors to user.
                if not os.path.exists(path):
                    plist.remove(path)
                continue
            else:
                self.LOG.info("[pluginmgr][info] Uninstalled: %s" % path)
                plist.remove(path)
        utils.profile_set('UNINSTALL_PLUGINS', plist)

    def UnloadPluginByName(self, name):
        """Unloads a named plugin.
        @todo: implement this method

        """
        for pdata in self._pdata.values():
            if name.lower() == pdata.GetName().lower():
                plugin_instance = pdata.GetInstance()
                plugin_instance.UninstallHook()
                
    def EnablePluginByName(self, name):
        """Unloads a named plugin.
        @todo: implement this method

        """
        for pdata in self._pdata.values():
            if name.lower() == pdata.GetName().lower():
                plugin_instance = pdata.GetInstance()
                plugin_instance.EnableHook()
                
    def DisablePluginByName(self, name):
        """Unloads a named plugin.
        @todo: implement this method

        """
        for pdata in self._pdata.values():
            if name.lower() == pdata.GetName().lower():
                plugin_instance = pdata.GetInstance()
                plugin_instance.DisableHook()
        
    def UpdateConfig(self):
        """Updates the in memory config data to recognize
        any plugins that may have been added or initialzed
        by a call to InitPlugins.
        @postcondition: plugins are enabled or disabled based
                        on the configuration data.

        """
        for pdata in self._pdata.values():
            plugin = pdata.GetClass()
            if self._config.get(plugin.__module__):
                self._enabled[plugin] = True
            else:
                self._config[plugin.__module__] = False
                self._enabled[plugin] = False

    def WritePluginConfig(self):
        """Writes out the plugin config.
        @postcondition: the configuration data is saved to disk

        """
        if self.cfg is None:
            return
       # writer.write("# Editra %s Plugin Config\n#\n" % ed_glob.VERSION)
       #writer.write("\n# EOF\n")
       #在初始化配置文件为空的时候,必须要先添加段才能写入数据
        if not self.cfg.has_section(self.CFG_PLUGIN_SECTION):
            self.cfg.add_section(self.CFG_PLUGIN_SECTION)
            
        for item in self._config:
            self.cfg.set(self.CFG_PLUGIN_SECTION,item,str(int(self._config[item])))
            
        plugin_config_path = self.GetPlugincfgPath()
        try:
            with open(plugin_config_path,"w") as f:
                self.cfg.write(f)
        except:
            self.LOG.error("[pluginmgr][err] Failed to write plugin config")
        
    def GetPlugincfgPath(self):
        '''
            插件配置文件路径,在C:\\Users\\Administrator\\AppData\\Roaming\\NovalIDE目录下
        '''
        app_data_path = utils.get_user_data_path()
        plugin_config_path = os.path.join(app_data_path,PLUGIN_CONFIG)
        return plugin_config_path
        
    def GetPluginData(self):
        return self._pdata.values()