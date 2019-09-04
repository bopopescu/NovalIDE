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
import noval.util.utils as utils

class CommonOutputctrl(texteditor.TextCtrl,findtext.FindTextEngine):
    '''
        调式输出控件同时兼顾查找功能
    '''
    TEXT_WRAP_ID = NewId()
    EXPORT_TEXT_ID = NewId()
  
    def __init__(self, parent,trace_log=False,**kwargs):
        '''
            trace_log表示是否追踪日志输出,即保存日志输出,方便输出框清空以后查看
        '''
        texteditor.TextCtrl.__init__(self, parent,**kwargs)
        findtext.FindTextEngine.__init__(self)
        self._first_input = True
        self._input_start_pos = 0
        self._executor = None
        self.trace_log = trace_log
        self.bind('<Double-Button-1>',self.OnDoubleClick)
        #鼠标和键盘松开时激活视图
        self.bind("<<ActivateView>>", self.ActivateView)
        self.event_add("<<ActivateView>>","<KeyRelease>","<ButtonRelease>")
        self.bind("<KeyPress>", self.OnChar, True)
        self.bind("<Return>", self.perform_return, True)
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
        self.logs = {}
        self.inputText = ""
        
    def perform_return(self, event):
        self._executor.WriteInput(self.inputText+"\n")
        self.insert("insert", "\n")
        #等待下一次输入,将上一次输入清空
        self.inputText = ""
        return "break"
      
    def OnChar(self, event):
        c = event.char
        self.AddInputTags(c)
        #纪录输入的字符
        self.inputText += c
        return "break"

            
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
                
    def CreatePopupMenu(self):
        texteditor.TextCtrl.CreatePopupMenu(self)
        self.ActivateView()
        self._popup_menu.add_separator()
        self._popup_menu.Append(self.TEXT_WRAP_ID,_("Word Wrap"),kind=consts.CHECK_MENU_ITEM_KIND,handler=self.SetWrap,variable=self._is_wrap)
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(constants.ID_FIND),handler=self.DoFind,tester=None)
        self._popup_menu.Append(self.EXPORT_TEXT_ID, _("Export All"),handler=self.SaveAll)

    def DoFind(self):
        finddialog.ShowFindReplaceDialog(self)
        
    def SetWrap(self):
        if self._is_wrap.get():
            self.configure(**{'wrap':'char'})
        else:
            self.configure(**{'wrap':'none'})
        
    def ActivateView(self,event=None):
        self.focus_set()
        GetApp().GetDocumentManager().ActivateView(GetApp().GetDebugger().GetView())
        
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
            with open(filename,"w") as f:
                f.write(self.GetValue())
        except Exception as e:
            messagebox.showerror(_("Error"),str(e))

    def OnDoubleClick(self, event):
        pass

    def AppendText(self,source,text,last_readonly=False):
        self.set_read_only(False)
        self.AddText(text)
        self.ScrolltoEnd()
        #rember last position
        self.InputStartPos = self.GetCurrentPos()
        if last_readonly:
            self.SetReadOnly(True)
        self.AppendLogs(source,text)

    def SetTraceLog(self,trace_log):
        self.trace_log = trace_log

    def AppendLogs(self,source,txt):
        if not self.trace_log:
            return
        #将日志输出按来源归类保存
        if source in self.logs:
            self.logs[source].append(txt)
        else:
            self.logs[source] = [txt]

    def AddText(self,txt):
        self.insert(tk.END, txt)

    def AppendErrorText(self, source,text,last_readonly=False):
        self.set_read_only(False)
        tags = ("io",'stderr')
        texteditor.TextCtrl.intercept_insert(self, "insert", text, tags)
        if last_readonly:
            self.SetReadOnly(True)
        self.AppendLogs(source,text)

    def OnModify(self,event):
        if self.GetCurrentPos() <= self.InputStartPos:
            #disable back delete key
            self.CmdKeyClear(wx.stc.STC_KEY_BACK ,0)
        else:
            #enable back delete key
            self.CmdKeyAssign(wx.stc.STC_KEY_BACK ,0,wx.stc.STC_CMD_DELETEBACK)
                
    def SetExecutor(self,executor):
        self._executor = executor
        
    def AddInputText(self,text):
        self.set_read_only(False)
        self.AddInputTags(text)
        self.set_read_only(True)
        
    def AddInputTags(self,text):
        '''
            设置输入文本标签,渲染颜色
        '''
        tags = ("io",'stdin')
        texteditor.TextCtrl.intercept_insert(self, "insert", text, tags)
        

class CommononOutputview(ttk.Frame):
    def __init__(self, master,trace_log=False,is_debug=False):
        ttk.Frame.__init__(self, master)
        self.vert_scrollbar = ui_base.SafeScrollbar(self, orient=tk.VERTICAL)
        self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        self.horizontal_scrollbar = ui_base.SafeScrollbar(self, orient=tk.HORIZONTAL)
        self.horizontal_scrollbar.grid(row=1, column=0, sticky=tk.NSEW)

        #设置查找结果文本字体为小一号的字体并且控件为只读状态,inactiveselectbackground表示查找并选择文本时的选中颜色
        #禁止undo操作
        self.text = self.GetOuputctrlClass()(self,font="SmallEditorFont",inactiveselectbackground="gray",read_only=True,yscrollcommand=self.vert_scrollbar.set,\
                                borderwidth=0,undo=False,xscrollcommand=self.horizontal_scrollbar.set,trace_log=trace_log)
        self.text.grid(row=0, column=0, sticky=tk.NSEW)
        
        self._ui_theme_change_binding = self.bind(
            "<<ThemeChanged>>", self.reload_ui_theme, True
        )
        #关联垂直滚动条和文本控件
        self.vert_scrollbar["command"] = self.text.yview
        self.horizontal_scrollbar["command"] = self.text.xview
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
    def SetExecutor(self,executor):
        self.text.SetExecutor(executor)
        
    def GetOutputCtrl(self):
        return self.text

    def GetOuputctrlClass(self):
        return CommonOutputctrl

    def SetTraceLog(self,trace_log):
        self.text.SetTraceLog(trace_log)
        
    def reload_ui_theme(self, event=None):
        self.text._reload_theme_options(force=True)

