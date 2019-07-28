# -*- coding: utf-8 -*-
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk
import os
import noval.util.apputils as apputils
import noval.util.fileutils as fileutils
import noval.util.utils as utils
import noval.project.resource as proejctresource
import noval.util.singleton as singleton
import noval.consts as consts
import noval.ui_base as ui_base
import noval.ttkwidgets.treeviewframe as treeviewframe
import six
RESOURCE_ITEM_NAME = "Resource"


class PropertiesService:
    """
    Service that installs under the File menu to show the properties of the file associated
    with the current document.
    """

    def __init__(self):
        """
        Initializes the PropertyService.
        """
        self._optionsPanelClasses = []
        self.current_project_document = GetApp().MainFrame.GetProjectView(generate_event=False).GetCurrentProject()
        pages = self.current_project_document.GetModel().GetPropertiPages()
        for page in pages:
            self.AddOptionsPanelClass(page.item,page.name,page.objclass)
        
    def AddOptionsPanelClass(self,item,name,optionsPanelClass):
        #这里针对python2和python3中各自的string类型进行了区分:在python2中,使用的为basestring;在python3中,使用的为str
        if isinstance(optionsPanelClass,six.string_types[0]):
            try:
                optionsPanelClass = utils.GetClassFromDynamicImportModule(optionsPanelClass)
            except Exception as e:
                utils.get_logger().exception('load property page %s error',optionsPanelClass)
                return
        self._optionsPanelClasses.append((item,name,optionsPanelClass),)
        
    def GetOptionPanelClasses(self):
        return self._optionsPanels

    def GetItemOptionsPanelClasses(self,item):
        option_panel_classes = []
        for optionsPanelClass in self._optionsPanelClasses:
            if optionsPanelClass[0] == item:
                option_panel_classes.append(optionsPanelClass)
        return option_panel_classes

    def ShowPropertyDialog(self,item,option_name=None):
        """
        Shows the PropertiesDialog for the specified file.
        """
        is_project = False
        project_view = self.current_project_document.GetFirstView()
        option_pages = {}
        if item == project_view._treeCtrl.GetRootItem():
            title = _("Project Property")
            file_path = self.current_project_document.GetFilename()
         #   self.AddOptionsPanel(INTERPRETER_ITEM_NAME,PythonInterpreterPanel)
          #  self.AddOptionsPanel(PYTHONPATH_ITEM_NAME,PythonPathPanel)
           # self.AddOptionsPanel(PROJECT_REFERENCE_ITEM_NAME,ProjectReferrencePanel)
            option_pages = self.GetItemOptionsPanelClasses('root')
            is_project = True
        elif project_view._IsItemFile(item):
            title = _("File Property")
            file_path = project_view._GetItemFilePath(item)
            option_pages = self.GetItemOptionsPanelClasses('file')
        else:
            title = _("Folder Property")
            file_path = project_view._GetItemFolderPath(item)
            option_pages = self.GetItemOptionsPanelClasses('folder')
            
        propertyDialog = PropertyDialog(GetApp().GetTopWindow(),title,item,option_pages,option_name)
        propertyDialog.ShowModal()
        
class PropertyDialog(ui_base.CommonModaldialog):
    """
    A default options dialog used by the OptionsService that hosts a notebook
    tab of options panels.
    """
    PANEL_WIDITH = 800
    PANEL_HEIGHT = 500

    def __init__(self, master, title,selected_item,option_pages,option_name=None):#item_type
        """
        Initializes the options dialog with a notebook page that contains new
        instances of the passed optionsPanelClasses.
        """
        ui_base.CommonModaldialog.__init__(self, master, takefocus=1)
        self.geometry("%dx%d" % (self.PANEL_WIDITH,self.PANEL_HEIGHT))
        self.title(title)
        self._optionsPanels = {}
        self.current_panel = None
        self.current_item = None
        self._selected_project_item = selected_item
        
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill="both",expand=1)

        sizer_frame = ttk.Frame(top_frame)
        sizer_frame.pack(side=tk.LEFT,fill="y")
        
        #设置path列存储模板路径,并隐藏改列
        treeview = treeviewframe.TreeViewFrame(sizer_frame,show_scrollbar=False,borderwidth=1,relief="solid")
        self.tree = treeview.tree
        treeview.pack(side=tk.LEFT,fill="both",expand=1,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.tree.bind("<<TreeviewSelect>>", self.DoSelection, True)
     
        # configure the only tree column
        self.tree.column("#0", anchor=tk.W, stretch=True)
        self.tree["show"] = ("tree",)#   wx.StaticLine(self, -1)
        
        page_frame = ttk.Frame(top_frame)
        page_frame.pack(side=tk.LEFT,fill="both",expand=1)
        separator = ttk.Separator(page_frame, orient = tk.HORIZONTAL)
        separator.grid(column=0, row=1, sticky="nsew",padx=(1,0))
        page_frame.columnconfigure(0, weight=1)
        page_frame.rowconfigure(0, weight=1)
        current_project_document = GetApp().MainFrame.GetProjectView(generate_event=False).GetCurrentProject()
        self._current_project_document = current_project_document
        ##force select one option
        if option_name:
            selection = option_name
        else:
            selection = utils.profile_get(current_project_document.GetKey("Selection"),"")
        for item,name,optionsPanelClass in option_pages:
            item = self.tree.insert("","end",text=_(name),values=(name,))
            option_panel = optionsPanelClass(page_frame,item = self._selected_project_item,current_project=self._current_project_document)
            self._optionsPanels[name] = option_panel
            #select the default item,to avoid select no item
            if name == RESOURCE_ITEM_NAME:
                self.select_item(item)
            if name == selection:
                self.select_item(item)
        self.AddokcancelButton()
                
    def select_item(self,item):
        self.tree.focus(item)
        self.tree.see(item)
        self.tree.selection_set(item)
                
    @property
    def CurrentProject(self):
        return self._current_project_document

    def DoSelection(self,event):
        sel = self.tree.selection()[0]
        text = self.tree.item(sel)["values"][0]
        panel = self._optionsPanels[text]
        if self.current_item is not None and sel != self.current_item:
            if not self.current_panel.Validate():
                self.tree.SelectItem(self.current_item)
                return 
        if self.current_panel is not None and panel != self.current_panel:
            self.current_panel.grid_forget()
        self.current_panel = panel
        self.current_panel.grid(column=0, row=0, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=consts.DEFAUT_CONTRL_PAD_Y)
        
    def _ok(self):
        """
        Calls the OnOK method of all of the OptionDialog's embedded panels
        """
        if not self.current_panel.Validate():
            return
        for name in self._optionsPanels:
            optionsPanel = self._optionsPanels[name]
            if not optionsPanel.OnOK(self):
                return
        selections = self.tree.selection()
        if selections:
            sel = selections[0]
            text = self.tree.item(sel)['values'][0]
            if self._current_project_document is not None:
                utils.profile_set(self._current_project_document.GetKey("Selection"),text)
        ui_base.CommonModaldialog._ok(self)
        
    def GetOptionPanel(self,option_name):
        return self._optionsPanels[option_name]
        
    def HasPanel(self,option_name):
        return option_name in self._optionsPanels
        