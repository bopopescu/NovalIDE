#----------------------------------------------------------------------------
# Name:         LogWindowService.py
# Purpose:      Console output service
#
# Author:       Matt Fryer
#
# Created:      9/2/04
# CVS-ID:       $Id: LogWindowService.py 9342 2006-03-25 00:17:36Z mfryer $
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import os
import sys
import threading
import cStringIO
import wx
import logging
import re
import noval.tool.service.Service as Service
import noval.tool.BaseCtrl as BaseCtrl
import LogHandler
import  wx.lib.newevent
from noval.util.logger import app_debugLogger
import noval.util.WxThreadSafe as WxThreadSafe
from noval.tool.consts import SPACE,HALF_SPACE,_ 

_ = wx.GetTranslation
_VERBOSE = False
MAX_LINE_LENGTH = 256
(LogTextEvent, EVT_LOG_TEXT) = wx.lib.newevent.NewEvent()


class LogWindowCtrl(wx.Panel):
    def __init__(self, parent, id, service):
        wx.Panel.__init__(self, parent, id)
        self.NO_CLOSE = True
        self.SERVICE = service
        

class LogCtrl(BaseCtrl.ScintillaCtrl):
    def __init__(self, parent, id):
        BaseCtrl.ScintillaCtrl.__init__(self, parent, id)


    def SetViewDefaults(self):
        """ Needed to override default """
        pass

                    
class LogView(Service.TabbedServiceView):
    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self, service):
        Service.TabbedServiceView.__init__(self, service)
        self.textCtrl = None
        self._loggers = [' ' * 30]
        
    def DoPollLogger(self):
        if self.currentLogReader:
            self.currentLogReader.SendTextToCallback()
            
        
    def _CreateControl(self, parent, id):
        panel = LogWindowCtrl(parent, id, self._service)
        sizer = wx.BoxSizer(wx.VERTICAL)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(buttonSizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, HALF_SPACE)
        buttonSizer.Add(wx.StaticText(panel, -1, _("Logger Name:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.logCtrl = wx.Choice(panel, -1, choices=self._loggers)
        wx.EVT_CHOICE(self.logCtrl, self.logCtrl.GetId(), self.OnLogChoice)
        buttonSizer.Add(self.logCtrl, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, HALF_SPACE)
        buttonSizer.Add(wx.StaticText(panel, -1, _("Logger Level:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
      ###  self.settingsButton = wx.Button(panel, -1, "Settings")
        log_levels = ['',logging.getLevelName(logging.DEBUG),logging.getLevelName(logging.INFO),\
                      logging.getLevelName(logging.WARN),logging.getLevelName(logging.ERROR),logging.getLevelName(logging.CRITICAL)]
        self.loglevelCtrl = wx.Choice(panel, -1, choices=log_levels)
        buttonSizer.Add(self.loglevelCtrl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, HALF_SPACE)
        wx.EVT_CHOICE(self.loglevelCtrl, self.loglevelCtrl.GetId(), self.OnLogLevelChoice)
        self.clearButton = wx.Button(panel, -1, _("Clear"))
        buttonSizer.Add(self.clearButton, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, HALF_SPACE)
        wx.EVT_BUTTON(self.clearButton, self.clearButton.GetId(), self.ClearLines)
        self.textCtrl = txtCtrl = LogCtrl(panel, id)
        self.log_ctrl_handler = LogHandler.LogCtrlHandler(self)
        #logging.getLogger() is root logger,add log ctrl handler to root logger
        #then other logger will output log to the log view
        logging.getLogger().addHandler(self.log_ctrl_handler)
        wx.stc.EVT_STC_DOUBLECLICK(self.textCtrl, self.textCtrl.GetId(), self.OnDoubleClick)

        txtCtrl.SetMarginWidth(1, 0)  # hide line numbers
        txtCtrl.SetReadOnly(True)

        if wx.Platform == '__WXMSW__':
            font = "Courier New"
        else:
            font = "Courier"
        txtCtrl.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = font))
        txtCtrl.SetFontColor(wx.BLACK)
        txtCtrl.StyleClearAll()
        txtCtrl.UpdateStyles()
        wx.EVT_SET_FOCUS(txtCtrl, self.OnFocus)

        sizer.Add(txtCtrl, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        sizer.Fit(panel)

        return panel

    def GetTextControl(self):
        return self.textCtrl
        
    def GetDocument(self):
        return None
      
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

    def OnFocus(self, event):
        wx.GetApp().GetDocumentManager().ActivateView(self)
        event.Skip()

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
    
    def ProcessEvent(self, event):
        stcControl = self.GetTextControl()
        if not isinstance(stcControl, LogCtrl):
            return wx.lib.docview.View.ProcessEvent(self, event)
        id = event.GetId()
        if id == wx.ID_COPY:
            stcControl.Copy()
            return True
        elif id == wx.ID_CLEAR:
            stcControl.Clear()
            return True
        elif id == wx.ID_SELECTALL:
            stcControl.SetSelection(0, -1)
            return True


    def ProcessUpdateUIEvent(self, event):
        stcControl = self.GetTextControl()
        if not isinstance(stcControl, LogCtrl):
            return wx.lib.docview.View.ProcessUpdateUIEvent(self, event)
        id = event.GetId()
        if id == wx.ID_CUT or id == wx.ID_PASTE:
            # I don't think cut or paste makes sense from a message/log window.
            event.Enable(False)
            return True
        elif id == wx.ID_COPY:
            hasSelection = (stcControl.GetSelectionStart() != stcControl.GetSelectionEnd()) 
            event.Enable(hasSelection)
            return True
        elif id == wx.ID_CLEAR:
            event.Enable(True)  # wxBug: should be stcControl.CanCut()) but disabling clear item means del key doesn't work in control as expected
            return True
        elif id == wx.ID_SELECTALL:
            event.Enable(stcControl.GetTextLength() > 0)
            return True

        
    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------

    def ClearLines(self, event):
        self.GetTextControl().SetReadOnly(False)
        self.GetTextControl().ClearAll()
        self.GetTextControl().SetReadOnly(True)

    @WxThreadSafe.call_after
    def AddLine(self, text,log_level):
        tc = self.GetTextControl()
        tc.SetReadOnly(False)
        tc.SetCurrentPos(tc.GetTextLength())
        try:
            tc.AddText(text)
        except UnicodeError:
            tc.AddText(text.decode('utf-8', 'replace'))
        tc.SetReadOnly(True)
        tc.ScrollToLine(tc.GetLineCount())

    #----------------------------------------------------------------------------
    # Callback Methods
    #----------------------------------------------------------------------------

    def SetCallback(self, callback=None):
        """ Sets in the event table for a doubleclick to invoke the given callback.
            Additional calls to this method overwrites the previous entry and only the last set callback will be invoked.
        """
        if not callback:
            callback = self.CallbackDummy
        wx.stc.EVT_STC_DOUBLECLICK(self.GetTextControl(), self.GetTextControl().GetId(), callback)


    def CallbackDummy(self, event):
        """ Do nothing, needed to clear out any old callbacks """
        pass
        
    @WxThreadSafe.call_after
    def AddLogger(self,name):
        if name not in self._loggers:
            self._loggers.append(name)
            self.logCtrl.Append(name)

        
class LogService(Service.Service):

    def __init__(self, serviceName="Logs", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM):
        Service.Service.__init__(self, serviceName, embeddedWindowLocation)

    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    SHOW_WINDOW = wx.NewId()  # keep this line for each subclass, need unique ID for each Service


    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def _CreateView(self):
        return LogView(self)



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
