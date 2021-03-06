#-------------------------------------------------------------------------------
# Name:        apputils.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-08
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp
import sys
import os
import time
import pyperclip
import psutil
import locale
import future.utils

MAINMODULE_DIR = "NOVAL_MAINMODULE_DIR"

#是否开发版本,在正式版本发行时需要设置为False,在内测版本时需要设置为True
isDev = False

def is_dev():
    return isDev

def is_windows():
    return os.name == 'nt'
    
def is_linux():
    return os.name == "posix"
    
def is_py2():
    return future.utils.PY2

def is_py3():
    return future.utils.PY3
    
def is_py3_plus():
    return sys.version_info[0] >= 3

def get_default_encoding():
    try:
        return locale.getpreferredencoding()
    except:
        return locale.getdefaultlocale()[1]
        
def get_default_locale():
    return locale.getdefaultlocale()[0] 
    
def _generateMainModuleDir():
    mainModuleDir = os.getenv(MAINMODULE_DIR)
    if mainModuleDir:  # if environment variable set, return it
        if is_windows():
            if is_py2():
                return mainModuleDir.decode(get_default_encoding())
        return mainModuleDir
    
    # On Mac, the python executable sometimes has a capital "P" so we need to 
    # lower the string first
    sysExecLower = sys.executable.lower()
    if sysExecLower == "/" or sysExecLower.find('python') != -1:
        utilModuleDir = os.path.dirname(__file__)
        if not os.path.isabs(utilModuleDir):
            utilModuleDir = os.path.join(os.getcwd(), utilModuleDir)
        mainModuleDir = os.path.normpath(os.path.join(utilModuleDir, os.path.join(os.path.pardir, os.path.pardir)))
        if mainModuleDir.endswith('.zip'):
            mainModuleDir = os.path.dirname(mainModuleDir) # Get rid of library.zip
    else:
        mainModuleDir = os.path.dirname(sys.executable)
        
    os.environ[MAINMODULE_DIR] = mainModuleDir  # pythonBug: os.putenv doesn't work, set environment variable
    if is_windows():
        if is_py2():
            return mainModuleDir.decode(get_default_encoding())
    return mainModuleDir

mainModuleDir = _generateMainModuleDir()

def getCommandNameForExecPath(execPath):
    if isWindows():
        return '"%s"' % execPath
    return execPath

def getUserName():
    if isWindows():
        return os.getenv('USERNAME')
    else:
        # 06-Feb-06 stoens@activegrid.com --
        # this blows up the linux cc runs with "Inappropriate ioctl for device"
        #return os.getlogin()
        return os.getenv('USER')        

def getCurrentTimeAsFloat():
    return time.time()

systemStartTime = getCurrentTimeAsFloat()

def CopyToClipboard(str):
    if is_windows():
        pyperclip.copy(str)
    else:
        GetApp().clipboard_clear()
        GetApp().clipboard_append(str)

def GetSupportableExtList():
    exts = []
    for template in GetApp().GetDocumentManager().GetTemplates():
        filter = template.GetFileFilter()
        parts = filter.split(";")
        for part in parts:
            ext = part.replace("*.","").strip()
            exts.append(ext)
    return exts

def is_ext_supportable(ext):
    if ext == "":
        return True
    return ext.lower() in GetSupportableExtList()
    
def get_app_version():
    # find version number from version.txt
    versionFilepath = os.path.join(mainModuleDir, "version.txt")
    if os.path.exists(versionFilepath):
        versionfile = open(versionFilepath, 'r')
        versionLines = versionfile.readlines()
        versionfile.close()
        version = "".join(versionLines)
    else:
        version = "Version Unknown - %s not found" % versionFilepath
    return version
        
if is_py2():
    from ConfigParser import ConfigParser
elif is_py3_plus():
    from configparser import ConfigParser

def get_lang_config():
    return int(get_config_value('IDE','Language',default_value=-1))
    
def get_config_path():
    return os.path.join(mainModuleDir,"config.ini")
    
def get_config_value(section,key,default_value=None):
    '''
        读取配置文件的属性值
    '''
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return default_value

    cfg = ConfigParser()
    cfg.read(config_path)
    if not cfg.has_option(section,key):
        return default_value
    return cfg.get(section,key)

def write_cofig_value(section,key,value):
    '''
        初始化配置文件的属性值
    '''
    config_path = get_config_path()
    cfg = ConfigParser()
    if os.path.exists(config_path):
        cfg.read(config_path)
    if not cfg.has_section(section):
        cfg.add_section(section)
    if not cfg.has_option(section,key):
        cfg.set(section, key,str(value))
        with open(config_path,"w+") as f:
            cfg.write(f) 
