# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        findctrl.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-14
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import _
import re
import tkinter as tk

class FindTextEngine:

    def __init__(self):
        self.last_processed_index = None

    def SetOption(self,find_option):
        self._find_option = find_option

    def getcookedpat(self):
        path = self._find_option.findstr
        if not self._find_option.regex:  # if True, see setcookedpat
            path = re.escape(path)
        if self._find_option.match_whole_word:
            path = r"\b%s\b" % path
        return path

    def getprog(self):
        "Return compiled cooked search pattern."
        path = self._find_option.findstr
        if not path:
            return None
        path = self.getcookedpat()
        flags = 0
        if not self._find_option.match_case:
            flags = flags | re.IGNORECASE
        try:
            prog = re.compile(path, flags)
        except re.error as what:
            args = what.args
            msg = args[0]
            col = args[1] if len(args) >= 2 else -1
            return None
        return prog

        
    def do_find(self, find_option,ok=0):
        '''Return (lineno, matchobj) or None for forward/backward search.

        This function calls the right function with the right arguments.
        It directly return the result of that call.

        Text is a text widget. Prog is a precompiled pattern.
        The ok parameter is a bit complicated as it has two effects.

        If there is a selection, the search begin at either end,
        depending on the direction setting and ok, with ok meaning that
        the search starts with the selection. Otherwise, search begins
        at the insert mark.

        To aid progress, the search functions do not return an empty
        match at the starting position unless ok is True.
        ok标志在替换字符串时需要设置为1
        '''
        self.SetOption(find_option)
        prog = self.getprog()
        if not prog:
            return None # Compilation failed -- stop
        wrap = self._find_option.wrap
        first, last = self.get_selection()
        if not self._find_option.down:
            if ok:
                start = last
            else:
                start = first
            line, col = self.get_line_col(start)
            res = self.search_backward(prog, line, col, wrap, ok)
        else:
            if ok:
                start = first
            else:
                start = last
            line, col = self.get_line_col(start)
            res = self.search_forward(prog, line, col, wrap, ok)
        return res

    def search_forward(self,prog, line, col, wrap, ok=0):
        '''
            向下搜索
        '''
        wrapped = 0
        startline = line
        chars = self.get("%d.0" % line, "%d.0" % (line+1))
        while chars:
            m = prog.search(chars[:-1], col)
            if m:
                if ok or m.end() > col:
                    return line, m
            line = line + 1
            if wrapped and line > startline:
                break
            col = 0
            ok = 1
            chars = self.get("%d.0" % line, "%d.0" % (line+1))
            if not chars and wrap:
                wrapped = 1
                wrap = 0
                line = 1
                chars = self.get("1.0", "2.0")
        return None

    def search_backward(self, prog, line, col, wrap, ok=0):
        '''
            向上搜索
        '''
        wrapped = 0
        startline = line
        chars = self.get("%d.0" % line, "%d.0" % (line+1))
        while 1:
            m = self.search_reverse(prog, chars[:-1], col)
            if m:
                if ok or m.start() < col:
                    return line, m
            line = line - 1
            if wrapped and line < startline:
                break
            ok = 1
            if line <= 0:
                if not wrap:
                    break
                wrapped = 1
                wrap = 0
                pos = self.index("end-1c")
                line, col = map(int, pos.split("."))
            chars = self.get("%d.0" % line, "%d.0" % (line+1))
            col = len(chars) - 1
        return None

    def search_reverse(self,prog, chars, col):
        '''Search backwards and return an re match object or None.

        This is done by searching forwards until there is no match.
        Prog: compiled re object with a search method returning a match.
        Chars: line of text, without \\n.
        Col: stop index for the search; the limit for match.end().
        '''
        m = prog.search(chars)
        if not m:
            return None
        found = None
        i, j = m.span()  # m.start(), m.end() == match slice indexes
        while i < col and j <= col:
            found = m
            if i == j:
                j = j+1
            m = prog.search(chars, j)
            if not m:
                break
            i, j = m.span()
        return found
        
    def find_and_select(self,res):
        line, m = res
        i, j = m.span()
        first = "%d.%d" % (line, i)
        last = "%d.%d" % (line, j)
        try:
            selfirst = self.index("sel.first")
            sellast = self.index("sel.last")
            if selfirst == first and sellast == last:
                self.bell()
                return False
        except TclError:
            pass
        self.tag_remove("sel", "1.0", "end")
        self.tag_add("sel", first, last)
        back = not self._find_option.down
        self.mark_set("insert",  back and first or last)
        self.see("insert")
        
    def do_wrap_search(self,info_label_var):
        line,col = self.get_line_col(self.index(tk.INSERT))
        wrap_search = False
        if self.last_processed_index:
            if self._find_option.down:
                if self.last_processed_index[0] > line:
                    wrap_search = True
                elif self.last_processed_index[0] == line and self.last_processed_index[1] >= col:
                    wrap_search = True
                if wrap_search:
                    info_label_var.set(_("search from the document begging!"))
            else:
                if self.last_processed_index[0] < line:
                    wrap_search = True
                elif self.last_processed_index[0] == line and self.last_processed_index[1] <= col:
                    wrap_search = True
                if wrap_search:
                    info_label_var.set(_("search from the document endding!"))
                    
        self.last_processed_index = line,col
        if wrap_search:
            self.last_processed_index = None
