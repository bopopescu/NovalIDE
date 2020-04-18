# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         DebuggerService.py
# Purpose:      Debugger Service for Python and PHP
#
# Author:       Matt Fryer
#
# Created:      12/9/04
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------
from noval import NewId,GetApp,_
import tkinter as tk
from tkinter import ttk,messagebox
import sys
from noval.project.debugger import *
import traceback
import noval.python.debugger.watchs as watchs
import pickle
from noval.python.debugger.commandui import BaseDebuggerUI,ShowBreakdebugViews,PythonDebuggerUI,RunCommandUI
import noval.menu as tkmenu
from noval.python.debugger.executor import PythonExecutor
import noval.ui_utils as ui_utils
import noval.misc as misc
from tkinter import colorchooser

class PythonDebugger(Debugger):
    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    RUN_PARAMETERS = []
    #异常中断列表
    EXCEPTIONS = []
    #调试器只允许运行一个
    _debugger_ui = None

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self):
        Debugger.__init__(self)
        self._frame = None
        self.projectPath = None
        self.phpDbgParam = None
       # self.dbgLanguage = projectmodel.LANGUAGE_DEFAULT
        self._tabs_menu = None
        self._popup_index = -1
        self._watch_separater = None
        
    @classmethod
    def SetDebuggerUI(cls,debugger_ui):
        cls._debugger_ui  = debugger_ui
        
    def GetExceptions(self):
        return PythonDebugger.EXCEPTIONS
        
    def SetExceptions(self,exceptions):
        PythonDebugger.EXCEPTIONS = exceptions

    def _right_btn_press(self, event):
        try:
            index = self.bottomTab.index("@%d,%d" % (event.x, event.y))
            self._popup_index = index
            self.create_tab_menu()
        except Exception:
            utils.get_logger().exception("Opening tab menu")

    def GetBottomtabInstancePage(self,index):
        tab_page = self.bottomTab.get_child_by_index(index)
        page = tab_page.winfo_children()[0]
        return page

    def CloseAllPages(self):
        '''
            关闭并移除所有运行调式标签页
        '''
        close_suc = True
        for i in range(self.bottomTab.GetPageCount()-1, -1, -1): # Go from len-1 to 1
            page = self.GetBottomtabInstancePage(i)
            close_suc = self.ClosePage(page)
            #关闭其中一个调试运行标签页失败,则表示关闭整个失败,在退出程序检查是否有进程运行时表示是否退出程序
            if not close_suc:
                return False
        return close_suc

    def ClosePage(self,page=None):
        '''
            关闭并移除单个运行调式标签页
        '''
        if page is None:
            page = self.GetBottomtabInstancePage(self._popup_index)
        #运行调试标签页关闭之前先检查进程是否在运行,并询问用户是否关闭
        if hasattr(page, 'StopAndRemoveUI'):
            return page.StopAndRemoveUI()
        #非运行调式标签页直接允许关闭
        return True
            
    def create_tab_menu(self):
        """
        Handles right clicks for the notebook, enabling users to either close
        a tab or select from the available documents if the user clicks on the
        notebook's white space.
        """
        if self._popup_index < 0:
            return
        page = self.GetBottomtabInstancePage(self._popup_index)
        #只有运行调试页面才弹出菜单
        if not hasattr(page, 'StopAndRemoveUI'):
            return
        if self._tabs_menu is None:
            menu = tkmenu.PopupMenu(self.bottomTab.winfo_toplevel())
            self._tabs_menu = menu
            menu.Append(constants.ID_CLOSE,_("Close"),handler=self.ClosePage)
            menu.Append(constants.ID_CLOSE_ALL,_("Close All"),handler=self.CloseAllPages)
        self._tabs_menu.tk_popup(*self.bottomTab.winfo_toplevel().winfo_pointerxy())

    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    # Class Methods
    #----------------------------------------------------------------------------
    
    def CheckScript(self):
        if not PythonExecutor.GetPythonExecutablePath():
            return
        interpreter = GetApp().GetCurrentInterpreter()
        doc_view = self.GetActiveView()
        if not doc_view:
            return
        document = doc_view.GetDocument()
        if not document.Save() or document.IsNewDocument:
            return
        if not os.path.exists(interpreter.Path):
            wx.MessageBox("Could not find '%s' on the path." % interpreter.Path,_("Interpreter not exists"),\
                          wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
            return
        ok,line,msg = interpreter.CheckSyntax(document.GetFilename())
        if ok:
            messagebox.showinfo(GetApp().GetAppName(),_("Check Syntax Ok!"),parent=doc_view.GetFrame())
            return
        messagebox.showerror(GetApp().GetAppName(),msg,parent=doc_view.GetFrame())
        if line > 0:
            doc_view.GotoLine(line)

    def Runfile(self,filetoRun=None):
        self.GetCurrentProject().Run(filetoRun)

    @common_run_exception 
    def RunWithoutDebug(self,filetoRun=None):
        self.GetCurrentProject().RunWithoutDebug(filetoRun)

    @common_run_exception 
    def RunLast(self):
        self.GetCurrentProject().RunLast()

    @common_run_exception
    def DebugLast(self):
        self.GetCurrentProject().DebugRunLast()
        
    @common_run_exception
    def RunLast(self):
        self.GetCurrentProject().RunLast()
        
    def StepNext(self):
        #如果调试器在运行,则执行单步调试
        if BaseDebuggerUI.DebuggerRunning():
            self._debugger_ui.OnNext()
        else:
            #否则进入断点调试并在开始出中断
            self.GetCurrentProject().BreakintoDebugger()
        
    def StepInto(self):
        #如果调试器在运行,则执行调试方法
        if BaseDebuggerUI.DebuggerRunning():
            self._debugger_ui.OnSingleStep()
        else:
            #否则进入断点调试并在开始出中断
            self.GetCurrentProject().BreakintoDebugger()

    def SetParameterAndEnvironment(self):
        self.GetCurrentProject().SetParameterAndEnvironment()

    @classmethod
    def CloseDebugger(cls):
        # IS THIS THE RIGHT PLACE?
        try:
            if cls._debugger_ui is not None:
                #保存监视信息
                cls._debugger_ui.framesTab.watchsTab.SaveWatchs()
                #保存断点信息
                cls._debugger_ui.framesTab.breakPointsTab.SaveBreakpoints()
            if not RunCommandUI.StopAndRemoveAllUI():
                return False
        except:
            tp,val,tb = sys.exc_info()
            traceback.print_exception(tp, val, tb)
        return True
    
    def AppendRunParameter(self,run_paramteter):
        if len(self.RUN_PARAMETERS) > 0:
            self.GetCurrentProject().SaveRunParameter(self.RUN_PARAMETERS[-1])
        self.RUN_PARAMETERS.append(run_paramteter)

    def IsFileContainBreakPoints(self,document):
        '''
            判断单个文件是否包含断点信息
        '''
        doc_path = document.GetFilename()
        masterBPDict = GetApp().MainFrame.GetView(consts.BREAKPOINTS_TAB_NAME).GetMasterBreakpointDict()
        if doc_path in masterBPDict and len(masterBPDict[doc_path]) > 0:
            return True
        return False
        
    def CreateDebuggerMenuItem(self,runMenu,menu_id,text,image,handler,menu_index):
        '''
            添加断点调式菜单项,如果菜单项已经存在不能重复添加
        '''
        if not runMenu.FindMenuItem(menu_id):
            runMenu.Insert(menu_index,menu_id,text,img=image,handler=handler)
            
    def DeleteDebuggerMenuItem(self,runMenu,menu_id):
        '''
            删除断点调式菜单项,只有在菜单项已经存在时才能删除
        '''
        if runMenu.FindMenuItem(menu_id):
            menu_index = runMenu.GetMenuIndex(menu_id)
            runMenu.delete(menu_index,menu_index)

    def ShowHideDebuggerMenu(self,show=True):
        run_menu = GetApp().Menubar.GetRunMenu()
        if show:
            menu_index = 3
            self.CreateDebuggerMenuItem(run_menu,constants.ID_RESTART_DEBUGGER,_("&Restart"),self._debugger_ui.restart_bmp,self._debugger_ui.RestartDebugger,menu_index)
            self.CreateDebuggerMenuItem(run_menu,constants.ID_TERMINATE_DEBUGGER,_("&Stop Debugging"),self._debugger_ui.stop_bmp,self._debugger_ui.StopExecution,menu_index)
            self.CreateDebuggerMenuItem(run_menu,constants.ID_BREAK_INTO_DEBUGGER,_("&Break"),self._debugger_ui.break_bmp,self._debugger_ui.BreakExecution,menu_index)
            self.CreateDebuggerMenuItem(run_menu,constants.ID_STEP_CONTINUE,_("&Continue"),self._debugger_ui.continue_bmp,self._debugger_ui.OnContinue,menu_index) 
            self.CreateDebuggerMenuItem(run_menu,constants.ID_STEP_OUT,_("&Step Out"),self._debugger_ui.stepOut_bmp,self._debugger_ui.OnStepOut,11)
            self.CreateDebuggerMenuItem(run_menu,constants.ID_QUICK_ADD_WATCH,_("&Quick add Watch"),self._debugger_ui.quick_watch_bmp,self._debugger_ui.OnQuickAddWatch,12)
            self.CreateDebuggerMenuItem(run_menu,constants.ID_ADD_WATCH,_("&Add Watch"),self._debugger_ui.watch_bmp,self._debugger_ui.OnAddWatch,13) 
            ShowBreakdebugViews(True)           
        else:
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_STEP_OUT)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_TERMINATE_DEBUGGER)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_STEP_CONTINUE)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_BREAK_INTO_DEBUGGER)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_RESTART_DEBUGGER)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_ADD_WATCH)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_QUICK_ADD_WATCH)
            ShowBreakdebugViews(False)
        
    def AddtoWatchText(self,text):
        self._debugger_ui.framesTab.AddtoWatchExpression(text,text)
        
    def AddWatchText(self,text,quick_watch=False):
        self._debugger_ui.framesTab.AddWatchExpression(text,text,quick_watch)

class DebuggerOptionsPanel(ui_utils.CommonOptionPanel):
    def __init__(self, parent):
        ui_utils.CommonOptionPanel.__init__(self, parent)
        row = ttk.Frame(self.panel)
        
        row = ttk.Frame(self.panel)
        self.disable_edit_var = tk.IntVar(value=utils.profile_get_int("DISABLE_EDIT_WHEN_DEBUGGER_RUNNING",True))
        disable_edit_chk_box = ttk.Checkbutton(row,text = _("Disable edit code file When debugger is running"),variable=self.disable_edit_var)
        disable_edit_chk_box.pack(fill="x")
        row.pack(fill=tk.X)

        row = ttk.Frame(self.panel)
        self.show_tip_value_var = tk.IntVar(value=utils.profile_get_int("ShowTipValueWhenDebugging",True))
        show_tip_value_chk_box = ttk.Checkbutton(row,text = _("Show memory value when mouse hover over word while debugger is running"),variable=self.show_tip_value_var)
        show_tip_value_chk_box.pack(fill="x")
        row.pack(fill=tk.X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
        row = ttk.Frame(self.panel)
        localHostStaticText = ttk.Label(row,text = _("Local Host Name:"))
        self.host_name_var = tk.StringVar(value=utils.profile_get("DebuggerHostName", consts.DEFAULT_HOST))
        LocalHostTextCtrl = ttk.Entry(row, textvariable=self.host_name_var)
        localHostStaticText.pack(fill="x",side=tk.LEFT)
        LocalHostTextCtrl.pack(fill="x",side=tk.LEFT)
        row.pack(fill=tk.X)
        row = ttk.Frame(self.panel)
        portNumberStaticText = ttk.Label(row,text= _("Port Range:"))
        dashStaticText = ttk.Label(row, text=_("through to"))
        startingPort = utils.profile_get_int("DebuggerStartingPort", consts.DEFAULT_PORT)
        self.start_port_var = tk.IntVar(value=startingPort)
        
        #验证端口文本控件输入是否合法,端口只能输入数字
        validate_cmd = self.register(self.validatePortInput)
        self._PortNumberTextCtrl = ttk.Entry(row, validate = 'key', validatecommand = (validate_cmd, '%P'),textvariable=self.start_port_var)
        self.start_port_var.trace("w", self.MinPortChange)
        
        self.end_port_var = tk.IntVar(value=startingPort + consts.PORT_COUNT)
        self._EndPortNumberTextCtrl = ttk.Entry(row,validate = 'key', validatecommand = (validate_cmd, '%P'), textvariable=self.end_port_var)
        self._EndPortNumberTextCtrl['state'] = tk.DISABLED
        
        portNumberStaticText.pack(fill="x",side=tk.LEFT)
        self._PortNumberTextCtrl.pack(fill="x",side=tk.LEFT)
        
        dashStaticText.pack(fill="x",side=tk.LEFT)
        self._EndPortNumberTextCtrl.pack(fill="x",side=tk.LEFT)
        row.pack(fill=tk.X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self._flushPortsButton = ttk.Button(self.panel,text=_("Reset Port List"),command=self.FlushPorts)
        self._flushPortsButton.pack(anchor=tk.W,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

    def validatePortInput(self,contents):
        if not contents.isdigit():
            self._PortNumberTextCtrl.bell()
            self._EndPortNumberTextCtrl.bell()
            return False
        return True
        
    def IsStartportInbounds(self):
        if self.start_port_var.get() >= 1 and self.start_port_var.get() <= 65514:
            return  True
        return False
        
    def IsEndportInbounds(self):
        if self.end_port_var.get() >= 22 and self.end_port_var.get() <= 65535:
            return  True
        return False
        
    def FlushPorts(self):
        if self.IsStartportInbounds():
            utils.profile_set("DebuggerStartingPort", self.start_port_var.get())
            PythonDebuggerUI.NewPortRange()
        else:
            messagebox.showinfo( _("Invalid Starting Port Number"),_("The starting port is not valid. Please change the value and try again."))

    def MinPortChange(self, *args):
        self._EndPortNumberTextCtrl['state'] = tk.NORMAL
        self.end_port_var.set( self.start_port_var.get() + consts.PORT_COUNT)
        self._EndPortNumberTextCtrl['state'] = tk.DISABLED

    def OnOK(self, optionsDialog):
        if self.IsStartportInbounds():
            utils.profile_set("DebuggerStartingPort", self.start_port_var.get())
        else:
            messagebox.showerror(_("Error"),_("Debugger start port is out of range"))
            return False
            
        if not self.IsEndportInbounds():
            messagebox.showerror(_("Error"),_("Debugger end port is out of range"))
            return False
        utils.profile_set("DebuggerHostName", self.host_name_var.get())
        utils.profile_set("DISABLE_EDIT_WHEN_DEBUGGER_RUNNING", self.disable_edit_var.get())
        utils.profile_set("ShowTipValueWhenDebugging", self.show_tip_value_var.get())
        return True

    def GetIcon(self):
        return getContinueIcon()

class OutputOptionsPanel(ui_utils.CommonOptionPanel):
    def __init__(self, parent):
        ui_utils.CommonOptionPanel.__init__(self, parent)
        row = ttk.Frame(self.panel)
        self.wrap_var = tk.IntVar(value=utils.profile_get_int("WordWrap",False))
        wrap_chk_box = ttk.Checkbutton(row,text = _("Word Wrap"),variable=self.wrap_var)
        wrap_chk_box.pack(fill="x",side=tk.LEFT)
        row.pack(fill=tk.X)
        
        row = ttk.Frame(self.panel)
        self.limit_line_var = tk.IntVar(value=utils.profile_get_int("LimitLineLength",True))
        limit_chk_box = ttk.Checkbutton(row,text = _("Limit console line output"),variable=self.limit_line_var,\
                                command=self.CheckLimitLine)
        limit_chk_box.pack(fill="x",side=tk.LEFT)
        row.pack(fill=tk.X)
        
        row = ttk.Frame(self.panel)
        consoleLineStaticText = ttk.Label(row,text= _("Console line length(characters):"))
   
        limit_line_length = utils.profile_get_int("MaxLineLength", 1000)
        self.max_line_length_var = tk.IntVar(value=limit_line_length)
        
        #验证控件输入是否合法,只能输入数字
        validate_cmd = self.register(self.validateLimitLineInput)
        self.limit_line_lengthTextCtrl = ttk.Entry(row, validate = 'key', validatecommand = (validate_cmd, '%P'),textvariable=self.max_line_length_var)
        misc.create_tooltip(self.limit_line_lengthTextCtrl,_('NB!Large values may cause poor performance!'))
        consoleLineStaticText.pack(fill="x",side=tk.LEFT)
        self.limit_line_lengthTextCtrl.pack(fill="x",side=tk.LEFT)
        
        row.pack(fill=tk.X)
        self.CheckLimitLine()
        palette = ttk.Frame(self.panel)
        self.output_label = self.CreateColorPalette(_("Standard Output text color:"),utils.profile_get("StandardOutputColor","black"),palette,0)
        self.error_label = self.CreateColorPalette(_("Standard Error text color:"),utils.profile_get("StandardErrorColor","red"),palette,1)
        self.input_label = self.CreateColorPalette(_("Standard Input text color:"),utils.profile_get("StandardInputColor","blue"),palette,2)
        palette.pack(fill="x",pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y,0))
        
    def CreateColorPalette(self,text,color,palette,row):
        ttk.Label(palette,text=text).grid(row=row,column=0,sticky="nsew")
        f = ttk.Frame(palette, borderwidth=1, relief="raised",style="palette.TFrame")
        l = tk.Label(f, background=color, width=2, height=1)
        l.bind("<1>", self._palette_cmd)
        f.bind("<FocusOut>", lambda e: e.widget.configure(relief="raised"))
        l.pack()
        f.grid(row=row,column=1,sticky="nsew",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0),pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y,0))
        return l
        
    def _palette_cmd(self, event):
        label = event.widget
        label.master.focus_set()
        label.master.configure(relief="sunken")
        rgb,result = colorchooser.askcolor(color=label.cget("background"),parent=self)
        if rgb and result:
            label.configure(background=result)
        label.master.configure(relief="raised")
        
    def CheckLimitLine(self):
        if not self.limit_line_var.get():
            self.limit_line_lengthTextCtrl['state'] = tk.DISABLED
        else:
            self.limit_line_lengthTextCtrl['state'] = tk.NORMAL

    def validateLimitLineInput(self,contents):
        if not contents.isdigit():
            self.limit_line_lengthTextCtrl.bell()
            return False
        return True
        
    def OnOK(self, optionsDialog):
        utils.profile_set('WordWrap',self.wrap_var.get())
        utils.profile_set('LimitLineLength',self.limit_line_var.get())
        if self.max_line_length_var.get() < 500:
            messagebox.showinfo(GetApp().GetAppName(),_('Max line length must greater then 500'))
            return False
        utils.profile_set('MaxLineLength',self.max_line_length_var.get())
        utils.profile_set('StandardOutputColor',self.output_label.cget("background"))
        utils.profile_set('StandardErrorColor',self.error_label.cget("background"))
        utils.profile_set('StandardInputColor',self.input_label.cget("background"))
        views = GetApp().MainFrame.GetViews()
        #将输出颜色设置应用到所有输出窗口
        for view_name in views:
            if view_name.find("Debugger") != -1:
                view = views[view_name]
                instance = view["instance"]
                instance.GetOutputCtrl().UpdateConfigure()
        return True
        
class RunOptionsPanel(ui_utils.CommonOptionPanel):
    def __init__(self, parent):
        ui_utils.CommonOptionPanel.__init__(self, parent)
        row = ttk.Frame(self.panel)
        self.keep_pause_var = tk.IntVar(value=utils.profile_get_int("KeepTerminalPause",True))
        keep_pause_chk_box = ttk.Checkbutton(row,text = _("Keep terminal window pause after Python process ends"),variable=self.keep_pause_var)
        keep_pause_chk_box.pack(fill="x",side=tk.LEFT)
        row.pack(fill=tk.X)
        
    def OnOK(self, optionsDialog):
        utils.profile_set('KeepTerminalPause',self.keep_pause_var.get())
        return True

