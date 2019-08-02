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
import _c
from noval.syntax.pat import *
    

#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

kwlist = _c.kwlist + ["class",'namespace',"public","private","protected","virtual","friend"]

def make_pat(kw_list):
    pat = _c.make_pat(kw_list)
    #匹配双斜线注释
    comment_uniline = matches_any("comment_uniline", [r"//((?!\n).)*"])
    return pat + "|" + comment_uniline

prog = get_prog(make_pat(kwlist))
idprog = get_id_prog()

#-----------------------------------------------------------------------------#

class SyntaxColorer(_c.SyntaxColorer):
    def __init__(self, text):
        _c.SyntaxColorer.__init__(self,text)
        self.prog = prog
        self.idprog = idprog

    def AddTag(self,head,match_start,match_end,key,value,chars):
        #双斜线注释和c注释颜色一样
        if key == "comment_uniline":
            key = "comment"
        _c.SyntaxColorer.AddTag(self,head,match_start,match_end,key,value,chars)
        if value in ("class",):
            m1 = self.idprog.match(chars, match_end)
            if m1:
                a, b = m1.span(1)
                self.text.tag_add("definition",
                             head + "+%dc" % match_start,
                             head + "+%dc" % match_end)

    def _config_tags(self):
        _c.SyntaxColorer._config_tags(self)
        self.tagdefs.update({
            "definition"
        })

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for Python""" 
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [ 
    ]
                 
    def __init__(self):
        lang_id = lang.RegisterNewLangId("ID_LANG_CPP")
        syndata.BaseLexer.__init__(self,lang_id)

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS
        
    def GetDescription(self):
        return _('C++ Source File')
        
    def GetExt(self):
        return "cc c++ cpp cxx hh h++ hpp hxx"

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'//']

    def GetShowName(self):
        return "C/C++"
        
    def GetDefaultExt(self):
        return "cpp"
        
    def GetDocTypeName(self):
        return "C++ Document"
        
    def GetViewTypeName(self):
        return _("C++ Editor")
        
    def GetDocTypeClass(self):
        return codeeditor.CodeDocument
        
    def GetViewTypeClass(self):
        return codeeditor.CodeView
        
    def GetDocIcon(self):
        return imageutils.load_image("","file/cpp.png")
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.get_app_data_location(),"sample","cpp.sample")
        return self.GetSampleCodeFromFile(sample_file_path)
        
    def GetCommentTemplate(self):
        return '''//******************************************************************************
// Name: {File}
// Copyright: (c) {Author} {Year}
// Author: {Author}
// Created: {Date}
// Description:
// Licence:     <your licence>
//******************************************************************************
'''
    def GetColorClass(self):
        return SyntaxColorer

    def GetKeywords(self):
        return kwlist + _c._builtinlist
