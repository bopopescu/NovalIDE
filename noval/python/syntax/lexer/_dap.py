# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        _python.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-17
# Copyright:   (c) wukan 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

#-----------------------------------------------------------------------------#
from noval import _
from noval.syntax import syndata,lang
import os
import _python
import noval.python.pyeditor as pyeditor
import noval.imageutils as imageutils

class SyntaxLexer(_python.SyntaxLexer):
    """SyntaxData object for Python""" 
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [ 
    ]
                 
    def __init__(self):
        lang_id = lang.RegisterNewLangId("ID_LANG_DAP")
        syndata.BaseLexer.__init__(self,lang_id)
        
    def GetDescription(self):
        return _('Cloudwms Dap File')
        
    def GetExt(self):
        return "dap"

    def GetShowName(self):
        return "Dap"
        
    def GetDefaultExt(self):
        return "dap"
        
    def GetDocTypeName(self):
        return "Dap Document"
        
    def GetViewTypeName(self):
        return _("Dap Editor")
        
    def GetDocTypeClass(self):
        return pyeditor.PythonDocument
        
    def GetViewTypeClass(self):
        return pyeditor.PythonView
        
    def GetDocIcon(self):
        return None
        return imageutils.getPythonIcon()
