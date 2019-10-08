# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        logview.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-09-03
# Copyright:   (c) wukan 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from noval import GetApp,_,NewId
import os
import sys
import logging
#from noval.util.logger import app_debugLogger
import tkinter as tk
from tkinter import ttk
import noval.editor.text as texteditor
import noval.util.utils as utils
import noval.toolbar as toolbar
import noval.ttkwidgets.textframe as textframe

class LogCtrl(texteditor.TextCtrl):
    def __init__(self, parent,**kwargs):
        texteditor.TextCtrl.__init__(self, parent,**kwargs)

    def SetViewDefaults(self):
        """ Needed to override default """
        pass

    def ClearAll(self):
        self.delete("1.0","end")
                    
class LogView(ttk.Frame):
    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------
    ID_SETTINGS = NewId()
    ID_CLEAR = NewId()
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.textCtrl = None
        self._loggers = []
        self._CreateControl()
            
    def _CreateControl(self):
        self._tb = toolbar.ToolBar(self,orient=tk.HORIZONTAL)
        self._tb.pack(fill="x",expand=0)
        self._tb.AddLabel(text=_("Logger Name:"))
        
        self.logCtrl = self._tb.AddCombox()
        self.logCtrl['values'] = self._loggers
        self.logmameVar = tk.StringVar()
        self.logCtrl['textvariable'] = self.logmameVar
        self.logCtrl.bind("<<ComboboxSelected>>",self.OnLogChoice)
        
        self._tb.AddLabel(text=_("Logger Level:"))
        
      #  self._tb.AddButton(self.ID_SETTINGS,None,_("Settings"),handler=self.OnSettingsClick,style=None)
        log_levels = ['',logging.getLevelName(logging.INFO),\
                      logging.getLevelName(logging.WARN),logging.getLevelName(logging.ERROR),logging.getLevelName(logging.CRITICAL)]
        self.loglevelCtrl = self._tb.AddCombox()
        self.loglevelVar = tk.StringVar()
        self.loglevelCtrl['textvariable'] = self.loglevelVar
        self.loglevelCtrl['values'] = log_levels
        self.loglevelCtrl.bind("<<ComboboxSelected>>",self.OnLogLevelChoice)
        
        self._tb.AddButton(self.ID_CLEAR,None,("Clear"),handler=self.ClearLines,style=None)
        text_frame = textframe.TextFrame(self,text_class=LogCtrl,undo=False)
        self.textCtrl = text_frame.text
        self.log_ctrl_handler = LogCtrlHandler(self)
        #屏蔽debug日志,由于日志窗口不支持多线程写入,但是很多多线程中包含debug日志,故屏蔽debug日志
        self.log_ctrl_handler.setLevel(logging.INFO)
        
        #logging.getLogger() is root logger,add log ctrl handler to root logger
        #then other logger will output log to the log view
        self.textCtrl.set_read_only(True)
        text_frame.pack(fill="both",expand=1)
        logging.getLogger().addHandler(self.log_ctrl_handler)
      
    def OnSettingsClick(self):  
        import LoggingConfigurationService
        dlg = LoggingConfigurationService.LoggingOptionsDialog(wx.GetApp().GetTopWindow())
        dlg.ShowModal()
        
    def OnDoubleClick(self, event):
        # Looking for a stack trace line.
        lineText, pos = self.textCtrl.GetCurLine()
        fileBegin = lineText.find("File \"")
        fileEnd = lineText.find("\", line ")
        lineEnd = lineText.find(", in ")
        if lineText == "\n" or  fileBegin == -1 or fileEnd == -1 or lineEnd == -1:
            # Check the line before the one that was clicked on
            lineNumber = self.textCtrl.GetCurrentLine()
            if(lineNumber == 0):
                return
            lineText = self.textCtrl.GetLine(lineNumber - 1)
            fileBegin = lineText.find("File \"")
            fileEnd = lineText.find("\", line ")
            lineEnd = lineText.find(", in ")
            if lineText == "\n" or  fileBegin == -1 or fileEnd == -1 or lineEnd == -1:
                return

        filename = lineText[fileBegin + 6:fileEnd]
        lineNum = int(lineText[fileEnd + 8:lineEnd])

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
            foundView.Activate()
            foundView.GetFrame().SetFocus()
            foundView.GotoLine(lineNum)
            startPos = foundView.PositionFromLine(lineNum)
            lineText = foundView.GetCtrl().GetLine(lineNum - 1)
            foundView.SetSelection(startPos, startPos + len(lineText.rstrip("\n")))
            import OutlineService
            wx.GetApp().GetService(OutlineService.OutlineService).LoadOutline(foundView, position=startPos)

    def OnLogChoice(self, event):
        ###wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        logname = self.logmameVar.get()
        if logname == '':
            self.log_ctrl_handler.ClearFilters()
        else:
            filter = logging.Filter(logname)
            self.log_ctrl_handler.addFilter(filter)
        ###wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            
    def OnLogLevelChoice(self,event):
        log_level_name = self.loglevelVar.get()
        if log_level_name == '':
            self.log_ctrl_handler.setLevel(logging.NOTSET)
        else:
            log_level = logging._checkLevel(log_level_name)
            self.log_ctrl_handler.setLevel(log_level)
    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------

    def ClearLines(self):
        self.textCtrl.set_read_only(False)
        self.textCtrl.ClearAll()
        self.textCtrl.set_read_only(True)

    def AddLine(self,text,log_level):
        #只读状态时无法写入数据需要先解除只读
        self.textCtrl.set_read_only(False)
        #linux系统下windows换行符会显示乱码,故统一成linux换行符
        if utils.is_linux():
            line_text = text.strip()
        #"1.0"表示在文本最开头插入,end表示在文件末尾插入
        self.textCtrl.insert(tk.END, text)
        if not text.endswith("\n"):
            self.textCtrl.insert(tk.END,"\n")
        #写入数据完后必须恢复只读
        self.textCtrl.set_read_only(True)

    #----------------------------------------------------------------------------
    # Callback Methods
    #----------------------------------------------------------------------------
    def AddLogger(self,name):
        if name not in self._loggers:
            self._loggers.append(name)
        self.logCtrl['values'] = self._loggers

class LogCtrlHandler(logging.Handler):
    
    def __init__(self, log_view):
        logging.Handler.__init__(self)
        self._log_view = log_view
        
        self.setLevel(logging.DEBUG)
        self.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s"))
        
    def emit(self, record):
        level = record.levelno
        msg = self.format(record)
        self._log_view.AddLogger(record.name)
        self._log_view.AddLine(msg + os.linesep ,level)
        
    def ClearFilters(self):
        self.filters = []
        
    def addFilter(self, filter):
        self.ClearFilters()
        logging.Handler.addFilter(self,filter)
        