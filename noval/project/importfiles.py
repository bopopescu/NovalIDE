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
    def __init__(self,master,add_bottom_page=True):
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
        self.filters = []
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
        self.root_item = self.check_box_view.tree.insert("", "end", text=os.path.basename(path))
     #   self.check_box_view.tree.set(self.root_item,"path",path)
        self.ListDirTreeItem(self.root_item,path)
        self.ListDirFiles(self.root_item,True,True)
        self.check_box_view.tree.CheckItem(self.root_item)
        
    def _on_select(self,event):
        item = self.check_box_view.tree.GetSelectionItem()
        self.ListDirFiles(item,True,True)
        
    def ListDirTreeItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isdir(file_path):
                item = self.check_box_view.tree.insert(parent_item, "end", text=f)
                self.check_box_view.tree.set(item,"path",file_path)
                self.ListDirTreeItem(item,file_path)
        self.check_box_view.tree.item(parent_item, open=True)
        
    def ListDirFiles(self,item,checked=True,force=False):
        path = self.check_box_view.tree.set(item,"path")
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
            if os.path.isfile(file_path):
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
        root_path = self.check_box_view.tree.set(self.root_item,"path")
       # ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID = wx.ID_YESTOALL
        self.project_browser.StartCopyFilesToProject(self,file_list,root_path,dest_path)
        return False
        
    def GetImportFileList(self):
        file_list = []
        root_path = self.check_box_view.tree.set(self.root_item,"path")
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
        dir_path = self.check_box_view.tree.set(item,"path")
        for i in range(self.check_box_view.tree.GetCount()):
            if self.check_box_view.tree.IsChecked(i):
                f = os.path.join(dir_path,self.check_box_view.tree.GetString(i))
                if self.filters != []:
                    if strutils.GetFileExt(f) in self.filters:
                        file_list.append(f)
                else:
                    file_list.append(f)
            
    def RotateItems(self,parent_item,file_list):
        for item in self.check_box_view.tree.get_children(parent_item):
            if self.check_box_view.tree.IsItemChecked(item):
                dir_path = self.check_box_view.tree.set(item,"path")
                #如果节点未选中则直接从硬盘中获取路径的文件列表
                if not self.IsItemSelected(item):
                    fileutils.GetDirFiles(dir_path,file_list,self.filters)
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

class ImportFilesDialog:
    def __init__(self,parent,dlg_id,title,folderPath):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        self._is_importing = False
        self._stop_importing = False
        projectService = wx.GetApp().GetService(ProjectEditor.ProjectService)
        self.project_view = projectService.GetView()
        project_path = os.path.dirname(self.project_view.GetDocument().GetFilename())
        #project path name is the relative dest path
        self.dest_path = os.path.basename(project_path)
        if folderPath != "":
            self.dest_path = os.path.join(self.dest_path,folderPath)
        if sysutilslib.isWindows():
            self.dest_path = self.dest_path.replace("/",os.sep)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        flagSizer = wx.BoxSizer(wx.HORIZONTAL)
        st_text = wx.StaticText(self,label = _("Local File System"))
        st_text.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
        flagSizer.Add(st_text, 1,flag=wx.LEFT|wx.EXPAND,border = SPACE)  
          
        icon = wx.StaticBitmap(self,bitmap = wx.Bitmap(os.path.join(sysutilslib.mainModuleDir, \
                            "noval", "tool", "bmp_source", "python_logo.png")))  
        flagSizer.Add(icon,0,flag=wx.TOP|wx.RIGHT,border = HALF_SPACE)
        boxsizer.Add(flagSizer,0,flag=wx.EXPAND|wx.ALL,border = HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        line = wx.StaticLine(self)
        lineSizer.Add(line,1,flag = wx.LEFT|wx.EXPAND,border = 0)
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.BOTTOM,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        dirLabelText = wx.StaticText(self, -1, _('Source Location:'))
        lineSizer.Add(dirLabelText,0,flag=wx.LEFT,border=SPACE)
        self.dirControl = wx.TextCtrl(self, -1)
        self.Bind(wx.EVT_TEXT,self.ChangeDir)
        lineSizer.Add(self.dirControl,1,flag=wx.LEFT|wx.EXPAND,border=SPACE) 
        self.browser_btn = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(self.browser_btn, -1, self.BrowsePath)
        lineSizer.Add(self.browser_btn, 0,flag=wx.LEFT, border=SPACE) 
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT,border = SPACE) 
        
        templates = wx.GetApp().GetDocumentManager().GetTemplates()
        iconList = wx.ImageList(16, 16, initialCount = len(templates))
                
        folder_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "packagefolder_obj.gif")
        folder_bmp = wx.Bitmap(folder_bmp_path, wx.BITMAP_TYPE_GIF)
        self.FolderIdx = iconList.Add(folder_bmp)
        
        listSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._treeCtrl = CT.CustomTreeCtrl(self, size=(300,250),style = wx.BORDER_THEME,agwStyle = wx.TR_DEFAULT_STYLE|CT.TR_AUTO_CHECK_CHILD|CT.TR_AUTO_CHECK_PARENT)
        self._treeCtrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX))
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.checked_item)
        wx.EVT_LEFT_DOWN(self._treeCtrl, self.OnLeftClick)
        listSizer.Add(self._treeCtrl,flag=wx.LEFT|wx.RIGHT,border=SPACE)
        self._treeCtrl.AssignImageList(iconList)
        
        self.listbox = wx.CheckListBox(self,-1,size=(300,250),choices=[])
        self.Bind(wx.EVT_CHECKLISTBOX,self.CheckBoxFile)
        listSizer.Add(self.listbox,1,flag=wx.TOP|wx.EXPAND,border=0)
        boxsizer.Add(listSizer,0,flag = wx.EXPAND|wx.BOTTOM|wx.TOP|wx.RIGHT,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.file_filter_btn = wx.Button(self, -1, _("File Filters"))
        wx.EVT_BUTTON(self.file_filter_btn, -1, self.ShowFilterFileDialog)
        lineSizer.Add(self.file_filter_btn, 0,flag=wx.LEFT, border=SPACE)
        self.filters = []
        
        self.select_all_btn = wx.Button(self, -1, _("Select All"))
        wx.EVT_BUTTON(self.select_all_btn, -1, self.SelectAll)
        lineSizer.Add(self.select_all_btn, 0,flag=wx.LEFT, border=SPACE)
        
        self.unselect_all_btn = wx.Button(self, -1, _("UnSelect All"))
        wx.EVT_BUTTON(self.unselect_all_btn, -1, self.UnSelectAll)
        lineSizer.Add(self.unselect_all_btn, 0,flag=wx.LEFT, border=SPACE)
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT,border = SPACE) 
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        destdirLabelText = wx.StaticText(self, -1, _('Dest Directory:'))
        lineSizer.Add(destdirLabelText,0,flag=wx.LEFT,border=0)
        self.destDirCtrl = wx.TextCtrl(self, -1,self.dest_path,size=(200,-1))
        self.destDirCtrl.Enable(False)
        lineSizer.Add(self.destDirCtrl,0,flag=wx.LEFT,border=SPACE)
        boxsizer.Add(lineSizer,0,flag = wx.ALL,border = SPACE)
        
        sbox = wx.StaticBox(self, -1, _("Option"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        self.overwrite_chkbox = wx.CheckBox(self, label = _("Overwrite existing files without warning"))
        sboxSizer.Add(self.overwrite_chkbox , flag=wx.LEFT|wx.TOP, border=HALF_SPACE)
        self.root_folder_chkbox = wx.CheckBox(self, label = _("Create top-level folder"))
        sboxSizer.Add(self.root_folder_chkbox,flag=wx.LEFT|wx.TOP, border=HALF_SPACE)
        boxsizer.Add(sboxSizer, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT , border=SPACE) 
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.m_gauge = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        lineSizer.Add(self.m_gauge,1,flag = wx.LEFT|wx.EXPAND,border = 0)
        boxsizer.Add(lineSizer,0,flag = wx.BOTTOM|wx.EXPAND,border = SPACE)
        Publisher.subscribe(self.UpdateImportProgress,NOVAL_MSG_UI_IMPORT_FILES_PROGRESS)
        
        bsizer = wx.StdDialogButtonSizer()
        self.ok_btn = wx.Button(self, wx.ID_OK, _("&Import"))
        wx.EVT_BUTTON(self.ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        self.ok_btn.SetDefault()
        bsizer.AddButton(self.ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        wx.EVT_BUTTON(cancel_btn, -1, self.OnCancelClick)
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        
        self.SetSizer(boxsizer)
        self.m_gauge.Hide()
        self.Fit()
        
    def ShowFilterFileDialog(self,event):
        file_filter_dlg = ProjectUI.FileFilterDialog(self,-1,_("File Filters"),self.filters)
        file_filter_dlg.ShowModal()
        self.filters = file_filter_dlg.filters
        file_filter_dlg.Destroy()
        
    def CheckAllItems(self,parent_item,check=True):
        (item, cookie) = self._treeCtrl.GetFirstChild(parent_item)
        while item:
            if self._treeCtrl.IsItemChecked(item):
                if not check:
                    self._treeCtrl.CheckItem2(item, False,True)
            else:
                if check:
                    self._treeCtrl.CheckItem2(item, True,True)
            self.CheckAllItems(item,check)
            (item, cookie) = self._treeCtrl.GetNextChild(parent_item, cookie)
        
    def SelectAll(self,event):
        root_item = self._treeCtrl.GetRootItem()
        if root_item is None:
            return
        self._treeCtrl.CheckItem2(root_item, True,True)
        self.CheckAllItems(root_item)
        self.ListDirFiles(self._treeCtrl.GetSelection(),True,False)
        
    def UnSelectAll(self,event):
        root_item = self._treeCtrl.GetRootItem()
        if root_item is None:
            return
        self._treeCtrl.CheckItem2(root_item, False,True)
        self.CheckAllItems(root_item,False)
        self.ListDirFiles(self._treeCtrl.GetSelection(),False,False)
        
    def ChangeDir(self,event):
        path = self.dirControl.GetValue().strip()
        if path == "":
            self._treeCtrl.DeleteAllItems()
            return
        if sysutilslib.isWindows():
            path = path.replace("/",os.sep)
        self.ListDirItemFiles(path.rstrip(os.sep))
        
    def checked_item(self, event):
        item = event.GetItem()
        is_item_checked = self._treeCtrl.IsItemChecked(item)
        self.ListDirFiles(item,is_item_checked)
        if is_item_checked:
            self.check_parent_item(item)

    def check_parent_item(self,item):
        parent_item = self._treeCtrl.GetItemParent(item)
        while parent_item:
            #will not cause checked_item event
            if not self._treeCtrl.IsItemChecked(parent_item):
                self._treeCtrl.CheckItem2(parent_item, True,True)
            parent_item = self._treeCtrl.GetItemParent(parent_item)
        
    def OnOKClick(self, event):
        root_item = self._treeCtrl.GetRootItem()
        if root_item is None or not self._treeCtrl.IsItemChecked(root_item):
            wx.MessageBox(_("You don't select any file"))
            return
        root_path = self._treeCtrl.GetPyData(root_item)
        file_list = []
        dir_path = self._treeCtrl.GetPyData(root_item)
        if not self.IsItemSelected(root_item):
            fileutils.GetDirFiles(dir_path,file_list,self.filters)
         #get checked tree item file list
        else:
            self.GetCheckedItemFiles(root_item,file_list)
        self.RotateItems(root_item,file_list)
        if 0 == len(file_list):
            wx.MessageBox(_("You don't select any file"))
            return
        project_file_path = self.project_view.GetDocument().GetFilename()
        if project_file_path in file_list:
            file_list.remove(project_file_path)
        self.m_gauge.Show()
        self.GetSizer().Layout()
        self.Fit()
        self.ok_btn.Enable(False)
        self.dirControl.Enable(False)
        self.browser_btn.Enable(False)
        self.select_all_btn.Enable(False)
        self.unselect_all_btn.Enable(False)
        self.file_filter_btn.Enable(False)
        self.m_gauge.SetRange(len(file_list))
        self._is_importing = True
        self.project_view.StopImport(False)
        
        if self.overwrite_chkbox.GetValue():
            ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID = wx.ID_YESTOALL
        if self.root_folder_chkbox.GetValue():
            self.dest_path = os.path.join(self.dest_path,self._treeCtrl.GetItemText(root_item))
            
        self.project_view.StartCopyFilesToProject(self,file_list,root_path,self.dest_path)
        
    def OnCancelClick(self, event):
        if self._is_importing:
            self._stop_importing = True
            self.project_view.StopImport(True)
        else:
            self.EndModal(wx.ID_CANCEL)
            
    def UpdateImportProgress(self,value,is_cancel):
        self.m_gauge.SetValue(value)
        if is_cancel:
            print ('cancel import .........')
            self.EndModal(wx.ID_CANCEL)
        elif self.m_gauge.GetRange() <= value:
            self.EndModal(wx.ID_OK)
            
    def CheckBoxFile(self,event):
        sel_item = self._treeCtrl.GetSelection()
        if self.listbox.IsChecked(event.GetInt()):
            if not self._treeCtrl.IsItemChecked(sel_item):
                self._treeCtrl.CheckItem2(sel_item, True,True)
        else:
            checked_item_count = 0
            for i in range(self.listbox.GetCount()):
                if self.listbox.IsChecked(i):
                    checked_item_count += 1
            if 0 == checked_item_count:
                self._treeCtrl.CheckItem(sel_item, False)
            
    def IsItemSelected(self,item):
        return self._treeCtrl.GetSelection() == item
        
    def GetCheckedItemFiles(self,item,file_list):
        dir_path = self._treeCtrl.GetPyData(item)
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                f = os.path.join(dir_path,self.listbox.GetString(i))
                if self.filters != []:
                    if strutils.GetFileExt(f) in self.filters:
                        file_list.append(f)
                else:
                    file_list.append(f)
            
    def RotateItems(self,parent_item,file_list):
        if parent_item is None or not self._treeCtrl.IsItemChecked(parent_item):
            return
       
        (item, cookie) = self._treeCtrl.GetFirstChild(parent_item)
        while item:
            if self._treeCtrl.IsItemChecked(item):
                dir_path = self._treeCtrl.GetPyData(item)
                if not self.IsItemSelected(item):
                    fileutils.GetDirFiles(dir_path,file_list,self.filters)
                #get checked tree item file list    
                else:
                    self.GetCheckedItemFiles(item,file_list)
            self.RotateItems(item,file_list)
            (item, cookie) = self._treeCtrl.GetNextChild(parent_item, cookie)
        
        
    def BrowsePath(self,event):
        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(),
                _("Choose the location"), 
                style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        #will cause wx.EVT_TEXT event
        self.dirControl.SetValue(path)
        
    def ListDirItemFiles(self,path):
        self._treeCtrl.DeleteAllItems()
        root_item = self._treeCtrl.AddRoot(os.path.basename(path),ct_type=1)
        self._treeCtrl.SetPyData(root_item,path)
        self._treeCtrl.SetItemImage(root_item,self.FolderIdx,wx.TreeItemIcon_Normal)
        self.ListDirItem(root_item,path)
        self.ListDirFiles(root_item,True,True)
        self._treeCtrl.CheckItem(root_item, True)
        
    def ListDirItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isdir(file_path):
                item = self._treeCtrl.AppendItem(parent_item, f,ct_type=1)
                self._treeCtrl.SetItemImage(item,self.FolderIdx,wx.TreeItemIcon_Normal)
                self._treeCtrl.SetPyData(item,file_path)
                self.ListDirItem(item,file_path)
        self._treeCtrl.Expand(parent_item)
                
    def OnLeftClick(self, event):
        item, flags = self._treeCtrl.HitTest(event.GetPosition())
        if item is not None and item.IsOk():
            file_path = self._treeCtrl.GetPyData(item)
            checked = self._treeCtrl.IsItemChecked(item)
            self.ListDirFiles(item,checked)
            if not self.IsItemSelected(item):
                self._treeCtrl.SelectItem(item)
        event.Skip()
        
    def ListDirFiles(self,item,checked=True,force=False):
        path = self._treeCtrl.GetPyData(item)
        if not os.path.exists(path):
            self.listbox.Clear()
            return
        if self._treeCtrl.GetSelection() == item and not force:
            for i in range(self.listbox.GetCount()):
                if checked:
                    if not self.listbox.IsChecked(i):
                        self.listbox.Check(i,True)
                else:
                    if self.listbox.IsChecked(i):
                        self.listbox.Check(i,False)
                    
            return
        self.listbox.Clear()
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isfile(file_path):
                i = self.listbox.Append(f)
                self.listbox.Check(i,checked)
                    
                
        