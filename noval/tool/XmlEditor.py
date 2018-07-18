#----------------------------------------------------------------------------
# Name:         XmlEditor.py
# Purpose:      Abstract Code Editor for pydocview tbat uses the Styled Text Control
#
# Author:       Peter Yared
#
# Created:      8/15/04
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------


import wx
import string
import STCTextEditor
import CodeEditor


class XmlDocument(CodeEditor.CodeDocument):

    pass


class XmlView(CodeEditor.CodeView):


    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        return XmlCtrl


    def GetAutoCompleteHint(self):
        pos = self.GetCtrl().GetCurrentPos()
        if pos == 0:
            return None, None
            
        validLetters = string.letters + string.digits + '_:'
        word = ''
        while (True):
            pos = pos - 1
            if pos < 0:
                break
            char = chr(self.GetCtrl().GetCharAt(pos))
            if char not in validLetters:
                break
            word = char + word
            
        return None, word


    def GetAutoCompleteDefaultKeywords(self):
        return XMLKEYWORDS


class XmlService(CodeEditor.CodeService):


    def __init__(self):
        CodeEditor.CodeService.__init__(self)


class XmlCtrl(CodeEditor.CodeCtrl):


    def __init__(self, parent, id=-1, style=wx.NO_FULL_REPAINT_ON_RESIZE):
        CodeEditor.CodeCtrl.__init__(self, parent, id, style)

    def GetMatchingBraces(self):
        return "<>[]{}()"


    def CanWordWrap(self):
        return True


    def SetViewDefaults(self):
        CodeEditor.CodeCtrl.SetViewDefaults(self, configPrefix = "Xml", hasWordWrap = True, hasTabs = True, hasFolding=True)


    def GetFontAndColorFromConfig(self):
        return CodeEditor.CodeCtrl.GetFontAndColorFromConfig(self, configPrefix = "Xml")


XMLKEYWORDS = [
        "ag:connectionstring", "ag:datasource", "ag:editorBounds", "ag:label", "ag:name", "ag:shortLabel", "ag:type",
        "element", "fractionDigits", "length", "minOccurs", "name", "objtype", "refer", "schema", "type", "xpath", "xmlns",
        "xs:complexType", "xs:element", "xs:enumeration", "xs:field", "xs:key", "xs:keyref", "xs:schema", "xs:selector"
    ]

#----------------------------------------------------------------------------
# Icon Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import ImageFromStream, BitmapFromImage
import cStringIO


def getXMLData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x08IDAT8\x8dc\xdc{\xf6\xde\x7f\x064p\xfb\xd1K\x06\x06\x06\x06\x86\
\xd7o\xbf2\xd4\xa5\xb93\xa2\xcb\xa3\x80\xbdg\xef\xfd\xbf\xff\xed?\x1c_\xf9\
\x04\xc13\xd6\x1f\xff\xbf\xeb\xf9\xff\xff\xcds\xf6\xfcgdbf\xc0\x85\x99\xb0\
\x19\xfa\xe5\x17\x82m\xee\xed\xcc\x90Z\xb7\x08\xc3\x950\xc0\x82\xcc\xf9\xfa\
\x07\xc1~\xfd\xf6+\xc3\xeb\xad{\x19\x1e?y\x89\xd7\x07,\xe8\x1aa\xb6\x9b{;300\
00(\xfdb`88\x7f\x19N\x03\x98`\x01\x86\xac\xf9\xd3o\xa8+\xa0\xfc\x07\x0f\x1e\
\xe3w\x01\xb2\x9f\xd15\xbf\xfa\x8e\xd7\x07\x0cL\xaf\xdf~%[3\xdc\x050\x8d\xa4\
jf````LkX\xfa\x7f\x8a\xcdi\xe2T\xe3r\x01\x03\x03\x03\xc3\xa7#\x13H\xd6|\xea1\
\x03jB\x12\xae\xffO\x14\x8d\x0cP\x0cx\xdb\xc8\xc8 \\\xff\x9f\xe1m#"\xf9c\xd3\
\x84b\xc0\xec\xa68\xb8j\x98fdM\xc8\x86\xc1\xd4 \xcb32213\xfc\xdc\x95\xfb\x9f\
\xdc0`A\xe6\x90\x03\x00\x11\x95\x8b;4e.A\x00\x00\x00\x00IEND\xaeB`\x82' 


def getXMLBitmap():
    return BitmapFromImage(getXMLImage())

def getXMLImage():
    stream = cStringIO.StringIO(getXMLData())
    return ImageFromStream(stream)

def getXMLIcon():
    return wx.IconFromBitmap(getXMLBitmap())
