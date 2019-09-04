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
from noval import GetApp,_
import os
import sys
import logging
#from noval.util.logger import app_debugLogger
import noval.iface as iface
import noval.plugin as plugin
import noval.consts as consts
import tkinter as tk
from tkinter import ttk
import noval.editor.text as texteditor
import noval.util.utils as utils

class LogCtrl(texteditor.TextCtrl):
    def __init__(self, parent):
        texteditor.TextCtrl.__init__(self, parent)

    def SetViewDefaults(self):
        """ Needed to override default """
        pass

                    
class LogView(ttk.Frame):
    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.textCtrl = None
        self._loggers = [' ' * 30]
        self._CreateControl()
            
    def _CreateControl(self):
        ttk.Label(self, text=_("Logger Name:"))
        self.logCtrl = ttk.Combobox(self, values=self._loggers)
      #  wx.EVT_CHOICE(self.logCtrl, self.logCtrl.GetId(), self.OnLogChoice)
        ttk.Label(self, text=_("Logger Level:"))
      ###  self.settingsButton = wx.Button(panel, -1, "Settings")
        log_levels = ['',logging.getLevelName(logging.DEBUG),logging.getLevelName(logging.INFO),\
                      logging.getLevelName(logging.WARN),logging.getLevelName(logging.ERROR),logging.getLevelName(logging.CRITICAL)]
        self.loglevelCtrl = ttk.Combobox(self, values=log_levels)
#        wx.EVT_CHOICE(self.loglevelCtrl, self.loglevelCtrl.GetId(), self.OnLogLevelChoice)
        self.clearButton = ttk.Button(self, text=_("Clear"),command=self.ClearLines)
        self.textCtrl = txtCtrl = LogCtrl(self)
        self.log_ctrl_handler = LogCtrlHandler(self)
        #logging.getLogger() is root logger,add log ctrl handler to root logger
        #then other logger will output log to the log view
        logging.getLogger().addHandler(self.log_ctrl_handler)
        txtCtrl.set_read_only(True)

    def GetTextControl(self):
        return self.textCtrl
      
    def OnSettingsClick(self, event):  
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
        log = self.logCtrl.GetStringSelection()
        if log.strip() == '':
            self.log_ctrl_handler.ClearFilters()
        else:
            filter = logging.Filter(log)
            self.log_ctrl_handler.addFilter(filter)
        ###wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            
    def OnLogLevelChoice(self,event):
        log_level_name = self.loglevelCtrl.GetStringSelection()
        if log_level_name.strip() == '':
            self.log_ctrl_handler.setLevel(logging.NOTSET)
        else:
            log_level = logging._checkLevel(log_level_name)
            self.log_ctrl_handler.setLevel(log_level)
    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------

    def ClearLines(self, event):
        self.GetTextControl().SetReadOnly(False)
        self.GetTextControl().ClearAll()
        self.GetTextControl().SetReadOnly(True)

    def AddLine(self,text,log_level):
        #只读状态时无法写入数据需要先解除只读
        self.GetTextControl().set_read_only(False)
        #linux系统下windows换行符会显示乱码,故统一成linux换行符
        if utils.is_linux():
            line_text = text.strip()
        #"1.0"表示在文本最开头插入,end表示在文件末尾插入
        self.GetTextControl().insert(tk.END, text)
        if not text.endswith("\n"):
            self.GetTextControl().insert(tk.END,"\n")
        #写入数据完后必须恢复只读
        self.GetTextControl().set_read_only(True)

    #----------------------------------------------------------------------------
    # Callback Methods
    #----------------------------------------------------------------------------
    def AddLogger(self,name):
        if name not in self._loggers:
            self._loggers.append(name)
          #  self.logCtrl.Append(name)

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

class LogViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView("Logs",LogView, _("Logs"), "s",default_position_key=3)