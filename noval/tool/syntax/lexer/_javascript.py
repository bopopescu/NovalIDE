###############################################################################
# Name: javascript.py                                                         #
# Purpose: Define JavaScript syntax for highlighting and other features       #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
FILE: javascript.py
AUTHOR: Cody Precord
@summary: Lexer configuration module for JavaScript.

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: _javascript.py 70228 2011-12-31 20:39:16Z CJP $"
__revision__ = "$Revision: 70228 $"

#-----------------------------------------------------------------------------#
# Imports
import wx.stc as stc

# Local Imports
from noval.tool.syntax import syndata,lang
import noval.tool.CodeEditor as CodeEditor
import _cpp
from noval.tool.consts import _
import noval.tool.images as images

#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

# JavaScript Keywords # set to 1 for embeded
JS_KEYWORDS = (0, "abstract break boolean byte case const continue catch "
                  "class char debugger default delete do double default "
                  "export false else enum export extend final finally "
                  "float for function goto if implements import in " 
                  "instanceof int interface long native new null "
                  "package private protected public return short static "
                  "synchronized switch super this throw throws transient "
                  "try true typeof var void volatile with while")

#-----------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for JavaScript""" 
    #---- Syntax Style Spec ----#
    SYNTAX_ITEMS = [ 
         (stc.STC_HJ_DEFAULT,       "DefaultText",                 _("Default Text") ,                ''),
         (stc.STC_HJ_COMMENT,       "Comment",                     _("Comment"),                      'comment_style'),
         (stc.STC_HJ_COMMENTDOC,    "CommentDoc",                  _("Comment Doc"),                  'dockey_style'),
         (stc.STC_HJ_COMMENTLINE,   "CommentLine",                 _("Comment Line"),                 'comment_style'),
         (stc.STC_HJ_DOUBLESTRING,  "DoubleString",                _("Double String"),                'string_style'),
         (stc.STC_HJ_KEYWORD,       "KeyWord",                     _("KeyWord"),                      'keyword_style'),
         (stc.STC_HJ_NUMBER,        "Number",                      _("Number"),                       'number_style'),
         (stc.STC_HJ_REGEX,         "Regex",                       _("Regex"),                        'scalar_style'), # STYLE ME
         (stc.STC_HJ_SINGLESTRING,  "SingleString",                _("Single String"),                'string_style'),
         (stc.STC_HJ_START,         "Start",                       _("Start"),                        'scalar_style'),
         (stc.STC_HJ_STRINGEOL,     "StringEOL",                   _("String EOL"),                   'stringeol_style'),
         (stc.STC_HJ_SYMBOLS,       "Symbols",                     _("Symbols"),                      'array_style'),
         (stc.STC_HJ_WORD,          "Word",                        _("Word"),                         'class_style'),
         (stc.STC_HJA_COMMENT,      "ASPComment",                  _("ASP  Comment"),                 'comment_style'),
         (stc.STC_HJA_COMMENTDOC,   "ASPCommentDoc",               _("ASP  Comment Doc"),             'dockey_style'),
         (stc.STC_HJA_COMMENTLINE,  "ASPCommentLine",              _("ASP  Comment Line"),            'comment_style'),
         (stc.STC_HJA_DEFAULT,      "ASPDefaultText",              _("ASP  Default Text"),            ''),
         (stc.STC_HJA_DOUBLESTRING, "ASPDoubleString",             _("ASP  Double String"),           'string_style'),
         (stc.STC_HJA_KEYWORD,      "ASPKeyWord",                  _("ASP  KeyWord"),                 'keyword_style'),
         (stc.STC_HJA_NUMBER,       "ASPNumber",                   _("ASP  Number"),                  'number_style'),
         (stc.STC_HJA_REGEX,        "ASPRegex",                    _("ASP  Regex"),                   'scalar_style'), # STYLE ME
         (stc.STC_HJA_SINGLESTRING, "ASPSingleString",             _("ASP  Single String"),           'string_style'),
         (stc.STC_HJA_START,        "ASPStart",                    _("ASP  Start"),                   'scalar_style'),
         (stc.STC_HJA_STRINGEOL,    "ASPStringEOL",                _("ASP  String EOL"),              'stringeol_style'),
         (stc.STC_HJA_SYMBOLS,      "ASPSymbols",                  _("ASP  Symbols"),                 'array_style'),
         (stc.STC_HJA_WORD,         "ASPWord",                     _("ASP  Word"),                    'class_style') 
    ] + _cpp.SyntaxLexer.SYNTAX_ITEMS
    def __init__(self):
        super(SyntaxLexer, self).__init__(lang.ID_LANG_JS)

        # Setup
        self.SetLexer(stc.STC_LEX_CPP)
       # self.RegisterFeature(synglob.FEATURE_AUTOINDENT, _cpp.AutoIndenter)

    def GetKeywords(self):
        """Returns Specified Keywords List """
        return [JS_KEYWORDS,]

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        if self.LangId == synglob.ID_LANG_HTML:
            return SYNTAX_ITEMS
        else:
            return _cpp.SYNTAX_ITEMS

    def GetProperties(self):
        """Returns a list of Extra Properties to set """
        return [("fold", "1")]

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'//']
        
    def GetShowName(self):
        return "JavaScript"
        
    def GetDefaultExt(self):
        return "js"
        
    def GetDocTypeName(self):
        return "JavaScript Document"
        
    def GetViewTypeName(self):
        return _("JavaScript Editor")
        
    def GetDocTypeClass(self):
        return CodeEditor.CodeDocument
        
    def GetViewTypeClass(self):
        return CodeEditor.CodeView
        
    def GetDocIcon(self):
        return images.getJavaScriptFileIcon()

#---- Syntax Modules Internal Functions ----#
def KeywordString(option=0):
    """Returns the specified Keyword String
    @keyword option: specific subset of keywords to get

    """
    return JS_KEYWORDS[1]

#---- End Syntax Modules Internal Functions ----#
