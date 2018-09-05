import wx
from noval.tool.consts import SPACE,HALF_SPACE,_

class NewDocumentDialog(wx.Dialog):
 
    def __init__(self,parent,dlg_id,title,strings,default_selection=-1):
        self.filters = []
        wx.Dialog.__init__(self,parent,dlg_id,title)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        self._selection = default_selection
        if -1 == self._selection:
            self._selection = 0
        
        boxsizer.Add(wx.StaticText(self, -1, _("Select a document type:"), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.ALL,border=SPACE)
        
        self.listbox = wx.ListBox(self,-1,size=(-1,200),choices=strings)
        wx.EVT_LISTBOX_DCLICK(self.listbox, self.listbox.GetId(), self.OnOKClick)
        boxsizer.Add(self.listbox,0,flag = wx.EXPAND|wx.LEFT|wx.RIGHT,border = SPACE)
        self.listbox.SetSelection(default_selection)
        boxsizer.Add(wx.StaticLine(self,-1),1,flag = wx.LEFT|wx.EXPAND|wx.TOP|wx.RIGHT,border = SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.BOTTOM|wx.TOP,SPACE)
        self.SetSizer(boxsizer)
        self.Fit()
        
    def OnOKClick(self,event):
        if self.listbox.GetSelection() == -1:
            wx.MessageBox(_("Please choose one new document type"))
            return
        self.EndModal(wx.ID_OK)


def GetNewDocumentChoiceIndex(parent,strings,default_selection):
    
    dlg = NewDocumentDialog(parent,-1,_("New Document"),
                                      strings,default_selection)
    dlg.CenterOnParent()
    if wx.ID_OK == dlg.ShowModal():
        sel = dlg.listbox.GetSelection()
        return sel
    return -1
    
