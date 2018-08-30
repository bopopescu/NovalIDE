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



