# -- coding: utf-8 --
#-------------------------------------------------------------------------------
# Name:        _xml.py
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
from noval.syntax.pat import *
import noval.util.appdirs as appdirs
import os
import noval.editor.code as codeeditor
import noval.imageutils as imageutils
import _cpp
#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#

kw_list = ['break', 'delete', 'function', 'return', 'typeof', 'case', 'do', 'if', \
           'switch', 'var', 'catch', 'else', 'in', 'this', 'void', 'continue', \
           'false', 'instanceof', 'throw', 'while', 'debugger', 'finally', \
           'new', 'true', 'with', 'default', 'for', 'null', 'try']
           
def make_pat():
    return _cpp.make_pat(kw_list)

prog = get_prog(make_pat())

#-----------------------------------------------------------------------------#

class SyntaxColorer(syndata.BaseSyntaxcolorer):
    def __init__(self, text):
        syndata.BaseSyntaxcolorer.__init__(self,text)
        self.prog = prog
        self.idprog = _cpp.get_id_prog()
        self._config_tags()

    def AddTag(self,head,match_start,match_end,key,value,chars):
        #双斜线注释和c注释颜色一样
        if key == "comment_uniline":
            key = "comment"
        syndata.BaseSyntaxcolorer.AddTag(self,head,match_start,match_end,key,value,chars)
        if value in ("function",):
            m1 = self.idprog.match(chars, match_end)
            if m1:
                id_match_start, id_match_end = m1.span(1)
                self.text.tag_add("definition",
                             head + "+%dc" % id_match_start,
                             head + "+%dc" % id_match_end)

    def _config_tags(self):
        self.tagdefs.update({
            "definition"
        })
        
class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for Python"""          
    def __init__(self):
        lang_id = lang.RegisterNewLangId("ID_LANG_JS")
        syndata.BaseLexer.__init__(self,lang_id)
        
    def GetDescription(self):
        return _('JavaScript File')
        
    def GetExt(self):
        return "js"

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
        return codeeditor.CodeDocument
        
    def GetViewTypeClass(self):
        return codeeditor.CodeView
        
    def GetDocIcon(self):
        return imageutils.load_image("","file/javascript.png")
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.get_app_data_location(),"sample","xml.sample")
        return self.GetSampleCodeFromFile(sample_file_path)
        
    def GetColorClass(self):
        return SyntaxColorer
