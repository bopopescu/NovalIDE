import wx
from noval.tool import FindTextCtrl
import noval.tool.service.FindService as FindService
import noval.util.sysutils as sysutilslib
import noval.tool.STCTextEditor as STCTextEditor
import os
_ = wx.GetTranslation

class DebugOutputCtrl(FindTextCtrl.FindTextCtrl):
    
    TEXT_WRAP_ID = wx.NewId()
    FIND_TEXT_ID = wx.NewId()
    EXPORT_TEXT_ID = wx.NewId()
    ERROR_COLOR_STYLE = 2
    INPUT_COLOR_STYLE = 1
    ItemIDs = [wx.ID_UNDO, wx.ID_REDO,None,wx.ID_CUT, wx.ID_COPY, wx.ID_PASTE, wx.ID_CLEAR,None, wx.ID_SELECTALL,TEXT_WRAP_ID,FindService.FindService.FIND_ID,EXPORT_TEXT_ID]
    
    def __init__(self, parent, id=-1, style = wx.NO_FULL_REPAINT_ON_RESIZE,is_debug=False):
        FindTextCtrl.FindTextCtrl.__init__(self, parent, id, style=style)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        if sysutilslib.isLinux():
            accelTbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('A'), wx.ID_SELECTALL),(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY),(wx.ACCEL_CTRL, ord('V'), wx.ID_PASTE),(wx.ACCEL_CTRL, ord('F'), FindService.FindService.FIND_ID)])  
            self.SetAcceleratorTable(accelTbl)
            
        if wx.Platform == '__WXMSW__':
            font = "Courier New"
        else:
            font = "Courier"
        self._font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = font)
        self.SetFont(self._font)
        self.SetFontColor(wx.BLACK)
        
        self._first_input = True
        self._input_start_pos = 0
        self._executor = None
        self._is_debug = is_debug
        wx.EVT_MOUSE_CAPTURE_LOST(self,self.OnMouseCaptureLost)
        wx.EVT_SET_FOCUS(self, self.OnFocus)
        wx.stc.EVT_STC_DOUBLECLICK(self, self.GetId(), self.OnDoubleClick) 
        
        wx.stc.EVT_STC_MODIFIED(self, self.GetId(), self.OnModify)    
        wx.EVT_KEY_DOWN(self, self.OnKeyPressed)
        
    def OnMouseCaptureLost(self,event):
        pass
        
    @property
    def IsFirstInput(self):
        return self._first_input
        
    @IsFirstInput.setter
    def IsFirstInput(self,first_input):
        self._first_input = first_input
        
    @property
    def InputStartPos(self):
        return self._input_start_pos
        
    @InputStartPos.setter
    def InputStartPos(self,input_start_pos):
        self._input_start_pos = input_start_pos
        
    def OnRightUp(self, event):
        self.ActiveDebugView()
        self.PopupMenu(self.CreatePopupMenu(), event.GetPosition())
        
    def CreatePopupMenu(self):
        menu = wx.Menu()
        frame = wx.GetApp().MainFrame
        menuBar = frame.GetMenuBar()
        for itemID in self.ItemIDs:
            if not itemID:
                menu.AppendSeparator()
            else:
                item = menuBar.FindItemById(itemID)
                if item:
                    menu_item = wx.MenuItem(menu,itemID,item.GetItemLabel())
                    bmp = item.GetBitmap()
                    if bmp:
                        menu_item.SetBitmap(bmp)
                    menu.AppendItem(menu_item)
                elif itemID == self.TEXT_WRAP_ID:
                    menu.AppendCheckItem(self.TEXT_WRAP_ID, _("Word Wrap"))
                elif itemID == self.EXPORT_TEXT_ID:
                    menu.Append(self.EXPORT_TEXT_ID, _("Export All"))
                    
        for itemID in self.ItemIDs:
            if itemID:
                wx.EVT_MENU(self, itemID, frame.ProcessEvent) 
                wx.EVT_UPDATE_UI(self, itemID, self.ProcessUpdateUIEvent)
        return menu
        
    def ProcessEvent(self, event):
        id = event.GetId()
        if id == wx.ID_UNDO:
            self.Undo()
            return True
        elif id == wx.ID_REDO:
            self.Redo()
            return True
        elif id == wx.ID_CUT:
            self.Cut()
            return True
        elif id == wx.ID_COPY:
            self.Copy()
            return True
        elif id == wx.ID_PASTE:
            self.OnPaste()
            return True
        elif id == wx.ID_CLEAR:
            self.ClearOutput()
            return True
        elif id == wx.ID_SELECTALL:
            self.SelectAll()
            return True
        elif id == self.TEXT_WRAP_ID:
            self.SetWordWrap(not self.GetWordWrap())
            return True
            
        elif id == FindService.FindService.FIND_ID:
            findService = wx.GetApp().GetService(FindService.FindService)
            findService.ShowFindReplaceDialog(findString = self.GetSelectedText())
            return True
        elif id == self.EXPORT_TEXT_ID:
            self.SaveAll()
            return True
        elif id == FindService.FindService.FINDONE_ID:
            self.DoFindText()
            return True
        else:
            return False
            
    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == wx.ID_UNDO:
            event.Enable(self.CanUndo())
            return True
        elif id == wx.ID_REDO:
            event.Enable(self.CanRedo())
            return True
        elif id == wx.ID_CUT or id == wx.ID_PASTE:
            event.Enable(False)
            return True
        elif id == wx.ID_COPY:
            event.Enable(self.HasSelection())
            return True
        elif id == wx.ID_CLEAR:
            event.Enable(True)  # wxBug: should be stcControl.CanCut()) but disabling clear item means del key doesn't work in control as expected
            return True
        elif id == wx.ID_SELECTALL or id == FindService.FindService.FIND_ID or id == self.EXPORT_TEXT_ID:
            hasText = self.GetTextLength() > 0
            event.Enable(hasText)
            return True
        elif id == self.TEXT_WRAP_ID:
            event.Enable(self.CanWordWrap())
            event.Check(self.CanWordWrap() and self.GetWordWrap())
            return True
        else:
            return False       
            
    def OnFocus(self, event):
        self.ActiveDebugView()
        event.Skip()
        
    def ActiveDebugView(self):
        if not self._is_debug:
            wx.GetApp().GetDocumentManager().ActivateView(self.GetParent()._service.GetView())
        else:
            wx.GetApp().GetDocumentManager().ActivateView(self.GetParent().GetParent().GetParent()._service.GetView())
        
    def ClearOutput(self):
        self.SetReadOnly(False)
        self.ClearAll()
        self.SetReadOnly(True)
        
    def DoFindText(self,forceFindNext = False, forceFindPrevious = False):
        findService = wx.GetApp().GetService(FindService.FindService)
        if not findService:
            return
        findString = findService.GetFindString()
        if len(findString) == 0:
            return -1
        flags = findService.GetFlags()
        if not FindTextCtrl.FindTextCtrl.DoFindText(self,findString,flags,forceFindNext,forceFindPrevious):
            self.TextNotFound(findString,flags,forceFindNext,forceFindPrevious)
            
    def SaveAll(self):
        text_docTemplate = wx.GetApp().GetDocumentManager().FindTemplateForPath("test.txt")
        descr = _(text_docTemplate.GetDescription()) + " (" + text_docTemplate.GetFileFilter() + ") |" + text_docTemplate.GetFileFilter()  # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
        if text_docTemplate.GetDocumentType() == STCTextEditor.TextDocument:
            default_ext = ""
            descr = _("All Files") +  "(*.*) |*.*|%s" % descr
        filename = wx.FileSelector(_("Save As"),
                                   text_docTemplate.GetDirectory(),
                                   "*.txt",
                                   default_ext,
                                   wildcard = descr,
                                   flags = wx.SAVE | wx.OVERWRITE_PROMPT,
                                   parent = self)
                                   

        if filename == "":
            return
            
        try:
            with open(filename,"wb") as f:
                f.write(self.GetText())
        except Exceptin as e:
            wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)

    def OnDoubleClick(self, event):
        # Looking for a stack trace line.
        lineText, pos = self.GetCurLine()
        fileBegin = lineText.find("File \"")
        fileEnd = lineText.find("\", line ")
        lineEnd = lineText.find(", in ")
        if lineText == "\n" or  fileBegin == -1 or fileEnd == -1:
            # Check the line before the one that was clicked on
            lineNumber = self.GetCurrentLine()
            if(lineNumber == 0):
                return
            lineText = self.GetLine(lineNumber - 1)
            fileBegin = lineText.find("File \"")
            fileEnd = lineText.find("\", line ")
            lineEnd = lineText.find(", in ")
            if lineText == "\n" or  fileBegin == -1 or fileEnd == -1:
                return

        filename = lineText[fileBegin + 6:fileEnd]
        if filename == "<string>" :
            return
        if -1 == lineEnd:
            lineNum = int(lineText[fileEnd + 8:])
        else:
            lineNum = int(lineText[fileEnd + 8:lineEnd])
        if filename and not os.path.exists(filename):
            wx.MessageBox("The file '%s' doesn't exist and couldn't be opened!" % filename,
                              _("File Error"),
                              wx.OK | wx.ICON_ERROR,
                              wx.GetApp().GetTopWindow())
            return
        wx.GetApp().GotoView(filename,lineNum)
        #last activiate debug view
        self.ActiveDebugView()
        

    def AppendText(self, text,last_readonly=False):
        self.SetReadOnly(False)
        self.SetCurrentPos(self.GetTextLength())
        self.AddText(text)
        self.ScrollToLine(self.GetLineCount())
        #rember last position
        self.InputStartPos = self.GetCurrentPos()
        if last_readonly:
            self.SetReadOnly(True)

    def AppendErrorText(self, text,last_readonly=False):
        self.SetReadOnly(False)
        self.SetCurrentPos(self.GetTextLength())
        self.StyleSetSpec(self.ERROR_COLOR_STYLE, 'fore:#ff0000, back:#FFFFFF,face:%s,size:%d' % \
                                    (self._font.GetFaceName(),self._font.GetPointSize())) 
        pos = self.GetCurrentPos()
        self.AddText(text)
        self.StartStyling(pos, 2)
        self.SetStyling(len(text), self.ERROR_COLOR_STYLE)
        self.ScrollToLine(self.GetLineCount())
        #rember last position
        self.InputStartPos = self.GetCurrentPos()
        if last_readonly:
            self.SetReadOnly(True)

    def OnModify(self,event):
        if self.GetCurrentPos() <= self.InputStartPos:
            #disable back delete key
            self.CmdKeyClear(wx.stc.STC_KEY_BACK ,0)
        else:
            #enable back delete key
            self.CmdKeyAssign(wx.stc.STC_KEY_BACK ,0,wx.stc.STC_CMD_DELETEBACK)
    
    def OnKeyPressed(self, event):
        #when ctrl is read only,disable all key events
        if self.GetReadOnly():
            return
        key = event.GetKeyCode()
        if key in [wx.WXK_LEFT,wx.WXK_UP,wx.WXK_RIGHT,wx.WXK_DOWN]:
            event.Skip()
            return
        if self.GetCurrentPos() < self.InputStartPos:
            return
        if self.IsFirstInput:
            self.InputStartPos = self.GetCurrentPos()
            self.IsFirstInput = False
        self.SetInputStyle()
        if key == wx.WXK_RETURN:
            inputText = self.GetRange(self.InputStartPos,self.GetCurrentPos())
            #should colorize last input char
            if self.GetCurrentPos() - 1 >= 0:
                self.StartStyling(self.GetCurrentPos()-1, 31)
                self.SetStyling(1, self.INPUT_COLOR_STYLE)
            self.AddText('\n')
            self._executor.WriteInput(inputText + "\n")
            self.IsFirstInput = True
        else:
            pos = self.GetCurrentPos()
            event.Skip()
            if pos-1 >= 0:
                #should colorize input char from last pos
                self.StartStyling(pos-1, 31)
                self.SetStyling(1, self.INPUT_COLOR_STYLE)
                
    def SetExecutor(self,executor):
        self._executor = executor
        
    def AddInputText(self,text):
        self.SetReadOnly(False)
        self.SetInputStyle()
        pos = self.GetCurrentPos()
        self.AddText(text+"\n")
        self.StartStyling(pos, 31)
        self.SetStyling(len(text), self.INPUT_COLOR_STYLE)
        self.SetReadOnly(True)
        
    def SetInputStyle(self):
        self.StyleSetSpec(self.INPUT_COLOR_STYLE, 'fore:#221dff, back:#FFFFFF,face:%s,size:%d' % \
                     (self._font.GetFaceName(),self._font.GetPointSize())) 
        