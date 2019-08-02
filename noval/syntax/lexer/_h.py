# -- coding: utf-8 --
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
import noval.util.appdirs as appdirs
import os
import noval.editor.code as codeeditor
import noval.imageutils as imageutils
import re
import _cpp
import _c

class SyntaxLexer(_c.SyntaxLexer):
    """SyntaxData object for Python""" 
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [ 
    ]
                 
    def __init__(self):
        lang_id = lang.RegisterNewLangId("ID_LANG_H")
        syndata.BaseLexer.__init__(self,lang_id)

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS
        
    def GetDescription(self):
        return _('C/C++ Header File')
        
    def GetExt(self):
        return "h"

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'/*',u'*/']

    def GetShowName(self):
        return "C/C++"
        
    def GetDefaultExt(self):
        return "h"
        
    def GetDocTypeName(self):
        return "C/C++ Header Document"
        
    def GetViewTypeName(self):
        return _("C/C++ Header Editor")
        
    def GetDocTypeClass(self):
        return codeeditor.CodeDocument
        
    def GetViewTypeClass(self):
        return codeeditor.CodeView
        
    def GetDocIcon(self):
        return imageutils.load_image("","file/h_file.gif")
    
    def GetColorClass(self):
        return _cpp.SyntaxColorer
        
    def IsVisible(self):
        return False
