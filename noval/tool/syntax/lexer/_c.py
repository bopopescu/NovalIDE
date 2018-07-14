###############################################################################
# Name: c.py                                                                #
# Purpose: Define C/CPP/ObjC/Vala syntax for highlighting and other features  #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################



# Local imports
from noval.tool.syntax import lang
import _cpp
import noval.tool.CodeEditor as CodeEditor
import noval.tool.images as images


#------------------------------------------------------------------------------#

class SyntaxLexer(_cpp.SyntaxLexer):
    """SyntaxData object for many C like languages""" 
    def __init__(self):
        super(SyntaxLexer, self).__init__(langid = lang.ID_LANG_C)
        
    def GetShowName(self):
        return "C"
        
    def GetDefaultExt(self):
        return "c"
        
    def GetDocTypeName(self):
        return "C Document"
        
    def GetViewTypeName(self):
        return "C View"
        
    def GetDocTypeClass(self):
        return CodeEditor.CodeDocument
        
    def GetViewTypeClass(self):
        return CodeEditor.CodeView
        
    def GetDocIcon(self):
        return images.getCFileIcon()
        
    def IsVisible(self):
        return False

