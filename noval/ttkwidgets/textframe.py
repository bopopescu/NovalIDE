# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import noval.ui_base as ui_base

class TextFrame(ttk.Frame):
    def __init__(
        self,
        master,
        show_scrollbar=True,
        borderwidth=0,
        relief="flat",
        text_class = tk.Text,
        **kw
    ):
        #设置文本框边界高度
        ttk.Frame.__init__(self, master, borderwidth=borderwidth, relief=relief)
        # http://wiki.tcl.tk/44444#pagetoc50f90d9a
        self.vert_scrollbar = ui_base.SafeScrollbar(
            self, orient=tk.VERTICAL, style=None
        )
        if show_scrollbar:
            self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)
        self.text = text_class(
            self,
            yscrollcommand=self.vert_scrollbar.set,
            selectborderwidth=0,
            borderwidth=0,
            **kw
        )

        self.text.grid(row=0, column=0, sticky=tk.NSEW)
        self.vert_scrollbar["command"] = self.text.yview
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
