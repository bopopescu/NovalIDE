# -*- coding: utf-8 -*-
from noval import _
import tkinter as tk
from tkinter import ttk
import noval.ui_base as ui_base
import os
import noval.ttkwidgets.linklabel as linklabel
import noval.ui_common as ui_common
import noval.ui_utils as ui_utils

class SystemEnvironmentVariableDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
        self.dvlc = dataview.DataViewListCtrl(self,size=(350,400))
        self.dvlc.AppendTextColumn(_('Key'), width=150)
        self.dvlc.AppendTextColumn(_('Value'),width=200)
        self.Sizer.Add(self.dvlc, 1, wx.EXPAND)
        self.SetVariables()
        self.Fit()
        
    def SetVariables(self):
        for env in os.environ:
            self.dvlc.AppendItem([env, os.environ[env]])

class EnvironmentPanel(ui_utils.BaseEnvironmentUI):
    def __init__(self,parent):
        ui_utils.BaseEnvironmentUI.__init__(self,parent)        
        row = ttk.Frame(self)
        self.include_chkvar = tk.IntVar(value=True)
        ttk.Checkbutton(row,text=_("Include system environment variable"),variable=self.include_chkvar).pack(fill="x",side=tk.LEFT)
        link_label = linklabel.LinkLabel(row,text=_("View"),link="https://github.com/RedFantom/ttkwidgets",\
                                         normal_color='royal blue',hover_color='blue',clicked_color='purple')
        link_label.pack(fill="x",side=tk.LEFT)
        row.pack(fill="x")
        self.interpreter = None
        self.UpdateUI()
        
    def checkInclude(self,event):
        if self.interpreter is None:
            return
        include_system_environ = self._includeCheckBox.GetValue()
        self.interpreter.Environ.IncludeSystemEnviron = include_system_environ
        
    def SetVariables(self,interpreter):
        self.interpreter = interpreter
        self.listview._clear_tree()
        if self.interpreter is not None:
            for env in self.interpreter.Environ:
                self.listview.tree.insert("",0,values=(env,self.interpreter.Environ[env]))
        self.UpdateUI()
        
    def OnGotoLink(self):
        dlg = SystemEnvironmentVariableDialog(self,-1,_("System Environment Variable"))
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()
        
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
        for item in self.listview.tree.get_children():
            value = self.listview.tree.item(item)['values']
            #存储值会把数字字符串自动转换成整形,这里需要转换成字符串类型
            dct[value[0]] = str(value[1])
        return dct