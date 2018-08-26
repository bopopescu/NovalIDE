import wx


def GetLogger():
    pass

def GetOpenView(file_path):
    foundView = None
    openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
    for openDoc in openDocs:
        if openDoc.GetFilename() == file_path:
            foundView = openDoc.GetFirstView()
            break
    return foundView



