# -*- coding: utf-8 -*-
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
import keyword
from noval.syntax import syndata,lang
import noval.util.appdirs as appdirs
import os
import noval.python.pyeditor as pyeditor
import noval.imageutils as imageutils
# Highlighted builtins
import six.moves.builtins as builtins
from noval.syntax.pat import *
#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

builtinlist = [str(name) for name in dir(builtins)
                                        if not name.startswith('_') and name not in keyword.kwlist]

def make_pat():
    kw = get_keyword_pat(keyword.kwlist)

    # We don't know whether "print" is a function or a keyword,
    # so we always treat is as a keyword (the most common case).
    # self.file = file("file") :
    # 1st 'file' colorized normal, 2nd as builtin, 3rd as string
    builtin = get_builtin_pat(builtinlist)
    comment = matches_any("comment", [r"#[^\n]*"])
    number = get_number_pat()
    sqstring = get_sqstring_pat()
    dqstring = get_dqstring_pat()
    sq3string = stringprefix + r"'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?"
    dq3string = stringprefix + r'"""[^"\\]*((\\.|"(?!""))[^"\\]*)*(""")?'
    string = matches_any("string", [sq3string, dq3string, sqstring, dqstring])
    return kw + "|" + builtin + "|" + comment + "|" + string + "|" + number +\
           "|" + matches_any("SYNC", [r"\n"])

prog = get_prog(make_pat())
idprog = get_id_prog()

#-----------------------------------------------------------------------------#

class SyntaxColorer(syndata.BaseSyntaxcolorer):
    def __init__(self, text):
        syndata.BaseSyntaxcolorer.__init__(self,text)
        self._config_tags()
        self.prog = prog
        self.idprog = idprog

    def _config_tags(self):
        self.tagdefs.update({
            "open_string",
            "definition"
        })

    def AddTag(self,head,match_start,match_end,key,value,chars):
        syndata.BaseSyntaxcolorer.AddTag(self,head,match_start,match_end,key,value,chars)
        if value in ("def", "class"):
            m1 = self.idprog.match(chars, match_end)
            if m1:
                a, b = m1.span(1)
                self.text.tag_add("definition",
                             head + "+%dc" % match_start,
                             head + "+%dc" % match_end)
                    
class ShellSyntaxColorer(SyntaxColorer):
    def __init__(self, text):
        SyntaxColorer.__init__(self,text)
        magic_command = matches_any("magic", [r"^%[^\n]*"])  # used only in shell
        self.prog = get_prog(make_pat()+ "|" + magic_command) 

    def _config_tags(self):
        SyntaxColorer._config_tags(self)
        self.tagdefs.update({
            "magic"
        })

    def _update_coloring(self):
        #TOTO end标签有待优化
        self.text.tag_remove("TODO", "1.0", "end")
        self.text.tag_add("SYNC", "1.0", "end")
        SyntaxColorer._update_coloring(self)

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for Python""" 
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [ 
    ]
                 
    def __init__(self):
        lang_id = lang.RegisterNewLangId("ID_LANG_PYTHON")
        syndata.BaseLexer.__init__(self,lang_id)

    def GetKeywords(self):
        """Returns Specified Keywords List """
        return [PY_KW, PY_BIN]

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS
        
    def GetDescription(self):
        return _('Python Script')
        
    def GetExt(self):
        return "py pyw"

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'#']

    def GetShowName(self):
        return "Python"
        
    def GetDefaultExt(self):
        return "py"
        
    def GetDocTypeName(self):
        return "Python Document"
        
    def GetViewTypeName(self):
        return _("Python Editor")
        
    def GetDocTypeClass(self):
        return pyeditor.PythonDocument
        
    def GetViewTypeClass(self):
        return pyeditor.PythonView
        
    def GetDocIcon(self):
        return imageutils.getPythonIcon()
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.get_app_data_location(),"sample","python.sample")
        return self.GetSampleCodeFromFile(sample_file_path)
        
    def GetCommentTemplate(self):
        return '''#-------------------------------------------------------------------------------
# Name:        {File}
# Purpose:
#
# Author:      {Author}
#
# Created:     {Date}
# Copyright:   (c) {Author} {Year}
# Licence:     <your licence>
#-------------------------------------------------------------------------------
'''
    def GetColorClass(self):
        return SyntaxColorer
        
    def GetShellColorClass(self):
        return ShellSyntaxColorer

    def GetKeywords(self):
        return keyword.kwlist + builtinlist
