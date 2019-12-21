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
from noval.syntax.pat import *

#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

kwlist = ['shift', 'unset', 'set', 'export', 'exit','readonly','if','fi','do','then','elif','else',
          'for','done']

_builtinlist = ['cat','echo','cp','sed','cd','sudo','sleep','grep','cut','ls','mv','rm',
                'du','df','more','less','clear','head','tail','wc','chown','time','mkdir']


def make_pat(kw_list):
    kw = get_keyword_pat(kw_list)
    builtin = get_builtin_pat(_builtinlist)
    comment = matches_any("comment", [r"#[^\n]*"])
    number = get_number_pat()
    sqstring = get_sqstring_pat()
    dqstring = get_dqstring_pat()
    string = matches_any("string", [sqstring, dqstring])
    pretreatment = matches_any("preprocess",[r"\${\w*}",r"\$((?![\n\s/:\.\+-]).)*"])
    return kw + "|" + builtin + "|" + comment + "|" + pretreatment + "|"+ string + "|" + number +\
           "|" + matches_any("SYNC", [r"\n"])

prog = get_prog(make_pat(kwlist))

#-----------------------------------------------------------------------------#

class SyntaxColorer(syndata.BaseSyntaxcolorer):
    def __init__(self, text):
        syndata.BaseSyntaxcolorer.__init__(self,text)
        self.prog = prog
        self._config_tags()

    def _config_tags(self):
        self.tagdefs.update({
        "stdin",
        })

    def AddTag(self,head,match_start,match_end,key,value,chars):
        #预处理标签颜色使用stdin标签的颜色
        if key == "preprocess":
            key = "stdin"
        syndata.BaseSyntaxcolorer.AddTag(self,head,match_start,match_end,key,value,chars)

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for Python""" 
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [ 
    ]
                 
    def __init__(self):
        lang_id = lang.RegisterNewLangId("ID_LANG_SHELL")
        syndata.BaseLexer.__init__(self,lang_id)

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS
        
    def GetDescription(self):
        return _('Bash/Shell Script')
        
    def GetExt(self):
        return "sh"

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'#']

    def GetShowName(self):
        return "Shell"
        
    def GetDefaultExt(self):
        return "sh"
        
    def GetDocTypeName(self):
        return "Shell Document"
        
    def GetViewTypeName(self):
        return _("Shell Editor")
        
    def GetDocTypeClass(self):
        return codeeditor.CodeDocument
        
    def GetViewTypeClass(self):
        return codeeditor.CodeView
        
    def GetDocIcon(self):
        return imageutils.load_image("","file/shell.png")

    def GetColorClass(self):
        return SyntaxColorer
        
    def IsVisible(self):
        return False

    def GetKeywords(self):
        return kwlist + _builtinlist
