# -*- coding: utf-8 -*-
from tkinter import messagebox
from noval import GetApp,_
import sys
import threading
import noval.process as process
import noval.util.strutils as strutils
import os
import noval.util.utils as utils
import time
import noval.terminal as terminal

EVT_UPDATE_STDTEXT = "UpdateOutputText"
EVT_UPDATE_ERRTEXT = "UpdateErrorText"

SOURCE_DEBUG = 'Debug'


class StartupPathNotExistError(RuntimeError):
    
    def __init__(self,startup_path):
        self.msg = _("Startup path \"%s\" is not exist") % startup_path

    def ShowMessageBox(self):
        messagebox.showerror(_("Startup path not exist"),self.msg,parent=GetApp().GetTopWindow())

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
        utils.get_logger().debug("Exiting OutputReaderThread")

    def AskToStop(self):
        self._keepGoing = False

class TerminalExecutor(object):
    def __init__(self, run_parameter):
        self._run_parameter = run_parameter
        #should convert to unicode when interpreter path contains chinese self._run_parameter.Environmentcharacter
        self._path = self._run_parameter.ExePath
        self._cmd = strutils.emphasis_path(self._path)

    #Better way to do this? Quotes needed for windows file paths.
    def spaceAndQuote(self,text):
        '''
            将路径用双引号括起来,防止路径包含空格出错
        '''
        if text.startswith("\"") and text.endswith("\""):
            return  ' ' + text
        else:
            return ' \"' + text + '\"'

    def GetStartupPath(self):
        startIn = self._run_parameter.StartupPath
        if not startIn:
            startIn = os.getcwd()
        ###startIn = os.path.abspath(startIn)
        if not os.path.exists(startIn):
            raise StartupPathNotExistError(startIn)
        return startIn

    def GetExecuteCommand(self):
        arguments = self._run_parameter.Arg
        if arguments and arguments != " ":
            command = self._cmd + ' ' + arguments
        else:
            command = self._cmd
        return command

    def Execute(self):
        command = self.GetExecuteCommand()
        utils.get_logger().debug("start run executable: %s in terminal",command)
        startIn = self.GetStartupPath()
        terminal.run_in_terminal(command,startIn,self._run_parameter.Environment,keep_open=False,pause=True,title="abc",overwrite_env=False)

    def GetExecPath(self):
        return self._path

class Executor(TerminalExecutor):
    def __init__(self, run_parameter, wxComponent,callbackOnExit=None,source=SOURCE_DEBUG):
        TerminalExecutor.__init__(self,run_parameter)
        self._stdOutCallback = self.OutCall
        self._stdErrCallback = self.ErrCall
        self._callbackOnExit = callbackOnExit
        self._wxComponent = wxComponent
        self._stdOutReader = None
        self._stdErrReader = None
        self._process = None
        self.source = source

    def OutCall(self, text):
        GetApp().event_generate(EVT_UPDATE_STDTEXT,value=text,interface=self._wxComponent,source=self.source)

    def ErrCall(self, text):
        GetApp().event_generate(EVT_UPDATE_ERRTEXT,value=text,interface=self._wxComponent,source=self.source)

    def Execute(self):
        command = self.GetExecuteCommand()
        startIn = self.GetStartupPath()
        utils.get_logger().debug("start debugger executable: %s",command)
        self._process = process.ProcessOpen(command, mode='b', cwd=startIn, env=self._run_parameter.Environment)
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
        
    def WriteInput(self,text):
        if None == self._process:
            return
        self._process.stdin.write(text)