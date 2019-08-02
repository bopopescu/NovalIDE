# -*- coding: utf-8 -*-
import re

def matches_any(name, alternates):
    "Return a named group pattern matching list of alternates."
    return "(?P<%s>" % name + "|".join(alternates) + ")"

def get_keyword_pat(kwlist):
    '''
        匹配关键字
    '''
    kw = r"\b" + matches_any("keyword", kwlist) + r"\b"
    return kw

def get_builtin_pat(builtinlist):
    '''
        匹配内建函数
    '''
    builtin = r"([^.'\"\\#]\b|^)" + matches_any("builtin", builtinlist) + r"\b"
    return builtin

def get_number_pat():
    '''
        匹配数字
    '''
    number = matches_any("number", [r"\b(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"])
    return number


stringprefix = r"(\br|u|ur|R|U|UR|Ur|uR|b|B|br|Br|bR|BR)?"

def get_sqstring_pat():
    '''
        匹配单引号字符串
    '''
    sqstring = stringprefix + r"'[^'\\\n]*(\\.[^'\\\n]*)*'?"
    return sqstring

def get_dqstring_pat():
    '''
        匹配双引号字符串
    '''
    dqstring = stringprefix + r'"[^"\\\n]*(\\.[^"\\\n]*)*"?'
    return dqstring

def get_prog(pat):
    prog = re.compile(pat, re.S)
    return prog

def get_id_prog():
    '''
        匹配标识符
    '''
    idprog = re.compile(r"\s+(\w+)", re.S)
    return idprog