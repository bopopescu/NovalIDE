###############################################################################
# Name: c.py                                                                #
# Purpose: Define C/CPP/ObjC/Vala syntax for highlighting and other features  #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################



# Local imports
from noval.tool.syntax import syndata,lang
import noval.tool.STCTextEditor as STCTextEditor
import wx.stc as stc
from noval.tool.consts import _,GLOBAL_STYLE_NAME
import os
import noval.util.appdirs as appdirs

#------------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for many C like languages""" 
    
    SYNTAX_ITEMS = [ 
         (stc.STC_STYLE_DEFAULT, GLOBAL_STYLE_NAME,  _("Global Text"),   'default_style'),
         (stc.STC_STYLE_LINENUMBER, "LineNumber",  _("Line Number"),   'line_num'),
         (stc.STC_STYLE_CONTROLCHAR, "CtrlChar",  _("Ctrl Char"),   'ctrl_char'),
         (stc.STC_STYLE_BRACELIGHT, "BraceLight",  _("Brace Light"),   'brace_good'),
         (stc.STC_STYLE_BRACEBAD, "BraceBad",  _("Brace Bad"),   'brace_bad'),
         (stc.STC_STYLE_INDENTGUIDE, "IndentGuideLine",  _("Indent GuideLine"),   'guide_style')
    ]
    def __init__(self):
        super(SyntaxLexer, self).__init__()
        
    def GetShowName(self):
        return "Plain Text"
        
    def GetDefaultExt(self):
        return "txt"
        
    def GetDocTypeName(self):
        return "Text Document"
        
    def GetViewTypeName(self):
        return "Text View"
        
    def GetDocTypeClass(self):
        return STCTextEditor.TextDocument
        
    def GetViewTypeClass(self):
        return STCTextEditor.TextView
        
    def GetDocIcon(self):
        return STCTextEditor.getTextIcon()
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.GetAppDataDirLocation(),"sample","txt.sample")
        return self.GetSampleCodeFromFile(sample_file_path)

