import wx
from noval.tool.consts import SPACE,HALF_SPACE,_
import wx.dataview as dataview
import noval.tool.interpreter.EnvironmentVariableDialog as EnvironmentVariableDialog

class BaseEnvironmentUI:
    """description of class"""

    def InitUI(self):
    
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        line_sizer.Add(wx.StaticText(self, label=_("Environment variables to set:")),0, wx.ALL|wx.EXPAND, 0)
        box_sizer.Add(line_sizer, 0, wx.TOP,HALF_SPACE)
        
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.dvlc = dataview.DataViewListCtrl(self,size=(-1,230))
        self.dvlc.AppendTextColumn(_('Key'), width=100)
        self.dvlc.AppendTextColumn(_('Value'),width=300)
        dataview.EVT_DATAVIEW_SELECTION_CHANGED(self.dvlc, -1, self.UpdateUI)
        line_sizer.Add(self.dvlc, 1, wx.ALL|wx.EXPAND,0)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.new_btn = wx.Button(self, -1, _("New.."))
        wx.EVT_BUTTON(self.new_btn, -1, self.NewVariable)
        right_sizer.Add(self.new_btn, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND|wx.RIGHT, HALF_SPACE)
        
        self.edit_btn = wx.Button(self, -1, _("Edit"))
        wx.EVT_BUTTON(self.edit_btn, -1, self.EditVariable)
        right_sizer.Add(self.edit_btn, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND|wx.RIGHT, HALF_SPACE)
        
        self.remove_btn = wx.Button(self, -1, _("Remove..."))
        wx.EVT_BUTTON(self.remove_btn, -1, self.RemoveVariable)
        right_sizer.Add(self.remove_btn, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND|wx.RIGHT, HALF_SPACE)
        
        line_sizer.Add(right_sizer, 0,flag=wx.ALL|wx.EXPAND)
        box_sizer.Add(line_sizer, 1, flag=wx.ALL|wx.EXPAND)
        self.SetSizer(box_sizer)
        
    def UpdateUI(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            self.remove_btn.Enable(False)
            self.edit_btn.Enable(False)
        else:
            self.remove_btn.Enable(True)
            self.edit_btn.Enable(True)
            

    def RemoveVariable(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        self.RemoveRowVariable(index)
        self.UpdateUI(None)
        
    def RemoveRowVariable(self,row):
        key = self.dvlc.GetTextValue(row,0)
        ##self.interpreter.environments = filter(lambda e:not e.has_key(key),self.interpreter.environments)
        self.dvlc.DeleteItem(row)
        
    def GetVariableRow(self,key):
        count = self.dvlc.GetStore().GetCount()
        for i in range(count):
            if self.dvlc.GetTextValue(i,0) == key:
                return i
        return -1
        
    def AddVariable(self,key,value):
        if self.CheckKeyExist(key):
            ret = wx.MessageBox(_("Key name has already exist in environment variable,Do you wann't to overwrite it?"),_("Warning"),wx.YES_NO|wx.ICON_QUESTION,self)
            if ret == wx.YES:
                row = self.GetVariableRow(key)
                assert(row != -1)
                self.RemoveRowVariable(row)
            else:
                return
        self.dvlc.AppendItem([key, value])
        
    def NewVariable(self,event):
        dlg = EnvironmentVariableDialog.EnvironmentVariableDialog(self,-1,_("New Environment Variable"))
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        key = dlg.key_ctrl.GetValue().strip()
        value = dlg.value_ctrl.GetValue().strip()
        if status == wx.ID_OK and key and value:
            self.AddVariable(key,value)
        self.UpdateUI(None)
        dlg.Destroy()
        
    def EditVariable(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        dlg = EnvironmentVariableDialog.EnvironmentVariableDialog(self,-1,_("Edit Environment Variable"))
        dlg.CenterOnParent()
        old_key = self.dvlc.GetTextValue(index,0)
        dlg.key_ctrl.SetValue(old_key)
        dlg.value_ctrl.SetValue(self.dvlc.GetTextValue(index,1))
        status = dlg.ShowModal()
        key = dlg.key_ctrl.GetValue().strip()
        value = dlg.value_ctrl.GetValue().strip()
        if status == wx.ID_OK and key and value:
            self.dvlc.SetTextValue(key,index,0)
            self.dvlc.SetTextValue(value,index,1)
        self.UpdateUI(None)
        dlg.Destroy()
    
    def CheckKeyExist(self,key):
        for row in range(self.dvlc.GetStore().GetCount()):
            if self.dvlc.GetTextValue(row,0) == key:
                return True
        return False
        
    def GetEnviron(self):
        dct = {}
        for row in range(self.dvlc.GetStore().GetCount()):
            dct[self.dvlc.GetTextValue(row,0)] = self.dvlc.GetTextValue(row,1)
        return dct