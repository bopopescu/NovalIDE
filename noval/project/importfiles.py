# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from noval import _ ,GetApp
import os
import noval.util.apputils as sysutilslib
import noval.util.fileutils as fileutils
import threading
import time
import noval.util.strutils as strutils
import noval.project.wizard as projectwizard
import noval.consts as consts
import noval.ttkwidgets.checkboxtreeview as checkboxtreeview
import noval.ttkwidgets.checklistbox as checklistbox
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.syntax.lang as lang
import noval.project.baseconfig as baseconfig
import queue
import noval.util.utils as utils
import noval.ui_base as ui_base
import noval.constants as constants
import noval.project.document as projectdocument

#添加项目文件覆盖已有文件时默认处理方式
DEFAULT_PROMPT_MESSAGE_ID = constants.ID_YES

class ImportfilesPage(projectwizard.BitmapTitledContainerWizardPage):
    def __init__(self,master,filters=[],rejects=[],is_wizard=True,folderPath=None):
        '''
            is_wizard表示该页面是否是新建项目向导时的页面
        '''
        
        
        self.folderPath = folderPath
        self.dest_path = ''
        self._is_wizard = is_wizard
        #文件类型过滤列表
        self.filters = filters
        self.rejects = rejects + projectdocument.ProjectDocument.BIN_FILE_EXTS
        
        projectwizard.BitmapTitledContainerWizardPage.__init__(self,master,_("Import codes from File System"),_("Local File System"),"python_logo.png")
        self.can_finish = True
        self.project_browser = GetApp().MainFrame.GetProjectView()

        
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=2, sticky="nsew")
        self.dir_label = ttk.Label(sizer_frame, text=_("Source Location:"))
        self.dir_label.grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.dir_entry_var = tk.StringVar()
        self.dir_entry = ttk.Entry(sizer_frame, textvariable=self.dir_entry_var)
        self.dir_entry_var.trace("w", self.ChangeDir)
        self.dir_entry.grid(column=1, row=0, sticky="nsew",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.browser_button = ttk.Button(
            sizer_frame, text=_("Browse..."), command=self.BrowsePath
        )
        self.browser_button.grid(column=2, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        sizer_frame.columnconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=3, sticky="nsew")
        self.rowconfigure(3, weight=1)

        self.check_box_view = treeviewframe.TreeViewFrame(sizer_frame,treeview_class=checkboxtreeview.CheckboxTreeview,borderwidth=1,relief="solid")
        self.check_box_view.grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.check_box_view.tree.bind("<<TreeviewSelect>>", self._on_select, True)
        self.check_box_view.tree.bind("<Button-1>", self._box_click, True)
        self.current_item = None
        
        self.check_listbox =treeviewframe.TreeViewFrame(sizer_frame,treeview_class=checklistbox.CheckListbox,borderwidth=1,relief="solid")
        self.check_listbox.grid(column=1, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        sizer_frame.columnconfigure(0, weight=1)
        sizer_frame.columnconfigure(1, weight=1)
        sizer_frame.rowconfigure(0, weight=1)
        

        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=4, sticky="nsew")
        
        self.file_filter_btn = ttk.Button(
            sizer_frame, text=_("File Filters"), command=self.SetFilters
        )
        self.file_filter_btn.grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))

        
        self.select_all_btn = ttk.Button(
            sizer_frame, text=_("Select All"), command=self.SelectAll
        )
        self.select_all_btn.grid(column=1, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.unselect_all_btn = ttk.Button(
            sizer_frame, text=_("UnSelect All"), command=self.UnselectAll
        )
        self.unselect_all_btn.grid(column=2, row=0, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self._progress_row = 5
        #导入对话框页面添加一行控件
        if not self._is_wizard:
            frame = ttk.Frame(content_frame)
            ttk.Label(frame, text=_('Dest Directory:')).pack(side=tk.LEFT,fill="x")
            self.dest_pathVar = tk.StringVar(value=self.dest_path)
            destDirCtrl = ttk.Entry(frame, textvariable=self.dest_pathVar,state=tk.DISABLED)
            destDirCtrl.pack(side=tk.LEFT,fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
            frame.grid(column=0, row=5, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
            sbox_frame = ttk.LabelFrame(content_frame, text=_("Option"))
            self.overwrite_chkboxVar = tk.IntVar(value=False)
            ttk.Checkbutton(sbox_frame, variable=self.overwrite_chkboxVar,text = _("Overwrite existing files without warning")).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
            self.root_folder_chkboxVar = tk.IntVar(value=False)
            ttk.Checkbutton(sbox_frame, variable=self.root_folder_chkboxVar,text = _("Create top-level folder")).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
            sbox_frame.grid(column=0, row=6, sticky="nsew")
            self._progress_row = 7
        self.root_item = None
        self.is_cancel = False

    def GetDestpath(self):
        #目的路径必须用相对路径
        current_project = self.project_browser.GetView().GetDocument()
        if current_project is None:
            raise RuntimeError(_('There is no available project yet.'))

        project_path = os.path.dirname(current_project.GetFilename())
        self.dest_path = os.path.basename(project_path)
        if self.folderPath:
            self.dest_path = os.path.join(self.dest_path,self.folderPath)

        #格式化系统标准路径
        if sysutilslib.is_windows():
            self.dest_path = self.dest_path.replace("/",os.sep)
            
    def InitDestpath(self):
        assert(not self._is_wizard)
        self.GetDestpath()
        self.dest_pathVar.set(self.dest_path)
        
    def ShowProgress(self,row):
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=row, sticky="nsew")
        self.label_var = tk.StringVar()
        self.label_ctrl = ttk.Label(sizer_frame,textvariable=self.label_var,width=30)
        self.label_ctrl.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.cur_prog_val = tk.IntVar(value=0)
        self.pb = ttk.Progressbar(sizer_frame,variable=self.cur_prog_val,mode="determinate")
        self.pb.pack(fill="x",padx=(0, 0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        sizer_frame.columnconfigure(0, weight=1)

    def SetFilters(self):
        filter_dlg = FileFilterDialog(self,self.filters,self.rejects)
        if filter_dlg.ShowModal() == constants.ID_OK:
            self.filters = filter_dlg.filters

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
        self.check_listbox.clear()
        self.root_item = self.check_box_view.tree.insert("", "end", text=os.path.basename(path),values=(path,))
        self.current_item = self.root_item
        self.ListDirTreeItem(self.root_item,path)
        self.ListDirFiles(self.root_item)
        self.check_box_view.tree.CheckItem(self.root_item)
        self.check_box_view.tree.focus(self.root_item)
        self.check_box_view.tree.selection_set(self.root_item)
        
    def _on_select(self,event):
        item = self.check_box_view.tree.GetSelectionItem()
        self.SelectItem(item)

    def _box_click(self,event):
        x, y, widget = event.x, event.y, event.widget
        elem = widget.identify("element", x, y)
        if not "image" in elem:
            return
        item = self.check_box_view.tree.identify_row(y)
        self.SelectItem(item)
        
    def SelectItem(self,item):
        #同一个节点无需遍历目录
        if self.current_item == item:
            self.CheckListbox(self.check_box_view.tree.IsItemChecked(item))
            return
        self.current_item = item
        self.ListDirFiles(item,self.check_box_view.tree.IsItemChecked(item))
        
    def ListDirTreeItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isdir(file_path) and not fileutils.is_file_path_hidden(file_path):
                try:
                    item = self.check_box_view.tree.insert(parent_item, "end", text=f,values=(file_path,))
                except:
                    continue
                self.ListDirTreeItem(item,file_path)
        self.check_box_view.tree.item(parent_item, open=True)
        
    def ListDirFiles(self,item,checked=True):
        path = self.check_box_view.tree.item(item)["values"][0]
        if not os.path.exists(path):
            self.check_box_view.clear()
            return
        self.check_listbox.clear()
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isfile(file_path) and not fileutils.is_file_path_hidden(file_path) and not strutils.get_file_extension(file_path) in self.rejects:
                i = self.check_listbox.tree.Append(f)
                self.check_listbox.tree.Check(i,checked)

    def Finish(self):
        global DEFAULT_PROMPT_MESSAGE_ID
        file_list = self.GetImportFileList()
        if 0 == len(file_list):
            return False

        self.GetDestpath()
        if not hasattr(self,"cur_prog_val"):
            self.ShowProgress(self._progress_row)

        self.DisableUI()
        if self._is_wizard:
            self.master.master.ok_button['state'] = tk.DISABLED
            self.master.master.prev_button['state'] = tk.DISABLED
        else:
            self.master.master.ok_button['state'] = tk.DISABLED
        self.pb["maximum"] = len(file_list)
        prev_page = self.GetPrev()
        if GetApp().GetDefaultLangId() == lang.ID_LANG_PYTHON and self._is_wizard:
            if prev_page._new_project_configuration.PythonpathMode == baseconfig.NewProjectConfiguration.PROJECT_ADD_SRC_PATH:
                #目的路径为Src路径
                self.dest_path = os.path.join(self.dest_path,baseconfig.NewProjectConfiguration.DEFAULT_PROJECT_SRC_PATH)
        root_path = self.check_box_view.tree.item(self.root_item)["values"][0]
        self.check_box_view.tree.item(self.root_item,open=True)       
        if not self._is_wizard:
            if self.overwrite_chkboxVar.get():
                DEFAULT_PROMPT_MESSAGE_ID = constants.ID_YESTOALL
            if self.root_folder_chkboxVar.get():
                self.dest_path = os.path.join(self.dest_path,self.check_box_view.tree.item(self.root_item,"text"))
            
        self.notify_queue = queue.Queue()
        GetApp().MainFrame.after(1000,self.ShowImportProgress)
        self.project_browser.StartCopyFilesToProject(self,file_list,root_path,self.dest_path,self.notify_queue)
        return False

    def ShowImportProgress(self):
        GetApp().after(400,self.ShowImportProgress)
        while not self.notify_queue.empty():
            try:
                msg = self.notify_queue.get()
                if msg[0] == None:
                    utils.get_logger().info("finish import code files")
                    self.master.master.destroy()
                else:
                    cur_val,filename = msg
                    self.cur_prog_val.set(cur_val)
                    self.label_var.set(_("importing file:") + filename)
            except queue.Empty:
                pass
        
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
        self.CheckListbox(True)
        
    def CheckListbox(self,check=True):
        for i in range(self.check_listbox.tree.GetCount()):
            self.check_listbox.tree.Check(i,check)
        
    def UnselectAll(self):
        if self.root_item is None:
            return
        self.check_box_view.tree.CheckItem(self.root_item,False)
        self.CheckListbox(False)
        
    def Validate(self):
        if self.root_item is None or not self.check_box_view.tree.IsItemChecked(self.root_item):
            messagebox.showinfo(GetApp().GetAppName(),_("You don't select any file"))
            return False
        return True
        
    def Cancel(self):
        self.is_cancel = True
        if hasattr(self,"cur_prog_val"):
            self.label_var.set("cancel importing file.....")

class ImportfilesDialog(ui_base.CommonModaldialog):
    
    def __init__(self, master,folderPath):
        ui_base.CommonModaldialog.__init__(self, master, takefocus=1)
        self.title(_("Import Files"))
        self.main_frame.content_page = self.main_frame
        project_template = GetApp().GetDocumentManager().FindTemplateForTestPath(consts.PROJECT_EXTENSION)
        #rejects为项目禁止导入的文件类型列表
        self.import_page = ImportfilesPage(self.main_frame,is_wizard=False,folderPath=folderPath,rejects=project_template.GetDocumentType().BIN_FILE_EXTS)
        self.import_page.pack(fill="both",expand=1)
        #初始化目的地址
        self.import_page.InitDestpath()
        self.AddokcancelButton()
        self.ok_button.configure(text=_("&Import"),default="active")
        self.FormatTkButtonText(self.ok_button)

    def _ok(self,event=None):
        if not self.import_page.Validate():
            return
        #导入文件时强制显示项目视图
        GetApp().MainFrame.GetProjectView(show=True)
        if not self.import_page.Finish():
            return
        ui_base.CommonModaldialog._ok(self,event)

    def _cancel(self):
        self.import_page.Cancel()
        ui_base.CommonModaldialog._cancel(self)


class FileFilterDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,filters,rejects=[]):
        self.filters = filters
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(_("File Filters"))
        ttk.Label(self.main_frame, text=_("Please select file types to to allow added to project:")).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.check_listbox_view = treeviewframe.TreeViewFrame(self.main_frame,treeview_class=checklistbox.CheckListbox,borderwidth=1,relief="solid")
        self.check_listbox_view.pack(fill="both",expand=1,padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.listbox = self.check_listbox_view.tree
        ttk.Label(self.main_frame, text=_("Other File Extensions:(seperated by ';')")).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.other_extensions_var = tk.StringVar()
        other_extensions_ctrl = ttk.Entry(self.main_frame,textvariable=self.other_extensions_var)
        other_extensions_ctrl.pack(fill="x",expand=1,padx=consts.DEFAUT_CONTRL_PAD_X)
        self.InitFilters()
        
        self.AddokcancelButton()

    def _ok(self,event=None):
        filters = []
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
               filters.append(self.listbox.GetString(i))
        extension_value = self.other_extensions_var.get().strip()
        if extension_value != "":
            extensions = extension_value.split(";")
            filters.extend(extensions)
        self.filters = [fitler.replace("*","").replace(".","") for fitler in filters]
        ui_base.CommonModaldialog._ok(self,event)
        
    def InitFilters(self):
        descr = ''
        for temp in GetApp().GetDocumentManager().GetTemplates():
            if temp.IsVisible() and temp.GetDocumentName() != 'Project Document':
                filters = temp.GetFileFilter().split(";")
                for filter in filters:
                    i = self.listbox.Append(filter)
                    if str(filter.replace("*","").replace(".","")) in self.filters:
                        self.listbox.Check(i)
