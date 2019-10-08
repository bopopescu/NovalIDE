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
import os
import tkinter as tk
from tkinter import ttk
import noval.project.executor as executor
import noval.toolbar as toolbar
from noval.project.output import *
from noval.project.executor import *
import noval.core as core

def common_run_exception(func):
    '''
        调式运行公共异常处理函数,装饰调式运行函数,做同样的异常处理
    '''
    def _wrapper(*args, **kwargs): 
        try:
            func(*args, **kwargs)
        except executor.StartupPathNotExistError as e:
            e.ShowMessageBox()
        except Exception as e:
            if not isinstance(e,RuntimeError):
                utils.get_logger().exception("")
            messagebox.showerror(_("Run Error"),str(e),parent=GetApp().GetTopWindow())
    return _wrapper 

class CommonRunCommandUI(ttk.Frame):
    KILL_PROCESS_ID = NewId()
    CLOSE_TAB_ID = NewId()
    TERMINATE_ALL_PROCESS_ID = NewId()
    RESTART_PROCESS_ID = NewId()

    def __init__(self,parent, debugger,run_parameter,toolbar_orient=tk.HORIZONTAL):
        ttk.Frame.__init__(self, parent)
        self._debugger = debugger
        self._run_parameter = run_parameter
        self._restarted = False
        self._stopped = False
        # GUI Initialization follows
        self._tb = toolbar.ToolBar(self,orient=toolbar_orient)
        if toolbar_orient == tk.HORIZONTAL:
            self._tb.pack(fill="x",expand=0)
        else:
            self._tb.pack(side=tk.LEFT,fill="y",expand=0)
        self.CreateToolbarButtons()
        self._output = self.GetOutputviewClass()(self) #id)
        self._output.pack(side=tk.LEFT,fill="both",expand=1)
        self._textCtrl = self._output.GetOutputCtrl()
        # Executor initialization
        self._executor = None
        if self._run_parameter is not None:
            self.CreateExecutor()
        self.EnableToolbar()
        
    def EnableToolbar(self):
        if self._executor is None:
            enable = False
        else:
            enable = True
        self._tb.EnableTool(self.KILL_PROCESS_ID,enable=enable)
        self._tb.EnableTool(self.TERMINATE_ALL_PROCESS_ID,enable=enable)
        self._tb.EnableTool(self.RESTART_PROCESS_ID,enable=enable)
            
    def CreateToolbarButtons(self):
        
        self.terminate_all_image = GetApp().GetImage("python/debugger/terminate_all.png")
        self.restart_image = GetApp().GetImage("python/debugger/restart.png")
        self.close_img = GetApp().GetImage("python/debugger/close.png")
        self.stop_img = GetApp().GetImage("python/debugger/stop.png")
        
        self._tb.AddButton(self.CLOSE_TAB_ID,self.close_img,_("Close Window"),lambda:self.OnToolClicked(self.CLOSE_TAB_ID))
        self._tb.AddButton(self.KILL_PROCESS_ID,self.stop_img,_("Stop the Run."),lambda:self.OnToolClicked(self.KILL_PROCESS_ID))
        
        self._tb.AddButton(self.TERMINATE_ALL_PROCESS_ID,self.terminate_all_image,_("Stop All the Run."),lambda:self.OnToolClicked(self.TERMINATE_ALL_PROCESS_ID))
        self._tb.AddButton(self.RESTART_PROCESS_ID,self.restart_image,_("Restart the Run."),lambda:self.OnToolClicked(self.RESTART_PROCESS_ID))


    def SetRunParameter(self,run_parameter):
        self._run_parameter = run_parameter

    def CreateExecutor(self,source=SOURCE_DEBUG,finish_stopped=True):
        '''
            finish_stopped表示该执行器支持完成后,是否表示整个运行完成,大部分情况下一个进程执行完成,就表示改运行完成
            考虑到一次完整的运行可能需要连续执行几个进程,第一个进程执行完后并不表示整个执行完成,要接着执行下一个,直到最后一个进程执行完成才表示运行完成
            source表示输出日志来源,比如有的是build输出,有的是debug输出,默认是debug输出
        '''
        self._executor = self.GetExecutorClass()(self._run_parameter, self, callbackOnExit=lambda:self.ExecutorFinished(finish_stopped),source=source)
        self.evt_stdtext_binding = GetApp().bind(executor.EVT_UPDATE_STDTEXT, self.AppendText,True)
        self.evt_stdterr_binding = GetApp().bind(executor.EVT_UPDATE_ERRTEXT, self.AppendErrorText,True)
        self._output.SetExecutor(self._executor)

    def GetExecutorClass(self):
        return Executor

    def destroy(self):
        # See comment on PythonDebuggerUI.StopExecution
        self._executor.DoStopExecution()
        ttk.Frame.destroy(self)
        
    def GetOutputview(self):
        return self._output

    def GetOutputviewClass(self):
        return CommononOutputview

    @common_run_exception
    def Execute(self):
        try:
            self._executor.Execute()
        except Exception as e:
            self.StopExecution()
            self.ExecutorFinished()
            raise e
    
    def IsProcessRunning(self):
        return not self.Stopped
    
    @property
    def Stopped(self):
        return self._stopped
        
    def UpdateTerminateAllUI(self):
        self._tb.EnableTool(self.TERMINATE_ALL_PROCESS_ID, self.IsProcessRunning())
        
    def UpdateAllRunnerTerminateAllUI(self):
        pass
        
    def ExecutorFinished(self,stopped=True):
        '''
            stopped表示该执行完成后是否表示整个运行完成了,stopped为True表示是,为False表示否,意外着还有下一个执行
        '''
        try:
            self._stopped = stopped
            self._tb.EnableTool(self.KILL_PROCESS_ID, False)
            self._textCtrl.set_read_only(True)
            self.UpdateAllRunnerTerminateAllUI()
        except tk.TclError:
            utils.get_logger().warn("RunCommandUI object has been deleted, attribute access no longer allowed when finish executor")
            return
        #如果是点了重新执行按钮,程序执行完成后,需要再运行一次
        if self._restarted:
            self.RestartRunProcess()
            self._restarted = False

    def StopExecution(self,unbind_evt=False):
        if not self._stopped:
            if unbind_evt:
                GetApp().unbind(executor.EVT_UPDATE_STDTEXT,self.evt_stdtext_binding)
                GetApp().unbind(executor.EVT_UPDATE_ERRTEXT,self.evt_stdterr_binding)
            self._executor.DoStopExecution()
            self._textCtrl.set_read_only(True)

    def AppendText(self, event):
        if event.get('interface') != self:
            utils.get_logger().debug('run view interface receive other stdout msg,ignore it')
            return
        self._textCtrl.AppendText(event.get('source'),event.get('value'))

    def AppendErrorText(self, event):
        if event.get('interface') != self:
            utils.get_logger().debug('run view interface receive other stderr msg,ignore it')
            return
        self._textCtrl.AppendErrorText(event.get('source'),event.get('value'))

    def StopAndRemoveUI(self):
        '''
            这里必须返回True,否则会导致程序不允许关闭
        '''
        #类似于右上角按钮关闭事件,会更新菜单是否选中
        self.master.close()
        return True

    def SaveProjectFiles(self):
        '''
            调式运行时保存文件策略,默认保存当前项目的修改文件
        '''
        self._debugger.GetCurrentProject().PromptToSaveFiles()
        
    def RestartProcess(self):
        currentProj = GetApp().MainFrame.GetProjectView(False).GetCurrentProject()
        self.SaveProjectFiles()
        if not self._stopped:
            self._restarted = True
            self.StopExecution()
        else:
            self.RestartRunProcess()
            
    def RestartRunProcess(self):
        self._textCtrl.ClearOutput()
        self._tb.EnableTool(self.KILL_PROCESS_ID, True)
        self._tb.EnableTool(self.TERMINATE_ALL_PROCESS_ID, True)
        self._stopped = False
        self.Execute()

    #------------------------------------------------------------------------------
    # Event handling
    #-----------------------------------------------------------------------------

    def OnToolClicked(self, id):
        if id == self.KILL_PROCESS_ID:
            self.StopExecution()

        elif id == self.CLOSE_TAB_ID:
            self.StopAndRemoveUI()
            
        elif id == self.TERMINATE_ALL_PROCESS_ID:
            self.ShutdownAllRunners()
            
        elif id == self.RESTART_PROCESS_ID:
            self.RestartProcess()        

    def Close(self):
        self.StopAndRemoveUI()


class DebugView(core.View):
    '''
        调试视图,所有调式输出窗口共用这个一个视图
    '''
    def __init__(self,debugger):
        self._debugger = debugger
        core.View.__init__(self)
        
    def GetCtrl(self):
        '''
            获取当前标签页的控件
        '''
        select_page = self._debugger.bottomTab.get_current_child()
        if select_page is None:
            return None
        debug_page = self.GetDebugPage(select_page)
        return debug_page.GetOutputview().GetOutputCtrl()
        
    def GetDebugPage(self,tab_page):
        page = tab_page.winfo_children()[0]
        return page

class Debugger(object):

    DebugView = None
    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self):
        self.current_project = None
        self.bottomTab = GetApp().MainFrame._view_notebooks['s']
        if Debugger.DebugView is None:
            Debugger.DebugView = self._CreateView()
            #只能绑定一次事件
            self.bottomTab.bind("<ButtonPress-3>", self._right_btn_press, True)
        
    def _CreateView(self):
        return DebugView(self)
        
    def GetView(self):
        return self.DebugView

    def SetCurrentProject(self,currentProj):
        self.current_project = currentProj
        if self.current_project is not None:
            self.current_project.SetDebugger(self)

    @staticmethod
    def CloseDebugger():
        return True

    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    # Class Methods
    #----------------------------------------------------------------------------
            
    def GetKey(self, currentProj,lastPart):
        if currentProj:
            return currentProj.GetKey(lastPart)
        return lastPart
        
    def GetCurrentProject(self,always_have_one=True):
        if always_have_one and self.current_project is None:
            #获取项目实际的项目文档类
            #在运行单个文件时,默认创建一个项目文档,以此类运行单个文件,这个项目文档是一个虚拟的项目,不会到添加程序的文档列表中
            return GetApp().GetProjectTemplateClassData()[1].GetUnProjectDocument()
        return self.current_project
        
    def GetActiveView(self):
        current_editor = GetApp().MainFrame.GetNotebook().get_current_editor()
        if current_editor is None:
            return None
        return current_editor.GetView()
        
    @common_run_exception
    def Debug(self):
        self.GetCurrentProject().Debug()
        
    @common_run_exception
    def Run(self):
        self.GetCurrentProject().Run()

    def _right_btn_press(self,event):
        pass


class OutputRunCommandUI(CommonRunCommandUI):
    def __init__(self,master,debugger):
        CommonRunCommandUI.__init__(self,master,debugger,None)
        self._tb.AddLabel(text=" " + _("Source:") + " ",pos=0)
        self.combo = self._tb.AddCombox(pos=1)

    def AppendText(self, event):
        CommonRunCommandUI.AppendText(self,event)
        self.AddSource(event.get('source'))

    def AppendErrorText(self, event):
        CommonRunCommandUI.AppendErrorText(self,event)
        self.AddSource(event.get('source'))

    def AddSource(self,source):
        '''
            把输出来源归类
        '''
        if source not in self.combo['values']:
            if not self.combo['values']:
                self.combo['values'] = (source,)
            else:
                self.combo['values'] = self.combo['values'] + (source,)
        
#----------------------------------------------------------------------

