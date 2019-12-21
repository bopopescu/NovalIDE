# -*- coding: utf-8 -*-

import subprocess
import os

#-p后面第一个路径为输出翻译文件路径, 第二个路径为源文件路径
curdir = os.getcwd()
#cmd = r'python C:\Python27\Tools\i18n\pygettext.py -a -d novalide -o novalide.pot -p {0}\locale {0}\noval'.format(curdir,)
#生成pot文件
cmd = r"C:\Users\Administrator\AppData\Roaming\Python\Python36\Scripts\pybabel.exe extract {0}/noval --output-file {0}/locale/novalide.pot".format(curdir,)
subprocess.call(cmd)

#po文件需要从pot文件更新,菜单Catalogue/Update from POT file
os.system(r'"C:\Program Files (x86)\Poedit\Poedit.exe" {0}\locale\zh_CN.po'.format(curdir,))