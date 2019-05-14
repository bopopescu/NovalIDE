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
from noval.syntax import syndata,lang,matches_any
import noval.util.appdirs as appdirs
import os
import noval.editor.code as codeeditor
import noval.imageutils as imageutils
import re
import _c
    

#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

kwlist = _c.kwlist + ["class",'namespace',"public","private","protected","virtual","friend"]
KEYWORD = r"\b" + matches_any("keyword", kwlist) + r"\b"

_builtinlist = ['printf','scanf','getchar','putchar','time','strcpy','strcmp','isupper','memset','islower','isalpha','isdigit','toupper',\
                'tolower','ceil','floor','sqrt','pow','abs','rand','system','exit','srand']

BUILTIN = r"([^.'\"\\#]\b|^)" + matches_any("builtin", _builtinlist) + r"\b"
NUMBER = matches_any("number", [r"\b(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"])
# TODO: would it make regex too slow? VARIABLE = matches_any("VARIABLE", [...])


COMMENT = matches_any("comment", [r"/\*((?!\*/).)*\*/"])

#下面这两个是匹配双斜线注释和#预处理，好像需要相应方法，放在上面comment里测试是有效的
COMMENT_UNILINE = matches_any("comment_uniline", [r"//((?!\n).)*"])

PRETREATMENT = matches_any("preprocess",[r"#((?!\n).)*"])

STRINGPREFIX = (
    r"(\br|u|ur|R|U|UR|Ur|uR|b|B|br|Br|bR|BR|rb|rB|Rb|RB|f|F|fr|Fr|fR|FR|rf|rF|Rf|RF)?"
)

SQSTRING_OPEN = STRINGPREFIX + r"'[^'\\\n]*(\\.[^'\\\n]*)*\n?"
SQSTRING_CLOSED = STRINGPREFIX + r"'[^'\\\n]*(\\.[^'\\\n]*)*'"

DQSTRING_OPEN = STRINGPREFIX + r'"[^"\\\n]*(\\.[^"\\\n]*)*\n?'
DQSTRING_CLOSED = STRINGPREFIX + r'"[^"\\\n]*(\\.[^"\\\n]*)*"'


STRING_OPEN = matches_any("open_string", [SQSTRING_OPEN, DQSTRING_OPEN])
STRING_CLOSED = matches_any("string", [SQSTRING_CLOSED, DQSTRING_CLOSED])

#-----------------------------------------------------------------------------#

class SyntaxColorer(syndata.BaseSyntaxcolorer):
    def __init__(self, text):
        syndata.BaseSyntaxcolorer.__init__(self,text)
        self._compile_regexes()
        self._config_tags()

    def _compile_regexes(self):
        self.uniline_regex = re.compile(
            KEYWORD
            + "|"
            + BUILTIN
            + "|"
            + NUMBER
            + "|"
            + COMMENT
            + "|"
            + COMMENT_UNILINE
            + "|"
            + STRING_CLOSED
            + "|"
            + STRING_OPEN
            + "|"
            + PRETREATMENT,
            re.S,
        )  # @UndefinedVariable

        self.multiline_regex = re.compile(
            COMMENT + "|"
            # + "|" + STRING_CLOSED # need to include single line strings otherwise '"""' ... '""""' will give wrong result
            + STRING_OPEN,  # (seems that it works faster and also correctly with only open strings)
            re.S,
        )  # @UndefinedVariable

        self.id_regex = re.compile(r"\s+(\w+)", re.S)  # @UndefinedVariable

    def _config_tags(self):
        self.uniline_tagdefs = {
            "comment",
            "comment_uniline",
            "string",
            "open_string",
            "keyword",
            "number",
            "builtin",
			"preprocess",
        }
        self.multiline_tagdefs = {"string3", "open_string3"}
        self.text.tag_raise("sel")
        tags = self.text.tag_names()
        # take into account that without themes some tags may be undefined
        if "string3" in tags:
            self.text.tag_raise("string3")
        if "open_string3" in tags:
            self.text.tag_raise("open_string3")

    def schedule_update(self, event, use_coloring=True):
        self._use_coloring = use_coloring

        # Allow reducing work by remembering only changed lines
        if hasattr(event, "sequence"):
            if event.sequence == "TextInsert":
                index = self.text.index(event.index)
                start_row = int(index.split(".")[0])
                end_row = start_row + event.text.count("\n")
                start_index = "%d.%d" % (start_row, 0)
                end_index = "%d.%d" % (end_row + 1, 0)
            elif event.sequence == "TextDelete":
                index = self.text.index(event.index1)
                start_row = int(index.split(".")[0])
                start_index = "%d.%d" % (start_row, 0)
                end_index = "%d.%d" % (start_row + 1, 0)
        else:
            start_index = "1.0"
            end_index = "end"

        self._dirty_ranges.add((start_index, end_index))

        def perform_update():
            try:
                self._update_coloring()
            finally:
                self._update_scheduled = False
                self._dirty_ranges = set()

        if not self._update_scheduled:
            self._update_scheduled = True
            self.text.after_idle(perform_update)

    def _update_coloring(self):
        self._update_uniline_tokens("1.0", "end")
        self._update_multiline_tokens("1.0", "end")

    def _update_uniline_tokens(self, start, end):
        chars = self.text.get(start, end)

        # clear old tags
        for tag in self.uniline_tagdefs:
            self.text.tag_remove(tag, start, end)

        if not self._use_coloring:
            return

        for match in self.uniline_regex.finditer(chars):
            for token_type, token_text in match.groupdict().items():
                if token_text and token_type in self.uniline_tagdefs:
                    token_text = token_text.strip()
                    match_start, match_end = match.span(token_type)
                    if token_type == "comment_uniline":
                        token_type = "comment"
                    elif token_type == "preprocess":
                        token_type = "stdin"
                    self.text.tag_add(
                        token_type,
                        start + "+%dc" % match_start,
                        start + "+%dc" % match_end,
                    )

    def _update_multiline_tokens(self, start, end):
        chars = self.text.get(start, end)
        # clear old tags
        for tag in self.multiline_tagdefs:
            self.text.tag_remove(tag, start, end)

        if not self._use_coloring:
            return

        # Count number of open multiline strings to be able to detect when string gets closed
        self.text.number_of_open_multiline_strings = 0

        interesting_token_types = list(self.multiline_tagdefs) + ["string3"]
        for match in self.multiline_regex.finditer(chars):
            for token_type, token_text in match.groupdict().items():
                if token_text and token_type in interesting_token_types:
                    token_text = token_text.strip()
                    match_start, match_end = match.span(token_type)
                    if token_type == "string3":
                        if (
                            token_text.startswith('"""')
                            and not token_text.endswith('"""')
                            or token_text.startswith("'''")
                            and not token_text.endswith("'''")
                            or len(token_text) == 3
                        ):
                            str_end = int(
                                float(self.text.index(start + "+%dc" % match_end))
                            )
                            file_end = int(float(self.text.index("end")))

                            if str_end == file_end:
                                token_type = "open_string3"
                                self.text.number_of_open_multiline_strings += 1
                            else:
                                token_type = None
                        elif len(token_text) >= 4 and token_text[-4] == "\\":
                            token_type = "open_string3"
                            self.text.number_of_open_multiline_strings += 1
                        else:
                            token_type = "string3"

                    token_start = start + "+%dc" % match_start
                    token_end = start + "+%dc" % match_end
                    # clear uniline tags
                    for tag in self.uniline_tagdefs:
                        self.text.tag_remove(tag, token_start, token_end)
                    # add tag
                    self.text.tag_add(token_type, token_start, token_end)

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
