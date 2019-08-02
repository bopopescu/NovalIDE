# -*- coding: utf-8 -*-
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

class SyntaxColorer(syndata.BaseSyntaxcolorer):
    def __init__(self, text):
        syndata.BaseSyntaxcolorer.__init__(self,text)

    def schedule_update(self, event, use_coloring=True):
        '''
            文本文件不需要语法着色,故这里方法体为空
        '''
        self.allow_colorizing = use_coloring

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
        sample_file_path = os.path.join(appdirs.get_app_data_location(),"sample","txt.sample")
        return self.GetSampleCodeFromFile(sample_file_path)
        
    def GetColorClass(self):
        return SyntaxColorer

