#----------------------------------------------------------------------------
# Name:         PythonEditor.py
# Purpose:      PythonEditor for wx.lib.pydocview tbat uses the Styled Text Control
#
# Author:       Peter Yared
#
# Created:      8/15/03
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import CodeEditor
import wx
import wx.lib.docview
import wx.lib.pydocview
import string
import keyword  # So it knows what to hilite
import wx.py  # For the Python interpreter
import wx.stc # For the Python interpreter
import StringIO  # For indent
import service.OutlineService as OutlineService
import STCTextEditor
import keyword # for GetAutoCompleteKeywordList
import sys # for GetAutoCompleteKeywordList
import service.MessageService as MessageService # for OnCheckCode
import service.OutlineService as OutlineService
import codecs
import noval.tool.syntax.lang as lang
import service.Service as Service
import noval.parser.fileparser as parser
import noval.parser.scope as scope
import interpreter.Interpreter as Interpreter
import noval.parser.intellisence as intellisence
import noval.parser.nodeast as nodeast
import noval.util.strutils as strutils
import service.CompletionService as CompletionService
import noval.tool.debugger as debugger
from noval.parser.utils import CmpMember
from noval.util.logger import app_debugLogger
import noval.util.sysutils as sysutilslib
import noval.tool.interpreter.InterpreterManager as interpretermanager
import threading
import PyShell
import noval.util.fileutils as fileutils
import noval.parser.utils as parserutils
import service.TextService as TextService
import consts
import noval.tool.project as project
from noval.model import configuration
from noval.util import utils
try:
    import checker # for pychecker
    _CHECKER_INSTALLED = True
except ImportError:
    _CHECKER_INSTALLED = False
import os.path # for pychecker
_ = wx.GetTranslation

VIEW_PYTHON_INTERPRETER_ID = wx.NewId()

class PythonDocument(CodeEditor.CodeDocument): 

    UTF_8_ENCODING = 0
    GBK_ENCODING = 1
    ANSI_ENCODING = 2
    UNKNOWN_ENCODING = -1
    
    def __init__(self):
        CodeEditor.CodeDocument.__init__(self)
        
    def GetRunParameter(self):
        config = wx.ConfigBase_Get()
        fileToRun = self.GetFilename()
        unprojProj = project.ProjectEditor.ProjectDocument.GetUnProjectDocument()
        initialArgs = config.Read(unprojProj.GetUnProjectFileKey(fileToRun,"RunArguments"),"")
        python_path = config.Read(unprojProj.GetUnProjectFileKey(fileToRun,"PythonPath"),"")
        startIn = config.Read(unprojProj.GetUnProjectFileKey(fileToRun,"RunStartIn"),"")
        if startIn == '':
            startIn = os.path.dirname(fileToRun)
        env = {}
        #should avoid environment contain unicode string,such as u'xxx'
        if python_path != '':
            env[consts.PYTHON_PATH_NAME] = str(python_path)
        return configuration.RunParameter(wx.GetApp().GetCurrentInterpreter(),fileToRun,initialArgs,env,startIn)

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
            raise LookupError, "Unknown encoding " + name
        return name
        
    def DoSaveBefore(self):
        CodeEditor.CodeDocument.DoSaveBefore(self)
        docTemplate = self.GetDocumentTemplate()
        view = self.GetFirstView()
        lines = view.GetTopLines(consts.ENCODING_DECLARE_LINE_NUM)
        declare_encoding = self.get_coding_spec(lines)
        interpreter = wx.GetApp().GetCurrentInterpreter()
        #when python version is 2,should check the encoding declare if python file contain
        #chinse character,which python3 is not necessary
        if interpreter.IsV2():
            if None == declare_encoding and self.file_encoding != self.ASC_FILE_ENCODING:
                ret = wx.MessageBox(_("Detect your python file contain chinese character,please insert encoding declare.\n\nClick 'Yes' to insert,or 'No' to cancel?"),_("Declare Encoding"),style = wx.YES_NO | wx.ICON_QUESTION)
                if ret == wx.YES:
                    txt_service = wx.GetApp().GetService(TextService.TextService)
                    if txt_service.InsertEncodingDeclare(view):
                        lines = view.GetTopLines(consts.ENCODING_DECLARE_LINE_NUM)
                        declare_encoding = self.get_coding_spec(lines)
        if declare_encoding is None:
            #only python2 must need encoding declare,while python3 is not must need
            if interpreter.IsV2():
                declare_encoding = CodeEditor.CodeDocument.DEFAULT_FILE_ENCODING
                if self.IsDocEncodingChanged(declare_encoding):
                    self.file_encoding = declare_encoding
        else:
            if self.IsDocEncodingChanged(declare_encoding):
                self.file_encoding = declare_encoding
    
    def DoSaveBehind(self):
        pass
        
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

class PythonView(CodeEditor.CodeView):

    def __init__(self):
        super(PythonView,self).__init__()
        self._module_scope = None
        self._parse_error = None
        #document checksum to check document is updated
        self._checkSum = -1
        self._lock = threading.Lock()
        #is parsing syntax tree?
        self._is_parsing = False
        #when close window,the flag is set to true
        self._is_parse_stoped = False
        
    @property
    def ModuleScope(self):
        return self._module_scope
        
    @property
    def ParseError(self):
        return self._parse_error

    def LoadModule(self,filename):
        module,error = parser.parse_content(self.GetCtrl().GetValue(),filename,self.GetDocument().file_encoding)
        if module is None:
            self._parse_error = error
            return
        module_scope = scope.ModuleScope(module,self.GetCtrl().GetLineCount())
        if not self._is_parse_stoped:
            module_scope.MakeModuleScopes()
        if not self._is_parse_stoped:
            module_scope.RouteChildScopes()
        self.ModuleScope = module_scope
        self._parse_error = None
        
    @ModuleScope.setter
    def ModuleScope(self,module_scope):
        self._module_scope = module_scope
        
    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        return PythonCtrl
    
    def GetLangId(self):
        return lang.ID_LANG_PYTHON

    def ProcessUpdateUIEvent(self, event):
        if not self.GetCtrl():
            return False
            
        id = event.GetId()
        if id == CodeEditor.CHECK_CODE_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            return True
            
        return CodeEditor.CodeView.ProcessUpdateUIEvent(self, event)


    def OnActivateView(self, activate, activeView, deactiveView):
        STCTextEditor.TextView.OnActivateView(self, activate, activeView, deactiveView)
        if activate and self.GetCtrl():
            if self.GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
                self.LoadOutline()
            else:
                wx.CallAfter(self.LoadOutline)  # need CallAfter because document isn't loaded yet

    def OnClose(self, deleteWindow = True):
        logger = utils.GetLogger()
        if self._is_parsing:
            self._is_parse_stoped = True
            logger.info("document %s is still parsing tree ,wait a moment to finish parsing before close",self.GetDocument().GetFilename())
            while True:
                if not self._is_parsing:
                    break
                wx.MilliSleep(250)
                wx.Yield()
            logger.info("document %s has been finish parsing,now will close",self.GetDocument().GetFilename())
        status = STCTextEditor.TextView.OnClose(self, deleteWindow)
        wx.CallAfter(self.ClearOutline)  # need CallAfter because when closing the document, it is Activated and then Close, so need to match OnActivateView's CallAfter
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


    def OnCheckCode(self):
        if not _CHECKER_INSTALLED:       
            wx.MessageBox(_("pychecker not found.  Please install pychecker."), _("Check Code"))
            return

        filename = os.path.basename(self.GetDocument().GetFilename())

        # pychecker only works on files, doesn't take a stream or string input
        if self.GetDocument().IsModified():
            dlg = wx.MessageDialog(self.GetFrame(), _("'%s' has been modfied and must be saved first.  Save file and check code?") % filename, _("Check Code"))
            dlg.CenterOnParent()
            val = dlg.ShowModal()
            dlg.Destroy()
            if val == wx.ID_OK:
                self.GetDocument().Save()
            else:
                return
            
        messageService = wx.GetApp().GetService(MessageService.MessageService)
        messageService.ShowWindow()
        view = messageService.GetView()
        if not view:
            return
            
        view.ClearLines()
        view.SetCallback(self.OnJumpToFoundLine)
        
        # Set cursor to Wait cursor
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))

        try:
            # This takes a while for involved code
            checker.checkSyntax(self.GetDocument().GetFilename(), view)

        finally:
            # Set cursor to Default cursor
            wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))


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

    def DoLoadOutlineCallback(self, force=False,lineNum=-1):
        outlineService = wx.GetApp().GetService(OutlineService.OutlineService)
        if not outlineService:
            return False

        outlineView = outlineService.GetView()
        if not outlineView:
            return False

        treeCtrl = outlineView.GetTreeCtrl()
        if not treeCtrl:
            return False

        view = treeCtrl.GetCallbackView()
        newCheckSum = self.GenCheckSum()
        force = self._checkSum != newCheckSum
        if not force:
            if view and view is self:
                if self._checkSum == newCheckSum:
                    return False
        self._checkSum = newCheckSum
        document = self.GetDocument()
        if not document:
            return True
        t = threading.Thread(target=self.LoadMouduleSynchronizeTree,args=(view,force,treeCtrl,outlineService,lineNum))
        t.start()
        return True
        
    def LoadMouduleSynchronizeTree(self,view,force,treeCtrl,outlineService,lineNum):
        with self._lock:
            if self._is_parsing:
                print 'document %s is already parseing,will not parse again' % self.GetDocument().GetFilename()
                return True
            self._is_parsing = True
            document = self.GetDocument()
            filename = document.GetFilename()
            if force:
                self.LoadModule(filename)
            if self.ModuleScope == None:
                if view is None or filename != view.GetDocument().GetFilename():
                    wx.CallAfter(treeCtrl.DeleteAllItems)
                self._is_parsing = False
                return True
            #should freeze control to prevent update and treectrl flick
            if not self._is_parse_stoped:
                treeCtrl.LoadModuleAst(self.ModuleScope,self,outlineService,lineNum)
            else:
                self._is_parsing = False
        
    def IsUnitTestEnable(self):
        return True

class PythonInterpreterView(Service.ServiceView):

    def _CreateControl(self, parent, id):
        sizer = wx.BoxSizer()
        self.shell = PyShell.PyShell(parent=parent, id=-1, introText='',
                           locals=None, InterpClass=None,
                           startupScript=None,
                           execStartupScript=True)
        sizer.Add(self.shell, 1, wx.EXPAND, 0)
        return self.shell
        
    def GetDocument(self):
        return None

    def OnFocus(self, event):
        wx.GetApp().GetDocumentManager().ActivateView(self)
        event.Skip()        

    def ProcessEvent(self, event):
        if not hasattr(self, "shell") or not self.shell:
            return wx.lib.docview.View.ProcessEvent(self, event)
        stcControl = wx.Window_FindFocus()
        if not isinstance(stcControl, wx.stc.StyledTextCtrl):
            return wx.lib.docview.View.ProcessEvent(self, event)
        id = event.GetId()
        if id == wx.ID_UNDO:
            stcControl.Undo()
            return True
        elif id == wx.ID_REDO:
            stcControl.Redo()
            return True
        elif id == wx.ID_CUT:
            stcControl.Cut()
            return True
        elif id == wx.ID_COPY:
            stcControl.Copy()
            return True
        elif id == wx.ID_PASTE:
            stcControl.Paste()
            return True
        elif id == wx.ID_CLEAR:
            stcControl.Clear()
            return True
        elif id == wx.ID_SELECTALL:
            stcControl.SetSelection(0, -1)
            return True
        else:
            return wx.lib.docview.View.ProcessEvent(self, event)

    def ProcessUpdateUIEvent(self, event):
        if not hasattr(self, "shell") or not self.shell:
            return wx.lib.docview.View.ProcessUpdateUIEvent(self, event)
        stcControl = wx.Window_FindFocus()
        if not isinstance(stcControl, wx.stc.StyledTextCtrl):
            return wx.lib.docview.View.ProcessUpdateUIEvent(self, event)
        id = event.GetId()
        if id == wx.ID_UNDO:
            event.Enable(stcControl.CanUndo())
            return True
        elif id == wx.ID_REDO:
            event.Enable(stcControl.CanRedo())
            return True
        elif id == wx.ID_CUT:
            event.Enable(stcControl.HasSelection())
            return True
        elif id == wx.ID_COPY:
            event.Enable(stcControl.HasSelection())
            return True
        elif id == wx.ID_PASTE:
            event.Enable(stcControl.CanPaste())
            return True
        elif id == wx.ID_CLEAR:
            event.Enable(True)  # wxBug: should be stcControl.CanCut()) but disabling clear item means del key doesn't work in control as expected
            return True
        elif id == wx.ID_SELECTALL:
            event.Enable(stcControl.GetTextLength() > 0)
            return True
        else:
            return wx.lib.docview.View.ProcessUpdateUIEvent(self, event)


    def OnClose(self, deleteWindow=True):
        if deleteWindow and self.GetFrame():
            self.GetFrame().Destroy()
        return True


class PythonInterpreterDocument(wx.lib.docview.Document):
    """ Generate Unique Doc Type """
    pass
    

class PythonService(Service.Service):

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def _CreateView(self):
        return PythonInterpreterView(self)

    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        Service.Service.InstallControls(self, frame, menuBar, toolBar, statusBar, document)

        if document and document.GetDocumentTemplate().GetDocumentType() != PythonDocument:
            return
        if not document and wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return

        #viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))
        #viewStatusBarItemPos = self.GetMenuItemPos(viewMenu, wx.lib.pydocview.VIEW_STATUSBAR_ID)
        #viewMenu.InsertCheckItem(viewStatusBarItemPos + 1, VIEW_PYTHON_INTERPRETER_ID, _("Python &Interpreter"), _("Shows or hides the Python interactive window"))
        #wx.EVT_MENU(frame, VIEW_PYTHON_INTERPRETER_ID, frame.ProcessEvent)
        #wx.EVT_UPDATE_UI(frame, VIEW_PYTHON_INTERPRETER_ID, frame.ProcessUpdateUIEvent)

    def ProcessEvent(self, event):
        id = event.GetId()
        if id == VIEW_PYTHON_INTERPRETER_ID:
            self.OnViewPythonInterpreter(event)
            return True
        else:
            return Service.Service.ProcessEvent(self, event)


    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == VIEW_PYTHON_INTERPRETER_ID:
            event.Enable(True)
            docManager = wx.GetApp().GetDocumentManager()
            event.Check(False)
            for doc in docManager.GetDocuments():
                if isinstance(doc, PythonInterpreterDocument):
                    event.Check(True)
                    break
            return True
        else:
            return Service.Service.ProcessUpdateUIEvent(self, event)


    def OnViewPythonInterpreter(self, event):
        for doc in wx.GetApp().GetDocumentManager().GetDocuments():
            if isinstance(doc, PythonInterpreterDocument):
                doc.DeleteAllViews()
                return
                
        for template in self.GetDocumentManager().GetTemplates():
            if template.GetDocumentType() == PythonInterpreterDocument:
                newDoc = template.CreateDocument('', wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
                if newDoc:
                    newDoc.SetDocumentName(template.GetDocumentName())
                    newDoc.SetDocumentTemplate(template)
                    newDoc.OnNewDocument()
                    newDoc.SetWriteable(False)
                    newDoc.GetFirstView().GetFrame().SetTitle(_("Python Interpreter"))
                break

    def GetIconIndex(self):
        return Service.ServiceView.InterpreterIconIndex


class PythonCtrl(CodeEditor.CodeCtrl):

    TypeKeyWords = "complex list tuple dict bool int long float True False None"

    def __init__(self, parent, id=-1, style=wx.NO_FULL_REPAINT_ON_RESIZE):
        CodeEditor.CodeCtrl.__init__(self, parent, id, style)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def CreatePopupMenu(self):
        SYNCTREE_ID = wx.NewId()
        menu = CodeEditor.CodeCtrl.CreatePopupMenu(self)
        menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.OnPopSyncOutline, id=SYNCTREE_ID)
        item = wx.MenuItem(menu, SYNCTREE_ID, _("Find in Outline View"))
        menu.AppendItem(item)
        
        self.Bind(wx.EVT_MENU, self.OnGotoDefinition, id=CompletionService.CompletionService.GO_TO_DEFINITION)
        item = wx.MenuItem(menu, CompletionService.CompletionService.GO_TO_DEFINITION, \
                            _("Goto Definition\tF12"))
        wx.EVT_UPDATE_UI(self,CompletionService.CompletionService.GO_TO_DEFINITION, self.DSProcessUpdateUIEvent)
        menu.AppendItem(item)
        
        menuBar = wx.GetApp().GetTopWindow().GetMenuBar()
        menu_item = menuBar.FindItemById(debugger.DebuggerService.DebuggerService.START_RUN_ID)
        item = wx.MenuItem(menu,debugger.DebuggerService.DebuggerService.START_RUN_ID,_("&Run"), kind = wx.ITEM_NORMAL)
        item.SetBitmap(menu_item.GetBitmap())
        menu.AppendItem(item)
        wx.EVT_MENU(self, debugger.DebuggerService.DebuggerService.START_RUN_ID, self.RunScript)
        
        debug_menu = wx.Menu()
        menu.AppendMenu(wx.NewId(), _("Debug"), debug_menu)

        menu_item = menuBar.FindItemById(debugger.DebuggerService.DebuggerService.START_DEBUG_ID)
        item = wx.MenuItem(menu,debugger.DebuggerService.DebuggerService.START_DEBUG_ID,_("&Debug"), kind = wx.ITEM_NORMAL)
        item.SetBitmap(menu_item.GetBitmap())
        debug_menu.AppendItem(item)
        wx.EVT_MENU(self, debugger.DebuggerService.DebuggerService.START_DEBUG_ID, self.DebugRunScript)
        
        item = wx.MenuItem(menu,debugger.DebuggerService.DebuggerService.BREAK_INTO_DEBUGGER_ID,_("&Break into Debugger"), kind = wx.ITEM_NORMAL)
        debug_menu.AppendItem(item)
        wx.EVT_MENU(self, debugger.DebuggerService.DebuggerService.BREAK_INTO_DEBUGGER_ID, self.BreakintoDebugger)
        return menu

    def DebugRunScript(self,event):
        view = wx.GetApp().GetDocumentManager().GetCurrentView()
        wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).RunWithoutDebug(view.GetDocument().GetFilename())
        
    def BreakintoDebugger(self,event):
        view = wx.GetApp().GetDocumentManager().GetCurrentView()
        wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).BreakIntoDebugger(view.GetDocument().GetFilename())
    
    def RunScript(self,event):
        view = wx.GetApp().GetDocumentManager().GetCurrentView()
        wx.GetApp().GetService(debugger.DebuggerService.DebuggerService).Run(view.GetDocument().GetFilename())

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


    # Callback for tokenizer in self.DoIndent
    def __call__(self, toktype, toktext, (srow,scol), (erow,ecol), line):
        if toktype == tokenize.COMMENT:
            for i in range(scol, ecol + 1):
                self._validChars[i] = False
        elif toktype == token.STRING:
            self._tokenizerChars[scol] = 2 # Open quote
            self._tokenizerChars[ecol - 1] = 3 # Close quote
            for i in range(scol + 1, ecol - 2):
                self._tokenizerChars[i] = 1 # Part of string, 1 == ignore the char
                
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

    def IsCaretLocateInWord(self,pos=-1):
        if pos == -1:
            pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos)
        line_text = self.GetLine(line).strip()
        if line_text == "":
            return False
        if line_text[0] == '#':
            return False
        start_pos = self.WordStartPosition(pos,True)
        end_pos = self.WordEndPosition(pos,True)
        word = self.GetTextRange(start_pos,end_pos).strip()
        return False if word == "" else True

    def GotoDefinition(self):
        line = self.GetCurrentLine()
        pos = self.GetCurrentPos()
        text = self.GetTypeWord(pos)
        open_new_doc = False
        module_scope = Service.Service.GetActiveView().ModuleScope
        if module_scope is None:
            scope_found = None
        else:
            scope = module_scope.FindScope(line)
            scope_found = scope.FindDefinitionMember(text)
        if scope_found is None:
            wx.MessageBox(_("Cannot find definition") + "\"" + text + "\"",_("Goto Definition"),wx.OK|wx.ICON_EXCLAMATION,wx.GetApp().GetTopWindow())
        else:
            if scope_found.Parent is None:
                wx.GetApp().GotoView(scope_found.Module.Path,0)
            else:
                open_new_doc = (scope_found.Root != scope.Root)
                if not open_new_doc:
                    doc_view = wx.GetApp().GetDocumentManager().GetCurrentView()
                    startPos = doc_view.PositionFromLine(scope_found.Node.Line)
                    doc_view.GotoPos(startPos + scope_found.Node.Col)
                else:
                    if -1 == scope_found.Node.Line:
                        wx.MessageBox(_("Cannot go to definition") + "\"" + text + "\"",_("Goto Definition"),wx.OK|wx.ICON_EXCLAMATION,wx.GetApp().GetTopWindow())
                        return
                    wx.GetApp().GotoViewPos(scope_found.Root.Module.Path,scope_found.Node.Line,scope_found.Node.Col)


    def OnDwellStart(self, evt):
        mpoint = wx.GetMousePosition()
        brect = self.GetScreenRect()
        #avoid trigger tool many times
        if not brect.Contains(mpoint) or \
           not self.IsShown() or \
           not wx.GetApp().GetTopWindow().IsActive():
            return
        position = evt.Position
        if position >= 0 and self.IsCaretLocateInWord(position):
            line = self.LineFromPosition(position) + 1
            dwellword = self.GetTypeWord(position)
            doc_view = Service.Service.GetActiveView()
            if doc_view.GetLangId() == lang.ID_LANG_PYTHON:
                module_scope = doc_view.ModuleScope
                if module_scope is None:
                    scope_found = None
                else:
                    scope = module_scope.FindScope(line)
                    scope_found = scope.FindDefinitionMember(dwellword)
                if scope_found is not None:
                    doc = scope_found.GetDoc()
                    if doc is not None:
                        self.CallTipShow(position, doc.decode('utf-8'))
            else:
                app_debugLogger.debug('active view is not python code view')
        
        CodeEditor.CodeCtrl.OnDwellStart(self,evt)

    def OnDwellEnd(self, evt):
        self.CallTipCancel()
        CodeEditor.CodeCtrl.OnDwellEnd(self,evt)
#----------------------------------------------------------------------------
# Icon Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import ImageFromStream, BitmapFromImage

def getPythonBitmap():
    python_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "python_module.png")
    python_image = wx.Image(python_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(python_image)

def getPythonIcon():
    return wx.IconFromBitmap(getPythonBitmap())
