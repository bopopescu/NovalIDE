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
from tkinter import ttk,messagebox,filedialog
import sys
import time
try:
    from SimpleXMLRPCServer import SimpleXMLRPCServer
    import xmlrpclib
    import Queue
    import SocketServer
   # import StringIO
except ImportError:
    from xmlrpc.server import SimpleXMLRPCServer
    import xmlrpc.client as xmlrpclib
    import queue as Queue
    import socketserver as SocketServer

import os
import threading
import noval.project.basemodel as projectlib
import types
from xml.dom.minidom import parse, parseString
import bz2
import pickle
import traceback
import noval.util.apputils as sysutilslib
import subprocess
import shutil
import noval.python.interpreter.interpreter as pythoninterpreter
import noval.syntax.lang as lang
import noval.python.debugger.output as debugoutput
import noval.util.strutils as strutils
import noval.python.parser.utils as parserutils
import copy
import noval.util.appdirs as appdirs
import noval.util.utils as utils
import noval.python.project.runconfig as runconfig
import noval.python.debugger.breakpoints as breakpoints
import noval.python.debugger.watchs as watchs
import noval.python.debugger.stacksframe as stacksframe
import noval.python.debugger.inspectconsole as inspectconsole
import pickle
import noval.project.baseconfig as baseconfig
import noval.util.timer as pytimer
import uuid
import noval.constants as constants
import noval.ui_base as ui_base
import noval.ui_common as ui_common
if utils.is_py2():
    import noval.python.debugger.debuggerharness as debuggerharness
elif utils.is_py3_plus():
    import noval.python.debugger.debuggerharness3 as debuggerharness
import noval.util.fileutils as fileutils
import noval.python.pyutils as pyutils
import noval.terminal as terminal
import noval.menu as tkmenu
import noval.consts as consts
import noval.python.project.runconfiguration as runconfiguration
import noval.project.executor as executor
from noval.project.debugger import *
from noval.python.debugger.output import *
import tempfile
import noval.core as core

#VERBOSE mode will invoke threading.Thread _VERBOSE,which will print a lot of thread debug text on screen
_VERBOSE = False
_WATCHES_ON = True

EVT_DEBUG_INTERNAL = "EVT_DEBUG_INTERNAL"

class CommonExecutorMixin:
    def __init__(self):
        self.is_windows_application = self._run_parameter.IsWindowsApplication()
        #如果是windows应用程序则使用pythonw.exe解释器来运行程序
        if self.is_windows_application:
            self._path = self._run_parameter.Interpreter.WindowPath
        #否则默认使用python.exe
        else:
            self._path = self._run_parameter.Interpreter.Path
        self._cmd = strutils.emphasis_path(self._path)
        if self._run_parameter.InterpreterOption and self._run_parameter.InterpreterOption != ' ':
            self._cmd = self._cmd + " " + self._run_parameter.InterpreterOption

class PythonExecutor(executor.Executor,CommonExecutorMixin):
    def GetPythonExecutablePath():
        current_interpreter = GetApp().GetCurrentInterpreter()
        if current_interpreter:
            return current_interpreter.Path
        messagebox.showinfo( _("Python Executable Location Unknown"),_("To proceed we need to know the location of the python.exe you would like to use.\nTo set this, go to Tools-->Options and use the 'Python Inpterpreter' panel to configuration a interpreter.\n"))
        ui_common.ShowInterpreterConfigurationPage()
        return None
    GetPythonExecutablePath = staticmethod(GetPythonExecutablePath)

    def __init__(self, run_parameter, wxComponent, callbackOnExit=None,source=executor.SOURCE_DEBUG,cmd_contain_path = True):
        executor.Executor.__init__(self,run_parameter,wxComponent,callbackOnExit,source)
        assert(self._run_parameter.Interpreter != None)
        CommonExecutorMixin.__init__(self)
        if cmd_contain_path:
            self._cmd += self.spaceAndQuote(self._run_parameter.FilePath)

        self._stdOutReader = None
        self._stdErrReader = None
        self._process = None

class PythonrunExecutor(executor.TerminalExecutor,CommonExecutorMixin):
    def __init__(self, run_parameter):
        executor.TerminalExecutor.__init__(self,run_parameter)
        CommonExecutorMixin.__init__(self)
        self._cmd += self.spaceAndQuote(self._run_parameter.FilePath)

    def Execute(self):
        command = self.GetExecuteCommand()
        #点击Run按钮或菜单时,如果是windows应用程序则直接使用pythonw.exe解释器来运行程序
        if self.is_windows_application:
            utils.get_logger().debug("start run executable: %s",command)
            #TODO 不知道为什么在调用python2.7解释器时必须重定向输出到文件才能工作正常
            temp_file = tempfile.TemporaryFile()
            subprocess.Popen(command,shell = False,cwd=self.GetStartupPath(),env=self._run_parameter.Environment,stdout=temp_file.fileno(), stderr=temp_file.fileno())
        #否则在控制台终端中运行程序,并且在程序运行结束时暂停,方便用户查看运行输出结果
        else:
            executor.TerminalExecutor.Execute(self)
        
    #Better way to do this? Quotes needed for windows file paths.
class PythonDebuggerExecutor(PythonExecutor):
    
    def __init__(self, debugger_fileName,run_parameter, wxComponent, arg1=None, arg2=None, arg3=None, arg4=None, arg5=None, arg6=None, arg7=None, arg8=None, arg9=None, callbackOnExit=None):
        
        super(PythonDebuggerExecutor,self).__init__(run_parameter,wxComponent,callbackOnExit,cmd_contain_path=False)
        self._debugger_fileName = debugger_fileName
        self._cmd += self.spaceAndQuote(self._debugger_fileName)
        
        if(arg1 != None):
            self._cmd += self.spaceAndQuote(arg1)
        if(arg2 != None):
            self._cmd += self.spaceAndQuote(arg2)
        if(arg3 != None):
            self._cmd += self.spaceAndQuote(arg3)
        if(arg4 != None):
            self._cmd += self.spaceAndQuote(arg4)
        if(arg5 != None):
            self._cmd += self.spaceAndQuote(arg5)
        if(arg6 != None):
            self._cmd += self.spaceAndQuote(arg6)
        if(arg7 != None):
            self._cmd += self.spaceAndQuote(arg7)
        if(arg8 != None):
            self._cmd += self.spaceAndQuote(arg8)
        if(arg9 != None):
            self._cmd += self.spaceAndQuote(arg9)

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
        RunCommandUI.runners = []
    ShutdownAllRunners = staticmethod(ShutdownAllRunners)
    
    @staticmethod
    def StopAndRemoveAllUI():
        return GetApp().GetDebugger().CloseAllPages()

    def __init__(self,parent, debugger,run_parameter,append_runner=True,toolbar_orient=tk.VERTICAL):
        #toolbar使用垂直布局
        CommonRunCommandUI.__init__(self, parent,debugger,run_parameter,toolbar_orient=toolbar_orient)
        self._noteBook = parent
        threading._VERBOSE = _VERBOSE
        if append_runner:
            RunCommandUI.runners.append(self)
        #重写关闭窗口事件,关闭窗口时检查进程是否在运行
        self.master.close = self.Close

    def GetOutputviewClass(self):
        return DebugOutputView

    def __del__(self):
        # See comment on PythonDebuggerUI.StopExecution
        CommonRunCommandUI.__del__(self)
        RunCommandUI.runners.remove(self)

    def GetExecutorClass(self):
        #python执行器
        return PythonExecutor
    
    def IsProcessRunning(self):
        process_runners = [runner for runner in self.runners if not runner.Stopped]
        return True if len(process_runners) > 0 else False
        
    def UpdateAllRunnerTerminateAllUI(self):
        for runner in self.runners:
            runner.UpdateTerminateAllUI()
        
    def ExecutorFinished(self,stopped=True):
        self.UpdateFinishedPagePaneText()
        CommonRunCommandUI.ExecutorFinished(self,stopped=stopped)
            
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
        self.next_bmp = GetApp().GetImage("python/debugger/step_next.png")
        self._tb.AddButton( constants.ID_STEP_NEXT, self.next_bmp, _("Step to next line"),self.OnNext,accelerator=GetApp().Menubar.GetRunMenu().FindMenuItem(constants.ID_STEP_NEXT).accelerator)

        self.step_bmp = GetApp().GetImage("python/debugger/step_into.png")
        self._tb.AddButton( constants.ID_STEP_INTO, self.step_bmp, _("Step in"),self.OnSingleStep,accelerator=GetApp().Menubar.GetRunMenu().FindMenuItem(constants.ID_STEP_INTO).accelerator)

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

    def OnSingleStep(self):
        self._callback.SingleStep()

    def OnContinue(self,event=None):
        self._callback.Continue()

    def OnStepOut(self):
        self._callback.Return()

    def OnNext(self):
        self._callback.Next()

    def BreakPointChange(self):
        if not self._stopped:
            self._callback.PushBreakpoints()
        self.framesTab.PopulateBPList()

    def __del__(self):
        # See comment on PythonDebuggerUI.StopExecution
        self.StopExecution(None)

    def DisableWhileDebuggerRunning(self):
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
        if self._toolEnabled:
            self.DisableWhileDebuggerRunning()
            self._tb.EnableTool(constants.ID_BREAK_INTO_DEBUGGER, False)
            if self.run_menu.FindMenuItem(constants.ID_BREAK_INTO_DEBUGGER):
                self.run_menu.Enable(constants.ID_BREAK_INTO_DEBUGGER,False)
            self._tb.EnableTool(self.KILL_PROCESS_ID, False)
            if self.run_menu.FindMenuItem(constants.ID_TERMINATE_DEBUGGER):
                self.run_menu.Enable(constants.ID_TERMINATE_DEBUGGER,False)

    def ExecutorFinished(self):
        if _VERBOSE: print ("In ExectorFinished")
        try:
            self.DisableAfterStop()
            self.UpdatePagePaneText(_("Debugging"), _("Finished Debugging"))
            self._tb.EnableTool(self.KILL_PROCESS_ID, False)
        except wx._core.PyDeadObjectError:
            utils.GetLogger().warn("BaseDebuggerUI object has been deleted, attribute access no longer allowed when finish debug executor")
            return
        #调式完成隐藏断点调式有关的菜单
        self._debugger.ShowHideDebuggerMenu(False)
        if self._restarted:
            wx.MilliSleep(250)
            self.RestartDebuggerProcess()
            self._restarted = False

    def SetStatusText(self, text):
        utils.update_statusbar(text)

    def BreakExecution(self):
        if not BaseDebuggerUI.DebuggerRunning():
            wx.MessageBox(_("Debugger has been stopped."),style=wx.OK|wx.ICON_ERROR)
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
            doc = GetApp().GetDocumentManager().CreateDocument(filename, core.DOC_SILENT)[0]
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
        if self in BaseDebuggerUI.debuggers:
            BaseDebuggerUI.debuggers.remove(self)
        self.RemoveUI()
        if self._callback.IsWait():
            utils.get_logger().warn("debugger callback is still wait for rpc when debugger stoped.will stop manualy")
            self._callback.StopWait()
        return True

    def OnAddWatch(self):
        self.framesTab.OnAddWatch()
            
    def OnQuickAddWatch(self):
        self.framesTab.QuickAddWatch()

    def MakeFramesUI(self):
        assert False, "MakeFramesUI not overridden"

    def OnClearOutput(self):
        self.ClearOutput(None)

    def SwitchToOutputTab(self):
        self.framesTab.SwitchToOutputTab()
        
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
        wx.MessageBox(_("Out of ports for debugging!  Please restart the application builder.\nIf that does not work, check for and remove running instances of python."), _("Out of Ports"))
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
            tp,val,tb = sys.exc_info()
            if _VERBOSE: traceback.print_exception(tp, val, tb)
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
                tp,val,tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)

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
                tp,val,tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)


    def MakeFramesUI(self):
        panel = PythonFramesUI(self)
        return panel
        
    def UpdateWatch(self,watch_obj,item):
        self.framesTab.UpdateWatch(watch_obj,item)
        
    def UpdateWatchs(self,reset=False):
        self.framesTab.UpdateWatchs(reset)

    def OnSingleStep(self):
        BaseDebuggerUI.OnSingleStep(self)
        self.UpdateWatchs()

    def OnContinue(self,event=None):
        BaseDebuggerUI.OnContinue(self,event)

    def OnStepOut(self):
        BaseDebuggerUI.OnStepOut(self)
        self.UpdateWatchs()

    def OnNext(self):
        BaseDebuggerUI.OnNext(self)
        self.UpdateWatchs()

    def DisableWhileDebuggerRunning(self):
        BaseDebuggerUI.DisableWhileDebuggerRunning(self)
        #when process is running normal,reset the watchs
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
            self.StopExecution(None)
        else:
            self.RestartDebuggerProcess()
            
    def RestartDebuggerProcess(self):
        
        if BaseDebuggerUI.DebuggerRunning():
            wx.MessageBox(_("A debugger is already running. Please shut down the other debugger first."), _("Debugger Running"))
            return

        self.OnClearOutput(None)
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
            utils.GetLogger().warn("debugger break server port %s is not available,will use new port %s",old_debuggerBreakPort,self._debuggerPort)
        else:
            utils.GetLogger().debug("when restart debugger ,break server port %s is still available",self._debuggerBreakPort)

        if not PythonDebuggerUI.PortAvailable(int(self._guiPort)):
            old_guiPort = self._guiPort
            self._guiPort = str(PythonDebuggerUI.GetAvailablePort())
            utils.GetLogger().warn("debugger gui server port %s is not available,will use new port %s",old_guiPort,self._guiPort)
        else:
            utils.GetLogger().debug("when restart debugger ,gui server port %s is still available",self._guiPort)
            
        if not PythonDebuggerUI.PortAvailable(int(self._debuggerPort)):
            old_debuggerPort = self._debuggerPort
            self._debuggerPort = str(PythonDebuggerUI.GetAvailablePort())
            utils.GetLogger().warn("debugger server port %s is not available,will use new port %s",old_debuggerPort,self._debuggerPort)
        else:
            utils.GetLogger().debug("when restart debugger ,debugger server port %s is still available",self._debuggerPort)

class BaseFramesUI:
    
    THING_COLUMN_WIDTH = 175
    def __init__(self, output):
        self._output = output
        self._debugger = self._output._debugger

    def PopulateBPList(self):
        self.breakPointsTab.PopulateBPList()

    def ExecuteCommand(self, command):
        assert False, "ExecuteCommand not overridden"

    def OnRightClick(self, event):
        assert False, "OnRightClick not overridden"

    def ClearWhileRunning(self):
        self.stackFrameTab._framesChoiceCtrl['values'] = ()
        self.stackFrameTab._framesChoiceCtrl['state'] = tk.DISABLED
        root = self.stackFrameTab._root
        self.stackFrameTab.DeleteChildren(root)
        self.inspectConsoleTab._cmdInput["state"] = tk.DISABLED
        self.inspectConsoleTab._cmdOutput["state"] = tk.DISABLED

    def OnListRightClick(self, event):
        if not hasattr(self, "syncFrameID"):
            self.syncFrameID = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnSyncFrame, id=self.syncFrameID)
        menu = wx.Menu()
        item = wx.MenuItem(menu, self.syncFrameID, "Goto Source Line")
        menu.AppendItem(item)
        self.PopupMenu(menu, event.GetPosition())
        menu.Destroy()

    def OnSyncFrame(self, event):
        assert False, "OnSyncFrame not overridden"

    def LoadFramesList(self, framesXML):
        assert False, "LoadFramesList not overridden"

    def ListItemSelected(self, event):
        assert False, "ListItemSelected not overridden"

    def PopulateTreeFromFrameMessage(self, message):
        assert False, "PopulateTreeFromFrameMessage not overridden"

    def IntrospectCallback(self, event):
        assert False, "IntrospectCallback not overridden"

    def AppendText(self, event):
        self._output.AppendText(event)

    def AppendErrorText(self, event):
        self._output.AppendErrorText(event)

    def ClearOutput(self, event):
        self._output.GetOutputCtrl().ClearOutput()

    def SwitchToOutputTab(self):
        self._notebook.SetSelection(0)

class PythonFramesUI(BaseFramesUI):
    def __init__(self, output):
        BaseFramesUI.__init__(self, output)
        #强制显示断点调式有关的视图
        self.breakPointsTab = GetApp().MainFrame.GetCommonView(breakpoints.BREAKPOINTS_TAB_NAME)
        self.stackFrameTab = GetApp().MainFrame.GetCommonView(stacksframe.STACKFRAME_TAB_NAME)
        self.inspectConsoleTab = GetApp().MainFrame.GetCommonView(inspectconsole.INTERACTCONSOLE_TAB_NAME)
        self.watchsTab = GetApp().MainFrame.GetCommonView(watchs.WATCH_TAB_NAME)
        
    def SetExecutor(self,executor):
        self._textCtrl.SetExecutor(executor)

    def ExecuteCommand(self, command):
        retval = self._ui._callback._debuggerServer.execute_in_frame(self._framesChoiceCtrl.GetStringSelection(), command)
        self._cmdOutput.AppendText(str(retval) + "\n")
        # Refresh the tree view in case this command resulted in changes there. TODO: Need to reopen tree items.
        self.PopulateTreeFromFrameMessage(self._framesChoiceCtrl.GetStringSelection())

    def OnRightClick(self, event):
        #Refactor this...
        self._introspectItem = event.GetItem()
        self._parentChain = self.GetItemChain(event.GetItem())
        watchOnly = len(self._parentChain) < 1
        if not _WATCHES_ON and watchOnly:
            return
        menu = wx.Menu()
        if _WATCHES_ON:
            if not hasattr(self, "watchID"):
                self.watchID = wx.NewId()
                self.Bind(wx.EVT_MENU, self.OnAddWatch, id=self.watchID)
            item = wx.MenuItem(menu, self.watchID, _("Add a Watch"))
            item.SetBitmap(Watchs.getAddWatchBitmap())
            menu.AppendItem(item)
            menu.AppendSeparator()
        if not watchOnly:
            AddWatchId = wx.NewId()
            item = wx.MenuItem(menu, AddWatchId, _("Add to Watch"))
            item.SetBitmap(Watchs.getAddtoWatchBitmap())
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnAddToWatch, id=AddWatchId)
            
            if not hasattr(self, "viewID"):
                self.viewID = wx.NewId()
                self.Bind(wx.EVT_MENU, self.OnView, id=self.viewID)
            item = wx.MenuItem(menu, self.viewID, _("View in Dialog"))
            menu.AppendItem(item)
            if not hasattr(self, "toInteractID"):
                self.toInteractID = wx.NewId()
                self.Bind(wx.EVT_MENU, self.OnSendToInteract, id=self.toInteractID)
            item = wx.MenuItem(menu, self.toInteractID, _("Send to Interact"))
            menu.AppendItem(item)

        offset = wx.Point(x=0, y=20)
        menuSpot = event.GetPoint() + offset
        self._treeCtrl.PopupMenu(menu, menuSpot)
        menu.Destroy()
        self._parentChain = None
        self._introspectItem = None

    def GetItemChain(self, item):
        parentChain = []
        if item:
            if _VERBOSE: print ('Exploding: %s' % self._treeCtrl.GetItemText(item, 0))
            while item != self._root:
                text = self._treeCtrl.GetItemText(item, 0)
                if _VERBOSE: print ("Appending ", text)
                parentChain.append(text)
                item = self._treeCtrl.GetItemParent(item)
            parentChain.reverse()
        return parentChain

    def OnView(self, event):
        title = self._treeCtrl.GetItemText(self._introspectItem,0)
        value = self._treeCtrl.GetItemText(self._introspectItem,1)
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, value, title, style=wx.DD_DEFAULT_STYLE | wx.RESIZE_BORDER)
        dlg.Show()

    def OnSendToInteract(self, event):
        value = ""
        prevItem = ""
        for item in self._parentChain:

            if item.find(prevItem + '[') != -1:
               value += item[item.find('['):]
               continue
            if value != "":
                value = value + '.'
            if item == 'globals':
                item = 'globals()'
            if item != 'locals':
                value += item
                prevItem = item
        print (value)
        self.ExecuteCommand(value)
        #swith to interact tab page
        self._notebook.SetSelection(1)

    def OnAddWatch(self):
        self.AddWatch()
        
    def AddWatch(self,watch_obj=None):
        try:
            if hasattr(self, '_parentChain'):
                wd = Watchs.WatchDialog(wx.GetApp().GetTopWindow(), _("Add a Watch"), self._parentChain,watch_obj=watch_obj)
            else:
                wd = watchs.WatchDialog(GetApp().GetTopWindow(), _("Add a Watch"), None,watch_obj=watch_obj)
            if wd.ShowModal() == constants.ID_OK:
                watch_obj = wd.GetSettings()
                self.AddtoWatch(watch_obj)
        except:
            tp, val, tb = sys.exc_info()
            traceback.print_exception(tp, val, tb)
            
    def OnAddToWatch(self,event):
        name = self._treeCtrl.GetItemText(self._introspectItem,0)
        watch_obj = Watchs.Watch.CreateWatch(name)
        self.AddtoWatch(watch_obj)
        
    def QuickAddWatch(self,watch_obj=None):
        wd = watchs.WatchDialog(GetApp().GetTopWindow(), _("Quick Add a Watch"), None,True,watch_obj)
        if wd.ShowModal() == constants.ID_OK:
            watch_obj = wd.GetSettings()
            self.AddtoWatch(watch_obj)
            
    def AddtoWatch(self,watch_obj):
        if not BaseDebuggerUI.DebuggerRunning() or not hasattr(self,"_stack"):
            self.watchsTab.AppendErrorWatch(watch_obj,self.watchsTab._treeCtrl.GetRootItem())
        else:
            frameNode = self._stack[int(self.currentItem)]
            message = frameNode.getAttribute("message")
            binType = self._ui._callback._debuggerServer.add_watch(watch_obj.Name, watch_obj.Expression, message, watch_obj.IsRunOnce())
            xmldoc = bz2.decompress(binType.data)
            domDoc = parseString(xmldoc)
            nodeList = domDoc.getElementsByTagName('watch')
            if len(nodeList) == 1:
                watchValue = nodeList[0].childNodes[0].getAttribute("value")
                self.watchsTab.AddWatch(nodeList[0].childNodes[0],watch_obj,self.watchsTab._treeCtrl.GetRootItem())
                ####self.watchsTab.AppendSubTreeFromNode(nodeList[0].childNodes[0],watch_obj.Name,self.watchsTab._treeCtrl.GetRootItem())
        #swith to watchs tab page
        self._notebook.SetSelection(3)
            
    #when step next,into,out action,will update watchs value
    def UpdateWatch(self,watch_obj,item):
        frameNode = self._stack[int(self.currentItem)]
        message = frameNode.getAttribute("message")
        binType = self._ui._callback._debuggerServer.add_watch(watch_obj.Name, watch_obj.Expression, message, watch_obj.IsRunOnce())
        xmldoc = bz2.decompress(binType.data)
        domDoc = parseString(xmldoc)
        nodeList = domDoc.getElementsByTagName('watch')
        if len(nodeList) == 1:
            watchValue = nodeList[0].childNodes[0].getAttribute("value")
            self.watchsTab.UpdateWatch(nodeList[0].childNodes[0],watch_obj,item)
            ####self.watchsTab.UpdateSubTreeFromNode(nodeList[0].childNodes[0],name,item)
            
    def UpdateWatchs(self,reset=False):
        if not reset:
            self.watchsTab.UpdateWatchs()
        else:
            self.ResetWatchs()
        
    def ResetWatchs(self):
        self.watchsTab.ResetWatchs()

    def OnIntrospect(self, event):
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))

        try:

            try:
                list = self._framesChoiceCtrl
                frameNode = self._stack[int(self.currentItem)]
                message = frameNode.getAttribute("message")
                binType = self._ui._callback._debuggerServer.attempt_introspection(message, self._parentChain)
                xmldoc = bz2.decompress(binType.data)
                domDoc = parseString(xmldoc)
                nodeList = domDoc.getElementsByTagName('replacement')
                replacementNode = nodeList.item(0)
                if len(replacementNode.childNodes):
                    thingToWalk = replacementNode.childNodes.item(0)
                    tree = self._treeCtrl
                    parent = tree.GetItemParent(self._introspectItem)
                    treeNode = self.AppendSubTreeFromNode(thingToWalk, thingToWalk.getAttribute('name'), parent, insertBefore=self._introspectItem)
                    if thingToWalk.getAttribute('name').find('[') == -1:
                        self._treeCtrl.SortChildren(treeNode)
                    self._treeCtrl.Expand(treeNode)
                    tree.Delete(self._introspectItem)
            except:
                tp,val,tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)

        finally:
            wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

    def OnSyncFrame(self, event):
        frameNode = self._stack[int(self.currentItem)]
        file = frameNode.getAttribute("file")
        line = frameNode.getAttribute("line")
        self._output.SynchCurrentLine( file, int(line) )

    def LoadFramesList(self, framesXML):
        GetApp().configure(cursor="circle")
        try:
            self.inspectConsoleTab._cmdInput["state"] = tk.NORMAL
            self.inspectConsoleTab._cmdOutput["state"] = tk.NORMAL
            try:
                domDoc = parseString(framesXML)
                frame_values = []
                self._stack = []
                nodeList = domDoc.getElementsByTagName('frame')
                frame_count = -1
                for index in range(0, nodeList.length):
                    frameNode = nodeList.item(index)
                    message = frameNode.getAttribute("message")
                    frame_values.append(message)
                    self._stack.append(frameNode)
                    frame_count += 1
                index = len(self._stack) - 1
                self.stackFrameTab._framesChoiceCtrl['values'] = frame_values
                self.stackFrameTab._framesChoiceCtrl.current(index)

                node = self._stack[index]
                self.currentItem = index
                self.PopulateTreeFromFrameNode(node)
                self.OnSyncFrame(None)

                frameNode = nodeList.item(index)
                file = frameNode.getAttribute("file")
                line = frameNode.getAttribute("line")
                self._output.SynchCurrentLine( file, int(line) )
            except:
                tp,val,tb=sys.exc_info()
                traceback.print_exception(tp, val, tb)

        finally:
            GetApp().configure(cursor="")


    def ListItemSelected(self, event):
        self.PopulateTreeFromFrameMessage(event.GetString())
        self.OnSyncFrame(None)

    def PopulateTreeFromFrameMessage(self, message):
        index = 0
        for node in self._stack:
            if node.getAttribute("message") == message:
                binType = self._ui._callback._debuggerServer.request_frame_document(message)
                xmldoc = bz2.decompress(binType.data)
                domDoc = parseString(xmldoc)
                nodeList = domDoc.getElementsByTagName('frame')
                self.currentItem = index
                if len(nodeList):
                    self.PopulateTreeFromFrameNode(nodeList[0])
                return
            index = index + 1

    def PopulateTreeFromFrameNode(self, frameNode):
        self.stackFrameTab._framesChoiceCtrl['state'] = 'readonly'
        tree = self.stackFrameTab.tree
        root = self.stackFrameTab._root
        self.stackFrameTab.DeleteChildren(root)
        children = frameNode.childNodes
        firstChild = None
        for index in range(0, children.length):
            subNode = children.item(index)
            treeNode = self.AppendSubTreeFromNode(subNode, subNode.getAttribute('name'), root)
            if not firstChild:
                firstChild = treeNode
        tree.item(root,open=True)
        if firstChild:
            tree.item(firstChild,open=True)

    def IntrospectCallback(self, event):
        tree = self._treeCtrl
        item = event.GetItem()
        if _VERBOSE:
            print ("In introspectCallback item is %s, pydata is %s" % (event.GetItem(), tree.GetPyData(item)))
        if tree.GetPyData(item) != "Introspect":
            event.Skip()
            return
        self._introspectItem = item
        self._parentChain = self.GetItemChain(item)
        self.OnIntrospect(event)
        event.Skip()

    def AppendSubTreeFromNode(self, node, name, parent, insertBefore=None):
        tree = self.stackFrameTab.tree
        if insertBefore != None:
            treeNode = tree.InsertItem(parent, insertBefore, name)
        else:
            treeNode = tree.insert(parent,"end",text=name)
        children = node.childNodes
        intro = node.getAttribute('intro')

        if intro == "True":
          #  tree.SetItemHasChildren(treeNode, True)
            self.stackFrameTab.SetPyData(treeNode, "Introspect")
        if node.getAttribute("value"):
            #tree.SetItemText(treeNode, self.StripOuterSingleQuotes(node.getAttribute("value")), 1)
            tree.set(treeNode, column='Value', value=self.StripOuterSingleQuotes(node.getAttribute("value")))
        for index in range(0, children.length):
            subNode = children.item(index)
            if self.HasChildren(subNode):
                self.AppendSubTreeFromNode(subNode, subNode.getAttribute("name"), treeNode)
            else:
                name = subNode.getAttribute("name")
                value = self.StripOuterSingleQuotes(subNode.getAttribute("value"))
                n = tree.insert(treeNode, "end",text=name)
                tree.set(n, value=value, column='Value')
                intro = subNode.getAttribute('intro')
                if intro == "True":
                    #tree.SetItemHasChildren(n, True)
                    self.stackFrameTab.SetPyData(n, "Introspect")
        if name.find('[') == -1:
            self.stackFrameTab.SortChildren(treeNode)
        return treeNode

    def StripOuterSingleQuotes(self, string):
        if string.startswith("'") and string.endswith("'"):
            retval =  string[1:-1]
        elif string.startswith("\"") and string.endswith("\""):
            retval = string[1:-1]
        else:
            retval = string
        if retval.startswith("u'") and retval.endswith("'"):
            retval = retval[1:]
        return retval

    def HasChildren(self, node):
        try:
            return node.childNodes.length > 0
        except:
            tp,val,tb=sys.exc_info()
            return False

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

class AGXMLRPCServer(SimpleXMLRPCServer):
    def __init__(self, address, logRequests=0):
        ###enable request method return None value
        SimpleXMLRPCServer.__init__(self, address, logRequests=logRequests,allow_none=1)

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
                tp, val, tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)
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
        
    def get_input_text(self):
        dialog = wx.TextEntryDialog(self._debuggerUI.framesTab._textCtrl, "Enter the input text:" , "Enter input")
        if dialog.ShowModal() == wx.ID_OK:
            self._input_text = dialog.GetValue()
            self._debuggerUI.framesTab._textCtrl.AddInputText(self._input_text)
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
                tp, val, tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)
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
                tp,val,tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)

class DebuggerOperationThread(threading.Thread):
        def __init__(self, function):
            threading.Thread.__init__(self)
            self._function = function

        def run(self):
            if _VERBOSE: print ("In DOT, before call")
            try:
                self._function()
            except:
                tp,val,tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)
            if _VERBOSE:
                print ("In DOT, after call")

class BaseDebuggerCallback(object):

    def Start(self):
        assert False, "Start not overridden"

    def ShutdownServer(self):
        assert False, "ShutdownServer not overridden"

    def BreakExecution(self):
        assert False, "BreakExecution not overridden"

    def SingleStep(self):
        assert False, "SingleStep not overridden"

    def Next(self):
        assert False, "Next not overridden"

    def Continue(self):
        assert False, "Start not overridden"

    def Return(self):
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

    def SingleStep(self):
        self._debuggerUI.DisableWhileDebuggerRunning()
        self._debuggerServer.set_step() # Figure out where to set allowNone
        self.WaitForRPC()

    def Next(self):
        self._debuggerUI.DisableWhileDebuggerRunning()
        self._debuggerServer.set_next()
        self.WaitForRPC()

    def Continue(self):
        self._debuggerUI.DisableWhileDebuggerRunning()
        self._debuggerServer.set_continue()
        self.WaitForRPC()

    def Return(self):
        self._debuggerUI.DisableWhileDebuggerRunning()
        self._debuggerServer.set_return()
        self.WaitForRPC()

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
            
        rbt = RequestBreakThread(self._breakServer, pushBreakpoints=True, breakDict=self._debuggerUI._debugger.GetMasterBreakpointDict())
        rbt.start()
        
    def PushExceptionBreakpoints(self):
        self._debuggerServer.set_all_exceptions(self._service.GetExceptions())

    def WaitForRPC(self):
        self._waiting = True
        self.RotateForRpc()
        
    def RotateForRpc(self):
        if not self._waiting:
            utils.get_logger().debug("Exiting WaitForRPC.")
            return
        self._debuggerUI.after(1000,self.RotateForRpc)
        try:
            self.ReadQueue()
            import time
            time.sleep(0.02)
        except:
            tp, val, tb = sys.exc_info()
            traceback.print_exception(tp, val, tb)

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
            if _VERBOSE: print ("Hit interaction with exception")
            #self._debuggerUI.StopExecution(None)
            #self._debuggerUI.SetStatusText("Got exception: " + str(info))
            self._debuggerUI.SwitchToOutputTab()
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
       # dbgService = wx.GetApp().GetService(DebuggerService)
        #evt = DebugInternalWebServer()
        #evt.SetId(constants.ID_STEP_CONTINUE)
        #wx.PostEvent(self._debuggerUI, evt)
        
        GetApp().event_generate(EVT_DEBUG_INTERNAL)
        if _VERBOSE: print ("Event Continue posted")
##
##        evt = DebugInternalWebServer()
##        evt.SetId(DebuggerService.DEBUG_WEBSERVER_NOW_RUN_PROJECT_ID)
##        wx.PostEvent(dbgService._frame, evt)
##        if _VERBOSE: print ("Event RunProject posted")

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

class PythonDebugger(Debugger):
    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    RUN_PARAMETERS = []
    #调试器只允许运行一个
    _debugger_ui = None

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self):
        Debugger.__init__(self)
        self.BREAKPOINT_DICT_STRING = "MasterBreakpointDict"
        pickledbps = utils.profile_get(self.BREAKPOINT_DICT_STRING)
        if pickledbps:
            try:
                self._masterBPDict = pickle.loads(pickledbps.encode('ascii'))
            except:
                tp, val, tb = sys.exc_info()
                traceback.print_exception(tp,val,tb)
                self._masterBPDict = {}
        else:
            self._masterBPDict = {}
        self.watchs = watchs.Watch.Load()
        self._exceptions = []
        self._frame = None
        self.projectPath = None
        self.phpDbgParam = None
       # self.dbgLanguage = projectmodel.LANGUAGE_DEFAULT
        self._tabs_menu = None
        self._popup_index = -1
        self._watch_separater = None
        
    def GetMasterBreakpointDict(self):
        return self._masterBPDict
        
    @classmethod
    def SetDebuggerUI(cls,debugger_ui):
        cls._debugger_ui  = debugger_ui
        
    def GetExceptions(self):
        return self._exceptions
        
    def SetExceptions(self,exceptions):
        self._exceptions = exceptions

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

    @staticmethod
    def CloseDebugger():
        # IS THIS THE RIGHT PLACE?
        try:
          #  config = wx.ConfigBase_Get()
           # config.Write(self.BREAKPOINT_DICT_STRING, pickle.dumps(self._masterBPDict))
            #Watchs.Watch.Dump(self.watchs)
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
        if doc_path in self._masterBPDict and len(self._masterBPDict[doc_path]) > 0:
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
        else:
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_STEP_OUT)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_TERMINATE_DEBUGGER)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_STEP_CONTINUE)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_BREAK_INTO_DEBUGGER)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_RESTART_DEBUGGER)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_ADD_WATCH)
            self.DeleteDebuggerMenuItem(run_menu,constants.ID_QUICK_ADD_WATCH)
            
            GetApp().MainFrame.GetCommonView(stacksframe.STACKFRAME_TAB_NAME,show=False)
            GetApp().MainFrame.GetCommonView(inspectconsole.INTERACTCONSOLE_TAB_NAME,show=False)
            GetApp().MainFrame.GetCommonView(breakpoints.BREAKPOINTS_TAB_NAME,show=False)
            GetApp().MainFrame.GetCommonView(watchs.WATCH_TAB_NAME,show=False)
            
    def AppendWatch(self,watch_obj):
        self.watchs.append(watch_obj)
        
    def AddtoWatch(self,watch_obj):
        self._debugger_ui.framesTab.AddtoWatch(watch_obj)
        
    def AddWatch(self,watch_obj=None,is_quick_watch=False):
        if is_quick_watch:
            self._debugger_ui.framesTab.QuickAddWatch(watch_obj)
        else:
            self._debugger_ui.framesTab.AddWatch(watch_obj)

class DebuggerOptionsPanel(ttk.Frame):


    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        SPACE = 10
        config = wx.ConfigBase_Get()
        localHostStaticText = wx.StaticText(self, -1, _("Local Host Name:"))
        self._LocalHostTextCtrl = wx.TextCtrl(self, -1, config.Read("DebuggerHostName", DEFAULT_HOST), size = (150, -1))
        portNumberStaticText = wx.StaticText(self, -1, _("Port Range:"))
        dashStaticText = wx.StaticText(self, -1, _("through to"))
        startingPort=config.ReadInt("DebuggerStartingPort", DEFAULT_PORT)
        self._PortNumberTextCtrl = wx.lib.intctrl.IntCtrl(self, -1, startingPort, size = (50, -1))
        self._PortNumberTextCtrl.SetMin(1)#What are real values?
        self._PortNumberTextCtrl.SetMax(65514) #What are real values?
        self.Bind(wx.lib.intctrl.EVT_INT, self.MinPortChange, self._PortNumberTextCtrl)

        self._EndPortNumberTextCtrl = wx.lib.intctrl.IntCtrl(self, -1, startingPort + PORT_COUNT, size = (50, -1))
        self._EndPortNumberTextCtrl.SetMin(22)#What are real values?
        self._EndPortNumberTextCtrl.SetMax(65535)#What are real values?
        self._EndPortNumberTextCtrl.Enable( False )
        debuggerPanelBorderSizer = wx.BoxSizer(wx.VERTICAL)
        debuggerPanelSizer = wx.GridBagSizer(hgap = 5, vgap = 5)
        debuggerPanelSizer.Add( localHostStaticText, (0,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        debuggerPanelSizer.Add( self._LocalHostTextCtrl, (0,1), (1,3), flag=wx.EXPAND|wx.ALIGN_CENTER)
        debuggerPanelSizer.Add( portNumberStaticText, (1,0), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        debuggerPanelSizer.Add( self._PortNumberTextCtrl, (1,1), flag=wx.ALIGN_CENTER)
        debuggerPanelSizer.Add( dashStaticText, (1,2), flag=wx.ALIGN_CENTER)
        debuggerPanelSizer.Add( self._EndPortNumberTextCtrl, (1,3), flag=wx.ALIGN_CENTER)
        FLUSH_PORTS_ID = wx.NewId()
        self._flushPortsButton = wx.Button(self, FLUSH_PORTS_ID, "Reset Port List")
        wx.EVT_BUTTON(parent, FLUSH_PORTS_ID, self.FlushPorts)
        debuggerPanelSizer.Add(self._flushPortsButton, (2,2), (1,2), flag=wx.ALIGN_RIGHT)

        debuggerPanelBorderSizer.Add(debuggerPanelSizer, 0, wx.ALL, SPACE)
        self.SetSizer(debuggerPanelBorderSizer)
        self.Layout()

    def FlushPorts(self, event):
        if self._PortNumberTextCtrl.IsInBounds():
            config = wx.ConfigBase_Get()
            config.WriteInt("DebuggerStartingPort", self._PortNumberTextCtrl.GetValue())
            PythonDebuggerUI.NewPortRange()
        else:
            wx.MessageBox(_("The starting port is not valid. Please change the value and try again."), _("Invalid Starting Port Number"))

    def MinPortChange(self, event):
        self._EndPortNumberTextCtrl.Enable( True )
        self._EndPortNumberTextCtrl.SetValue( self._PortNumberTextCtrl.GetValue() + PORT_COUNT)
        self._EndPortNumberTextCtrl.Enable( False )

    def OnOK(self, optionsDialog):
        config = wx.ConfigBase_Get()
        config.Write("DebuggerHostName", self._LocalHostTextCtrl.GetValue())
        if self._PortNumberTextCtrl.IsInBounds():
            config.WriteInt("DebuggerStartingPort", self._PortNumberTextCtrl.GetValue())
        return True

    def GetIcon(self):
        return getContinueIcon()
    
def getBreakPointBitmap():
    return images.load("debugger/breakpoint.png")
    
def getRestartDebuggerBitmap():
    return images.load("debugger/restart_debugger.png")

#----------------------------------------------------------------------

