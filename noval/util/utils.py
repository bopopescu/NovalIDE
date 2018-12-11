import wx
from noval.util.logger import app_debugLogger
import noval.util.sysutils as sysutilslib
import WxThreadSafe
from appdirs import *
import logging
import requests

def GetLogger(logger_name = ""):
    if logger_name == "" or logger_name == "root":
        return app_debugLogger
    return logging.getLogger(logger_name)

def GetOpenView(file_path):
    foundView = None
    openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
    for openDoc in openDocs:
        if openDoc.GetFilename() == file_path:
            foundView = openDoc.GetFirstView()
            break
    return foundView
    
def ProfileGet(key,default_value=""):
    if isinstance(default_value,basestring):
        return wx.ConfigBase_Get().Read(key, default_value)
    else:
        try:
            default_value = ""
            return eval(wx.ConfigBase_Get().Read(key, default_value))
        except:
            return default_value
    
def ProfileGetInt(key,default_value=-1):
    return wx.ConfigBase_Get().ReadInt(key, default_value)
    
def ProfileSet(key,value):
    if type(value) == int:
        wx.ConfigBase_Get().WriteInt(key,value)
    else:
        wx.ConfigBase_Get().Write(key,value)

@WxThreadSafe.call_after
def UpdateStatusBar(msg,number=0):
    wx.GetApp().MainFrame.GetStatusBar().SetStatusText(msg,number)

def GetMainModulePath():
    return sysutilslib.mainModuleDir
    

def GetUserDataPath():
    return getAppDataFolder()
    
def GetUserDataPluginPath():
    return os.path.join(GetUserDataPath(),"plugins")

def GetSystemPluginPath():
    return os.path.join(GetMainModulePath(),"plugins")
    
def GetAppVersion():
    return sysutilslib.GetAppVersion()
    
def GetMainWindow():
    return wx.GetApp().MainFrame
    
def IsWindows():
    return sysutilslib.isWindows()
    
def IsLinux():
    return sysutilslib.isLinux()
    

def RequestData(addr,arg={},method='get',timeout = None,to_json=True):
    '''
    '''
    params = {}
    try:
        if timeout is not None:
            params['timeout'] = timeout
        req = None
        if method == 'get':
            params['params'] = arg
            req = requests.get(addr,**params)
        elif method == 'post':
            req = requests.post(addr,data = arg,**params)
        if not to_json:
            return req.text
        return req.json()
    except Exception as e:
        GetLogger().error('open %s error:%s' ,addr,e)
    return None