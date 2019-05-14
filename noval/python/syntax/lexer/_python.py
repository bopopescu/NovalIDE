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
from noval.syntax import syndata,lang,matches_any
import noval.util.appdirs as appdirs
import os
import noval.python.pyeditor as pyeditor
import noval.imageutils as imageutils
import re

# Highlighted builtins
try:
    import __builtin__ as builtins
except:
    import builtins
    

#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

KEYWORD = r"\b" + matches_any("keyword", keyword.kwlist) + r"\b"
_builtinlist = [
    str(name)
    for name in dir(builtins)
    if not name.startswith("_") and name not in keyword.kwlist
]

# TODO: move builtin handling to global-local
BUILTIN = r"([^.'\"\\#]\b|^)" + matches_any("builtin", _builtinlist) + r"\b"
NUMBER = matches_any("number", [r"\b(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"])
# TODO: would it make regex too slow? VARIABLE = matches_any("VARIABLE", [...])

COMMENT = matches_any("comment", [r"#[^\n]*"])
MAGIC_COMMAND = matches_any("magic", [r"^%[^\n]*"])  # used only in shell
STRINGPREFIX = (
    r"(\br|u|ur|R|U|UR|Ur|uR|b|B|br|Br|bR|BR|rb|rB|Rb|RB|f|F|fr|Fr|fR|FR|rf|rF|Rf|RF)?"
)

SQSTRING_OPEN = STRINGPREFIX + r"'[^'\\\n]*(\\.[^'\\\n]*)*\n?"
SQSTRING_CLOSED = STRINGPREFIX + r"'[^'\\\n]*(\\.[^'\\\n]*)*'"

DQSTRING_OPEN = STRINGPREFIX + r'"[^"\\\n]*(\\.[^"\\\n]*)*\n?'
DQSTRING_CLOSED = STRINGPREFIX + r'"[^"\\\n]*(\\.[^"\\\n]*)*"'

SQ3STRING = STRINGPREFIX + r"'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?"
DQ3STRING = STRINGPREFIX + r'"""[^"\\]*((\\.|"(?!""))[^"\\]*)*(""")?'

SQ3DELIMITER = STRINGPREFIX + "'''"
DQ3DELIMITER = STRINGPREFIX + '"""'

STRING_OPEN = matches_any("open_string", [SQSTRING_OPEN, DQSTRING_OPEN])
STRING_CLOSED = matches_any("string", [SQSTRING_CLOSED, DQSTRING_CLOSED])
STRING3_DELIMITER = matches_any("DELIMITER3", [SQ3DELIMITER, DQ3DELIMITER])
STRING3 = matches_any("string3", [DQ3STRING, SQ3STRING])

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
            + MAGIC_COMMAND
            + "|"
            + STRING3_DELIMITER  # to avoid marking """ and ''' as single line string in uniline mode
            + "|"
            + STRING_CLOSED
            + "|"
            + STRING_OPEN,
            re.S,
        )  # @UndefinedVariable

        self.multiline_regex = re.compile(
            STRING3 + "|" + COMMENT + "|" + MAGIC_COMMAND
            # + "|" + STRING_CLOSED # need to include single line strings otherwise '"""' ... '""""' will give wrong result
            + "|"
            + STRING_OPEN,  # (seems that it works faster and also correctly with only open strings)
            re.S,
        )  # @UndefinedVariable

        self.id_regex = re.compile(r"\s+(\w+)", re.S)  # @UndefinedVariable

    def _config_tags(self):
        self.uniline_tagdefs = {
            "comment",
            "magic",
            "string",
            "open_string",
            "keyword",
            "number",
            "builtin",
            "definition",
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
        syndata.BaseSyntaxcolorer.schedule_update(self,event,use_coloring)
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

                    self.text.tag_add(
                        token_type,
                        start + "+%dc" % match_start,
                        start + "+%dc" % match_end,
                    )

                    # Mark also the word following def or class
                    if token_text in ("def", "class"):
                        id_match = self.id_regex.match(chars, match_end)
                        if id_match:
                            id_match_start, id_match_end = id_match.span(1)
                            self.text.tag_add(
                                "definition",
                                start + "+%dc" % id_match_start,
                                start + "+%dc" % id_match_end,
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
                    
class ShellSyntaxColorer(SyntaxColorer):
    def _update_coloring(self):
        parts = self.text.tag_prevrange("command", "end")

        if parts:
            end_row, end_col = map(int, self.text.index(parts[1]).split("."))

            if end_col != 0:  # if not just after the last linebreak
                end_row += 1  # then extend the range to the beginning of next line
                end_col = 0  # (otherwise open strings are not displayed correctly)

            start_index = parts[0]
            end_index = "%d.%d" % (end_row, end_col)

            self._update_uniline_tokens(start_index, end_index)
            self._update_multiline_tokens(start_index, end_index)

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
