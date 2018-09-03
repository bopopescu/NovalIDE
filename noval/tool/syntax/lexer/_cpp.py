###############################################################################
# Name: cpp.py                                                                #
# Purpose: Define C/CPP/ObjC/Vala syntax for highlighting and other features  #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
FILE: cpp.py                                                                
@author: Cody Precord                                                       
@summary: Lexer configuration file for C/C++/C#/Objective C/Vala/Cilk source files.
                                                                         
"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: _cpp.py 68798 2011-08-20 17:17:05Z CJP $"
__revision__ = "$Revision: 68798 $"

#-----------------------------------------------------------------------------#
# Imports
import wx.stc as stc
import re

# Local imports
from noval.tool.syntax import syndata,lang
import noval.tool.CodeEditor as CodeEditor
import noval.tool.images as images
from noval.tool.consts import _
import noval.util.appdirs as appdirs
import os

#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

# C Keywords
C_KEYWORDS = ("asm break case const continue default do else for goto return "
              "if sizeof static switch typeof while")

# C Types/Structures/Storage Classes
C_TYPES = ("auto bool char clock_t complex div_t double enum extern float "
           "fpos_t inline int int_least8_t int_least16_t int_least32_t "
           "int_least64_t int8_t int16_t int32_t int64_t intmax_t intptr_t "
           "jmp_buf ldiv_t long mbstate_t ptrdiff_t register sig_atomic_t "
           "size_t ssize_t short signed struct typedef union time_t "
           "uint_fast8_t uint_fast16_t uint_fast32_t uint_fast64_t uint8_t "
           "uint16_t uint32_t uint64_t uintptr_t uintmax_t unsigned va_list "
           "void volatile wchar_t wctrans_t wctype_t wint_t FILE DIR __label__ "
           "__complex__ __volatile__ __attribute__")

# C/CPP Documentation Keywords (includes Doxygen keywords)
DOC_KEYWORDS = (2, "TODO FIXME XXX author brief bug callgraph category class "
                   "code date def depreciated dir dot dotfile else elseif em "
                   "endcode enddot endif endverbatim example exception file if "
                   "ifnot image include link mainpage name namespace page par "
                   "paragraph param pre post return retval section struct "
                   "subpage subsection subsubsection test todo typedef union "
                   "var verbatim version warning $ @ ~ < > # % HACK")

# CPP Keyword Extensions
CPP_KEYWORDS = ("and and_eq bitand bitor catch class compl const_cast delete "
                "dynamic_cast false friend new not not_eq operator or or_eq "
                "private protected public reinterpret_cast static_cast this "
                "throw try true typeid using xor xor_eq")

# CPP Type/Structure/Storage Class Extensions
CPP_TYPES = ("bool inline explicit export mutable namespace template typename "
             "virtual wchar_t")

# C# Keywords
CSHARP_KW = ("abstract as base break case catch checked class const continue  "
             "default delegate do else event explicit extern false finally "
             "fixed for foreach goto if implicit in interface internal is lock "
             "new null operator out override params readonly ref return sealed "
             "sizeof stackalloc static switch this throw true try typeof "
             "unchecked unsafe using while")

# C# Types
CSHARP_TYPES = ("bool byte char decimal double enum float int long "
                "namespace object private protected public sbyte short string "
                "struct uint ulong ushort virtual void volatile")

# Objective C
OBJC_KEYWORDS = ("@catch @interface @implementation @end @finally @private "
                 "@protected @protocol @public @throw @try self super false "
                 "true")

OBJC_TYPES = ("id")

# Vala Keywords
VALA_KEYWORDS = ("abstract as base break case catch checked construct continue "
                 "default delegate do else event false finally for foreach get "
                 "goto if implicit interface internal is lock new operator out "
                 "override params readonly ref return sealed set sizeof "
                 "stackalloc this throw true try typeof unchecked using while")

VALA_TYPES = ("bool byte char class const decimal double enum explicit extern "
              "fixed float int long namespace private protected public sbyte "
              "short static string struct uint ulong unichar unsafe ushort var "
              "volatile void virtual")

# Cilk Keywords
CILK_KEYWORDS = ("abort private shared spawn sync SYNCHED")

CILK_TYPES = ("cilk inlet")



#---- Extra Properties ----#
FOLD = ("fold", "1")
FOLD_PRE = ("styling.within.preprocessor", "0")
FOLD_COM = ("fold.comment", "1")
FOLD_COMP = ("fold.compact", "1")
FOLD_ELSE = ("fold.at.else", "0")
ALLOW_DOLLARS = ("lexer.cpp.allow.dollars", "1")

#------------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for many C like languages""" 
    #---- Syntax Style Specs ----#
    SYNTAX_ITEMS = [ 
         (stc.STC_C_DEFAULT,                "DefaultText",             _("Default Text") ,              ''),
         (stc.STC_C_COMMENT,                "Comment",                 _("Comment"),                    'comment_style'),
         (stc.STC_C_COMMENTLINE,            "CommentLine",             _("Comment Line"),               'comment_style'),
         (stc.STC_C_COMMENTDOC,             "CommentDoc",              _("Comment Doc"),                'comment_style'),
         (stc.STC_C_COMMENTDOCKEYWORD,      "CommentDocKeyWord",       _("Comment Doc KeyWord"),        'dockey_style'),
         (stc.STC_C_COMMENTDOCKEYWORDERROR, "CommentDocKeyWordError",  _("Comment Doc KeyWord Error"),  'error_style'),
         (stc.STC_C_COMMENTLINEDOC,         "CommentLineDoc",          _("Comment Line Doc"),           'comment_style'),
         (stc.STC_C_CHARACTER,              "Character",               _("Character"),                  'char_style'),
         (stc.STC_C_GLOBALCLASS,            "GlobalClass",             _("Global Class"),                'global_style'),
         (stc.STC_C_IDENTIFIER,             "Identifier",              _("Identifier"),                 ''),
         (stc.STC_C_NUMBER,                 "Number",                  _("Number"),                     'number_style'),
         (stc.STC_C_OPERATOR,               "Operator",                _("Operator"),                   'operator_style'),
         (stc.STC_C_PREPROCESSOR,           "Preprocessor",            _("Preprocessor"),               'pre_style'),
         (stc.STC_C_REGEX,                  "Regex",                   _("Regex"),                      'pre_style'),
         (stc.STC_C_STRING,                 "String",                  _("String"),                     'string_style'),
         (stc.STC_C_STRINGEOL,              "StringEOL",               _("String EOL"),                 'stringeol_style'),
         (stc.STC_C_VERBATIM,               "Verbatim",                _("Verbatim"),                   'number2_style'),
         (stc.STC_C_WORD,                   "KeyWord1",                _("KeyWord1"),                   'keyword_style'),
         (stc.STC_C_WORD2,                  "KeyWord2",                _("KeyWord2"),                   'keyword2_style') 
        ]
                 
    def __init__(self,langid = lang.ID_LANG_CPP):
        super(SyntaxLexer, self).__init__(langid)

        # Setup
        self.SetLexer(stc.STC_LEX_CPP)
       # self.RegisterFeature(synglob.FEATURE_AUTOINDENT, AutoIndenter)

    def GetKeywords(self):
        """Returns Specified Keywords List"""
        keywords = list()
        kw1_str = [C_KEYWORDS]
        kw2_str = [C_TYPES]
        if self.LangId == lang.ID_LANG_CPP or self.LangId == lang.ID_LANG_H:
            kw1_str.append(CPP_KEYWORDS)
            kw2_str.append(CPP_TYPES)
        else:
            pass

        keywords.append((0, " ".join(kw1_str)))
        keywords.append((1, " ".join(kw2_str)))
        keywords.append(DOC_KEYWORDS)
        return keywords

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return SYNTAX_ITEMS

    def GetProperties(self):
        """Returns a list of Extra Properties to set"""
        return [FOLD, FOLD_PRE, FOLD_COM]

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code

        """
        if self.LangId in [ synglob.ID_LANG_CPP,
                            synglob.ID_LANG_CSHARP,
                            synglob.ID_LANG_OBJC,
                            synglob.ID_LANG_VALA ]:
            return [u'//']
        else:
            return [u'/*', u'*/']
            
    def GetShowName(self):
        return "C/C++"
        
    def GetDefaultExt(self):
        return "cpp"
        
    def GetDocTypeName(self):
        return "CPP Document"
        
    def GetViewTypeName(self):
        return _("C++ Editor")
        
    def GetDocTypeClass(self):
        return CodeEditor.CodeDocument
        
    def GetViewTypeClass(self):
        return CodeEditor.CodeView
        
    def GetDocIcon(self):
        return images.getCppFileIcon()
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.GetAppDataDirLocation(),"sample","cpp.sample")
        return self.GetSampleCodeFromFile(sample_file_path)

#-----------------------------------------------------------------------------#

def AutoIndenter(estc, pos, ichar):
    """Auto indent cpp code.
    @param estc: EditraStyledTextCtrl
    @param pos: current carat position
    @param ichar: Indentation character
    @return: string

    """
    rtxt = u''
    line = estc.GetCurrentLine()
    text = estc.GetTextRange(estc.PositionFromLine(line), pos)
    eolch = estc.GetEOLChar()

    indent = estc.GetLineIndentation(line)
    if ichar == u"\t":
        tabw = estc.GetTabWidth()
    else:
        tabw = estc.GetIndent()

    i_space = indent / tabw
    ndent = eolch + ichar * i_space
    rtxt = ndent + ((indent - (tabw * i_space)) * u' ')

    cdef_pat = re.compile('(public|private|protected)\s*\:')
    case_pat = re.compile('(case\s+.+|default)\:')
    text = text.strip()
    if text.endswith('{') or cdef_pat.match(text) or case_pat.match(text):
        rtxt += ichar

    # Put text in the buffer
    estc.AddText(rtxt)
