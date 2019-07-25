# -*- coding: utf-8 -*-
from noval import GetApp,_
import os
import tkinter as tk
from tkinter import ttk,messagebox
import noval.util.fileutils as fileutils
import noval.imageutils as imageutils
import time
import noval.util.apputils as apputils
import noval.ui_utils as ui_utils
import noval.misc as misc

#set the max width of location label,to avoid too long
MAX_LOCATION_LABEL_WIDTH  = 400

class ResourcePanel(ui_utils.BaseConfigurationPanel):
    """description of class"""
    
    def __init__(self,parent,item,current_project):
        ui_utils.BaseConfigurationPanel.__init__(self,parent)
        relative_path = ""
        path = ""
        type_name = ""
        project_path = os.path.dirname(current_project.GetFilename())
        is_file = False
        project_view = current_project.GetFirstView()
        if item == project_view._treeCtrl.GetRootItem():
            path = current_project.GetFilename()
            type_name = _("Project")
            relative_path = os.path.basename(path)
        elif project_view._IsItemFile(item):
            path = project_view._GetItemFilePath(item)
            template = GetApp().GetDocumentManager().FindTemplateForPath(path)
            type_name = _("File") + "(%s)" % _(template.GetDescription())
            relative_path = path.replace(project_path,"").lstrip(os.sep)
            is_file = True
        else:
            relative_path = project_view._GetItemFolderPath(item)
            type_name = _("Folder")
            path = os.path.join(project_path,relative_path)
            
        self.columnconfigure(1, weight=1)    
        ttk.Label(self, text=_("Path:")).grid(column=0, row=0, sticky="nsew",padx=(1,0))
        ttk.Label(self, text=fileutils.opj(relative_path)).grid(column=1, row=0, sticky="nsew",padx=(1,0))
        
        ttk.Label(self,text=_("Type:")).grid(column=0, row=1, sticky="nsew",padx=(1,0))
        ttk.Label(self, text=type_name).grid(column=1, row=1, sticky="nsew",padx=(1,0))
        
        ttk.Label(self,text= _("Location:")).grid(column=0, row=2, sticky="nsew",padx=(1,0))
        self.dest_path = fileutils.opj(path)
        row = ttk.Frame(self)
        row.grid(column=1, row=2, sticky="nsew",padx=(1,0))
        self.location_label_ctrl = ttk.Label(row, text = self.dest_path)
        self.location_label_ctrl.pack(side=tk.LEFT,fill="x")
        self.into_img = GetApp().GetImage("project/into.png")
        into_btn = ttk.Button(
            row,
            command=self.IntoExplorer,
            image=self.into_img,
            style="Toolbutton",##设置样式为Toolbutton(工具栏按钮),如果该参数为空,则button样式为普通button,不是工具栏button,边框有凸起
            state=tk.NORMAL,
            compound=None,
            pad=None,
        )
        into_btn.pack(side=tk.LEFT)
        misc.create_tooltip(into_btn, _("Into file explorer"))
    
        self.copy_img = GetApp().GetImage("project/copy.png")
        copy_btn = ttk.Button(
            row,
            command=self.CopyPath,
            image=self.copy_img,
            style="Toolbutton",##设置样式为Toolbutton(工具栏按钮),如果该参数为空,则button样式为普通button,不是工具栏button,边框有凸起
            state=tk.NORMAL,
            compound=None,
            pad=None,
        )
        copy_btn.pack(side=tk.LEFT)
        misc.create_tooltip(copy_btn, _("Copy path"))
        
        is_path_exist = os.path.exists(path)
        show_label_text = ""
        if not is_path_exist:
            show_label_text = _("resource does not exist") 
        if is_file:
            ttk.Label(self, text=_("Size:")).grid(column=0, row=3, sticky="nsew",padx=(1,0))
            if is_path_exist:
                show_label_text = str(os.path.getsize(path))+ _(" Bytes")
            size_label_ctrl = ttk.Label(self,text=show_label_text)
            size_label_ctrl.grid(column=1, row=3, sticky="nsew",padx=(1,0))
            if not is_path_exist:
                size_label_ctrl.config(foreground="red")
        ttk.Label(self, text=_("Created:")).grid(column=0, row=4, sticky="nsew",padx=(1,0))
        if is_path_exist:
            show_label_text = time.ctime(os.path.getctime(path))
        ctime_lable_ctrl = ttk.Label(self, text=show_label_text)
        ctime_lable_ctrl.grid(column=1, row=4, sticky="nsew",padx=(1,0))
        if not is_path_exist:
            ctime_lable_ctrl.config(foreground="red")
        if is_path_exist:
            show_label_text = time.ctime(os.path.getmtime(path))
        ttk.Label(self, text=_("Modified:")).grid(column=0, row=5, sticky="nsew",padx=(1,0))
        mtime_label_ctrl = ttk.Label(self, text=show_label_text)
        mtime_label_ctrl.grid(column=1, row=5, sticky="nsew",padx=(1,0))
        if not is_path_exist:
            mtime_label_ctrl.config(foreground="red")
        ttk.Label(self, text=_("Accessed:")).grid(column=0, row=6, sticky="nsew",padx=(1,0))
        if is_path_exist:
            show_label_text = time.ctime(os.path.getatime(path))
        atime_label_ctrl = ttk.Label(self, text=show_label_text)
        atime_label_ctrl.grid(column=1, row=6, sticky="nsew",padx=(1,0))
        if not is_path_exist:
            atime_label_ctrl.config(foreground="red")
        
    def IntoExplorer(self):
        location = self.dest_path
        fileutils.safe_open_file_directory(location)
            
    def CopyPath(self):
        path = self.dest_path
        apputils.CopyToClipboard(path)
        messagebox.showinfo(GetApp().GetAppName(),_("Copied to clipboard"))
        
    def OnOK(self,optionsDialog):
        return True
