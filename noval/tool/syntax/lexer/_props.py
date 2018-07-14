###############################################################################
# Name: props.py                                                              #
# Purpose: Define Properties/ini syntax for highlighting and other features   #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
FILE: props.py
AUTHOR: Cody Precord
@summary: Lexer configuration module for properties/config files
          (ini, cfg, ect..).

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: _props.py 68798 2011-08-20 17:17:05Z CJP $"
__revision__ = "$Revision: 68798 $"

#-----------------------------------------------------------------------------#
# Imports
import wx.stc as stc

# Imports
from noval.tool.syntax import syndata,lang
import noval.tool.CodeEditor as CodeEditor
from noval.tool.consts import _
import noval.tool.images as images
import noval.util.appdirs as appdirs
import os

#-----------------------------------------------------------------------------#


#---- Extra Properties ----#
FOLD = ('fold', '1')

#-----------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for Properties files""" 
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [
        (stc.STC_PROPS_DEFAULT,     "DefaultText",      _("Default Text"), 'default_style'),
        (stc.STC_PROPS_ASSIGNMENT,  "Assignment",       _("Assignment"),   'operator_style'),
        (stc.STC_PROPS_COMMENT,     "Comment",          _("Comment"),      'comment_style'),
        (stc.STC_PROPS_DEFVAL,      "Defval",           _("Defval"),        'string_style'),
        (stc.STC_PROPS_KEY,         "Key",              _("Key"),          'scalar_style'),
        (stc.STC_PROPS_SECTION,     "Section",          _("Section"),      'keyword_style')
    ]
    def __init__(self):
        super(SyntaxLexer, self).__init__(lang.ID_LANG_PROPS)

        # Setup
        self.SetLexer(stc.STC_LEX_PROPERTIES)

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS

    def GetProperties(self):
        """Returns a list of Extra Properties to set """
        return [FOLD]

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return list(u'#')
        
    def GetShowName(self):
        return "Properties"
        
    def GetDefaultExt(self):
        return "ini"
        
    def GetDocTypeName(self):
        return "Property Document"
        
    def GetViewTypeName(self):
        return "Property View"
        
    def GetDocTypeClass(self):
        return CodeEditor.CodeDocument
        
    def GetViewTypeClass(self):
        return CodeEditor.CodeView
        
    def GetDocIcon(self):
        return images.getConfigFileIcon()
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.GetAppDataDirLocation(),"sample","ini.sample")
        return self.GetSampleCodeFromFile(sample_file_path)
