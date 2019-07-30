# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        imageviewer.py
# Purpose:     图片查看器,浏览所有支持图片类型
#
# Author:      wukan
#
# Created:     2019-01-21
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import _,GetApp
import noval.core as core
import sys
import noval.consts as consts
from PIL import Image
from PIL import ImageTk
import tkinter as tk
from tkinter import ttk,messagebox
import noval.constants as constants

class ImageDocument(core.Document):
    pass


class ImageView(core.View):

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self):
        core.View.__init__(self)
        self._ctrl = None

    def OnCreate(self, doc, flags):
        try:
            self._bitmap = ImageTk.PhotoImage(Image.open(doc.GetFilename()))
        except Exception as e:
            messagebox.showerror(_("Open Image File"),_("Error loading '%s'. %s") % (doc.GetPrintableName(), e))
            return False

        frame = GetApp().CreateDocumentFrame(self, doc, flags)
        panel = ttk.Frame(frame)      
        panel.pack(fill="x")
        label = tk.Label(panel, image=self._bitmap,compound='left',anchor=tk.NW)
        label.pack(side=tk.LEFT)
        self.Activate()
        return True


    def OnFocus(self, event):
        self._ctrl.SetFocus()
        event.Skip()

    def OnClose(self, deleteWindow = True):
        self.Activate(False)
        if deleteWindow:
            self.GetFrame().Destroy()
        return True
        
    def OnActivateView(self, activate, activeView, deactiveView):
        if activate and activeView:
            pass
           ### wx.GetApp().MainFrame.GetStatusBar().Reset()
        
    def set_line_and_column(self):
        '''
            图片视图不在状态栏显示行列号
        '''
        GetApp().MainFrame.GetStatusBar().Reset()
        
    def UpdateUI(self, command_id):
        '''
            图片视图只允许关闭菜单有效
        '''
        if command_id in [constants.ID_CLOSE,constants.ID_CLOSE_ALL]:
            return True
        return core.View.UpdateUI(self,command_id)

    def GotoLine(self):
        '''
            图片视图不能跳转到行,实现一个空方法
        '''
        pass

    def ZoomView(self,delta = 0):
        ''''''
        ##TODO 待实现图片的放大缩小
