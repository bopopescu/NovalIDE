#----------------------------------------------------------------------------
# Name:         strutils.py
# Purpose:      String Utilities
#
# Author:       Morgan Hua
#
# Created:      11/3/05
# CVS-ID:       $Id$
# Copyright:    (c) 2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------
import os
import re
import wx

_ = wx.GetTranslation

def caseInsensitiveCompare(s1, s2):
    """ Method used by sort() to sort values in case insensitive order """
    s1L = s1.lower()
    s2L = s2.lower()
    if s1L == s2L:
        return 0
    elif s1L < s2L:
        return -1
    else:
        return 1

def multiSplit(stringList, tokenList=[" "]):
    """Splits strings in stringList by tokens, returns list of string."""
    if not stringList: return []
    if isinstance(tokenList, basestring):
        tokenList = [tokenList]
    if isinstance(stringList, basestring):
        stringList = [stringList]
    rtnList = stringList
    for token in tokenList:
        rtnList = rtnList[:]
        for string in rtnList:
            if string.find(token) > -1:
                rtnList.remove(string)
                names = string.split(token)
                for name in names:
                    name = name.strip()
                    if name:
                        rtnList.append(name)
    return rtnList

QUOTES = ("\"", "'")

def _findArgStart(argStr):
    i = -1
    for c in argStr:
        i += 1
        if (c == " "):
            continue
        elif (c == ","):
            continue
        return i
    return None

def _findArgEnd(argStr):
    quotedArg = True
    argEndChar = argStr[0]
    if (not argEndChar in QUOTES):
        argEndChar = ","
        quotedArg = False
    i = -1
    firstChar = True
    for c in argStr:
        i+= 1
        if (firstChar):
            firstChar = False
            if (quotedArg):
                continue
        if (c == argEndChar):
            if (quotedArg):
                return min(i+1, len(argStr))
            else:
                return i
    return i

def parseArgs(argStr, stripQuotes=False):
    """
    Given a str representation of method arguments, returns list arguments (as
    strings).
    
    Input: "('[a,b]', 'c', 1)" -> Output: ["'[a,b]'", "'c'", "1"].

    If stripQuotes, removes quotes from quoted arg.
    """
    if (argStr.startswith("(")):
        argStr = argStr[1:]
        if (argStr.endswith(")")):
            argStr = argStr[:-1]
        else:
            raise AssertionError("Expected argStr to end with ')'")

    rtn = []
    argsStr = argStr.strip()
    while (True):
        startIndex = _findArgStart(argStr)
        if (startIndex == None):
            break
        argStr = argStr[startIndex:]
        endIndex = _findArgEnd(argStr)
        if (endIndex == len(argStr) - 1):
            rtn.append(argStr.strip())
            break        
        t = argStr[:endIndex].strip()
        if (stripQuotes and t[0] in QUOTES and t[-1] in QUOTES):
            t = t[1:-1]
        rtn.append(t)
        argStr = argStr[endIndex:]
    return rtn

def GetFileExt(filename,to_lower=True):
    basename = os.path.basename(filename)
    names = basename.split(".")
    if 1 == len(names):
        return ""
    if to_lower:
        return names[-1].lower()
    else:
        return names[-1]
    
def GetFilenameWithoutExt(file_path_name):
    filename = os.path.basename(file_path_name)
    return os.path.splitext(filename)[0]

def get_python_coding_declare(lines):
    # Only consider the first two lines
    CODING_REG_STR = re.compile(r'^[ \t\f]*#.*coding[:=][ \t]*([-\w.]+)')
    BLANK_REG_STR = re.compile(r'^[ \t\f]*(?:[#\r\n]|$)')
    lst = lines[:2]
    hit_line = 0
    for line in lst:
        match = CODING_REG_STR.match(line)
        if match is not None:
            break
        if not BLANK_REG_STR.match(line):
            return None,-1
        hit_line += 1
    else:
        return None,-1
    name = match.group(1)
    return name,hit_line
    
def emphasis_path(path):
    path = "\"%s\"" % path
    return path
    

def GenFileFilters(exclude_template_type = None):
    
    if wx.Platform == "__WXMSW__" or wx.Platform == "__WXGTK__" or wx.Platform == "__WXMAC__":
        descr = ''
        for temp in wx.GetApp().GetDocumentManager()._templates:
            if exclude_template_type is not None and temp.GetDocumentType() == exclude_template_type:
                continue
            if temp.IsVisible() :
                if len(descr) > 0:
                    descr = descr + _('|')
                descr = descr + _(temp.GetDescription()) + " (" + temp.GetFileFilter() + ") |" + temp.GetFileFilter()  # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
        descr = _("All Files") + "(*.*) |*.*|%s" % descr # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
    else:
        descr = "*.*"
        
    return descr
    

def HexToRGB(hex_str):
    """Returns a list of red/green/blue values from a
    hex string.
    @param hex_str: hex string to convert to rgb

    """
    hexval = hex_str
    if hexval[0] == u"#":
        hexval = hexval[1:]
    ldiff = 6 - len(hexval)
    hexval += ldiff * u"0"
    # Convert hex values to integer
    red = int(hexval[0:2], 16)
    green = int(hexval[2:4], 16)
    blue = int(hexval[4:], 16)
    return [red, green, blue]
    
def RGBToHex(clr):
    return "#%02x%02x%02x" % (clr.Red(),clr.Green(),clr.Blue())