###############################################################################
# Name: yaml.py                                                               #
# Purpose: Define YAML syntax for highlighting and other features             #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
FILE: yaml.py
AUTHOR: Cody Precord
@summary: Lexer configuration module for YAML
@todo: Maybe new custom style for text regions

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: _yaml.py 68798 2011-08-20 17:17:05Z CJP $"
__revision__ = "$Revision: 68798 $"

#-----------------------------------------------------------------------------#
# Imports
import wx
import wx.stc as stc

# Local Imports
from noval.tool.syntax import syndata,lang
import noval.tool.CodeEditor as CodeEditor
from noval.tool.consts import _

#-----------------------------------------------------------------------------#

#---- Keyword Definitions ----#
YAML_KW = [(0, "true false yes no")]

#---- End Keyword Definitions ----#





#---- Extra Properties ----#
FOLD_COMMENT = ("fold.comment.yaml", "1")

#-----------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for YAML""" 
    
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [
        (stc.STC_YAML_DEFAULT,      "DefaultText",     _("Default Text") ,  ''),
        (stc.STC_YAML_COMMENT,      "Comment",         _("Comment"),        'comment_style'),
        (stc.STC_YAML_DOCUMENT,     "Document",        _("Document"),       'scalar_style'),
        (stc.STC_YAML_ERROR,        "Error",           _("Error"),          'error_style'),
        (stc.STC_YAML_IDENTIFIER,   "Identifier",      _("Identifier"),     'keyword2_style'),
        (stc.STC_YAML_KEYWORD,      "KeyWord",         _("KeyWord"),        'keyword_style'),
        (stc.STC_YAML_NUMBER,       "Number",          _("Number"),         'number_style'),
        (stc.STC_YAML_REFERENCE,    "Reference",       _("Reference"),      'global_style'),
        (stc.STC_YAML_TEXT,         "Text",            _("Text"),           '')
    ] # Different style maybe
    
    if wx.VERSION >= (2, 9, 0, 0, ''):
        SYNTAX_ITEMS.append((stc.STC_YAML_OPERATOR, "Operator",   _("Operator"), 'operator_style'))
                
    def __init__(self):
        super(SyntaxLexer, self).__init__(lang.ID_LANG_YAML)

        # Setup
        self.SetLexer(stc.STC_LEX_YAML)

    def GetKeywords(self):
        """Returns Specified Keywords List """
        return YAML_KW

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS

    def GetProperties(self):
        """Returns a list of Extra Properties to set """
        return [FOLD_COMMENT]

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'#']
        
    def GetShowName(self):
        return "Yaml"
        
    def GetDefaultExt(self):
        return "yml"
        
    def GetDocTypeName(self):
        return "Yaml Document"
        
    def GetViewTypeName(self):
        return "Yaml View"
        
    def GetDocTypeClass(self):
        return CodeEditor.CodeDocument
        
    def GetViewTypeClass(self):
        return CodeEditor.CodeView
        
    def GetDocIcon(self):
        return None
