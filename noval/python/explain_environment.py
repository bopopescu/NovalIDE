# -*- coding: utf-8 -*-
import platform
import sys
import os
if sys.version_info[0] == 2:
    def which(cmd):
        target_cmd = cmd
        if platform.system() == "Windows":
            target_cmd += ".exe"
        sys_paths = os.environ['PATH'].split(os.pathsep)
        for sys_path in sys_paths:
            cmd_path = os.path.join(sys_path,target_cmd)
            if os.path.exists(cmd_path):
                return cmd_path
        return None
elif sys.version_info[0] == 3:
    from shutil import which
import sys
import os.path

def _clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def equivalent_realpath(p):
    pdir = os.path.dirname(p)
    if os.path.isfile(os.path.join(pdir, "activate")):
        # it's a virtual environment
        # can use realpath only if it doesn't move out of its dir
        real = os.path.realpath(p)
        if os.path.dirname(real) == pdir:
            return real
        try:
            link = os.readlink(p)
            if not os.path.isabs(link):
                link = os.path.join(pdir, link)
            link = os.path.normpath(link)
            if os.path.dirname(link) == pdir:
                return link
            return p
        except:
            return p
    else:
        return os.path.realpath(p)

def is_virtual_exe(p):
    pdir = os.path.dirname(p)
    return (
        os.path.exists(os.path.join(pdir, "activate"))
        or os.path.exists(os.path.join(pdir, "activate.bat"))
    )
    
def get_targets(prefix):
    targets = []
    target_paths = []
    for suffix in ["", "3", "3.5", "3.6", "3.7", "3.8"]:
        cmd = prefix + suffix
        target = which(cmd)
        if target is not None:
            real_path = equivalent_realpath(target)
            #在Linux系统上python使用快捷方式指向的路径有可能是同一个python路径,故需要获取快捷方式指向的实际路径
            #并且除去重复的路径
            if real_path not in target_paths:
                targets.append((cmd,target),)
                target_paths.append(real_path)
    return targets

def list_commands(prefix, highlighted_reals, highlighted_dirs):
    
    def list_cmd(cmd,target):
        target = normpath_with_actual_case(target)
        real = equivalent_realpath(target)
        
        if target == real:
            relation = "=="
        else:
            relation = "->"
            
        line = " - " + cmd.ljust(9) + " " + relation + " " + real
        if (real in highlighted_reals
            or os.path.dirname(real) in highlighted_dirs
            or os.path.dirname(target) in highlight_dirs):
            if platform.system() == "Windows":
                print (line)
            else:
                print("\033[1m" + line + "\033[0m")
        else:
            if platform.system() == "Windows":
                print (line)
            else:
                print("\033[2m" + line + "\033[0m")
         
    if os.name == "nt":     
        for cmd in highlighted_reals:
            list_cmd(prefix,cmd)
        
    for cmd,target in get_targets(prefix):
        if normpath_with_actual_case(target) not in highlighted_reals:
            list_cmd(cmd,target)
        
##    for suffix in ["", "3", "3.5", "3.6", "3.7", "3.8"]:
##        cmd = prefix + suffix
##        target = which(cmd)
##        if target is not None and normpath_with_actual_case(target) not in highlighted_reals:
##            list_cmd(cmd,target)

def normpath_with_actual_case(name):
    """In Windows return the path with the case it is stored in the filesystem"""
    # copied from thonny.common to make this script independent
    assert os.path.isabs(name)
    assert os.path.exists(name)

    if os.name == "nt":
        name = os.path.realpath(name)

        from ctypes import create_unicode_buffer,create_string_buffer, windll

        if sys.version_info[0] == 2:
            buf = create_string_buffer(512)
            windll.kernel32.GetShortPathNameA(name, buf, 512)  # @UndefinedVariable
            windll.kernel32.GetLongPathNameA(buf.value, buf, 512)  # @UndefinedVariable
        elif sys.version_info[0] == 3:
            buf = create_unicode_buffer(512)
            windll.kernel32.GetShortPathNameW(name, buf, 512)  # @UndefinedVariable
            windll.kernel32.GetLongPathNameW(buf.value, buf, 512)  # @UndefinedVariable
        assert len(buf.value) >= 2

        result = buf.value
        if sys.version_info[0] == 3:
            assert isinstance(result, str)

        if result[1] == ":":
            # ensure drive letter is capital
            return result[0].upper() + result[1:]
        else:
            return result
    else:
        return os.path.normpath(name)



if __name__ == "__main__":
    _clear_screen()
    print("*" * 80)
    print("Some Python commands in the PATH of this session:")
    #删除路径列表中的当前目录,否则会出现Module use of python36.dll conflicts with this version of Python
    if os.environ['MAIN_MODULE_APTH'] in sys.path:
        sys.path.remove(os.environ['MAIN_MODULE_APTH'])
    sys_real = normpath_with_actual_case(equivalent_realpath(sys.executable))
    sys_executable = normpath_with_actual_case(sys.executable)
    
    if is_virtual_exe(sys_executable):
        highlight_dirs = [os.path.dirname(sys_executable)]
    else:
        highlight_dirs = []
    
    if platform.system() == "Windows":
        # Add Scripts for pip
        highlight_dirs.append(os.path.join(os.path.dirname(sys_real), "Scripts"))
        highlight_dirs.append(os.path.join(os.path.dirname(sys_executable), "Scripts"))
            
    list_commands("python", [sys_real], highlight_dirs)
    
    likely_pips = []
    if sys_real[-9:-1] == "python3.":
        likely_pips.append(sys_real[:-9] + "pip3." + sys_real[-1])
    if sys_executable.endswith("/python3"):
        # This is not as likely match as previous, but still quite likely
        likely_pips.append(sys_executable.replace("/python3", "/pip3"))
        
    list_commands("pip", likely_pips, highlight_dirs)
    
    print("")
    print("*" * 80)
    
