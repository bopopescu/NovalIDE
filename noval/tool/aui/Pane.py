import wx.lib.agw.aui as aui

class TabPaneFrame(aui.AuiPaneInfo):
    def __init__(self):
        aui.AuiPaneInfo.__init__(self)
        
    def SetFocus(self):
        self.window.SetFocus()
