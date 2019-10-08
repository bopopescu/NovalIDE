# -*- coding: utf-8 -*-
from noval import _
import tkinter as tk
from tkinter import ttk
import noval.util.singleton as singleton
import noval.consts as consts
import noval.ui_base as ui_base
import noval.ttkwidgets.treeviewframe as treeviewframe
from noval.util import utils
ENVIRONMENT_OPTION_NAME = "Environment"

#option item names
GENERAL_ITEM_NAME = "General"
TEXT_ITEM_NAME = "Text"
PROJECT_ITEM_NAME = "Project"
FONTS_CORLORS_ITEM_NAME = "Fonts and Colors"
INTERPRETER_OPTION_NAME = "Interpreter"
INTERPRETER_CONFIGURATIONS_ITEM_NAME = "Configuration List"

EXTENSION_ITEM_NAME = "Extension"


PREFERENCE_DLG_WIDITH = 850
PREFERENCE_DLG_HEIGHT = 580

def GetOptionName(caterory,name):
    return caterory + "/" + name

class PreferenceDialog(ui_base.CommonModaldialog):
    
    def __init__(self, master,selection=None):
        ui_base.CommonModaldialog.__init__(self, master, takefocus=1)
        self.title(_("Options"))
        self.geometry("%dx%d" % (PREFERENCE_DLG_WIDITH,PREFERENCE_DLG_HEIGHT))
        if not selection:
            selection=ENVIRONMENT_OPTION_NAME+"/"+GENERAL_ITEM_NAME
        
        self.current_panel = None
        self.current_item = None
        self._optionsPanels = {}
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill="both",expand=1)
        sizer_frame = ttk.Frame(top_frame)
        sizer_frame.pack(side=tk.LEFT,fill="y")
        #设置path列存储模板路径,并隐藏改列 
        treeview = treeviewframe.TreeViewFrame(sizer_frame,show_scrollbar=False,borderwidth=1,relief="solid")
        self.tree = treeview.tree
        treeview.pack(side=tk.LEFT,fill="both",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.tree.bind("<<TreeviewSelect>>", self._on_select, True)

        # configure the only tree column
        self.tree.column("#0", anchor=tk.W, stretch=True)
        self.tree["show"] = ("tree",)
        
        page_frame = ttk.Frame(top_frame)
        page_frame.pack(side=tk.LEFT,fill="both",expand=1)
        separator = ttk.Separator(page_frame, orient = tk.HORIZONTAL)
        separator.grid(column=0, row=1, sticky="nsew",padx=(1,0))
        page_frame.columnconfigure(0, weight=1)
        page_frame.rowconfigure(0, weight=1)

        option_catetory,sel_option_name = self.GetOptionNames(selection)
        category_list = PreferenceManager().GetOptionList()
        category_dct = PreferenceManager().GetOptionPageClasses()
        for category in category_list:
            item = self.tree.insert("", "end", text=_(category))
            optionsPanelClasses = category_dct[category]
            for name,optionsPanelClass in optionsPanelClasses:
                option_panel = optionsPanelClass(page_frame)
                option_name = GetOptionName(category , name)
                self._optionsPanels[option_name] = option_panel
                child = self.tree.insert(item,"end",text=_(name),values=(option_name,))
                #select the default item,to avoid select no item
                if name == GENERAL_ITEM_NAME and category == ENVIRONMENT_OPTION_NAME:
                    self.select_item(child)
                if name == sel_option_name and category == option_catetory:
                    self.select_item(child)
                    
        self.AddokcancelButton()
        
    def select_item(self,item):
        self.tree.focus(item)
        self.tree.see(item)
        self.tree.selection_set(item)
        
    def GetOptionNames(self,selection_name):
        names = selection_name.split("/")
        if 1 >= len(names):
            return "",selection_name
        return names[0],names[1]
        
    def GetOptionPanel(self,category,option_name):
        return self._optionsPanels[GetOptionName(category , option_name)]
        
    def _on_select(self,event):
        sel = self.tree.selection()[0]
        childs = self.tree.get_children(sel)
        if len(childs) > 0:
            sel = childs[0]
        text = self.tree.item(sel)["values"][0]
        panel = self._optionsPanels[text]
        if self.current_item is not None and sel != self.current_item:
            if not self.current_panel.Validate():
                self.tree.SelectItem(self.current_item)
                return 
        if self.current_panel is not None and panel != self.current_panel:
            self.current_panel.grid_forget()
        self.current_panel = panel
        self.current_panel.grid(column=0, row=0, sticky="nsew")
        
    def _ok(self, event=None):
        if not self.current_panel.Validate():
            return
        for name in self._optionsPanels:
            optionsPanel = self._optionsPanels[name]
            if not optionsPanel.OnOK(self):
                return
        sel = self.tree.selection()[0]
        if len(self.tree.get_children(sel)) > 0:
            sel = self.tree.get_children(sel)[0]
        text = self.tree.item(sel)['values'][0]
        utils.profile_set("PrefereceOptionName",text)
        ui_base.CommonModaldialog._ok(self,event)
        
    def _cancel(self, event=None):
        for name in self._optionsPanels:
            optionsPanel = self._optionsPanels[name]
            if hasattr(optionsPanel,"OnCancel") and not optionsPanel.OnCancel(self):
                return
        ui_base.CommonModaldialog._cancel(self,event)

@singleton.Singleton
class PreferenceManager:
    
    def __init__(self):
        self._optionsPanelClasses = {}
        self.category_list = []
        
    def GetOptionPageClasses(self):
        return self._optionsPanelClasses

    def AddOptionsPanelClass(self,category,name,optionsPanelClass):
        if category not in self._optionsPanelClasses:
            self._optionsPanelClasses[category] = [(name,optionsPanelClass),]
            self.category_list.append(category)
        else:
            self._optionsPanelClasses[category].append((name,optionsPanelClass),)
            
    def GetOptionList(self):
        return self.category_list