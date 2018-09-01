import wx
from noval.util.logger import app_debugLogger

def GetLogger():
    return app_debugLogger

def GetOpenView(file_path):
    foundView = None
    openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
    for openDoc in openDocs:
        if openDoc.GetFilename() == file_path:
            foundView = openDoc.GetFirstView()
            break
    return foundView
    
def ProfileGet(key,default_value=""):
    return wx.ConfigBase_Get().Read(key, default_value)
    
def ProfileGetInt(key,default_value=-1):
    return wx.ConfigBase_Get().ReadInt(key, default_value)
    
def ProfileSet(key,value):
    if type(value) == int:
        wx.ConfigBase_Get().WriteInt(key,value)
    else:
        wx.ConfigBase_Get().Write(key,value)



