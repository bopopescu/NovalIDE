import tkinter as tk
from tkinter import ttk

class PythonBuiltinsPanel(ttk.Frame):
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill="both",expand=1)
        
    def SetBuiltiins(self,interpreter):
        self.listbox.delete(0,"end")
        if interpreter is not None:
            for name in interpreter.Builtins:
                self.listbox.insert(0,name)