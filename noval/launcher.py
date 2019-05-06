# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        launcher.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-08
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
import os
import sys
import noval.util.apputils as apputils
from noval import model

if apputils.is_py2():
    reload(sys)
    sys.setdefaultencoding("utf-8")

def run(language):
    #双击启动软件时,添加软件的安装路径到python解释器的搜索路径,以便py2exe转换成exe时所有引用模块都能找到
    #在使用python解释器运行软件时此处代码将不起作用,因为系统路径已经包含了解释器安装路径
    execDir = os.path.dirname(sys.executable)
    try:
        sys.path.index(execDir)
    except ValueError:
        sys.path.append(execDir)

    if language == model.LANGUAGE_PYTHON:
        import noval.python.pyide
        app = noval.python.pyide.PyIDEApplication()
    app.mainloop()

