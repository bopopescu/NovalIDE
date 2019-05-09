# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from noval import _ ,GetApp
import os
import noval.util.apputils as sysutilslib
import noval.util.fileutils as fileutils
import threading
import time
#import ProjectUI
import noval.util.strutils as strutils
import noval.project.Wizard as Wizard
import noval.consts as consts
import noval.ttkwidgets.checkboxtreeview as checkboxtreeview
import noval.ttkwidgets.checklistbox as checklistbox
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.syntax.lang as lang
import noval.project.baserun as baserun

class ImportfilesPage(Wizard.BitmapTitledWizardPage):
    def __init__(self,master,add_bottom_page=True,filters=[],rejects=[]):
        Wizard.BitmapTitledWizardPage.__init__(self,master,_("Import codes from File System"),_("Local File System"),"python_logo.png")
        self.can_finish = True
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        separator = ttk.Separator(sizer_frame, orient = tk.HORIZONTAL)
        separator.pack(side=tk.LEFT,fill="x",expand=1)
        
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=2, sticky="nsew")
        self.dir_label = ttk.Label(sizer_frame, text=_("Source Location:"))
        self.dir_label.grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.dir_entry_var = tk.StringVar()
        self.dir_entry = ttk.Entry(sizer_frame, textvariable=self.dir_entry_var)
        self.dir_entry_var.trace("w", self.ChangeDir)
        self.dir_entry.grid(column=1, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X/2,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.browser_button = ttk.Button(
            sizer_frame, text=_("Browse..."), command=self.BrowsePath
        )
        self.browser_button.grid(column=2, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        sizer_frame.columnconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=3, sticky="nsew")
        self.rowconfigure(3, weight=1)

        self.check_box_view = treeviewframe.TreeViewFrame(sizer_frame,treeview_class=checkboxtreeview.CheckboxTreeview)
        self.check_box_view.grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.check_box_view.tree.bind("<<TreeviewSelect>>", self._on_select, True)
        
        self.check_listbox =treeviewframe.TreeViewFrame(sizer_frame,treeview_class=checklistbox.CheckListbox)
        self.check_listbox.grid(column=1, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        sizer_frame.columnconfigure(0, weight=1)
        sizer_frame.columnconfigure(1, weight=1)
        sizer_frame.rowconfigure(0, weight=1)
        

        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=4, sticky="nsew")
        
        self.file_filter_btn = ttk.Button(
            sizer_frame, text=_("File Filters"), command=self.BrowsePath
        )
        self.file_filter_btn.grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        #文件类型过滤列表
        self.filters = filters
        self.rejects = rejects
        self.select_all_btn = ttk.Button(
            sizer_frame, text=_("Select All"), command=self.SelectAll
        )
        self.select_all_btn.grid(column=1, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.unselect_all_btn = ttk.Button(
            sizer_frame, text=_("UnSelect All"), command=self.UnselectAll
        )
        self.unselect_all_btn.grid(column=2, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.root_item = None
        self.project_browser = GetApp().MainFrame.GetProjectView()
        
    def ShowProgress(self,row):
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=row, sticky="nsew")
        self.cur_prog_val = tk.IntVar(value=0)
        self.pb = ttk.Progressbar(sizer_frame,variable=self.cur_prog_val)
        self.pb.pack(fill="x",padx=(0, 0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        sizer_frame.columnconfigure(0, weight=1)

    def BrowsePath(self):
        path = filedialog.askdirectory()
        if path:
            #必须转换一下路径为系统标准路径格式
            path = fileutils.opj(path)
            self.dir_entry_var.set(path)
            
    def ChangeDir(self,*args):
        path =  self.dir_entry_var.get().strip()
        if path == "":
            self.check_box_view.clear()
            return
        if sysutilslib.is_windows():
            path = path.replace("/",os.sep)
        self.ListDirItemFiles(path.rstrip(os.sep))

    def ListDirItemFiles(self,path):
        self.check_box_view._clear_tree()
        self.root_item = self.check_box_view.tree.insert("", "end", text=os.path.basename(path),values=(path,))
        self.ListDirTreeItem(self.root_item,path)
        self.ListDirFiles(self.root_item,True,True)
        self.check_box_view.tree.CheckItem(self.root_item)
        self.check_box_view.tree.focus(self.root_item)
        self.check_box_view.tree.selection_set(self.root_item)
        
    def _on_select(self,event):
        item = self.check_box_view.tree.GetSelectionItem()
        self.ListDirFiles(item,True,True)
        
    def ListDirTreeItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isdir(file_path) and not fileutils.is_file_path_hidden(file_path):
                item = self.check_box_view.tree.insert(parent_item, "end", text=f,values=(file_path,))
                self.ListDirTreeItem(item,file_path)
        self.check_box_view.tree.item(parent_item, open=True)
        
    def ListDirFiles(self,item,checked=True,force=False):
        path = self.check_box_view.tree.item(item)["values"][0]
        if not os.path.exists(path):
            self.check_box_view.clear()
            return
        if self.check_box_view.tree.GetSelectionItem() == item and not force:
            for i in range(self.listbox.GetCount()):
                if checked:
                    if not self.check_listbox.IsChecked(i):
                        self.check_listbox.Check(i,True)
                else:
                    if self.check_listbox.IsChecked(i):
                        self.check_listbox.Check(i,False)
                    
            return
        self.check_listbox.clear()
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isfile(file_path) and not fileutils.is_file_path_hidden(file_path) and not strutils.get_file_extension(file_path) in self.rejects:
                i = self.check_listbox.tree.Append(f)
                self.check_listbox.tree.Check(i,checked)

    def Finish(self):
        file_list = self.GetImportFileList()
        if 0 == len(file_list):
            return False
        if not hasattr(self,"cur_prog_val"):
            self.ShowProgress(5)

        self.DisableUI()
        self.master.master.ok_button['state'] = tk.DISABLED
        self.master.master.prev_button['state'] = tk.DISABLED
        self.pb["maximum"] = len(file_list)

        project_path = os.path.dirname(self.project_browser.GetView().GetDocument().GetFilename())
        #目的路径必须用相对路径
        dest_path = os.path.basename(project_path)
        prev_page = self.GetPrev()
        if GetApp().GetDefaultLangId() == lang.ID_LANG_PYTHON:
            if prev_page._project_configuration.PythonpathMode == baserun.BaseProjectConfiguration.PROJECT_ADD_SRC_PATH:
                #目的路径为Src路径
                dest_path = os.path.join(dest_path,baserun.BaseProjectConfiguration.DEFAULT_PROJECT_SRC_PATH)
        root_path = self.check_box_view.tree.item(self.root_item)["values"][0]
       # ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID = wx.ID_YESTOALL
        self.project_browser.StartCopyFilesToProject(self,file_list,root_path,dest_path)
        return False
        
    def GetImportFileList(self):
        file_list = []
        root_path = self.check_box_view.tree.item(self.root_item)["values"][0]
        #如果根节点未选中则直接从硬盘中获取根路径的文件列表
        if not self.IsItemSelected(self.root_item):
            fileutils.GetDirFiles(root_path,file_list,self.filters)
        else:
            #如果根节点选中则从界面获取有哪些文件被选中了
            self.GetCheckedItemFiles(self.root_item,file_list)
        #扫描根节点下的所有文件列表
        self.RotateItems(self.root_item,file_list)
        if 0 == len(file_list):
            messagebox.showinfo(GetApp().GetAppName(),_("You don't select any file"))
            return file_list

        project_file_path = self.project_browser.GetView().GetDocument().GetFilename()
        #如果项目文件在文件列表中剔除
        if project_file_path in file_list:
            file_list.remove(project_file_path)

        return file_list
        
    def DisableUI(self):
        self.dir_entry['state'] = tk.DISABLED
        self.browser_button['state'] = tk.DISABLED
        self.select_all_btn['state'] = tk.DISABLED
        self.unselect_all_btn['state'] = tk.DISABLED
        self.file_filter_btn['state'] = tk.DISABLED
        self.check_box_view.tree.state([tk.DISABLED])
        self.check_listbox.tree.state([tk.DISABLED])
        
    def IsItemSelected(self,item):
        return self.check_box_view.tree.GetSelectionItem() == item
        
    def GetCheckedItemFiles(self,item,file_list):
        dir_path = self.check_box_view.tree.item(item)["values"][0]
        for i in range(self.check_listbox.tree.GetCount()):
            if self.check_listbox.tree.IsChecked(i):
                f = os.path.join(dir_path,self.check_listbox.tree.GetString(i))
                if self.filters != []:
                    if strutils.get_file_extension(f) in self.filters:
                        file_list.append(f)
                else:
                    file_list.append(f)
            
    def RotateItems(self,parent_item,file_list):
        for item in self.check_box_view.tree.get_children(parent_item):
            if self.check_box_view.tree.IsItemChecked(item):
                dir_path = self.check_box_view.tree.item(item)["values"][0]
                #如果节点未选中则直接从硬盘中获取路径的文件列表
                if not self.IsItemSelected(item):
                    fileutils.GetDirFiles(dir_path,file_list,filters=self.filters,rejects=self.rejects)
                else:
                    #如果节点选中则从界面获取有哪些文件被选中了
                    self.GetCheckedItemFiles(item,file_list)
            #递归子节点
            self.RotateItems(item,file_list)
        
    def SelectAll(self):
        if self.root_item is None:
            return
        self.check_box_view.tree.CheckItem(self.root_item)
        
    def UnselectAll(self):
        if self.root_item is None:
            return
        self.check_box_view.tree.CheckItem(self.root_item,False)
        
    def Validate(self):
        if self.root_item is None or not self.check_box_view.tree.IsItemChecked(self.root_item):
            messagebox.showinfo(GetApp().GetAppName(),_("You don't select any file"))
            return False
        return True
        
    def SetProgress(self,value,is_cancel):
       ### print value,self.pb["maximum"],is_cancel,"==================="
        self.cur_prog_val.set(value)
        if is_cancel:
            print ('user cancel import ,will destroy wizard')
            self.parent.destroy()
        
    def Cancel(self):
        self.project_browser.StopImport()
