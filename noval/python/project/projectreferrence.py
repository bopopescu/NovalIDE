from noval import _,GetApp
import tkinter as tk
from tkinter import ttk
import os
import noval.consts as consts
from noval.util import utils
import noval.ui_utils as ui_utils
import noval.ttkwidgets.checklistbox as checklistbox
import noval.project.property as projectproperty
import noval.ttkwidgets.treeviewframe as treeviewframe

class ProjectReferrencePanel(ui_utils.BaseConfigurationPanel):
    def __init__(self,parent,item,current_project):
        ui_utils.BaseConfigurationPanel.__init__(self,parent)
        self._current_project = current_project
        project_StaticText = ttk.Label(self, text=_("Project may refer to other projects.The reference project path will append to the PYTHONPATH of current project.\n"))
        project_StaticText.pack(fill="x")
        ttk.Label(self,text=_("The reference projects for '%s':") % self.GetProjectName()).pack(fill="x")
        row = ttk.Frame(self)
        listbox_view =treeviewframe.TreeViewFrame(row,treeview_class=checklistbox.CheckListbox,borderwidth=1,relief="solid",show_scrollbar=False)
        self.listbox = listbox_view.tree
        self.listbox["show"] = "tree"
        listbox_view.pack(side=tk.LEFT,fill="both",expand=1)
        right = ttk.Frame(row)
        ttk.Button(right, text= _("Select All"),command=self.SelectAll).pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        ttk.Button(right,text= _("UnSelect All"),command=self.UnSelectAll).pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        right.pack(side=tk.LEFT,fill="y")
        row.pack(fill="both",expand=1)
        self.LoadProjects()

    def GetProjectName(self):
        return os.path.basename(self._current_project.GetFilename())
        
    def OnOK(self,optionsDialog):
        ref_project_names = self.GetReferenceProjects()
        utils.profile_set(self._current_project.GetKey() + "/ReferenceProjects",ref_project_names)
        return True
        
    def SelectAll(self):
        for i in range(self.listbox.GetCount()):
            if not self.listbox.IsChecked(i):
                self.listbox.Check(i,True)
        
    def UnSelectAll(self):
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                self.listbox.Check(i,False)
        
    def LoadProjects(self):
        ref_project_names = utils.profile_get(self._current_project.GetKey() + "/ReferenceProjects",[])
        current_project_document = GetApp().MainFrame.GetProjectView(generate_event=False).GetCurrentProject()
        for document in GetApp().MainFrame.GetProjectView(generate_event=False).GetOpenProjects():
            if document == current_project_document:
                continue
            project_name = document.GetModel().Name
            i = self.listbox.Append(project_name)
            self.listbox.SetData(i,document.GetFilename())
            if document.GetFilename() in ref_project_names:
                self.listbox.Check(i,True)
            
    def GetReferenceProjects(self):
        projects = []
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                projects.append(self.listbox.GetData(i))
        return projects


