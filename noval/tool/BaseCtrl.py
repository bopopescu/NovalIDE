import wx
import wx.stc
from noval.tool.syntax import syntax

class ScintillaCtrl(wx.stc.StyledTextCtrl):
    
    """base scintilla ctrl"""
    DEFAULT_LINE_MARKER_NUM = 1

    def __init__(self, parent, id=-1,style=wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.stc.StyledTextCtrl.__init__(self, parent, id, style=style)

        if isinstance(parent, wx.gizmos.DynamicSashWindow):
            self._dynSash = parent
            self.SetupDSScrollBars()
            self.Bind(wx.gizmos.EVT_DYNAMIC_SASH_SPLIT, self.OnDSSplit)
            self.Bind(wx.gizmos.EVT_DYNAMIC_SASH_UNIFY, self.OnDSUnify)

        self._font = None
        self._fontColor = None
        
        self.SetVisiblePolicy(wx.stc.STC_VISIBLE_STRICT,1)
        
        self.CmdKeyClear(wx.stc.STC_KEY_ADD, wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(wx.stc.STC_KEY_SUBTRACT, wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyAssign(wx.stc.STC_KEY_PRIOR, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(wx.stc.STC_KEY_NEXT, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_ZOOMOUT)
        
        wx.EVT_KEY_DOWN(self, self.OnKeyPressed)
        wx.EVT_KILL_FOCUS(self, self.OnKillFocus)
        wx.EVT_SET_FOCUS(self, self.OnFocus)
        self.SetMargins(0,0)

        self.SetUseTabs(0)
        self.SetTabWidth(4)
        self.SetIndent(4)

        self.SetViewWhiteSpace(False)
        self.SetEOLMode(wx.stc.STC_EOL_LF)

        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, self.EstimatedLineNumberMarginWidth())

        self.UpdateStyles()

        self.SetCaretForeground("BLACK")
        
        self.SetViewDefaults()
        font, color = self.GetFontAndColorFromConfig()

        self.SetFont(font)
        self.SetFontColor(color)
        
        self.SetLineNumberStyle()
        self.SetCaretLineColor((210,210,210),)
        # for multisash initialization   
        if isinstance(parent, wx.lib.multisash.MultiClient):     
            while parent.GetParent():    
                parent = parent.GetParent()      
                if hasattr(parent, "GetView"):   
                    break        
            if hasattr(parent, "GetView"):       
                textEditor = parent.GetView()._textEditor        
                if textEditor:   
                    doc = textEditor.GetDocPointer()     
                    if doc:      
                        self.SetDocPointer(doc)

    def OnFocus(self, event):
        # wxBug: On Mac, the STC control may fire a focus/kill focus event
        # on shutdown even if the control is in an invalid state. So check
        # before handling the event.
        if self.IsBeingDeleted():
            return            
        self.SetSelBackground(1, "BLUE")
        self.SetSelForeground(1, "WHITE")
        if hasattr(self, "_dynSash"):
            self._dynSash._view.SetCtrl(self)
        event.Skip()

    def OnKillFocus(self, event):
        # wxBug: On Mac, the STC control may fire a focus/kill focus event
        # on shutdown even if the control is in an invalid state. So check
        # before handling the event.
        if self.IsBeingDeleted():
            return
        self.SetSelBackground(0, "BLUE")
        self.SetSelForeground(0, "WHITE")
        self.SetSelBackground(1, "#C0C0C0")
        # Don't set foreground color, use syntax highlighted default colors.
        event.Skip()
        
    def SetViewDefaults(self, configPrefix="Text", hasWordWrap=True, hasTabs=False, hasFolding=False):
        pass

    def GetDefaultFont(self):
        """ Subclasses should override this """
        return syntax.LexerManager().GetDefaultFont()

    def GetDefaultColor(self):
        """ Subclasses should override this """
        return syntax.LexerManager().GetDefaultColor()

    def GetFontAndColorFromConfig(self):
        font = self.GetDefaultFont()
        color = self.GetDefaultColor()
        return font, color

    def GetFont(self):
        return self._font
        
    def SetFont(self, font):
        self._font = font
        self.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, self._font)
        
    def GetFontColor(self):
        return self._fontColor

    def SetFontColor(self, fontColor = wx.BLACK):
        self._fontColor = fontColor
        self.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, "#%02x%02x%02x" % (self._fontColor.Red(), self._fontColor.Green(), self._fontColor.Blue()))

    def SetLineNumberStyle(self):
        ###self.UpdateStyles()
        faces = { 'font' : self.GetFont().GetFaceName(),
          'size' : self.GetFont().GetPointSize(),
          'size2': self.GetFont().GetPointSize()-2,
          'color' : "%02x%02x%02x" % (self.GetFontColor().Red(), self.GetFontColor().Green(), self.GetFontColor().Blue())
        }
        # Global default styles for all languages
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,  "face:%(font)s,back:#C0C0C0,face:%(font)s,size:%(size2)d" % faces)
        
    def UpdateStyles(self):
        self.StyleClearAll()
        return

    def EstimatedLineNumberMarginWidth(self):
        lineNum = self.GetLineCount()
        baseNumbers = " %d " % (lineNum)
        lineNum = lineNum/100
        while lineNum >= 10:
            lineNum = lineNum/10
            baseNumbers = baseNumbers + " "
        return self.TextWidth(wx.stc.STC_STYLE_LINENUMBER, baseNumbers) 

    def OnClear(self):
        # Used when Delete key is hit.
        sel = self.GetSelection()              
        # Delete the selection or if no selection, the character after the caret.
        if sel[0] == sel[1]:
            self.SetSelection(sel[0], sel[0] + 1)
        else:
            # remove any folded lines also.
            startLine = self.LineFromPosition(sel[0])
            endLine = self.LineFromPosition(sel[1])
            endLineStart = self.PositionFromLine(endLine)
            if startLine != endLine and sel[1] - endLineStart == 0:
                while not self.GetLineVisible(endLine):
                    endLine += 1
                self.SetSelectionEnd(self.PositionFromLine(endLine))          
        self.Clear()

    def OnPaste(self):
        # replace any folded lines also.
        sel = self.GetSelection()
        startLine = self.LineFromPosition(sel[0])
        endLine = self.LineFromPosition(sel[1])
        endLineStart = self.PositionFromLine(endLine)
        if startLine != endLine and sel[1] - endLineStart == 0:
            while not self.GetLineVisible(endLine):
                endLine += 1
            self.SetSelectionEnd(self.PositionFromLine(endLine))
        self.Paste()
        
    def OnKeyPressed(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_NUMPAD_ADD:  #wxBug: For whatever reason, the key accelerators for numpad add and subtract with modifiers are not working so have to trap them here
            if event.ControlDown():
                self.ToggleFoldAll(expand = True, topLevelOnly = True)
            elif event.ShiftDown():
                self.ToggleFoldAll(expand = True)
            else:
                self.ToggleFold(self.GetCurrentLine())
        elif key == wx.WXK_NUMPAD_SUBTRACT:
            if event.ControlDown():
                self.ToggleFoldAll(expand = False, topLevelOnly = True)
            elif event.ShiftDown():
                self.ToggleFoldAll(expand = False)
            else:
                self.ToggleFold(self.GetCurrentLine())
        else:
            event.Skip()

    #----------------------------------------------------------------------------
    # View Text methods
    #----------------------------------------------------------------------------
    def GetViewRightEdge(self):
        return self.GetEdgeMode() != wx.stc.STC_EDGE_NONE

    def SetViewRightEdge(self, viewRightEdge):
        if viewRightEdge:
            self.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        else:
            self.SetEdgeMode(wx.stc.STC_EDGE_NONE)

    def CanWordWrap(self):
        return True

    def GetWordWrap(self):
        return self.GetWrapMode() == wx.stc.STC_WRAP_WORD

    def SetWordWrap(self, wordWrap):
        if wordWrap:
            self.SetWrapMode(wx.stc.STC_WRAP_WORD)
        else:
            self.SetWrapMode(wx.stc.STC_WRAP_NONE)

    def AddText(self,text):
        try:
            wx.stc.StyledTextCtrl.AddText(self,text)
        except:
            wx.stc.StyledTextCtrl.AddText(self,text.decode("utf-8"))

    def HasSelection(self):
        return self.GetSelectionStart() - self.GetSelectionEnd() != 0  
    #----------------------------------------------------------------------------
    # DynamicSashWindow methods
    #----------------------------------------------------------------------------

    def SetupDSScrollBars(self):
        # hook the scrollbars provided by the wxDynamicSashWindow
        # to this view
        v_bar = self._dynSash.GetVScrollBar(self)
        h_bar = self._dynSash.GetHScrollBar(self)
        v_bar.Bind(wx.EVT_SCROLL, self.OnDSSBScroll)
        h_bar.Bind(wx.EVT_SCROLL, self.OnDSSBScroll)
        v_bar.Bind(wx.EVT_SET_FOCUS, self.OnDSSBFocus)
        h_bar.Bind(wx.EVT_SET_FOCUS, self.OnDSSBFocus)

        # And set the wxStyledText to use these scrollbars instead
        # of its built-in ones.
        self.SetVScrollBar(v_bar)
        self.SetHScrollBar(h_bar)


    def OnDSSplit(self, evt):
        newCtrl = self._dynSash._view.GetCtrlClass()(self._dynSash, -1, style=wx.NO_BORDER)
        newCtrl.SetDocPointer(self.GetDocPointer())     # use the same document
        self.SetupDSScrollBars()
        if self == self._dynSash._view.GetCtrl():  # originally had focus
            wx.CallAfter(self.SetFocus)  # do this to set colors correctly.  wxBug:  for some reason, if we don't do a CallAfter, it immediately calls OnKillFocus right after our SetFocus.


    def OnDSUnify(self, evt):
        self.SetupDSScrollBars()
        self.SetFocus()  # do this to set colors correctly


    def OnDSSBScroll(self, evt):
        # redirect the scroll events from the _dynSash's scrollbars to the STC
        self.GetEventHandler().ProcessEvent(evt)


    def OnDSSBFocus(self, evt):
        # when the scrollbar gets the focus move it back to the STC
        self.SetFocus()


    def DSProcessEvent(self, event):
        # wxHack: Needed for customized right mouse click menu items.        
        if hasattr(self, "_dynSash"):
            if event.GetId() == wx.ID_SELECTALL:
                # force focus so that select all occurs in the window user right clicked on.
                self.SetFocus()

            return self._dynSash._view.ProcessEvent(event)
        return False


    def DSProcessUpdateUIEvent(self, event):
        # wxHack: Needed for customized right mouse click menu items.        
        if hasattr(self, "_dynSash"):
            id = event.GetId()
            if (id == wx.ID_SELECTALL  # allow select all even in non-active window, then force focus to it, see above ProcessEvent
            or id == wx.ID_UNDO
            or id == wx.ID_REDO):
                pass  # allow these actions even in non-active window
            else:  # disallow events in non-active windows.  Cut/Copy/Paste/Delete is too confusing user experience.
                if self._dynSash._view.GetCtrl() != self:
                     event.Enable(False)
                     return True

            return self._dynSash._view.ProcessUpdateUIEvent(event)
        return False

    def SetCaretLineColor(self,color):
        self.SetCaretLineVisible(True)
        self.SetCaretLineBack(color)
        
    def HideLineNumber(self):
        self.SetMarginWidth(self.DEFAULT_LINE_MARKER_NUM, 0)

   