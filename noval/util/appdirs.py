# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        appdirs.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-08
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------

import sys
import os
import string
import noval.util.apputils as apputils
from noval import GetApp

PLUGIN_DIR_NAME = "plugins"

def _getSystemDir(kind):
    '''
        获取软件的工作目录,比如项目默认的存放路径等
    '''
    if (kind == AG_LOGS_DIR):
        return os.path.join(getSystemDir(AG_SYSTEM_DIR) , "logs")
    elif (kind == AG_DEMOS_DIR):
        return os.path.join(getSystemDir(AG_SYSTEM_DIR), "demos")
    else:
        path = os.getenv("AG_DOCUMENTS_DIR")
        if ((path is None) or (len(path) < 1)):
            if apputils.is_windows():
                try:
                    from win32com.shell import shell, shellcon
                    path = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
                except:
                    pass
                if ((path is None) or (len(path) < 1)):
                    homedrive = asString(os.getenv("HOMEDRIVE"))
                    homepath = os.getenv("HOMEPATH")
##                        if ((homedrive is not None) and (len(homedrive) > 0) and (homepath is not None) and (len(homepath) > 0)):
                    path = os.path.join(homedrive, homepath, "MYDOCU~1")
            else:
                if sys.platform == "darwin":
                    try:
                        import macfs
                        import MACFS
                        fsspec_disk, fsspec_desktop = macfs.FindFolder(MACFS.kOnSystemDisk, MACFS.kDocumentsFolderType, 0)
                        path = macfs.FSSpec((fsspec_disk, fsspec_desktop, '')).as_pathname()
                    except:
                        pass
            
            if ((path is None) or (len(path) < 1)):
                path = os.path.expanduser("~")
            if ((path is None) or (len(path) < 1)):
                path = "/"
            path = os.path.join(path, "NovalIDE")
            
        return path
        

AG_SYSTEM_DIR = 0
AG_LOGS_DIR = 1
AG_DEMOS_DIR = 2

__systemDir = None
__logsDir = None
__demosDir = None

def getSystemDir(kind=0):
    if (kind == AG_SYSTEM_DIR):
        global __systemDir
        if (__systemDir is None):
            __systemDir = _getSystemDir(kind)
        return __systemDir
    elif (kind == AG_LOGS_DIR):
        global __logsDir
        if (__logsDir is None):
            __logsDir = _getSystemDir(kind)
        return __logsDir
    elif (kind == AG_DEMOS_DIR):
        global __demosDir
        if (__demosDir is None):
            __demosDir = _getSystemDir(kind)
        return __demosDir
    return None


# NOTE: We don't set this at startup because wxStandardPaths needs a running
# application object. This makes sure the wxApp will always be created when
# we get the folder.

def get_user_data_path():
    if apputils.is_windows():
        try:
            import ctypes.wintypes
            CSIDL_APPDATA = 26
            SHGFP_TYPE_CURRENT = 0
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(
                0, CSIDL_APPDATA, 0, SHGFP_TYPE_CURRENT, buf
            )
            return os.path.join(buf.value, GetApp().GetAppName())
        except:
            app_datapath = os.getenv('APPDATA')
            return os.path.join(app_datapath, GetApp().GetAppName())
    else:
        # wxBug: on *nix, it wants to point to ~/.appname, but
        # so does wxConfig... For now, redirect this to ~/.appbuilder
        # when this is fixed, we'll migrate settings to the correct place
        return os.path.join(os.path.expanduser("~"), ".Noval")

def createSystemDirs():
    if (not os.path.exists(getSystemDir())):
        os.mkdir(getSystemDir())
    if (not os.path.exists(getSystemDir(AG_LOGS_DIR))):
        os.mkdir(getSystemDir(AG_LOGS_DIR))
    if (not os.path.exists(getSystemDir(AG_DEMOS_DIR))):
        os.mkdir(getSystemDir(AG_DEMOS_DIR))

def get_app_image_location():
    app_image_path = os.path.join(apputils.mainModuleDir, "noval", "bmp_source")
    return app_image_path
    
def get_app_data_location():
    app_data_path = os.path.join(apputils.mainModuleDir, "noval", "data")
    return app_data_path
    
def get_app_path():
    return apputils.mainModuleDir
    
def get_user_plugin_path():
    return os.path.join(get_user_data_path(),PLUGIN_DIR_NAME)

def get_sys_plugin_path():
    return os.path.join(get_app_path(),PLUGIN_DIR_NAME)
    
def get_cache_path():
    user_data_path = get_user_data_path()
    cache_path = os.path.join(user_data_path,"cache")
    return cache_path
    
def get_home_dir():
    '''
        获取用户的主目录
    '''
    if apputils.is_windows():
        try:
            from win32com.shell import shell, shellcon
            path = shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0)
        except:
            homedrive = asString(os.getenv("HOMEDRIVE"))
            homepath = os.getenv("HOMEPATH")
            path = os.path.join(homedrive, homepath)
        finally:
            return path
    else:
        return os.path.expanduser("~")
