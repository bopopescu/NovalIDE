#-------------------------------------------------------------------------------
# Name:        _txt.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-17
# Copyright:   (c) wukan 2019
# Licence:      GPL-3.0
#-------------------------------------------------------------------------------

from noval import _
from noval.syntax import syndata,lang
import os
import noval.util.appdirs as appdirs
from noval.editor import text as texteditor
import noval.imageutils as imageutils

#------------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for many C like languages""" 
    
    SYNTAX_ITEMS = [
    ]
    def __init__(self):
        syndata.BaseLexer.__init__(self,lang.ID_LANG_TXT)
        
    def GetShowName(self):
        return "Plain Text"
        
    def GetDefaultExt(self):
        return "txt"
        
    def GetExt(self):
        return "txt text"
        
    def GetDocTypeName(self):
        return "Text Document"
        
    def GetViewTypeName(self):
        return _("Text Editor")
        
    def GetDocTypeClass(self):
        return texteditor.TextDocument
        
    def GetViewTypeClass(self):
        return texteditor.TextView
        
    def GetDocIcon(self):
        return imageutils.getTextIcon()
        
    def GetDescription(self):
        return _("Text File")
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.GetAppDataDirLocation(),"sample","txt.sample")
        return self.GetSampleCodeFromFile(sample_file_path)

