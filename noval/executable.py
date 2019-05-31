# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        executable.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-10
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------


import noval.util.apputils as apputils
import noval.util.strutils as strutils
import os


EXECUTABLE_INTERPRETER_TYPE = "Interpreter"
UNKNOWN_VERSION_NAME = "Unknown Version"

class Executable(object):
    
    def __init__(self,name,path,type_name=EXECUTABLE_INTERPRETER_TYPE):
        self._path = path
        self._install_path = os.path.dirname(self._path)
        self._name = name
        self._type_name = type_name
        
    @property
    def Path(self):
        return self._path
        
    @property
    def UnicodePath(self):
        return self.GetUnicodePath()
        
    def GetUnicodePath(self):
        default_encoding = apputils.get_default_encoding()
        assert(not strutils.is_none_or_empty(default_encoding))
        if apputils.is_py2():
            unicode_path = self.Path.decode(default_encoding)
            return unicode_path
        return self.Path
        
    def CheckPathEncoding(self):
        '''
            检查路径是否包含中文字符等
        '''
        unicode_path = self.GetUnicodePath()
        if unicode_path != self.Path:
            wx.MessageBox(_("%s path '%s' contains no asc character") % (self.TypeName,unicode_path),_("Warning"),wx.OK|wx.ICON_WARNING,wx.GetApp().GetTopWindow())
        
    @property
    def InstallPath(self):
        return self._install_path
        
    @property
    def Version(self):
        return UNKNOWN_VERSION_NAME
        
    @property
    def Name(self):
        return self._name
 
    @Name.setter
    def Name(self,name):
        self._name = name
        
    @property
    def TypeName(self):
        return self._type_name

