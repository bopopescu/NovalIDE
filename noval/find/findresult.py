# -*- coding: utf-8 -*-
from noval import GetApp,_
import os
import tkinter as tk
from tkinter import messagebox
import noval.iface as iface
import noval.plugin as plugin
import noval.consts as consts
from tkinter import ttk
import noval.editor.text as texteditor
from noval.find.findindir import FILENAME_MARKER,PROJECT_MARKER,FILE_MARKER,FindIndirService
import noval.ttkwidgets.textframe as textframe
import noval.ui_base as ui_base
import noval.util.utils as utils

class FindResultsview(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        #设置查找结果文本字体为小一号的字体并且控件为只读状态
        text_frame = textframe.TextFrame(self,borderwidth=0,text_class=texteditor.TextCtrl,font="SmallEditorFont",read_only=True,undo=False)
        self.text = text_frame.text
        text_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.text.bind("<Double-Button-1>", self.OnJumptoFoundLine, "+")
        self._ui_theme_change_binding = self.bind(
            "<<ThemeChanged>>", self.reload_ui_theme, True
        )
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
    def destroy(self):
        self.unbind("<<ThemeChanged>>")
        ttk.Frame.destroy(self)

    def reload_ui_theme(self, event=None):
        self.text._reload_theme_options(force=True)
        
    def AddLine(self,line_text):
        #只读状态时无法写入数据需要先解除只读
        self.text.set_read_only(False)
        #linux系统下windows换行符会显示乱码,故统一成linux换行符
        if utils.is_linux():
            line_text = line_text.strip()
        #"1.0"表示在文本最开头插入,end表示在文件末尾插入
        self.text.insert(tk.END, line_text)
        if not line_text.endswith("\n"):
            self.text.insert(tk.END,"\n")
        #写入数据完后必须恢复只读
        self.text.set_read_only(True)

    def ClearLines(self):
        #只读状态时无法删除数据需要先解除只读
        self.text.set_read_only(False)
        self.text.delete('1.0','end')
        self.text.set_read_only(True)
        
    def OnJumptoFoundLine(self, event=None, defLineNum=-1):
        if 0 == self.text.GetCurrentLine():
            return
        if defLineNum == -1:
            defLineNum = self.text.GetCurrentLine()
  
        lineText = self.text.GetLineText(defLineNum)
        #忽略查找结果框第一行,第一行不是查找结果
        if lineText == "\n" or lineText.find(FILENAME_MARKER) != -1 or lineText.find(PROJECT_MARKER) != -1 or lineText.find(FILE_MARKER) != -1 or defLineNum == 1:
            return
        lineEnd = lineText.find(":")
        #忽略最后一行
        if lineEnd == -1:
            return
        else:
            lineNum = int(lineText[0:lineEnd].replace(FindIndirService.LINE_PREFIX ,"").strip())
        filename = self.GetDefineFilename(defLineNum)
        foundDoc = GetApp().GetDocumentManager().GetDocument(filename)
        foundView = None
        if not foundDoc:
            if not os.path.exists(filename):
                messagebox.showerror(_("Open File Error"),_("The file '%s' doesn't exist and couldn't be opened!") % filename)
                return
        GetApp().GotoView(filename,lineNum,load_outline=False)
		
    def GetTextLineEndPosition(self,linenum):
        pos = 0
        for iline in range(linenum):
            col = self.text.index("%d.end" % (iline+1)).split(".")[1]
            pos += int(col)
        return pos

    def GetDefineFilename(self,defLineNum):        
        while defLineNum >0:
            lineText = self.text.GetLineText(defLineNum)
            if lineText.find(FILENAME_MARKER) != -1 and lineText.find(FindIndirService.LINE_PREFIX) == -1:
                filename = lineText.replace(FILENAME_MARKER,"").strip()
                return filename
            defLineNum -=1
        return None
        
    def ScrolltoEnd(self):
        self.text.ScrolltoEnd()
        
class FindResultsviewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(consts.SEARCH_RESULTS_VIEW_NAME,FindResultsview, _("Search Results"), "s",\
                        image_file="search.ico",default_position_key=2)
