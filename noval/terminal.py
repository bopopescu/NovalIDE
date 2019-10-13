# -*- coding: utf-8 -*-
import os
import platform
import shlex
import noval.util.utils as utils
if utils.is_py2():
    from noval.util.which import which
elif utils.is_py3_plus():
    from shutil import which
import subprocess
import noval.ui_utils as ui_utils

def run_in_terminal(cmd, cwd, env_overrides={}, keep_open=True, title=None,pause=False,overwrite_env=True):
    from noval.ui_utils import get_environment_with_overrides
    if overwrite_env:
        env = get_environment_with_overrides(env_overrides)
    else:
        env = env_overrides
        #如果环境变量为空,使用系统默认的环境变量
        if not env:
            env = os.environ
            
    if platform.system() == "Windows":
        _run_in_terminal_in_windows(cmd, cwd, env, keep_open, title,pause)
    elif platform.system() == "Linux":
        _run_in_terminal_in_linux(cmd, cwd, env, keep_open,pause)
    elif platform.system() == "Darwin":
        _run_in_terminal_in_macos(cmd, cwd, env_overrides, keep_open)
    else:
        raise RuntimeError("Can't launch terminal in " + platform.system())

def open_system_shell(cwd, env_overrides={}):
    env = ui_utils.get_environment_with_overrides(env_overrides)
    
    if platform.system() == "Darwin":
        _run_in_terminal_in_macos([], cwd, env_overrides, True)
    elif platform.system() == "Windows":
        cmd = "start cmd"
        subprocess.Popen(cmd, cwd=cwd, env=env, shell=True)
    elif platform.system() == "Linux":
        cmd = _get_linux_terminal_command()
        subprocess.Popen(cmd, cwd=cwd, env=env, shell=True)
    else:
        raise RuntimeError("Can't launch terminal in " + platform.system())

def _add_to_path(directory, path):
    # Always prepending to path may seem better, but this could mess up other things.
    # If the directory contains only one Python distribution executables, then
    # it probably won't be in path yet and therefore will be prepended.
    if (directory in path.split(os.pathsep)
        or platform.system() == "Windows"
        and directory.lower() in path.lower().split(os.pathsep)):
        return path
    else:
        return directory + os.pathsep + path


def _run_in_terminal_in_windows(cmd, cwd, env, keep_open, title=None,pause=False):
    if keep_open:
        # Yes, the /K argument has weird quoting. Can't explain this, but it works
        quoted_args = " ".join(map(lambda s: s if s == "&" else '"' + s + '"', cmd))
        cmd_line = ("""start {title} /D "{cwd}" /W cmd /K "{quoted_args}" """
                    .format(cwd=cwd,
                            quoted_args=quoted_args,
                            title='"' + title + '"' if title else ""))
    
        subprocess.Popen(cmd_line, cwd=cwd, env=env, shell=True)
    elif pause:
        command = u"cmd.exe /c call %s"  % (cmd)
        command += " &pause"
        subprocess.Popen(command,shell = False,creationflags = subprocess.CREATE_NEW_CONSOLE,cwd=cwd,env=env)
    else:
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE,
                         cwd=cwd, env=env)


def _run_in_terminal_in_linux(cmd, cwd, env, keep_open,pause=False):
    def _shellquote(s):
        return subprocess.list2cmdline([s])
    
    term_cmd = _get_linux_terminal_command()
    
    
    if isinstance(cmd, list):
        cmd = " ".join(map(_shellquote, cmd))
        
    if keep_open:
        # http://stackoverflow.com/a/4466566/261181
        core_cmd = "{cmd}; exec bash -i".format(cmd=cmd)
        in_term_cmd = "bash -c {core_cmd}".format(core_cmd=_shellquote(core_cmd))
    elif pause:
        in_term_cmd = cmd + ";echo 'Please enter any to continue';read"
    else:
        in_term_cmd = cmd
    
    if term_cmd == "lxterminal":
        # https://www.raspberrypi.org/forums/viewtopic.php?t=221490
        whole_cmd = "{term_cmd} --command={in_term_cmd}".format(
            term_cmd=term_cmd, in_term_cmd=_shellquote(in_term_cmd)
        )
    elif term_cmd == "gnome-terminal":
        whole_cmd = "{term_cmd} -x bash -c {in_term_cmd}".format(
            term_cmd=term_cmd, in_term_cmd=_shellquote(in_term_cmd)
        )
    else:
        whole_cmd = "{term_cmd} {in_term_cmd}".format(
            term_cmd=term_cmd, in_term_cmd=_shellquote(in_term_cmd)
        )
    subprocess.Popen(whole_cmd, cwd=cwd, env=env, shell=True)


def _get_linux_terminal_command():
    
    if which("gnome-terminal"):
        return "gnome-terminal"
    elif which("x-terminal-emulator"):
        xte = which("x-terminal-emulator")
        if xte:
            if (os.path.realpath(xte).endswith("/lxterminal")
                and which("lxterminal")):
                # need to know exact program, because it needs special treatment
                return "lxterminal"
            else:
                return "x-terminal-emulator"
        # Can't use konsole, because it doesn't pass on the environment
        #         elif shutil.which("konsole"):
        #             if (shutil.which("gnome-terminal")
        #                 and "gnome" in os.environ.get("DESKTOP_SESSION", "").lower()):
        #                 term_cmd = "gnome-terminal"
        #             else:
        #                 term_cmd = "konsole"
    elif which("xfce4-terminal"):
        return "xfce4-terminal"
    elif which("lxterminal"):
        return "lxterminal"
    elif which("xterm"):
        return "xterm"
    else:
        raise RuntimeError("Don't know how to open terminal emulator")
    