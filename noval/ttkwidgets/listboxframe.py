import tkinter as tk
from tkinter import ttk

class ListboxFrame(ttk.Frame):
    def __init__(
        self,
        main,
        show_scrollbar=True,
        borderwidth=0,
        relief="flat",
        listbox_class = tk.Listbox,
        **kw
    ):
        ttk.Frame.__init__(self, main, borderwidth=borderwidth, relief=relief)
        # http://wiki.tcl.tk/44444#pagetoc50f90d9a
        self.vert_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, style=None
        )
        if show_scrollbar:
            self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)
        self.listbox = listbox_class(
            self,
            yscrollcommand=self.vert_scrollbar.set,
            selectborderwidth=0,
            borderwidth=0,
            **kw
        )

        self.listbox.grid(row=0, column=0, sticky=tk.NSEW)
        self.vert_scrollbar["command"] = self.listbox.yview
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
