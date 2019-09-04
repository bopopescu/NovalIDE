# -*- coding: utf-8 -*-
from noval import GetApp,_
import noval.iface as iface
import noval.plugin as plugin
from tkinter import ttk,messagebox
import tkinter as tk
import noval.editor.text as texteditor
import noval.ttkwidgets.textframe as textframe
from noval.python.debugger.commandui import BaseDebuggerUI
import noval.consts as consts

class InspectConsoleTab(ttk.Frame):
    """description of class"""
    def handleCommand(self,event=None):
        cmdStr = self.inputTxt.get()
        if not cmdStr:
            return

        self._cmdList.append(cmdStr)
        self._cmdIndex = len(self._cmdList)
        self.inputTxt.set('')
        
        self.ExecuteCommand(cmdStr)
        return
        
    def ExecuteCommand(self, command):
        GetApp().GetDebugger()._debugger_ui.framesTab.ExecuteCommand(command)

    def OnCmdButtonPressed(self):
        if not BaseDebuggerUI.DebuggerRunning():
            messagebox.showinfo(GetApp().GetAppName(),_("Debugger has been stopped."))
            return
        self.handleCommand()
        
    def AppendText(self,text,tags):
        self._cmdOutput.set_read_only(False)
        self._cmdOutput.intercept_insert("end", text, tags)
        self._cmdOutput.set_read_only(True)

    def OnKeyPressed(self,event):
        key = event.GetKeyCode()
        if key == wx.WXK_RETURN:
            handleCommand()
        elif key == wx.WXK_UP:
            if len(self._cmdList) < 1 or self._cmdIndex < 1:
                return

            self._cmdInput.Clear()
            self._cmdInput.AppendText(self._cmdList[self._cmdIndex - 1])
            self._cmdIndex = self._cmdIndex - 1
        elif key == wx.WXK_DOWN:
            if len(self._cmdList) < 1 or self._cmdIndex >= len(self._cmdList):
                return

            self._cmdInput.Clear()
            self._cmdInput.AppendText(self._cmdList[self._cmdIndex - 1])
            self._cmdIndex = self._cmdIndex + 1
        else:
            event.Skip()
        return

    def OnClrButtonPressed(self):
        self.Clear()
        
    def Clear(self):
        self._cmdOutput.set_read_only(False)
        self._cmdOutput.delete("1.0","end")
        self._cmdOutput.set_read_only(True)
        
    def __init__(self,parent):
        ttk.Frame.__init__(self,parent)
        row = ttk.Frame(self)   
        ttk.Label(row, text= _("Cmd: ")).pack(fill="x",side=tk.LEFT)
        #style wx.TE_PROCESS_ENTER will response enter key
        self.inputTxt = tk.StringVar()
        self._cmdInput  = ttk.Entry(row,textvariable=self.inputTxt)
        self._cmdInput.pack(fill="x",side=tk.LEFT,expand=1)
        ###self._cmdInput.Bind(wx.EVT_TEXT_ENTER,OnCmdButtonPressed)
        cmdButton       = ttk.Button(row, text=_("Execute"),command=self.OnCmdButtonPressed)
        cmdButton.pack(fill="x",side=tk.LEFT)
        clrButton       = ttk.Button(row, text=_("Clear"),command=self.OnClrButtonPressed)
        clrButton.pack(fill="x",side=tk.LEFT)
        
        row.pack(fill="x")
        
        text_frame = textframe.TextFrame(self,borderwidth=0,text_class=texteditor.TextCtrl,font="SmallEditorFont",read_only=True,undo=False)
        self._cmdOutput = text_frame.text
        
        self._cmdOutput.tag_configure(
            "io",
            font="IOFont",
        )
        self._cmdOutput.tag_configure(
            "stdout",
            foreground="Black"
        )
        
        self._cmdOutput.tag_configure(
            "stderr",
            foreground="Red"
        )
        
        self._ui_theme_change_binding = self.bind(
            "<<ThemeChanged>>", self.reload_ui_theme, True
        )
        text_frame.pack(fill="both",expand=1)
      #  wx.EVT_KEY_DOWN(self._cmdInput, OnKeyPressed)
        #回车键发送命令
        self._cmdInput.bind("<Return>",self.handleCommand,True)
        self._cmdList  = []
        self._cmdIndex = 0
        
    def reload_ui_theme(self, event=None):
        self._cmdOutput._reload_theme_options(force=True)

class InspectConsoleViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(consts.INTERACTCONSOLE_TAB_NAME,InspectConsoleTab, _("Interact"), "e",image_file="python/debugger/interact.png")
        
