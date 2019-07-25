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
from noval import _
from tkinter import messagebox
import noval.util.apputils as apputils
import noval.util.strutils as strutils
import os



UNKNOWN_VERSION_NAME = "Unknown Version"

class Executable(object):
    
    def __init__(self,name,path):
        self._path = path
        self._install_path = os.path.dirname(self._path)
        self._name = name
        
    @property
    def Path(self):
        return self._path
        
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
        

