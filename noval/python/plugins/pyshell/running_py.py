# -*- coding: utf-8 -*-

"""Code for maintaining the background process and for running
user programs

Commands get executed via shell, this way the command line in the 
shell becomes kind of title for the execution.

"""
from noval import GetApp
import os.path
import subprocess
import sys
import traceback
from noval.util import utils
import noval.python.pyutils as pyutils
from noval.util.command import *
from noval.running import *
from code import InteractiveInterpreter
import six.moves.builtins as builtins
import threading
import queue
import shlex

WINDOWS_EXE = "python.exe"

def execfile(filePath):
    with open(filePath,encoding="utf-8") as f:
        exec(f.read())

class PythonRunner(Runner):
    def __init__(self,shell_view):
        #get_workbench().set_default("run.auto_cd", True)
        Runner.__init__(self,shell_view)
        
    def get_backend(self):
        backend_name = utils.profile_get("run.backend_name","SameAsFrontend")
        return backend_name

    def get_sys_path(self):
        return self._proxy.get_sys_path()

    def execute_script(
        self,
        script_path,
        args,
        working_directory,
        command_name = "Run",
    ):

        if working_directory is not None and get_workbench().get_local_cwd() != working_directory:
            # create compound command
            # start with %cd
            cd_cmd_line = construct_cd_command(working_directory) + "\n"
            next_cwd = working_directory
        else:
            # create simple command
            cd_cmd_line = ""
            next_cwd = get_workbench().get_local_cwd()

        if not is_remote_path(script_path) and self._proxy.uses_local_filesystem():
            rel_filename = os.path.relpath(script_path, next_cwd)
            cmd_parts = ["%" + command_name, rel_filename] + args
        else:
            cmd_parts = ["%" + command_name, "-c", EDITOR_CONTENT_TOKEN] + args

        exe_cmd_line = construct_cmd_line(cmd_parts, [EDITOR_CONTENT_TOKEN]) + "\n"

        # submit to shell (shell will execute it)
        get_shell().submit_magic_command(cd_cmd_line + exe_cmd_line)

    def execute_current(self, command_name):
        """
        This method's job is to create a command for running/debugging
        current file/script and submit it to shell
        """

        if not self.is_waiting_toplevel_command():
            self.restart_backend(True, False, 2)

        filename = get_saved_current_script_filename()

        if not filename:
            # user has cancelled file saving
            return

        if is_remote_path(filename) or not self._proxy.uses_local_filesystem():
            working_directory = None
        else:
            # changing dir may be required
            script_dir = os.path.dirname(filename)

            if get_workbench().get_option("run.auto_cd") and command_name[0].isupper():
                working_directory = script_dir  # type: Optional[str]
            else:
                working_directory = None

        args = self._get_active_arguments()

        self.execute_script(filename, args, working_directory, command_name)

    def cmd_run_current_script_enabled(self):
        return (
            get_workbench().get_editor_notebook().get_current_editor() is not None
            and "run" in get_runner().get_supported_features()
        )

    def _cmd_run_current_script_in_terminal_enabled(self):
        return (
            self._proxy
            and "run_in_terminal" in self._proxy.get_supported_features()
            and self.cmd_run_current_script_enabled()
        )

    def cmd_run_current_script(self):
        if get_workbench().in_simple_mode():
            get_workbench().hide_view("VariablesView")
        self.execute_current("Run")

    def _cmd_run_current_script_in_terminal(self):
        filename = get_saved_current_script_filename()
        self._proxy.run_script_in_terminal(
            filename,
            self._get_active_arguments(),
            get_workbench().get_option("run.run_in_terminal_python_repl"),
            get_workbench().get_option("run.run_in_terminal_keep_open"),
        )

    def using_venv(self):
        return isinstance(self._proxy, CPythonProxy) and self._proxy._in_venv

class CPythonProxy(SubprocessProxy):
    "abstract class"

    def __init__(self, clean, executable):
        SubprocessProxy.__init__(self,clean, executable)
        self._sys_path = []
        self._usersitepackages = None
        self._in_venv = None
        self._send_msg(ToplevelCommand("get_environment_info"))
        
    def get_site_packages(self):
        # NB! site.sitepackages may not be present in virtualenv
        for d in self._sys_path:
            if ("site-packages" in d or "dist-packages" in d) and path_startswith(
                d, self._sys_prefix
            ):
                return d

        return None
        
    def _get_initial_cwd(self):
        return utils.get_app_path()

    def get_user_site_packages(self):
        return self._usersitepackages

    def GetEnv(self):
        # prepare environment
        env = pyutils.get_environment_for_python_subprocess(self._executable,False)
        # variables controlling communication with the back-end process
        env["PYTHONIOENCODING"] = "utf-8"

        # Let back-end know about plug-ins
        env["NOVAL_USER_DIR"] = utils.get_app_path()
        env["NOVAL_FRONTEND_SYS_PATH"] = repr(sys.path)
        env["BACKEND_LOG_PATH"] = utils.get_user_data_path()
        
        if utils.is_py2():
            for key in env:
                env[key] = str(env[key])

        if GetApp().GetDebug():
            env["NOVAL_DEBUG"] = "1"
        elif "NOVAL_DEBUG" in env:
            del env["NOVAL_DEBUG"]
        return env

    def get_sys_path(self):
        return self._sys_path

    def _get_launcher_with_args(self):
        import noval.python.plugins.pyshell.backend_launcher
        return [
            "-u",  # unbuffered IO
            "-B",  # don't write pyo/pyc files
            # (to avoid problems when using different Python versions without write permissions)
            noval.python.plugins.pyshell.backend_launcher.__file__]
        
    def run_script_in_terminal(self, script_path, interactive, keep_open):
        raise NotImplementedError()

    def get_sys_path(self):
        "backend's sys.path"
        return []

    def _store_state_info(self, msg):
        SubprocessProxy._store_state_info(self,msg)

        if "gui_is_active" in msg:
            self._update_gui_updating(msg)

    def _clear_environment(self):
        self._close_backend()
        self._start_background_process()

    def _close_backend(self):
        self._cancel_gui_update_loop()
        SubprocessProxy._close_backend(self)

    def _update_gui_updating(self, msg):
        """Enables running Tkinter or Qt programs which doesn't call mainloop. 
        
        When mainloop is omitted, then program can be interacted with
        from the shell after it runs to the end.
        
        Each ToplevelResponse is supposed to tell, whether gui is active
        and needs updating.
        """
        if not "gui_is_active" in msg:
            return

        if msg["gui_is_active"] and self._gui_update_loop_id is None:
            # Start updating
            self._loop_gui_update(True)
        elif not msg["gui_is_active"] and self._gui_update_loop_id is not None:
            self._cancel_gui_update_loop()

    def _loop_gui_update(self, force=False):
        if force or get_runner().is_waiting_toplevel_command():
            self.send_command(InlineCommand("process_gui_events"))

        self._gui_update_loop_id = get_workbench().after(50, self._loop_gui_update)

    def _cancel_gui_update_loop(self):
        if self._gui_update_loop_id is not None:
            try:
                get_workbench().after_cancel(self._gui_update_loop_id)
            finally:
                self._gui_update_loop_id = None

    def run_script_in_terminal(self, script_path, args, interactive, keep_open):
        cmd = [self._executable]
        if interactive:
            cmd.append("-i")
        cmd.append(os.path.basename(script_path))
        cmd.extend(args)

        run_in_terminal(cmd, os.path.dirname(script_path), keep_open=keep_open)

    def get_supported_features(self):
        return {"run", "debug", "run_in_terminal", "pip_gui", "system_shell"}


class PrivateVenvCPythonProxy(CPythonProxy):
    def __init__(self, clean):
        self._prepare_private_venv()
        super().__init__(clean, get_private_venv_executable())

    def _prepare_private_venv(self):
        path = get_private_venv_path()
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "pyvenv.cfg")):
            self._check_upgrade_private_venv(path)
        else:
            self._create_private_venv(
                path, "Please wait!\nThonny prepares its virtual environment."
            )

    def _check_upgrade_private_venv(self, path):
        # If home is wrong then regenerate
        # If only micro version is different, then upgrade
        info = _get_venv_info(path)

        if not is_same_path(info["home"], os.path.dirname(sys.executable)):
            self._create_private_venv(
                path,
                "Thonny's virtual environment was created for another interpreter.\n"
                + "Regenerating the virtual environment for current interpreter.\n"
                + "(You may need to reinstall your 3rd party packages)\n"
                + "Please wait!.",
                clear=True,
            )
        else:
            venv_version = tuple(map(int, info["version"].split(".")))
            sys_version = sys.version_info[:3]
            assert venv_version[0] == sys_version[0]
            assert venv_version[1] == sys_version[1]

            if venv_version[2] != sys_version[2]:
                self._create_private_venv(
                    path, "Please wait!\nUpgrading Thonny's virtual environment.", upgrade=True
                )

    def _create_private_venv(self, path, description, clear=False, upgrade=False):
        # Don't include system site packages
        # This way all students will have similar configuration
        # independently of system Python (if Thonny is used with system Python)

        # NB! Cant run venv.create directly, because in Windows
        # it tries to link venv to thonny.exe.
        # Need to run it via proper python
        args = ["-m", "venv"]
        if clear:
            args.append("--clear")
        if upgrade:
            args.append("--upgrade")

        try:
            # pylint: disable=unused-variable
            import ensurepip  # @UnusedImport
        except ImportError:
            args.append("--without-pip")

        args.append(path)

        proc = create_frontend_python_process(args)

        from thonny.ui_utils import SubprocessDialog

        dlg = SubprocessDialog(
            get_workbench(), proc, "Preparing the backend", long_description=description
        )
        try:
            ui_utils.show_dialog(dlg)
        except Exception:
            # if using --without-pip the dialog may close very quickly
            # and for some reason wait_window would give error then
            utils.get_logger().exception("Problem with waiting for venv creation dialog")
        get_workbench().become_active_window()  # Otherwise focus may get stuck somewhere

        bindir = os.path.dirname(get_private_venv_executable())
        # create private env marker
        marker_path = os.path.join(bindir, "is_private")
        with open(marker_path, mode="w") as fp:
            fp.write("# This file marks Thonny-private venv")

        # Create recommended pip conf to get rid of list deprecation warning
        # https://github.com/pypa/pip/issues/4058
        pip_conf = "pip.ini" if running_on_windows() else "pip.conf"
        with open(os.path.join(path, pip_conf), mode="w") as fp:
            fp.write("[list]\nformat = columns")

        assert os.path.isdir(path)

class PythonInteractiveInterpreter(InteractiveInterpreter):
    """Interpreter based on code.InteractiveInterpreter."""
    
    @staticmethod
    def InitPrompt():
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = '>>> '
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = '... '
    
    def __init__(self, locals=None, rawin=None, 
                 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                 showInterpIntro=True):
        """Create an interactive interpreter object."""
        InteractiveInterpreter.__init__(self, locals=locals)
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        if rawin:
            builtins.raw_input = rawin
        if showInterpIntro:
            copyright = 'Type "help", "copyright", "credits" or "license"'
            copyright += ' for more information.'
            #linux系统下sys.version包含换行符,需要去除掉
            self.introText = 'Python %s on %s%s%s' % \
                             (sys.version.replace(os.linesep,""), sys.platform, os.linesep, copyright)
        self.InitPrompt()
        self.more = 0
        # List of lists to support recursive push().
        self.commandBuffer = []
        self.startupScript = None
    
    def push(self, command, astMod=None):
        """Send command to the interpreter to be executed.
        
        Because this may be called recursively, we append a new list
        onto the commandBuffer list and then append commands into
        that.  If the passed in command is part of a multi-line
        command we keep appending the pieces to the last list in
        commandBuffer until we have a complete command. If not, we
        delete that last list."""
        
        # In case the command is unicode try encoding it
        if utils.is_py2():
            if type(command) == unicode:
                try:
                    command = command.encode(utils.get_default_encoding())
                except UnicodeEncodeError:
                    pass # otherwise leave it alone
                
        if not self.more:
            try: del self.commandBuffer[-1]
            except IndexError: pass
        if not self.more: self.commandBuffer.append([])
        self.commandBuffer[-1].append(command)
        source = '\n'.join(self.commandBuffer[-1])
        
        # If an ast code module is passed, pass it to runModule instead
        more=False
        if astMod != None:
            self.runModule(astMod)
            self.more=False
        else:
            more = self.more = self.runsource(source)
        return more
        
    def runsource(self, source,filename="<input>", symbol="single"):
        """Compile and run source code in the interpreter."""
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   self.stdin, self.stdout, self.stderr
        more = InteractiveInterpreter.runsource(self, source,filename,symbol)
        # this was a cute idea, but didn't work...
        #more = self.runcode(compile(source,'',
        #               ('exec' if self.useExecMode else 'single')))
        
        
        # If sys.std* is still what we set it to, then restore it.
        # But, if the executed source changed sys.std*, assume it was
        # meant to be changed and leave it. Power to the people.
        if sys.stdin == self.stdin:
            sys.stdin = stdin
        else:
            self.stdin = sys.stdin
        if sys.stdout == self.stdout:
            sys.stdout = stdout
        else:
            self.stdout = sys.stdout
        if sys.stderr == self.stderr:
            sys.stderr = stderr
        else:
            self.stderr = sys.stderr
        return more
        
    def runModule(self, mod):
        """Compile and run an ast module in the interpreter."""
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   self.stdin, self.stdout, self.stderr
        self.runcode(compile(mod,'','single'))
        # If sys.std* is still what we set it to, then restore it.
        # But, if the executed source changed sys.std*, assume it was
        # meant to be changed and leave it. Power to the people.
        if sys.stdin == self.stdin:
            sys.stdin = stdin
        else:
            self.stdin = sys.stdin
        if sys.stdout == self.stdout:
            sys.stdout = stdout
        else:
            self.stdout = sys.stdout
        if sys.stderr == self.stderr:
            sys.stderr = stderr
        else:
            self.stderr = sys.stderr
        return False
    
    def getAutoCompleteKeys(self):
        """Return list of auto-completion keycodes."""
        return [ord('.')]

    def getAutoCompleteList(self, command='', *args, **kwds):
        """Return list of auto-completion options for a command.
        
        The list of options will be based on the locals namespace."""
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   self.stdin, self.stdout, self.stderr
        l = introspect.getAutoCompleteList(command, self.locals,
                                           *args, **kwds)
        sys.stdin, sys.stdout, sys.stderr = stdin, stdout, stderr
        return l

    def getCallTip(self, command='', *args, **kwds):
        """Return call tip text for a command.
        
        Call tip information will be based on the locals namespace."""
        return introspect.getCallTip(command, self.locals, *args, **kwds)
        

class PseudoFile:

    def __init__(self):
        """Create a file-like object."""
        pass

    def readline(self):
        pass

    def write(self, s):
        pass

    def writelines(self, l):
        map(self.write, l)

    def flush(self):
        pass

    def isatty(self):
        pass


class PseudoFileIn(PseudoFile):

    def __init__(self, readline, readlines=None):
        if callable(readline):
            self.readline = readline
        else:
            raise ValueError('readline must be callable')
        if callable(readlines):
            self.readlines = readlines

    def isatty(self):
        return 1
        
        
class PseudoFileOut(PseudoFile):

    def __init__(self, write):
        if callable(write):
            self.write = write
        else:
            raise ValueError('write must be callable')

    def isatty(self):
        return 1


class PseudoFileErr(PseudoFile):

    def __init__(self, write):
        if callable(write):
            self.write = write
        else:
            raise ValueError('write must be callable')

    def isatty(self):
        return 1


class BuiltinCPythonProxy(BackendProxy):
    
    #执行内建解释器退出方法时,提示的信息
    EXIT_PROMPT_ERROR_MSG = 'Click on the close button to leave the application.'
    def __init__(self, clean,introText='', locals=None, InterpClass=PythonInteractiveInterpreter,startupScript=None, \
                 execStartupScript=True,*args, **kwds):
        if locals is None:
            import __main__
            locals = __main__.__dict__

        # Grab these so they can be restored by self.redirect* methods.
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        
        # Create a replacement for stdin.
        self.reader = PseudoFileIn(self.readline, self.readlines)
        self.reader.input = ''
        self.reader.isreading = False
        
        self.interp = InterpClass(locals=locals,
                                  rawin=self.raw_input,
                                  stdin=self.reader,
                                  stdout=PseudoFileOut(self.writeOut),
                                  stderr=PseudoFileErr(self.writeErr),
                                  *args, **kwds)
                                  
        #显示Python解释器信息.
        self.introText = introText
        
        #重写内建的解释器关闭,退出事件,不运行用户在解释器中执行退出,关闭方法
        self.setBuiltinKeywords()
        self.more = False
        #python3没有execfile函数,自己实现一个
        if utils.is_py3():
            import builtins
            builtins.execfile = execfile
            
        BackendProxy.__init__(self,clean)
        self.next_msg = None
        #欢迎信息
        self._send_welcom_msg()
        
    def writeOut(self, text):
        """Replacement for stdout."""
        GetApp().event_generate("ProgramOutput", stream_name="stdout", data=text)

    def writeErr(self, text):
        """Replacement for stderr."""
        GetApp().event_generate("ProgramOutput", stream_name="stderr", data=text)

    def raw_input(self, prompt=''):
        """Return string based on user input."""
        if prompt:
            self.write(prompt)
        return self.readline()
        

    def readline(self):
        """Replacement for stdin.readline()."""
        input = ''
        reader = self.reader
        reader.isreading = True
        self.prompt()
        try:
            while not reader.input:
                wx.YieldIfNeeded()
            input = reader.input
        finally:
            reader.input = ''
            reader.isreading = False
        input = str(input)  # In case of Unicode.
        return input

    def readlines(self):
        """Replacement for stdin.readlines()."""
        lines = []
        while lines[-1:] != ['\n']:
            lines.append(self.readline())
        return lines
        
    def getIntro(self, text=''):
        """Display introductory text in the shell."""
        if text:
            return text
        self.introText = self.interp.introText
        return self.introText
        
    def fetch_next_message(self):
        msg =  self.next_msg
        self.next_msg = None
        return msg
        
    def _start_background_process(self):
        pass

    def _send_welcom_msg(self):
        msg = ToplevelResponse(
            main_dir=None,
            path=sys.path,
            usersitepackages=site.getusersitepackages() if site.ENABLE_USER_SITE else None,
            prefix=sys.prefix,
            welcome_text=self.getIntro(),
            executable=sys.executable,
            exe_dirs=get_exe_dirs(),
            in_venv=(
                hasattr(sys, "base_prefix")
                and sys.base_prefix != sys.prefix
                or hasattr(sys, "real_prefix")
                and getattr(sys, "real_prefix") != sys.prefix
            ),
            python_version=pyutils.get_python_version_string(),
            cwd=os.getcwd(),
        )
        self.next_msg = msg
        
    def setBuiltinKeywords(self):
        #重定向系统模块的退出方法到一个字符串
        builtins.close = builtins.exit = builtins.quit = self.EXIT_PROMPT_ERROR_MSG
        os._exit = sys.exit = self.EXIT_PROMPT_ERROR_MSG

    def push(self, command, silent = False):
        try:
            #DNM
          #  if USE_MAGIC:
           #     command=magic(command)
             
            self.waiting = True
            self.lastUpdate=None
            self.more = self.interp.push(command)
            self.lastUpdate=None
            self.waiting = False
            #执行一条语句后打印>>>提示
            if not silent:
                self.next_msg = ToplevelResponse()
        except SystemExit as x:
            self.writeErr(str(x))
            self.send_program_input('')
        except Exception as x:
            self.writeErr(str(x))
            
    def run(self, command, prompt=True, verbose=True):
        """Execute command as if it was typed in directly.
        >>> shell.run('print "this"')
        >>> print "this"
        this
        >>>
        """
        # Go to the very bottom of the text.
     #   endpos = self.GetTextLength()
      #  self.SetCurrentPos(endpos)
        command = command.rstrip()
        if prompt: self.prompt()
        if verbose: self.write(command)
        self.push(command)

    def runsource(self,source,filename="<editor selection>", symbol="exec"):
        self.write('\n')
        self.interp.runsource(source.strip(),filename,symbol)
        self.prompt()
        
    def send_program_input(self, data):
        self.push(data.strip())
        
    def send_command(self, cmd):
        if cmd.cmd_line.startswith("!"):
            self.execute_system_command(cmd)
            return
        elif cmd.cmd_line.startswith("%"):
            self.cd(cmd.cmd_line.strip()[1:])
            return
        """Send the command to backend. Return None, 'discard' or 'postpone'"""
        if cmd.source is None:
            self.next_msg = ToplevelResponse()
            return
        self.push(cmd.source.strip())
        
    def execute_system_command(self, cmd):
        self._stopped = False
        self.notify_queue = queue.Queue()
        self.process_msg()
#        self._check_update_tty_mode(cmd)
        env = dict(os.environ).copy()
        encoding = utils.get_default_encoding()
        env["PYTHONIOENCODING"] = encoding
        # Make sure this python interpreter and its scripts are available
        # in PATH
        update_system_path(env, get_augmented_system_path(get_exe_dirs()))
        popen_kw = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            env=env,
            universal_newlines=True,
            cwd=os.getcwd(),
        )

        if sys.version_info >= (3, 6):
            popen_kw["errors"] = "replace"
            popen_kw["encoding"] = encoding

        assert cmd.cmd_line.startswith("!")
        cmd_line = cmd.cmd_line[1:]
        proc = subprocess.Popen(cmd_line, **popen_kw)

        def copy_stream(source, is_error):
            while True:
                c = source.readline()
                c = c.encode(encoding,'ignore').decode(encoding)
                if c == "":
                    break
                else:
                    self.notify_queue.put((c,is_error))
        #tkinter text控件不支持多线程,这里使用队列的方式操作text控件
        copy_out = threading.Thread(target=lambda: copy_stream(proc.stdout, False), daemon=True)
        copy_err = threading.Thread(target=lambda: copy_stream(proc.stderr, True), daemon=True)

        copy_out.start()
        copy_err.start()
        try:
            proc.wait()
        except KeyboardInterrupt as e:
            print(str(e), file=sys.stderr)

        copy_out.join()
        copy_err.join()
        self.notify_queue.put((None,0))
        
    def process_msg(self):
        if self._stopped:
            return
        GetApp().after(1,self.process_msg)
        while not self.notify_queue.empty():
            try:
                msg = self.notify_queue.get()
                if msg[0] == None:
                    self._stopped = True
                    self.next_msg = ToplevelResponse()
                else:
                    data,is_error = msg
                    if is_error:
                        self.writeErr(data)
                    else:
                        self.writeOut(data)
            except queue.Empty:
                pass
                
    def cd(self,cmd,usePrint=False):
        path = shlex.split(cmd)[1]
        os.chdir(os.path.expandvars(os.path.expanduser(path)))
        if usePrint:
            pwd()
        self.next_msg = ToplevelResponse()

class CustomCPythonProxy(CPythonProxy):
    def __init__(self, clean):
        current_interpreter = GetApp().GetCurrentInterpreter()
        assert(not current_interpreter.IsBuiltIn)
        executable = current_interpreter.Path
        # Rembember the usage of this non-default interpreter
#        used_interpreters = get_workbench().get_option("CustomInterpreter.used_paths")
 #       if executable not in used_interpreters:
  #          used_interpreters.append(executable)
   #     get_workbench().set_option("CustomInterpreter.used_paths", used_interpreters)
        super().__init__(clean, executable)

    def fetch_next_message(self):
        msg = super().fetch_next_message()
        if msg and "welcome_text" in msg:
            msg["welcome_text"] += " (" + self._executable + ")"
        return msg


def get_private_venv_path():
    if is_bundled_python(sys.executable.lower()):
        prefix = "BundledPython"
    else:
        prefix = "Python"
    return os.path.join(
        THONNY_USER_DIR, prefix + "%d%d" % (sys.version_info[0], sys.version_info[1])
    )


def get_private_venv_executable():
    venv_path = get_private_venv_path()

    if running_on_windows():
        exe = os.path.join(venv_path, "Scripts", WINDOWS_EXE)
    else:
        exe = os.path.join(venv_path, "bin", "python3")

    return exe


def _get_venv_info(venv_path):
    cfg_path = os.path.join(venv_path, "pyvenv.cfg")
    result = {}

    with open(cfg_path, encoding="UTF-8") as fp:
        for line in fp:
            if "=" in line:
                key, val = line.split("=", maxsplit=1)
                result[key.strip()] = val.strip()

    return result


def is_bundled_python(executable):
    return os.path.exists(os.path.join(os.path.dirname(executable), "thonny_python.ini"))


def create_backend_python_process(
    args, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
):
    """Used for running helper commands (eg. pip) on CPython backend.
    Assumes current backend is CPython."""

    # TODO: if backend == frontend, then delegate to create_frontend_python_process

    python_exe = get_runner().get_local_executable()

    env = get_environment_for_python_subprocess(python_exe)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    # TODO: remove frontend python from path and add backend python to it

    return _create_python_process(python_exe, args, stdin, stdout, stderr, env=env)


def create_frontend_python_process(
    args, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
):
    """Used for running helper commands (eg. for installing plug-ins on by the plug-ins)"""
    python_exe = get_frontend_python().replace("pythonw.exe", "python.exe")
    env = get_environment_for_python_subprocess(python_exe)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    return _create_python_process(python_exe, args, stdin, stdout, stderr)

def get_frontend_python():
    return sys.executable.replace("NovalIDE.exe", "python.exe").replace("pythonw.exe", "python.exe")

def is_venv_interpreter_of_current_interpreter(executable):
    for location in [".", ".."]:
        cfg_path = os.path.join(location, "pyvenv.cfg")
        if os.path.isfile(cfg_path):
            with open(cfg_path) as fp:
                content = fp.read()
            for line in content.splitlines():
                if line.replace(" ", "").startswith("home="):
                    _, home = line.split("=", maxsplit=1)
                    home = home.strip()
                    if os.path.isdir(home) and os.path.samefile(home, sys.prefix):
                        return True
    return False
