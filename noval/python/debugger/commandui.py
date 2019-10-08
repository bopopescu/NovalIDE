# -*- coding: utf-8 -*-
from noval import _,GetApp
import sys
import time
from noval.python.debugger.output import *
from noval.python.debugger.executor import *
from tkinter import ttk,messagebox
try:
    from SimpleXMLRPCServer import SimpleXMLRPCServer
    import xmlrpclib
    import Queue
    import SocketServer
except ImportError:
    import xmlrpc.client as xmlrpclib
    import queue as Queue
    import socketserver as SocketServer
    from xmlrpc.server import SimpleXMLRPCServer
import os
import threading
import types
from xml.dom.minidom import parse, parseString
import bz2
import shutil
import noval.python.interpreter.interpreter as pythoninterpreter
import noval.python.parser.utils as parserutils
import copy
import noval.util.appdirs as appdirs
import noval.util.utils as utils
import noval.python.project.runconfig as runconfig
import noval.python.debugger.watchs as watchs
import pickle
import noval.util.timer as pytimer
import noval.constants as constants
import noval.ui_base as ui_base
import noval.util.fileutils as fileutils
import noval.consts as consts
from noval.project.debugger import *


import noval.core as core
if utils.is_py2():
    import noval.python.debugger.debuggerharness as debuggerharness
elif utils.is_py3_plus():
    import noval.python.debugger.debuggerharness3 as debuggerharness
    
try:
    import tkSimpleDialog
except ImportError:
    import tkinter.simpledialog as tkSimpleDialog

#VERBOSE mode will invoke threading.Thread _VERBOSE,which will print a lot of thread debug text on screen
_VERBOSE = False
_WATCHES_ON = True
EVT_DEBUG_INTERNAL = "EVT_DEBUG_INTERNAL"


def ShowBreakdebugViews(show=True):
    GetApp().MainFrame.GetCommonView(consts.INTERACTCONSOLE_TAB_NAME,show=show)
    GetApp().MainFrame.GetCommonView(consts.BREAKPOINTS_TAB_NAME,show=show)
    GetApp().MainFrame.GetCommonView(consts.WATCH_TAB_NAME,show=show)
    GetApp().MainFrame.GetCommonView(consts.STACKFRAME_TAB_NAME,show=show)

class RunCommandUI(CommonRunCommandUI):
    runners = []
    def ShutdownAllRunners():
        # See comment on PythonDebuggerUI.StopExecution
        for runner in RunCommandUI.runners:
            try:
                runner.StopExecution()
                runner.UpdateAllRunnerTerminateAllUI()
            except tk.TclError:
                pass
    ShutdownAllRunners = staticmethod(ShutdownAllRunners)
    
    @staticmethod
    def StopAndRemoveAllUI():
        return GetApp().GetDebugger().CloseAllPages()

    def __init__(self,parent, debugger,run_parameter,append_runner=True,toolbar_orient=tk.VERTICAL):
        #toolbar使用垂直布局
        CommonRunCommandUI.__init__(self, parent,debugger,run_parameter,toolbar_orient=toolbar_orient)
        self._noteBook = parent
        if append_runner:
            RunCommandUI.runners.append(self)
        #重写关闭窗口事件,关闭窗口时检查进程是否在运行
        self.master.close = self.Close

    def GetOutputviewClass(self):
        return DebugOutputView

    def destroy(self):
        # See comment on PythonDebuggerUI.StopExecution
        RunCommandUI.runners.remove(self)
        CommonRunCommandUI.destroy(self)

    def GetExecutorClass(self):
        #python执行器
        return PythonExecutor
    
    def IsProcessRunning(self):
        process_runners = [runner for runner in self.runners if not runner.Stopped]
        return True if len(process_runners) > 0 else False
        
    def UpdateAllRunnerTerminateAllUI(self):
        for runner in self.runners:
            runner.UpdateTerminateAllUI()
        
    @utils.call_after
    def ExecutorFinished(self,stopped=True):
        self.UpdateFinishedPagePaneText()
        CommonRunCommandUI.ExecutorFinished(self,stopped=stopped)
        
    def UpdateViewLabel(self,src_text,to_text):
        '''
            更新调式视图刚开始的标签文本,否则在最大化和恢复文档窗口时,调式窗口显示的标签文本不准确
        '''
        for view_name in GetApp().MainFrame._views:
            instance = GetApp().MainFrame._views[view_name]["instance"]
            if instance == self:
                old_label = GetApp().MainFrame._views[view_name]['label']
                newLabel = old_label.replace(src_text,to_text)
                GetApp().MainFrame._views[view_name]['label'] = newLabel
                break
            
    #when process finished,update tag page text
    def UpdateFinishedPagePaneText(self):
        self.UpdatePagePaneText(_("Running"),_("Finished Running"))

    def StopAndRemoveUI(self):
        if not self._stopped:
            ret = messagebox.askyesno(_("Process Running.."),_("Process is still running,Do you want to kill the process and remove it?"),parent=self)
            if ret == False:
                return False

        self.StopExecution(unbind_evt=True)
        return self.RemoveUI()

    def RemoveUI(self):
        #关闭调试窗口,关闭notebook的子窗口
        self.master.master.close_child(self.master)
        #务必从视图列表中移除
        for view_name in GetApp().MainFrame._views:
            instance = GetApp().MainFrame._views[view_name]["instance"]
            if instance == self:
                del GetApp().MainFrame._views[view_name]
                break
        return True

    def RestartRunProcess(self):
        CommonRunCommandUI.RestartRunProcess(self)
        self.UpdateRestartPagePaneText()
        
    def UpdatePagePaneText(self,src_text,to_text):
        nb = self.master.master
        for index in range(0,len(nb.tabs())):
            if self.master == nb.get_child_by_index(index):
                text = nb.tab(nb.tabs()[index],"text")
                newText = text.replace(src_text,to_text)
                nb.tab(nb.tabs()[index], text=newText)
                break
        self.UpdateViewLabel(src_text,to_text)
    #when restart process,update tag page text
    def UpdateRestartPagePaneText(self):
        self.UpdatePagePaneText(_("Finished Running"), _("Running"))

    def SaveProjectFiles(self):
        '''
            调式运行python时保存文件策略,由于运行python文件时有多个调式页面,而且还可以运行单个文件,故保存文件策略比较复杂
        '''
        #如果调式运行的文件属于这个项目,则保存项目所有文件
        if self._debugger.GetCurrentProject().GetModel().FindFile(self._run_parameter.FilePath):
            self._debugger.GetCurrentProject().PromptToSaveFiles()
        else:
            #如果调式运行的文件不属于这个项目,则只保存该文件
            openDoc = GetApp().GetDocumentManager().GetDocument(self._run_parameter.FilePath)
            if openDoc:
                openDoc.Save()
                


DEFAULT_PORT = 32032
DEFAULT_HOST = 'localhost'
PORT_COUNT = 21


class AGXMLRPCServer(SimpleXMLRPCServer):
    def __init__(self, address, logRequests=0):
        ###enable request method return None value
        SimpleXMLRPCServer.__init__(self, address, logRequests=logRequests,allow_none=1)

class BaseDebuggerUI(RunCommandUI):
    debuggers = []
    
    KILL_PROCESS_ID = NewId()
    CLOSE_WINDOW_ID = NewId()
    CLEAR_ID = NewId()

    def NotifyDebuggersOfBreakpointChange():
        for debugger in BaseDebuggerUI.debuggers:
            debugger.BreakPointChange()

    NotifyDebuggersOfBreakpointChange = staticmethod(NotifyDebuggersOfBreakpointChange)

    def DebuggerRunning():
        for debugger in BaseDebuggerUI.debuggers:
            if debugger._executor:
                return True
        return False
    DebuggerRunning = staticmethod(DebuggerRunning)

    def DebuggerInWait():
        for debugger in BaseDebuggerUI.debuggers:
            if debugger._executor:
                if debugger._callback._waiting:
                    return True
        return False
    DebuggerInWait = staticmethod(DebuggerInWait)

    def DebuggerPastAutoContinue():
        for debugger in BaseDebuggerUI.debuggers:
            if debugger._executor:
                if debugger._callback._waiting and not debugger._callback._autoContinue:
                    return True
        return False
    DebuggerPastAutoContinue = staticmethod(DebuggerPastAutoContinue)

    def ShutdownAllDebuggers():
        for debugger in BaseDebuggerUI.debuggers:
            try:
                debugger.StopExecution(None)
            except wx._core.PyDeadObjectError:
                pass
        BaseDebuggerUI.debuggers = []
    ShutdownAllDebuggers = staticmethod(ShutdownAllDebuggers)

    def __init__(self,parent, debugger,run_parameter):
        RunCommandUI.__init__(self, parent,debugger,run_parameter,append_runner=False,toolbar_orient=tk.HORIZONTAL)
        self._executor = None
        self._callback = None
        self._stopped = False
        self._restarted = False

        BaseDebuggerUI.debuggers.append(self)
        self._stopped = True
        self.run_menu = GetApp().Menubar.GetRunMenu()
        self._toolEnabled = True
        self.framesTab = self.MakeFramesUI()
        self.DisableWhileDebuggerRunning()
        utils.update_statusbar(_("Starting debug..."))
        
    def CreateToolbarButtons(self):
        
        self.close_bmp = GetApp().GetImage("python/debugger/close.png")
        self._tb.AddButton( self.CLOSE_WINDOW_ID, self.close_bmp, _('Close Window'),self.StopAndRemoveUI)
        self._tb.AddSeparator()
        
        self.continue_bmp = GetApp().GetImage("python/debugger/step_continue.png")
        self._tb.AddButton( constants.ID_STEP_CONTINUE, self.continue_bmp, _("Continue Execution"),self.OnContinue)
        self.evt_debug_internal_binding = GetApp().bind(EVT_DEBUG_INTERNAL, self.OnContinue,True)
        
        self.break_bmp = GetApp().GetImage("python/debugger/break_into.png")
        self._tb.AddButton( constants.ID_BREAK_INTO_DEBUGGER, self.break_bmp, _("Break into Debugger"),self.BreakExecution)
        
        self.stop_bmp = GetApp().GetImage("python/debugger/stop.png")
        self._tb.AddButton( self.KILL_PROCESS_ID, self.stop_bmp, _("Stop Debugging"),self.StopExecution)
        
        self.restart_bmp = GetApp().GetImage("python/debugger/restart_debugger.png")
        self._tb.AddButton( constants.ID_RESTART_DEBUGGER, self.restart_bmp, _("Restart Debugging"),self.RestartDebugger)

        self._tb.AddSeparator()
        #表示运行下一行代码,快捷键为F10
        self.next_bmp = GetApp().GetImage("python/debugger/step_next.png")
        self._tb.AddButton( constants.ID_STEP_NEXT, self.next_bmp, _("Step to next line"),self.OnNext,accelerator=GetApp().Menubar.GetRunMenu().FindMenuItem(constants.ID_STEP_NEXT).accelerator)

        self.step_bmp = GetApp().GetImage("python/debugger/step_into.png")
        #表示进入当前方法,快捷键为F11
        self._tb.AddButton( constants.ID_STEP_INTO, self.step_bmp, _("Step in"),self.OnSingleStep,accelerator=GetApp().Menubar.GetRunMenu().FindMenuItem(constants.ID_STEP_INTO).accelerator)
        #表示退出当前方法,返回到调用层,快捷键为
        self.stepOut_bmp = GetApp().GetImage("python/debugger/step_return.png")
        self._tb.AddButton(constants.ID_STEP_OUT, self.stepOut_bmp, _("Stop at function return"),self.OnStepOut)

        self._tb.AddSeparator()
        if _WATCHES_ON:
            
            self.quick_watch_bmp = watchs.getQuickAddWatchBitmap()
            self._tb.AddButton(constants.ID_QUICK_ADD_WATCH, self.quick_watch_bmp, _("Quick Add a Watch"),self.OnQuickAddWatch)
            
            self.watch_bmp = watchs.getAddWatchBitmap()
            self._tb.AddButton(constants.ID_ADD_WATCH, self.watch_bmp, _("Add a Watch"),self.OnAddWatch)
            self._tb.AddSeparator()

        self.clear_bmp = GetApp().GetImage("python/debugger/clear_output.png")
        self._tb.AddButton(self.CLEAR_ID, self.clear_bmp, _("Clear output pane"),self.OnClearOutput)

    def OnSingleStep(self,callback=None):
        self._callback.SingleStep(callback)

    def OnContinue(self,event=None):
        self._callback.Continue()

    def OnStepOut(self,callback=None):
        self._callback.Return(callback)

    def OnNext(self,callback=None):
        self._callback.Next(callback)

    def BreakPointChange(self):
        if not self._stopped:
            #更改断点时,重新发送断点信息给服务器
            self._callback.PushBreakpoints()

    def destroy(self):
        # See comment on PythonDebuggerUI.StopExecution
        self.StopExecution()
        BaseDebuggerUI.debuggers.remove(self)
        ttk.Frame.destroy(self)

    def DisableWhileDebuggerRunning(self):
        '''
            调试器运行时需要禁止的菜单
        '''
        if self._toolEnabled:
            self._tb.EnableTool(constants.ID_STEP_INTO, False)
            self._tb.EnableTool(constants.ID_STEP_CONTINUE, False)
            if self.run_menu.FindMenuItem(constants.ID_STEP_CONTINUE):
                self.run_menu.Enable(constants.ID_STEP_CONTINUE,False)
            self._tb.EnableTool(constants.ID_STEP_OUT, False)
            if self.run_menu.FindMenuItem(constants.ID_STEP_OUT):
                self.run_menu.Enable(constants.ID_STEP_OUT,False)
            self._tb.EnableTool(constants.ID_STEP_NEXT, False)
            self._tb.EnableTool(constants.ID_BREAK_INTO_DEBUGGER, True)
            if self.run_menu.FindMenuItem(constants.ID_BREAK_INTO_DEBUGGER):
                self.run_menu.Enable(constants.ID_BREAK_INTO_DEBUGGER,True)
    
            if _WATCHES_ON:
                self._tb.EnableTool(constants.ID_ADD_WATCH, False)
                self._tb.EnableTool(constants.ID_QUICK_ADD_WATCH, False)
    
            self.DeleteCurrentLineMarkers()
    
            if self.framesTab:
                self.framesTab.ClearWhileRunning()

            self._toolEnabled = False

    def EnableWhileDebuggerStopped(self):
        '''
            调试器中断时需要允许使用的菜单
        '''
        self._tb.EnableTool(constants.ID_STEP_INTO, True)
        self._tb.EnableTool(constants.ID_STEP_CONTINUE, True)
        if self.run_menu.FindMenuItem(constants.ID_STEP_CONTINUE):
            self.run_menu.Enable(constants.ID_STEP_CONTINUE,True)
        self._tb.EnableTool(constants.ID_STEP_OUT, True)
        if self.run_menu.FindMenuItem(constants.ID_STEP_OUT):
            self.run_menu.Enable(constants.ID_STEP_OUT,True)
        self._tb.EnableTool(constants.ID_STEP_NEXT, True)
        self._tb.EnableTool(constants.ID_BREAK_INTO_DEBUGGER, False)
        if self.run_menu.FindMenuItem(constants.ID_BREAK_INTO_DEBUGGER):
            self.run_menu.Enable(constants.ID_BREAK_INTO_DEBUGGER,False)
        self._tb.EnableTool(self.KILL_PROCESS_ID, True)
        if self.run_menu.FindMenuItem(constants.ID_TERMINATE_DEBUGGER):
            self.run_menu.Enable(constants.ID_TERMINATE_DEBUGGER,True)

        if _WATCHES_ON:
            self._tb.EnableTool(constants.ID_ADD_WATCH, True)
            self._tb.EnableTool(constants.ID_QUICK_ADD_WATCH, True)

        self._toolEnabled = True

    def DisableAfterStop(self):
        '''
            调试器停止时需要禁止的菜单
        '''
        if self._toolEnabled:
            self.DisableWhileDebuggerRunning()
            self._tb.EnableTool(constants.ID_BREAK_INTO_DEBUGGER, False)
            if self.run_menu.FindMenuItem(constants.ID_BREAK_INTO_DEBUGGER):
                self.run_menu.Enable(constants.ID_BREAK_INTO_DEBUGGER,False)
            self._tb.EnableTool(self.KILL_PROCESS_ID, False)
            if self.run_menu.FindMenuItem(constants.ID_TERMINATE_DEBUGGER):
                self.run_menu.Enable(constants.ID_TERMINATE_DEBUGGER,False)

    @utils.call_after
    def ExecutorFinished(self):
        if _VERBOSE: print ("In ExectorFinished")
        try:
            self.DisableAfterStop()
            self.UpdatePagePaneText(_("Debugging"), _("Finished Debugging"))
            self._tb.EnableTool(self.KILL_PROCESS_ID, False)
        except tk.TclError:
            utils.get_logger().warn("BaseDebuggerUI object has been deleted, attribute access no longer allowed when finish debug executor")
            #关闭断点调式窗口,隐藏断点调式有关的菜单
            self._debugger.ShowHideDebuggerMenu(False)
            return
        if self._restarted:
            self.after(250,self.DoRestartDebugger)
        else:
            #调式完成并且不是重启调试器的话,隐藏断点调式有关的菜单
            self._debugger.ShowHideDebuggerMenu(False)
            
    def DoRestartDebugger(self):
        self.RestartDebuggerProcess()
        self._restarted = False

    def SetStatusText(self, text):
        utils.update_statusbar(text)

    def BreakExecution(self):
        if not BaseDebuggerUI.DebuggerRunning():
            messagebox.showinfo(GetApp().GetAppName(),_("Debugger has been stopped."))
            return
        self._callback.BreakExecution()

    def StopExecution(self):
        self._callback.ShutdownServer()

    def Execute(self, initialArgs, startIn, environment, onWebServer = False):
        assert False, "Execute not overridden"

    def SynchCurrentLine(self, filename, lineNum, noArrow=False):
        self.DeleteCurrentLineMarkers()

        # Filename will be <string> if we're in a bit of code that was executed from
        # a string (rather than a file). I haven't been able to get the original string
        # for display.
        if filename == '<string>':
            return
        foundView = None
        openDocs = GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            # This ugliness to prevent comparison failing because the drive letter
            # gets lowercased occasionally. Don't know why that happens or why  it
            # only happens occasionally.
            if parserutils.ComparePath(openDoc.GetFilename(),filename):
                foundView = openDoc.GetFirstView()
                break

        if not foundView:
            if _VERBOSE:
                print ("filename=", filename)
            docs = GetApp().GetDocumentManager().CreateDocument(filename, core.DOC_SILENT)
            if not docs:
                return
            doc = docs[0]
            foundView = doc.GetFirstView()

        if foundView:
            foundView.GetFrame().SetFocus()
            foundView.Activate()
            foundView.GotoLine(lineNum)

        if not noArrow:
            #标记并高亮断点调试所在的行
            foundView.GetCtrl().MarkerAdd(lineNum)
            
    def IsPythonDocument(self,openDoc):
        return fileutils.is_python_file(openDoc.GetFilename())
        
    def DeleteCurrentLineMarkers(self):
        openDocs = GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if self.IsPythonDocument(openDoc):
                openDoc.GetFirstView().GetCtrl().ClearCurrentLineMarkers()

    def StopAndRemoveUI(self):
        if self._executor:
            ret = messagebox.askyesno(_("Debugger Running.."),_("Debugger is still running,Do you want to kill the debugger and remove it?"), parent=self)
            if ret == False:
                return False
        self.StopExecution()
        self.RemoveUI()
        if self._callback.IsWait():
            utils.get_logger().warn("debugger callback is still wait for rpc when debugger stoped.will stop manualy")
            self._callback.StopWait()
        return True

    def OnAddWatch(self):
        self.framesTab.AddWatchExpression("","",False)
            
    def OnQuickAddWatch(self):
        self.framesTab.AddWatchExpression("","",True)

    def MakeFramesUI(self):
        assert False, "MakeFramesUI not overridden"

    def OnClearOutput(self):
        self.ClearOutput()
        
    def ClearOutput(self):
        self._textCtrl.ClearOutput()
        
    def RestartDebugger(self):
        assert False, "RestartDebugger not overridden"

class PythonDebuggerUI(BaseDebuggerUI):
    debuggerPortList = None

    def GetAvailablePort():
        for index in range( 0, len(PythonDebuggerUI.debuggerPortList)):
            port = PythonDebuggerUI.debuggerPortList[index]
            if PythonDebuggerUI.PortAvailable(port):
                PythonDebuggerUI.debuggerPortList.pop(index)
                return port
        messagebox.showerror(_("Out of Ports"),_("Out of ports for debugging!  Please restart the application builder.\nIf that does not work, check for and remove running instances of python."))
        assert False, "Out of ports for debugger."

    GetAvailablePort = staticmethod(GetAvailablePort)

    def ReturnPortToPool(port):
        config = wx.ConfigBase_Get()
        startingPort = config.ReadInt("DebuggerStartingPort", DEFAULT_PORT)
        val = int(startingPort) + int(PORT_COUNT)
        if int(port) >= startingPort and (int(port) <= val):
            PythonDebuggerUI.debuggerPortList.append(int(port))

    ReturnPortToPool = staticmethod(ReturnPortToPool)

    def PortAvailable(port):
        hostname = utils.profile_get("DebuggerHostName", DEFAULT_HOST)
        try:
            server = AGXMLRPCServer((hostname, port))
            server.server_close()
            if _VERBOSE: print ("Port ", str(port), " available.")
            return True
        except:
            utils.get_logger().exception('')
            if _VERBOSE: print ("Port ", str(port), " unavailable.")
            return False

    PortAvailable = staticmethod(PortAvailable)

    def NewPortRange():
        startingPort = utils.profile_get_int("DebuggerStartingPort", DEFAULT_PORT)
        PythonDebuggerUI.debuggerPortList = list(range(startingPort, startingPort + PORT_COUNT))
    NewPortRange = staticmethod(NewPortRange)

    def __init__(self, parent, debugger,run_parameter ,autoContinue=True):
        # Check for ports before creating the panel.
        if not PythonDebuggerUI.debuggerPortList:
            PythonDebuggerUI.NewPortRange()
        self._debuggerPort = str(PythonDebuggerUI.GetAvailablePort())
        self._guiPort = str(PythonDebuggerUI.GetAvailablePort())
        self._debuggerBreakPort = str(PythonDebuggerUI.GetAvailablePort())
        self._debuggerHost = self._guiHost = utils.profile_get("DebuggerHostName", DEFAULT_HOST)
        BaseDebuggerUI.__init__(self, parent, debugger,run_parameter)
        self._run_parameter = run_parameter
        self._autoContinue = autoContinue
        self._callback = None
        
        self.CreateCallBack()
        self.CreateExecutor()
        self._stopped = False

    def CreateExecutor(self):
        interpreter = self._run_parameter.Interpreter
        script_path = os.path.dirname(debuggerharness.__file__)
        if debuggerharness.__file__.find('.pyc') == -1:
            print ("Starting debugger on these ports: %s, %s, %s" % (str(self._debuggerPort) , str(self._guiPort) , str(self._debuggerBreakPort)))
        
        if interpreter.IsV2():
            path = os.path.join(script_path,"debuggerharness.py")
        elif interpreter.IsV3():
            path = os.path.join(script_path,"debuggerharness3.py")
        self._executor = PythonDebuggerExecutor(path, self._run_parameter,self, self._debuggerHost, \
                                                self._debuggerPort, self._debuggerBreakPort, self._guiHost, self._guiPort, self._run_parameter.FilePath, callbackOnExit=self.ExecutorFinished)
        self.evt_stdtext_binding = GetApp().bind(executor.EVT_UPDATE_STDTEXT, self.AppendText,True)
        self.evt_stdterr_binding = GetApp().bind(executor.EVT_UPDATE_ERRTEXT, self.AppendErrorText,True)
            
    def LoadPythonFramesList(self, framesXML):
        self.framesTab.LoadFramesList(framesXML)
        #进入断掉调试,更新监视的值
        self.framesTab.UpdateWatchs()

    def Execute(self, onWebServer = False):
        initialArgs = self._run_parameter.Arg
        startIn = self._run_parameter.StartupPath
        environment = self._run_parameter.Environment
        self._callback.Start()
        self._executor.Execute()
        self._callback.WaitForRPC()


    def StopExecution(self):
        # This is a general comment on shutdown for the running and debugged processes. Basically, the
        # current state of this is the result of trial and error coding. The common problems were memory
        # access violations and threads that would not exit. Making the OutputReaderThreads daemons seems
        # to have side-stepped the hung thread issue. Being very careful not to touch things after calling
        # process.py:ProcessOpen.kill() also seems to have fixed the memory access violations, but if there
        # were more ugliness discovered I would not be surprised. If anyone has any help/advice, please send
        # it on to mfryer@activegrid.com.
        if not self._stopped:
            self._stopped = True
            try:
                self.DisableAfterStop()
            except tk.TclError:
                pass
            try:
                self._callback.ShutdownServer()
            except:
                utils.get_logger().exception('')

            try:
                self.DeleteCurrentLineMarkers()
            except:
                pass
            try:
                PythonDebuggerUI.ReturnPortToPool(self._debuggerPort)
                PythonDebuggerUI.ReturnPortToPool(self._guiPort)
                PythonDebuggerUI.ReturnPortToPool(self._debuggerBreakPort)
            except:
                pass
            try:
                if self._executor:
                    self._executor.DoStopExecution()
                    self.framesTab.ResetWatchs()
                    self._executor = None
            except:
                utils.get_logger().exception('')


    def MakeFramesUI(self):
        panel = PythonFramesUI(self)
        return panel
        
    def UpdateWatch(self,watch_obj,item):
        self.framesTab.UpdateWatch(watch_obj,item)
        
    def UpdateWatchs(self,reset=False):
        self.framesTab.UpdateWatchs(reset)

    def OnSingleStep(self):
        #进入方法之后更新监视值
        BaseDebuggerUI.OnSingleStep(self,callback=self.UpdateWatchs)

    def OnContinue(self,event=None):
        BaseDebuggerUI.OnContinue(self,event)

    def OnStepOut(self):
        #退出方法之后更新监视值
        BaseDebuggerUI.OnStepOut(self,callback=self.UpdateWatchs)

    def OnNext(self):
        #单步调试之后更新监视值
        BaseDebuggerUI.OnNext(self,callback=self.UpdateWatchs)

    def DisableWhileDebuggerRunning(self):
        BaseDebuggerUI.DisableWhileDebuggerRunning(self)
        #运行调试器,在执行下一步调试的空隙,这个时间段调试器是没有运行的,故需要重置监视值
        self.UpdateWatchs(reset=True)
            
    def CreateCallBack(self):
        url = 'http://' + self._debuggerHost + ':' + self._debuggerPort + '/'
        self._breakURL = 'http://' + self._debuggerHost + ':' + self._debuggerBreakPort + '/'
        self._callback = PythonDebuggerCallback(self._guiHost, self._guiPort, url, self._breakURL, self, self._autoContinue)
            
    def RestartDebugger(self):
        currentProj = self._debugger.GetCurrentProject()
        if currentProj is not None and currentProj.GetModel().FindFile(self._run_parameter.FilePath):
            currentProj.PromptToSaveFiles()
        else:
            openView = utils.GetOpenView(self._run_parameter.FilePath)
            if openView:
                openDoc = openView.GetDocument()
                openDoc.Save()
        
        if not self._stopped:
            self._restarted = True
            self.StopExecution()
        else:
            self.RestartDebuggerProcess()
            
    def RestartDebuggerProcess(self):
        
        if BaseDebuggerUI.DebuggerRunning():
            messagebox.showinfo( _("Debugger Running"),_("A debugger is already running. Please shut down the other debugger first."))
            return

        self.OnClearOutput()
        self._tb.EnableTool(self.KILL_PROCESS_ID, True)
        self._stopped = False
        self.CheckPortAvailable()
        self.CreateCallBack()
        self.CreateExecutor()
        self.UpdatePagePaneText(_("Finished Debugging"),_("Debugging"))
        self.Execute()
        
    def CheckPortAvailable(self):
        
        if not PythonDebuggerUI.PortAvailable(int(self._debuggerBreakPort)):
            old_debuggerBreakPort = self._debuggerBreakPort
            self._debuggerPort = str(PythonDebuggerUI.GetAvailablePort())
            utils.get_logger().warn("debugger break server port %s is not available,will use new port %s",old_debuggerBreakPort,self._debuggerPort)
        else:
            utils.get_logger().debug("when restart debugger ,break server port %s is still available",self._debuggerBreakPort)

        if not PythonDebuggerUI.PortAvailable(int(self._guiPort)):
            old_guiPort = self._guiPort
            self._guiPort = str(PythonDebuggerUI.GetAvailablePort())
            utils.get_logger().warn("debugger gui server port %s is not available,will use new port %s",old_guiPort,self._guiPort)
        else:
            utils.get_logger().debug("when restart debugger ,gui server port %s is still available",self._guiPort)
            
        if not PythonDebuggerUI.PortAvailable(int(self._debuggerPort)):
            old_debuggerPort = self._debuggerPort
            self._debuggerPort = str(PythonDebuggerUI.GetAvailablePort())
            utils.get_logger().warn("debugger server port %s is not available,will use new port %s",old_debuggerPort,self._debuggerPort)
        else:
            utils.get_logger().debug("when restart debugger ,debugger server port %s is still available",self._debuggerPort)
            

class BaseFramesUI:
    
    THING_COLUMN_WIDTH = 175
    def __init__(self, output):
        self._output = output
        self._debugger = self._output._debugger

    def ExecuteCommand(self, command):
        assert False, "ExecuteCommand not overridden"

    def ClearWhileRunning(self):
        self.stackFrameTab._framesChoiceCtrl['values'] = ()
        self.stackFrameTab._framesChoiceCtrl['state'] = tk.DISABLED
        root = self.stackFrameTab._root
        self.stackFrameTab.DeleteChildren(root)
        self.inspectConsoleTab._cmdInput["state"] = tk.DISABLED
        self.inspectConsoleTab._cmdOutput["state"] = tk.DISABLED

    def LoadFramesList(self, framesXML):
        assert False, "LoadFramesList not overridden"

    def AppendText(self, event):
        self._output.AppendText(event)

    def AppendErrorText(self, event):
        self._output.AppendErrorText(event)

class PythonFramesUI(BaseFramesUI):
    def __init__(self, output):
        BaseFramesUI.__init__(self, output)
        #强制显示断点调式有关的视图
        self.breakPointsTab = GetApp().MainFrame.GetCommonView(consts.BREAKPOINTS_TAB_NAME)
        self.stackFrameTab = GetApp().MainFrame.GetCommonView(consts.STACKFRAME_TAB_NAME)
        self.inspectConsoleTab = GetApp().MainFrame.GetCommonView(consts.INTERACTCONSOLE_TAB_NAME)
        self.watchsTab = GetApp().MainFrame.GetCommonView(consts.WATCH_TAB_NAME)
        
    def SetExecutor(self,executor):
        self._textCtrl.SetExecutor(executor)

    def ExecuteCommand(self, command):
        '''
            在交互窗口中执行解释器命令,并将执行的结果反馈到堆栈窗口中
        '''
        self.inspectConsoleTab.AppendText(">>> " + command + "\n",tags = ("io",'stdout'))
        retval = self._output._callback._debuggerServer.execute_in_frame(self.stackFrameTab.frameValue.get(), command)
        self.inspectConsoleTab.AppendText(str(retval) + "\n",tags = ("io",'stderr'))
        # Refresh the tree view in case this command resulted in changes there. TODO: Need to reopen tree items.
        self.stackFrameTab.PopulateTreeFromFrameMessage(self.stackFrameTab.frameValue.get())

    def AddWatchExpression(self,name,expression,quick_watch):
        if quick_watch:
            title = _("Quick Add a Watch")
        else:
            title = _("Add a Watch")
        watch_obj = watchs.Watch.CreateWatch(name,expression)
        if hasattr(self.stackFrameTab, '_parentChain'):
            wd = watchs.WatchDialog(GetApp().GetTopWindow(),title , self.stackFrameTab._parentChain,watch_obj=watch_obj,is_quick_watch=quick_watch)
        else:
            wd = watchs.WatchDialog(GetApp().GetTopWindow(), title, None,watch_obj=watch_obj,is_quick_watch=quick_watch)
        if wd.ShowModal() == constants.ID_OK:
            watch_obj = wd.GetSettings()
            self.AddtoWatchExpression(watch_obj.Name,watch_obj.Expression)
            
    def AddtoWatchExpression(self,name,expression):
        watch_obj = watchs.Watch.CreateWatch(name,expression)
        if not BaseDebuggerUI.DebuggerRunning() or not self.stackFrameTab.HasStack():
            self.watchsTab.AppendErrorWatch(watch_obj,self.watchsTab.GetRootItem())
        else:
            nodeList = self.stackFrameTab.GetWatchList(watch_obj)
            if len(nodeList) == 1:
                watchValue = nodeList[0].childNodes[0].getAttribute("value")
                self.watchsTab.AddWatch(nodeList[0].childNodes[0],watch_obj,self.watchsTab.GetRootItem())
            
    #when step next,into,out action,will update watchs value
    def UpdateWatch(self,watch_obj,item):
        nodeList = self.stackFrameTab.GetWatchList(watch_obj)
        if len(nodeList) == 1:
            watchValue = nodeList[0].childNodes[0].getAttribute("value")
            self.watchsTab.UpdateWatch(nodeList[0].childNodes[0],watch_obj,item)
            
    def UpdateWatchs(self,reset=False):
        if not reset:
            self.watchsTab.UpdateWatchs()
        else:
            self.ResetWatchs()
        
    def ResetWatchs(self):
        self.watchsTab.ResetWatchs()

    def SynchCurrentLine(self,file,line):
        self._output.SynchCurrentLine( file, int(line) )

    def LoadFramesList(self, framesXML):
        GetApp().configure(cursor="circle")
        try:
            self.inspectConsoleTab._cmdInput["state"] = tk.NORMAL
            self.inspectConsoleTab._cmdOutput["state"] = tk.NORMAL
            try:
                domDoc = parseString(framesXML)
                self.stackFrameTab.LoadFrame(domDoc)
            except:
                utils.get_logger().exception('')
        finally:
            GetApp().configure(cursor="")
            
    def attempt_introspection(self,message,chain):
        return self._output._callback._debuggerServer.attempt_introspection(message, chain)
        
    def request_frame_document(self,message):
        return self._output._callback._debuggerServer.request_frame_document(message)
        
    def add_watch(self,message,watch_data):
        return self._output._callback._debuggerServer.add_watch(watch_data.Name, watch_data.Expression, message, watch_data.IsRunOnce())

class Interaction:
    def __init__(self, message, framesXML,  info=None, quit=False):
        self._framesXML = framesXML
        self._message = message
        self._info = info
        self._quit = quit

    def getFramesXML(self):
        return self._framesXML

    def getMessage(self):
        return self._message

    def getInfo(self):
        return self._info

    def getQuit(self):
        return self._quit

class RequestHandlerThread(threading.Thread):
    def __init__(self,debuggerUI, queue, address):
        threading.Thread.__init__(self)
        self._keepGoing = True
        self._queue = queue
        self._address = address
        self._server = AGXMLRPCServer(self._address,logRequests=0)
        self._server.register_function(self.interaction)
        self._server.register_function(self.quit)
        self._server.register_function(self.dummyOperation)
        self._server.register_function(self.request_input)
        self._debuggerUI = debuggerUI
        self._input_text = ""
        if _VERBOSE: print ("RequestHandlerThread on fileno %s" % str(self._server.fileno()))

    def run(self):
        while self._keepGoing:
            try:
                self._server.handle_request()
            except:
                utils.get_logger().exception('')
                self._keepGoing = False
        if _VERBOSE: print ("Exiting Request Handler Thread.")

    def interaction(self, message, frameXML, info):
        if _VERBOSE: print ("In RequestHandlerThread.interaction -- adding to queue")
        interaction = Interaction(message, frameXML, info)
        self._queue.put(interaction)
        return ""

    def quit(self):
        interaction = Interaction(None, None, info=None, quit=True)
        self._queue.put(interaction)
        return ""

    def dummyOperation(self):
        return ""
        
    
    def request_input(self):
        #create a thread event
        self.input_evt = threading.Event()
        self.get_input_text()
        #block until the event activated
        self.input_evt.wait()
        return self._input_text
        
    @utils.call_after
    def get_input_text(self):
        text = tkSimpleDialog.askstring(
            _("Enter input"),
            _("Enter the input text:")
        )
        if text:
            self._input_text = text
            self._debuggerUI._textCtrl.AddInputText(self._input_text)
        else:
            ##simulate the keyboard interrupt when cancel button is pressed
            self._input_text = None
        #activated the event,then the input will return
        self.input_evt.set()

    def AskToStop(self):
        if self._server is not None:
            try:
                # This is a really ugly way to make sure this thread isn't blocked in
                # handle_request.
                url = 'http://' + self._address[0] + ':' + str(self._address[1]) + '/'
                tempServer = xmlrpclib.ServerProxy(url, allow_none=1)
                tempServer.dummyOperation()
                self._keepGoing = False
            except:
                utils.get_logger().exception('')
            self._server.server_close()


class RequestBreakThread(threading.Thread):
        def __init__(self, server, interrupt=False, pushBreakpoints=False, breakDict=None, kill=False):
            threading.Thread.__init__(self)
            self._server = server

            self._interrupt = interrupt
            self._pushBreakpoints = pushBreakpoints
            self._breakDict = breakDict
            self._kill = kill

        def run(self):
            try:
                if _VERBOSE: print ("RequestBreakThread, before call")
                if self._interrupt:
                    self._server.break_requested()
                if self._pushBreakpoints:
                    self._server.update_breakpoints(xmlrpclib.Binary(pickle.dumps(self._breakDict)))
                if self._kill:
                    try:
                        self._server.die()
                    except:
                        pass
                if _VERBOSE: print ("RequestBreakThread, after call")
            except:
                utils.get_logger().exception('')

class DebuggerOperationThread(threading.Thread):
        def __init__(self, function):
            threading.Thread.__init__(self)
            self._function = function

        def run(self):
            if _VERBOSE: print ("In DOT, before call")
            try:
                self._function()
            except:
                utils.get_logger().exception('')
            if _VERBOSE:
                print ("In DOT, after call")

class BaseDebuggerCallback(object):

    def Start(self):
        assert False, "Start not overridden"

    def ShutdownServer(self):
        assert False, "ShutdownServer not overridden"

    def BreakExecution(self):
        assert False, "BreakExecution not overridden"

    def SingleStep(self,callback=None):
        assert False, "SingleStep not overridden"

    def Next(self,callback=None):
        assert False, "Next not overridden"

    def Continue(self):
        assert False, "Start not overridden"

    def Return(self,callback=None):
        assert False, "Return not overridden"

    def PushBreakpoints(self):
        assert False, "PushBreakpoints not overridden"

class PythonDebuggerCallback(BaseDebuggerCallback):

    def __init__(self, host, port, debugger_url, break_url, debuggerUI, autoContinue=False):
        if _VERBOSE: print ("+++++++ Creating server on port, ", str(port))
        self._timer = None
        self._queue = Queue.Queue(50)
        self._host = host
        self._port = int(port)
        threading._VERBOSE = _VERBOSE
        self._serverHandlerThread = RequestHandlerThread(debuggerUI,self._queue, (self._host, self._port))

        self._debugger_url = debugger_url
        self._debuggerServer = None
        self._waiting = False
        self._debuggerUI = debuggerUI
        self._break_url = break_url
        self._breakServer = None
        self._firstInteraction = True
        self._pendingBreak = False
        self._autoContinue = autoContinue

    def Start(self):
        self._serverHandlerThread.start()

    def ShutdownServer(self):
        #rbt = RequestBreakThread(self._breakServer, kill=True)
        #rbt.start()
        self._waiting = False
        if self._serverHandlerThread:
            self._serverHandlerThread.AskToStop()
            self._serverHandlerThread = None
            
    def CheckBreakServer(self):
        if self._breakServer is None:
            messagebox.showerror(GetApp().GetAppName(),_("Could not connect to break server!"))
            return False
        return True

    def BreakExecution(self):
        if not self.CheckBreakServer():
            return
        rbt = RequestBreakThread(self._breakServer, interrupt=True)
        rbt.start()

    def SingleStep(self,callback):
        '''
            进入当前方法
        '''
        #执行下一步调试之前,在没有返回之前需要先禁止一些东西
        self._debuggerUI.DisableWhileDebuggerRunning()
        self._debuggerServer.set_step() # Figure out where to set allowNone
        self.WaitForRPC(callback)

    def Next(self,callback):
        '''
            运行下一行代码
        '''
        #执行下一步调试之前,在没有返回之前需要先禁止一些东西
        self._debuggerUI.DisableWhileDebuggerRunning()
        self._debuggerServer.set_next()
        self.WaitForRPC(callback)

    def Continue(self):
        self._debuggerUI.DisableWhileDebuggerRunning()
        self._debuggerServer.set_continue()
        self.WaitForRPC()

    def Return(self,callback):
        '''
            退出当前方法，返回到调用层
        '''
        #执行下一步调试之前,在没有返回之前需要先禁止一些东西
        self._debuggerUI.DisableWhileDebuggerRunning()
        self._debuggerServer.set_return()
        self.WaitForRPC(callback)

    def ReadQueue(self):
        if self._queue.qsize():
            try:
                item = self._queue.get_nowait()
                if item.getQuit():
                    self.interaction(None, None, None, True)
                else:
                    data = bz2.decompress(item.getFramesXML().data)
                    self.interaction(item.getMessage().data, data, item.getInfo(), False)
            except Queue.Empty:
                pass

    def PushBreakpoints(self):
        
        if not self.CheckBreakServer():
            return
            
        rbt = RequestBreakThread(self._breakServer, pushBreakpoints=True, breakDict=self._debuggerUI.framesTab.breakPointsTab.GetMasterBreakpointDict())
        rbt.start()
        
    def PushExceptionBreakpoints(self):
        self._debuggerServer.set_all_exceptions(self._service.GetExceptions())

    def WaitForRPC(self,callback=None):
        self._waiting = True
        self.RotateForRpc(callback)
        
    def RotateForRpc(self,callback):
        if not self._waiting:
            utils.get_logger().debug("Exiting WaitForRPC.")
            if callback:
                utils.get_logger().debug("After exit rpc,callback.....")
                callback()
            return
        #1000毫秒设置的正好,不能设置得太长也不能设置得太短,设置太短程序会很卡
        self._debuggerUI.after(1000,self.RotateForRpc,*[callback])
        try:
            self.ReadQueue()
            import time
            time.sleep(0.02)
        except:
            utils.get_logger().exception('')

    def interaction(self, message, frameXML, info, quit):

        #This method should be hit as the debugger starts.
        #if the debugger starts.then show the debugger menu
        if self._firstInteraction:
            #断点调试时显示断点调式有关的菜单
            self._debuggerUI._debugger.ShowHideDebuggerMenu()
            self._firstInteraction = False
            self._debuggerServer = xmlrpclib.ServerProxy(self._debugger_url,  allow_none=1)
            self._breakServer = xmlrpclib.ServerProxy(self._break_url, allow_none=1)
            self.PushBreakpoints()
            if self._debuggerUI._debugger.GetExceptions():
                self.PushExceptionBreakpoints()
        self._waiting = False
        if _VERBOSE: print ("+"*40)
        #quit gui server
        if(quit):
            #whhen quit gui server stop the debugger execution
            self._debuggerUI.StopExecution()
            return ""
        if(info != ""):
            utils.get_logger().error("Hit interaction with exception")
            #self._debuggerUI.StopExecution()
            self._debuggerUI.SetStatusText("Got exception: " + str(info))
        else:
            if _VERBOSE: print ("Hit interaction no exception")
        #if not self._autoContinue:
        self._debuggerUI.SetStatusText(message)
        if not self._autoContinue:
            self._debuggerUI.LoadPythonFramesList(frameXML)
            self._debuggerUI.EnableWhileDebuggerStopped()

        if self._autoContinue:
            self._timer = pytimer.PyTimer(self.DoContinue)
            self._autoContinue = False
            self._timer.Start(0.25)
        if _VERBOSE: print ("+"*40)

    def DoContinue(self):
        self._timer.Stop()
        GetApp().event_generate(EVT_DEBUG_INTERNAL)
        if _VERBOSE: print ("Event Continue posted")

    def SendRunEvent(self):
        class SendEventThread(threading.Thread):
            def __init__(self):
                threading.Thread.__init__(self)

            def run(self):
                dbgService = wx.GetApp().GetService(DebuggerService)
                evt = DebugInternalWebServer()
                evt.SetId(DebuggerService.DEBUG_WEBSERVER_NOW_RUN_PROJECT_ID)
                wx.PostEvent(dbgService._frame, evt)
                print ("Event posted")
        set = SendEventThread()
        set.start()
        
    def IsWait(self):
        return self._waiting
        
    def StopWait(self):
        assert(self._waiting)
        self.ShutdownServer()
