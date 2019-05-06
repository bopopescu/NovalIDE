from noval import _
import tkinter as tk
from tkinter import ttk
import noval.ui_base as ui_base
import os
import noval.ttkwidgets.linklabel as linklabel

class SystemEnvironmentVariableDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,dlg_id,title):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        self.Sizer = wx.BoxSizer()
        self.dvlc = dataview.DataViewListCtrl(self,size=(350,400))
        self.dvlc.AppendTextColumn(_('Key'), width=150)
        self.dvlc.AppendTextColumn(_('Value'),width=200)
        self.Sizer.Add(self.dvlc, 1, wx.EXPAND)
        self.SetVariables()
        self.Fit()
        
    def SetVariables(self):
        for env in os.environ:
            self.dvlc.AppendItem([env, os.environ[env]])

class EnvironmentPanel(ttk.Frame):
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        
        ttk.Label(self, text=_("Set user defined environment variable:"))
        columns = [_('Key'),_('Value')]
        self.listview = ui_base.TreeFrame(self,columns=columns)
        self.new_btn = ttk.Button(self, text=_("New.."),command=self.NewVariable)
        self.edit_btn = ttk.Button(self, text=_("Edit"),command=self.EditVariable)
        self.remove_btn = ttk.Button(self,text=_("Remove..."),command=self.RemoveVariable)
        self.include_chkvar = tk.IntVar(value=True)
        includeCheckBox = ttk.Checkbutton(self,text=_("Include system environment variable"),variable=self.include_chkvar)
        link_label = linklabel.LinkLabel(self,text=_("View"),link="https://github.com/RedFantom/ttkwidgets",\
                                         normal_color='royal blue',hover_color='blue',clicked_color='purple')
        self.interpreter = None
       ### self.UpdateUI(None)
        
    def checkInclude(self,event):
        if self.interpreter is None:
            return
        include_system_environ = self._includeCheckBox.GetValue()
        self.interpreter.Environ.IncludeSystemEnviron = include_system_environ
        
    def UpdateUI(self,event):
        selections = self.listview.tree.selection()
        if selections == []:
            self.remove_btn["state"] = tk.DISABLED
            self.edit_btn["state"] = tk.DISABLED
        else:
            self.remove_btn["state"] = "normal"
            self.edit_btn["state"] = "normal"
        if self.interpreter is None:
            self.edit_btn["state"] = tk.DISABLED
        else:
            self.new_btn["state"] = "normal"
            
    def SetVariables(self,interpreter):
        self.interpreter = interpreter
        self.listview._clear_tree()
        if self.interpreter is not None:
            for env in self.interpreter.Environ:
                self.listview.tree.insert("",0,values=(env,self.interpreter.Environ[env]))
        self.UpdateUI(None)
            
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
        
    def OnGotoLink(self,event):
        dlg = SystemEnvironmentVariableDialog(self,-1,_("System Environment Variable"))
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()
    
    def CheckKeyExist(self,key):
        for row in range(self.dvlc.GetStore().GetCount()):
            if self.dvlc.GetTextValue(row,0) == key:
                return True
        return False
        
    def GetEnviron(self):
        dct = self.GetEnvironValues()
        is_environ_changed = self.IsEnvironChanged(dct)
        if is_environ_changed:
            self.interpreter.Environ.SetEnviron(dct)
        return is_environ_changed
        
    def IsEnvironChanged(self,dct):
        if self.interpreter is None:
            return False
        if len(dct) != self.interpreter.Environ.GetCount():
            return True
        for name in dct:
            if not self.interpreter.Environ.Exist(name):
                return True
            elif dct[name] != self.interpreter.Environ[name]:
                return True
        return False
        
    def CheckEnviron(self):
        return self.IsEnvironChanged(self.GetEnvironValues())

    def GetEnvironValues(self):
        dct = {}
        for row in range(self.dvlc.GetStore().GetCount()):
            dct[self.dvlc.GetTextValue(row,0)] = self.dvlc.GetTextValue(row,1)
        return dct