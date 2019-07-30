# -*- coding: utf-8 -*-
# Common py2exe boot script - executed for all target types.

# When we are a windows_exe we have no console, and writing to
# sys.stderr or sys.stdout will sooner or later raise an exception,
# and tracebacks will be lost anyway (see explanation below).
#
# We assume that output to sys.stdout can go to the bitsink, but we
# *want* to see tracebacks.  So we redirect sys.stdout into an object
# with a write method doing nothing, and sys.stderr into a logfile
# having the same name as the executable, with '.log' appended.
#
# We only open the logfile if something is written to sys.stderr.
#
# If the logfile cannot be opened for *any* reason, we have no choice
# but silently ignore the error.
#
# It remains to be seen if the 'a' flag for opening the logfile is a
# good choice, or 'w' would be better.
#
# More elaborate explanation on why this is needed:
#
# The sys.stdout and sys.stderr that GUI programs get (from Windows) are
# more than useless.  This is not a py2exe problem, pythonw.exe behaves
# in the same way.
#
# To demonstrate, run this program with pythonw.exe:
#
# import sys
# sys.stderr = open("out.log", "w")
# for i in range(10000):
#     print i
#
# and open the 'out.log' file.  It contains this:
#
# Traceback (most recent call last):
#   File "out.py", line 6, in ?
#     print i
# IOError: [Errno 9] Bad file descriptor
#
# In other words, after printing a certain number of bytes to the
# system-supplied sys.stdout (or sys.stderr) an exception will be raised.
#

import sys
#判断是原始的python程序,还是用pyinstaller转换后的exe程序.
#用pyinstaller转换py成exe后,会注入frozen属性到sys模块,并设置为True
if getattr(sys,"frozen",False):
    try:
        #判断程序是否是控制台程序
        from ctypes import *
        hwnd = windll.user32.GetForegroundWindow()
        out = windll.kernel32.GetStdHandle(-0xb)  # stdin: 0xa, stdout: 0xb, stderr: 0xc
        USECONSOLE = bool(windll.kernel32.SetConsoleTextAttribute(out, 0x7))
    except:
        USECONSOLE = False
    #只有转换成Windows程序才重定向输出到日志文件
    if not USECONSOLE:
        class Stderr(object):
            softspace = 0
            _file = None
            _error = None
            def write(self, text, alert=None, fname=sys.executable + '.log'):
                if self._file is None and self._error is None:
                    try:
                        #以exe的名称作为日志文件名称
                        self._file = open(fname, 'a')
                    except Exception as e:
                        self._error = str(e)
                if self._file is not None:
                    self._file.write(text)
                    self.flush()
            def flush(self):
                if self._file is not None:
                    self._file.flush()
        #重定向错误输出
        sys.stderr = Stderr()
        class Stdout(Stderr):
            ''''''
        #重定向标准输出
        sys.stdout = Stdout()

