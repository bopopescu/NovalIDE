# -*- coding: utf-8 -*-
import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import noval.util.WxThreadSafe as WxThreadSafe
import wx.dataview as dataview
import noval.tool.interpreter.InterpreterManager as interpretermanager
import os
import subprocess
import noval.tool.OutputThread as OutputThread
import threading
import noval.util.strutils as strutils
import noval.util.sysutils as sysutils
import noval.util.utils as utils
import time
from urlparse import urlparse

class ManagePackagesDialog(wx.Dialog):
    
    MANAGE_INSTALL_PACKAGE = 1
    MANAGE_UNINSTALL_PACKAGE = 2
    
    SOURCE_LIST = [
        "https://pypi.org/simple",
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        "http://mirrors.aliyun.com/pypi/simple",
        "https://pypi.mirrors.ustc.edu.cn/simple",
        "http://pypi.hustunique.com",
        "http://pypi.sdutlinux.org",
        "http://pypi.douban.com/simple"
    ]
    
    BEST_PIP_SOURCE = None
        
    def __init__(self,parent,dlg_id,title,manage_action,interpreter,interpreters,package_name=''):
        self.interpreter = interpreter
        self.interpreters = interpreters
        self._manage_action = manage_action
        
        self.SOURCE_NAME_LIST = [
            _('Default Source'),
            _('Tsinghua'),
            _('Aliyun'),
            _('USTC'),
            _('HUST'),
            _('SDUT'),
            _('Douban'),
        ]
        wx.Dialog.__init__(self,parent,dlg_id,title,size=(-1,-1))
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        

        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            lineSizer.Add(wx.StaticText(self, -1, _("We will use the pip source:")), 0, \
                              wx.ALIGN_CENTER, SPACE)
            self._pipSourceCombo = wx.ComboBox(self, -1,choices=self.SOURCE_NAME_LIST,value=self.SOURCE_NAME_LIST[0], \
                                               size=(200,-1),style = wx.CB_READONLY)
            lineSizer.Add(self._pipSourceCombo,1, wx.EXPAND|wx.LEFT, SPACE)
            
            self.check_source_btn = wx.Button(self, -1, _("Check the best source"))
            wx.EVT_BUTTON(self.check_source_btn, -1, self.CheckTheBestSource)
            lineSizer.Add(self.check_source_btn, 0,flag=wx.LEFT, border=SPACE) 
            
            box_sizer.Add(lineSizer, 0,wx.EXPAND| wx.LEFT|wx.TOP|wx.RIGHT, SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            lineSizer.Add(wx.StaticText(self, -1, _("We will download and install it in the interpreter:")), 0, \
                          wx.ALIGN_CENTER | wx.LEFT, SPACE)
        else:
            lineSizer.Add(wx.StaticText(self, -1, _("We will uninstall it in the interpreter:")), 0, \
                          wx.ALIGN_CENTER | wx.LEFT, SPACE)
        names = self.GetNames()
        self._interpreterCombo = wx.ComboBox(self, -1,choices=names,value=self.interpreter.Name, style = wx.CB_READONLY)
        lineSizer.Add(self._interpreterCombo,0, wx.EXPAND|wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0,wx.EXPAND| wx.RIGHT|wx.TOP, SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            lineSizer.Add(wx.StaticText(self, -1, _("Type the name of package to install:")), 0, wx.ALIGN_CENTER|wx.LEFT, SPACE)
        else:
            lineSizer.Add(wx.StaticText(self, -1, _("Type the name of package to uninstall:")), 0, wx.ALIGN_CENTER|wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0,wx.EXPAND| wx.TOP, SPACE)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.value_ctrl = wx.TextCtrl(self, -1, "",size=(-1,-1))
        lineSizer.Add(self.value_ctrl, 1, wx.LEFT|wx.EXPAND, SPACE)
        if self._manage_action == ManagePackagesDialog.MANAGE_UNINSTALL_PACKAGE:
            self.value_ctrl.SetValue(package_name)
        self.browser_btn = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(self.browser_btn, -1, self.BrowsePath)
        lineSizer.Add(self.browser_btn, 0,flag=wx.LEFT, border=SPACE) 
        box_sizer.Add(lineSizer, 0, flag=wx.RIGHT|wx.TOP|wx.EXPAND, border=SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            lineSizer.Add(wx.StaticText(self, -1, _("To install the specific version,type \"xxx==1.0.1\"\nTo install more packages,please specific the path of requirements.txt")), \
                          0, wx.ALIGN_CENTER | wx.LEFT, SPACE)
            
        else:
            lineSizer.Add(wx.StaticText(self, -1, _("To uninstall more packages,please specific the path of requirements.txt")), \
                          0, wx.ALIGN_CENTER | wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0, wx.RIGHT|wx.TOP|wx.EXPAND, SPACE)
        
        self.detailSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.output_ctrl = wx.TextCtrl(self, -1, "", style = wx.TE_MULTILINE|wx.TE_READONLY,size=(-1,250))
      ###  self.output_ctrl.Enable(False)
        self.detailSizer.Add(self.output_ctrl, 1, wx.LEFT, SPACE)
        box_sizer.Add(self.detailSizer, 0, wx.RIGHT|wx.TOP|wx.EXPAND, SPACE)
        box_sizer.Hide(self.detailSizer)
        
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detail_btn = wx.Button(self, -1, _("Show Details") + "↓")
        self._show_details = False
        wx.EVT_BUTTON(self.detail_btn, -1, self.ShowHideDetails)
        bsizer.Add(self.detail_btn, 0,flag=wx.LEFT, border=SPACE) 
        
        bsizer.Add(wx.StaticText(self, -1, ""), 1, wx.LEFT|wx.EXPAND, 0)
        
        self.ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        #set ok button default focused
        self.ok_btn.SetDefault()
        wx.EVT_BUTTON(self.ok_btn, -1, self.OnOKClick)
        bsizer.Add(self.ok_btn, 0,flag=wx.RIGHT, border=SPACE) 
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.Add(cancel_btn, 0,flag=wx.RIGHT, border=SPACE) 
        
        box_sizer.Add(bsizer, 0, wx.EXPAND |wx.BOTTOM|wx.TOP,SPACE)
        
        self.SetSizer(box_sizer)
        self.Fit()
        self._install_with_name = True
        
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            if self.BEST_PIP_SOURCE is None:
                self.CheckBestPipSource()
            else:
                self.SelectBestPipSource()
        
    def ShowHideDetails(self,event):
        if self._show_details:
            self.detail_btn.SetLabel( _("Show Details") + "↓")
            self.GetSizer().Hide(self.detailSizer)
            self._show_details = False 
        else:  
            self.GetSizer().Show(self.detailSizer)  
            self.detail_btn.SetLabel( _("Hide Details") + "↑") 
            self._show_details = True   
        self.GetSizer().Layout()
        self.Fit()
        
    def BrowsePath(self,event):
        descr = _("Text File (*.txt)|*.txt")
        title = _("Choose requirements.txt")
        dlg = wx.FileDialog(self,title ,
                       wildcard = descr,
                       style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        dlg.Destroy()
        self.value_ctrl.SetValue(path)
        
    def ExecCommandAndOutput(self,command,dlg):
        #shell must be True on linux
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout_thread = OutputThread.OutputThread(p.stdout,p,dlg,call_after=True)
        stdout_thread.start()
        stderr_thread = OutputThread.OutputThread(p.stderr,p,dlg,call_after=True)
        stderr_thread.start()
        p.wait()
        self.EndDialog(p.returncode)
    
    @WxThreadSafe.call_after
    def EndDialog(self,retcode):
        package_name = self.value_ctrl.GetValue().strip()
        if package_name.find(" ") != -1 or package_name.find("==") != -1 or package_name.find("-U") != -1:
            self._install_with_name = False
        python_package = self.interpreter.GetInstallPackage(package_name)
        ret_suc = False
        if retcode == 0:
            if self._manage_action == self.MANAGE_INSTALL_PACKAGE and python_package:
                self.GetParent().AddPackage(python_package,self.interpreter,True)
                wx.MessageBox(_("Install Success"))
                ret_suc = True
            elif self._manage_action == self.MANAGE_UNINSTALL_PACKAGE and not python_package and self._install_with_name:
                self.GetParent().RemovePackage(package_name,self.interpreter)
                wx.MessageBox(_("Uninstall Success"))
                ret_suc = True
            elif self._manage_action == self.MANAGE_INSTALL_PACKAGE and not self._install_with_name:
                self.interpreter.LoadPackages(self.GetParent(),True)
                wx.MessageBox(_("Install Success"))
                ret_suc = True
            elif self._manage_action == self.MANAGE_UNINSTALL_PACKAGE and not self._install_with_name:
                self.interpreter.LoadPackages(self.GetParent(),True)
                wx.MessageBox(_("Uninstall Success"))
                ret_suc = True
        if ret_suc:
            self.EndModal(wx.ID_OK)
        else:
            if self._manage_action == self.MANAGE_INSTALL_PACKAGE:
                wx.MessageBox(_("Install Fail"),style=wx.OK|wx.ICON_ERROR)
            elif self._manage_action == self.MANAGE_UNINSTALL_PACKAGE:
                wx.MessageBox(_("Uninstall Fail"),style=wx.OK|wx.ICON_ERROR)
            self.value_ctrl.Enable(True)
            self.ok_btn.Enable(True)
        
    def InstallPackage(self,interpreter):
        should_root = False
        if not sysutils.isWindows():
            should_root = not interpreter.IsPythonlibWritable()
        package_name = self.value_ctrl.GetValue().strip()
        if os.path.basename(package_name) == "requirements.txt":
            self._install_with_name = False
            if not sysutils.isWindows() and should_root:
                command = "pkexec " + strutils.emphasis_path(interpreter.GetPipPath()) + " install -r %s" % (package_name)
            else:
                command = strutils.emphasis_path(interpreter.GetPipPath()) + " install -r %s" % (package_name)
        else:
            if not sysutils.isWindows() and should_root:
                command = "pkexec " + strutils.emphasis_path(interpreter.GetPipPath()) + " install %s" % (package_name)
            else:
                command = strutils.emphasis_path(interpreter.GetPipPath()) + " install %s" % (package_name)
                
        if self.SOURCE_NAME_LIST[self._pipSourceCombo.GetSelection()] != self.SOURCE_NAME_LIST[0]:
            command += " -i " + self.SOURCE_LIST[self._pipSourceCombo.GetSelection()]
            parts = urlparse(self.SOURCE_LIST[self._pipSourceCombo.GetSelection()])
            host = parts.netloc
            command += " --trusted-host " + host
            
        self.output_ctrl.write(command + os.linesep)
        self.call_back = self.output_ctrl.write
        t = threading.Thread(target=self.ExecCommandAndOutput,args=(command,self))
        t.start()
        
    def UninstallPackage(self,interpreter):
        should_root = False
        if not sysutils.isWindows():
            should_root = not interpreter.IsPythonlibWritable()
        package_name = self.value_ctrl.GetValue().strip()
        if os.path.basename(package_name) == "requirements.txt":
            self._install_with_name = False
            if not sysutils.isWindows() and should_root:
                command = "pkexec " + strutils.emphasis_path(interpreter.GetPipPath()) + " uninstall -y -r %s" % (package_name)
            else:
                command = strutils.emphasis_path(interpreter.GetPipPath()) + " uninstall -y -r %s" % (package_name)
        else:
            if not sysutils.isWindows() and should_root:
                command = "pkexec " + strutils.emphasis_path(interpreter.GetPipPath()) + " uninstall -y %s" % (package_name)
            else:
                command = strutils.emphasis_path(interpreter.GetPipPath()) + " uninstall -y %s" % (package_name)
        self.output_ctrl.write(command + os.linesep)
        self.call_back = self.output_ctrl.write
        t = threading.Thread(target=self.ExecCommandAndOutput,args=(command,self))
        t.start()
        
    def OnOKClick(self, event):
        if self.value_ctrl.GetValue().strip() == "":
            wx.MessageBox(_("package name is empty"))
            return
        sel = self._interpreterCombo.GetSelection()
        self.interpreter = self.interpreters[sel]
        if self.interpreter.IsBuiltIn or self.interpreter.GetPipPath() is None:
            wx.MessageBox(_("Could not find pip on the path"),style=wx.OK|wx.ICON_ERROR)
            return
        self.value_ctrl.Enable(False)
        self.ok_btn.Enable(False)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            self.InstallPackage(self.interpreter)
        else:
            self.UninstallPackage(self.interpreter)
            
    def GetNames(self):
        names = []
        for interpreter in self.interpreters:
            names.append(interpreter.Name)
        return names
        
    def CheckBestPipSource(self):
        t = threading.Thread(target=self.GetBestPipSource)
        t.start()
        
    def GetBestPipSource(self):
        self.EnableCheckSourcButton(False)
        sort_pip_source_dct = {}
        for i,pip_source_name in enumerate(self.SOURCE_NAME_LIST):
            pip_source = self.SOURCE_LIST[i]
            api_addr = pip_source + "/ok"
            start = time.time()
            if utils.RequestData(api_addr,timeout=10,to_json=False):
                end = time.time()
                elapse = end - start
                sort_pip_source_dct[pip_source] = elapse
                utils.GetLogger().debug("response time of pip source %s is %.2fs",pip_source,elapse)
                
        if len(sort_pip_source_dct) == 0:
            return
                
        best_source,elapse = sorted(sort_pip_source_dct.items(),key = lambda x:x[1],reverse = False)[0]
        utils.GetLogger().info("the best pip source is %s,response time is %.2fs",best_source,elapse)
        ManagePackagesDialog.BEST_PIP_SOURCE = best_source
        self.SelectBestPipSource()
        self.EnableCheckSourcButton(True)
        
    @WxThreadSafe.call_after
    def SelectBestPipSource(self):
        for i in range(self._pipSourceCombo.GetCount()):
            if self._pipSourceCombo.GetString(i).find(_("The Best Source")) != -1:
                self._pipSourceCombo.Delete(i)
                self._pipSourceCombo.Insert(self.SOURCE_NAME_LIST[i],i)
                break
        for i,pip_source in enumerate(self.SOURCE_LIST):
            if pip_source == self.BEST_PIP_SOURCE:
                best_source_name = self.SOURCE_NAME_LIST[i] + "(" + _("The Best Source") + ")"
                self._pipSourceCombo.Delete(i)
                self._pipSourceCombo.Insert(best_source_name,i)
                self._pipSourceCombo.Select(i)
                break

    def CheckTheBestSource(self,event):
        self.CheckBestPipSource()

    @WxThreadSafe.call_after
    def EnableCheckSourcButton(self,enable=True):
        if enable:
            self.check_source_btn.Enable(True)
            self.check_source_btn.SetLabel(_("Check the best source"))
        else:
            self.check_source_btn.SetLabel(_("Checking the best source"))
            self.check_source_btn.Enable(False)
        
class PackagePanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.Sizer = wx.BoxSizer()
        self.dvlc = dataview.DataViewListCtrl(self)
        self.dvlc.AppendTextColumn(_('Name'), width=200)
        self.dvlc.AppendTextColumn(_('Version'),width=210)
        self.Sizer.Add(self.dvlc, 1, wx.EXPAND)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.install_btn = wx.Button(self, -1, _("Install with pip"))
        wx.EVT_BUTTON(self.install_btn, -1, self.InstallPip)
        right_sizer.Add(self.install_btn, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND|wx.RIGHT, HALF_SPACE)
        
        self.uninstall_btn = wx.Button(self, -1, _("Uninstall with pip"))
        wx.EVT_BUTTON(self.uninstall_btn, -1, self.UninstallPip)
        right_sizer.Add(self.uninstall_btn, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND|wx.RIGHT, HALF_SPACE)
        
        self.freeze_btn = wx.Button(self, -1, _("Freeze"))
        wx.EVT_BUTTON(self.freeze_btn, -1, self.FreezePackage)
        right_sizer.Add(self.freeze_btn, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND|wx.RIGHT, HALF_SPACE)
        
        self.Sizer.Add(right_sizer, 0, wx.TOP, SPACE)
        self.interpreter = None

    def InstallPip(self,event):
        dlg = ManagePackagesDialog(self,-1,_("Install Package"),ManagePackagesDialog.MANAGE_INSTALL_PACKAGE,self.interpreter,self.GetParent().GetParent()._interpreters)
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        if status == wx.ID_OK:
            self.NotifyPackageConfigurationChange()
        dlg.Destroy()
        
        
    def UninstallPip(self,event):
        index = self.dvlc.GetSelectedRow()
        package_name = ""
        if index != wx.NOT_FOUND:
            package_name = self.dvlc.GetTextValue(index,0)
        dlg = ManagePackagesDialog(self,-1,_("Uninstall Package"),ManagePackagesDialog.MANAGE_UNINSTALL_PACKAGE,self.interpreter,self.GetParent().GetParent()._interpreters,package_name=package_name)
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        if status == wx.ID_OK:
            self.NotifyPackageConfigurationChange()
        dlg.Destroy()
        
    def LoadPackages(self,interpreter,force=False):
        self.interpreter = interpreter
        if self.interpreter is None or self.interpreter.IsBuiltIn or self.interpreter.GetPipPath() is None:
            self.install_btn.Enable(False)
            self.uninstall_btn.Enable(False)
            self.freeze_btn.Enable(False)
        else:
            self.install_btn.Enable(True)
            self.uninstall_btn.Enable(True)
            self.freeze_btn.Enable(True)
        self.dvlc.DeleteAllItems()
        if self.interpreter is not None:
            utils.GetLogger().debug("load interpreter %s package" % self.interpreter.Name)
            self.interpreter.LoadPackages(self,force)
            if self.interpreter.IsLoadingPackage:
                self.dvlc.AppendItem([_("Loading Package List....."),""])
                return
            self.LoadPackageList(self.interpreter)
            
    def LoadPackageList(self,interpreter):
        for name in interpreter.Packages:
            self.AddPackage(interpreter.Packages[name])
        utils.GetLogger().debug("load interpreter %s package end" % self.interpreter.Name)
            
    @WxThreadSafe.call_after
    def LoadPackageEnd(self,interpreter):
        if self.interpreter != interpreter:
            utils.GetLogger().debug("interpreter %s is not panel current interprter,current interpreter is %s" , interpreter.Name,self.interpreter.Name)
            return
        self.dvlc.Freeze()
        self.dvlc.DeleteAllItems()
        self.LoadPackageList(interpreter)
        self.dvlc.Thaw()
        
    def AddPackage(self,python_package,interpreter=None,remove_exist=False):
        if remove_exist:
            utils.GetLogger().info("package name %s version %s already exist,remove package first!",python_package.Name,python_package.Version)
            self.RemovePackage(python_package.Name,interpreter)
        self.dvlc.AppendItem([python_package.Name,python_package.Version])
        if interpreter is not None:
            interpreter.Packages[python_package.Name] = python_package
        
    def RemovePackage(self,name,interpreter):
        row,package_name = self.GetPackageRow(name)
        if row == -1:
            return
        self.dvlc.DeleteItem(row)
        del interpreter.Packages[package_name]
        
    def GetPackageRow(self,package_name):
        count = self.dvlc.GetStore().GetCount()
        for i in range(count):
            column_value = self.dvlc.GetTextValue(i,0)
            if column_value.lower() == package_name.lower():
                return i,column_value
        return -1,""
        
    def NotifyPackageConfigurationChange(self):
        self.GetParent().GetParent().NotifyConfigurationChange()
        
    def FreezePackage(self,event):
        text_docTemplate = wx.GetApp().GetDocumentManager().FindTemplateForPath("test.txt")
        descr = _(text_docTemplate.GetDescription()) + " (" + text_docTemplate.GetFileFilter() + ") |" + text_docTemplate.GetFileFilter()
        default_ext = text_docTemplate.GetDefaultExtension()
        filename = wx.FileSelector(_("Save As"),
                                   text_docTemplate.GetDirectory(),
                                   "requirements.txt",
                                   default_ext,
                                   wildcard = descr,
                                   flags = wx.SAVE | wx.OVERWRITE_PROMPT,
                                   parent = self.GetParent())
        if filename == "":
            return
        try:
            with open(filename,"wb") as f:
                command = self.interpreter.GetPipPath() + " freeze"
                subprocess.call(command,shell=True,stdout=f,stderr=subprocess.STDOUT)
        except Exception as e:
            wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)