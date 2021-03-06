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
import intellisence
import nodeast
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
import noval.python.pyutils as pyutils
import io as StringIO  # For indent
import noval.python.debugger.debugger as pythondebugger
import noval.python.debugger.watchs as watchs
import noval.util.compat as compat
from noval.util.command import ToplevelCommand

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
        
    def DetectFileEncoding(self,filepath):
        '''
            检查python文件的编码
        '''
        encoding = None
        try:
            #必须以rb方式读取文件,可以消除编码影响
            with open(filepath,'rb') as f:
                coding_declare_lines = []
                for i,line in enumerate(f):
                    if utils.is_py3_plus():
                        line = compat.ensure_string(line)
                    #编码声明只读取前2行
                    if i <=2:
                        coding_declare_lines.append(line)
                    else:
                        break
                #先获取python文件声明的编码
                encoding = self.get_coding_spec(coding_declare_lines)
        except Exception as e:
            messagebox.showerror(_("Error"),str(e))
        #如果没有声明编码则检测文件的编码
        if encoding is None:
            return codeeditor.CodeDocument.DetectFileEncoding(self,filepath)
        else:
            return encoding

class PythonView(codeeditor.CodeView):

    def __init__(self):
        codeeditor.CodeView.__init__(self)
        self._module_analyzer = analyzer.PythonModuleAnalyzer(self)
        #document checksum to check document is updated
        self._checkSum = -1
        
    def OnCreate(self, doc, flags):
        if not codeeditor.CodeView.OnCreate(self,doc,flags):
            return False
        self.bp_margin = self._text_frame.bp_margin
        #单击左边空白框添加断点
        self.bp_margin.bind("<Button-1>", self.on_bp_click)
        return True
        
    def OnUpdate(self, sender = None, hint = None):
        if codeeditor.CodeView.OnUpdate(self, sender, hint):
            return
        #加载文档断点信息
        self.SetCurrentBreakpointMarkers()
        
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
       
    def GetAutoCompleteKeywords(self,line):
        #先获取默认的公用关键字列表
        default_keywords = codeeditor.CodeView.GetAutoCompleteDefaultKeywords(self)
        members = []
        kw = default_keywords
        #再获取语法分析当前范围的单词列表
        if self.ModuleScope is not None:
            #查找当前行所在的范围
            scope = self.ModuleScope.FindScope(line)
            is_cls_scope = scope.IsClassMethodScope()
            is_self_scope = scope.IsMethodScope()
            parent = scope
            while parent is not None:
                if parent.Parent is None:
                    members.extend(parent.GetMembers())
                else:
                    if is_cls_scope and parent == scope.Parent:
                        member_list = ['cls']
                    elif is_self_scope and parent == scope.Parent:
                        member_list = ['self']
                    else:
                        member_list = parent.GetMemberList()
                    members.extend(member_list)
                parent = parent.Parent
            kw.extend(members)
        return kw

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

    def UpdateUI(self, command_id):
        if command_id in [constants.ID_INSERT_DECLARE_ENCODING, constants.ID_UNITTEST,constants.ID_RUN,constants.ID_DEBUG,constants.ID_SET_EXCEPTION_BREAKPOINT,constants.ID_STEP_INTO,constants.ID_STEP_NEXT,constants.ID_RUN_LAST,\
                    constants.ID_CHECK_SYNTAX,constants.ID_SET_PARAMETER_ENVIRONMENT,constants.ID_DEBUG_LAST,constants.ID_START_WITHOUT_DEBUG,constants.ID_TOGGLE_BREAKPOINT]:
            return True
        elif command_id == constants.ID_GOTO_DEFINITION:
            return self.GetCtrl().IsCaretLocateInWord()
        return codeeditor.CodeView.UpdateUI(self,command_id)
        
    def GotoDefinition(self):
        self.GetCtrl().GotoDefinition()
        
    def on_bp_click(self, event=None):
        linepos = int(self.bp_margin.index("@%s,%s" % (event.x, event.y)).split(".")[0])
        self.ToogleBreakpoint(linepos)
            
    def DeleteBpMark(self,lineno,delete_master_bp=True,notify=True):
        try:
            self.bp_margin.image_cget("%d.0"%lineno,option="name")
            self.bp_margin.config(state="normal")
            self.bp_margin.delete("%d.0"%lineno,"%d.1"%lineno)
            self.bp_margin.config(state="disabled")
        except:
            return False
        #删除断点视图中断点数据
        if delete_master_bp:
            GetApp().MainFrame.GetView(consts.BREAKPOINTS_TAB_NAME).ToogleBreakpoint(str(lineno),self.GetDocument().GetFilename(),delete=True,notify=notify)
        return True
        
    def SetCurrentBreakpointMarkers(self):
        breakpoints = GetApp().MainFrame.GetView(consts.BREAKPOINTS_TAB_NAME).GetMasterBreakpointDict()
        for linenum in breakpoints.get(self.GetDocument().GetFilename(),[]):
            self.DeleteBpMark(linenum,delete_master_bp=False)
            self.bp_margin.image_create("%d.0"%linenum,image=self._text_frame.bp_bmp)

    def ToogleBreakpoint(self,lineno):
        '''
            设置断点,断点存在时删除断点,否则添加断点
        '''
        try:
            line_text = self.GetCtrl().GetLineText(lineno).strip()
            #空行或者注释行不能添加断点
            if not self.DeleteBpMark(lineno) and line_text and not line_text.startswith('#'):
                self.bp_margin.image_create("%d.0"%lineno,image=self._text_frame.bp_bmp)
                #往断点视图中添加断点数据
                GetApp().MainFrame.GetView(consts.BREAKPOINTS_TAB_NAME).ToogleBreakpoint(lineno,self.GetDocument().GetFilename())
        except tk.TclError:
            utils.exception("on_bp_click")
            
    def GetAutoCompleteKeywordList(self, context, hint,line):
        line,col = self.GetCtrl().GetCurrentPos()
        last_char = self.GetCtrl().GetCharAt(line,col-1)
        word = self.GetCtrl().GetTypeWord(line,col-1)
        if (not word and not last_char) or (word and word == context):
            return codeeditor.CodeView.GetAutoCompleteKeywordList(self,context,hint,line)
        else:
            return self.GetCtrl().GetAutoCompletions(context,hint,last_char)

    def GetAutoCompleteHint(self):
        """
            如果输入内容是abc则返回abc,abc
            如果输入内容是os.path.j,则返回os.path,j
        """
        line,col = self.GetCtrl().GetCurrentPos()
        if line == 0 and col == 0:
            return None, None
        if self.GetCtrl().GetCharAt(line,col) == PythonCtrl.TYPE_POINT_WORD:
            col = col - 1
            hint = None
        else:
            hint = ''
            
        validLetters = self.GetCtrl().DEFAULT_WORD_CHARS + PythonCtrl.TYPE_POINT_WORD
        word = ''
        while (True):
            col = col - 1
            if col < 0:
                break
            char = self.GetCtrl().GetCharAt(line,col)
            if char not in validLetters:
                break
            word = char + word
            
        context = word
        
        if hint is not None:            
            lastDot = word.rfind(PythonCtrl.TYPE_POINT_WORD)
            if lastDot != -1:
                context = word[0:lastDot]
                hint = word[lastDot+1:]
            else:
                hint = word
        #自动完成根据context来弹出列表框内容,hint表示初始选中以hint开头的内容
        return context, hint
            

class PythonCtrl(codeeditor.CodeCtrl):
    TYPE_POINT_WORD = "."
    TYPE_IMPORT_WORD = "import"
    TYPE_FROM_WORD = "from"

    def __init__(self, master=None, cnf={}, **kw):
        codeeditor.CodeCtrl.__init__(self, master, cnf=cnf, **kw)
        #鼠标放在文本上方移动,显示文本的提示文档信息
        self.tag_bind("motion", "<Motion>", self.OnDwellStart)
        
    def OnDwellStart(self,event):
        #是否启用智能提示以及是否鼠标悬停显示文档提示
        if not utils.profile_get_int("ShowDocumentTips", True):
            return
        mouse_index = self.index("@%d,%d" % (event.x, event.y))
        pos = self.get_line_col(mouse_index)
        line,col = pos
        #先隐藏提示信息
        self.CallTipHide()
        if col >= 0 and self.IsCaretLocateInWord(pos):
            dwellword = self.GetTypeWord(line,col)
            if not dwellword:
                return
            doc_view = GetApp().GetDocumentManager().GetCurrentView()
            if not isinstance(doc_view,PythonView):
                return
            #调试器运行时是否鼠标悬停时显示内存变量值
            if pythondebugger.BaseDebuggerUI.DebuggerRunning() and utils.profile_get_int("ShowTipValueWhenDebugging",True):
                if not GetApp().GetDebugger()._debugger_ui._toolEnabled:
                    return
                watch_obj = watchs.Watch.CreateWatch(dwellword,dwellword)
                nodeList = GetApp().GetDebugger()._debugger_ui.framesTab.stackFrameTab.GetWatchList(watch_obj)
                if len(nodeList) == 1:
                    watchValue = nodeList[0].childNodes[0].getAttribute("value")
                    watchType = nodeList[0].childNodes[0].getAttribute("type")
                    #不显示未知类型的值
                    if watchType != consts.DEBUG_UNKNOWN_VALUE_TYPE:
                        self.CallTipShow(pos, dwellword + ":" + watchValue)
            else:
                module_scope = doc_view.ModuleScope
                scope_founds = []
                if module_scope is not None:
                    scope = module_scope.FindScope(line)
                    scope_founds = scope.GetDefinitions(dwellword)
                if scope_founds:
                    scope_found = scope_founds[0]
                    doc = scope_found.GetDoc()
                    if doc is not None:
                        self.CallTipShow(pos, doc)

    def CreatePopupMenu(self):
        codeeditor.CodeCtrl.CreatePopupMenu(self)
        menuBar = GetApp().Menubar
        
        menu_item = menuBar.FindItemById(constants.ID_TOGGLE_BREAKPOINT)
        self._popup_menu.AppendMenuItem(menu_item,handler=self.ToogleBreakpoint)
        self._popup_menu.add_separator()

        menu_item = tkmenu.MenuItem(constants.ID_OUTLINE_SYNCTREE,_("Find in Outline View"),None,None,None)
        self._popup_menu.AppendMenuItem(menu_item,handler=self.SyncOutline)
        
        
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
        
        if pythondebugger.BaseDebuggerUI.DebuggerRunning():
            
            item = tkmenu.MenuItem(constants.ID_QUICK_ADD_WATCH,_("&Quick add Watch"), None,watchs.getQuickAddWatchBitmap(),None)
            self._popup_menu.AppendMenuItem(item,handler=self.QuickAddWatch)
            
            item = tkmenu.MenuItem(constants.ID_ADD_WATCH,_("&Add Watch"), None,watchs.getAddWatchBitmap(),None)
            self._popup_menu.AppendMenuItem(item,handler=self.AddWatch)
            
            item = tkmenu.MenuItem(constants.ID_ADD_TO_WATCH,_("&Add to Watch"), None,watchs.getAddtoWatchBitmap(),None)
            self._popup_menu.AppendMenuItem(item,handler=self.AddtoWatch)
            
    def ExecCode(self):
        first,last = self.get_selection()
        code = self.get(first,last)
        GetApp().MainFrame.ShowView(consts.PYTHON_INTERPRETER_VIEW_NAME,toogle_visibility_flag=True)
        python_interpreter_view = GetApp().MainFrame.GetCommonView(consts.PYTHON_INTERPRETER_VIEW_NAME)
        python_interpreter_view.Runner.send_command(ToplevelCommand("execute_source", source=code))
        
    def ToogleBreakpoint(self):
        line_no = self.GetCurrentLine()
        GetApp().GetDocumentManager().GetCurrentView().ToogleBreakpoint(line_no)
        
    def SyncOutline(self):
        line_no = self.GetCurrentLine()
        #获取文本控件对应的视图需要取2次master
        GetApp().MainFrame.GetOutlineView(show=True).SyncToPosition(self.master.master.GetView(),line_no)

    def DebugRunScript(self):
        view = GetApp().GetDocumentManager().GetCurrentView()
        GetApp().GetDebugger().RunWithoutDebug(view.GetDocument().GetFilename())
        
    def QuickAddWatch(self):
        '''
            快速添加监视,弹出监视对话框,监视的名称和表达式初始一样
        '''
        self.AddWatchText(quick_add=True)
        
    def AddWatch(self):
        '''
            添加监视,弹出监视对话框,监视的名称和表达式初始不一样
        '''
        self.AddWatchText()

    def AddtoWatch(self):
        '''
            直接添加监视,不弹出监视对话框
        '''
        self.AddWatchText(add_to=True)
                
    def AddWatchText(self,quick_add=False,add_to=False):
        text = ""
        if self.HasSelection():
            text = self.GetSelectionText()
        else:
            if self.IsCaretLocateInWord():
                line,col= self.GetCurrentLineColumn()
                text = self.GetTypeWord(line,col-1)
        if not add_to:
           GetApp().GetDebugger().AddWatchText(text,quick_add)
        elif add_to and text:
            GetApp().GetDebugger().AddtoWatchText(text)

    def BreakintoDebugger(self):
        view = GetApp().GetDocumentManager().GetCurrentView()
        GetApp().GetDebugger().GetCurrentProject().BreakintoDebugger(view.GetDocument().GetFilename())
    
    def RunScript(self):
        view = GetApp().GetDocumentManager().GetCurrentView()
        GetApp().GetDebugger().Runfile(view.GetDocument().GetFilename())

    def GetFontAndColorFromConfig(self):
        return CodeEditor.CodeCtrl.GetFontAndColorFromConfig(self, configPrefix = "Python")

    def DoIndent(self):
        text = self.GetLineText(self.GetCurrentLine())
        caretPos = self.GetCurrentColumn()
        self._tokenizerChars = {}  # This is really too much, need to find something more like a C array
        for i in range(len(text)):
            self._tokenizerChars[i] = 0
        ctext = StringIO.StringIO(text)
        try:
            tokenize.tokenize(ctext.readline, self)
        except:
            pass
        eol_char = "\n"
        if caretPos == 0 or len(text.strip()) == 0:  # At beginning of line or within an empty line
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
                spaces = text[0:len(text) - len(text.lstrip())]
                if caretPos < len(spaces):  # If within the opening spaces of a line
                    spaces = spaces[:caretPos]

                # strip comment off
                if commentStart != -1:
                    text = text[0:commentStart]

                textNoTrailingSpaces = text[0:caretPos].rstrip()
                if doExtraIndent or len(textNoTrailingSpaces) and textNoTrailingSpaces[-1] == ':':
                    spaces = spaces + ' ' * self.GetIndent()
            self.AddText(eol_char + spaces)
        self.see("insert")
                
    def IsImportType(self,pos):
        '''
            用户是否输入from关键字
        '''
        return self.IsKeywordBeforePos(pos,self.TYPE_IMPORT_WORD)[0]

    def IsKeywordBeforePos(self,pos,keyword):
        '''
            判断某个位置之前是否存在from或者import等关键字
        '''
        line,col = pos
        at = self.GetCharAt(line,col)
        #忽略所有空格 
        while at == self.TYPE_BLANK_WORD:
            col -= 1
            at = self.GetCharAt(line,col)
        if col <= 0:
            return False,None
        word = self.GetTypeWord(line,col)
        return word == keyword,(line,col)
        
    def IsFromType(self,pos):
        '''
            用户是否输入import关键字
        '''
        return self.IsKeywordBeforePos(pos,self.TYPE_FROM_WORD)[0]
        
    def IsFromplusType(self,pos):
        '''
            用户是否输入from xxx表达式
        '''
        line,col = pos
        
        at = self.GetCharAt(line,col)
        #忽略所有空格 
        while at == self.TYPE_BLANK_WORD:
            col -= 1
            at = self.GetCharAt(line,col)
        if col <= 0:
            return False
        
        word = self.GetTypeWord(line,col)
        col -= len(word)
        col -= 1
        pos = line,col
        return self.IsKeywordBeforePos(pos,self.TYPE_FROM_WORD)[0]

    def IsFromImportType(self,pos):
        '''
            from xxx import ....
        '''
        ret,pos = self.IsKeywordBeforePos(pos,self.TYPE_IMPORT_WORD)
        if ret:
            line,col = pos
            col -= len(self.TYPE_IMPORT_WORD)
            col -= 1
            at = self.GetCharAt(line,col)
            while at == self.TYPE_BLANK_WORD:
                col -= 1
                at = self.GetCharAt(line,col)
            if col <= 0:
                return False,''
            from_word = self.GetTypeWord(line,col)
            col -= len(from_word)
            col -= 1
            pos = line,col
            ret,pos = self.IsKeywordBeforePos(pos,self.TYPE_FROM_WORD)
            return ret,from_word
        return False,''
                
    def OnChar(self,event):
        return self.HandlerInput(event)
        
    def GetAutoCompletions(self,context,hint,last_char):
        pos = self.GetCurrentPos()
        pos = pos[0],pos[1]-1
        #输入dot(.)符号,列出成员
        if last_char == self.TYPE_POINT_WORD:
            text = self.GetTypeWord(pos[0],pos[1])
            return self.ListMembers(pos,text)
        #输入空格提示导入信息
        elif last_char == self.TYPE_BLANK_WORD:
            #输入的是否from xx import 这样的句式
            ret,name = self.IsFromImportType(pos)
            if ret:
                member_list = intellisence.IntellisenceManager().GetMemberList(name)
                if member_list == []:
                    return [],0
                member_list.insert(0,"*")
                return member_list,0
            #输入的是from或者import这样的句式
            elif self.IsImportType(pos) or self.IsFromType(pos):
                import_list = intellisence.IntellisenceManager().GetImportList()
                #import_list.extend(self.GetCurdirImports())
                import_list = parserutils.py_sorted(import_list,parserutils.CmpMember)
                return import_list,0
            #输入from xxx后自动完成输入import关键字
            elif self.IsFromplusType(pos):
                self.AddText(self.TYPE_BLANK_WORD)
                self.AutoCompShow(0, [self.TYPE_IMPORT_WORD])
                #输入from xx import后接着弹出后面的提示信息
                return self.GetAutoCompletions("","",self.TYPE_BLANK_WORD)
            else:
                return [],0
        elif last_char not in self.DEFAULT_WORD_CHARS:
            return [],0
        else:
            member_list,repLen = self.ListMembers(pos,context)
            self.AutoCompShow(repLen, member_list,auto_insert=False)
            if self.autocompleter is not None:
                self.autocompleter.ShowHintCompletions(hint)
            return [],0

    def HandlerInput(self,event):
        #是否启用代码自动完成
        if not utils.profile_get_int("UseAutoCompletion", True):
            return
        char = event.char
        #只有启用代码自动完成增强版功能时才能边输入边提示
        if char and char in self.DEFAULT_WORD_CHARS and not self.AutoCompActive() and utils.profile_get_int("UseEnhancedAutoCompletion", False):
            current_view = GetApp().GetDocumentManager().GetCurrentView()
            GetApp().event_generate(constants.AUTO_COMPLETION_INPUT_EVT,view=current_view,char=char)
        elif char in [self.TYPE_BLANK_WORD,self.TYPE_POINT_WORD]:
            completions,replaceLen = self.GetAutoCompletions("","",char)
            self.insert("insert", char)
            self.AutoCompShow(replaceLen, completions)
            return "break"
        else:
            #输入非asc字符时关闭自动完成列表框
            if not char in self.DEFAULT_WORD_CHARS:
                self.AutoCompHide()
            pos = self.GetCurrentPos()
            pos = pos[0],pos[1]-1
            #输入(符号,弹出文档提示信息
            if char == "(":
                self.GetArgTip(pos)
                self.insert("insert", '()')
                self.GotoPos(pos[0],pos[1]+2)
                return "break"
            elif char == "'":
                #如果单引号前面有2个单引号,插入单三引号
                if self.GetCharAt(pos[0],pos[1]) == "'" and self.GetCharAt(pos[0],pos[1]-1) == "'":
                   #插入成双的单三引号
                    self.insert("insert","'''")
                    self.GotoPos(pos[0],pos[1]+1)
                #如果单引号前后面各有1个单引号,也插入单三引号
                elif self.GetCharAt(pos[0],pos[1]) == "'" and self.GetCharAt(pos[0],pos[1]+1) == "'":
                    #插入成双的单三引号
                    self.insert("insert","'''")
                    self.GotoPos(pos[0],pos[1]+2)
                else:
                    #插入成双的单引号
                    return codeeditor.CodeCtrl.OnChar(self,event)
            elif char == '"':
                #如果双引号前面有2个单引号,插入双三引号
                if self.GetCharAt(pos[0],pos[1]) == '"' and self.GetCharAt(pos[0],pos[1]-1) == '"':
                    #插入成双的双三引号
                    self.insert("insert",'"""')
                    self.GotoPos(pos[0],pos[1]+1)
                #如果双引号前后面各有1个双引号,也插入双三引号
                elif self.GetCharAt(pos[0],pos[1]) == '"' and self.GetCharAt(pos[0],pos[1]+1) == '"':
                    #插入成双的双三引号
                    self.insert("insert",'"""')
                    self.GotoPos(pos[0],pos[1]+2)
                else:
                    #插入成双的双引号
                    return codeeditor.CodeCtrl.OnChar(self,event)
            else:
                return codeeditor.CodeCtrl.OnChar(self,event)

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
        text = self.GetTypeWord(pos[0],pos[1])
        module_scope = GetApp().GetDocumentManager().GetCurrentView().ModuleScope
        if module_scope is None:
            return
        line = pos[0]
        scope = module_scope.FindScope(line+1)
        found_scopes = scope.FindNameScopes(text)
        tip = ''
        if found_scopes:
            scope_found = found_scopes[0]
            if scope_found.Parent is not None and isinstance(scope_found.Node,nodeast.ImportNode):
                tip = scope_found.GetImportMemberArgTip(text)
            else:
                tip = scope_found.GetArgTip()
        if not tip:
            return
        self.CallTipShow(pos,tip)

    def ListMembers(self,pos,text):
        line = pos[0]
        module_scope = GetApp().GetDocumentManager().GetCurrentView().ModuleScope
        if module_scope is None:
            return [],0
        scope = module_scope.FindScope(line+1)
        found_top_scopes = scope.FindNameScopes(text)
        member_list = []
        if found_top_scopes:
            scope_top_found = found_top_scopes[0]
            if scope_top_found.Parent is not None and isinstance(scope_top_found.Node,nodeast.ImportNode):
                member_list = scope_top_found.GetImportMemberList(text)
            else:
                if scope.IsClassMethodScope() and scope.Parent == scope_top_found:
                    member_list = scope_top_found.GetClassMemberList()
                else:
                    #这里查找的顶层的范围,需要查找精确的子范围
                    scope_founds = scope_top_found.GetMember(text)
                    if scope_founds:
                        scope_found = scope_founds[0]
                        member_list = scope_found.GetMemberList()
        member_list = parserutils.py_sorted(member_list,parserutils.CmpMember)
        if member_list == []:
            return [],0
        return member_list,0

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
        at = self.GetCharAt(line,col-1)
        if at == "":
            return False
        return True if at in self.DEFAULT_WORD_CHARS else False

    def GotoDefinition(self):
        
        def NotFoundDefinition(txt):
            messagebox.showwarning(_("Goto Definition"),_("Cannot find definition") + "\"" + txt + "\"",parent = self.master)
            
        line,col= self.GetCurrentLineColumn()
        text = self.GetTypeWord(line,col-1)
        open_new_doc = False
        module_scope = GetApp().GetDocumentManager().GetCurrentView().ModuleScope
        definitions = []
        if module_scope is not None:
            scope = module_scope.FindScope(line)
            definitions = scope.GetDefinitions(text)
        if not definitions:
            NotFoundDefinition(text)
        else:
            if len(definitions) == 1:
                definition = definitions[0]
                if definition.Parent is None:
                    GetApp().GotoView(definition.Module.Path,0)
                else:
                    open_new_doc = (definition.Root != scope.Root)
                    if not open_new_doc:
                        doc_view = GetApp().GetDocumentManager().GetCurrentView()
                        doc_view.GotoPos(definition.Node.Line , definition.Node.Col)
                    else:
                        #找到python内建函数,无法定位到行
                        if -1 == definition.Node.Line or definition.Node.IsBuiltIn:
                            NotFoundDefinition(text)
                            return
                        GetApp().GotoView(definition.Root.Module.Path,definition.Node.Line,definition.Node.Col)
            else:
                dlg = pyutils.DefinitionsDialog(GetApp().GetTopWindow(),GetApp().GetDocumentManager().GetCurrentView(),definitions)
                dlg.ShowModal()

    def GetTypeWord(self,cur_line,cur_col):
        line,word_col = self.get_line_col(self.index("%d.%d wordstart"% (cur_line,cur_col)))
        word_end = self.index("%d.%d wordend"% (cur_line,cur_col))
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
        return text.strip()

    def perform_return(self, event):
        '''
            回车键自动缩进文本
        '''
        #回车时关闭鼠标提示信息
        self.CallTipHide()
        #是否启用自动缩进
        if not self.AutoCompActive() and utils.profile_get_int("AutoIndent", True):
            self.DoIndent()
            #屏蔽默认回车键事件
            return "break"
        else:
            return codeeditor.CodeCtrl.perform_return(self,event)
            
    def perform_smart_backspace(self, event):
        codeeditor.CodeCtrl.perform_smart_backspace(self,event)
        #退格时关闭文档提示
        self.CallTipHide()
        #退格时完成代码提示
        #只有启用代码自动完成增强版功能时才能边退格边提示
        if utils.profile_get_int("UseAutoCompletion", True) and not self.AutoCompActive() and utils.profile_get_int("UseEnhancedAutoCompletion", False):
            current_view = GetApp().GetDocumentManager().GetCurrentView()
            GetApp().event_generate(constants.AUTO_COMPLETION_BACKSPACE_EVT,view=current_view)
        return "break"
        
    def IsEditDisabled(self):
        '''
            调试器运行时是否允许编辑代码文件,新建文件除外
        '''
        doc_view = GetApp().GetDocumentManager().GetCurrentView()
        if doc_view and doc_view.GetDocument() and isinstance(doc_view,codeeditor.CodeView) and utils.profile_get_int("DISABLE_EDIT_WHEN_DEBUGGER_RUNNING",True) and \
                pythondebugger.BaseDebuggerUI.DebuggerRunning() and not doc_view.GetDocument().IsNewDocument:
            return True
        return False
        
    def is_read_only(self):
        if self.IsEditDisabled():
            return True
        return codeeditor.CodeCtrl.is_read_only(self)
        
