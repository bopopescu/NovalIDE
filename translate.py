# -*- coding: utf-8 -*-

import subprocess
import os

#-p后面第一个路径为输出翻译文件路径, 第二个路径为源文件路径
curdir = os.getcwd()
cmd = r'python C:\Python27\Tools\i18n\pygettext.py -a -d novalide -o novalide.pot -p {0}\locale {0}\noval'.format(curdir,)
subprocess.call(cmd)

os.system(r'"C:\Program Files (x86)\Poedit\Poedit.exe" {0}\locale\zh_CN.po'.format(curdir,))