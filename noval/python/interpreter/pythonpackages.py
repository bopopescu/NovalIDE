# -*- coding: utf-8 -*-
from noval import _,GetApp
from tkinter import ttk
from tkinter import messagebox,filedialog
import tkinter as tk
import noval.ui_base as ui_base
import noval.python.interpreter.interpretermanager as interpretermanager
import os
import subprocess
import noval.outputthread as outputthread
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
import noval.ttkwidgets.textframe as textframe
import noval.util.compat as compat
import noval.util.fileutils as fileutils
from dummy.userdb import UserDataDb
import noval.ui_utils as ui_utils

def url_parse_host(url):
    '''
        解析url中的host
    '''
    parts = urlparse(url)
    host = parts.netloc
    return host

def get_package_versions(name):
    '''
    '''
    # Fetch info from novalide server
    api_addr = '%s/member/get_package' % (UserDataDb.HOST_SERVER_ADDR)
    data = utils.RequestData(api_addr,method='get',arg={'name':name})
    if not data:
        #未能从服务器上找到包
        return []
    else:
        return sorted(data['releases'])

class PackageActionChoiceDialog(ui_base.CommonModaldialog):
    '''
        检查到安装包时包已经存在,提示用户可供选择的几个操作选项对话框
    '''
    #重新安装
    REINSTALL = 0
    #安装最新版本
    UPDATE_LATEST = 1
    #安装指定版本
    UPDATE_SPECIFIED = 2
    def __init__(self, main,pkg_name):
        ui_base.CommonModaldialog.__init__(self, main, takefocus=1)
        self.title(_("Package '%s' installed")%pkg_name)
        #禁止对话框改变大小
        label_ctrl = ttk.Label(self.main_frame,text=_("Please choose the action you want:"))
        label_ctrl.pack(expand=1, fill="x",padx = consts.DEFAUT_CONTRL_PAD_X,pady = consts.DEFAUT_CONTRL_PAD_Y)

        self.choice_chkvar = tk.IntVar(value=self.UPDATE_LATEST)
        sizer_frame = ttk.Frame(self.main_frame)
        sizer_frame.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        self.reinstall_radiobutton = ttk.Radiobutton( sizer_frame, text=_("Reinstall"),value = self.REINSTALL,variable=self.choice_chkvar)
        self.reinstall_radiobutton.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.update_latest_radiobutton = ttk.Radiobutton(sizer_frame, text=_("Update to latest version"),value = self.UPDATE_LATEST,variable=self.choice_chkvar)
        self.update_latest_radiobutton.pack(fill="x")
        
        self.update_specified_radiobutton = ttk.Radiobutton(sizer_frame, text=_("Update to specified version"),value = self.UPDATE_SPECIFIED,variable=self.choice_chkvar)
        self.update_specified_radiobutton.pack(fill="x")
        
        separator = ttk.Separator (self.main_frame, orient = tk.HORIZONTAL)
        separator.pack(expand=1, fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady = (consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AddokcancelButton()

class CommonManagePackagesDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title,interpreter,interpreters,pkg_name,pkg_args='',autorun=False,call_back=None):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
        #包安装的解释器
        #解释器列表
        self.interpreter = interpreter
        self.interpreters = interpreters
        #包名称
        self.pkg_name = pkg_name
        #参数
        self.pkg_args = pkg_args
        #是否自动运行
        self.autorun = autorun
        #执行完成后的回调函数
        self.end_callback = call_back
        
    def CreateWidgets(self,row_no,interpreter_lablel,pkg_args_label,extra_label):
        row = ttk.Frame(self.main_frame)
        ttk.Label(row,text=interpreter_lablel).pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        names = self.GetNames()
        self.interpreter_name_var =  tk.StringVar(value=self.interpreter.Name)
        self._interpreterCombo = ttk.Combobox(row,values=names,textvariable=self.interpreter_name_var,state="readonly")
        self._interpreterCombo.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),fill="x",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.grid(row=row_no,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW)
        row_no += 1   
        
        label_1 = ttk.Label(self.main_frame, text=pkg_args_label)
        label_1.grid(row=row_no,column=0,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW)
        row_no += 1
        row = ttk.Frame(self.main_frame)
        self.args_var = tk.StringVar(value=self.pkg_args)
        self.args_ctrl = ttk.Entry(row,textvariable=self.args_var)
        self.args_ctrl.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),fill="x",expand=1)
        self.args_ctrl.bind("<Return>", self._ok, False)
        self.browser_btn = ttk.Button(row, text=_("Browse..."),command=self.BrowsePath)
        self.browser_btn.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.grid(row=row_no,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW)
        row_no += 1
        label_2 = ttk.Label(self.main_frame, text=extra_label)
        label_2.grid(row=row_no,column=0,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW)
        row_no += 1

        self.text_frame = textframe.TextFrame(self.main_frame,borderwidth=1,relief="solid",text_class=texteditor.TextCtrl)
        self.output_ctrl = self.text_frame.text
        #这里需要设置高亮属性为False否则会在安装取消时抛出异常
        self.output_ctrl.SetTagCurrentLine(False)
        self.output_ctrl['state'] = tk.DISABLED
        self.detail_output_row = row_no
        self.text_frame.grid(row=row_no,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.NSEW)
        row_no += 1
        
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.detail_btn = ttk.Button(self.bottom_frame, text=_("Show Details") + "↓",command=self.ShowHideDetails)
        self.detail_btn.pack(side=tk.LEFT,pady=consts.DEFAUT_CONTRL_PAD_Y,padx=consts.DEFAUT_CONTRL_PAD_X)
        self._show_details = False
        self.AddokcancelButton()
        self.bottom_frame.grid(row=row_no,column=0,sticky=tk.NSEW)

        self.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.ShowHideDetails()

    def ShowHideDetails(self):
        if not self._show_details:
            self.detail_btn.configure( text=_("Show Details") + "↓")
            self.text_frame.grid_forget()
            self._show_details = True 
        else:  
            self.text_frame.grid(row=self.detail_output_row,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.NSEW)
            self.detail_btn.configure( text=_("Hide Details") + "↑") 
            self._show_details = False   
        
    def BrowsePath(self):
        descrs = [(_("Text File"),".txt"),]
        title = _("Choose requirements.txt")
        path = filedialog.askopenfilename(main=self,title=title ,
                       filetypes = descrs,
                       initialfile= "requirements.txt"
                       )
        if not path:
            return
        self.GetInterpreter()
        self.SetRequirementsArgs(path)
        
    def SetRequirementsArgs(self,path):
        ''''''

    def AddokcancelButton(self):
        button_frame = ttk.Frame(self.bottom_frame)
        button_frame.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AppendokcancelButton(button_frame)
        
    def ExecCommandAndOutput(self,command,dlg):
        #shell must be True on linux
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout_thread = outputthread.OutputThread(p.stdout,p,dlg,call_after=True)
        stdout_thread.start()
        stderr_thread = outputthread.OutputThread(p.stderr,p,dlg,call_after=True)
        stderr_thread.start()
        p.wait()
        self.EndDialog(p.returncode)
        
    #界面关闭了但是多线程仍在运行操作界面控件,这里需要统一捕获tk异常
    @ui_utils.capture_tclerror
    def AppendText(self,content):
        self.output_ctrl['state'] = tk.NORMAL
        self.output_ctrl.set_read_only(False)
        if utils.is_py3_plus():
            content = compat.ensure_string(content)
        self.output_ctrl.insert(tk.END,content)
        self.output_ctrl.set_read_only(True)
        self.output_ctrl['state'] = tk.DISABLED
        
    def GetNames(self):
        names = []
        for interpreter in self.interpreters:
            names.append(interpreter.Name)
        return names

    def GetInterpreter(self):
        sel = self._interpreterCombo.current()
        self.interpreter = self.interpreters[sel]
        
    def _ok(self,event=None):
        if self.args_var.get().strip() == "":
            messagebox.showinfo(GetApp().GetAppName(),_("package name is empty"))
            return False
        self.GetInterpreter()
        if self.interpreter.IsBuiltIn or self.interpreter.GetPipPath() is None:
            messagebox.showerror(GetApp().GetAppName(),_("Could not find pip on the path"))
            return False
        self.EnableButton(enable=False)
        return True
        
    def EnableButton(self,enable=True):
        if enable:
            self.args_ctrl['state'] = tk.NORMAL
            self.ok_button['state'] = tk.NORMAL
        else:
            self.args_ctrl['state'] = tk.DISABLED
            self.ok_button['state'] = tk.DISABLED
            
    def run(self):
        pass
        
    def auto_run(self):
        if not self.autorun:
            return
        self._ok()
        
    def GetPackageName(self):
        #包名称为空,获取输入参数是否为包名称
        pkg_name = self.pkg_name
        if not pkg_name:
            args_name = self.args_var.get().strip()
            #输入参数没有空格,则输入为包名称
            if args_name.find(" ") == -1:
                pkg_name = args_name
        return pkg_name
        
class InstallPackagesDialog(CommonManagePackagesDialog):
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
    def __init__(self,parent,interpreter,interpreters=interpretermanager.InterpreterManager().interpreters,pkg_name='',install_args='',autorun=False,install_update=False,call_back=None):
        CommonManagePackagesDialog.__init__(self,parent,_("Install Package"),interpreter,interpreters,pkg_name,install_args,autorun,call_back)
        self.SOURCE_NAME_LIST = [
            _('Default Source'),
            _('Tsinghua'),
            _('Aliyun'),
            _('USTC'),
            _('HUST'),
            _('SDUT'),
            _('Douban'),
        ]
        #是否更新安装
        self.install_update = install_update
        row = ttk.Frame(self.main_frame)
        ttk.Label(row,text=_("We will use the pip source:")).pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self._pipSourceCombo = ttk.Combobox(row, values=self.SOURCE_NAME_LIST,state="readonly")
        self._pipSourceCombo.current(0)
        self._pipSourceCombo.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),fill="x",expand=1)
        self.check_source_btn = ttk.Button(row, text= _("Check the best source"),command=self.CheckTheBestSource)
        self.check_source_btn.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.grid(row=0,column=0,padx=consts.DEFAUT_CONTRL_PAD_X,sticky=tk.EW,)
        self.CreateWidgets(1,_("We will download and install it in the interpreter:"),\
                           _("Type the name of package or args to install:"),_("To install the specific version,type \"xxx==1.0.1\"\nTo install more packages,please specific the path of requirements.txt"))
        check_best_source = True
        pip_source = self.BEST_PIP_SOURCE
        if utils.profile_get_int("RemberPipsource", True):
            pip_source_path = self.GetPipsourcePath()
            #读取上次保存的pip源,并无需检查最佳pip源
            if os.path.exists(pip_source_path):
                check_best_source = False
                with open(pip_source_path) as f:
                    pip_source = f.read().strip()
        if self.BEST_PIP_SOURCE is None and check_best_source:
            self.CheckBestPipSource()
        else:
            self.SelectPipSource(pip_source)
            self.auto_run()

    def InstallPackage(self,interpreter):
        install_args = self.args_var.get().strip()
        command = strutils.emphasis_path(interpreter.GetPipPath()) + " install %s" % (install_args)
        #linux系统下安装包可能需要root权限
        if not sysutils.is_windows():
            #如果参数里面包含--user则包安装在$HOME目录下,无需root权限
            root = False if '--user ' in install_args else True
            if root:
                #这里是提示root权限
                command = "pkexec " + command
            
        if self.SOURCE_NAME_LIST[self._pipSourceCombo.current()] != self.SOURCE_NAME_LIST[0]:
            command += " -i " + self.SOURCE_LIST[self._pipSourceCombo.current()]
            host = url_parse_host(self.SOURCE_LIST[self._pipSourceCombo.current()])
            command += " --trusted-host " + host
            
        utils.get_logger().info("install command is %s",command)
        self.AppendText(command + os.linesep)
        self.call_back = self.AppendText
        t = threading.Thread(target=self.ExecCommandAndOutput,args=(command,self))
        t.start()
        
    def CheckBestPipSource(self):
        t = threading.Thread(target=self.GetBestPipSource)
        t.start()
        
    def GetBestPipSource(self):
        self.AppendText(_("Checking the best pip source...\n"))
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
            self.AppendText(_("Could not get the best pip source...\n"))
            return
                
        best_source,elapse = sorted(sort_pip_source_dct.items(),key = lambda x:x[1],reverse = False)[0]
        utils.get_logger().info("the best pip source is %s,response time is %.2fs",best_source,elapse)
        self.AppendText(_("the best pip source is %s\n")%best_source)
        InstallPackagesDialog.BEST_PIP_SOURCE = best_source
        self.SelectPipSource(self.BEST_PIP_SOURCE)
        self.EnableCheckSourcButton(True)
        self.auto_run()
        
    @ui_utils.capture_tclerror
    def SelectPipSource(self,pip_source_url=None):
        index = -1
        values = list(self._pipSourceCombo['values'])
        #删除原来的最优源选项
        for i,value in enumerate(values):
            if value.find(_("The Best Source")) != -1:
                values.remove(value)
                values.insert(i,self.SOURCE_NAME_LIST[i])
                break
                
        #设置新的最优源
        for i,pip_source in enumerate(self.SOURCE_LIST):
            if pip_source == self.BEST_PIP_SOURCE:
                best_source_name = self.SOURCE_NAME_LIST[i] + "(" + _("The Best Source") + ")"
                values.remove(self.SOURCE_NAME_LIST[i])
                values.insert(i,best_source_name)
                break
        #选中需要显示的源
        for i,pip_source in enumerate(self.SOURCE_LIST):
            if pip_source == pip_source_url:
                index = i
                break
        self._pipSourceCombo['values'] = tuple(values)
        if index != -1:
            self._pipSourceCombo.current(index)
  
    def CheckTheBestSource(self):
        self.CheckBestPipSource()

    @ui_utils.capture_tclerror
    def EnableCheckSourcButton(self,enable=True):
        if enable:
            self.check_source_btn['state'] = "normal"
            self.check_source_btn.configure(text=_("Check the best source"))
        else:
            self.check_source_btn.configure(text=_("Checking the best source"))
            self.check_source_btn['state'] = tk.DISABLED

    def EndDialog(self,retcode):
        pkg_name = self.GetPackageName()
        install_suc = False
        utils.get_logger().debug('install ret code is %d',retcode)
        if retcode == 0:
            if pkg_name:
                #检查包是否安装到解释器中
                python_package = self.interpreter.GetInstallPackage(pkg_name)
                #如果包存在说明安装成功
                install_suc = True if python_package else False
            #用户自定义输入安装参数
            else:
                python_package = None
                self.interpreter.LoadPackages(self.main,True)
                install_suc = True
        if install_suc:
            #只有安装成功才执行回调函数
            if self.end_callback:
                self.end_callback(python_package,self.interpreter) 
            if self.install_update:
                messagebox.showinfo(GetApp().GetAppName(),_("Update Success"),parent=self)
            else:
                messagebox.showinfo(GetApp().GetAppName(),_("Install Success"),parent=self)
            self.destroy()
        else:
            if self.install_update:
                messagebox.showerror(GetApp().GetAppName(),_("Update Fail"),parent=self)
            else:
                messagebox.showerror(GetApp().GetAppName(),_("Install Fail"),parent=self)
            self.EnableButton()
            
    def run(self):
        self.InstallPackage(self.interpreter)
        
    def GetPipsourcePath(self):
        cache_path = utils.get_cache_path()
        pip_source_path = os.path.join(cache_path,"pip_source.txt")
        return pip_source_path
        
    def _ok(self,event=None):
        if not CommonManagePackagesDialog._ok(self):
            return False
        #保存选择的pip源
        if utils.profile_get_int("RemberPipsource",True):
            pip_source_path = self.GetPipsourcePath()
            with open(pip_source_path,"w") as f:
                f.write(self.SOURCE_LIST[self._pipSourceCombo.current()])
              
        pkg_name = self.GetPackageName()
        if pkg_name:
            #安装包时查找包是否已经安装了,如果已经安装提示用户操作选项
            python_package = self.interpreter.GetInstallPackage(pkg_name)
            if python_package:
                choice_dlg = PackageActionChoiceDialog(self,pkg_name)
                if constants.ID_OK == choice_dlg.ShowModal():
                    choice = choice_dlg.choice_chkvar.get()
                    if choice != PackageActionChoiceDialog.REINSTALL:
                        self.install_update = True
                        #用户选择安装最新版本
                        if choice == PackageActionChoiceDialog.UPDATE_LATEST:
                            #pip更新到最新版本命令
                            self.args_var.set("-U %s"%pkg_name)
                        #用户选择安装指定版本
                        else:
                            versions = get_package_versions(pkg_name)
                            if not versions:
                                self.EnableButton()
                                return False
                            specified_dlg = ui_base.SingleChoiceDialog(self,_("Choose the specified version"),_("Please choose the specified version to install:"),versions,show_scrollbar=True)
                            if constants.ID_OK == specified_dlg.ShowModal():
                                install_version = specified_dlg.selection
                                #pip更新到指定版本命令
                                self.args_var.set("%s==%s"%(pkg_name,install_version))
                            else:
                                self.EnableButton()
                                return False
                        
                else:
                    self.EnableButton()
                    return False
                    
        self.run()
        
    def SetRequirementsArgs(self,path):
        '''
            设置通过requirements文件安装批量包的参数
        '''
        args = "-r "
        #如果不是虚拟解释器,通过user参数安装
        if not self.interpreter.IsVirtual():
            args = "--user " + args
        self.args_var.set(args + fileutils.opj(path))
                                      
class UninstallPackagesDialog(CommonManagePackagesDialog):    
    def __init__(self,parent,interpreter,interpreters=interpretermanager.InterpreterManager().interpreters,pkg_name='',uninstall_args='',\
                        autorun=False,call_back=None):
        CommonManagePackagesDialog.__init__(self,parent,_("Uninstall Package"),interpreter,interpreters,pkg_name,uninstall_args,autorun,call_back)
        self.CreateWidgets(0,_("We will uninstall it in the interpreter:"),\
                          _("Type the name of package or args to uninstall:"), _("To uninstall more packages,please specific the path of requirements.txt"))
        self.auto_run()
            
    def EndDialog(self,retcode):
        pkg_name = self.GetPackageName()
        uninstall_suc = False
        if retcode == 0:
            if pkg_name:
                #如果包不存在说明卸载成功
                python_package = self.interpreter.GetInstallPackage(pkg_name)
                uninstall_suc = False if python_package else True
            else:
                self.interpreter.LoadPackages(self.main,True)
                uninstall_suc = True
        if uninstall_suc:
            #只有卸载成功才执行回调函数
            if self.end_callback:
                self.end_callback(pkg_name,self.interpreter)
            messagebox.showinfo(GetApp().GetAppName(),_("Uninstall Success"),parent=self)
            self.destroy()
        else:
            messagebox.showerror(GetApp().GetAppName(),_("Uninstall Fail"),parent=self)
            self.EnableButton()
        
    def UninstallPackage(self,interpreter):
        uninstall_args = self.args_var.get().strip()
        command = strutils.emphasis_path(interpreter.GetPipPath()) + " uninstall -y %s" % (uninstall_args)
        pkg_name = self.GetPackageName()
        python_package = self.interpreter.GetInstallPackage(pkg_name)
        #linux系统卸载包可能需要root权限
        if not sysutils.is_windows():
            root = False
            if python_package:
                pkg_location = python_package.Location
                if pkg_location is not None:
                    #判断包安装目录是否有当前用户写的权限,如果有则不需要root,否则需要root
                    root = not fileutils.is_writable(pkg_location)
            if root:
                #这里是提示root权限
                command = "pkexec " + command
            
        utils.get_logger().info("uninstall command is %s",command)
        self.AppendText(command + os.linesep)
        self.call_back = self.AppendText
        t = threading.Thread(target=self.ExecCommandAndOutput,args=(command,self))
        t.start()
        
    def run(self):
        self.UninstallPackage(self.interpreter)
        
    def _ok(self,event=None):
        if not CommonManagePackagesDialog._ok(self):
            return False
        self.run()

    def SetRequirementsArgs(self,path):
        '''
            设置通过requirements文件安装卸载包的参数
        '''
        args = "-r "
        self.args_var.set(args + fileutils.opj(path))
            
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
        
    def InstallCallback(self,python_package,interpreter):
        '''
            安装完后如果包已经存在,则删除已有包
        '''
        if python_package:
            #如果包已经存在,删除现有包,添加包信息
            self.AddPyPiPackage(python_package,interpreter,True)
        else:
            #如果不知道安装包名称,则重新加载所有包信息
            self.LoadPackages(interpreter,force=True)
        self.NotifyPackageConfigurationChange()

    def InstallPip(self):
        dlg = InstallPackagesDialog(self,self.interpreter,self.main.main._interpreters,call_back=self.InstallCallback)
        status = dlg.ShowModal()
            
    def UninstallCallback(self,pkg_name,interpreter):
        '''
            卸载完后则删除已有包
        '''
        if pkg_name:
            self.RemovePackage(pkg_name,interpreter)
        else:
            #如果不知道安装包名称,则重新加载所有包信息
            self.LoadPackages(interpreter,force=True)
        self.NotifyPackageConfigurationChange()
        
    def UninstallPip(self):
        selections = self.listview.tree.selection()
        package_name = ""
        if selections:
            package_name = self.listview.tree.item(selections[0])['values'][0]
        dlg = UninstallPackagesDialog(self,self.interpreter,self.main.main._interpreters,pkg_name=package_name,uninstall_args=package_name,call_back=self.UninstallCallback)
        status = dlg.ShowModal()
        
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
            if name not in interpreter.Packages:
                continue
            self.AddPyPiPackage(interpreter.Packages[name])
        utils.get_logger().debug("load interpreter %s package end" % self.interpreter.Name)
            
    @ui_utils.capture_tclerror
    def LoadPackageEnd(self,interpreter):
        if self.interpreter != interpreter:
            utils.get_logger().debug("interpreter %s is not panel current interprter,current interpreter is %s" , interpreter.Name,self.interpreter.Name)
            return
        self.listview._clear_tree()
        self.LoadPackageList(interpreter)
        
    def AddPyPiPackage(self,python_package,interpreter=None,remove_exist=False):
        if remove_exist:
            self.RemovePackage(python_package.Name,interpreter)
        self.listview.tree.insert("",0,values=(python_package.Name,python_package.Version))
        if interpreter is not None:
            interpreter.Packages[python_package.Name] = python_package
        
    def RemovePackage(self,name,interpreter):
        item,package_name = self.GetPackageItem(name)
        if not item:
            return
        self.listview.tree.delete(item)
        if not package_name in interpreter.Packages:
            utils.get_logger().error("package name %s is not exist in packages when remove it....",package_name)
            return
        python_package = interpreter.Packages[package_name]
        utils.get_logger().info("package name %s version %s already exist,remove package first!",python_package.Name,python_package.Version)
        interpreter.Packages.pop(package_name)

    def GetPackageItem(self,package_name):
        #TODO: 有些包名称为0xxx之类的,tkinter treeview保存此类数据时,会去掉前面的0,并储存为整数如果字符串为整数字符串的话.
        #TODO: 需要采取方法避免此种情况
        package_name = str(package_name)
        childs = self.listview.tree.get_children()
        for child in childs:
            column_value = str(self.listview.tree.item(child)['values'][0])
            if column_value.lower() == package_name.lower():
                return child,column_value
        return None,""
        
    def NotifyPackageConfigurationChange(self):
        self.main.main.NotifyConfigurationChanged()
        
    def FreezePackage(self):
        text_docTemplate = GetApp().GetDocumentManager().FindTemplateForPath("test.txt")
        default_ext = text_docTemplate.GetDefaultExtension()
        descrs = strutils.get_template_filter(text_docTemplate)
        filename = filedialog.asksaveasfilename(
            main = self,
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