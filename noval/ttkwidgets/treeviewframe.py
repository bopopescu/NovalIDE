import tkinter as tk
from tkinter import ttk

class TreeViewFrame(ttk.Frame):
    def __init__(
        self,
        master,
        show_scrollbar=True,
        borderwidth=0,
        relief="flat",
        treeview_class=ttk.Treeview,
        **tree_kw
    ):
        ttk.Frame.__init__(self, master, borderwidth=borderwidth, relief=relief)
        # http://wiki.tcl.tk/44444#pagetoc50f90d9a
        self.vert_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, style=None
        )
        if show_scrollbar:
            self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        self.tree = treeview_class(
            self,
            yscrollcommand=self.vert_scrollbar.set,
            **tree_kw
        )
        self.tree["show"] = "tree"
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.vert_scrollbar["command"] = self.tree.yview
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
     ###   self.tree.bind("<<TreeviewSelect>>", self.on_select, "+")

    def _clear_tree(self):
        for child_id in self.tree.get_children():
            self.tree.delete(child_id)

    def clear(self):
        self._clear_tree()

    def on_select(self, event):
        node_id = self.tree.focus()
        self.tree.selection_set(node_id)
        self.tree.focus(node_id)
