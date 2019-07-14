# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from noval import _,NewId,GetApp
import noval.editor.text as texteditor
import noval.find.findtext as findtext
import noval.find.find as finddialog
import noval.ui_base as ui_base
import noval.util.apputils as apputils
import os
import noval.constants as constants
import noval.consts as consts
import noval.util.strutils as strutils

class OutputCtrl(texteditor.TextCtrl,findtext.FindTextEngine):
    '''
        调式输出控件同时兼顾查找功能
    '''
    TEXT_WRAP_ID = NewId()
    EXPORT_TEXT_ID = NewId()
  
    def __init__(self, parent,is_debug=False,**kwargs):
        texteditor.TextCtrl.__init__(self, parent,**kwargs)
        findtext.FindTextEngine.__init__(self)
        self._first_input = True
        self._input_start_pos = 0
        self._executor = None
        self._is_debug = is_debug
   #     wx.EVT_SET_FOCUS(self, self.OnFocus)
        self.bind('<Double-Button-1>',self.OnDoubleClick)
        
     #   wx.stc.EVT_STC_MODIFIED(self, self.GetId(), self.OnModify)    
      #  wx.EVT_KEY_DOWN(self, self.OnKeyPressed)
      
        self.tag_configure(
            "io",
            font="IOFont",
        )
        
        self.tag_configure(
            "stdin",
            foreground="Blue"
        )
        
        self.tag_configure(
            "stdout",
            foreground="Black"
        )
        
        self.tag_configure(
            "stderr",
            foreground="Red"
        )
        self._is_wrap = tk.IntVar(value=False)
        self.SetWrap()
            
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
        texteditor.TextCtrl.CreatePopupMenu(self)
        self._popup_menu.add_separator()
        self._popup_menu.Append(self.TEXT_WRAP_ID,_("Word Wrap"),kind=consts.CHECK_MENU_ITEM_KIND,handler=self.SetWrap,variable=self._is_wrap)
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(constants.ID_FIND),handler=self.DoFind,tester=None)
        self._popup_menu.Append(self.EXPORT_TEXT_ID, _("Export All"),handler=self.SaveAll)
        

    def DoFind(self):
        finddialog.ShowFindReplaceDialog(self)
            
    def OnFocus(self, event):
        self.ActiveDebugView()
        event.Skip()
        
    def SetWrap(self):
        if self._is_wrap.get():
            self.configure(**{'wrap':'char'})
        else:
            self.configure(**{'wrap':'none'})
        
    def ActiveDebugView(self):
        if not self._is_debug:
            wx.GetApp().GetDocumentManager().ActivateView(self.GetParent()._service.GetView())
        else:
            wx.GetApp().GetDocumentManager().ActivateView(self.GetParent().GetParent().GetParent()._service.GetView())
        
    def ClearOutput(self):
        self.set_read_only(False)
        self.delete("1.0","end")
        self.set_read_only(True)
        
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
        text_docTemplate = GetApp().GetDocumentManager().FindTemplateForPath("test.txt")
        default_ext = text_docTemplate.GetDefaultExtension()
        descrs = strutils.get_template_filter(text_docTemplate)
        filename = filedialog.asksaveasfilename(
            master = self,
            filetypes=[descrs],
            defaultextension=default_ext,
            initialdir=text_docTemplate.GetDirectory(),
            initialfile="outputs.txt"
        )
        if filename == "":
            return
        try:
            with open(filename,"wb") as f:
                f.write(self.GetValue())
        except Exception as e:
            messagebox.showerror(_("Error"),str(e))

    def OnDoubleClick(self, event):
        # Looking for a stack trace line.
        line, col = self.GetCurrentLineColumn()
        lineText = self.GetLineText(line)
        fileBegin = lineText.find("File \"")
        fileEnd = lineText.find("\", line ")
        lineEnd = lineText.find(", in ")
        if lineText == "\n" or  fileBegin == -1 or fileEnd == -1:
            # Check the line before the one that was clicked on
            lineNumber = self.GetCurrentLine()
            if(lineNumber == 0):
                return
            lineText = self.GetLineText(lineNumber - 1)
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
        GetApp().GotoView(filename,lineNum,load_outline=False)
        #last activiate debug view
        self.ActiveDebugView()

    def AppendText(self, text,last_readonly=False):
        self.set_read_only(False)
        self.AddText(text)
        self.ScrolltoEnd()
        #rember last position
        self.InputStartPos = self.GetCurrentPos()
        if last_readonly:
            self.SetReadOnly(True)

    def AddText(self,txt):
        self.insert(tk.END, txt)

    def AppendErrorText(self, text,last_readonly=False):
        self.set_read_only(False)
        tags = ("io",'stderr')
        texteditor.TextCtrl.intercept_insert(self, "insert", text, tags)
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
        

class OutputView(ttk.Frame):
    def __init__(self, master,is_debug=False):
        ttk.Frame.__init__(self, master)
        self.vert_scrollbar = ui_base.SafeScrollbar(self, orient=tk.VERTICAL)
        self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)
        #设置查找结果文本字体为小一号的字体并且控件为只读状态
        self.text = OutputCtrl(self,is_debug,font="SmallEditorFont",read_only=True,yscrollcommand=self.vert_scrollbar.set,borderwidth=0)
        self.text.grid(row=0, column=0, sticky=tk.NSEW)
        self.text.bind("<Double-Button-1>", self.JumptoLine, "+")
        #关联垂直滚动条和文本控件
        self.vert_scrollbar["command"] = self.text.yview
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        

    def JumptoLine(self,event):
        pass
        
    def SetExecutor(self,executor):
        self.text.SetExecutor(executor)
        
    def GetOutputCtrl(self):
        return self.text