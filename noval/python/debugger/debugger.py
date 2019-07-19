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
import noval.core as core
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
import noval.python.parser.intellisence as intellisence
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.util.strutils as strutils
import noval.python.parser.utils as parserutils
import noval.util.fileutils as fileutils
import copy
import noval.util.appdirs as appdirs
import noval.util.utils as utils
import noval.python.project.runconfig as runconfig
import noval.python.debugger.breakpoints as breakpoints
import pickle
import noval.project.baseconfig as baseconfig
import noval.python.debugger.watchs as watchs
import uuid
import noval.constants as constants
import noval.ui_base as ui_base
import noval.ui_common as ui_common
if utils.is_py2():
    import noval.python.debugger.debuggerharness as debuggerharness
elif utils.is_py3_plus():
    import noval.python.debugger.debuggerharness3 as debuggerharness
    
import noval.python.pyutils as pyutils
from noval.util.exceptions import StartupPathNotExistError
import noval.terminal as terminal
import noval.toolbar as toolbar
import noval.process as process
import noval.menu as tkmenu
import noval.python.project.viewer as projectviewer
import noval.consts as consts
import noval.misc as misc
from noval.python.parser.utils import py_cmp,py_sorted
import noval.python.pyeditor as pyeditor
import noval.python.project.runconfiguration as runconfiguration

#VERBOSE mode will invoke threading.Thread _VERBOSE,which will print a lot of thread debug text on screen
_VERBOSE = False
_WATCHES_ON = True


EVT_UPDATE_STDTEXT = "UpdateOutputText"
EVT_UPDATE_ERRTEXT = "UpdateErrorText"

class OutputReaderThread(threading.Thread):
    def __init__(self, file, callback_function, callbackOnExit=None, accumulate=True):
        threading.Thread.__init__(self)
        self._file = file
        self._callback_function = callback_function
        self._keepGoing = True
        self._lineCount = 0
        self._accumulate = accumulate
        self._callbackOnExit = callbackOnExit
        self.setDaemon(True)

    def __del__(self):
        # See comment on PythonDebuggerUI.StopExecution
        self._keepGoing = False

    def run(self):
        file = self._file
        start = time.time()
        output = ""
        while self._keepGoing:
            try:
                # This could block--how to handle that?
                text = file.readline()
                if text == '' or text == None:
                    self._keepGoing = False
                elif not self._accumulate and self._keepGoing:
                    self._callback_function(text)
                else:
                    # Should use a buffer? StringIO?
                    output += text
                # Seems as though the read blocks if we got an error, so, to be
                # sure that at least some of the exception gets printed, always
                # send the first hundred lines back as they come in.
                if self._lineCount < 100 and self._keepGoing:
                    self._callback_function(output)
                    self._lineCount += 1
                    output = ""
                elif time.time() - start > 0.25 and self._keepGoing:
                    try:
                        self._callback_function(output)
                    except wx._core.PyDeadObjectError:
                        # GUI was killed while we were blocked.
                        self._keepGoing = False
                    start = time.time()
                    output = ""
                elif not self._keepGoing:
                    self._callback_function(output)
                    output = ""
            #except TypeError:
            #    pass
            except:
                tp, val, tb = sys.exc_info()
                print ("Exception in OutputReaderThread.run():", tp, val)
                utils.get_logger().exception("")
                self._keepGoing = False
        if self._callbackOnExit:
            try:
                self._callbackOnExit()
            except Exception as e:
                utils.get_logger().exception("")
                pass
        if _VERBOSE: print ("Exiting OutputReaderThread")

    def AskToStop(self):
        self._keepGoing = False


class Executor(object):
    def GetPythonExecutablePath():
        current_interpreter = GetApp().GetCurrentInterpreter()
        if current_interpreter:
            return current_interpreter.Path
        messagebox.showinfo( _("Python Executable Location Unknown"),_("To proceed we need to know the location of the python.exe you would like to use.\nTo set this, go to Tools-->Options and use the 'Python Inpterpreter' panel to configuration a interpreter.\n"))
        ui_common.ShowInterpreterConfigurationPage()
        return None
    GetPythonExecutablePath = staticmethod(GetPythonExecutablePath)

    def __init__(self, run_parameter, wxComponent, callbackOnExit=None,cmd_contain_path = True):
        self._run_parameter = run_parameter
        self._stdOutCallback = self.OutCall
        self._stdErrCallback = self.ErrCall
        self._callbackOnExit = callbackOnExit
        self._wxComponent = wxComponent
        assert(self._run_parameter.Interpreter != None)
        if sysutilslib.is_windows():
            #should convert to unicode when interpreter path contains chinese character
            self._path = self._run_parameter.Interpreter.GetUnicodePath()
        else:
            self._path = self._run_parameter.Interpreter.Path
            
        self._cmd = strutils.emphasis_path(self._path)
        if self._run_parameter.InterpreterOption and self._run_parameter.InterpreterOption != ' ':
            self._cmd = self._cmd + " " + self._run_parameter.InterpreterOption
        if cmd_contain_path:
            self._cmd += self.spaceAndQuote(self._run_parameter.FilePath)

        self._stdOutReader = None
        self._stdErrReader = None
        self._process = None
        
    #Better way to do this? Quotes needed for windows file paths.
    def spaceAndQuote(self,text):
        if text.startswith("\"") and text.endswith("\""):
            return  ' ' + text
        else:
            return ' \"' + text + '\"'

    def OutCall(self, text):
        GetApp().event_generate(EVT_UPDATE_STDTEXT,value=text,interface=self._wxComponent)

    def ErrCall(self, text):
        GetApp().event_generate(EVT_UPDATE_ERRTEXT,value=text,interface=self._wxComponent)

    def Execute(self, arguments, startIn=None, environment=None):
        if not startIn:
            startIn = str(os.getcwd())
        ###startIn = os.path.abspath(startIn)
        if not os.path.exists(startIn):
            msg = _("Startup path \"%s\" is not exist") % startIn
            raise RuntimeError(msg)

        if arguments and arguments != " ":
            command = self._cmd + ' ' + arguments
        else:
            command = self._cmd

        if _VERBOSE: print ("start debugger executable: " + command + "\n")
        utils.get_logger().debug("start debugger executable: %s",command)
        self._process = process.ProcessOpen(command, mode='b', cwd=startIn, env=environment)
        # Kick off threads to read stdout and stderr and write them
        # to our text control.
        self._stdOutReader = OutputReaderThread(self._process.stdout, self._stdOutCallback, callbackOnExit=self._callbackOnExit)
        self._stdOutReader.start()
        self._stdErrReader = OutputReaderThread(self._process.stderr, self._stdErrCallback, accumulate=False)
        self._stdErrReader.start()

    def DoStopExecution(self):
        # See comment on PythonDebuggerUI.StopExecution
        if(self._process != None):
            self._stdOutReader.AskToStop()
            self._stdErrReader.AskToStop()
            try:
                self._process.kill(gracePeriod=2.0)
            except:
                pass
            self._process = None

    def GetExecPath(self):
        return self._path
        
    def WriteInput(self,text):
        if None == self._process:
            return
        self._process.stdin.write(text)
        
class DebuggerExecutor(Executor):
    
    def __init__(self, debugger_fileName,run_parameter, wxComponent, arg1=None, arg2=None, arg3=None, arg4=None, arg5=None, arg6=None, arg7=None, arg8=None, arg9=None, callbackOnExit=None):
        
        super(DebuggerExecutor,self).__init__(run_parameter,wxComponent,callbackOnExit,cmd_contain_path=False)
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

class RunCommandUI(ttk.Frame):
    runners = []
    
    KILL_PROCESS_ID = NewId()
    CLOSE_TAB_ID = NewId()
    TERMINATE_ALL_PROCESS_ID = NewId()
    RESTART_PROCESS_ID = NewId()

    def ShutdownAllRunners():
        # See comment on PythonDebuggerUI.StopExecution
        for runner in RunCommandUI.runners:
            try:
                runner.StopExecution()
                runner.UpdateAllRunnerTerminateAllUI()
            except wx._core.PyDeadObjectError:
                pass
        RunCommandUI.runners = []
    ShutdownAllRunners = staticmethod(ShutdownAllRunners)
    
    @staticmethod
    def StopAndRemoveAllUI():
        return GetApp().GetDebugger().CloseAllPages()

    def __init__(self,parent, debugger, fileName,run_parameter):
        ttk.Frame.__init__(self, parent)
        self._debugger = debugger
        self._noteBook = parent
        self._run_parameter = run_parameter
        self._restarted = False
        threading._VERBOSE = _VERBOSE
        # GUI Initialization follows
        self._tb = tb = toolbar.ToolBar(self,orient=tk.VERTICAL)
        self._tb.pack(side=tk.LEFT,fill="y",expand=0)
        self.terminate_all_image = GetApp().GetImage("python/debugger/terminate_all.png")
        self.restart_image = GetApp().GetImage("python/debugger/restart.png")
        self.close_img = GetApp().GetImage("python/debugger/close.png")
        self.stop_img = GetApp().GetImage("python/debugger/stop.png")
        
        self._tb.AddButton(self.CLOSE_TAB_ID,self.close_img,_("Close Window"),lambda:self.OnToolClicked(self.CLOSE_TAB_ID))
        self._tb.AddButton(self.KILL_PROCESS_ID,self.stop_img,_("Stop the Run."),lambda:self.OnToolClicked(self.KILL_PROCESS_ID))
        
        self._tb.AddButton(self.TERMINATE_ALL_PROCESS_ID,self.terminate_all_image,_("Stop All the Run."),lambda:self.OnToolClicked(self.TERMINATE_ALL_PROCESS_ID))
        self._tb.AddButton(self.RESTART_PROCESS_ID,self.restart_image,_("Restart the Run."),lambda:self.OnToolClicked(self.RESTART_PROCESS_ID))

        self._output = debugoutput.OutputView(self) #id)
        self._output.pack(side=tk.LEFT,fill="both",expand=1)
        self._textCtrl = self._output.GetOutputCtrl()
        self._stopped = False
        # Executor initialization
        self._executor = Executor(self._run_parameter, self, callbackOnExit=self.ExecutorFinished)
        self.evt_stdtext_binding = GetApp().bind(EVT_UPDATE_STDTEXT, self.AppendText,True)
        self.evt_stdterr_binding = GetApp().bind(EVT_UPDATE_ERRTEXT, self.AppendErrorText,True)
        self._output.SetExecutor(self._executor)
        RunCommandUI.runners.append(self)
        #重写关闭窗口事件,关闭窗口时检查进程是否在运行
        self.master.close = self.Close

    def __del__(self):
        # See comment on PythonDebuggerUI.StopExecution
        self._executor.DoStopExecution()
        RunCommandUI.runners.remove(self)
        
    def GetOutputView(self):
        return self._output

    def Execute(self,onWebServer = False):
        try:
            initialArgs = self._run_parameter.Arg
            startIn = self._run_parameter.StartupPath
            environment = self._run_parameter.Environment
            self._executor.Execute(initialArgs, startIn, environment)
        except StartupPathNotExistError as e:
            wx.MessageBox(e.msg,_("Startup path not exist"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
            self.StopExecution()
            self.ExecutorFinished()
        except Exception as e:
            utils.get_logger().exception("")
            messagebox.showerror(_("Run Error"),str(e),parent=GetApp().GetTopWindow())
            self.StopExecution()
            self.ExecutorFinished()
    
    def IsProcessRunning(self):
        process_runners = [runner for runner in self.runners if not runner.Stopped]
        return True if len(process_runners) > 0 else False
    
    @property
    def Stopped(self):
        return self._stopped
        
    def UpdateTerminateAllUI(self):
        self._tb.EnableTool(self.TERMINATE_ALL_PROCESS_ID, self.IsProcessRunning())
        
    def UpdateAllRunnerTerminateAllUI(self):
        for runner in self.runners:
            runner.UpdateTerminateAllUI()
        
    def ExecutorFinished(self):
        try:
            self._tb.EnableTool(self.KILL_PROCESS_ID, False)
            self.UpdateFinishedPagePaneText()
            self._stopped = True
            self._textCtrl.set_read_only(True)
            self.UpdateAllRunnerTerminateAllUI()
        except Exception as e:
            utils.get_logger().exception("")
         ###   utils.GetLogger().warn("RunCommandUI object has been deleted, attribute access no longer allowed when finish executor")
            return
        if self._restarted:
            self.RestartRunProcess()
            self._restarted = False
            
    #when process finished,update tag page text
    def UpdateFinishedPagePaneText(self):
        self.UpdatePagePaneText(_("Running"),_("Finished Running"))

    def StopExecution(self,unbind_evt=False):
        if not self._stopped:
            if unbind_evt:
                GetApp().unbind(EVT_UPDATE_STDTEXT,self.evt_stdtext_binding)
                GetApp().unbind(EVT_UPDATE_ERRTEXT,self.evt_stdterr_binding)
            self._executor.DoStopExecution()
            self._textCtrl.set_read_only(True)

    def AppendText(self, event):
        if event.get('interface') != self:
            utils.get_logger().debug('run view interface receive other stdout msg,ignore it')
            return
        self._textCtrl.AppendText(event.get('value'))

    def AppendErrorText(self, event):
        if event.get('interface') != self:
            utils.get_logger().debug('run view interface receive other stderr msg,ignore it')
            return
        self._textCtrl.AppendErrorText(event.get('value'))

    def StopAndRemoveUI(self):
        if not self._stopped:
            ret = messagebox.askyesno(_("Process Running.."),_("Process is still running,Do you want to kill the process and remove it?"),parent=self)
            if ret == False:
                return False

        self.StopExecution(unbind_evt=True)
        #关闭调试窗口,关闭notebook的子窗口
        self.master.master.close_child(self.master)
        return True
        
    def RestartProcess(self):
        currentProj = GetApp().MainFrame.GetProjectView(False).GetCurrentProject()
        if currentProj is not None and currentProj.GetModel().FindFile(self._run_parameter.FilePath):
            self._debugger.PromptToSaveFiles(currentProj)
        else:
            openDoc = GetApp().GetDocumentManager().GetDocument(self._run_parameter.FilePath)
            if openDoc:
                openDoc.Save()
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
        self.UpdateRestartPagePaneText()
        self.Execute()
        
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
                
    def ProcessUpdateUIEvent(self,event):
        return self._textCtrl.ProcessUpdateUIEvent(event)
        
    def ProcessEvent(self,event):
        return self._textCtrl.ProcessEvent(event)
        

    def Close(self):
        self.StopAndRemoveUI()

DEFAULT_PORT = 32032
DEFAULT_HOST = 'localhost'
PORT_COUNT = 21

class BaseDebuggerUI(ttk.Frame):
    debuggers = []
    
    KILL_PROCESS_ID = NewId()
    CLOSE_WINDOW_ID = NewId()
    CLEAR_ID = NewId()
    STEP_INTO_ID = NewId()
    STEP_NEXT_ID = NewId()

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

    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self._parentNoteBook = parent

        self._service = None
        self._executor = None
        self._callback = None
        self._stopped = False
        self._restarted = False

        BaseDebuggerUI.debuggers.append(self)
        self._stopped = True
        self.Bind(EVT_UPDATE_STDTEXT, self.AppendText)
        self.Bind(EVT_UPDATE_ERRTEXT, self.AppendErrorText)
        
        menubar = wx.GetApp().GetTopWindow().GetMenuBar()
        run_menu_index = menubar.FindMenu(_("&Run"))
        self.run_menu = menubar.GetMenu(run_menu_index)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self._tb = tb = wx.ToolBar(self,  -1, wx.DefaultPosition, (1000,30), wx.TB_HORIZONTAL| wx.NO_BORDER| wx.TB_FLAT, "Debugger" )
        sizer.Add(tb, 0, wx.EXPAND |wx.ALIGN_LEFT|wx.ALL, 1)
        tb.SetToolBitmapSize((16,16))

        close_bmp = getCloseBitmap()
        tb.AddSimpleTool( self.CLOSE_WINDOW_ID, close_bmp, _('Close Window'))
        wx.EVT_TOOL(self, self.CLOSE_WINDOW_ID, self.StopAndRemoveUI)
        tb.AddSeparator()
        
        continue_bmp = getContinueBitmap()
        tb.AddSimpleTool( constants.ID_STEP_CONTINUE, continue_bmp, _("Continue Execution"))
        wx.EVT_TOOL(self, constants.ID_STEP_CONTINUE, self.OnContinue)
        self.Bind(EVT_DEBUG_INTERNAL, self.OnContinue)
        
        break_bmp = getBreakBitmap()
        tb.AddSimpleTool( constants.ID_BREAK_INTO_DEBUGGER, break_bmp, _("Break into Debugger"))
        wx.EVT_TOOL(self, constants.ID_BREAK_INTO_DEBUGGER, self.BreakExecution)
        
        stop_bmp = getStopBitmap()
        tb.AddSimpleTool( self.KILL_PROCESS_ID, stop_bmp, _("Stop Debugging"))
        wx.EVT_TOOL(self, self.KILL_PROCESS_ID, self.StopExecution)
        
        restart_bmp = getRestartDebuggerBitmap()
        tb.AddSimpleTool( constants.ID_RESTART_DEBUGGER, restart_bmp, _("Restart Debugging"))
        wx.EVT_TOOL(self, constants.ID_RESTART_DEBUGGER, self.RestartDebugger)

        tb.AddSeparator()
        next_bmp = getNextBitmap()
        tb.AddSimpleTool( self.STEP_NEXT_ID, next_bmp, _("Step to next line"))
        wx.EVT_TOOL(self, self.STEP_NEXT_ID, self.OnNext)

        step_bmp = getStepInBitmap()
        tb.AddSimpleTool( self.STEP_INTO_ID, step_bmp, _("Step in"))
        wx.EVT_TOOL(self, self.STEP_INTO_ID, self.OnSingleStep)

        stepOut_bmp = getStepReturnBitmap()
        tb.AddSimpleTool(constants.ID_STEP_OUT, stepOut_bmp, _("Stop at function return"))
        wx.EVT_TOOL(self, constants.ID_STEP_OUT, self.OnStepOut)

        tb.AddSeparator()
        if _WATCHES_ON:
            
            quick_watch_bmp = Watchs.getQuickAddWatchBitmap()
            tb.AddSimpleTool(constants.ID_QUICK_ADD_WATCH, quick_watch_bmp, _("Quick Add a Watch"))
            wx.EVT_TOOL(self, constants.ID_QUICK_ADD_WATCH, self.OnQuickAddWatch)
            
            watch_bmp = Watchs.getAddWatchBitmap()
            tb.AddSimpleTool(constants.ID_ADD_WATCH, watch_bmp, _("Add a Watch"))
            wx.EVT_TOOL(self, constants.ID_ADD_WATCH, self.OnAddWatch)
            tb.AddSeparator()

        clear_bmp = getClearOutputBitmap()
        tb.AddSimpleTool(self.CLEAR_ID, clear_bmp, _("Clear output pane"))
        wx.EVT_TOOL(self, self.CLEAR_ID, self.OnClearOutput)

        self._toolEnabled = True
        self.framesTab = None
        self.DisableWhileDebuggerRunning()
        self.framesTab = self.MakeFramesUI(self, wx.NewId(), None)
        sizer.Add(self.framesTab, 1, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 1)
        self._statusBar = wx.StatusBar( self, -1)
        self._statusBar.SetFieldsCount(1)
        sizer.Add(self._statusBar, 0, wx.EXPAND |wx.ALIGN_LEFT|wx.ALL, 1)
        self.SetStatusText("Starting debug...")
        self.SetSizer(sizer)
        tb.Realize()
        sizer.Fit(self)

    def OnSingleStep(self, event):
        self._callback.SingleStep()

    def OnContinue(self, event):
        self._callback.Continue()

    def OnStepOut(self, event):
        self._callback.Return()

    def OnNext(self, event):
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
            self._tb.EnableTool(self.STEP_INTO_ID, False)
            self._tb.EnableTool(constants.ID_STEP_CONTINUE, False)
            if self.run_menu.FindItemById(constants.ID_STEP_CONTINUE):
                self.run_menu.Enable(constants.ID_STEP_CONTINUE,False)
            self._tb.EnableTool(constants.ID_STEP_OUT, False)
            if self.run_menu.FindItemById(constants.ID_STEP_OUT):
                self.run_menu.Enable(constants.ID_STEP_OUT,False)
            self._tb.EnableTool(self.STEP_NEXT_ID, False)
            self._tb.EnableTool(constants.ID_BREAK_INTO_DEBUGGER, True)
            if self.run_menu.FindItemById(constants.ID_BREAK_INTO_DEBUGGER):
                self.run_menu.Enable(constants.ID_BREAK_INTO_DEBUGGER,True)
    
            if _WATCHES_ON:
                self._tb.EnableTool(constants.ID_ADD_WATCH, False)
                self._tb.EnableTool(constants.ID_QUICK_ADD_WATCH, False)
    
            self.DeleteCurrentLineMarkers()
    
            if self.framesTab:
                self.framesTab.ClearWhileRunning()

            self._toolEnabled = False

    def EnableWhileDebuggerStopped(self):
        self._tb.EnableTool(self.STEP_INTO_ID, True)
        self._tb.EnableTool(constants.ID_STEP_CONTINUE, True)
        if self.run_menu.FindItemById(constants.ID_STEP_CONTINUE):
            self.run_menu.Enable(constants.ID_STEP_CONTINUE,True)
        self._tb.EnableTool(constants.ID_STEP_OUT, True)
        if self.run_menu.FindItemById(constants.ID_STEP_OUT):
            self.run_menu.Enable(constants.ID_STEP_OUT,True)
        self._tb.EnableTool(self.STEP_NEXT_ID, True)
        self._tb.EnableTool(constants.ID_BREAK_INTO_DEBUGGER, False)
        if self.run_menu.FindItemById(constants.ID_BREAK_INTO_DEBUGGER):
            self.run_menu.Enable(constants.ID_BREAK_INTO_DEBUGGER,False)
        self._tb.EnableTool(self.KILL_PROCESS_ID, True)
        if self.run_menu.FindItemById(constants.ID_TERMINATE_DEBUGGER):
            self.run_menu.Enable(constants.ID_TERMINATE_DEBUGGER,True)

        if _WATCHES_ON:
            self._tb.EnableTool(constants.ID_ADD_WATCH, True)
            self._tb.EnableTool(constants.ID_QUICK_ADD_WATCH, True)

        self._toolEnabled = True

    def DisableAfterStop(self):
        if self._toolEnabled:
            self.DisableWhileDebuggerRunning()
            self._tb.EnableTool(constants.ID_BREAK_INTO_DEBUGGER, False)
            if self.run_menu.FindItemById(constants.ID_BREAK_INTO_DEBUGGER):
                self.run_menu.Enable(constants.ID_BREAK_INTO_DEBUGGER,False)
            self._tb.EnableTool(self.KILL_PROCESS_ID, False)
            if self.run_menu.FindItemById(constants.ID_TERMINATE_DEBUGGER):
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
        wx.GetApp().GetService(DebuggerService).ShowHideDebuggerMenu(False)
        if self._restarted:
            wx.MilliSleep(250)
            self.RestartDebuggerProcess()
            self._restarted = False

    def SetStatusText(self, text):
        self._statusBar.SetStatusText(text,0)

    def BreakExecution(self, event):
        if not BaseDebuggerUI.DebuggerRunning():
            wx.MessageBox(_("Debugger has been stopped."),style=wx.OK|wx.ICON_ERROR)
            return
        self._callback.BreakExecution()

    def StopExecution(self, event):
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
        openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            # This ugliness to prevent comparison failing because the drive letter
            # gets lowercased occasionally. Don't know why that happens or why  it
            # only happens occasionally.
            if DebuggerService.ComparePaths(openDoc.GetFilename(),filename):
                foundView = openDoc.GetFirstView()
                break

        if not foundView:
            if _VERBOSE:
                print ("filename=", filename)
            doc = wx.GetApp().GetDocumentManager().CreateDocument(DebuggerService.ExpandPath(filename), wx.lib.docview.DOC_SILENT)
            foundView = doc.GetFirstView()

        if foundView:
            foundView.GetFrame().SetFocus()
            foundView.Activate()
            foundView.GotoLine(lineNum)
            startPos = foundView.PositionFromLine(lineNum)

        if not noArrow:
            foundView.GetCtrl().MarkerAdd(lineNum -1, CodeEditor.CodeCtrl.CURRENT_LINE_MARKER_NUM)

    def DeleteCurrentLineMarkers(self):
        openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if(isinstance(openDoc, CodeEditor.CodeDocument)):
                openDoc.GetFirstView().GetCtrl().ClearCurrentLineMarkers()

    def StopAndRemoveUI(self, event):
        if self._executor:
            ret = wx.MessageBox(_("Debugger is still running,Do you want to kill the debugger and remove it?"), _("Debugger Running.."),
                       wx.YES_NO  | wx.ICON_QUESTION ,self)
            if ret == wx.NO:
                return False
        self.StopExecution(None)
        if self in BaseDebuggerUI.debuggers:
            BaseDebuggerUI.debuggers.remove(self)
        tab_page_pane = self._service.AuiManager.GetPane(self)
        tab_page_pane.Show(False)
        #destroy the window pane after close,but not destroy pane window
        tab_page_pane.DestroyOnClose()
        self._service.AuiManager.ClosePane(tab_page_pane,destroy_pane_window=False)
        self._service.AuiManager.Update()
        if self._callback.IsWait():
            utils.GetLogger().warn("debugger callback is still wait for rpc when debugger stoped.will stop manualy")
            self._callback.StopWait()
            
        return True

    def OnAddWatch(self, event):
        if self.framesTab:
            self.framesTab.OnAddWatch(event)
            
    def OnQuickAddWatch(self,event):
        if self.framesTab:
            self.framesTab.QuickAddWatch()

    def MakeFramesUI(self, parent, id, debugger):
        assert False, "MakeFramesUI not overridden"

    def AppendText(self, event):
        self.framesTab.AppendText(event.value)

    def AppendErrorText(self, event):
        self.framesTab.AppendErrorText(event.value)

    def OnClearOutput(self, event):
        self.framesTab.ClearOutput(None)

    def SwitchToOutputTab(self):
        self.framesTab.SwitchToOutputTab()
        
    def RestartDebugger(self,event):
        assert False, "RestartDebugger not overridden"
        
    def UpdatePagePaneText(self,src_text,to_text):
        nb = self._service.GetBottomTab()
        pane_info = self._service.AuiManager.GetPane(self)
        if nb is None:
            text = pane_info.caption
            newText = text.replace(src_text,to_text)
            pane_info.Caption(newText)
        else:
            nb_pane_info = self._service.AuiManager.GetPane(nb)
            for i in range(0,nb.GetPageCount()):
                if self == nb.GetPage(i):
                    text = nb.GetPageText(i)
                    newText = text.replace(src_text,to_text)
                    nb.SetPageText(i, newText)
                    pane_info.Caption(newText)
                    nb_pane_info.Caption(newText)
                    break
        self._service.AuiManager.Update()


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
        config = wx.ConfigBase_Get()
        hostname = config.Read("DebuggerHostName", DEFAULT_HOST)
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
        config = wx.ConfigBase_Get()
        startingPort = config.ReadInt("DebuggerStartingPort", DEFAULT_PORT)
        PythonDebuggerUI.debuggerPortList = range(startingPort, startingPort + PORT_COUNT)
    NewPortRange = staticmethod(NewPortRange)

    def __init__(self, parent, id, command, service,run_parameter, autoContinue=True):
        # Check for ports before creating the panel.
        if not PythonDebuggerUI.debuggerPortList:
            PythonDebuggerUI.NewPortRange()
        self._debuggerPort = str(PythonDebuggerUI.GetAvailablePort())
        self._guiPort = str(PythonDebuggerUI.GetAvailablePort())
        self._debuggerBreakPort = str(PythonDebuggerUI.GetAvailablePort())
        BaseDebuggerUI.__init__(self, parent, id)
        self._run_parameter = run_parameter
        self._command = command
        self._service = service
        self._autoContinue = autoContinue
        self._callback = None
        config = wx.ConfigBase_Get()
        self._debuggerHost = self._guiHost = config.Read("DebuggerHostName", DEFAULT_HOST)
        self.CreateCallBack()
        self.CreateExecutor()
        self._stopped = False

    def CreateExecutor(self):
        interpreter = interpretermanager.InterpreterManager.GetCurrentInterpreter()
        if DebuggerHarness.__file__.find('library.zip') > 0:
            try:
                fname = DebuggerHarness.__file__
                parts = fname.split('library.zip')
                if interpreter.IsV2():
                    path = os.path.join(parts[0],'noval', 'tool','debugger', 'DebuggerHarness.py')
                elif interpreter.IsV3():
                    path = os.path.join(parts[0],'noval', 'tool','debugger', 'DebuggerHarness3.py')
            except:
                tp, val, tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)

        else:
            print ("Starting debugger on these ports: %s, %s, %s" % (str(self._debuggerPort) , str(self._guiPort) , str(self._debuggerBreakPort)))
            path = DebuggerService.ExpandPath(DebuggerHarness.__file__)
            if interpreter.IsV3():
                path = path.replace("DebuggerHarness","DebuggerHarness3").replace("DebuggerHarness3.pyc","DebuggerHarness3.py")
        self._executor = DebuggerExecutor(path, self._run_parameter,self, self._debuggerHost, \
                                                self._debuggerPort, self._debuggerBreakPort, self._guiHost, self._guiPort, self._command, callbackOnExit=self.ExecutorFinished)
        self.framesTab.SetExecutor(self._executor)
        
    def LoadPythonFramesList(self, framesXML):
        self.framesTab.LoadFramesList(framesXML)
        self.framesTab.UpdateWatchs()

    def Execute(self, onWebServer = False):
        initialArgs = self._run_parameter.Arg
        startIn = self._run_parameter.StartupPath
        environment = self._run_parameter.Environment
        self._callback.Start()
        self._executor.Execute(initialArgs, startIn, environment)
        self._callback.WaitForRPC()


    def StopExecution(self, event):
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
            except wx._core.PyDeadObjectError:
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


    def MakeFramesUI(self, parent, id, debugger):
        panel = PythonFramesUI(parent, id, self)
        return panel
        
    def UpdateWatch(self,watch_obj,item):
        self.framesTab.UpdateWatch(watch_obj,item)
        
    def UpdateWatchs(self,reset=False):
        self.framesTab.UpdateWatchs(reset)

    def OnSingleStep(self, event):
        BaseDebuggerUI.OnSingleStep(self,event)
        self._service.UpdateWatchs()

    def OnContinue(self, event):
        BaseDebuggerUI.OnContinue(self,event)

    def OnStepOut(self, event):
        BaseDebuggerUI.OnStepOut(self,event)
        self._service.UpdateWatchs()

    def OnNext(self, event):
        BaseDebuggerUI.OnNext(self,event)
        self._service.UpdateWatchs()

    def DisableWhileDebuggerRunning(self):
        BaseDebuggerUI.DisableWhileDebuggerRunning(self)
        if self._service is not None:
        #when process is running normal,reset the watchs
            self._service.UpdateWatchs(reset=True)
            
    def CreateCallBack(self):
        url = 'http://' + self._debuggerHost + ':' + self._debuggerPort + '/'
        self._breakURL = 'http://' + self._debuggerHost + ':' + self._debuggerBreakPort + '/'
        self._callback = PythonDebuggerCallback(self._guiHost, self._guiPort, url, self._breakURL, self, self._autoContinue)
            
    def RestartDebugger(self,event):
        
        projectService = wx.GetApp().GetService(project.ProjectEditor.ProjectService)
        currentProj = projectService.GetCurrentProject()
        if currentProj is not None and currentProj.GetModel().FindFile(self._run_parameter.FilePath):
            wx.GetApp().GetService(DebuggerService).PromptToSaveFiles(currentProj)
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
            

    def ProcessUpdateUIEvent(self,event):
        return self.framesTab._textCtrl.ProcessUpdateUIEvent(event)
        
    def ProcessEvent(self,event):
        return self.framesTab._textCtrl.ProcessEvent(event)

class BaseFramesUI:
    
    THING_COLUMN_WIDTH = 175
    def __init__(self, parent, id, ui):
        wx.SplitterWindow.__init__(self, parent, id, style = wx.SP_3D)
        self._ui = ui
        self._p1 = p1 = wx.ScrolledWindow(self, -1)
        self.MakeConsoleOutput(self._p1)

        self._p2 = p2 = wx.Window(self, -1)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        p2.SetSizer(sizer3)
        p2.Bind(wx.EVT_SIZE, self.OnSize)
        self._notebook = wx.Notebook(p2, -1, size=(20,20))
        iconList = wx.ImageList(16, 16, 4)
        
        stackframe_icon = images.load_icon("debugger/flag.ico")
        stackframe_icon_index = iconList.AddIcon(stackframe_icon)
        interact_icon = images.load_icon("debugger/interact.png")
        interact_icon_index = iconList.AddIcon(interact_icon)
        breakpoints_icon = images.load_icon("debugger/breakpoints.png")
        breakpoints_icon_index = iconList.AddIcon(breakpoints_icon)
        watchs_icon = images.load_icon("debugger/watches.png")
        watchs_icon_index = iconList.AddIcon(watchs_icon)
        
        self._notebook.AssignImageList(iconList)
        self._notebook.Hide()
        sizer3.Add(self._notebook, 1, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 1)
        self.stackFrameTab = self.MakeStackFrameTab(self._notebook, wx.NewId())
        self.inspectConsoleTab = self.MakeInspectConsoleTab(self._notebook, wx.NewId())
        self.breakPointsTab = self.MakeBreakPointsTab(self._notebook, wx.NewId())
        self.watchsTab = self.MakeWatchsTab(self._notebook, wx.NewId())
        self._notebook.AddPage(self.stackFrameTab, _("Stack Frame"))
        self._notebook.SetPageImage(self._notebook.GetPageCount() - 1,stackframe_icon_index)
        self._notebook.AddPage(self.inspectConsoleTab, _("Interact"))
        self._notebook.SetPageImage(self._notebook.GetPageCount() - 1,interact_icon_index)
        self._notebook.AddPage(self.breakPointsTab, _("Break Points"))
        self._notebook.SetPageImage(self._notebook.GetPageCount() - 1,breakpoints_icon_index)
        self._notebook.AddPage(self.watchsTab, _("Watchs"))
        self._notebook.SetPageImage(self._notebook.GetPageCount() - 1,watchs_icon_index)
        self.SetMinimumPaneSize(20)
        self.SplitVertically(p1, p2, 550)
        self.currentItem = None
        self._notebook.Show(True)

    def PopulateBPList(self):
        self.breakPointsTab.PopulateBPList()

    def OnSize(self, event):
        self._notebook.SetSize(self._p2.GetSize())
        #fit thing column width
        self._treeCtrl.SetColumnWidth(1, self._notebook.GetSize().x-self.THING_COLUMN_WIDTH-SPACE*2)
        self.breakPointsTab._bpListCtrl.SetColumnWidth(2, self._notebook.GetSize().x-self.breakPointsTab.FILE_NAME_COLUMN_WIDTH - self.breakPointsTab.FILE_LINE_COLUMN_WIDTH-SPACE)
        self.watchsTab._treeCtrl.SetColumnWidth(1, self._notebook.GetSize().x-self.watchsTab.WATCH_NAME_COLUMN_WIDTH-SPACE)

    def MakeStackFrameTab(self, parent, id):
        
        panel = wx.Panel(parent, id)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        framesLabel = wx.StaticText(panel, -1, _("Stack Frame:"))
        sizer.Add(framesLabel, 0, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.LEFT, border=2)

        self._framesChoiceCtrl = wx.Choice(panel, -1, choices=["                                           "])
        sizer.Add(self._framesChoiceCtrl, 1, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 1)
        self._framesChoiceCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnListRightClick)
        self.Bind(wx.EVT_CHOICE, self.ListItemSelected, self._framesChoiceCtrl)
        self._treeCtrl = wx.gizmos.TreeListCtrl(panel, -1, style=wx.TR_DEFAULT_STYLE| wx.TR_FULL_ROW_HIGHLIGHT)
        self._treeCtrl.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        panel_sizer.Add(sizer, 0, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 1)
        panel_sizer.Add(self._treeCtrl,1, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 1)
        tree = self._treeCtrl
        tree.AddColumn("Thing")
        tree.AddColumn("Value")
        tree.SetMainColumn(0) # the one with the tree in it...
        tree.SetColumnWidth(0, self.THING_COLUMN_WIDTH)
        tree.SetColumnWidth(1, 355)
        self._root = tree.AddRoot("Frame")
        tree.SetPyData(self._root, "root")
        tree.SetItemText(self._root, "", 1)
        tree.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.IntrospectCallback)
        panel.SetSizer(panel_sizer)
        
        return panel
        
    def MakeConsoleOutput(self, parent):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._textCtrl = DebugOutputCtrl.DebugOutputCtrl(parent, wx.NewId(),is_debug=True)
        sizer.Add(self._textCtrl, 1, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 2)
        self._textCtrl.HideLineNumber()
        self._textCtrl.SetReadOnly(True)
        if wx.Platform == '__WXMSW__':
            font = "Courier New"
        else:
            font = "Courier"
        self._textCtrl.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = font))
        self._textCtrl.SetFontColor(wx.BLACK)
        self._textCtrl.StyleClearAll()

        parent.SetSizer(sizer)
        #sizer.Fit(panel)
        
    def MakeWatchsTab(self, parent, id):
        panel = Watchs.WatchsPanel(parent, id,wx.GetApp().GetService(DebuggerService))
        return panel

    def ExecuteCommand(self, command):
        assert False, "ExecuteCommand not overridden"

    def MakeInspectConsoleTab(self, parent, id):
        def handleCommand():
            cmdStr = self._cmdInput.GetValue()
            if cmdStr:
                self._cmdList.append(cmdStr)
                self._cmdIndex = len(self._cmdList)
            self._cmdInput.Clear()
            self._cmdOutput.SetDefaultStyle(style=self._cmdOutputTextStyle)
            self._cmdOutput.AppendText(">>> " + cmdStr + "\n")
            self._cmdOutput.SetDefaultStyle(style=self._defaultOutputTextStyle)
            self.ExecuteCommand(cmdStr)
            return

        def OnCmdButtonPressed(event):
            if not BaseDebuggerUI.DebuggerRunning():
                wx.MessageBox(_("Debugger has been stopped."),style=wx.OK|wx.ICON_ERROR)
                return
            handleCommand()
            

        def OnKeyPressed(event):
            key = event.GetKeyCode()
            if key == wx.WXK_RETURN:
                handleCommand()
            elif key == wx.WXK_UP:
                if len(self._cmdList) < 1 or self._cmdIndex < 1:
                    return

                self._cmdInput.Clear()
                self._cmdInput.AppendText(self._cmdList[self._cmdIndex - 1])
                self._cmdIndex = self._cmdIndex - 1
            elif key == wx.WXK_DOWN:
                if len(self._cmdList) < 1 or self._cmdIndex >= len(self._cmdList):
                    return

                self._cmdInput.Clear()
                self._cmdInput.AppendText(self._cmdList[self._cmdIndex - 1])
                self._cmdIndex = self._cmdIndex + 1
            else:
                event.Skip()
            return

        def OnClrButtonPressed(event):
            self._cmdOutput.Clear()

        panel           = wx.Panel(parent, id)

        cmdLabel        = wx.StaticText(panel, -1, _("Cmd: "))
        #style wx.TE_PROCESS_ENTER will response enter key
        self._cmdInput  = wx.TextCtrl(panel,style = wx.TE_PROCESS_ENTER)
        ###self._cmdInput.Bind(wx.EVT_TEXT_ENTER,OnCmdButtonPressed)
        cmdButton       = wx.Button(panel, label=_("Execute"))
        clrButton       = wx.Button(panel, label=_("Clear"))
        self._cmdOutput = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY | wx.TE_RICH2)

        hbox            = wx.BoxSizer()
        hbox.Add(cmdLabel, proportion=0, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL)
        hbox.Add(self._cmdInput, proportion=1, flag=wx.EXPAND)
        hbox.Add(cmdButton, proportion=0, flag=wx.RIGHT)
        hbox.Add(clrButton, proportion=0, flag=wx.RIGHT)

        vbox            = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        vbox.Add(self._cmdOutput, proportion=1, flag=wx.EXPAND | wx.LEFT, border=2)

        panel.SetSizer(vbox)
        cmdButton.Bind(wx.EVT_BUTTON, OnCmdButtonPressed)
        clrButton.Bind(wx.EVT_BUTTON, OnClrButtonPressed)
        wx.EVT_KEY_DOWN(self._cmdInput, OnKeyPressed)

        fixedFont = wx.Font(self._cmdInput.GetFont().GetPointSize(), family=wx.TELETYPE, style=wx.NORMAL, weight=wx.NORMAL)
        self._defaultOutputTextStyle = wx.TextAttr("BLACK", wx.NullColour, fixedFont)
        self._cmdOutputTextStyle = wx.TextAttr("RED", wx.NullColour, fixedFont)
        self._cmdOutput.SetDefaultStyle(style=self._defaultOutputTextStyle)
        self._cmdList  = []
        self._cmdIndex = 0

        panel.Show()
        return panel

    def MakeBreakPointsTab(self, parent, id):
        panel = BreakPoints.BreakpointsUI(parent, id, self._ui,wx.GetApp().GetService(DebuggerService))
        return panel

    def OnRightClick(self, event):
        assert False, "OnRightClick not overridden"

    def ClearWhileRunning(self):
        list = self._framesChoiceCtrl
        list.Clear()
        list.Enable(False)
        tree = self._treeCtrl
        root = self._root
        tree.DeleteChildren(root)
        self._cmdInput.Enable(False)
        self._cmdOutput.Enable(False)

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

    def AppendText(self, text):
        self._textCtrl.AppendText(text,True)

    def AppendErrorText(self, text):
        self._textCtrl.AppendErrorText(text,True)

    def ClearOutput(self, event):
        self._textCtrl.ClearOutput()

    def SwitchToOutputTab(self):
        self._notebook.SetSelection(0)

class PythonFramesUI(BaseFramesUI):
    def __init__(self, parent, id, ui):
        BaseFramesUI.__init__(self, parent, id, ui)
        
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

    def OnAddWatch(self, event):
        self.AddWatch()
        
    def AddWatch(self,watch_obj=None):
        try:
            if hasattr(self, '_parentChain'):
                wd = Watchs.WatchDialog(wx.GetApp().GetTopWindow(), _("Add a Watch"), self._parentChain,watch_obj=watch_obj)
            else:
                wd = Watchs.WatchDialog(wx.GetApp().GetTopWindow(), _("Add a Watch"), None,watch_obj=watch_obj)
            wd.CenterOnParent()
            if wd.ShowModal() == wx.ID_OK:
                watch_obj = wd.GetSettings()
                self.AddtoWatch(watch_obj)
            wd.Destroy()
        except:
            tp, val, tb = sys.exc_info()
            traceback.print_exception(tp, val, tb)
            
    def OnAddToWatch(self,event):
        name = self._treeCtrl.GetItemText(self._introspectItem,0)
        watch_obj = Watchs.Watch.CreateWatch(name)
        self.AddtoWatch(watch_obj)
        
    def QuickAddWatch(self,watch_obj=None):
        wd = Watchs.WatchDialog(wx.GetApp().GetTopWindow(), _("Quick Add a Watch"), None,True,watch_obj)
        wd.CenterOnParent()
        if wd.ShowModal() == wx.ID_OK:
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
        list = self._framesChoiceCtrl
        frameNode = self._stack[int(self.currentItem)]
        file = frameNode.getAttribute("file")
        line = frameNode.getAttribute("line")
        self._ui.SynchCurrentLine( file, int(line) )

    def LoadFramesList(self, framesXML):
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        try:
            self._cmdInput.Enable(True)
            self._cmdOutput.Enable(True)

            try:
                domDoc = parseString(framesXML)
                list = self._framesChoiceCtrl
                list.Clear()
                self._stack = []
                nodeList = domDoc.getElementsByTagName('frame')
                frame_count = -1
                for index in range(0, nodeList.length):
                    frameNode = nodeList.item(index)
                    message = frameNode.getAttribute("message")
                    list.Append(message)
                    self._stack.append(frameNode)
                    frame_count += 1
                index = len(self._stack) - 1
                list.SetSelection(index)

                node = self._stack[index]
                self.currentItem = index
                self.PopulateTreeFromFrameNode(node)
                self.OnSyncFrame(None)

                self._p1.FitInside()
                frameNode = nodeList.item(index)
                file = frameNode.getAttribute("file")
                line = frameNode.getAttribute("line")
                self._ui.SynchCurrentLine( file, int(line) )
            except:
                tp,val,tb=sys.exc_info()
                traceback.print_exception(tp, val, tb)

        finally:
            wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))


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
        list = self._framesChoiceCtrl
        list.Enable(True)
        tree = self._treeCtrl
        #tree.Show(True)
        root = self._root
        tree.DeleteChildren(root)
        children = frameNode.childNodes
        firstChild = None
        for index in range(0, children.length):
            subNode = children.item(index)
            treeNode = self.AppendSubTreeFromNode(subNode, subNode.getAttribute('name'), root)
            if not firstChild:
                firstChild = treeNode
        tree.Expand(root)
        if firstChild:
            tree.Expand(firstChild)
        self._p2.FitInside()

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
        tree = self._treeCtrl
        if insertBefore != None:
            treeNode = tree.InsertItem(parent, insertBefore, name)
        else:
            treeNode = tree.AppendItem(parent, name)
        children = node.childNodes
        intro = node.getAttribute('intro')

        if intro == "True":
            tree.SetItemHasChildren(treeNode, True)
            tree.SetPyData(treeNode, "Introspect")
        if node.getAttribute("value"):
            tree.SetItemText(treeNode, self.StripOuterSingleQuotes(node.getAttribute("value")), 1)
        for index in range(0, children.length):
            subNode = children.item(index)
            if self.HasChildren(subNode):
                self.AppendSubTreeFromNode(subNode, subNode.getAttribute("name"), treeNode)
            else:
                name = subNode.getAttribute("name")
                value = self.StripOuterSingleQuotes(subNode.getAttribute("value"))
                n = tree.AppendItem(treeNode, name)
                tree.SetItemText(n, value, 1)
                intro = subNode.getAttribute('intro')
                if intro == "True":
                    tree.SetItemHasChildren(n, True)
                    tree.SetPyData(n, "Introspect")
        if name.find('[') == -1:
            self._treeCtrl.SortChildren(treeNode)
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
        if type(self._server) is not types.NoneType:
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
        self._service = wx.GetApp().GetService(DebuggerService)
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
            wx.MessageBox(_("Could not connect to break server!"),style=wx.OK|wx.ICON_ERROR)
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
            
        rbt = RequestBreakThread(self._breakServer, pushBreakpoints=True, breakDict=self._service.GetMasterBreakpointDict())
        rbt.start()
        
    def PushExceptionBreakpoints(self):
        self._debuggerServer.set_all_exceptions(self._service.GetExceptions())

    def WaitForRPC(self):
        self._waiting = True
        while self._waiting:
            try:
                self.ReadQueue()
                import time
                time.sleep(0.02)
            except:
                tp, val, tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)
            wx.GetApp().Yield(True)
        utils.GetLogger().debug("Exiting WaitForRPC.")

    def interaction(self, message, frameXML, info, quit):

        #This method should be hit as the debugger starts.
        #if the debugger starts.then show the debugger menu
        if self._firstInteraction:
            assert(self._debuggerUI._service != None)
            self._debuggerUI._service.ShowHideDebuggerMenu()
            self._firstInteraction = False
            self._debuggerServer = xmlrpclib.ServerProxy(self._debugger_url,  allow_none=1)
            self._breakServer = xmlrpclib.ServerProxy(self._break_url, allow_none=1)
            self.PushBreakpoints()
            if self._service.GetExceptions():
                self.PushExceptionBreakpoints()
        self._waiting = False
        if _VERBOSE: print ("+"*40)
        #quit gui server
        if(quit):
            #whhen quit gui server stop the debugger execution
            self._debuggerUI.StopExecution(None)
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
            self._timer = wx.PyTimer(self.DoContinue)
            self._autoContinue = False
            self._timer.Start(250)
        if _VERBOSE: print ("+"*40)

    def DoContinue(self):
        self._timer.Stop()
        dbgService = wx.GetApp().GetService(DebuggerService)
        evt = DebugInternalWebServer()
        evt.SetId(constants.ID_STEP_CONTINUE)
        wx.PostEvent(self._debuggerUI, evt)
        if _VERBOSE: print ("Event Continue posted")

        evt = DebugInternalWebServer()
        evt.SetId(DebuggerService.DEBUG_WEBSERVER_NOW_RUN_PROJECT_ID)
        wx.PostEvent(dbgService._frame, evt)
        if _VERBOSE: print ("Event RunProject posted")

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
        

class DebuggerView(core.View):
    def __init__(self,debugger):
        self._debugger = debugger
        core.View.__init__(self)
        
    def GetCtrl(self):
        select_page = self._debugger.bottomTab.get_current_child()
        if select_page is None:
            return None
        debugger_page = self.GetInstancePage(select_page)
        return debugger_page.GetOutputView().GetOutputCtrl()
        
    def GetInstancePage(self,tab_page):
        page = tab_page.winfo_children()[0]
        return page

class Debugger:

    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    RUN_PARAMETERS = []
    
    def AppendRunParameter(self,run_paramteter):
        if len(self.RUN_PARAMETERS) > 0:
            self.SaveRunParameter(self.RUN_PARAMETERS[-1])
        self.RUN_PARAMETERS.append(run_paramteter)
        
    def ComparePaths(first, second):
        one = DebuggerService.ExpandPath(first)
        two = DebuggerService.ExpandPath(second)
        if _WINDOWS:
            return one.lower() == two.lower()
        else:
            return one == two
    ComparePaths = staticmethod(ComparePaths)

    # Make sure we're using an expanded path on windows.
    def ExpandPath(path):
        if _WINDOWS:
            try:
                return win32api.GetLongPathName(path)
            except:
                if _VERBOSE:
                    print ("Cannot get long path for %s" % path)

        return path

    ExpandPath = staticmethod(ExpandPath)

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self):
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
        self._debugger_ui = None


        self.bottomTab = GetApp().MainFrame._view_notebooks['s']
        self.bottomTab.bind("<ButtonPress-3>", self._right_btn_press, True)
        self._tabs_menu = None
        self._popup_index = -1
        self._watch_separater = None
        self._view = self._CreateView()
        
    def _CreateView(self):
        return DebuggerView(self)
        
    def GetView(self):
        return self._view

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


    def CloseDebugger(self):
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

    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------

    def ShowHideDebuggerMenu(self,show=True):
        menuBar = wx.GetApp().GetTopWindow().GetMenuBar()
        runMenuIndex = menuBar.FindMenu(_("&Run"))
        runMenu = menuBar.GetMenu(runMenuIndex)
        ###BaseDebuggerUI.DebuggerRunning() 
        if show:
            menu_index = 3
            
            if self._watch_separater is None:
                self._watch_separater = runMenu.InsertSeparator(8)
            else:
                runMenu.InsertItem(8,self._watch_separater)
            if not menuBar.FindItemById(constants.ID_ADD_WATCH):
                item = wx.MenuItem(runMenu,constants.ID_ADD_WATCH, _("&Add Watch"), _("Add a Watch"))
                item.SetBitmap(Watchs.getAddWatchBitmap())
                runMenu.InsertItem(8,item)
                wx.EVT_MENU(self._frame, constants.ID_ADD_WATCH, self.ProcessEvent)
            
            if not menuBar.FindItemById(constants.ID_QUICK_ADD_WATCH):
                item = wx.MenuItem(runMenu,constants.ID_QUICK_ADD_WATCH, _("&Quick add Watch"), _("Quick add a Watch"))
                item.SetBitmap(Watchs.getQuickAddWatchBitmap())
                runMenu.InsertItem(8,item)
                wx.EVT_MENU(self._frame, constants.ID_QUICK_ADD_WATCH, self.ProcessEvent)
                
            if not menuBar.FindItemById(constants.ID_STEP_OUT):
                item = wx.MenuItem(runMenu,constants.ID_STEP_OUT, _("&Step Out\tShift+F11"), _("Step out the function"))
                item.SetBitmap(getStepReturnBitmap())
                runMenu.InsertItem(7,item)
                wx.EVT_MENU(self._frame, constants.ID_STEP_OUT, self.ProcessEvent)

            if not menuBar.FindItemById(constants.ID_RESTART_DEBUGGER):
                item = wx.MenuItem(runMenu,constants.ID_RESTART_DEBUGGER, _("&Restart"), _("Restart Debugging"))
                item.SetBitmap(getRestartDebuggerBitmap())
                runMenu.InsertItem(menu_index,item)
                wx.EVT_MENU(self._frame, constants.ID_RESTART_DEBUGGER, self.ProcessEvent)
                

            if not menuBar.FindItemById(constants.ID_TERMINATE_DEBUGGER):
                item = wx.MenuItem(runMenu,constants.ID_TERMINATE_DEBUGGER, _("&Stop Debugging"), _("Stop the debugger"))
                item.SetBitmap(getStopBitmap())
                runMenu.InsertItem(menu_index,item)
                wx.EVT_MENU(self._frame, constants.ID_TERMINATE_DEBUGGER, self.ProcessEvent)
                
            if not menuBar.FindItemById(constants.ID_BREAK_INTO_DEBUGGER):
                item = wx.MenuItem(runMenu,constants.ID_BREAK_INTO_DEBUGGER, _("&Break"), _("Break into the debugger"))
                item.SetBitmap(getBreakBitmap())
                runMenu.InsertItem(menu_index,item)
                wx.EVT_MENU(self._frame, constants.ID_BREAK_INTO_DEBUGGER, self.ProcessEvent)
                
            if not menuBar.FindItemById(constants.ID_STEP_CONTINUE):
                item = wx.MenuItem(runMenu,constants.ID_STEP_CONTINUE, _("&Continue"), _("Continue the debugger"))
                item.SetBitmap(getContinueBitmap())
                runMenu.InsertItem(menu_index,item)
                wx.EVT_MENU(self._frame, constants.ID_STEP_CONTINUE, self.ProcessEvent)
        else:
            ###TODO:Removes the menu item from the menu but doesn't delete the associated C++ object.
            ###we should use destroy to delete the menu permanently 
            if menuBar.FindItemById(constants.ID_STEP_OUT):
                runMenu.Remove(constants.ID_STEP_OUT)
            if menuBar.FindItemById(constants.ID_TERMINATE_DEBUGGER):
                runMenu.Remove(constants.ID_TERMINATE_DEBUGGER)
            if menuBar.FindItemById(constants.ID_STEP_CONTINUE):
                runMenu.Remove(constants.ID_STEP_CONTINUE)
            if menuBar.FindItemById(constants.ID_BREAK_INTO_DEBUGGER):
                runMenu.Remove(constants.ID_BREAK_INTO_DEBUGGER)
            if menuBar.FindItemById(constants.ID_RESTART_DEBUGGER):
                runMenu.Remove(constants.ID_RESTART_DEBUGGER)

            if menuBar.FindItemById(constants.ID_ADD_WATCH):
                runMenu.Remove(constants.ID_ADD_WATCH)
            if menuBar.FindItemById(constants.ID_QUICK_ADD_WATCH):
                runMenu.Remove(constants.ID_QUICK_ADD_WATCH)
                runMenu.RemoveItem(self._watch_separater)
    #----------------------------------------------------------------------------
    # Event Processing Methods
    #----------------------------------------------------------------------------
    def OnCombo(self, event):
        cb = wx.GetApp().ToolbarCombox
        selection = event.GetSelection()
        prompt = False
        if selection == cb.GetCount() - 1:
            if BaseDebuggerUI.DebuggerRunning():
                prompt = True
            else:
                UICommon.ShowInterpreterOptionPage()
        else:
            interpreter = cb.GetClientData(selection)
            if interpreter != wx.GetApp().GetCurrentInterpreter() and BaseDebuggerUI.DebuggerRunning():
                prompt = True
            else:
                self.SelectInterpreter(interpreter)
        if prompt:
            wx.MessageBox(_("Please stop the debugger first!"),style=wx.OK|wx.ICON_WARNING)
            wx.GetApp().SetCurrentInterpreter()
           
    def SelectInterpreter(self,interpreter):
        if interpreter != interpretermanager.InterpreterManager.GetCurrentInterpreter():
            interpretermanager.InterpreterManager.SetCurrentInterpreter(interpreter)
            if intellisence.IntellisenceManager().IsRunning:
                return
            intellisence.IntellisenceManager().load_intellisence_data(interpreter)
        
    def ProcessEventBeforeWindows(self, event):
        return False

    def ProcessEvent(self, event):
        if Service.Service.ProcessEvent(self, event):
            return True

        an_id = event.GetId()
        if an_id == constants.ID_TOGGLE_BREAKPOINT:
            self.OnToggleBreakpoint(event)
            return True
        elif an_id == constants.ID_CLEAR_ALL_BREAKPOINTS:
            self.ClearAllBreakpoints()
            return True
        elif an_id == constants.ID_RUN:
            self.OnRun(event)
            return True
        elif an_id == constants.ID_DEBUG:
            self.OnDebugRun(event)
            return True
        elif an_id == constants.ID_BREAK_INTO_DEBUGGER:
            self.OnBreakDebugger()
            return True
        elif an_id == constants.ID_START_WITHOUT_DEBUG:
            self.OnRunWithoutDebug(event)
            return True
        elif an_id == constants.ID_SET_EXCEPTION_BREAKPOINT:
            self.SetExceptionBreakPoint()
            return True
        elif an_id == constants.ID_CHECK_SYNTAX:
            self.CheckScript(event)
            return True
        elif an_id == constants.ID_RUN_LAST:
            self.RunLast(event)
            return True
        elif an_id == constants.ID_DEBUG_LAST:
            self.DebugRunLast(event)
            return True
        elif an_id == DebuggerService.DEBUG_WEBSERVER_ID:
            self.OnDebugWebServer(event)
            return True
        elif an_id == DebuggerService.DEBUG_WEBSERVER_CONTINUE_ID:
            self.OnDebugWebServerContinue(event)
            return True
        elif an_id == DebuggerService.DEBUG_WEBSERVER_NOW_RUN_PROJECT_ID:
            self.WaitDebuggerThenRunProject()
            return True
        elif an_id == DebuggerService.RUN_WEBSERVER_ID:
            self.OnRunWebServer(event)
            return True
        elif an_id == constants.ID_SET_PARAMETER_ENVIRONMENT:
            self.SetParameterAndEnvironment()
            return True
        elif an_id == constants.ID_TERMINATE_DEBUGGER:
            self._debugger_ui.StopExecution(None)
            return True
        elif an_id == constants.ID_STEP_INTO:
            self.OnStepInto()
            return True
        elif an_id == constants.ID_STEP_NEXT:
            self.OnStepNext()
            return True
        elif an_id == constants.ID_STEP_OUT:
            self._debugger_ui.OnStepOut(None)
            return True
        elif an_id == constants.ID_STEP_CONTINUE:
            self._debugger_ui.OnContinue(None)
            return True

        elif an_id == constants.ID_QUICK_ADD_WATCH:
            active_text_view = self.GetActiveView()
            if active_text_view is not None:
                active_text_view.GetCtrl().QuickAddWatch(None)
            else:
                self.AddWatch(None,True)
            return True

        elif an_id == constants.ID_ADD_WATCH:
            active_text_view = self.GetActiveView()
            if active_text_view is not None:
                active_text_view.GetCtrl().AddWatch(None)
            else:
                self.AddWatch(None,False)
            return True

        elif an_id == constants.ID_RESTART_DEBUGGER:
            self._debugger_ui.RestartDebugger(None)
            return True
        return False
        
    def OnStepNext(self):
        if BaseDebuggerUI.DebuggerRunning():
            self._debugger_ui.OnNext(None)
        else:
            self.BreakIntoDebugger()
        
    def OnStepInto(self):
        if BaseDebuggerUI.DebuggerRunning():
            self._debugger_ui.OnSingleStep(None)
        else:
            self.BreakIntoDebugger()
            
    def OnBreakDebugger(self):
        self._debugger_ui.BreakExecution(None)
        
    def IsRunFileEnable(self):
        interpreter = wx.GetApp().GetCurrentInterpreter()
        if interpreter and interpreter.IsBuiltIn:
            return False
        else:
            if wx.GetApp().GetService(project.ProjectEditor.ProjectService).GetView().GetDocument() is None:
                return self.HasAnyFiles() and self.GetActiveView().GetLangId() == lang.ID_LANG_PYTHON
            return True

    def ProcessUpdateUIEvent(self, event):
        if Service.Service.ProcessUpdateUIEvent(self, event):
            return True

        an_id = event.GetId()
        if an_id == constants.ID_TOGGLE_BREAKPOINT:
            currentView = self.GetDocumentManager().GetCurrentView()
            event.Enable(isinstance(currentView, PythonEditor.PythonView))
            return True
        elif an_id == constants.ID_CLEAR_ALL_BREAKPOINTS:
            event.Enable(self.HasBreakpointsSet())
            return True
        elif an_id == constants.ID_RUN_LAST:
            interpreter = wx.GetApp().GetCurrentInterpreter()
            if interpreter and interpreter.IsBuiltIn:
                event.Enable(False)
            else:
                event.Enable(True)
            return True
        elif (an_id == constants.ID_RUN
        or an_id == constants.ID_SET_EXCEPTION_BREAKPOINT):
            event.Enable(self.IsRunFileEnable())
            return True
        elif (an_id == constants.ID_DEBUG
        or an_id == constants.ID_START_WITHOUT_DEBUG
        or an_id == constants.ID_CHECK_SYNTAX
        or an_id == constants.ID_SET_PARAMETER_ENVIRONMENT):
            if wx.GetApp().GetService(project.ProjectEditor.ProjectService).GetView().GetDocument() is None:
                event.Enable(self.HasAnyFiles() and \
                        self.GetActiveView().GetLangId() == lang.ID_LANG_PYTHON)
            else:
                event.Enable(True)
            return True
        elif (an_id == constants.ID_STEP_NEXT
        or an_id == constants.ID_STEP_INTO):
            if not self.IsRunFileEnable():
                event.Enable(False)
            elif self._debugger_ui is None or not BaseDebuggerUI.DebuggerRunning():
                event.Enable(True)
            else:
                event.Enable(self._debugger_ui._tb.GetToolEnabled(self._debugger_ui.STEP_NEXT_ID))
            return True
        else:
            return False
    #----------------------------------------------------------------------------
    # Class Methods
    #----------------------------------------------------------------------------
    
    def CheckScript(self):
        if not Executor.GetPythonExecutablePath():
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
            
    def GetKey(self, currentProj,lastPart):
        if currentProj:
            return currentProj.GetKey(lastPart)
        return lastPart
            
    def SaveRunParameter(self,run_parameter):
        cur_project_document = GetApp().MainFrame.GetProjectView(generate_event=False).GetCurrentProject()
        if cur_project_document is None:
            project_name = consts.NOT_IN_ANY_PROJECT
            cur_project_document = projectviewer.PythonProjectDocument()
        else:
            project_name = os.path.basename(cur_project_document.GetFilename())
        utils.profile_set(self.GetKey(cur_project_document,"LastRunProject"), project_name)
        utils.profile_set(self.GetKey(cur_project_document,"LastRunFile"), run_parameter.FilePath)
        # Don't update the arguments or starting directory unless we're runing python.
        utils.profile_set(self.GetKey(cur_project_document,"LastRunArguments"), run_parameter.Arg)
        utils.profile_set(self.GetKey(cur_project_document,"LastRunStartIn"), run_parameter.StartupPath)
        if run_parameter.Environment is not None and consts.PYTHON_PATH_NAME in run_parameter.Environment:
            utils.profile_set(self.GetKey(cur_project_document,"LastPythonPath"),run_parameter.Environment[consts.PYTHON_PATH_NAME])

    def DebugRunBuiltin(self,run_parameter):
        fileToRun = run_parameter.FilePath
        GetApp().MainFrame.ShowView(consts.PYTHON_INTERPRETER_VIEW_NAME,toogle_visibility_flag=True)
        python_interpreter_view = GetApp().MainFrame.GetCommonView(consts.PYTHON_INTERPRETER_VIEW_NAME)
        old_argv = sys.argv
        environment,initialArgs = run_parameter.Environment,run_parameter.Arg
        sys.argv = [fileToRun]
        command = 'execfile(r"%s")' % fileToRun
        python_interpreter_view.run(command)
        sys.argv = old_argv

    def IsProjectContainBreakPoints(self,cur_project):
        for key in self._masterBPDict:
            if cur_project.FindFile(key) and len(self._masterBPDict[key]) > 0:
                return True
        return False
        
    def GetProjectStartupFile(self,project_document):
        startup_file = project_document.GetStartupFile()
        if startup_file is None:
            messagebox.showerror(GetApp().GetAppName(),_("Your project needs a Python script marked as startup file to perform this action"))
            #show the property dialog to remind user to set the startup file
            GetApp().MainFrame.GetProjectView(generate_event=False).OnProjectProperties(item_name="Debug/Run")
            return None
        return startup_file
        
    def IsFileContainBreakPoints(self,document):
        doc_path = document.GetFilename()
        if doc_path in self._masterBPDict and len(self._masterBPDict[doc_path]) > 0:
            return True
        return False
        
    def GetRunConfiguration(self):
        '''
            get selected run configuration of current project
        '''
        cur_project_document = self.GetCurrentProject()
        if cur_project_document is None:
            return ''
        pj_key = cur_project_document.GetKey()
        run_configuration_name = utils.profile_get(pj_key + "/RunConfigurationName","")
        return run_configuration_name
        
    def GetCurrentProject(self):
        return GetApp().MainFrame.GetProjectView(generate_event=False).GetCurrentProject()
        
    def GetActiveView(self):
        return GetApp().GetDocumentManager().GetCurrentView()
        
    def GetFileRunParameter(self,filetoRun=None,is_break_debug=False):
        cur_project_document = self.GetCurrentProject()
        
        #when there is not project or run file is not in current project
        # run one single python file
        if cur_project_document is None or (filetoRun is not None and \
                    cur_project_document.GetModel().FindFile(filetoRun) is None):
            doc_view = self.GetActiveView()
            if doc_view:
                document = doc_view.GetDocument()
                if not document.Save() or document.IsNewDocument:
                    return None
                if self.IsFileContainBreakPoints(document) or is_break_debug:
                    wx.MessageBox(_("Debugger can only run in active project"),style=wx.OK|wx.ICON_WARNING)
            else:
                return None
            run_parameter = document.GetRunParameter()
        else:
            #run project
            if filetoRun is None:
                #default run project start up file
                start_up_file = self.GetProjectStartupFile(cur_project_document)
            else:
                start_up_file = cur_project_document.GetModel().FindFile(filetoRun)
            if not start_up_file:
                return None
            self.PromptToSaveFiles(cur_project_document)
            run_parameter = cur_project_document.GetRunParameter(start_up_file)
        return run_parameter
        
    def GetRunParameter(self,filetoRun=None,is_break_debug=False):
        '''
            @is_break_debug:user force to debug breakpoint or not
        '''
        if not Executor.GetPythonExecutablePath():
            return None
        cur_project_document = self.GetCurrentProject()
        is_debug_breakpoint = False
        #load project configuration first,if have one run configuration,the run it
        run_configuration_name = self.GetRunConfiguration()
        #if user force run one project file ,then will not run configuration from config
        if filetoRun is None and run_configuration_name:
            project_configuration = runconfiguration.ProjectConfiguration(cur_project_document)
            run_configuration = project_configuration.LoadConfiguration(run_configuration_name)
            #if run configuration name does not exist,then run in normal
            if not run_configuration:
                run_parameter = self.GetFileRunParameter(filetoRun,is_break_debug)
            else:
                run_parameter = run_configuration.GetRunParameter()
                #try:
                 #   run_parameter = run_configuration.GetRunParameter()
                #except PromptErrorException as e:
                 #   wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR)
                  #  return None
        else:
            run_parameter = self.GetFileRunParameter(filetoRun,is_break_debug)
        
        #invalid run parameter
        if run_parameter is None:
                return None
                    
        #check project files has breakpoint,if has one breakpoint,then run in debugger mode
        if cur_project_document is not None:
            cur_project = cur_project_document.GetModel()
            if self.IsProjectContainBreakPoints(cur_project):
                is_debug_breakpoint = True
            
        run_parameter = pyutils.get_override_runparameter(run_parameter)
        run_parameter.IsBreakPointDebug = is_debug_breakpoint
        #check interprter path contain chinese character or not
        if utils.profile_get_int("WarnInterpreterPath", True):
            #if path have chinese character,prompt a warning message
            run_parameter.Interpreter.CheckPathEncoding()
        return run_parameter
        
    def DebugRun(self):
        run_parameter = self.GetRunParameter()
        if run_parameter is None:
            return
        if not run_parameter.IsBreakPointDebug:
            self.DebugRunScript(run_parameter)
        else:
            self.DebugRunScriptBreakPoint(run_parameter)
        self.AppendRunParameter(run_parameter)
            
    def DebugRunScript(self,run_parameter):
      #  self.ShowWindow(True)
        if run_parameter.Interpreter.IsBuiltIn:
            self.DebugRunBuiltin(run_parameter)
            return
        fileToRun = run_parameter.FilePath
        shortFile = os.path.basename(fileToRun)
        view = GetApp().MainFrame.AddView("Debugger"+ str(uuid.uuid1()).lower(),RunCommandUI,_("Running: ") + shortFile,"s",visible_by_default=True,\
                                   image_file="python/debugger/debug.ico",debugger=self, fileName=fileToRun,run_parameter=run_parameter,visible_in_menu=False)
        page = view['instance']
        page.Execute(onWebServer = False)
        GetApp().GetDocumentManager().ActivateView(self.GetView())
        
    def SetExceptionBreakPoint(self):
        exception_dlg = BreakPoints.BreakpointExceptionDialog(wx.GetApp().GetTopWindow(),-1,_("Add Python Exception Breakpoint"))
        exception_dlg.CenterOnParent()
        if exception_dlg.ShowModal() == wx.ID_OK:
            wx.GetApp().GetService(DebuggerService).SetExceptions(exception_dlg.exceptions)
        exception_dlg.Destroy()
        
    def OnRunWithoutDebug(self):
        self.RunWithoutDebug()
        
    def RunWithoutDebug(self,filetoRun=None):
        run_parameter = self.GetRunParameter(filetoRun)
        if run_parameter is None:
            return
        run_parameter.IsBreakPointDebug = False
        self.DebugRunScript(run_parameter)
        self.AppendRunParameter(run_parameter)
        
    def BreakIntoDebugger(self,filetoRun=None):
        run_parameter = self.GetRunParameter(filetoRun,is_break_debug=True)
        #debugger must run in project
        if run_parameter is None or run_parameter.Project is None:
            return
        run_parameter.IsBreakPointDebug = True
        self.DebugRunScriptBreakPoint(run_parameter,autoContinue=False)
        
    def Run(self,filetoRun=None):
        run_parameter = self.GetRunParameter(filetoRun)
        if run_parameter is None:
            return
        try:
            self.RunScript(run_parameter)
        except StartupPathNotExistError as e:
            messagebox.showerror(_("Startup path not exist"),str(e),parent=GetApp().GetTopWindow())
            return
        except Exception as e:
            messagebox.showerror(_("Run Error"),str(e),parent=GetApp().GetTopWindow())
            return
        self.AppendRunParameter(run_parameter)
            
    def RunScript(self,run_parameter):
        interpreter = run_parameter.Interpreter
        if interpreter.IsBuiltIn:
            return
        if sysutilslib.is_windows():
            #should convert to unicode when interpreter path contains chinese character
            python_executable_path = interpreter.GetUnicodePath()
        else:
            python_executable_path = interpreter.Path
        sys_encoding = sysutilslib.get_default_encoding()
        fileToRun = run_parameter.FilePath
        startIn,environment,initialArgs = run_parameter.StartupPath,run_parameter.Environment,run_parameter.Arg
        if not os.path.exists(startIn):
            raise StartupPathNotExistError(startIn)

        if utils.is_py2():
            initDir = startIn.encode(sys_encoding)
        else:
            initDir = startIn
        
        cmd = u"%s \"%s\"" % (strutils.emphasis_path(python_executable_path),fileToRun)
        if initialArgs is not None:
            cmd += " " + initialArgs
        terminal.run_in_terminal(cmd,initDir,environment,keep_open=False,pause=True,title="abc")
            
    def GetLastRunParameter(self,is_debug):
        if not Executor.GetPythonExecutablePath():
            return None
        dlg_title = _('Run File')
        btn_name = _("Run")
        if is_debug:
           dlg_title = _('Debug File')
           btn_name = _("Debug")
        dlg = CommandPropertiesDialog(GetApp().GetTopWindow(),dlg_title, GetApp().MainFrame.GetProjectView(), okButtonName=btn_name, debugging=is_debug,is_last_config=True)
        showDialog = dlg.MustShowDialog()
        is_parameter_save = False
        if showDialog and dlg.ShowModal() == constants.ID_OK:
            projectDocument, fileToDebug, initialArgs, startIn, isPython, environment = dlg.GetSettings()
            #when show run dialog first,need to save parameter
            is_parameter_save = True
        elif not showDialog:
            #隐藏窗口
            dlg.withdraw()
            projectDocument, fileToDebug, initialArgs, startIn, isPython, environment = dlg.GetSettings()
            dlg.destroy()
        else:
            dlg.Destroy()
            return None
        if projectDocument.GetFilename() != consts.NOT_IN_ANY_PROJECT and self.IsProjectContainBreakPoints(projectDocument.GetModel()):
            is_debug_breakpoint = True
        else:
            is_debug_breakpoint = False
        run_parameter = runconfig.PythonRunconfig(GetApp().GetCurrentInterpreter(),\
                            fileToDebug,initialArgs,environment,startIn,is_debug_breakpoint)
        if is_parameter_save:
            self.SaveRunParameter(run_parameter)
        return run_parameter
            
    def DebugRunLast(self):
        run_parameter = self.GetLastRunParameter(True)
        if run_parameter is None:
            return
        run_parameter = pyutils.get_override_runparameter(run_parameter)
        if not run_parameter.IsBreakPointDebug:
            self.DebugRunScript(run_parameter)
        else:
            self.DebugRunScriptBreakPoint(run_parameter)
        
    def RunLast(self):
        run_parameter = self.GetLastRunParameter(False)
        if run_parameter is None:
            return
        run_parameter = pyutils.get_override_runparameter(run_parameter)
        try:
            self.RunScript(run_parameter)
        except StartupPathNotExistError as e:
            wx.MessageBox(e.msg,_("Startup path not exist"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
        except Exception as e:
            wx.MessageBox(str(e),_("Run Error"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
        
    def DebugRunScriptBreakPoint(self,run_parameter,autoContinue=True):
        '''
            autoContinue will determine whether debugger break first 
        '''
        if _WINDOWS and not _PYWIN32_INSTALLED:
            wx.MessageBox(_("Python for Windows extensions (pywin32) is required to debug on Windows machines. Please download and install pywin32 via pip tool"))
            return
        if BaseDebuggerUI.DebuggerRunning():
            wx.MessageBox(_("A debugger is already running. Please shut down the other debugger first."), _("Debugger Running"))
            return
        config = wx.ConfigBase_Get()
        host = config.Read("DebuggerHostName", DEFAULT_HOST)
        if not host:
            wx.MessageBox(_("No debugger host set. Please go to Tools->Options->Debugger and set one."), _("No Debugger Host"))
            return
        self.ShowWindow(True)
        fileToDebug = run_parameter.FilePath
        fileToDebug = DebuggerService.ExpandPath(fileToDebug)
        shortFile = os.path.basename(fileToDebug)

        self._debugger_ui = PythonDebuggerUI(self._frame, -1, str(fileToDebug),self,run_parameter,autoContinue=autoContinue)
        target_pane = self.GetTargetPane(aui.AUI_DOCK_BOTTOM)
        pane_info = self.CreatePane(aui.AUI_DOCK_BOTTOM,target=target_pane,control=self._debugger_ui,caption=_("Debugging: ") + shortFile,\
                                    name= self.GetServiceName() + str(uuid.uuid1()).lower(),icon=self.GetBreakDebugIcon())
        self._frame._mgr.Update()
        
        self._debugger_ui.Execute()

    def HasAnyFiles(self):
        docs = wx.GetApp().GetDocumentManager().GetDocuments()
        return len(docs) > 0 and self.GetActiveView() != None

    def PromptToSaveFiles(self, cur_project_document):
        def save_docs():
            for modify_doc in modify_docs:
                modify_doc.Save()
            
        filesModified = False
        modify_docs = []
        docs = GetApp().GetDocumentManager().GetDocuments()
        for doc in docs:
              if doc.IsModified() and (cur_project_document == GetApp().MainFrame.GetProjectView(show=False,generate_event=False).FindProjectFromMapping(doc) or\
                                     cur_project_document.GetModel().FindFile(doc.GetFilename())):
                filesModified = True
                modify_docs.append(doc)
        if filesModified:
            if utils.profile_get_int("PromptSaveProjectFile", True):
                yesNoMsg = messagebox.askyesno(_("Run Project"),
                          _("Files have been modified.\nWould you like to save all files before running?")
                          )
                if yesNoMsg == True:
                    save_docs()
            else:
                save_docs()

    def OnExit(self):
        BaseDebuggerUI.ShutdownAllDebuggers()
        RunCommandUI.ShutdownAllRunners()

    def SetParameterAndEnvironment(self):
        projectview = GetApp().MainFrame.GetProjectView()
        dlg = CommandPropertiesDialog(GetApp().GetTopWindow(), _('Set Parameter And Environment'), projectview,okButtonName=_("&OK"))
        dlg.ShowModal()

    def OnToggleBreakpoint(self, event, line=-1, fileName=None):
        if not fileName:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            # Test to make sure we aren't the project view.
            if not hasattr(view, 'MarkerExists'):
                return
            fileName = wx.GetApp().GetDocumentManager().GetCurrentDocument().GetFilename()
            if line < 0:
                line = view.GetCtrl().GetCurrentLine()
        else:
            view = None
        if  self.BreakpointSet(fileName, line + 1):
            self.ClearBreak(fileName, line + 1)
            if view:
                view.GetCtrl().Refresh()
        else:
            self.SetBreak(fileName, line + 1)
            if view:
                view.GetCtrl().Refresh()
        # Now refresh all the markers icons in all the open views.
        self.ClearAllBreakpointMarkers()
        self.SetAllBreakpointMarkers()

    def SilentToggleBreakpoint(self, fileName, line):
        found = False
        for lineNumber in self.GetBreakpointList(fileName):
            if int(lineNumber) == int(line):
                found = True
                break
        if found:
            self.SetBreak(fileName, line)
        else:
            self.ClearBreak(fileName, line)

    def SetBreak(self, fileName, line):
        expandedName = DebuggerService.ExpandPath(fileName)
        if not self._masterBPDict.has_key(expandedName):
            self._masterBPDict[expandedName] = [line]
        else:
            self._masterBPDict[expandedName] += [line]
        # If we're already debugging, pass this bp off to the PythonDebuggerCallback
        self.NotifyDebuggersOfBreakpointChange()
        
    def GetExceptions(self):
        return self._exceptions
        
    def SetExceptions(self,exceptions):
        self._exceptions = exceptions

    def NotifyDebuggersOfBreakpointChange(self):
        BaseDebuggerUI.NotifyDebuggersOfBreakpointChange()

    def GetBreakpointList(self, fileName):
        expandedName = DebuggerService.ExpandPath(fileName)
        if not self._masterBPDict.has_key(expandedName):
            return []
        else:
            return self._masterBPDict[expandedName]

    def SetBreakpointList(self, fileName, bplist):
        expandedName = DebuggerService.ExpandPath(fileName)
        self._masterBPDict[expandedName] = bplist

    def BreakpointSet(self, fileName, line):
        expandedName = DebuggerService.ExpandPath(fileName)
        if not self._masterBPDict.has_key(expandedName):
            return False
        else:
            newList = []
            for number in self._masterBPDict[expandedName]:
                if(int(number) == int(line)):
                    return True
        return False

    def ClearBreak(self, fileName, line):
        expandedName = DebuggerService.ExpandPath(fileName)
        if not self._masterBPDict.has_key(expandedName):
            print ("In ClearBreak: no key")
            return
        else:
            newList = []
            for number in self._masterBPDict[expandedName]:
                if(int(number) != int(line)):
                    newList.append(number)
            self._masterBPDict[expandedName] = newList
        self.NotifyDebuggersOfBreakpointChange()

    def HasBreakpointsSet(self):
        for key, value in self._masterBPDict.items():
            if len(value) > 0:
                return True
        return False

    def ClearAllBreakpoints(self):
        self._masterBPDict = {}
        self.NotifyDebuggersOfBreakpointChange()
        self.ClearAllBreakpointMarkers()

    def ClearAllBreakpointMarkers(self):
        openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if isinstance(openDoc, CodeEditor.CodeDocument):
                openDoc.GetFirstView().MarkerDeleteAll(CodeEditor.CodeCtrl.BREAKPOINT_MARKER_NUM)

    def UpdateBreakpointsFromMarkers(self, view, fileName):
        newbpLines = view.GetMarkerLines(CodeEditor.CodeCtrl.BREAKPOINT_MARKER_NUM)
        self.SetBreakpointList(fileName, newbpLines)

    def GetMasterBreakpointDict(self):
        return self._masterBPDict

    def SetAllBreakpointMarkers(self):
        openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if(isinstance(openDoc, CodeEditor.CodeDocument)):
                self.SetCurrentBreakpointMarkers(openDoc.GetFirstView())

    def SetCurrentBreakpointMarkers(self, view):
        if isinstance(view, CodeEditor.CodeView) and hasattr(view, 'GetDocument'):
            view.MarkerDeleteAll(CodeEditor.CodeCtrl.BREAKPOINT_MARKER_NUM)
            for linenum in self.GetBreakpointList(view.GetDocument().GetFilename()):
                view.MarkerAdd(lineNum=int(linenum) - 1, marker_index=CodeEditor.CodeCtrl.BREAKPOINT_MARKER_NUM)

    def GetPhpDbgParam(self):
        return self.phpDbgParam

    def SetPhpDbgParam(self, value = None):
        self.phpDbgParam = value
        
    def GetBreakDebugIcon(self):
        return images.load("debugger/debugger.png")
        
    def AppendWatch(self,watch_obj):
        self.watchs.append(watch_obj)
        
    def AddtoWatch(self,watch_obj):
        self._debugger_ui.framesTab.AddtoWatch(watch_obj)
        
    def AddWatch(self,watch_obj=None,is_quick_watch=False):
        if is_quick_watch:
            self._debugger_ui.framesTab.QuickAddWatch(watch_obj)
        else:
            self._debugger_ui.framesTab.AddWatch(watch_obj)
        
    def UpdateWatchs(self,reset=False):
        self._debugger_ui.UpdateWatchs(reset)

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
            wx.MessageBox(_("The starting port is not valid. Please change the value and try again.", "Invalid Starting Port Number"))

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


class CommandPropertiesDialog(ui_base.CommonModaldialog):
    def __init__(self, parent, title, projectview, okButtonName="&OK", debugging=False,is_last_config=False):
        self._projectview = projectview
        self._is_last_config = is_last_config
        self._currentProj = self._projectview.GetCurrentProject()
        self._projectNameList, self._projectDocumentList, selectedIndex = self.GetProjectList()
        if not self._projectNameList:
            wx.MessageBox(_("To run or debug you must have an open runnable file or project containing runnable files. Use File->Open to open the file you wish to run or debug."), _("Nothing to Run"))
            raise Exception("Nothing to Run or Debug.")

        ui_base.CommonModaldialog.__init__(self, parent)
        self.title(title)
        self.main_frame.columnconfigure(1, weight=1)

        ttk.Label(self.main_frame, text=_("PYTHONPATH:")).grid(row=4,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text=_("Project:")).grid(row=0,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text=_("File:")).grid(row=1,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text=_("Arguments:")).grid(row=2,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text=_("Start in:")).grid(row=3,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        postpendStaticText = _("Postpend content root path")
        self._projectNameVar = tk.StringVar()
        self._projList = ttk.Combobox(self.main_frame, values=self._projectNameList,textvariable=self._projectNameVar)
        self._projList['state'] = 'readonly'
        self._projList.grid(row=0,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2,padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        self._projList.bind("<<ComboboxSelected>>",self.EvtListBox)

        self._fileList = ttk.Combobox(self.main_frame)
        self._fileList['state'] = 'readonly'
        self._fileList.grid(row=1,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2,padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        self._fileList.bind("<<ComboboxSelected>>",self.OnFileSelected)
  
        self._lastArguments = utils.profile_get(self.GetKey("LastRunArguments"))
        self._lastArgumentsVar = tk.StringVar(value=self._lastArguments)
        row = ttk.Frame(self.main_frame)
        self._argsEntry = ttk.Combobox(row,values=[],textvariable=self._lastArgumentsVar)
        self._argsEntry.pack(side=tk.LEFT,fill="x",expand=1)
             
        self._useArgCheckBoxVar = tk.IntVar(value=1)
        useArgCheckBox = ttk.Checkbutton(row, text= _("Use"),command=self.CheckUseArgument,variable=self._useArgCheckBoxVar)
        useArgCheckBox.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0))
        
        row.grid(row=2,column=1,sticky=tk.NSEW,columnspan=2,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_HALF_CONTRL_PAD_X))

        self._lastStartIn = utils.profile_get(self.GetKey("LastRunStartIn"),os.getcwd())
        self._lastStartInVar = tk.StringVar(value=self._lastStartIn)
        startEntry = ttk.Entry(self.main_frame, textvariable=self._lastStartInVar)
        startEntry.grid(row=3,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_HALF_CONTRL_PAD_X))

        self._findDir = ttk.Button(self.main_frame,text=_("Browse..."),command=self.OnFindDirClick)
        self._findDir.grid(row=3,column=2,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
    
        if 'PYTHONPATH' in os.environ:
            startval = os.environ['PYTHONPATH']
        else:
            startval = ""
        self._lastPythonPath = utils.profile_get(self.GetKey("LastPythonPath"), startval)
        self._lastPythonPathVar = tk.StringVar(value=self._lastPythonPath)
        pythonPathEntry = ttk.Entry(self.main_frame, textvariable=self._lastPythonPathVar)
        pythonPathEntry.grid(row=4,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2,padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        misc.create_tooltip(pythonPathEntry,_('multiple path is seperated by %s') % os.pathsep)

        last_row = 4
        if self._projectview.GetCurrentProject() is not None:
            last_row += 1
            self._postpendCheckBoxVar = tk.IntVar(value=1)
            self._postpendCheckBox = ttk.Checkbutton(self.main_frame, text=postpendStaticText,variable=self._postpendCheckBoxVar)
            self._postpendCheckBox.grid(row=last_row,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2)
        # Set up selections based on last values used.
        self._fileNameList = None
        self._selectedFileIndex = -1
        lastProject = utils.profile_get(self.GetKey("LastRunProject"))
        lastFile = utils.profile_get(self.GetKey("LastRunFile"))
        self._mustShow = not lastFile

        if lastProject in self._projectNameList:
            selectedIndex = self._projectNameList.index(lastProject)
        elif selectedIndex < 0:
            selectedIndex = 0
        self._projList.current(selectedIndex)
        self._selectedProjectIndex = selectedIndex
        self._selectedProjectDocument = self._projectDocumentList[selectedIndex]
        self.PopulateFileList(self._selectedProjectDocument, lastFile)
        
        if not self._is_last_config:
            self.SetEntryParams()
        last_row += 1
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.grid(row=last_row,column=0,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=3)
        self.AppendokcancelButton(bottom_frame)

    def MustShowDialog(self):
        return self._mustShow

    def GetKey(self, lastPart):
        if self._currentProj:
            return self._currentProj.GetKey(lastPart)
        return lastPart
        
    def GetProjectFileKey(self, filepath,lastPart):
        if not self._currentProj:
            return self.GetKey(lastPart)
        if self._currentProj.GetFilename() == consts.NOT_IN_ANY_PROJECT:
            return self._currentProj.GetUnProjectFileKey(filepath,lastPart)
        else:
            pj_file = self._currentProj.GetModel().FindFile(filepath)
            if pj_file is None:
                return self.GetKey(lastPart)
            return self._currentProj.GetFileKey(pj_file,lastPart)
            
    def SetEntryParams(self):
        self._lastArgumentsVar.set("")
        if self._selectedFileIndex >= 0 and len(self._fileNameList) > self._selectedFileIndex:
            selected_filename = self._fileNameList[self._selectedFileIndex]
        else:
            selected_filename = ""
        argments = utils.profile_get(self.GetProjectFileKey(selected_filename,"RunArguments"),"")
        self._lastArgumentsVar.set(argments)
        self._lastPythonPathVar.set(utils.profile_get(self.GetProjectFileKey(selected_filename,"PythonPath"),""))
        startin = utils.profile_get(self.GetProjectFileKey(selected_filename,"RunStartIn"),"")
        self._lastStartInVar.set(startin)
        saved_arguments = utils.profile_get(self.GetProjectFileKey(selected_filename,"FileSavedArguments"),[])
        if saved_arguments:
            self._argsEntry['values'] = saved_arguments
        self._useArgCheckBoxVar.set(utils.profile_get_int(self.GetProjectFileKey(selected_filename,"UseArgument"),True))
        self.CheckUseArgument()
        
        if hasattr(self, "_postpendCheckBox"):
            if self._projectNameVar.get() == consts.NOT_IN_ANY_PROJECT:
                self._postpendCheckBox['state'] = tk.DISABLED
            else:
                self._postpendCheckBox['state'] = tk.NORMAL
                checked = bool(utils.profile_get_int(self.GetKey("PythonPathPostpend"), True))
                self._postpendCheckBoxVar.set(checked)
        
    def _ok(self,event=None):
        startIn = self._lastStartInVar.get().strip()
        if self._selectedFileIndex >= 0 and len(self._fileNameList) > self._selectedFileIndex:
            fileToRun = self._fileNameList[self._selectedFileIndex]
        else:
            fileToRun = ""
        if not fileToRun:
            messagebox.showinfo(GetApp().GetAppName(),_("You must select a file to proceed. Note that not all projects have files that can be run or debugged."))
            return
        isPython = fileutils.is_python_file(fileToRun)
        if isPython and not os.path.exists(startIn) and startIn != '':
            messagebox.showinfo(GetApp().GetAppName(),_("Starting directory does not exist. Please change this value."))
            return
        # Don't update the arguments or starting directory unless we're runing python.
        if isPython:
            utils.profile_set(self.GetProjectFileKey(fileToRun,"RunStartIn"), startIn)
            utils.profile_set(self.GetProjectFileKey(fileToRun,"PythonPath"),self._lastPythonPathVar.get().strip())
            utils.profile_set(self.GetProjectFileKey(fileToRun,"UseArgument"), self._useArgCheckBoxVar.get())
            #when use argument is checked,save argument
            if self._useArgCheckBoxVar.get():
                utils.profile_set(self.GetProjectFileKey(fileToRun,"RunArguments"), self._lastArgumentsVar.get())
                arguments = set()
                values = self._argsEntry['values']
                if not values:
                    values = []
                values = list(values)
                values.append(self._lastArgumentsVar.get())
                arguments = set(values)
                utils.profile_set(self.GetProjectFileKey(fileToRun,"FileSavedArguments"),list(arguments))
            if hasattr(self, "_postpendCheckBox"):
                utils.profile_set(self.GetKey("PythonPathPostpend"), self._postpendCheckBoxVar.get())
                
        ui_base.CommonModaldialog._ok(self,event=None)

    def GetSettings(self):
        projectDocument = self._selectedProjectDocument
        if self._selectedFileIndex >= 0 and len(self._fileNameList) > self._selectedFileIndex:
            fileToRun = self._fileNameList[self._selectedFileIndex]
        else:
            fileToRun = ""
        filename = utils.profile_get(self.GetKey("LastRunFile"),fileToRun)
        args = self._lastArgumentsVar.get()
        startIn = self._lastStartInVar.get().strip()
        isPython = fileutils.is_python_file(filename)
        env = {}
        if hasattr(self, "_postpendCheckBox"):
            postpend = self._postpendCheckBoxVar.get()
        else:
            postpend = False
        if postpend:
            env[consts.PYTHON_PATH_NAME] = str(self._lastPythonPathVar.get()) + os.pathsep + os.path.join(os.getcwd(), "3rdparty", "pywin32")
        else:
            #should avoid environment contain unicode string,such as u'xxx'
            env[consts.PYTHON_PATH_NAME] = str(self._lastPythonPathVar.get())

        return projectDocument, filename, args, startIn, isPython, env

    def OnFileSelected(self, event):
        self._selectedFileIndex = self._fileList.current()
        self.SetEntryParams()

    def OnFindDirClick(self):
        path = filedialog.askdirectory(title=_("Choose a starting directory:"))
        if not path:
            return
        self._lastStartInVar.set(fileutils.opj(path))
        
    def CheckUseArgument(self):
        use_arg = self._useArgCheckBoxVar.get()
        if use_arg:
            self._argsEntry['state'] = tk.NORMAL 
        else:
            self._argsEntry['state'] = tk.DISABLED

    def EvtListBox(self, event):
        if self._projectNameVar.get():
            index = self._projectNameList.index(self._projectNameVar.get())
            self._selectedProjectDocument = self._projectDocumentList[index]
            self._currentProj = self._selectedProjectDocument
            self._selectedProjectIndex = index
            self.PopulateFileList(self._selectedProjectDocument)
            self.SetEntryParams()

    def FilterFileList(self, file_list):
        files = filter(lambda f:fileutils.is_python_file(f), file_list)
        return list(files)

    def PopulateFileList(self, project, shortNameToSelect=None):
        project_startup_file = project.GetStartupFile()
        if project_startup_file is None:
            pj_files = project.GetFiles()[:]
        else:
            pj_files = [project_startup_file.filePath]
        self._fileNameList = self.FilterFileList(pj_files)
        if not self._fileNameList:
            self._fileList['values'] = []
            return
        py_sorted(self._fileNameList, cmp_func=lambda a, b: py_cmp(os.path.basename(a).lower(), os.path.basename(b).lower()))
        strings = list(map(lambda file: os.path.basename(file), self._fileNameList))
        for index in range(0, len(self._fileNameList)):
            if shortNameToSelect == self._fileNameList[index]:
                self._selectedFileIndex = index
                break

        self._fileList['values'] = (strings)
        if self._selectedFileIndex not in range(0, len(strings)):
            # Pick first bpel file if there is one.
            for index in range(0, len(strings)):
                if strings[index].endswith('.bpel'):
                    self._selectedFileIndex = index
                    break
        # Still no selected file, use first file.      
        if self._selectedFileIndex not in range(0, len(strings)):
            self._selectedFileIndex = 0
        self._fileList.current(self._selectedFileIndex)

    def GetProjectList(self):
        docList = []
        nameList = []
        found = False
        index = -1
        count = 0
        for document in GetApp().GetDocumentManager().GetDocuments():
            if document.GetDocumentTemplate().GetDocumentType() == projectviewer.PythonProjectDocument:
                docList.append(document)
                nameList.append(os.path.basename(document.GetFilename()))
                if document == self._currentProj:
                    found = True
                    index = count
                count += 1
        #Check for open files not in any of these projects and add them to a default project
        def AlreadyInProject(fileName):
            for projectDocument in docList:
                if projectDocument.IsFileInProject(fileName):
                    return True
            return False

        unprojectedFiles = []
        for document in GetApp().GetDocumentManager().GetDocuments():
            if type(document) == pyeditor.PythonDocument:
                if not AlreadyInProject(document.GetFilename()):
                    unprojectedFiles.append(document.GetFilename())
        if unprojectedFiles:
            unprojProj = projectviewer.PythonProjectDocument.GetUnProjectDocument()
            unprojProj.AddFiles(unprojectedFiles)
            docList.append(unprojProj)
            nameList.append(consts.NOT_IN_ANY_PROJECT)
            if self._currentProj is None:
                self._currentProj = unprojProj
                index = count
        if self._currentProj is None:
            unprojProj = projectviewer.PythonProjectDocument.GetUnProjectDocument()
            docList.append(unprojProj)
            nameList.append(consts.NOT_IN_ANY_PROJECT)
            self._currentProj = unprojProj
        return nameList, docList, index
    
def getBreakPointBitmap():
    return images.load("debugger/breakpoint.png")
    
def getRestartDebuggerBitmap():
    return images.load("debugger/restart_debugger.png")

#----------------------------------------------------------------------

