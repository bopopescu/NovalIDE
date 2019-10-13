import tkinter as tk
from tkinter import ttk
import noval.ttkwidgets.listboxframe as listboxframe
import noval.ui_utils as ui_utils

class PythonBuiltinsPanel(ttk.Frame):
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        self.listview = listboxframe.ListboxFrame(self,listbox_class=ui_utils.ThemedListbox)
        self.listview.pack(fill="both",expand=1)
        
    def SetBuiltiins(self,interpreter):
        self.listview.listbox.delete(0,"end")
        if interpreter is not None:
            for name in interpreter.Builtins:
                self.listview.listbox.insert(0,name)