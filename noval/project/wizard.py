# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Wizard.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-11
# Copyright:   (c) wukan 2019
# Licence:      GPL-3.0
#-------------------------------------------------------------------------------
from noval import _,GetApp
import tkinter as tk
from tkinter import ttk
from noval.consts import DEFAUT_CONTRL_PAD_X,DEFAUT_CONTRL_PAD_Y
import noval.ui_base as ui_base
import tkinter.font as tk_font
import noval.imageutils as imageutils
from noval.util import utils
import noval.consts as consts

class BaseWizard(ui_base.CommonModaldialog):
    def __init__(self, master):
        ui_base.CommonModaldialog.__init__(self, master)
        self.current_page = None
        self.content_page = ttk.Frame(self)
        self.content_page.grid(column=0, row=0, sticky=tk.NSEW, padx=0, pady=0)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        bottom_page = ttk.Frame(self)
        space_label = ttk.Label(bottom_page,text="")
        space_label.grid(column=0, row=0, sticky=tk.EW, padx=(DEFAUT_CONTRL_PAD_X, DEFAUT_CONTRL_PAD_X), pady=DEFAUT_CONTRL_PAD_Y)
        self.prev_button = ttk.Button(bottom_page, text=_("<Previous"), command=self.GotoPrevPage)
        self.prev_button.grid(column=1, row=0, sticky=tk.EW, padx=(DEFAUT_CONTRL_PAD_X, DEFAUT_CONTRL_PAD_X), pady=DEFAUT_CONTRL_PAD_Y)
        self.next_button = ttk.Button(bottom_page, text=_("Next>"), command=self.GotoNextPage)
        self.next_button.grid(column=2, row=0, sticky=tk.EW, padx=(0, DEFAUT_CONTRL_PAD_X), pady=DEFAUT_CONTRL_PAD_Y)
        
        self.ok_button = ttk.Button(bottom_page, text=_("Finish"), command=self._ok,default=tk.ACTIVE)
        self.ok_button.grid(column=3, row=0, sticky=tk.EW, padx=(0, DEFAUT_CONTRL_PAD_X), pady=DEFAUT_CONTRL_PAD_Y)
        self.cancel_button = ttk.Button(bottom_page, text=_("Cancel"), command=self._cancel)
        self.cancel_button.grid(column=4, row=0, sticky=tk.EW, padx=(0, DEFAUT_CONTRL_PAD_X), pady=DEFAUT_CONTRL_PAD_Y)
        bottom_page.grid(column=0, row=1, sticky=tk.EW, padx=0, pady=0)
        bottom_page.columnconfigure(0, weight=1)
        self.bind("<Return>", self._ok, True)

    def SetPrevNext(self, prev, next):
        prev.SetNext(next)
        next.SetPrev(prev)
        
    def RunWizard(self, firstPage):
        '''
            显示向导对话框并显示第一个页面
        '''
        self.firstPage = firstPage
        self.current_page = self.firstPage 
        self.title(self.firstPage.title)
        self.ShowModal()
        
    def _ok(self, event=None):
        #ok按钮处于不可用状态时无法执行回车键操作
        if str(self.ok_button['state']) == tk.DISABLED:
            return
        if not self.current_page.Validate():
            return
            
        #从第一页开始调用每个页面的Finish方法
        next = self.firstPage.GetNext()
        while next:
            if not next.Finish():
                return
            next = next.GetNext()
        self.destroy()
        
    def _cancel(self, event=None):
        #向每一级页面通知Cancel
        next = self.firstPage.GetNext()
        while next:
            next.Cancel()
            next = next.GetNext()
        self.destroy()
        
    def FitToPage(self,page):
        '''
            更换页面
        '''
        if self.current_page is not None:
            self.current_page.pack_forget()
        page.pack(expand=1, fill="both")
        
    def GotoNextPage(self):
        '''
            显示下一页页面
        '''
        if not self.current_page.Validate():
            return
        next = self.current_page.GetNext()
        if next is None:
            self.UpdateNext(self.current_page)
            return
        self.FitToPage(next)
        self.SetTitle(next)
        self.current_page = next
        self.UpdateNext(self.current_page)
        self.prev_button["state"] = "normal"
        self.SetFinish(self.current_page.CanFinish())
        
    def GotoPrevPage(self):
        '''
            显示上一页页面
        '''
        prev = self.current_page.GetPrev()
        if prev is None:
            self.UpdatePrev(self.current_page)
            return
        self.FitToPage(prev)
        self.SetTitle(prev)
        self.current_page = prev
        self.UpdatePrev(self.current_page)
        self.next_button["state"] = "normal"
        self.SetFinish(self.current_page.CanFinish())
        
    def SetTitle(self,page):
        '''
            设置向导对话框标题
        '''
        title = page.title
        if not title:
            title = self.firstPage.title
        self.title(title)
        
    def SetFinish(self,can_finish=True):
        '''
            该页面是否允许完成操作
        '''
        if can_finish:
            self.ok_button["state"] = "normal"
        else:
            self.ok_button["state"] = tk.DISABLED
            
    def UpdateNext(self,cur_page):
        '''
            该页面是否有下一个页面来更新下一个按钮状态
        '''
        next = cur_page.GetNext()
        if next is None:
            self.next_button["state"] = tk.DISABLED
            return
        self.next_button["state"] = "normal"

    def UpdatePrev(self,cur_page):
        '''
            该页面是否有上一个页面来更新上一个按钮状态
        '''
        prev = cur_page.GetPrev()
        if prev is None:
            self.prev_button["state"] = tk.DISABLED
            return
        self.prev_button["state"] = "normal"

class TitledWizardPage(ttk.Frame):
    def __init__(self, master,title):
        ttk.Frame.__init__(self,master=master.content_page)
        self.title = title
        self.next = self.prev = None
        self.can_finish = True

    def SetNext(self, next):
        self.next = next

    def SetPrev(self, prev):
        self.prev = prev

    def GetNext(self):
        return self.next

    def GetPrev(self):
        return self.prev
        
    def Validate(self):
        return True
        
    def CanFinish(self):
        return self.can_finish
        
    def Cancel(self):
        '''
            取消按钮事件,默认不处理,如果要处理取消事件,需要在派生类继承并重写该方法
        '''
        pass
        
class BitmapTitledWizardPage(TitledWizardPage):
    '''
        显示标题和图标的通用页面
    '''
    def __init__(self, master,title,label,bitmap):
        TitledWizardPage.__init__(self,master=master,title=title)
        self.img = imageutils.load_image("",bitmap)
        #标题大号字体
        wizard_title_font = tk_font.Font(
            name="WizardFont",
            family=utils.profile_get(consts.EDITOR_FONT_FAMILY_KEY,GetApp().GetDefaultEditorFamily()),
            weight="bold",
            size=14,
        )
        #创建向导标题框
        labels = label.split("\n")
        show_text = labels[0]
        title_frame = ttk.Frame(self)
        title_frame.grid(column=0, row=0, sticky="ew",padx=DEFAUT_CONTRL_PAD_X)
        
        label_frame = ttk.Frame(title_frame)
        label_frame.pack(side=tk.LEFT,fill="x",expand=1)
        #设置标题的大号字体
        label_ctrl = ttk.Label(label_frame,text=show_text,font=wizard_title_font)
        label_ctrl.pack(fill="x",expand=1)
        #如果标题内容包含换行符,则创建一个小号的文本标签
        if len(labels) > 1:
            detail_text = labels[1]
            detail_text_ctrl = ttk.Label(label_frame,text=detail_text)
            #缩进小号的文本
            detail_text_ctrl.pack(fill="x",expand=1,padx=DEFAUT_CONTRL_PAD_X)
        #标题框图标
        img_ctrl = ttk.Label(title_frame,image=self.img,compound=tk.RIGHT)
        img_ctrl.pack(side=tk.LEFT)
        self.can_finish = False
        

class BitmapTitledContainerWizardPage(BitmapTitledWizardPage):
    '''
        显示标题和图标以及包含上下分隔符的通用页面
    '''
    def __init__(self, master,title,label,bitmap,**kwargs):
        BitmapTitledWizardPage.__init__(self,master,title,label,bitmap)
        
        #创建顶部分隔符
        top = ttk.Frame(self)
        top.grid(column=0, row=1, sticky="nsew")
        separator = ttk.Separator(top, orient = tk.HORIZONTAL)
        separator.pack(side=tk.LEFT,fill="x",expand=1)
        
        #创建向导框内容
        content_frame = ttk.Frame(self)
        #设置内容框左右间隔
        content_frame.grid(column=0, row=2, sticky="nsew",padx=DEFAUT_CONTRL_PAD_X)
        self.CreateContent(content_frame,**kwargs)
        content_frame.columnconfigure(0, weight=1)
        
        #创建底部分隔符
        bottom = ttk.Frame(self)
        bottom.grid(column=0, row=3, sticky="nsew",pady=(2*consts.DEFAUT_CONTRL_PAD_Y,0))
        separator = ttk.Separator(bottom, orient = tk.HORIZONTAL)
        separator.pack(side=tk.LEFT,fill="x",expand=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

    def CreateContent(self,content_frame,**kwargs):
        pass
