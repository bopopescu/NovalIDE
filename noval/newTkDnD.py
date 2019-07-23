# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        newTkDnD.py
# Purpose:     允许在软件中拖拽打开文件
#
# Author:      wukan
#
# Created:     2019-04-19
# Copyright:   (c) wukan 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import tkinter as tk
import noval.util.utils as utils
import os
import sys
import noval.util.fileutils as fileutils

def _load_tkdnd(master):
    tkdndlib = os.path.normpath(os.path.join(utils.get_app_path(),"tkdnd"))
    if tkdndlib:
        master.tk.eval('global auto_path; lappend auto_path {%s}' % tkdndlib)
    try:
        master.tk.eval('package require tkdnd')
        master._tkdnd_loaded = True
        utils.get_logger().info("load module tkdnd success")
    except tk.TclError as e:
        utils.get_logger().error("load module tkdnd error %s",e)
        master._tkdnd_loaded = False

class TkDND(object):

    def __init__(self, master):
        if not getattr(master, '_tkdnd_loaded', False):
            _load_tkdnd(master)
        self.master = master
        self.tk = master.tk

    def bindtarget(self, window, callback, dndtype, event='<Drop>', priority=50):
        cmd = self._prepare_tkdnd_func(callback)
        return self.tk.call('dnd', 'bindtarget', window, dndtype, event, cmd, priority)

    def bindtarget_query(self, window, dndtype=None, event='<Drop>'):
        return self.tk.call('dnd', 'bindtarget', window, dndtype, event)

    def cleartarget(self, window):
        self.tk.call('dnd', 'cleartarget', window)

    def bindsource(self, window, callback, dndtype, priority=50):
        cmd = self._prepare_tkdnd_func(callback)
        self.tk.call('dnd', 'bindsource', window, dndtype, cmd, priority)

    def bindsource_query(self, window, dndtype=None):
        return self.tk.call('dnd', 'bindsource', window, dndtype)

    def clearsource(self, window):
        self.tk.call('dnd', 'clearsource', window)

    def drag(self, window, actions=None, descriptions=None, cursorwin=None, callback=None):
        cmd = None
        if cursorwin is not None:
            if callback is not None:
                cmd = self._prepare_tkdnd_func(callback)
        self.tk.call('dnd', 'drag', window, actions, descriptions, cursorwin, cmd)
        return

    _subst_format = ('%A', '%a', '%b', '%D', '%d', '%m', '%T', '%W', '%X', '%Y', '%x',
                     '%y')
    _subst_format_str = (' ').join(_subst_format)

    def _prepare_tkdnd_func(self, callback):
        funcid = self.master.register(callback, self._dndsubstitute)
        cmd = '%s %s' % (funcid, self._subst_format_str)
        return cmd

    def _dndsubstitute(self, *args):
        if len(args) != len(self._subst_format):
            return args

        def try_int(x):
            x = str(x)
            try:
                return int(x)
            except ValueError:
                return x

        A, a, b, D, d, m, T, W, X, Y, x, y = args
        event = tk.Event()
        event.action = A
        event.action_list = a
        event.mouse_button = b
        event.data = D
        event.descr = d
        event.modifier = m
        event.dndtype = T
        event.widget = self.master.nametowidget(W)
        event.x_root = X
        event.y_root = Y
        event.x = x
        event.y = y
        event.action_list = str(event.action_list).split()
        for name in ('mouse_button', 'x', 'y', 'x_root', 'y_root'):
            setattr(event, name, try_int(getattr(event, name)))

        return (
         event,)

class FileDropTarget(object):
    def __call__(self, event):
        filenames = self.dndHandler(event.data)
        self.OnDropFiles(event.x,event.y,filenames)
        
    def dndHandler(self,data):
        '''
            解析拖拽的数据,如果文件路径包含空格,则用{}包裹文件吗
            多个文件名以空格分割
        '''
        start_index = data.find('{')
        file_list = []
        while start_index != -1:
            end_index = data.find("}")
            file_name = data[start_index+1:end_index]
            #标准化文件路径格式
            file_list.append(fileutils.opj(file_name))
            data = data.replace("{%s}" % file_name,"")
            start_index = data.find('{')
        left_data = data.strip()
        if left_data != "":
            left_file_list = list(map(fileutils.opj,left_data.split()))
            file_list.extend(left_file_list)
        return file_list
        
    def OnDropFiles(self, x, y, filenames):
        return False
