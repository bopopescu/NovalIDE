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

kwlist = ['auto', 'double', 'int', 'struct', 'break', 'else', 'long', 'switch', 'case', 'enum',
          'register', 'typedef', 'char', 'extern', 'return', 'union', 'const', 'float', 'short', 'unsigned',
          'continue', 'for', 'signed', 'void', 'default', 'goto', 'sizeof', 'volatile', 'do', 'if', 'while', 'static']

_builtinlist = ['printf','scanf','getchar','putchar','time','strcpy','strcmp','isupper','memset','islower','isalpha','isdigit','toupper',\
                'tolower','ceil','floor','sqrt','pow','abs','rand','system','exit','srand']


def make_pat(kw_list):
    kw = get_keyword_pat(kw_list)
    # We don't know whether "print" is a function or a keyword,
    # so we always treat is as a keyword (the most common case).
    # self.file = file("file") :
    # 1st 'file' colorized normal, 2nd as builtin, 3rd as string
    builtin = get_builtin_pat(_builtinlist)
    #匹配块注释
    cregx = stringprefix + r"/\*((?!(\*/)).)*(\*/)?"
    comment = matches_any("comment", [cregx])
    #匹配预处理
    pretreatment = matches_any("preprocess",[r"#((?!\n).)*"])
    number = get_number_pat()
    sqstring = get_sqstring_pat()
    dqstring = get_dqstring_pat()
    string = matches_any("string", [sqstring, dqstring])
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
        lang_id = lang.RegisterNewLangId("ID_LANG_C")
        syndata.BaseLexer.__init__(self,lang_id)

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS
        
    def GetDescription(self):
        return _('C Source File')
        
    def GetExt(self):
        return "c"

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'/*',u'*/']

    def GetShowName(self):
        return "C"
        
    def GetDefaultExt(self):
        return "c"
        
    def GetDocTypeName(self):
        return "C Document"
        
    def GetViewTypeName(self):
        return _("C Editor")
        
    def GetDocTypeClass(self):
        return codeeditor.CodeDocument
        
    def GetViewTypeClass(self):
        return codeeditor.CodeView
        
    def GetDocIcon(self):
        return imageutils.load_image("","file/c_file.gif")
        
    def GetCommentTemplate(self):
        return '''/*******************************************************************************
* Name: {File}
* Copyright: (c) {Author} {Year}
* Author: {Author}
* Created: {Date}
* Description:
* Licence:     <your licence>
********************************************************************************/
'''
    def GetColorClass(self):
        return SyntaxColorer
        
    def IsVisible(self):
        return False

    def GetKeywords(self):
        return kwlist + _builtinlist
