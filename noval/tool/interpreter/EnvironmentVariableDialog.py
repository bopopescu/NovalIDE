import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 

class EnvironmentVariableDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Key: ")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.key_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        lineSizer.Add(self.key_ctrl, 0, wx.LEFT|wx.ALIGN_BOTTOM, SPACE)
        contentSizer.Add(lineSizer, 0, wx.ALL, HALF_SPACE)
    
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Value:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.value_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        lineSizer.Add(self.value_ctrl, 0, wx.LEFT, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.ALL, HALF_SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        
        self.SetSizer(contentSizer)
        self.Fit()
