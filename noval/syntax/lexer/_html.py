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
import _xml
#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#

# HTML Tags (HTML4)
HTML_TAGS = "address applet area a base basefont big blockquote br caption "\
            "center cite code dd dfn dir div dl dt font form hr html img "\
            "input isindex kbd li link map menu meta ol option param pre p "\
            "samp span select small strike sub sup table td textarea th tr "\
            "script noscript tt ul var xmp b i u h1 h2 h3 h4 h5 h6 em "\
            "strong head body title "\
            "abbr acronym bdo button col label colgroup del fieldset "\
            "iframe ins legend object optgroup q s tbody tfoot thead "\
            "article aside audio canvas command datalist details dialog "\
            "embed figcaption figure footer header hgroup keygen mark "\
            "meter nav output progress rp rt ruby section source time "\
            "video "\
            "action align alink alt archive background bgcolor border "\
            "bordercolor cellpadding cellspacing checked class clear "\
            "codebase color cols colspan content coords enctype face "\
            "gutter height hspace id link lowsrc marginheight marginwidth "\
            "maxlength method name prompt rel rev rows rowspan scrolling "\
            "selected shape size src start target text type url usemap "\
            "ismap valign value vlink vspace width wrap href http-equiv "\
            "accept accesskey axis char charoff charset cite classid "\
            "codetype compact data datetime declare defer dir disabled for "\
            "frame headers hreflang lang language longdesc multiple nohref "\
            "nowrap profile readonly rules scheme scope standby style "\
            "summary tabindex valuetype version "\
            "async autocomplete contenteditable contextmenu date "\
            "datetime-local draggable email formaction formenctype "\
            "formmethod formnovalidate formtarget hidden list manifest max "\
            "media min month novalidate number pattern ping range required "\
            "reversed role sandbox scoped seamless search sizes spellcheck "\
            "srcdoc step tel week "\
            "dtml-var dtml-if dtml-unless dtml-in dtml-with dtml-let "\
            "dtml-call dtml-raise dtml-try dtml-comment dtml-tree"\

SGML_KEYWORDS = "ELEMENT DOCTYPE ATTLIST ENTITY NOTATION"

def make_pat(kw_list):
    kw = get_keyword_pat(kw_list)
    pat = _xml.make_pat(is_html=True)
    return pat + "|" + kw

KW_LIST = HTML_TAGS.split() + SGML_KEYWORDS.split()
prog = get_prog(make_pat(KW_LIST))

#-----------------------------------------------------------------------------#

class SyntaxColorer(_xml.SyntaxColorer):
    def __init__(self, text):
        _xml.SyntaxColorer.__init__(self,text)
        self.prog = prog
        
class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for Python"""            
    def __init__(self):
        lang_id = lang.RegisterNewLangId("ID_LANG_HTML")
        syndata.BaseLexer.__init__(self,lang_id)
        
    def GetDescription(self):
        return _('HTML File')
        
    def GetExt(self):
        return "html htm shtm shtml xhtml"

    def GetDefaultCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'<!--', u'-->']

    def GetShowName(self):
        return "HTML"
        
    def GetDefaultExt(self):
        return "html"
        
    def GetDocTypeName(self):
        return "HTML Document"
        
    def GetViewTypeName(self):
        return _("HTML Editor")
        
    def GetDocTypeClass(self):
        return codeeditor.CodeDocument
        
    def GetViewTypeClass(self):
        return codeeditor.CodeView
        
    def GetDocIcon(self):
        return imageutils.load_image("","file/html.png")
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.get_app_data_location(),"sample","html.sample")
        return self.GetSampleCodeFromFile(sample_file_path)
        
    def GetColorClass(self):
        return SyntaxColorer
