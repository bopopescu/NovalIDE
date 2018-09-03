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
from noval.tool.consts import _
#------------------------------------------------------------------------------#

class SyntaxLexer(_cpp.SyntaxLexer):
    """SyntaxData object for many C like languages""" 
    def __init__(self):
        super(SyntaxLexer, self).__init__(langid = lang.ID_LANG_H)
        
    def GetShowName(self):
        return "C/C++"
        
    def GetDefaultExt(self):
        return "h"
        
    def GetDocTypeName(self):
        return "C/C++ Header Document"
        
    def GetViewTypeName(self):
        return _("C/C++ Header Editor")
        
    def GetDocTypeClass(self):
        return CodeEditor.CodeDocument
        
    def GetViewTypeClass(self):
        return CodeEditor.CodeView
        
    def GetDocIcon(self):
        return images.getCHeaderFileIcon()
        
    def IsVisible(self):
        return False

