# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        toolbar.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-16
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
import noval.misc as misc
from noval.menu import MenubarMixin
import noval.ui_base as ui_base
import noval.consts as consts
import noval.util.utils as utils

class ToolBar(ui_base.DockFrame):
    toolbar_group = 100
    def __init__(self,parent,orient = tk.HORIZONTAL):
        ui_base.DockFrame.__init__(self,consts.DEFAULT_TOOL_BAR_ROW, parent,show=self.IsDefaultShown())
        #padx设置工具栏左边距
      #  self.grid(column=0, row=0, sticky=tk.EW, padx=0, pady=(5, 0))
        self._orient = orient
        self._commands = []
        
    def CreateSlave(self):
        slaves = self.grid_slaves(0, self.toolbar_group)
        if len(slaves) == 0:
            group_frame = ttk.Frame(self)
            padx = (0, 10)
            group_frame.grid(row=0, column=self.toolbar_group, padx=padx)
        else:
            group_frame = slaves[0]
        return group_frame

    def AddButton(self,command_id,image,command_label,handler,accelerator=None,tester=None,pos=-1,style="Toolbutton"):
        group_frame = self.CreateSlave()
        button = ttk.Button(
            group_frame,
            command=handler,
            image=image,
            style=style,##设置样式为Toolbutton(工具栏按钮),如果该参数为空,则button样式为普通button,不是工具栏button,边框有凸起
            state=tk.NORMAL,
            compound=None,
            pad=None,
        )
        if style is None:
            button.configure(text=command_label)
        self.SetControlPos(command_id,button,pos)
        button.tester = tester
        tooltip_text = MenubarMixin.FormatMenuName(command_label)
        if accelerator:
            tooltip_text += " (" + accelerator + ")"
        misc.create_tooltip(button, tooltip_text)

    def IsDefaultShown(self):
        toolbar_key = self.GetToolbarKey()
        return utils.profile_get_int(toolbar_key,False)
        
    def GetToolbarKey(self):
        return consts.FRAME_VIEW_VISIBLE_KEY % "toolbar"
        
    def Update(self):
        if not self.winfo_ismapped():
           return
        for group_frame in self.grid_slaves(0):
            for button in group_frame.grid_slaves():
                if isinstance(button,ttk.Button):
                    if button.tester and not button.tester():
                        button["state"] = tk.DISABLED
                    else:
                        button["state"] = tk.NORMAL
        
    def AddCombox(self,pos=-1):
        group_frame = self.CreateSlave()
        combo = ttk.Combobox(group_frame)
        self.SetControlPos(-1,combo,pos)
        combo.state(['readonly'])
        return combo

    def AddLabel(self,text,pos=-1):
        group_frame = self.CreateSlave()
        label = ttk.Label(group_frame,text=text)
        self.SetControlPos(-1,label,pos)

    def SetControlPos(self,command_id,ctrl,pos):
        '''
            pos为-1表示在最后添加控件,不为-1表示在某个位置插入控件
        '''
        update_layout = False
        if pos == -1:
            pos = len(self._commands)
            self._commands.append([command_id,ctrl])
        #这里要插入控件,插入控件后需要重新排列控件
        else:
            update_layout = True
            self._commands.insert(pos,[command_id,ctrl])

        if self._orient == tk.HORIZONTAL:
            ctrl.grid(row=0,column=pos)
        elif self._orient == tk.VERTICAL:
            ctrl.grid(row=pos,column=0)
        
        if update_layout:
            #重新调整控件的位置
            self.UpdateLayout(pos)

    def UpdateLayout(self,pos):
        for i,data in enumerate(self._commands):
            ctrl = data[1]
            #所有位置大于pos的控件都需要重新排列
            if i>pos:
                if self._orient == tk.HORIZONTAL:
                    ctrl.grid(row=0,column=i)
                elif self._orient == tk.VERTICAL:
                    ctrl.grid(row=i,column=0)

    def AddSeparator(self):
        slaves = self.grid_slaves(0, self.toolbar_group)
        group_frame = slaves[0]
        separator = ttk.Separator (group_frame, orient = tk.VERTICAL)
        pos = len(self._commands)
        separator.grid(row=0,column=pos,sticky=tk.NSEW, padx=0, pady=3)
        self._commands.append([None,separator])
        return separator
        
    def EnableTool(self,button_id,enable=True):
        for command_button in self._commands:
            if command_button[0] == button_id:
                button = command_button[1]
                if enable:
                    button["state"] = tk.NORMAL
                else:
                    button["state"] = tk.DISABLED