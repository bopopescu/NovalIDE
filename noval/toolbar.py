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
from noval.menu import MenuBar
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

    def AddButton(self,command_id,image,command_label,handler,accelerator=None,tester=None):
        
        slaves = self.grid_slaves(0, self.toolbar_group)
        if len(slaves) == 0:
            group_frame = ttk.Frame(self)
            padx = (0, 10)
            group_frame.grid(row=0, column=self.toolbar_group, padx=padx)
        else:
            group_frame = slaves[0]

        button = ttk.Button(
            group_frame,
            command=handler,
            image=image,
            style="Toolbutton",##设置样式为Toolbutton(工具栏按钮),如果该参数为空,则button样式为普通button,不是工具栏button,边框有凸起
            state=tk.NORMAL,
            compound=None,
            pad=None,
        )
        if self._orient == tk.HORIZONTAL:
            button.pack(side=tk.LEFT)
        elif self._orient == tk.VERTICAL:
            button.pack(side=tk.TOP)
        button.tester = tester
        tooltip_text = MenuBar.FormatMenuName(command_label)
        if accelerator:
            tooltip_text += " (" + accelerator + ")"
        misc.create_tooltip(button, tooltip_text)
        self._commands.append([command_id,button])

    def IsDefaultShown(self):
        toolbar_key = self.GetToolbarKey()
        return utils.profile_get_int(toolbar_key,False)
        
    def GetToolbarKey(self):
        return consts.FRAME_VIEW_VISIBLE_KEY % "toolbar"
        
    def Update(self):
        if not self.winfo_ismapped():
           return
        for group_frame in self.grid_slaves(0):
            for button in group_frame.pack_slaves():
                if isinstance(button,ttk.Button):
                    if button.tester and not button.tester():
                        button["state"] = tk.DISABLED
                    else:
                        button["state"] = tk.NORMAL
        
    def AddCombox(self):
        slaves = self.grid_slaves(0, self.toolbar_group)
        group_frame = slaves[0]
        combo = ttk.Combobox(group_frame)
        combo.pack(side=tk.LEFT)
        combo.state(['readonly'])
        return combo
        
    def AddSeparator(self):
        slaves = self.grid_slaves(0, self.toolbar_group)
        group_frame = slaves[0]
        separator = ttk.Separator (group_frame, orient = tk.VERTICAL)
        separator.pack(side=tk.LEFT,expand=1,fill="y",pady = 3)
        return separator
        
    def EnableTool(self,button_id,enable=True):
        for command_button in self._commands:
            if command_button[0] == button_id:
                button = command_button[1]
                if enable:
                    button["state"] = tk.NORMAL
                else:
                    button["state"] = tk.DISABLED