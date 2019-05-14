# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        misc.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-16
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp,NewId,_
from tkinter import ttk
import tkinter as tk
import noval.util.strutils as strutils
from PIL import Image
from PIL import ImageTk
import noval.consts as consts
from noval.util import utils
import noval.core as core
import os

def get_style_configuration(style_name, default={}):
    style = ttk.Style()
    # NB! style.configure seems to reuse the returned dict
    # Don't change it without copying first
    result = style.configure(style_name)
    if result is None:
        return default
    else:
        return result
        

def lookup_style_option(style_name, option_name, default=None):
    style = ttk.Style()
    setting = style.lookup(style_name, option_name)
    if setting in [None, ""]:
        return default
    elif setting == "True":
        return True
    elif setting == "False":
        return False
    else:
        return setting
        

class ToolTip:
    """Taken from http://www.voidspace.org.uk/python/weblog/arch_d7_2006_07_01.shtml"""

    def __init__(self, widget, options):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.options = options

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        try:
            # For Mac OS
            tw.tk.call(
                "::tk::unsupported::MacWindowStyle",
                "style",
                tw._w,
                "help",
                "noActivates",
            )
        except tk.TclError:
            pass
        label = tk.Label(tw, text=self.text, **self.options)
        label.pack()

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def create_tooltip(widget, text, **kw):
    options = get_style_configuration("Tooltip").copy()
    options.setdefault("background", "#ffffe0")
    options.setdefault("relief", "solid")
    options.setdefault("borderwidth", 1)
    options.setdefault("padx", 1)
    options.setdefault("pady", 0)
    options.update(kw)

    toolTip = ToolTip(widget, options)

    def enter(event):
        toolTip.showtip(text)

    def leave(event):
        toolTip.hidetip()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)
    

def accelerator_to_sequence(accelerator):
    '''
        将类似快捷键ctrl+N转换成<Control-n>, Ctrl+Shift+S转换成<Control-Shift-S>
    '''
    assert(not strutils.is_none_or_empty(accelerator))
    sequence = accelerator.replace("Ctrl","Control")
    sequence_parts = sequence.split("+")
    #如果是2个键组合,最后一个键必须小写
    if len(sequence_parts[-1]) == 1 and len(sequence_parts) <=2:
        sequence_parts[-1] = sequence_parts[-1].lower()
    sequence = "-".join(sequence_parts)
    return "<%s>" % sequence
    

def get_zoomed(toplevel):
    if "-zoomed" in toplevel.wm_attributes():  # Linux
        return bool(toplevel.wm_attributes("-zoomed"))
    else:  # Win/Mac
        return toplevel.wm_state() == "zoomed"


def set_zoomed(toplevel, value):
    if "-zoomed" in toplevel.wm_attributes():  # Linux
        toplevel.wm_attributes("-zoomed", str(int(value)))
    else:  # Win/Mac
        if value:
            toplevel.wm_state("zoomed")
        else:
            toplevel.wm_state("normal")
        
def update_toolbar(func):
    def wrap_func(*args,**kwargs):
        func(*args,**kwargs)
        GetApp().MainFrame.UpdateToolbar()
    return wrap_func
    
class AlarmEventView(core.View):
    
    def __init__(self):
        core.View.__init__(self)
        self._asking_about_external_change = False
        self._alarm_event = -1
        self._is_external_changed = False
        
    def Alarm(self,alarm_event):
        if os.path.exists(self.GetDocument().GetFilename()) and self.GetDocument().IsDocumentModificationDateCorrect():
            utils.get_logger().warn("accept modify alarm event,but file %s modify time is not chanaged",self.GetDocument().GetFilename())
            return
        self._alarm_event = alarm_event
        self._is_external_changed = True
        
    def check_for_external_changes(self):
        self._is_external_changed = False