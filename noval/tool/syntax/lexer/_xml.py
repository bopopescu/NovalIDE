###############################################################################
# Name: xml.py                                                                #
# Purpose: Define XML syntax for highlighting and other features              #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
FILE: xml.py
AUTHOR: Cody Precord
@summary: Lexer configuration module for XML Files.

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: _xml.py 68798 2011-08-20 17:17:05Z CJP $"
__revision__ = "$Revision: 68798 $"

#-----------------------------------------------------------------------------#
# Imports
import wx.stc as stc

# Local Imports
from noval.tool.syntax import syndata,lang
import _html
import noval.tool.XmlEditor as XmlEditor
from noval.tool.consts import _
import noval.util.appdirs as appdirs
import os

#-----------------------------------------------------------------------------#

#---- Keyword Specifications ----#

# Xml Keywords
XML_KEYWORDS = ("rss atom pubDate channel version title link description "
                "language generator item")

#-----------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for XML""" 
    
    SYNTAX_ITEMS = _html.SyntaxLexer.SYNTAX_ITEMS
    def __init__(self):
        super(SyntaxLexer, self).__init__(lang.ID_LANG_XML)

        # Setup
        self.SetLexer(stc.STC_LEX_XML)
       ## self.RegisterFeature(synglob.FEATURE_AUTOINDENT, _html.AutoIndenter)

    def GetKeywords(self):
        """Returns Specified Keywords List """
        sgml = _html.KeywordString(lang.ID_LANG_SGML)
        return [(5, XML_KEYWORDS + u" " + sgml)]

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return _html.SYNTAX_ITEMS

    def GetProperties(self):
        """Returns a list of Extra Properties to set """
        return [_html.FOLD, _html.FLD_HTML]

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'<!--', u'-->']
        
    def GetShowName(self):
        return "XML"
        
    def GetDefaultExt(self):
        return "xml"
        
    def GetDocTypeName(self):
        return "XML Document"
        
    def GetViewTypeName(self):
        return _("XML Editor")
        
    def GetDocTypeClass(self):
        return XmlEditor.XmlDocument
        
    def GetViewTypeClass(self):
        return XmlEditor.XmlView
        
    def GetDocIcon(self):
        return XmlEditor.getXMLIcon()
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.GetAppDataDirLocation(),"sample","xml.sample")
        return self.GetSampleCodeFromFile(sample_file_path)
