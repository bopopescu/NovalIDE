###############################################################################
# Name: python.py                                                             #
# Purpose: Define Python syntax for highlighting and other features           #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
FILE: python.py
AUTHOR: Cody Precord
@summary: Lexer configuration module for Python.

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: _python.py 69016 2011-09-06 20:00:06Z CJP $"
__revision__ = "$Revision: 69016 $"

#-----------------------------------------------------------------------------#
# Imports
import wx.stc as stc
import keyword

# Local Imports
from noval.tool.syntax import syndata,lang
import noval.tool.PythonEditor as PythonEditor
from noval.tool.consts import _
import noval.util.appdirs as appdirs
import os

#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

# Indenter keywords
INDENT_KW = (u"def", u"if", u"elif", u"else", u"for", u"while",
             u"class", u"try", u"except", u"finally", u"with")
UNINDENT_KW = (u"return", u"raise", u"break", u"continue",
               u"pass", u"exit", u"quit")

# Python Keywords
KEYWORDS = keyword.kwlist
KEYWORDS.extend(['True', 'False', 'None', 'self'])
PY_KW = (0, u" ".join(KEYWORDS))

# Highlighted builtins
try:
    import __builtin__
    BUILTINS = dir(__builtin__)
except:
    BUILTINS = list()
#BUILTINS.append('self')
BUILTINS = list(set(BUILTINS))

PY_BIN = (1, u" ".join(sorted(BUILTINS)))

#---- Extra Properties ----#
FOLD = ("fold", "1")
FOLD_QUOTES = ("fold.quotes.python", "1")
FOLD_COMMENTS = ("fold.comment.python", "1")
TIMMY = ("tab.timmy.whinge.level", "1") # Mark Inconsistent indentation

#-----------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for Python""" 
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [ 
         (stc.STC_P_DEFAULT,      "DefaultText",  _("Default Text"),   ''),
         (stc.STC_P_CHARACTER,    "Character",    _("Character"),      'char_style'),
         (stc.STC_P_CLASSNAME,    "ClassName",    _("Class Name"),     'class_style'),
         (stc.STC_P_COMMENTBLOCK, "CommentBlock", _("Comment Block"),  'comment_style'),
         (stc.STC_P_COMMENTLINE,  "CommentLine",  _("Comment Line"),   'comment_style'),
         (stc.STC_P_DECORATOR,    "Decorator",    _("Decorator"),      'decor_style'),
         (stc.STC_P_DEFNAME,      "FunctionName", _("Function Name"),  'keyword3_style'),
         (stc.STC_P_IDENTIFIER,   "Identifier",   _("Identifier"),     ''),
         (stc.STC_P_NUMBER,       "Number",       _("Number"),         'number_style'),
         (stc.STC_P_OPERATOR,     "Operator",     _("Operator"),       'operator_style'),
         (stc.STC_P_STRING,       "String",       _("String"),         'string_style'),
         (stc.STC_P_STRINGEOL,    "StringEOL",    _("String EOL"),     'stringeol_style'),
         (stc.STC_P_TRIPLE,       "Triple",       _("Triple"),         'string_style'),
         (stc.STC_P_TRIPLEDOUBLE, "TripleDouble", _("Triple Double"),  'string_style'),
         (stc.STC_P_WORD,         "KeyWord1",     _("KeyWord1"),       'keyword_style'),
         (stc.STC_P_WORD2,        "KeyWord2",     _("KeyWord2"),       'userkw_style')
    ]
                 
    def __init__(self):
        super(SyntaxLexer, self).__init__(lang.ID_LANG_PYTHON)

        # Setup
        self.SetLexer(stc.STC_LEX_PYTHON)
       # self.RegisterFeature(synglob.FEATURE_AUTOINDENT, AutoIndenter)

    def GetKeywords(self):
        """Returns Specified Keywords List """
        return [PY_KW, PY_BIN]

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS

    def GetProperties(self):
        """Returns a list of Extra Properties to set """
        return [FOLD, TIMMY, FOLD_QUOTES, FOLD_COMMENTS]

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
        return PythonEditor.PythonDocument
        
    def GetViewTypeClass(self):
        return PythonEditor.PythonView
        
    def GetDocIcon(self):
        return PythonEditor.getPythonIcon()
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.GetAppDataDirLocation(),"sample","python.sample")
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

#-----------------------------------------------------------------------------#

def AutoIndenter(estc, pos, ichar):
    """Auto indent python code.
    @param estc: EditraStyledTextCtrl
    @param pos: current carat position
    @param ichar: Indentation character

    """
    line = estc.GetCurrentLine()
    spos = estc.PositionFromLine(line)
    text = estc.GetTextRange(spos, pos)
    eolch = estc.GetEOLChar()
    inspace = text.isspace()

    # Cursor is in the indent area somewhere
    if inspace:
        estc.AddText(eolch + text.replace(eolch, u""))
        return

    # Check if the cursor is in column 0 and just return newline.
    if not len(text):
        estc.AddText(eolch)
        return

    # In case of open bracket: Indent next to open bracket
    def BackTrack(tmp_text, tline):
        bcount = [ tmp_text.count(brac) for brac in u")}]({[" ]
        bRecurse = False
        for idx, val in enumerate(bcount[:3]):
            if val > bcount[idx+3]:
                bRecurse = True
                break
        if bRecurse:
            tline = tline - 1
            if tline < 0:
                return tmp_text
            spos = estc.PositionFromLine(tline)
            tmp_text = estc.GetTextRange(spos, pos)
            BackTrack(tmp_text, tline)
        return tmp_text
    text = BackTrack(text, line)
    pos = PosOpenBracket(text)
    if pos > -1:
        rval = eolch + (pos + 1) * u" "
        estc.AddText(rval)
        return

    indent = estc.GetLineIndentation(line)
    if ichar == u"\t":
        tabw = estc.GetTabWidth()
    else:
        tabw = estc.GetIndent()

    i_space = indent / tabw
    end_spaces = ((indent - (tabw * i_space)) * u" ")

    tokens = filter(None, text.strip().split())
    if tokens and not inspace:
        if tokens[-1].endswith(u":"):
            if tokens[0].rstrip(u":") in INDENT_KW:
                i_space += 1
        elif tokens[-1].endswith(u"\\"):
            i_space += 1
        elif len(tokens[-1]) and tokens[-1][-1] in u"}])":
            ptok = tokens[-1][-1]
            paren_pos = pos - (len(text) - text.rfind(ptok))
            oparen, cparen = estc.GetBracePair(paren_pos)
            if cparen >= 0: # Found matching bracket
                line = estc.LineFromPosition(cparen)
                indent = estc.GetLineIndentation(line)
                i_space = indent / tabw
                end_spaces = ((indent - (tabw * i_space)) * u" ")
        elif tokens[0] in UNINDENT_KW:
            i_space = max(i_space - 1, 0)

    rval = eolch + (ichar * i_space) + end_spaces
    if inspace and ichar != u"\t":
        rpos = indent - (pos - spos)
        if rpos < len(rval) and rpos > 0:
            rval = rval[:-rpos]
        elif rpos >= len(rval):
            rval = eolch

    # Put text in the buffer
    estc.AddText(rval)

#---- End Required Module Functions ----#

#---- Syntax Modules Internal Functions ----#
def KeywordString():
    """Returns the specified Keyword String
    @note: not used by most modules

    """
    return PY_KW[1]

def PosOpenBracket(text):
    """Returns the position of the right most open bracket in text.
    Brackets inside strings are ignored. In case of no open bracket
    the returned value is -1
    @param text: The line preceding the new line to be indented.
    @return res: The position of right most open bracket.
    @note: Used by AutoIndenter

    """
    # Store positions of '(', '[','{', ')', ']', '}'
    brackets = [[], [], [], [], [], []]
    quotes = u"'" + u'"'
    in_string = False
    for pos, char in enumerate(text):
        if in_string:
            in_string = not char == quote
        else:
            if char == u'#':
                break
            typ = u'([{)]}'.find(char)
            if typ > -1:
                brackets[typ].append(pos)
            else:
                typ = quotes.find(char)
                if typ > -1:
                    in_string = True
                    quote = quotes[typ]
    res = -1
    for typ in range(3):
        opn, cls = brackets[typ], brackets[typ+3]
        nopn, ncls = len(opn), len(cls)
        if nopn > ncls:
            res = max(res, opn[nopn - ncls - 1])
    return res

#---- End Syntax Modules Internal Functions ----#