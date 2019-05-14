# -*- coding: utf-8 -*-
from noval import GetApp,_,core,constants
import os
import tkinter as tk
from tkinter import messagebox,filedialog
import noval.consts as consts
from tkinter import ttk
import noval.util.utils as utils
import noval.util.fileutils as fileutils
import noval.util.strutils as strutils
import noval.project.baseviewer as baseviewer
import noval.imageutils as imageutils
import noval.menu as tkmenu
import noval.misc as misc
import threading
from noval.project.command import ProjectAddProgressFilesCommand

def AddProjectMapping(doc, projectDoc=None, hint=None):
    project_view = GetApp().MainFrame.GetProjectView()
    if not projectDoc:
        if not hint:
            hint = doc.GetFilename()
        projectDocs = project_view.FindProjectByFile(hint)
        if projectDocs:
            projectDoc = projectDocs[0]
            
    project_view.AddProjectMapping(doc, projectDoc)
    if hasattr(doc, "GetModel"):
        project_view.AddProjectMapping(doc.GetModel(), projectDoc)

class ProjectTreeCtrl(ttk.Treeview):
    
    #用来设置粗体节点,粗体节点用来表示项目启动文件
    BOLD_TAG = 'BoldItem'

    #----------------------------------------------------------------------------
    # Overridden Methods
    #----------------------------------------------------------------------------

    def __init__(self, master, **kw):
        ttk.Treeview.__init__(self, master, **kw)
        self._iconLookup = {}
        self._blankIconImage = imageutils.getBlankIcon()
        self._packageFolderImage = imageutils.getPackageFolderIcon()
        self._folderClosedImage = imageutils.getFolderClosedIcon()
        
    def SelectItem(self,node):
        self.selection_set(node)
        self.focus(node)
        
    def BuildLookupIcon(self):
        if 0 == len(self._iconLookup):
            templates = GetApp().GetDocumentManager().GetTemplates()
            for template in templates:
                icon = template.GetIcon()
                self._iconLookup[template] = icon
        
        
    #设置项目启动文件节点为粗体
    def SetItemBold(self,node):
        self.item(node, tags=(self.BOLD_TAG))
        self.tag_configure(self.BOLD_TAG, font=consts.TREE_VIEW_BOLD_FONT)
        
    def GetPyData(self,node):
        values = self.item(node)["values"]
        if type(values) == str:
            return None
        return values[0]
        
    def SortChildren(self,node):
        # update tree
        children = self.get_children(node)
        if utils.is_py2():
            ids_sorted_by_name = sorted(children, cmp=self.OnCompareItems)
        elif utils.is_py3():
            import functools
            ids_sorted_by_name = sorted(children, key=functools.cmp_to_key(self.OnCompareItems))
        self.set_children(node, *ids_sorted_by_name)
        
    def DeleteChildren(self,node):
        for child_id in self.get_children(node):
            self.delete(child_id)

    def GetRootItem(self):
        return self.GetFirstChild(None)
        
    def GetFirstChild(self,item):
        childs = self.get_children(item)
        if 0 == len(childs):
            return None
        return childs[0]

    def OnCompareItems(self, item1, item2):
        item1IsFolder = (self.GetPyData(item1) == None)
        item2IsFolder = (self.GetPyData(item2) == None)
        if (item1IsFolder == item2IsFolder):  # if both are folders or both not
            #python3没有cmp函数,自己实现一个
            if utils.is_py2():
                return cmp(self.item(item1,"text").lower(), self.item(item2,"text").lower())
            elif utils.is_py3():
                return utils.py3_cmp(self.item(item1,"text").lower(), self.item(item2,"text").lower())
        elif item1IsFolder and not item2IsFolder: # folders sort above non-folders
            return -1
        elif not item1IsFolder and item2IsFolder: # folders sort above non-folders
            return 1
        
    def AppendFolder(self, parent, folderName):
        item = self.insert(parent, "end", text=folderName, image=self._folderClosedImage)
        return item
        
    def GetIconFromName(self,filename):
        template = wx.GetApp().GetDocumentManager().FindTemplateForPath(filename)
        return self.GetTemplateIcon(template)
        
    def GetProjectIcon(self):
        template = GetApp().GetDocumentManager().FindTemplateForTestPath(consts.PROJECT_EXTENSION)
        project_file_image = self.GetTemplateIcon(template)
        return project_file_image
        
    def GetTemplateIcon(self,template):
        self.BuildLookupIcon()
        if template in self._iconLookup:
            return self._iconLookup[template]
        return self._blankIconImage

    def AppendItem(self, parent, filename, file):
        #如果是虚拟文件,则不创建树节点
        if filename == consts.DUMMY_NODE_TEXT:
            return None
            
        template = GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME).GetView().GetOpenDocumentTemplate(file)
        found = False
        if template is None:
            template = GetApp().GetDocumentManager().FindTemplateForPath(filename)
        file_image = self.GetTemplateIcon(template)
        #valus参数必须用tuple类型,不能用str类型,否则会数据存储错误
        item = self.insert(parent, "end", text=filename, image=file_image,values=(file.filePath,))
   #     self.set(item, "path", file.filePath)
        return item

    def AddFolder(self, folderPath):
        folderItems = []
        
        if folderPath != None:
            folderTree = folderPath.split('/')
            
            item = self.GetRootItem()
            for folderName in folderTree:
                found = False
                for child in self.get_children(item):
                    file = self.GetPyData(child)
                    if file:
                        pass
                    else: # folder
                        if self.item(child, "text") == folderName:
                            item = child
                            found = True
                            break
                    
                if not found:
                    item = self.AppendFolder(item, folderName)
                    folderItems.append(item)

        return folderItems
        

    def FindItem(self, filePath, parentItem=None):
        if not parentItem:
            parentItem = self.GetRootItem()
            
        for child in self.get_children(parentItem):
            child_file_path = self.GetPyData(child)
            if child_file_path:
                if child_file_path == filePath:
                    return child
            else: # folder
                result = self.FindItem(filePath, child)  # do recursive call
                if result:
                    return result
        
        return None


    def FindFolder(self, folderPath):
        if folderPath != None:
            folderTree = folderPath.split('/')
            
            item = self.GetRootItem()
            for folderName in folderTree:
                found = False
                for child in self.get_children(item):
                    file = self.GetPyData(child)
                    if file:
                        pass
                    else: # folder
                        if self.item(child, "text") == folderName:
                            item = child
                            found = True
                            break
                    
            if found:
                return item
                
        return None


    def FindClosestFolder(self, x, y):
        item, flags = self.HitTest((x,y))
        if item:
            file = self.GetPyData(item)
            if file:
                item = self.GetItemParent(item)
                return item
            return item
        return None

    def GetSingleSelectItem(self):
        items = self.GetSelections()
        if not items:
            return None
        return items[0]

class BaseProjectbrowser(ttk.Frame):
    def __init__(
        self,
        master,
        columns=["#0", "kind", "path"],
        displaycolumns="#all",
        show_scrollbar=True,
        borderwidth=0,
        relief="flat",
        **tree_kw
    ):
        ttk.Frame.__init__(self, master, borderwidth=borderwidth, relief=relief)
        #文档和项目的对照表
        self._mapToProject = dict()
        #绑定ShowView事件,在事件中加载保存的历史项目列表
        GetApp().bind("ShowView", self.Show, True)
        # http://wiki.tcl.tk/44444#pagetoc50f90d9a
        self.vert_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, style=None
        )
        if show_scrollbar:
            self.vert_scrollbar.grid(row=1, column=1, sticky=tk.NSEW)
            
        self.project_combox = ttk.Combobox(self)
        self.project_combox.bind("<<ComboboxSelected>>",self.ProjectSelect)
        self.project_combox.grid(row=0, column=0, sticky=tk.NSEW)
        #设置combox只读不能编辑
        self.project_combox.state(['readonly'])
        self.tree = self.GetProjectTreectrl(**tree_kw)

        #控件默认会显示头部,此处用以屏蔽头部的显示
        self.tree.column("#0", anchor=tk.W, stretch=True)
        self.tree["show"] = ("tree",)
        self.tree.grid(row=1, column=0, sticky=tk.NSEW)
        self.vert_scrollbar["command"] = self.tree.yview
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        #鼠标双击Tree控件事件
        self.tree.bind("<Double-Button-1>", self.on_double_click, "+")
        #展开节点时记住并保存子节点展开状态
        self.tree.bind("<<TreeviewOpen>>", self.OpenTreeItem)
        #软件启动时加载存储配置保存的历史项目列表,记住这个状态
        self._is_loading = False
        #创建项目视图,所有项目共享同一个视图,必须在函数的最后创建
        view = self.CreateView()
        self.SetView(view)
        self.GetView().AddProjectRoot(_("Projects"))
        GetApp().bind("InitTkDnd",self.SetDropTarget,True)
        self.tree.bind("<3>", self.on_secondary_click, True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select, True)
        #是否停止导入代码
        self.stop_import = False
        
    def SetDropTarget(self,event):
        #项目视图允许拖拽添加文件
        if GetApp().dnd is not None and utils.profile_get_int('ALLOW_DROP_OPENFILE',True):
            GetApp().dnd.bindtarget(self, baseviewer.ProjectFileDropTarget(self.GetView()), 'text/uri-list')
        
    def GetProjectTreectrl(self,**tree_kw):
        return ProjectTreeCtrl(self,
            yscrollcommand=self.vert_scrollbar.set,**tree_kw)
    
    def _on_select(self,event):
        #选中项目节点时设置项目视图为活跃视图
        GetApp().GetDocumentManager().ActivateView(self.GetView())

    def _clear_tree(self):
        for child_id in self.tree.get_children():
            self.tree.delete(child_id)

    def clear(self):
        self._clear_tree()            

    def GetItemFilePath(self, item):
        data = self.tree.GetPyData(item)
        if data:
            return data
        else:
            return None
            
    def GetItemFile(self, item):
        file_path = self.GetItemFilePath(item)
        if not file_path:
            return None
        return self.GetView().GetDocument().GetModel().FindFile(file_path)

    def on_double_click(self, event):
        doc = None
        try:
            item = self.tree.selection()[0]
            filepath = self.GetItemFilePath(item)
            file_template = None
            if filepath:
                if not os.path.exists(filepath):
                    msgTitle = GetApp().GetAppName()
                    if not msgTitle:
                        msgTitle = _("File Not Found")
                    ret = messagebox.askyesno(msgTitle,_("The file '%s' was not found in '%s'.\n\nWould you like to browse for the file?") \
                                        % (fileutils.get_filename_from_path(filepath), fileutils.get_filepath_from_path(filepath)),parent=self)
                    #选中否
                    if not ret:
                        return
                    newpath = filedialog.askopenfilename(
                            master=self,
                           ### filetypes=descrs,
                            initialdir=os.getcwd(),
                            title = _("Choose a file"),
                            initialfile = fileutils.get_filename_from_path(filepath)
                    )
                    if newpath:
                        # update Project Model with new location
                        self.GetView().GetDocument().UpdateFilePath(filepath, newpath)
                        filepath = newpath
                    else:
                        #选择取消按钮
                        return
                else:        
                    project_file = self.GetItemFile(item)
                    file_template = self.GetView().GetOpenDocumentTemplate(project_file)
                if file_template:
                    doc = GetApp().GetDocumentManager().CreateTemplateDocument(file_template,filepath, wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
                else:
                    docs = GetApp().GetDocumentManager().CreateDocument(filepath, core.DOC_SILENT|core.DOC_OPEN_ONCE)
                if not docs and filepath.endswith(consts.PROJECT_EXTENSION):  # project already open
                    self.SetProject(filepath)
                elif docs:
                    AddProjectMapping(docs[0])
                        

        except IOError as e:
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            wx.MessageBox("Could not open '%s'." % wx.lib.docview.FileNameFromPath(filepath),
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION,
                          self.GetFrame())
            
    def GetView(self):
        return self._view
        
    def CreateView(self):
        return baseviewer.ProjectView(self)
        
    def SetView(self,view):
        self._view = view
        
    def AddProject(self,name):
        if type(self.project_combox['values']) == str:
            self.project_combox['values'] = [name]
            return 0
        else:
            self.project_combox['values'] = self.project_combox['values'] + (name,)
            return len(self.project_combox['values']) - 1
            
    def LoadSavedProjects(self):
        self._is_loading = True
        openedDocs = False
        if utils.profile_get_int(consts.PROJECT_DOCS_SAVED_KEY, True):
            docString = utils.profile_get(consts.PROJECT_SAVE_DOCS_KEY)
            if docString:
                doc = None
                docList = eval(docString)
                for fileName in docList:
                    if isinstance(fileName, str) and \
                            strutils.get_file_extension(fileName) == consts.PROJECT_SHORT_EXTENSION:
                        if utils.is_py2():
                            fileName = fileName.decode("utf-8")
                        if os.path.exists(fileName):
                            doc = GetApp().GetDocumentManager().CreateDocument(fileName, core.DOC_SILENT|core.DOC_OPEN_ONCE)
                if doc:
                    openedDocs = True
        self._is_loading = False
        return openedDocs
        
    def SetCurrentProject(self):
        #如果是命令行打开项目,则设置该项目为当前项目
        open_project_path = GetApp().OpenProjectPath
        if open_project_path is not None:
            self.GetView().SetProject(open_project_path)
        #否则从存储配置中加载当前项目
        else:
            currProject = utils.profile_get(consts.CURRENT_PROJECT_KEY)
            docList = [document.GetFilename() for document in self.GetView().Documents]
            #从所有存储项目中查找是否存在当前项目,如果存在则加载为活跃项目
            if currProject in docList:
                self.GetView().SetProject(currProject)
          
    @property
    def IsLoading(self):
        return self._is_loading
        
    def SetFocus(self):
        self.focus_set()
        self.tree.focus_set()
        
    def ProjectSelect(self,event):
        self.GetView().ProjectSelect()
        
    def Show(self,event):
        if event.get('view_name') != consts.PROJECT_VIEW_NAME:
            utils.get_logger().info("project view could not handler view %s showview event",event.get('view_name'))
            return
        project = self.GetView().GetDocument()
        #加载存储项目
        if not project:
            self.LoadSavedProjects()
            
    def OpenTreeItem(self,event):
        #项目列表为空时不处理事件
        if self.GetView().GetDocument() == None:
            return
        self.GetView().SaveFolderState()
        
    def FindProjectFromMapping(self, key):
        """ 从对照表中快速查找文档对应的项目"""
        return self._mapToProject.get(key,None)

    def AddProjectMapping(self, key, projectDoc=None):
        """ 设置文档或者其他对象对应的项目
        """
        if not projectDoc:
            projectDoc = self.GetCurrentProject()
        self._mapToProject[key] = projectDoc

    def RemoveProjectMapping(self, key):
        """ Remove mapping from model or document to project.  """
        if key in self._mapToProject:
            del self._mapToProject[key]
            
    def GetCurrentProject(self):
        view = self.GetView()
        if view:
            return view.GetDocument()
        return None

    def FindProjectByFile(self, filename):
        '''查找包含文件的所有项目文档,当前项目文档放在第一位'''
        retval = []
        for document in GetApp().GetDocumentManager().GetDocuments():
            #文档类型为项目文档
            if document.GetDocumentTemplate().GetDocumentType() == baseviewer.ProjectDocument:
                if document.GetFilename() == filename:
                    retval.append(document)
                #项目文档是否包含该文件
                elif document.IsFileInProject(filename):
                    retval.append(document)
                    
        #将当前项目置于第一位
        currProject = self.GetCurrentProject()
        if currProject and currProject in retval:
            retval.remove(currProject)
            retval.insert(0, currProject)
                
        return retval
        
    def _InitCommands(self):
        GetApp().AddCommand(constants.ID_NEW_PROJECT,_("&Project"),_("New Project"),self.NewProject,image="project/new.png")
        GetApp().AddCommand(constants.ID_OPEN_PROJECT,_("&Project"),_("Open Project"),self.OpenProject,image="project/open.png")
        GetApp().AddCommand(constants.ID_CLOSE_PROJECT,_("&Project"),_("Close Project"),self.CloseProject,tester=lambda:self.GetView().UpdateUI(constants.ID_CLOSE_PROJECT))
        GetApp().AddCommand(constants.ID_SAVE_PROJECT,_("&Project"),_("Save Project"),self.SaveProject,image="project/save.png",tester=lambda:self.GetView().UpdateUI(constants.ID_SAVE_PROJECT))
        GetApp().AddCommand(constants.ID_DELETE_PROJECT,_("&Project"),_("Delete Project"),self.DeleteProject,image="project/trash.png",tester=lambda:self.GetView().UpdateUI(constants.ID_DELETE_PROJECT))
        GetApp().AddCommand(constants.ID_CLEAN_PROJECT,_("&Project"),_("Clean Project"),self.CleanProject,tester=lambda:self.GetView().UpdateUI(constants.ID_CLEAN_PROJECT))
        GetApp().AddCommand(constants.ID_ARCHIVE_PROJECT,_("&Project"),_("Archive Project"),self.ArchiveProject,image="project/archive.png",add_separator=True,tester=lambda:self.GetView().UpdateUI(constants.ID_ARCHIVE_PROJECT))
        GetApp().AddCommand(constants.ID_IMPORT_FILES,_("&Project"),_("Import Files..."),None,image=GetApp().GetImage("project/import.png"))
        GetApp().AddCommand(constants.ID_ADD_FILES_TO_PROJECT,_("&Project"),_("Add &Files to Project..."),None)
        GetApp().AddCommand(constants.ID_ADD_CURRENT_FILE_TO_PROJECT,_("&Project"),_("Add Directory Files to Project..."),None,add_separator=True)
        GetApp().AddCommand(constants.ID_NEW_PROJECT,_("&Project"),_("New Project"),None,image=GetApp().GetImage("project/new.png"))
        

    def NewProject(self):
        '''
            新建项目
        '''
        template = GetApp().GetDocumentManager().FindTemplateForTestPath(consts.PROJECT_EXTENSION)
        template.CreateDocument("", flags = core.DOC_NEW)
                
    def OpenProject(self):
        '''
            打开项目
        '''
        template = GetApp().GetDocumentManager().FindTemplateForTestPath(consts.PROJECT_EXTENSION)
        descrs = [strutils.get_template_filter(template),]
        project_path = filedialog.askopenfilename(
            master=GetApp(),
            filetypes=descrs,
            initialdir=template.GetDirectory()
        )
        if not project_path:
            return
        docs = GetApp().GetDocumentManager().CreateDocument(project_path, core.DOC_SILENT|core.DOC_OPEN_ONCE)
        if not docs:  # project already open
            self.SetProject(project_path)
        elif docs:
            AddProjectMapping(docs[0])
          
    @misc.update_toolbar  
    def CloseProject(self):
        self.GetView().CloseProject()
        
    @misc.update_toolbar
    def SaveProject(self):
        self.GetView().SaveProject()
        
    @misc.update_toolbar
    def DeleteProject(self):
        self.GetView().DeleteProject()

    def ArchiveProject(self):
        self.GetView().ArchiveProject()

    def CleanProject(self):
        self.GetView().CleanProject()
            
    def GetFilesFromCurrentProject(self):
        view = self.GetView()
        if view:
            project = view.GetDocument()
            if project:
                return project.GetFiles()
        return None
        
    def on_secondary_click(self, event):
        node_id = self.tree.identify_row(event.y)
        if node_id:
            self.tree.selection_set(node_id)
            self.tree.focus(node_id)
            if not self.tree.parent(node_id):
                menu = self.GetPopupProjectMenu()
            else:
                menu = self.GetPopupFileMenu()
        menu["postcommand"] = lambda: menu._update_menu()
        menu.tk_popup(event.x_root, event.y_root)

    def GetPopupFileMenu(self):
        menu = tkmenu.PopupMenu(self,**misc.get_style_configuration("Menu"))
        menu.Append(constants.ID_OPEN_SELECTION, _("&Open"))
        common_item_ids = [None,consts.ID_UNDO,consts.ID_REDO,consts.ID_CUT,consts.ID_COPY,consts.ID_PASTE,consts.ID_CLEAR,None,consts.ID_SELECTALL]
        self.GetCommonItemsMenu(menu,common_item_ids)
        
        menu.Append(constants.ID_RENAME,_("&Rename"),handler=lambda:self.ProcessEvent(constants.ID_RENAME))
        menu.Append(constants.ID_REMOVE_FROM_PROJECT,_("Remove from Project"),handler=lambda:self.ProcessEvent(constants.ID_REMOVE_FROM_PROJECT))
##        tree_item = self._treeCtrl.GetSingleSelectItem()
##        filePath = self._GetItemFilePath(tree_item)
##        itemIDs = []
##        if self._IsItemFile(tree_item) and fileutils.is_python_file(filePath):
##            menuBar = wx.GetApp().GetTopWindow().GetMenuBar()
##            menu_item = menuBar.FindItemById(constants.ID_RUN)
##            item = wx.MenuItem(menu,constants.ID_START_RUN,_("&Run"), kind = wx.ITEM_NORMAL)
##            item.SetBitmap(menu_item.GetBitmap())
##            menu.AppendItem(item)
##            wx.EVT_MENU(self._treeCtrl, constants.ID_START_RUN, self.ProcessEvent)
##            
##            debug_menu = wx.Menu()
##            menu.AppendMenu(wx.NewId(), _("Debug"), debug_menu)
##
##            menu_item = menuBar.FindItemById(constants.ID_DEBUG)
##            item = wx.MenuItem(menu,constants.ID_START_DEBUG,_("&Debug"), kind = wx.ITEM_NORMAL)
##            item.SetBitmap(menu_item.GetBitmap())
##            debug_menu.AppendItem(item)
##            wx.EVT_MENU(self._treeCtrl, constants.ID_START_DEBUG, self.ProcessEvent)
##            
##            item = wx.MenuItem(menu,constants.ID_BREAK_INTO_DEBUGGER,_("&Break into Debugger"), kind = wx.ITEM_NORMAL)
##            debug_menu.AppendItem(item)
##            wx.EVT_MENU(self._treeCtrl, constants.ID_BREAK_INTO_DEBUGGER, self.ProcessEvent)
##            if tree_item != self._bold_item:
##                menu.Append(constants.ID_SET_PROJECT_STARTUP_FILE, _("Set as Startup File..."), _("Set the start script of project"))
##                wx.EVT_MENU(self._treeCtrl, constants.ID_SET_PROJECT_STARTUP_FILE, self.ProcessEvent)
##                wx.EVT_UPDATE_UI(self._treeCtrl, constants.ID_SET_PROJECT_STARTUP_FILE, self.ProcessUpdateUIEvent)
##            itemIDs.append(None)
##        itemIDs.append(Property.FilePropertiesService.PROPERTIES_ID)
##        self.GetCommonItemsMenu(menu,itemIDs)
##        menu.Append(constants.ID_OPEN_FOLDER_PATH, _("Open Path in Explorer"))
##        wx.EVT_MENU(self._treeCtrl, constants.ID_OPEN_FOLDER_PATH, self.ProcessEvent)
##        
##        menu.Append(constants.ID_OPEN_TERMINAL_PATH, _("Open Command Prompt here..."))
##        wx.EVT_MENU(self._treeCtrl, constants.ID_OPEN_TERMINAL_PATH, self.ProcessEvent)
##
##        menu.Append(constants.ID_COPY_PATH, _("Copy Full Path"))
##        wx.EVT_MENU(self._treeCtrl, constants.ID_COPY_PATH, self.ProcessEvent)
        
        return menu

    def GetPopupFolderMenu(self):
        menu = wx.Menu()
        itemIDs = [constants.ID_IMPORT_FILES,constants.ID_ADD_FILES_TO_PROJECT, \
                           constants.ID_ADD_DIR_FILES_TO_PROJECT,constants.ID_ADD_NEW_FILE,constants.ID_ADD_FOLDER, constants.ID_ADD_PACKAGE_FOLDER]
        itemIDs.extend([None,wx.ID_UNDO, wx.ID_REDO, None, wx.ID_CUT, wx.ID_COPY, wx.ID_PASTE, wx.ID_CLEAR,None, \
                            wx.ID_SELECTALL,ProjectService.RENAME_ID , constants.ID_REMOVE_FROM_PROJECT, None, Property.FilePropertiesService.PROPERTIES_ID])
        self.GetCommonItemsMenu(menu,itemIDs)
        
        menu.Append(constants.ID_OPEN_FOLDER_PATH, _("Open Path in Explorer"))
        wx.EVT_MENU(self._treeCtrl, constants.ID_OPEN_FOLDER_PATH, self.ProcessEvent)
        
        menu.Append(constants.ID_OPEN_TERMINAL_PATH, _("Open Command Prompt here..."))
        wx.EVT_MENU(self._treeCtrl, constants.ID_OPEN_TERMINAL_PATH, self.ProcessEvent)

        menu.Append(constants.ID_COPY_PATH, _("Copy Full Path"))
        wx.EVT_MENU(self._treeCtrl, constants.ID_COPY_PATH, self.ProcessEvent)
        return menu
        
    def GetPopupProjectMenu(self):
        menu = tkmenu.PopupMenu(self,**misc.get_style_configuration("Menu"))
        menu["postcommand"] = lambda: menu._update_menu()
        common_item_ids = [constants.ID_NEW_PROJECT,constants.ID_OPEN_PROJECT]
        if self.GetCurrentProject() is not None:
            common_item_ids.extend([constants.ID_CLOSE_PROJECT,constants.ID_SAVE_PROJECT, constants.ID_DELETE_PROJECT,\
                            constants.ID_CLEAN_PROJECT,constants.ID_ARCHIVE_PROJECT])
            common_item_ids.extend([None,constants.ID_IMPORT_FILES,constants.ID_ADD_FILES_TO_PROJECT, \
                               constants.ID_ADD_DIR_FILES_TO_PROJECT,None,constants.ID_ADD_NEW_FILE,constants.ID_ADD_FOLDER,constants.ID_ADD_PACKAGE_FOLDER])
            common_item_ids.extend([None, constants.ID_PROJECT_PROPERTIES])
       # itemIDs.append(ProjectService.RENAME_ID)
        #itemIDs.append(constants.ID_OPEN_PROJECT_PATH)
        self.GetCommonItemsMenu(menu,common_item_ids)

     #   menu.Append(constants.ID_OPEN_TERMINAL_PATH, _("Open Command Prompt here..."))
      #  wx.EVT_MENU(self._treeCtrl, constants.ID_OPEN_TERMINAL_PATH, self.ProcessEvent)

      #  menu.Append(constants.ID_COPY_PATH, _("Copy Full Path"))
       # wx.EVT_MENU(self._treeCtrl, constants.ID_COPY_PATH, self.ProcessEvent)

        return menu
        
    def GetCommonItemsMenu(self,menu,menu_item_ids):
        for item_id in menu_item_ids:
            if item_id == None:
                menu.add_separator()
                continue
            menu_item = GetApp().Menubar.FindItemById(item_id)
            if menu_item is None:
                continue
            handler = GetApp().Menubar.GetMenuhandler(_("&Project"),item_id)
            extra = {}
            #更改编辑菜单的tester命令
            if item_id in [consts.ID_UNDO,consts.ID_REDO]:
                extra.update(dict(tester=lambda:False))
            elif item_id in [consts.ID_CUT,consts.ID_COPY,consts.ID_PASTE,consts.ID_CLEAR,consts.ID_SELECTALL]:
                extra.update(dict(tester=None))
            if handler == None:
                def common_handler(id=item_id):
                    self.ProcessEvent(id)
                handler = common_handler
            menu.AppendMenuItem(menu_item,handler=handler,**extra)
            
    def ProcessEvent(self, id):
        view = self.GetView()
        if id == constants.ID_ADD_FILES_TO_PROJECT:
            self.OnAddFileToProject(event)
            return True
        elif id == constants.ID_ADD_DIR_FILES_TO_PROJECT:
            self.OnAddDirToProject(event)
            return True
        elif id == constants.ID_ADD_CURRENT_FILE_TO_PROJECT:
            return False  # Implement this one in the service
        elif id == constants.ID_ADD_NEW_FILE:
            self.OnAddNewFile(event)
            return True
        elif id == constants.ID_ADD_FOLDER:
            self.OnAddFolder(event)
            return True
        elif id == constants.ID_ADD_PACKAGE_FOLDER:
            self.OnAddPackageFolder(event)
            return True
        elif id == constants.ID_RENAME:
            view.OnRename()
            return True
        elif id == constants.ID_CLEAR:
            view.DeleteFromProject()
            return True
        elif id == constants.ID_DELETE_PROJECT:
            self.OnDeleteProject(event)
            return True
        elif id == constants.ID_CUT:
            view.OnCut()
            return True
        elif id == constants.ID_COPY:
            view.OnCopy()
            return True
        elif id == constants.ID_PASTE:
            view.OnPaste()
            return True
        elif id == constants.ID_REMOVE_FROM_PROJECT:
            view.RemoveFromProject()
            return True
        elif id == constants.ID_SELECTALL:
            self.OnSelectAll(event)
            return True
        elif id == constants.ID_OPEN_SELECTION:
            self.OnOpenSelection(event)
            return True
        elif id == Property.FilePropertiesService.PROPERTIES_ID:
            self.OnProperties(event)
            return True
        elif id == constants.ID_PROJECT_PROPERTIES:
            self.OnProjectProperties()
            return True
        elif id == constants.ID_IMPORT_FILES:
            self.ImportFilesToProject(event)
            return True
        elif id == constants.ID_OPEN_PROJECT_PATH:
            self.OpenProjectPath(event)
            return True
        elif id == constants.ID_SET_PROJECT_STARTUP_FILE:
            self.SetProjectStartupFile()
            return True
        elif id == constants.ID_START_RUN:
            self.RunFile()
            return True
        elif id == constants.ID_START_DEBUG:
            self.DebugRunFile()
            return True
        elif id == constants.ID_BREAK_INTO_DEBUGGER:
            self.BreakintoDebugger()
            return True
        elif id == constants.ID_OPEN_FOLDER_PATH:
            self.OpenFolderPath(event)
            return True
        elif id == constants.ID_OPEN_TERMINAL_PATH:
            self.OpenPromptPath(event)
            return True
        elif id == constants.ID_COPY_PATH:
            self.CopyPath(event)
            return True
        else:
            return False
            
    def StartCopyFilesToProject(self,progress_ui,file_list,src_path,dest_path):
        self.copy_thread = threading.Thread(target = self.CopyFilesToProject,args=(progress_ui,file_list,src_path,dest_path))
        self.copy_thread.start()
        
       # self.CopyFilesToProject(progress_ui,file_list,src_path,dest_path)
        
    def BuildFileList(self,file_list):
        return file_list
        
    def CopyFilesToProject(self,progress_ui,file_list,src_path,dest_path):
        #构建路径对应文件列表的对照表
        files_dict = self.BuildFileMaps(file_list)
        copy_file_count = 0
        #按照路径分别来拷贝文件
        for dir_path in files_dict:
            if self.stop_import:
                break
            #路径下所有拷贝的文件列表
            file_path_list = files_dict[dir_path]
            self.BuildFileList(file_path_list)
            #导入文件的相对路径
            folder_path = dir_path.replace(src_path,"").replace(os.sep,"/").lstrip("/").rstrip("/")
            paths = dest_path.split(os.sep)
            #目录路径如果有多层则导入文件的相对路径需添加多层目录
            if len(paths) > 1:
                #第一层目录为项目目录必须剔除
                dest_folder_path =  "/".join(paths[1:]) 
                if folder_path != "":
                    dest_folder_path +=  "/" + folder_path
            else:
                dest_folder_path = folder_path
            self.GetView().GetDocument().GetCommandProcessor().Submit(ProjectAddProgressFilesCommand(progress_ui,\
                self.GetView().GetDocument(), file_path_list, folderPath=dest_folder_path,range_value = copy_file_count))
            copy_file_count += len(file_path_list)

    def BuildFileMaps(self,file_list):
        d = {}
        for file_path in file_list:
            dir_path = os.path.dirname(file_path)
            if not d.has_key(dir_path):
                d[dir_path] = [file_path]
            else:
                d[dir_path].append(file_path)
        return d
        
    def StopImport(self):
        self.stop_import = True
        
    def SaveProjectConfig(self):
        self.GetView().WriteProjectConfig()

