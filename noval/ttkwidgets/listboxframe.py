import tkinter as tk
from tkinter import ttk

class ListboxFrame(ttk.Frame):
    def __init__(
        self,
        master,
        show_scrollbar=True,
        borderwidth=0,
        relief="flat",
        **kw
    ):
        ttk.Frame.__init__(self, master, borderwidth=borderwidth, relief=relief)
        # http://wiki.tcl.tk/44444#pagetoc50f90d9a
        self.vert_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, style=None
        )
        if show_scrollbar:
            self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)
        self.listbox = tk.Listbox(
            self,
            yscrollcommand=self.vert_scrollbar.set,
            **kw
        )

        self.listbox.grid(row=0, column=0, sticky=tk.NSEW)
        self.vert_scrollbar["command"] = self.listbox.yview
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
