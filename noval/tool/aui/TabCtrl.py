import wx.lib.agw.aui as aui

class IDEAuiTabCtrl(aui.AuiTabCtrl):
    def OnRightDown(self, event):
        
        self.StopTooltipTimer()

        x, y = event.GetX(), event.GetY()
        wnd = self.TabHitTest(x, y)
        if wnd:
            e = aui.AuiNotebookEvent(aui.wxEVT_COMMAND_AUINOTEBOOK_TAB_RIGHT_DOWN, self.GetId())
            e.SetEventObject(self)
            e.SetSelection(self.GetIdxFromWindow(wnd))
            e.Page = wnd
            e.X =x
            e.Y = y
            self.GetEventHandler().ProcessEvent(e)
        elif not self.ButtonHitTest(x, y):
            e = aui.AuiNotebookEvent(aui.wxEVT_COMMAND_AUINOTEBOOK_BG_RIGHT_DOWN, self.GetId())
            e.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(e)