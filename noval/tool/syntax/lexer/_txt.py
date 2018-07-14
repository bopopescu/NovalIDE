###############################################################################
# Name: c.py                                                                #
# Purpose: Define C/CPP/ObjC/Vala syntax for highlighting and other features  #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################



# Local imports
from noval.tool.syntax import syndata,lang
import noval.tool.STCTextEditor as STCTextEditor



#------------------------------------------------------------------------------#

class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for many C like languages""" 
    def __init__(self):
        super(SyntaxLexer, self).__init__()
        
    def GetShowName(self):
        return "Plain Text"
        
    def GetDefaultExt(self):
        return "txt"
        
    def GetDocTypeName(self):
        return "Text Document"
        
    def GetViewTypeName(self):
        return "Text View"
        
    def GetDocTypeClass(self):
        return STCTextEditor.TextDocument
        
    def GetViewTypeClass(self):
        return STCTextEditor.TextView
        
    def GetDocIcon(self):
        return STCTextEditor.getTextIcon()

