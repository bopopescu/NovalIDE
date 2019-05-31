from noval import _,GetApp
import tkinter as tk
from tkinter import ttk
import noval.consts as consts
import noval.ui_base as ui_base
import noval.util.utils as utils

class MultiStatusBar(ui_base.DockFrame):
    
    DEFUALT_LABEL = "default"

    def __init__(self, master=None, **kw):
        ui_base.DockFrame.__init__(self,consts.DEFAULT_STATUS_BAR_ROW, master,show=self.IsDefaultShown())
        self.labels = {}
        self.set_label(self.DEFUALT_LABEL,_('Ready'),expand=True)

    def set_label(self, name, text='', side=tk.LEFT, width=0,expand=False):
        if name not in self.labels:
            label = ttk.Label(self, borderwidth=0, anchor=tk.W)
            kwargs = dict(side=side, pady=0, padx=4)
            if expand:
                kwargs.update({'expand':1,'fill':"x"})
            label.pack(**kwargs)
            self.labels[name] = label
            if name != self.DEFUALT_LABEL:
                separator = ttk.Separator (self, orient = tk.VERTICAL)
                separator.pack(side=side, pady=0, padx=0, fill="y")
        else:
            label = self.labels[name]
        if width != 0:
            label.config(width=width)
        label.config(text=text)
        return label
        
    def SetLineNumber(self, lineNumber):
        newText = _("Ln %i") % lineNumber
        self.set_label(consts.STATUS_BAR_LABEL_LINE,newText,side=tk.RIGHT)
        
    def GotoLine(self,event):
        GetApp().MainFrame.GetNotebook().GotoLine()

    def SetColumnNumber(self, colNumber):
        newText = _("Col %i") % colNumber
        self.set_label(consts.STATUS_BAR_LABEL_COL,newText,side=tk.RIGHT)
        
    def Reset(self):
        for name,label in self.labels.items():
            if name == self.DEFUALT_LABEL:
                text = _('Ready')
            else:
                text = ""
            label.config(text=text)
            
    def SetDocumentEncoding(self,encoding):
        self.set_label(consts.STATUS_BAR_LABEL_ENCODING,encoding,side=tk.RIGHT)

    def IsDefaultShown(self):
        statusbar_key = self.GetStatusbarKey()
        return utils.profile_get_int(statusbar_key,True)
        
    def GetStatusbarKey(self):
        return consts.FRAME_VIEW_VISIBLE_KEY % "statusbar"
        
    def PushStatusText(self,msg,label=""):
        if label == "":
            label = self.DEFUALT_LABEL
        assert(label in self.labels)
        self.set_label(label,msg)
        