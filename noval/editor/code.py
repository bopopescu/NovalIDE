# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        code.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-21
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp
import noval.editor.text as texteditor
import os
import re
import string
import sys
import noval.python.parser.config as parserconfig
import noval.util.strutils as strutils
import noval.consts as consts
import noval.util.appdirs as appdirs
import noval.util.utils as utils
import noval.syntax.syntax as syntax
import noval.constants as constants
from noval.syntax.syndata import BaseSyntaxcolorer
from noval.python.parser.utils import py_sorted
import noval.autocomplete as autocomplete
import noval.calltip as calltip

class CodeDocument(texteditor.TextDocument):
    def OnOpenDocument(self, filename):
        if not texteditor.TextDocument.OnOpenDocument(self,filename):
            return False
        #view = self.GetFirstView()
        #check_eol = wx.ConfigBase_Get().ReadInt(consts.CHECK_EOL_KEY, True)
        #if check_eol:
         #   view.GetCtrl().CheckEOL()
        return True

class CodeView(texteditor.TextView):

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------
    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        return CodeCtrl

    def OnChangeFilename(self):
        texteditor.TextView.OnChangeFilename(self)
       # if self.GetLangId() == lang.ID_LANG_PYTHON:
        #    self.LoadOutline(force=True)

    def LoadOutLine(self, outlineView,force=False,lineNum=-1):
        pass
 
    def GenCheckSum(self):
        """ Poor man's checksum.  We'll assume most changes will change the length of the file.
        """
        text = self.GetValue()
        if text:
            return len(text)
        else:
            return 0


    #----------------------------------------------------------------------------
    # Format methods
    #----------------------------------------------------------------------------

    def GetAutoCompleteHint(self):
        """获取自动完成的上下文以及提示内容"""
        return '',''

    def GetAutoCompleteDefaultKeywords(self):
        """ Replace this method with Editor specific keywords """
        lexer = self.GetCtrl().GetLangLexer()
        return lexer.GetKeywords()

    def GetAutoCompleteKeywords(self,line):
        return self.GetAutoCompleteDefaultKeywords()

    def GetAutoCompleteKeywordList(self, context, hint,line):            
        """ Replace this method with Editor specific keywords """
        kw = self.GetAutoCompleteKeywords(line)
        if not kw:
            return
        
        if hint and len(hint):
            lowerHint = hint.lower()
            filterkw = filter(lambda item: item.lower().startswith(lowerHint), kw)  # remove variables and methods that don't match hint
            kw = filterkw
        #提示补全的单词
        if hint:
            #补全单词已经输入的长度
            replaceLen = len(hint)
        else:
            replaceLen = 0
            
        kw = py_sorted(kw,cmp_func=strutils.caseInsensitiveCompare)
        return kw, replaceLen
                
    def GetLangId(self):
        lexer = self.GetCtrl().GetLangLexer()
        return lexer.GetLangId()
        
    def comment_region(self):
        lexer = self.GetCtrl().GetLangLexer()
        comment_pattern_list = lexer.GetDefaultCommentPattern()
        if 0 == len(comment_pattern_list):
            return
            
        comment_block = False
        if len(comment_pattern_list) > 1:
            comment_block = True
            
        head, tail, chars, lines = self.GetCtrl()._get_region()
        for pos in range(len(lines) - 1):
            line = lines[pos]
            if not comment_block:
                lines[pos] = comment_pattern_list[0]*2 + line
            else:
                if pos == 0:
                    lines[pos] = comment_pattern_list[0] + line
                if pos == (len(lines) - 2):
                    lines[pos] = lines[pos] + comment_pattern_list[1]
        self.GetCtrl()._set_region(head, tail, chars, lines)

    def uncomment_region(self):
        
        lexer = self.GetCtrl().GetLangLexer()
        comment_pattern_list = lexer.GetDefaultCommentPattern()
        if 0 == len(comment_pattern_list):
            return
            
        comment_block = False
        if len(comment_pattern_list) > 1:
            comment_block = True
            
        head, tail, chars, lines = self.GetCtrl()._get_region()
        #注释符号的长度
        comment_char_length = len(comment_pattern_list[0])
        for pos in range(len(lines)):
            line = lines[pos]
            if not line:
                continue
            if not comment_block:
                #起始2个注释符
                if line[:2*comment_char_length] == comment_pattern_list[0]*2:
                    line = line[2*comment_char_length:]
                #起始1个注释符
                elif line[:comment_char_length] == comment_pattern_list[0]:
                    line = line[comment_char_length:]
            lines[pos] = line
        self.GetCtrl()._set_region(head, tail, chars, lines)
        

    def UpdateUI(self, command_id):
        if command_id == constants.ID_INSERT_COMMENT_TEMPLATE:
            langid = self.GetLangId()
            lexer = syntax.SyntaxThemeManager().GetLexer(langid)
            enabled = lexer.IsCommentTemplateEnable()
            return enabled
        elif command_id == constants.ID_INSERT_DECLARE_ENCODING:
            return False
        elif command_id in [constants.ID_COMMENT_LINES,constants.ID_UNCOMMENT_LINES,constants.ID_AUTO_COMPLETE]:
            return True
        return texteditor.TextView.UpdateUI(self,command_id)

class CodeCtrl(texteditor.SyntaxTextCtrl):
    CURRENT_LINE_MARKER_NUM = 2
    BREAKPOINT_MARKER_NUM = 1
    CURRENT_LINE_MARKER_MASK = 0x4
    BREAKPOINT_MARKER_MASK = 0x4
    TYPE_BLANK_WORD = " "

    if utils.is_py2():
        DEFAULT_WORD_CHARS = string.letters + string.digits + '_'
    elif utils.is_py3_plus():
        DEFAULT_WORD_CHARS = string.ascii_letters + string.digits + '_'
            
    def __init__(self, main=None, cnf={}, **kw):
        texteditor.SyntaxTextCtrl.__init__(self, main, cnf=cnf, **kw)
        self._lang_lexer = None
        #允许绑定所有CodeCtrl类文件控件事件
        self.bindtags(self.bindtags() + ("CodeCtrl",))
        #设置单词列表
        self.fixwordbreaks(GetApp())
        self.autocompleter = None
        self.calltip = None
        self.tag_configure("before", syntax.SyntaxThemeManager().get_syntax_options_for_tag("active_focus"))
        #单击文本框时,关闭自动完成和文档提示
        self.bind("<1>", self.on_text_click)
        self.bind("<KeyPress>", self.OnChar, True)
        
    def on_text_click(self, event=None):
        #关闭文档提示信息
        self.CallTipHide()
        #关闭自动完成列表框
        self.AutoCompHide()

    def CreatePopupMenu(self):
        texteditor.TextCtrl.CreatePopupMenu(self)
        self._popup_menu.add_separator()
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetFormatMenu().FindMenuItem(consts.ID_COMMENT_LINES),\
                                    handler=self.main.main.GetView().comment_region)
                                    
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetFormatMenu().FindMenuItem(consts.ID_UNCOMMENT_LINES),\
                                    handler=self.main.main.GetView().uncomment_region)

    def DoIndent(self):
        self.AddText(self.GetEOLChar())
        self.EnsureCaretVisible()
        # Need to do a default one for all languges
            
    def GetLangLexer(self):
        if self._lang_lexer is None:
            document = self.main.main.GetView().GetDocument()
            file_ext = document.GetDocumentTemplate().GetDefaultExtension()
            self._lang_lexer = syntax.SyntaxThemeManager().GetLangLexerFromExt(file_ext)
        return self._lang_lexer
        
    def SetLangLexer(self,lexer):
        self._lang_lexer = lexer
        
    def SetSyntax(self,syntax_options):
        # apply new options
        for tag_name in syntax_options:
            if tag_name == "TEXT":
                self.configure(**syntax_options[tag_name])
            else:
                self.tag_configure(tag_name, **syntax_options[tag_name])

        self.tag_configure(list(BaseSyntaxcolorer.BASE_TAGDEFS)[0], {'background':None,'foreground':None})
        self.tag_configure(list(BaseSyntaxcolorer.BASE_TAGDEFS)[1],{'background':None,'foreground':None})
        self.SetOtherOptions(syntax_options)
        
    def GetColorClass(self):
        lexer = self.GetLangLexer()
        return lexer.GetColorClass()

    def SetKeyWords(self, kw_lst):
        """Sets the keywords from a list of keyword sets
        @param kw_lst: [ (KWLVL, "KEWORDS"), (KWLVL2, "KEYWORDS2"), ect...]

        """
        # Parse Keyword Settings List simply ignoring bad values and badly
        # formed lists
        kwlist = ""
        for keyw in kw_lst:
            if len(keyw) != 2:
                continue
            else:
                if not isinstance(keyw[0], int) or \
                   not isinstance(keyw[1], basestring):
                    continue
                else:
                    kwlist += keyw[1]
                    super(CodeCtrl, self).SetKeyWords(keyw[0], keyw[1])

        # Can't have ? in scintilla autocomp list unless specifying an image
        # TODO: this should be handled by the autocomp service
        if '?' in kwlist:
            kwlist.replace('?', '')

        kwlist = kwlist.split()         # Split into a list of words
        kwlist = list(set(kwlist))      # Remove duplicates from the list
        kwlist.sort()                   # Sort into alphabetical order
        
    def GetCharAt(self,line,col):
        return self.get("%d.%d"%(line,col),"%d.%d"%(line,col+1))
        
    def fixwordbreaks(self,root):
        '''
            重新设定单词分割,默认把括号等都当做单词
        '''
        # Adapted from idlelib.EditorWindow (Python 3.4.2)
        # Modified to include non-ascii chars

        # Make sure that Tk's double-click and next/previous word
        # operations use our definition of a word (i.e. an identifier)
        root.tk.call("tcl_wordBreakAfter", "a b", 0)  # make sure word.tcl is loaded
        # TODO: IDLE updated following to
        # root.tk.call('set', 'tcl_wordchars', r'\w')
        # root.tk.call('set', 'tcl_nonwordchars', r'\W')
        root.tk.call("set", "tcl_wordchars", u"[a-zA-Z0-9_À-ÖØ-öø-ÿĀ-ſƀ-ɏА-я]")
        root.tk.call("set", "tcl_nonwordchars", u"[^a-zA-Z0-9_À-ÖØ-öø-ÿĀ-ſƀ-ɏА-я]")

    def AutoCompShow(self,replaceLen,chars,auto_insert=True):
        '''
            显示自动完成列表框
            chars:显示内容列表
            replaceLen:已输入的内容长度,回车键插入填充内容时将不插入整个文本,而是只插入replaceLen长度以后的内容
        '''
        #列表内容为空时关闭已显示的自动完成列表框
        if 0 == len(chars):
            self.AutoCompHide()
            return
        if self.autocompleter is None:
            self.autocompleter = autocomplete.Completer(self)
        self.autocompleter._present_completions(chars,replaceLen,auto_insert)
        
    def AutoCompHide(self):
        '''
            关闭自动完成列表框
        '''
        if self.autocompleter is None:
            return
        self.autocompleter.close()
        
    def AutoCompActive(self):
        '''
            自动完成列表框是否可见
        '''
        if self.autocompleter is None:
            return False
        return self.autocompleter._is_visible()

    def OnChar(self,event):
        '''
            插入成双的符合对,并且光标置于一对符合的中间
        '''
        pos = self.GetCurrentPos()
        if event.char == "(":
            self.insert("insert", '()')
            self.GotoPos(pos[0],pos[1]+1)
            return "break"
        elif event.char == "'":
            #插入成双的单引号
            self.insert("insert", "'")
            self.GotoPos(pos[0],pos[1])
            #单引号字符是一样的不需要返回"break"
        elif event.char == '"':
            #插入成双的双引号
            self.insert("insert", '"')
            self.GotoPos(pos[0],pos[1])
            #双引号字符是一样的不需要返回"break"
        elif event.char == "[":
            self.insert("insert", '[]')
            self.GotoPos(pos[0],pos[1]+1)
            return "break"
        elif event.char == "{":
            self.insert("insert", '{}')
            self.GotoPos(pos[0],pos[1]+1)
            return "break"
        else:
            return None

    def CallTipShow(self,pos,tip):
        '''
            显示提示信息框
        '''
        if self.calltip is None:
            self.calltip = calltip.CalltipBox(self)
        self.calltip._show_box(pos,tip)
        
    def CallTipHide(self):
        '''
            隐藏提示信息框
        '''
        if self.calltip is None:
            return
        self.calltip.close()
        
    def ClearCurrentLineMarkers(self):
        '''
            调试下一步时,先要删除所有断点调试的标记,以便标记下一行
        '''
        self.remove_focus_tags()
        
    def MarkerAdd(self,line):
        '''
            标记并高亮断点调试的当前行
        '''
        self._tag_range(line,line,"active_focus")
        
    def _tag_range(self, start_line,end_line, tag):
        # For most statements I want to highlight block of whole lines
        # but for pseudo-statements (like header in for-loop) I want to highlight only the indicated range

        line_prefix = self.GetLineText(start_line)
        if line_prefix.strip():
            # pseudo-statement
            first_line = start_line
            last_line = end_line
            self.tag_add(
                tag,
                "%d.0" % (first_line),
                "%d.end" % (last_line),
            )
        else:
            # normal statement
            first_line, first_col, last_line = self._get_text_range_block(text_range)

            for lineno in range(first_line, last_line + 1):
                self._text.tag_add(tag, "%d.%d" % (lineno, first_col), "%d.0" % (lineno + 1))

        self.update_idletasks()
        self.see("%d.0" % (last_line))
        self.see("%d.0" % (first_line))

        if last_line - first_line < 3:
            # if it's safe to assume that whole code fits into screen
            # then scroll it down a bit so that expression view doesn't hide behind
            # lower edge of the editor
            self.update_idletasks()
            self.see("%d.0" % (first_line + 3))
            
    def remove_focus_tags(self):
        for name in [
            "exception_focus",
            "active_focus",
            "completed_focus",
            "suspended_focus",
            "sel",
        ]:
            self.tag_remove(name, "0.0", "end")
        
#重写perform_midline_tab方法,这里实现tab键自动完成单词功能
CodeCtrl.perform_midline_tab = autocomplete.patched_perform_midline_tab