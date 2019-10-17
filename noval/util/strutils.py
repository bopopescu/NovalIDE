# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        strutils.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-18
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------

import os
import re
import noval.python.parser.utils as parserutils
from noval.util import apputils
from noval import _,GetApp
import noval.util.txtutils as txtutils

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

def get_file_extension(filename,to_lower=True,has_dot=False):
    basename = os.path.basename(filename)
    names = basename.split(".")
    if 1 == len(names):
        return ""
    if to_lower:
        ext = names[-1].lower()
    else:
        ext = names[-1]
    if has_dot:
        ext = "." + ext
    return ext
    

def MakeNameEndInExtension(name, extension):
    if not name:
        return name
    ext = get_file_extension(name)
    if ext == extension:
        return name
    else:
        return name + extension
    
def get_filename_without_ext(file_path_name):
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
    
def gen_file_filters(exclude_template_type = None):
    filters = []
    for temp in GetApp().GetDocumentManager().GetTemplates():
        if exclude_template_type is not None and (temp.GetDocumentType() == exclude_template_type):
            continue
        if temp.IsVisible():
            filter = get_template_filter(temp)
            filters.append(filter)
    filters.append((_("All Files"),".*"))
    #将列表倒序,使"所有文件"显示在看得见的第一行
    filters = filters[::-1]
    return filters
    
def get_template_filter(template):
    descr = template.GetFileFilter()
    filter_types = [l.lstrip("*") for l in descr.split(";")]
    return (template.GetDescription(),' '.join(filter_types))
    

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
    

def EncodeString(string, encoding=None):
    """Try and encode a given unicode object to a string
    with the provided encoding returning that string. The
    default encoding will be used if None is given for the
    encoding.
    @param string: unicode object to encode into a string
    @keyword encoding: encoding to use for conversion

    """
    if not encoding:
        encoding = DEFAULT_ENCODING

    if txtutils.IsUnicode(string):
        try:
            rtxt = string.encode(encoding)
        except LookupError:
            rtxt = string
        return rtxt
    else:
        return string
        

def is_none_or_empty(value_str):
    return parserutils.IsNoneOrEmpty(value_str)
    
def is_same_path(path1,path2):
    return parserutils.ComparePath(path1,path2)
    
def compare_version(new_ver_str,old_ver_str):
    new_ver = parserutils.CalcVersionValue(new_ver_str)
    old_ver = parserutils.CalcVersionValue(old_ver_str)
    if new_ver == old_ver:
        return 0
    elif new_ver > old_ver:
        return 1
    else:
        return -1
        

def isInArgs(argname, argv):
    result = False
    if ("-" + argname) in argv:
        result = True
    if apputils.is_windows() and ("/" + argname) in argv:
        result = True        
    return result
    
def path_startswith(child_name, dir_name):
    '''
        判断路径是否包含另外一个路径
    '''
    normchild = os.path.normpath(os.path.normcase(child_name))
    normdir = os.path.normpath(os.path.normcase(dir_name))
    return normdir == normchild or normchild.startswith(normdir.rstrip(os.path.sep) + os.path.sep)

def normpath_with_actual_case(name):
    """In Windows return the path with the case it is stored in the filesystem"""
    assert os.path.isabs(name) or os.path.ismount(name), "Not abs nor mount: " + name
    assert os.path.exists(name), "Not exists: " + name
    if os.name == "nt":
        name = os.path.realpath(name)
        from ctypes import create_unicode_buffer, windll
        buf = create_unicode_buffer(512)
        windll.kernel32.GetShortPathNameW(name, buf, 512)  # @UndefinedVariable
        windll.kernel32.GetLongPathNameW(buf.value, buf, 512)  # @UndefinedVariable
        if len(buf.value):
            result = buf.value
        else:
            result = name
        assert isinstance(result, str)
        if result[1] == ":":
            # ensure drive letter is capital
            return result[0].upper() + result[1:]
        else:
            return result
    else:
        return os.path.normpath(name)