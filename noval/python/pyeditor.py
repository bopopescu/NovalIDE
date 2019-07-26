# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        pyeditor.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-24
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
import os
from tkinter import messagebox
from noval import _,GetApp,NewId
import noval.editor.code as codeeditor
import string
import keyword
import sys
import codecs
import noval.python.parser.scope as scope
import noval.python.interpreter.interpreter as pythoninterpreter
import noval.python.parser.intellisence as intellisence
import noval.python.parser.nodeast as nodeast
import noval.util.strutils as strutils
from noval.python.parser.utils import CmpMember
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.util.fileutils as fileutils
import noval.python.parser.utils as parserutils
import noval.consts as consts
from noval.util import utils
import noval.python.analyzer as analyzer
import noval.syntax.lang as lang
import noval.menu as tkmenu
import noval.constants as constants
import noval.python.project.viewer as projectviewer
import noval.python.project.runconfig as runconfig
import noval.ui_utils as ui_utils
from noval.python.project.rundocument import *

class PythonDocument(codeeditor.CodeDocument): 

    UTF_8_ENCODING = 0
    GBK_ENCODING = 1
    ANSI_ENCODING = 2
    UNKNOWN_ENCODING = -1
    
    def __init__(self):
        codeeditor.CodeDocument.__init__(self)
        
    def GetRunParameter(self):
        fileToRun = self.GetFilename()
        unprojProj = PythonProjectDocument.GetUnProjectDocument()
        initialArgs = utils.profile_get(unprojProj.GetUnProjectFileKey(fileToRun,"RunArguments"),"")
        python_path = utils.profile_get(unprojProj.GetUnProjectFileKey(fileToRun,"PythonPath"),"")
        startIn = utils.profile_get(unprojProj.GetUnProjectFileKey(fileToRun,"RunStartIn"),"")
        if startIn == '':
            startIn = os.path.dirname(fileToRun)
        env = {}
        #should avoid environment contain unicode string,such as u'xxx'
        if python_path != '':
            env[consts.PYTHON_PATH_NAME] = str(python_path)
        return runconfig.PythonRunconfig(GetApp().GetCurrentInterpreter(),fileToRun,initialArgs,env,startIn)

    def get_coding_spec(self,lines):
        """Return the encoding declaration according to PEP 263.
        Raise LookupError if the encoding is declared but unknown.
        """
        name,_ = strutils.get_python_coding_declare(lines)
        if name is None:
            return None
        # Check whether the encoding is known
        try:
            codecs.lookup(name)
        except LookupError:
            # The standard encoding error does not indicate the encoding
            raise RuntimeError("Unknown encoding %s" % name)
        return name
        
    def DoSave(self):
        codeeditor.CodeDocument.DoSave(self)
        docTemplate = self.GetDocumentTemplate()
        view = self.GetFirstView()
        lines = view.GetCtrl().GetTopLines(consts.ENCODING_DECLARE_LINE_NUM)
        declare_encoding = self.get_coding_spec(lines)
        interpreter = GetApp().GetCurrentInterpreter()
        #when python version is 2,should check the encoding declare if python file contain
        #chinse character,which python3 is not necessary
        is_v2 = False
        if interpreter is None or interpreter.IsV2():
            is_v2 = True
        if is_v2:
            if None == declare_encoding and self.file_encoding != self.ASC_FILE_ENCODING:
                ret = messagebox.askyesno(_("Declare Encoding"),_("Detect your python file contain chinese character,please insert encoding declare.\n\nClick 'Yes' to insert,or 'No' to cancel?"),parent=view.GetFrame())
                if ret == True:
                    if GetApp().InsertEncodingDeclare(view):
                        lines = view.GetCtrl().GetTopLines(consts.ENCODING_DECLARE_LINE_NUM)
                        declare_encoding = self.get_coding_spec(lines)
        if declare_encoding is None:
            #if not decalare encoding,then set file encoding default to ascii encoding
            if is_v2:
                declare_encoding = codeeditor.CodeDocument.DEFAULT_FILE_ENCODING
                if self.IsDocEncodingChanged(declare_encoding):
                    self.file_encoding = declare_encoding
        else:
            if self.IsDocEncodingChanged(declare_encoding):
                self.file_encoding = declare_encoding
        
    def GetDocEncoding(self,encoding):
        lower_encoding = encoding.lower() 
        if lower_encoding == self.UTF_8_FILE_ENCODING or lower_encoding == "utf-8-sig":
            return self.UTF_8_ENCODING
        elif lower_encoding == "gbk" or lower_encoding == "gb2312" \
             or lower_encoding == "gb18030" or lower_encoding == self.ANSI_FILE_ENCODING:
            return self.GBK_ENCODING
        elif lower_encoding == self.ASC_FILE_ENCODING:
            return self.ANSI_ENCODING
        return self.UNKNOWN_ENCODING

    def IsUtf8Doc(self,encoding):
        if encoding.lower().find("utf-8"):
            return True
        return False

    def IsDocEncodingChanged(self,encoding):
        if self.GetDocEncoding(encoding) != self.GetDocEncoding(self.file_encoding):
            return True
        return False

class PythonView(codeeditor.CodeView):

    def __init__(self):
        codeeditor.CodeView.__init__(self)
        self._module_analyzer = analyzer.PythonModuleAnalyzer(self)
        #document checksum to check document is updated
        self._checkSum = -1
        
    @property
    def ModuleAnalyzer(self):
        return self._module_analyzer
        
    @property
    def ModuleScope(self):
        return self._module_analyzer.ModuleScope
        
    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        return PythonCtrl
    
    def GetLangId(self):
        return lang.ID_LANG_PYTHON

    def OnClose(self, deleteWindow = True):
        if self._module_analyzer.IsAnalyzing():
            utils.get_logger().info("document %s is still analyzing ,wait a moment to finish analyze before close",self.GetDocument().GetFilename())
            self._module_analyzer.StopAnalyzing()
            while True:
                if not self._module_analyzer.IsAnalyzing():
                    break
                wx.MilliSleep(250)
                wx.Yield()
            utils.get_logger().info("document %s has been finish analyze,now will close",self.GetDocument().GetFilename())
        status = codeeditor.CodeView.OnClose(self, deleteWindow)
       # wx.CallAfter(self.ClearOutline)  # need CallAfter because when closing the document, it is Activated and then Close, so need to match OnActivateView's CallAfter
        return status
       

    def GetAutoCompleteKeywordList(self, context, hint,line):
        obj = None
        try:
            if context and len(context):
                obj = eval(context, globals(), locals())
        except:
            if not hint or len(hint) == 0:  # context isn't valid, maybe it was the hint
                hint = context
            
        if obj is None:
            kw = keyword.kwlist[:]
            module_scope = self.ModuleScope
            members = []
            if module_scope is not None:
                scope = module_scope.FindScope(line)
                parent = scope
                while parent is not None:
                    if parent.Parent is None:
                        members.extend(parent.GetMembers())
                    else:
                        members.extend(parent.GetMemberList(False))
                    parent = parent.Parent
                kw.extend(members)
                builtin_members = intellisence.IntellisenceManager().GetBuiltinModuleMembers()
                kw.extend(builtin_members)
        else:
            symTbl = dir(obj)
            kw = filter(lambda item: item[0] != '_', symTbl)  # remove local variables and methods
        
        if hint and len(hint):
            lowerHint = hint.lower()
            filterkw = filter(lambda item: item.lower().startswith(lowerHint), kw)  # remove variables and methods that don't match hint
            kw = filterkw

        kw.sort(CmpMember)
        if hint:
            replaceLen = len(hint)
        else:
            replaceLen = 0
        return " ".join(kw), replaceLen

    def OnJumpToFoundLine(self, event):
        messageService = wx.GetApp().GetService(MessageService.MessageService)
        lineText, pos = messageService.GetView().GetCurrLine()
        
        lineEnd = lineText.find(".py:")
        if lineEnd == -1:
            return

        lineStart = lineEnd + len(".py:")
        lineEnd = lineText.find(":", lineStart)
        lineNum = int(lineText[lineStart:lineEnd])

        filename = lineText[0:lineStart - 1]

        foundView = None
        openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if openDoc.GetFilename() == filename:
                foundView = openDoc.GetFirstView()
                break

        if not foundView:
            doc = wx.GetApp().GetDocumentManager().CreateDocument(filename, wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
            foundView = doc.GetFirstView()

        if foundView:
            foundView.GetFrame().SetFocus()
            foundView.Activate()
            foundView.GotoLine(lineNum)
            startPos = foundView.PositionFromLine(lineNum)
            endPos = foundView.GetLineEndPosition(lineNum)
            # wxBug:  Need to select in reverse order, (end, start) to put cursor at head of line so positioning is correct
            #         Also, if we use the correct positioning order (start, end), somehow, when we open a edit window for the first
            #         time, we don't see the selection, it is scrolled off screen
            foundView.SetSelection(endPos, startPos)
            wx.GetApp().GetService(OutlineService.OutlineService).LoadOutline(foundView, position=startPos)

    def LoadOutLine(self, outlineView,force=False,lineNum=-1):
        callback_view = outlineView.GetCallbackView()
        newCheckSum = self.GenCheckSum()
        if not force:
            #文件长度改变,重新解析并生成语法树
            force = self._checkSum != newCheckSum
            if callback_view and callback_view is self:
                if self._checkSum == newCheckSum:
                    utils.get_logger().info("document %s check sum is same not will not analyze again",self.GetDocument().GetFilename())
                    if lineNum > -1:
                        outlineView.SyncToPosition(self,lineNum)
                    return False
        self._checkSum = newCheckSum
        document = self.GetDocument()
        if not document:
            return True
        self.GetCtrl().after(1,self._module_analyzer.AnalyzeModuleSynchronizeTree,callback_view,outlineView,force,lineNum)
        return True
        
    def IsUnitTestEnable(self):
        return True
        

    def OnCommentLines(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetCtrl().GetLine(lineNo)
            if (len(lineText) > 1 and lineText[0] == '#') or (len(lineText) > 2 and lineText[:2] == '##'):
                newText = newText + lineText
            else:
                newText = newText + "##" + lineText
        self._ReplaceSelectedLines(newText)

    def OnUncommentLines(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetCtrl().GetLine(lineNo)
            if len(lineText) >= 2 and lineText[:2] == "##":
                lineText = lineText[2:]
            elif len(lineText) >= 1 and lineText[:1] == "#":
                lineText = lineText[1:]
            newText = newText + lineText
        self._ReplaceSelectedLines(newText)
        

    def UpdateUI(self, command_id):
        if command_id in [constants.ID_INSERT_DECLARE_ENCODING, constants.ID_UNITTEST,constants.ID_RUN,constants.ID_DEBUG,constants.ID_SET_EXCEPTION_BREAKPOINT,constants.ID_STEP_INTO,constants.ID_STEP_NEXT,constants.ID_RUN_LAST,\
                    constants.ID_CHECK_SYNTAX,constants.ID_SET_PARAMETER_ENVIRONMENT,constants.ID_DEBUG_LAST,constants.ID_START_WITHOUT_DEBUG]:
            return True
        elif command_id == constants.ID_GOTO_DEFINITION:
            return self.GetCtrl().IsCaretLocateInWord()
        return codeeditor.CodeView.UpdateUI(self,command_id)

class PythonCtrl(codeeditor.CodeCtrl):
    TYPE_POINT_WORD = "."
    TYPE_IMPORT_WORD = "import"
    TYPE_FROM_WORD = "from"

    def __init__(self, master=None, cnf={}, **kw):
        codeeditor.CodeCtrl.__init__(self, master, cnf=cnf, **kw)

    def CreatePopupMenu(self):
        codeeditor.CodeCtrl.CreatePopupMenu(self)
        self._popup_menu.add_separator()

        menu_item = tkmenu.MenuItem(constants.ID_OUTLINE_SYNCTREE,_("Find in Outline View"),None,None,None)
        self._popup_menu.AppendMenuItem(menu_item,handler=self.SyncOutline)
        
        menuBar = GetApp().Menubar
        menu_item = menuBar.FindItemById(constants.ID_GOTO_DEFINITION)
        self._popup_menu.AppendMenuItem(menu_item,handler=self.GotoDefinition)

        item = tkmenu.MenuItem(constants.ID_EXECUTE_CODE,_("&Execute Code in interpreter"), None,None,self.HasSelection)
        self._popup_menu.AppendMenuItem(item,handler=self.ExecCode)
        
        
        menu_item = menuBar.FindItemById(constants.ID_RUN)
        self._popup_menu.AppendMenuItem(menu_item,handler=self.RunScript)
        
        debug_menu = tkmenu.PopupMenu()
        self._popup_menu.AppendMenu(NewId(),_("Debug"),debug_menu)
        menu_item = menuBar.FindItemById(constants.ID_DEBUG)
        debug_menu.AppendMenuItem(menu_item,handler=self.DebugRunScript)
        
        item = tkmenu.MenuItem(constants.ID_BREAK_INTO_DEBUGGER,_("&Break into Debugger"), None,None,None)
        debug_menu.AppendMenuItem(item,handler=self.BreakintoDebugger)
        
##        if debugger.DebuggerService.BaseDebuggerUI.DebuggerRunning():
##            
##            item = wx.MenuItem(menu,constants.ID_QUICK_ADD_WATCH,_("&Quick add Watch"), kind = wx.ITEM_NORMAL)
##            item.SetBitmap(debugger.Watchs.getQuickAddWatchBitmap())
##            menu.AppendItem(item)
##            wx.EVT_MENU(self, constants.ID_QUICK_ADD_WATCH, self.QuickAddWatch)
##            
##            item = wx.MenuItem(menu,constants.ID_ADD_WATCH,_("&Add Watch"), kind = wx.ITEM_NORMAL)
##            item.SetBitmap(debugger.Watchs.getAddWatchBitmap())
##            menu.AppendItem(item)
##            wx.EVT_MENU(self, constants.ID_ADD_WATCH, self.AddWatch)
##            
##            item = wx.MenuItem(menu,constants.ID_ADD_TO_WATCH,_("&Add to Watch"), kind = wx.ITEM_NORMAL)
##            item.SetBitmap(debugger.Watchs.getAddtoWatchBitmap())
##            menu.AppendItem(item)
##            wx.EVT_MENU(self, constants.ID_ADD_TO_WATCH, self.AddtoWatch)
            
    def ExecCode(self):
        first,last = self.get_selection()
        code = self.get(first,last)
        GetApp().MainFrame.ShowView(consts.PYTHON_INTERPRETER_VIEW_NAME,toogle_visibility_flag=True)
        python_interpreter_view = GetApp().MainFrame.GetCommonView(consts.PYTHON_INTERPRETER_VIEW_NAME)
        python_interpreter_view.runsource(code)
        
    def SyncOutline(self):
        line_no = self.GetCurrentLine()
        #获取文本控件对应的视图需要取2次master
        GetApp().MainFrame.GetOutlineView().SyncToPosition(self.master.master.GetView(),line_no)

    def DebugRunScript(self):
        view = GetApp().GetDocumentManager().GetCurrentView()
        GetApp().GetDebugger().RunWithoutDebug(view.GetDocument().GetFilename())
        
    def QuickAddWatch(self):
        if self.HasSelection():
            text = self.GetSelectedText()
            watch = debugger.Watchs.Watch(text,text)
            wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).AddWatch(watch,True)
        else:
            if self.IsCaretLocateInWord():
                pos = self.GetCurrentPos()
                text = self.GetTypeWord(pos)
                watch = debugger.Watchs.Watch(text,text)
                wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).AddWatch(watch,True)
            else:
                wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).AddWatch(None,True)
        
    def AddWatch(self,event):
        if self.HasSelection():
            text = self.GetSelectedText()
            watch = debugger.Watchs.Watch(text,text)
            wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).AddWatch(watch)
        else:
            if self.IsCaretLocateInWord():
                pos = self.GetCurrentPos()
                text = self.GetTypeWord(pos)
                watch = debugger.Watchs.Watch(text,text)
                wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).AddWatch(watch)
            else:
                wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).AddWatch(None)

    def AddtoWatch(self,event):
        
        if self.HasSelection():
            text = self.GetSelectedText()
            watch = debugger.Watchs.Watch(text,text)
            wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).AddtoWatch(watch)
        else:
            if self.IsCaretLocateInWord():
                pos = self.GetCurrentPos()
                text = self.GetTypeWord(pos)
                watch = debugger.Watchs.Watch(text,text)
                wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).AddtoWatch(watch)
        
    @ui_utils.no_implemented_yet
    def BreakintoDebugger(self):
        pass
       # view = wx.GetApp().GetDocumentManager().GetCurrentView()
        #wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).BreakIntoDebugger(view.GetDocument().GetFilename())
    
    def RunScript(self):
        view = GetApp().GetDocumentManager().GetCurrentView()
        GetApp().GetDebugger().Run(view.GetDocument().GetFilename())

    def GetFontAndColorFromConfig(self):
        return CodeEditor.CodeCtrl.GetFontAndColorFromConfig(self, configPrefix = "Python")

    def OnUpdateUI(self, evt):
        braces = self.GetMatchingBraces()
        
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()
        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in braces and styleBefore == wx.stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)
            if charAfter and chr(charAfter) in braces and styleAfter == wx.stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)

        evt.Skip()


    def DoIndent(self):
        (text, caretPos) = self.GetCurLine()

        self._tokenizerChars = {}  # This is really too much, need to find something more like a C array
        for i in range(len(text)):
            self._tokenizerChars[i] = 0
        ctext = StringIO.StringIO(text)
        try:
            tokenize.tokenize(ctext.readline, self)
        except:
            pass

        # Left in for debugging purposes:
        #for i in range(len(text)):
        #    print i, text[i], self._tokenizerChars[i]
        eol_char = self.GetEOLChar()
        if caretPos == 0 or len(string.strip(text)) == 0:  # At beginning of line or within an empty line
            self.AddText(eol_char)
        else:
            doExtraIndent = False
            brackets = False
            commentStart = -1
            if caretPos > 1:
                startParenCount = 0
                endParenCount = 0
                startSquareBracketCount = 0
                endSquareBracketCount = 0
                startCurlyBracketCount = 0
                endCurlyBracketCount = 0
                startQuoteCount = 0
                endQuoteCount = 0
                for i in range(caretPos - 1, -1, -1): # Go through each character before the caret
                    if i >= len(text): # Sometimes the caret is at the end of the text if there is no LF
                        continue
                    if self._tokenizerChars[i] == 1:
                        continue
                    elif self._tokenizerChars[i] == 2:
                        startQuoteCount = startQuoteCount + 1
                    elif self._tokenizerChars[i] == 3:
                        endQuoteCount = endQuoteCount + 1
                    elif text[i] == '(': # Would be nice to use a dict for this, but the code is much more readable this way
                        startParenCount = startParenCount + 1
                    elif text[i] == ')':
                        endParenCount = endParenCount + 1
                    elif text[i] == "[":
                        startSquareBracketCount = startSquareBracketCount + 1
                    elif text[i] == "]":
                        endSquareBracketCount = endSquareBracketCount + 1
                    elif text[i] == "{":
                        startCurlyBracketCount = startCurlyBracketCount + 1
                    elif text[i] == "}":
                        endCurlyBracketCount = endCurlyBracketCount + 1
                    elif text[i] == "#":
                        commentStart = i
                        break
                    if startQuoteCount > endQuoteCount or startParenCount > endParenCount or startSquareBracketCount > endSquareBracketCount or startCurlyBracketCount > endCurlyBracketCount:
                        if i + 1 >= caretPos:  # Caret is right at the open paren, so just do indent as if colon was there
                            doExtraIndent = True
                            break
                        else:
                            spaces = " " * (i + 1)
                            brackets = True
                            break
            if not brackets:
                spaces = text[0:len(text) - len(string.lstrip(text))]
                if caretPos < len(spaces):  # If within the opening spaces of a line
                    spaces = spaces[:caretPos]

                # strip comment off
                if commentStart != -1:
                    text = text[0:commentStart]

                textNoTrailingSpaces = text[0:caretPos].rstrip()
                if doExtraIndent or len(textNoTrailingSpaces) and textNoTrailingSpaces[-1] == ':':
                    spaces = spaces + ' ' * self.GetIndent()
            self.AddText(eol_char + spaces)
        self.EnsureCaretVisible()
                
    def IsImportType(self,start_pos):
        line_start_pos = self.PositionFromLine(self.LineFromPosition(start_pos))
        at = self.GetCharAt(start_pos)
        while chr(at) == self.TYPE_BLANK_WORD:
            start_pos -= 1
            at = self.GetCharAt(start_pos)
        if start_pos <= line_start_pos:
            return False
        word = self.GetTypeWord(start_pos)
        return True if word == self.TYPE_IMPORT_WORD else False
        
    def IsFromType(self,start_pos):
        line_start_pos = self.PositionFromLine(self.LineFromPosition(start_pos))
        at = self.GetCharAt(start_pos)
        while chr(at) == self.TYPE_BLANK_WORD:
            start_pos -= 1
            at = self.GetCharAt(start_pos)
        if start_pos <= line_start_pos:
            return False
        word = self.GetTypeWord(start_pos)
        return True if word == self.TYPE_FROM_WORD else False
        
    def IsFromModuleType(self,start_pos):
        line_start_pos = self.PositionFromLine(self.LineFromPosition(start_pos))
        at = self.GetCharAt(start_pos)
        while chr(at) == self.TYPE_BLANK_WORD:
            start_pos -= 1
            at = self.GetCharAt(start_pos)
        if start_pos <= line_start_pos:
            return False
        word = self.GetTypeWord(start_pos)
        start_pos -= len(word)
        start_pos -= 1
        at = self.GetCharAt(start_pos)
        while chr(at) == self.TYPE_BLANK_WORD:
            start_pos -= 1
            at = self.GetCharAt(start_pos)
        if start_pos <= line_start_pos:
            return False
        word = self.GetTypeWord(start_pos)
        return True if word == self.TYPE_FROM_WORD else False

    def IsFromImportType(self,start_pos):
        line_start_pos = self.PositionFromLine(self.LineFromPosition(start_pos))
        at = self.GetCharAt(start_pos)
        while chr(at) == self.TYPE_BLANK_WORD:
            start_pos -= 1
            at = self.GetCharAt(start_pos)
        if start_pos <= line_start_pos:
            return False,''
        word = self.GetTypeWord(start_pos)
        if word == self.TYPE_IMPORT_WORD:
            start_pos -= len(self.TYPE_IMPORT_WORD)
            start_pos -= 1
            at = self.GetCharAt(start_pos)
            while chr(at) == self.TYPE_BLANK_WORD:
                start_pos -= 1
                at = self.GetCharAt(start_pos)
            if start_pos <= line_start_pos:
                return False,''
            from_word = self.GetTypeWord(start_pos)
            start_pos -= len(from_word)
            start_pos -= 1
            at = self.GetCharAt(start_pos)
            while chr(at) == self.TYPE_BLANK_WORD:
                start_pos -= 1
                at = self.GetCharAt(start_pos)
            if start_pos <= line_start_pos:
                return False,''
            word = self.GetTypeWord(start_pos)
            return True if word == self.TYPE_FROM_WORD else False,from_word
        return False,''
                
    def OnChar(self,event):
        if self.CallTipActive():
            self.CallTipCancel()
        key = event.GetKeyCode()
        pos = self.GetCurrentPos()
        # Tips
        if key == ord("("):
            #delete selected text
            if self.GetSelectedText():
                self.ReplaceSelection("")
            self.AddText("(")
            self.GetArgTip(pos)
        elif key == ord(self.TYPE_POINT_WORD):
            #delete selected text
            if self.GetSelectedText():
                self.ReplaceSelection("")
            self.AddText(self.TYPE_POINT_WORD)
            self.ListMembers(pos)
        elif key == ord(self.TYPE_BLANK_WORD):
            if self.GetSelectedText():
                self.ReplaceSelection("")
            self.AddText(self.TYPE_BLANK_WORD)
            is_from_import_type,name = self.IsFromImportType(pos)
            if is_from_import_type:
                member_list = intellisence.IntellisenceManager().GetMemberList(name)
                if member_list == []:
                    return
                member_list.insert(0,"*")
                self.AutoCompShow(0, string.join(member_list))
            elif self.IsImportType(pos) or self.IsFromType(pos):
                import_list = intellisence.IntellisenceManager().GetImportList()
                import_list.extend(self.GetCurdirImports())
                import_list.sort(parserutils.CmpMember)
                if import_list == []:
                    return
                self.AutoCompShow(0, string.join(import_list))
            elif self.IsFromModuleType(pos):
                self.AutoCompShow(0, string.join([self.TYPE_IMPORT_WORD]))
        else:
            event.Skip()
            

    def GetCurdirImports(self):
        cur_project = wx.GetApp().GetService(project.ProjectEditor.ProjectService).GetView().GetDocument()
        if cur_project is None:
            return []
        document = wx.GetApp().GetDocumentManager().GetCurrentView().GetDocument()
        if document.IsNewDocument:
            return []
        file_path_name = document.GetFilename()
        cur_file_name = os.path.basename(file_path_name)
        dir_path = os.path.dirname(file_path_name)
        imports = []
        for file_name in os.listdir(dir_path):
            if parserutils.ComparePath(cur_file_name,file_name) or not fileutils.is_python_file(file_name) \
                    or file_name.find(" ") != -1:
                continue
            file_path_name = os.path.join(dir_path,file_name)
            if os.path.isdir(file_path_name) and not parser.is_package_dir(file_path_name):
                continue
            imports.append(os.path.splitext(file_name)[0])
        return imports
            
    def GetArgTip(self,pos):
        text = self.GetTypeWord(pos)
        line = self.LineFromPosition(pos)
        module_scope = wx.GetApp().GetDocumentManager().GetCurrentView().ModuleScope
        if module_scope is None:
            return
        scope = module_scope.FindScope(line+1)
        scope_found = scope.FindDefinitionMember(text)
        tip = ''
        if None != scope_found:
            if scope_found.Parent is not None and isinstance(scope_found.Node,nodeast.ImportNode):
                tip = scope_found.GetImportMemberArgTip(text)
            else:
                tip = scope_found.GetArgTip()
        if tip == '':
            return
        self.CallTipShow(pos,tip)    

    def IsListMemberFlag(self,pos):
        at = self.GetCharAt(pos)
        if chr(at) != self.TYPE_POINT_WORD:
            return False
        return True

    def ListMembers(self,pos):
        text = self.GetTypeWord(pos)
        line = self.LineFromPosition(pos)
        module_scope = wx.GetApp().GetDocumentManager().GetCurrentView().ModuleScope
        if module_scope is None:
            return
        scope = module_scope.FindScope(line+1)
        scope_found = scope.FindDefinitionScope(text)
        member_list = []
        if None != scope_found:
            if scope_found.Parent is not None and isinstance(scope_found.Node,nodeast.ImportNode):
                member_list = scope_found.GetImportMemberList(text)
            else:
                if scope.IsClassMethodScope() and scope.Parent == scope_found:
                    member_list = scope_found.GetClassMemberList()
                else:
                    member_list = scope_found.GetMemberList()
        if member_list == []:
            return
        self.AutoCompSetIgnoreCase(True)
        self.AutoCompShow(0, string.join(member_list))

    def IsCaretLocateInWord(self,pos=None):
        if pos == None:
            line,col = self.GetCurrentLineColumn()
        else:
            line,col = pos
        line_text = self.GetLineText(line).strip()
        if line_text == "":
            return False
        if line_text[0] == '#':
            return False
        at = self.GetCharAt(line,col)
        if at == "":
            return False
        return True if at in self.DEFAULT_WORD_CHARS else False

    def GotoDefinition(self):
        
        def NotFoundDefinition(txt):
            messagebox.showwarning(_("Goto Definition"),_("Cannot find definition") + "\"" + txt + "\"",parent = self.master)
            
        line,col= self.GetCurrentLineColumn()
        text = self.GetTypeWord(line,col)
        open_new_doc = False
        module_scope = GetApp().GetDocumentManager().GetCurrentView().ModuleScope
        if module_scope is None:
            scope_found = None
        else:
            scope = module_scope.FindScope(line)
            scope_found = scope.FindDefinitionMember(text)
        if scope_found is None:
            NotFoundDefinition(text)
        else:
            if scope_found.Parent is None:
                GetApp().GotoView(scope_found.Module.Path,0)
            else:
                open_new_doc = (scope_found.Root != scope.Root)
                if not open_new_doc:
                    doc_view = GetApp().GetDocumentManager().GetCurrentView()
                    doc_view.GotoPos(scope_found.Node.Line , scope_found.Node.Col)
                else:
                    #找到python内建函数,无法定位到行
                    if -1 == scope_found.Node.Line:
                        NotFoundDefinition(text)
                        return
                    GetApp().GotoView(scope_found.Root.Module.Path,scope_found.Node.Line,scope_found.Node.Col)

    def GetTypeWord(self,line,col):
        line,word_col = self.get_line_col(self.index("insert wordstart"))
        word_end = self.index("insert wordend")
        at = self.GetCharAt(line,word_col)
        rem_chars = self.DEFAULT_WORD_CHARS + self.TYPE_POINT_WORD
        while at in rem_chars:
            if word_col < 0:
                break
            if at == self.TYPE_POINT_WORD:
                word_col -=1
                at = self.GetCharAt(line,word_col)
                while at == self.TYPE_BLANK_WORD:
                    word_col -=1
                    at = self.GetCharAt(line,word_col)
            else:
                word_col -=1
                at = self.GetCharAt(line,word_col)    
        word_start = "%d.%d" % (line,word_col+1)
        text = self.get(word_start,word_end)
        return text

