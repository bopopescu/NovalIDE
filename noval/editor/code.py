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
import noval.python.parser.nodeast as nodeast
import noval.python.parser.intellisence as intellisence
import noval.python.parser.config as parserconfig
import noval.util.strutils as strutils
import noval.consts as consts
import noval.util.appdirs as appdirs
import noval.util.utils as utils
import noval.syntax.syntax as syntax
import noval.constants as constants

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

    def OnAutoComplete(self):
        self.GetCtrl().AutoCompCancel()
        self.GetCtrl().AutoCompSetAutoHide(0)
        self.GetCtrl().AutoCompSetChooseSingle(True)
        self.GetCtrl().AutoCompSetIgnoreCase(True)
        context, hint = self.GetAutoCompleteHint()
        replaceList, replaceLen = self.GetAutoCompleteKeywordList(context, hint,self.GetCtrl().GetCurrentLine())
        if replaceList and len(replaceList) != 0: 
            self.GetCtrl().AutoCompShow(replaceLen, replaceList)


    def GetAutoCompleteHint(self):
        """ Replace this method with Editor specific method """
        pos = self.GetCtrl().GetCurrentPos()
        if pos == 0:
            return None, None
        if chr(self.GetCtrl().GetCharAt(pos - 1)) == '.':
            pos = pos - 1
            hint = None
        else:
            hint = ''
            
        validLetters = string.letters + string.digits + '_.'
        word = ''
        while (True):
            pos = pos - 1
            if pos < 0:
                break
            char = chr(self.GetCtrl().GetCharAt(pos))
            if char not in validLetters:
                break
            word = char + word
            
        context = word
        if hint is not None:            
            lastDot = word.rfind('.')
            if lastDot != -1:
                context = word[0:lastDot]
                hint = word[lastDot+1:]
                    
        return context, hint
        

    def GetAutoCompleteDefaultKeywords(self):
        """ Replace this method with Editor specific keywords """
        return ['Put', 'Editor Specific', 'Keywords', 'Here']


    def GetAutoCompleteKeywordList(self, context, hint,line):            
        """ Replace this method with Editor specific keywords """
        kw = self.GetAutoCompleteDefaultKeywords()
        
        if hint and len(hint):
            lowerHint = hint.lower()
            filterkw = filter(lambda item: item.lower().startswith(lowerHint), kw)  # remove variables and methods that don't match hint
            kw = filterkw

        if hint:
            replaceLen = len(hint)
        else:
            replaceLen = 0
            
        kw.sort(CaseInsensitiveCompare)
        return " ".join(kw), replaceLen
        

    def OnCleanWhiteSpace(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = string.rstrip(self.GetCtrl().GetLine(lineNo))
            indent = 0
            lstrip = 0
            for char in lineText:
                if char == '\t':
                    indent = indent + self.GetCtrl().GetIndent()
                    lstrip = lstrip + 1
                elif char in string.whitespace:
                    indent = indent + 1
                    lstrip = lstrip + 1
                else:
                    break
            if self.GetCtrl().GetUseTabs():
                indentText = (indent / self.GetCtrl().GetIndent()) * '\t' + (indent % self.GetCtrl().GetIndent()) * ' '
            else:
                indentText = indent * ' '
            lineText = indentText + lineText[lstrip:] + '\n'
            newText = newText + lineText
        self._ReplaceSelectedLines(newText)


    def OnSetIndentWidth(self):
        dialog = wx.TextEntryDialog(self._GetParentFrame(), _("Enter new indent width (2-10):"), _("Set Indent Width"), "%i" % self.GetCtrl().GetIndent())
        dialog.CenterOnParent()
        if dialog.ShowModal() == wx.ID_OK:
            try:
                indent = int(dialog.GetValue())
                if indent >= 2 and indent <= 10:
                    self.GetCtrl().SetIndent(indent)
                    self.GetCtrl().SetTabWidth(indent)
            except:
                pass
        dialog.Destroy()


    def GetIndentWidth(self):
        return self.GetCtrl().GetIndent()
                

    def OnCommentLines(self):
        lexer = self.GetCtrl().GetLangLexer()
        comment_pattern_list = lexer.GetCommentPattern()
        if 0 == len(comment_pattern_list):
            return
        newText = ""
        comment_block = False
        if len(comment_pattern_list) > 1:
            comment_block = True
        if not comment_block:
            for lineNo in self._GetSelectedLineNumbers():
                lineText = self.GetCtrl().GetLine(lineNo)
                if len(lineText) > 1 and lineText.startswith(comment_pattern_list[0]):
                    newText = newText + lineText
                else:
                    newText = newText + comment_pattern_list[0] + lineText
        else:
            selected_line_nums = self._GetSelectedLineNumbers()
            for i,lineNo in enumerate(selected_line_nums):
                lineText = self.GetCtrl().GetLine(lineNo)
                if i == 0:
                    newText = newText + comment_pattern_list[0] + lineText
                elif i == len(selected_line_nums) - 1:
                    if lineText.endswith(consts.CR_LF_EOL_CHAR):
                        lineText = lineText[0:len(lineText)  - len(consts.CR_LF_EOL_CHAR)] + comment_pattern_list[1] + consts.CR_LF_EOL_CHAR
                        
                    elif lineText.endswith(consts.CR_EOL_CHAR) or lineText.endswith(consts.LF_EOL_CHAR):
                        lineText = lineText[0:len(lineText)  - 1] + comment_pattern_list[1] + lineText[-1]
                    else:
                        lineText = lineText + comment_pattern_list[1]
                    newText = newText + lineText
                else:
                    newText = newText + lineText
        self._ReplaceSelectedLines(newText)


    def OnUncommentLines(self):
        lexer = self.GetCtrl().GetLangLexer()
        comment_pattern_list = lexer.GetCommentPattern()
        if 0 == len(comment_pattern_list):
            return
            
        comment_block = False
        if len(comment_pattern_list) > 1:
            comment_block = True
            
        newText = ""
        if not comment_block:
            for lineNo in self._GetSelectedLineNumbers():
                lineText = self.GetCtrl().GetLine(lineNo)
                if len(lineText) > 1 and lineText.startswith(comment_pattern_list[0]):
                    lineText = lineText[len(comment_pattern_list[0]):]
                newText = newText + lineText
        else:
            selected_line_nums = self._GetSelectedLineNumbers()
            for i,lineNo in enumerate(selected_line_nums):
                lineText = self.GetCtrl().GetLine(lineNo)
                if i == 0 and lineText.startswith(comment_pattern_list[0]):
                    lineText = lineText[len(comment_pattern_list[0]):]
                elif i == len(selected_line_nums) - 1 and lineText.strip().endswith(comment_pattern_list[1]):
                    if lineText.endswith(consts.CR_LF_EOL_CHAR):
                        lineText = lineText[0:len(lineText) - len(comment_pattern_list[1])-len(consts.CR_LF_EOL_CHAR)] + consts.CR_LF_EOL_CHAR
                    elif lineText.endswith(consts.CR_EOL_CHAR) or lineText.endswith(consts.LF_EOL_CHAR):
                        lineText = lineText[0:len(lineText) - len(comment_pattern_list[1])-len(consts.LF_EOL_CHAR)] + lineText[-1]
                    else:
                        lineText = lineText[0:len(lineText) - len(comment_pattern_list[1])]
                newText = newText + lineText
        self._ReplaceSelectedLines(newText)
        
    def _GetSelectedLineNumbers(self):
        selStart, selEnd,is_last_line = self._GetPositionsBoundingSelectedLines()
        endLine = self.GetCtrl().LineFromPosition(selEnd)
        if is_last_line:
            endLine += 1
        return range(self.GetCtrl().LineFromPosition(selStart), endLine)


    def _GetPositionsBoundingSelectedLines(self):
        startPos = self.GetCtrl().GetCurrentPos()
        endPos = self.GetCtrl().GetAnchor()
        if startPos > endPos:
            temp = endPos
            endPos = startPos
            startPos = temp
        if endPos == self.GetCtrl().PositionFromLine(self.GetCtrl().LineFromPosition(endPos)):
            endPos = endPos - 1  # If it's at the very beginning of a line, use the line above it as the ending line
        selStart = self.GetCtrl().PositionFromLine(self.GetCtrl().LineFromPosition(startPos))
        line_num = self.GetCtrl().LineFromPosition(endPos)
        selEnd = self.GetCtrl().PositionFromLine(line_num + 1)
        
        return selStart, selEnd,line_num == self.GetCtrl().LineFromPosition(selEnd)


    def _ReplaceSelectedLines(self, text):
        if len(text) == 0:
            return
        selStart, selEnd,_is_last_line = self._GetPositionsBoundingSelectedLines()
        self.GetCtrl().SetSelection(selStart, selEnd)
        self.GetCtrl().ReplaceSelection(text)
        self.GetCtrl().SetSelection(selStart + len(text), selStart)

    def OnUpdate(self, sender = None, hint = None):
        if texteditor.TextView.OnUpdate(self, sender, hint):
            return
                
    def GetLangId(self):
        lexer = self.GetCtrl().GetLangLexer()
        return lexer.GetLangId()
        
    def comment_region(self):
        lexer = self.GetCtrl().GetLangLexer()
        comment_pattern_list = lexer.GetCommentPattern()
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
        comment_pattern_list = lexer.GetCommentPattern()
        if 0 == len(comment_pattern_list):
            return
            
        comment_block = False
        if len(comment_pattern_list) > 1:
            comment_block = True
            
        head, tail, chars, lines = self.GetCtrl()._get_region()
        for pos in range(len(lines)):
            line = lines[pos]
            if not line:
                continue
            if not comment_block:
                if line[:2] == comment_pattern_list[0]*2:
                    line = line[2:]
                elif line[:1] == comment_pattern_list[0]:
                    line = line[1:]
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
        elif command_id in [constants.ID_COMMENT_LINES,constants.ID_UNCOMMENT_LINES]:
            return True
        return texteditor.TextView.UpdateUI(self,command_id)

class CodeCtrl(texteditor.TextCtrl):
    CURRENT_LINE_MARKER_NUM = 2
    BREAKPOINT_MARKER_NUM = 1
    CURRENT_LINE_MARKER_MASK = 0x4
    BREAKPOINT_MARKER_MASK = 0x4
    TYPE_BLANK_WORD = " "

    if utils.is_py2():
        DEFAULT_WORD_CHARS = string.letters + string.digits + '_'
    elif utils.is_py3():
        DEFAULT_WORD_CHARS = string.ascii_letters + string.digits + '_'
            
    def __init__(self, master=None, cnf={}, **kw):
        texteditor.TextCtrl.__init__(self, master, cnf=cnf, **kw)
        self._lang_lexer = None
        #允许绑定所有CodeCtrl类文件控件事件
        self.bindtags(self.bindtags() + ("CodeCtrl",))
        self.UpdateSyntaxTheme()
        #设置单词列表
        self.fixwordbreaks(GetApp())

    def CreatePopupMenu(self):
        texteditor.TextCtrl.CreatePopupMenu(self)
        self._popup_menu.add_separator()
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetFormatMenu().FindMenuItem(consts.ID_COMMENT_LINES),\
                                    handler=self.master.master.GetView().comment_region)
                                    
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetFormatMenu().FindMenuItem(consts.ID_UNCOMMENT_LINES),\
                                    handler=self.master.master.GetView().uncomment_region)

    def DoIndent(self):
        self.AddText(self.GetEOLChar())
        self.EnsureCaretVisible()
        # Need to do a default one for all languges
            
    def GetLangLexer(self):
        if self._lang_lexer is None:
            document = self.master.master.GetView().GetDocument()
            file_ext = document.GetDocumentTemplate().GetDefaultExtension()
            self._lang_lexer = syntax.SyntaxThemeManager().GetLexer(syntax.SyntaxThemeManager().GetLangIdFromExt(file_ext))
        return self._lang_lexer
        
    def SetLangLexer(self,lexer):
        self._lang_lexer = lexer

    def UpdateSyntaxTheme(self):
        self.SetSyntax(syntax.SyntaxThemeManager().SYNTAX_THEMES)
        
    def SetSyntax(self,syntax_options):
        # apply new options
        for tag_name in syntax_options:
            if tag_name == "TEXT":
                self.configure(**syntax_options[tag_name])
            else:
                self.tag_configure(tag_name, **syntax_options[tag_name])

        if "current_line" in syntax_options:
            self.tag_lower("current_line")

        self.tag_raise("sel")
        
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