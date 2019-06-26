# -*- coding: utf-8 -*-
from noval import _,GetApp
from tkinter import ttk
from tkinter import messagebox,filedialog
import tkinter as tk
import noval.ui_base as ui_base
import noval.python.interpreter.interpretermanager as interpretermanager
import os
import subprocess
###import noval.OutputThread as OutputThread
import threading
import noval.util.strutils as strutils
import noval.util.apputils as sysutils
import noval.util.utils as utils
import time
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
import noval.consts as consts
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.editor.text as texteditor
import noval.util.urlutils as urlutils
import noval.python.parser.utils as parserutils
import noval.constants as constants

class ManagePackagesDialog(ui_base.CommonModaldialog):
    
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
        
    def __init__(self,parent,title,manage_action,interpreter,interpreters,package_name=''):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
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
        row_no = 0
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            row = ttk.Frame(self.main_frame)
            ttk.Label(row,text=_("We will use the pip source:")).pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
            self._pipSourceCombo = ttk.Combobox(row, values=self.SOURCE_NAME_LIST,state="readonly")
            self._pipSourceCombo.current(0)
            self._pipSourceCombo.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),fill="x",expand=1)
            self.check_source_btn = ttk.Button(row, text= _("Check the best source"),command=self.CheckTheBestSource)
            self.check_source_btn.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
            row.grid(row=row_no,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW,)
            row_no += 1
        row = ttk.Frame(self.main_frame)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            ttk.Label(row,text=_("We will download and install it in the interpreter:")).pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        else:
            ttk.Label(row,text=_("We will uninstall it in the interpreter:")).pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        names = self.GetNames()
        self._interpreterCombo = ttk.Combobox(row,values=names,value=self.interpreter.Name,state="readonly")
        self._interpreterCombo.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),fill="x",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.grid(row=row_no,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW,)
        row_no += 1
        
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            label_1 = ttk.Label(self.main_frame, text=_("Type the name of package to install:"))
        else:
            label_1 = ttk.Label(self.main_frame,text= _("Type the name of package to uninstall:"))
        label_1.grid(row=row_no,column=0,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW)
        row_no += 1
        row = ttk.Frame(self.main_frame)
        self.value_var = tk.StringVar(value=package_name)
        value_ctrl = ttk.Entry(row,textvariable=self.value_var)
        value_ctrl.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),fill="x",expand=1)
        #if self._manage_action == ManagePackagesDialog.MANAGE_UNINSTALL_PACKAGE:
         #   self.value_var.set()
        self.browser_btn = ttk.Button(row, text=_("Browse..."),command=self.BrowsePath)
        self.browser_btn.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.grid(row=row_no,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW)
        row_no += 1
    
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            label_2 = ttk.Label(self.main_frame, text=_("To install the specific version,type \"xxx==1.0.1\"\nTo install more packages,please specific the path of requirements.txt"))
        else:
            label_2 = ttk.Label(self.main_frame, text=_("To uninstall more packages,please specific the path of requirements.txt"))
        label_2.grid(row=row_no,column=0,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW)
        row_no += 1
        
        self.output_ctrl = texteditor.TextCtrl(self.main_frame)
        self.output_ctrl['state'] = tk.DISABLED
        self.detail_output_row = row_no
        self.output_ctrl.grid(row=row_no,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.NSEW)
        row_no += 1
        
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.detail_btn = ttk.Button(self.bottom_frame, text=_("Show Details") + "↓",command=self.ShowHideDetails)
        self.detail_btn.pack(side=tk.LEFT,pady=consts.DEFAUT_CONTRL_PAD_Y,padx=consts.DEFAUT_CONTRL_PAD_X)
        self._show_details = False
        self.AddokcancelButton()
        self.bottom_frame.grid(row=row_no,column=0,sticky=tk.NSEW)
        row_no += 1
        self._install_with_name = True
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            if self.BEST_PIP_SOURCE is None:
                self.CheckBestPipSource()
            else:
                self.SelectBestPipSource()
        self.columnconfigure(0, weight=1)
        self.ShowHideDetails()
                
    def AddokcancelButton(self):
        button_frame = ttk.Frame(self.bottom_frame)
        button_frame.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AppendokcancelButton(button_frame)
        
    def ShowHideDetails(self):
        if not self._show_details:
            self.detail_btn.configure( text=_("Show Details") + "↓")
            self.output_ctrl.grid_forget()
            self._show_details = True 
        else:  
            self.output_ctrl.grid(row=self.detail_output_row,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.NSEW)
            self.detail_btn.configure( text=_("Hide Details") + "↑") 
            self._show_details = False   
        
    def BrowsePath(self):
        descrs = [(_("Text File"),".txt"),]
        title = _("Choose requirements.txt")
        path = filedialog.askopenfilename(master=self,title=title ,
                       filetypes = descrs,
                       initialfile= "requirements.txt"
                       )
        if not path:
            return
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
            if urlutils.RequestData(api_addr,timeout=10,to_json=False):
                end = time.time()
                elapse = end - start
                sort_pip_source_dct[pip_source] = elapse
                utils.get_logger().debug("response time of pip source %s is %.2fs",pip_source,elapse)
                
        if len(sort_pip_source_dct) == 0:
            return
                
        best_source,elapse = sorted(sort_pip_source_dct.items(),key = lambda x:x[1],reverse = False)[0]
        utils.get_logger().info("the best pip source is %s,response time is %.2fs",best_source,elapse)
        ManagePackagesDialog.BEST_PIP_SOURCE = best_source
        self.SelectBestPipSource()
        self.EnableCheckSourcButton(True)
        
    def SelectBestPipSource(self):
        for i in range(self._pipSourceCombo['values']):
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

    def EnableCheckSourcButton(self,enable=True):
        if enable:
            self.check_source_btn['state'] = "normal"
            self.check_source_btn.configure(text=_("Check the best source"))
        else:
            self.check_source_btn.configure(text=_("Checking the best source"))
            self.check_source_btn['state'] = tk.DISABLED
        
class PackagePanel(ttk.Frame):
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        columns = ['Name','Version']
        self.listview = treeviewframe.TreeViewFrame(self,columns=columns,show="headings")
        self.listview.pack(side=tk.LEFT,fill="both",expand=1)
        for column in columns:
            self.listview.tree.heading(column, text=_(column))
        #设置第一列可排序
        self.listview.tree.heading(columns[0], command=lambda:self.treeview_sort_column(columns[0], False))
        right_frame = ttk.Frame(self)
        self.install_btn = ttk.Button(right_frame, text=_("Install with pip"),command=self.InstallPip)
        self.install_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.uninstall_btn = ttk.Button(right_frame, text=_("Uninstall with pip"),command=self.UninstallPip)
        self.uninstall_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.freeze_btn = ttk.Button(right_frame, text=_("Freeze"),command=self.FreezePackage)
        self.freeze_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        right_frame.pack(side=tk.LEFT,fill="y")
        self.interpreter = None
        
    def SortNameAZ(self,l,r):
        return parserutils.py_cmp(l[0].lower(),r[0].lower())
        
    def SortNameZA(self,l,r):
        return parserutils.py_cmp(r[0].lower(),l[0].lower())
        
    def treeview_sort_column(self,col, reverse):
        l = [(self.listview.tree.set(k, col), k) for k in self.listview.tree.get_children('')]
        if reverse:
            #倒序
            l = parserutils.py_sorted(l,self.SortNameZA)
        else:
            l = parserutils.py_sorted(l,self.SortNameAZ)
        #根据排序后索引移动
        for index, (val, k) in enumerate(l):
            self.listview.tree.move(k, '', index)
        #重写标题,使之成为再点倒序的标题
        self.listview.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))

    def InstallPip(self):
        dlg = ManagePackagesDialog(self,_("Install Package"),ManagePackagesDialog.MANAGE_INSTALL_PACKAGE,self.interpreter,self.master.master._interpreters)
        status = dlg.ShowModal()
        if status == constants.ID_OK:
            self.NotifyPackageConfigurationChange()
        
    def UninstallPip(self):
        selections = self.listview.tree.selection()
        package_name = ""
        if selections:
            package_name = self.listview.tree.item(selections[0])['values'][0]
        dlg = ManagePackagesDialog(self,_("Uninstall Package"),ManagePackagesDialog.MANAGE_UNINSTALL_PACKAGE,self.interpreter,self.master.master._interpreters,package_name=package_name)
        status = dlg.ShowModal()
        if status == constants.ID_OK:
            self.NotifyPackageConfigurationChange()
        
    def LoadPackages(self,interpreter,force=False):
        self.interpreter = interpreter
        if self.interpreter is None or self.interpreter.IsBuiltIn or self.interpreter.GetPipPath() is None:
            self.install_btn["state"] = tk.DISABLED
            self.uninstall_btn["state"] = tk.DISABLED
            self.freeze_btn["state"] = tk.DISABLED
        else:
            self.install_btn["state"] = "normal"
            self.uninstall_btn["state"] = "normal"
            self.freeze_btn["state"] = "normal"
            
        self.listview._clear_tree()
        if self.interpreter is not None:
            utils.get_logger().debug("load interpreter %s package" % self.interpreter.Name)
            self.interpreter.LoadPackages(self,force)
            if self.interpreter.IsLoadingPackage:
                self.listview.tree.insert("",0,values=(_("Loading Package List....."),""))
                return
            self.LoadPackageList(self.interpreter)
            
    def LoadPackageList(self,interpreter):
        for name in interpreter.Packages:
            self.AddPackage(interpreter.Packages[name])
        utils.get_logger().debug("load interpreter %s package end" % self.interpreter.Name)
            
    def LoadPackageEnd(self,interpreter):
        if self.interpreter != interpreter:
            utils.get_logger().debug("interpreter %s is not panel current interprter,current interpreter is %s" , interpreter.Name,self.interpreter.Name)
            return
        self.listview._clear_tree()
        self.LoadPackageList(interpreter)
        
    def AddPackage(self,python_package,interpreter=None,remove_exist=False):
        if remove_exist:
            utils.get_logger().info("package name %s version %s already exist,remove package first!",python_package.Name,python_package.Version)
            self.RemovePackage(python_package.Name,interpreter)
        self.listview.tree.insert("",0,values=(python_package.Name,python_package.Version))
        if interpreter is not None:
            interpreter.Packages[python_package.Name] = python_package
        
    def RemovePackage(self,name,interpreter):
        row,package_name = self.GetPackageRow(name)
        if row == -1:
            return
        self.dvlc.DeleteItem(row)
        del interpreter.Packages[package_name]
        
    def NotifyPackageConfigurationChange(self):
        self.GetParent().GetParent().NotifyConfigurationChange()
        
    def FreezePackage(self):
        text_docTemplate = GetApp().GetDocumentManager().FindTemplateForPath("test.txt")
        default_ext = text_docTemplate.GetDefaultExtension()
        descrs = strutils.get_template_filter(text_docTemplate)
        filename = filedialog.asksaveasfilename(
            master = self,
            filetypes=[descrs],
            defaultextension=default_ext,
            initialdir=text_docTemplate.GetDirectory(),
            initialfile="requirements.txt"
        )
        if filename == "":
            return
        try:
            with open(filename,"wb") as f:
                command = self.interpreter.GetPipPath() + " freeze"
                subprocess.call(command,shell=True,stdout=f,stderr=subprocess.STDOUT)
        except Exception as e:
            messagebox.showerror(_("Error"),str(e))