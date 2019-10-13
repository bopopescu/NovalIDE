# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        baseviewer.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-02-15
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp,_
import noval.core as core
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import copy
import os
import os.path
import sys
import time
import types
import noval.util.appdirs as appdirs
import noval.util.strutils as strutils
import noval.util.fileutils as fileutils
import noval.util.apputils as sysutilslib
import shutil
import noval.python.parser.utils as parserutils
import uuid
import noval.filewatcher as filewatcher
import pickle
import noval.project.newfile as newfile
import datetime
from noval.util import utils
import noval.constants as constants
import noval.consts as consts
import noval.project.wizard as projectwizard
import noval.imageutils as imageutils
import noval.project.baseconfig as baseconfig
import noval.project.command as projectcommand
from noval.project.templatemanager import ProjectTemplateManager
import noval.newTkDnD as newTkDnD
import noval.misc as misc
import noval.ui_base as ui_base
import noval.ui_utils as ui_utils
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.project.importfiles as importfiles
try:
    import tkSimpleDialog
except ImportError:
    import tkinter.simpledialog as tkSimpleDialog
import noval.ui_common as ui_common
import six
    
#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------


PROJECT_DIRECTORY_KEY = "NewProjectDirectory"

NEW_PROJECT_DIRECTORY_DEFAULT = appdirs.getSystemDir()


def getProjectKeyName(project_document):
    return project_document.GetKey("OpenFolders")

#----------------------------------------------------------------------------
# Classes
#----------------------------------------------------------------------------

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



class ProjectNameLocationPage(projectwizard.BitmapTitledContainerWizardPage):
    def __init__(self,master,**kwargs):
        projectwizard.BitmapTitledContainerWizardPage.__init__(self,master,_("Enter the name and location for the project"),_("Name and Location"),"python_logo.png",**kwargs)
        self.can_finish = kwargs.get('can_finish',True)
        self.allowOverwriteOnPrompt = False
            
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=0, sticky="nsew")
        info_label = ttk.Label(sizer_frame, text=_("Enter the name and location for the project."))
        info_label.pack(side=tk.LEFT,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y, consts.DEFAUT_CONTRL_PAD_Y))
        self.CreateNamePage(content_frame)
        if kwargs.get('project_dir_option',False):
            self.CreateProjectDirPage(content_frame,**kwargs)
            
    def GetChoiceDirs(self,choiceDirs):
        choiceDirs.append(self.dir_entry_var.get())
        curProjectDoc = GetApp().MainFrame.GetProjectView().GetCurrentProject()
        projectDirs = []
        #先添加当前项目文档的路径到可选路径列表中
        if curProjectDoc:
            homeDir = os.path.dirname(curProjectDoc.GetAppDocMgr().homeDir)
            if homeDir and (homeDir not in choiceDirs):
                choiceDirs.append(homeDir)
            #if not startingDirectory:
             #   startingDirectory = homeDir
        #再添加其它项目文档的路径到可选路径列表中
        for projectDoc in GetApp().MainFrame.GetProjectView().GetOpenProjects():
            if projectDoc == curProjectDoc:
                continue
            homeDir = os.path.dirname(projectDoc.GetAppDocMgr().homeDir
)
            if homeDir and (homeDir not in projectDirs):
                projectDirs.append(homeDir)
        for projectDir in projectDirs:
            if projectDir not in choiceDirs:
                choiceDirs.append(projectDir)
                
        #添加当前路径到可选路径列表中
        cwdir = None
        try:
            cwdir = os.getcwd()
        except:
            pass
        if cwdir and cwdir not in choiceDirs:
            choiceDirs.append(cwdir)   
        #最后添加系统默认路径到可选路径列表中             
        if appdirs.getSystemDir() not in choiceDirs:
            choiceDirs.append(appdirs.getSystemDir()) 
            
    def CreateNamePage(self,content_frame):
        
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        self.name_label = ttk.Label(sizer_frame, text=_("Name:"))
        self.name_label.grid(column=0, row=0, sticky="nsew")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(sizer_frame, textvariable=self.name_var)
        self.name_entry.grid(column=1, row=0, sticky="nsew",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0))
        sizer_frame.columnconfigure(1, weight=1)
        
        self.dir_label = ttk.Label(sizer_frame, text=_("Location:"))
        self.dir_label.grid(column=0, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        choiceDirs = []
        self.dir_entry_var = tk.StringVar(value=utils.profile_get(PROJECT_DIRECTORY_KEY, NEW_PROJECT_DIRECTORY_DEFAULT))
        self.GetChoiceDirs(choiceDirs)
        self.dir_entry = ttk.Combobox(sizer_frame, textvariable=self.dir_entry_var,values=choiceDirs)
        self.dir_entry.grid(column=1, row=1, sticky="nsew",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.browser_button = ttk.Button(
            sizer_frame, text=_("Browse..."), command=self.BrowsePath
        )
        self.browser_button.grid(column=2, row=1, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        return sizer_frame
        
    def CreateProjectDirPage(self,content_frame,chk_box_row=2,**kwargs):
        
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=chk_box_row, sticky="nsew")
        #默认创建项目目录
        self.project_dir_chkvar = tk.IntVar(value=kwargs.get('project_dir_checked',True))
        self.create_project_dir_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Create Project Directory"), variable=self.project_dir_chkvar
        )
        self.create_project_dir_checkbutton.pack(side=tk.LEFT,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))

        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=chk_box_row+1, sticky="nsew")

        self.infotext_label_var = tk.StringVar()
        self.infotext_label_var.set("")
        self.infotext_label = ttk.Label(
            sizer_frame, textvariable=self.infotext_label_var, foreground="red"
        )
        self.infotext_label.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        
    def BrowsePath(self):
        path = filedialog.askdirectory()
        if path:
            #必须转换一下路径为系统标准路径格式
            path = fileutils.opj(path)
            self.dir_entry_var.set(path)
        
    def Validate(self):
        self.infotext_label_var.set("")
        projName = self.name_var.get().strip()
        if projName == "":
            self.infotext_label_var.set(_("Please provide a file name."))
            return False
        #项目名称不能包含空格
        if projName.find(' ') != -1:
            self.infotext_label_var.set(_("Please provide a file name that does not contains spaces."))        
            return False

        if projName[0].isdigit():
            self.infotext_label_var.set(_("File name cannot start with a number.  Please enter a different name."))            
            return False
        if projName.endswith(consts.PROJECT_EXTENSION):
            projName2 = projName[:-4]
        else:
            projName2 = projName
        #项目名称必须是字母或数字,下划线字符串允许合法
        if not projName2.replace("_", "a").isalnum():  # [a-zA-Z0-9_]  note '_' is allowed and ending '.agp'.
            self.infotext_label_var.set(_("Name must be alphanumeric ('_' allowed).  Please enter a valid name."))
            return False

        dirName = self.dir_entry_var.get().strip()
        if dirName == "":
            self.infotext_label_var.set(_("No directory.  Please provide a directory."))            
            return False
        if os.sep == "\\" and dirName.find("/") != -1:
            self.infotext_label_var.set(_("Wrong delimiter '/' found in directory path.  Use '%s' as delimiter.") % os.sep)            
            return False
        
        return True
        
    def GetProjectLocation(self):
        projName = self.name_var.get().strip()
        dirName = self.dir_entry_var.get()
        #是否创建项目名称目录,如果是则目录包含项目名称
        if self.project_dir_chkvar.get():
            dirName = os.path.join(dirName,projName)
        return dirName
        
    def Finish(self):
        dirName = self.GetProjectLocation()
        #if dir not exist,create it first
        if not os.path.exists(dirName):
            try:
                parserutils.MakeDirs(dirName)
            except Exception as e:
                self.infotext_label_var.set("%s"%str(e))
                #如果不是最后的页面,错误的信息需要弹出来,来醒目地提示用户错误,否则用户看不到错误信息
                if self.GetNext():
                    messagebox.showerror(_('Error'),str(e),parent=self)
                return False
            
        projName = self.name_var.get().strip()
        fullProjectPath = os.path.join(dirName, strutils.MakeNameEndInExtension(projName, consts.PROJECT_EXTENSION))
        if os.path.exists(fullProjectPath):
            if self.allowOverwriteOnPrompt:
                res = wx.MessageBox(_("That %sfile already exists. Would you like to overwrite it.") % infoString, "File Exists", style=wx.YES_NO|wx.NO_DEFAULT)
                if res != wx.YES:
                    return False
            else:                
                self.infotext_label_var.set(_("That file already exists. Please choose a different name."))
                #如果不是最后的页面,错误的信息需要弹出来,来醒目地提示用户错误,否则用户看不到错误信息
                if self.GetNext():
                    messagebox.showerror(_('File Exists'),_("That file already exists. Please choose a different name."),parent=self)
                return False
                
            # What if the document is already open and we're overwriting it?
            documents = docManager.GetDocuments()
            for document in documents:
                if os.path.normcase(document.GetFilename()) == os.path.normcase(self._fullProjectPath):  # If the renamed document is open, update it
                    document.DeleteAllViews()
                    break
            os.remove(self._fullProjectPath)
   
        self._new_project_configuration = self.GetNewPojectConfiguration()
        utils.profile_set(PROJECT_DIRECTORY_KEY, self._new_project_configuration.Location)
        template = self.GetProjectTemplate()
        doc = template.CreateDocument(fullProjectPath, flags = core.DOC_NEW)
        #set project name
        doc.GetModel().Name = self._new_project_configuration.Name
        doc.GetModel().Id = str(uuid.uuid1()).upper()
        doc.GetModel().SetInterpreter(self._new_project_configuration.Interpreter)
        if not doc.OnSaveDocument(fullProjectPath):
            return False
        #强制显示项目视图
        view = GetApp().MainFrame.GetProjectView(show=True).GetView()
        view.AddProjectToView(doc)
        return True

    def GetProjectTemplate(self):
        return GetApp().GetDocumentManager().FindTemplateForTestPath(consts.PROJECT_EXTENSION)

    def GetNewPojectConfiguration(self):
        return baseconfig.NewProjectConfiguration(self.name_var.get(),self.dir_entry_var.get(),self.project_dir_chkvar.get())
        
class NewProjectWizard(projectwizard.BaseWizard):
    def __init__(self, parent):
        self._parent = parent
        projectwizard.BaseWizard.__init__(self, parent)
        self._project_template_page = self.CreateProjectTemplatePage(self)
        self.template_pages = {
        }
        self.project_template_icon = GetApp().GetImage("packagefolder_obj.gif")
        self.project_templates = ProjectTemplateManager().ProjectTemplates
        self.LoadProjectTemplates()
        
    def CreateProjectTemplatePage(self,wizard):
        page = projectwizard.BitmapTitledWizardPage(wizard, _("New Project Wizard"),_("Welcom to new project wizard"),"python_logo.png")    
        # init and place tree
        sizer_frame = ttk.Frame(page)
        sizer_frame.grid(column=0, row=1, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X)
        #设置path列存储模板路径,并隐藏改列 
        treeview = treeviewframe.TreeViewFrame(sizer_frame,show_scrollbar=False,borderwidth=1,relief="solid")
        self.tree = treeview.tree
        treeview.pack(side=tk.LEFT,fill="both",expand=1)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        # init tree events
        self.tree.bind("<<TreeviewSelect>>", self._on_select, True)
        #鼠标双击Tree控件事件
        self.tree.bind("<Double-Button-1>", self.on_double_click, "+")

        # configure the only tree column
        self.tree.column("#0", anchor=tk.W, stretch=True)
        self.tree["show"] = ("tree",)

        wizard.FitToPage(page)
        return page

    def LoadDefaultProjectTemplates(self):
        ProjectTemplateManager().AddProjectTemplate("General","Empty Project",[ProjectNameLocationPage,])
        ProjectTemplateManager().AddProjectTemplate("General","New Project From Existing Code",["noval.project.baseviewer.ProjectNameLocationPage",])

    def LoadProjectTemplates(self):
        self.LoadDefaultProjectTemplates()
        for project_template in self.project_templates:
            template_catlog = list(project_template.keys())[0]
            catlogs = template_catlog.split('/')
            path = ''
            for i,catlog_name in enumerate(catlogs):
                if i == 0:
                    path += catlog_name
                else:
                    path += "/" + catlog_name
                
                #found表示是否已经存在改路径的节点,node_id,表示从该节点下面插入
                found,node_id = self.GetProjectTemplateNode(path)
                if not found:
                    node_id = self.tree.insert(node_id, "end", text=_(catlog_name),image=self.project_template_icon,values=path)
                    self.tree.selection_set(node_id)
            for template_name,pages in project_template[template_catlog]:
                template_path = template_catlog + "/" + template_name
                template_node_id = self.tree.insert(node_id, "end", text=_(template_name),values=(template_path,))
                page_instances = self.InitPageInstances(pages)
                self.SetPagesChain(page_instances)
                self.template_pages[template_path] = page_instances
                
    def InitPageInstances(self,pages):
        page_instances = []
        for page_info in pages:
            args = {}
            #如果页面初始化需要参数,则使用列表或元祖的方式指定页面和参数信息
            if isinstance(page_info,list) or isinstance(page_info,tuple):
                #列表的第一个元素为页面名称或类名
                page_class_obj = page_info[0]
                #列表第二个元素为页面启动的参数,为字典类型
                args = page_info[1]
            else:
                page_class_obj = page_info

            try:
                #如果类对象是字符串,则从字符串中动态获取类对象
                if isinstance(page_class_obj,str):
                    page_class_obj = utils.GetClassFromDynamicImportModule(page_class_obj)
                page = page_class_obj(self,**args)
                page_instances.append(page)
            except Exception as e:
                utils.get_logger().error("init page instance error %s",e)
                utils.get_logger().exception('')
        return page_instances

    def SetPagesChain(self,pages):
        '''
            设置各页面的链接关系
        '''
        if len(pages) == 0:
            return
        for i,page in enumerate(pages):
            if i >= len(pages) - 1:
                continue
            pages[i+1].SetPrev(pages[i])
            pages[i].SetNext(pages[i+1])

    def GetProjectTemplatePathNode(self, folderPath,item=None):
        for child in self.tree.get_children(item):
            #获取存储的路径值
            path = self.tree.item(child, "values")[0]
            if folderPath == path:
                return child
            else:
                node_id = self.GetProjectTemplatePathNode(folderPath,child)
                if node_id:
                    return node_id
        return ''

    def GetProjectTemplateNode(self, path):
        found = self.GetProjectTemplatePathNode(path)
        sub_path = '/'.join(path.split('/')[0:-1])
        parent_node = self.GetProjectTemplatePathNode(sub_path)
        return found,parent_node
        
    def _on_select(self,event):
        
        def update_ui(enable=False):
            if enable:
                self.next_button['state'] = tk.NORMAL
            else:
                self.next_button['state'] = tk.DISABLED
            self.prev_button['state'] = tk.DISABLED
            self.SetFinish(False)
        nodes = self.tree.selection()
        if len(nodes) == 0:
            update_ui(False)
            return
        node = nodes[0]
        path = self.tree.item(node)["values"][0]
        childs = self.tree.get_children(node)
        if len(childs) > 0:
            update_ui(False)
        else:
            pages = self.template_pages[path]
            if not pages:
                update_ui(False)
                return
            #单独设置起始页的下一个页面为第一个页面
            pages[0].SetPrev(self._project_template_page)
            self._project_template_page.SetNext(pages[0])
            update_ui(True)
            
    def on_double_click(self,event):
        nodes = self.tree.selection()
        node = nodes[0]
        childs = self.tree.get_children(node)
        if len(childs) == 0:
            self.GotoNextPage()
        
class ProjectTemplate(core.DocTemplate):

    def CreateDocument(self, path, flags,wizard_cls=NewProjectWizard):
        if path:
            doc = core.DocTemplate.CreateDocument(self, path, flags)
            if path:
                doc.GetModel()._projectDir = os.path.dirname(path)
            return doc
        else:
            wiz = wizard_cls(GetApp().GetTopWindow())
            wiz.RunWizard(wiz._project_template_page)
            return None  # never return the doc, otherwise docview will think it is a new file and rename it


class ProjectView(misc.AlarmEventView):
    COPY_FILE_TYPE = 1
    CUT_FILE_TYPE = 2
    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self, frame):
        misc.AlarmEventView.__init__(self)
        self._prject_browser = frame  # not used, but kept to match other Services
        self._treeCtrl = self._prject_browser.tree
        self._loading = False  # flag to not to try to saving state of folders while it is loading
        self._documents = []
        self._document = None
        self._bold_item = None

    def GetDocumentManager(self):  # Overshadow this since the superclass uses the view._viewDocument attribute directly, which the project editor doesn't use since it hosts multiple docs
        return GetApp().GetDocumentManager()
        
    @property
    def IsImportStop(self):
        return self._prject_browser.stop_import

    @property
    def Documents(self):
        return self._documents
        
    def GetDocument(self):
        return self._document

    def GetFrame(self):
        return self._prject_browser

    def SetDocument(self,document):
        self._document = document
        
    def Activate(self, activate = True):
        if self.IsShown():
            core.View.Activate(self, activate = activate)
            if activate and self._treeCtrl:
                self._treeCtrl.focus_set()
        self.Show()

    def OnCreate(self, doc, flags):
        return True

    def OnChangeFilename(self):
        pass

    def ProjectSelect(self):
        selItem = self._prject_browser.project_combox.current()
        if selItem == -1:
            self._prject_browser.project_combox.set("")
            return
        document = self._documents[selItem]
        self.SetDocument(document)
        self.LoadProject(self.GetDocument())
        if self.GetDocument():
            filename = self.GetDocument().GetFilename()
        else:
            filename = ''
       # self._projectChoice.SetToolTipString(filename)

    def WriteProjectConfig(self):
        config = GetApp().GetConfig()
        if config.ReadInt(consts.PROJECT_DOCS_SAVED_KEY, True):
            projectFileNames = []
            curProject = None
            for i in range(len(self._prject_browser.project_combox['values'])):
                project_document = self._documents[i]
                if not project_document.OnSaveModified():
                    return
                if project_document.GetDocumentSaved():  # Might be a new document and "No" selected to save it
                    projectFileNames.append(str(project_document.GetFilename()))
            config.Write(consts.PROJECT_SAVE_DOCS_KEY, projectFileNames.__repr__())

            document = None
            if self._prject_browser.project_combox['values']:
                i = self._prject_browser.project_combox.current()
                if i != -1:
                    document = self._documents[i]
            if document:
                config.Write(consts.CURRENT_PROJECT_KEY, document.GetFilename())
            else:
                config.DeleteEntry(consts.CURRENT_PROJECT_KEY)

    def OnClose(self, deleteWindow = True):
        self.WriteProjectConfig()
            
        project = self.GetDocument()
        if not project:
            return True
        if not project.Close():
            return True

        if not deleteWindow:
            self.RemoveCurrentDocumentUpdate()
        else:
            # need this to accelerate closing down app if treeCtrl has lots of items
            rootItem = self._treeCtrl.GetRootItem()
            self._treeCtrl.DeleteChildren(rootItem)
        

        # We don't need to delete the window since it is a floater/embedded
        return True
        
    def AddProgressFiles(self,newFilePaths,range_value,projectDoc,progress_ui,que):
        project = projectDoc.GetModel()
        projectDir = project.homeDir
        rootItem = self._treeCtrl.GetRootItem()
        # add new folders and new items
        addList = []                    
        for filePath in newFilePaths:
            file = project.FindFile(filePath)
            if file:
                folderPath = file.logicalFolder
                if folderPath:
                    if os.path.basename(filePath).lower() == self.PACKAGE_INIT_FILE:
                        self._treeCtrl.AddPackageFolder(folderPath)
                    else:
                        self._treeCtrl.AddFolder(folderPath)
                    folder = self._treeCtrl.FindFolder(folderPath)
                else:
                    folder = rootItem
                if folderPath is None:
                    folderPath = ""
                dest_path = os.path.join(projectDir,folderPath,os.path.basename(filePath))
                #如果源文件和目的文件地址一样,则不用覆盖
                if not parserutils.ComparePath(filePath,dest_path):
                    #判断目的文件是否存在
                    if os.path.exists(dest_path):
                        #如果文件已经存在于项目中,需要先移除
                        if project.FindFile(dest_path):
                            project.RemoveFile(file)
                        #选择yes和no将显示覆盖确认对话框
                        if importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_YES or importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_NO:
                            prompt_dlg = ui_common.PromptmessageBox(self.GetFrame(),_("Project File Exists"),\
                                    _("The file %s is already exist in project ,Do You Want to overwrite it?") % filePath)
                            prompt_dlg.ShowModal()
                            importfiles.DEFAULT_PROMPT_MESSAGE_ID = prompt_dlg.status
                            #选择No时不要覆盖文件
                            if importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_NO:
                                range_value += 1
                                continue
                    dest_dir_path = os.path.dirname(dest_path)
                    if not os.path.exists(dest_dir_path):
                        parserutils.MakeDirs(dest_dir_path)
                        
                    #选择yestoall和notoall将不再显示覆盖确认对话框
                    if importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_YESTOALL or \
                                importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_YES:
                        try:
                            shutil.copyfile(filePath,dest_path)
                        except Exception as e:
                            messagebox.showerror(GetApp().GetAppName(),str(e))
                            return
                    #路径有可能不符合规范,规范路径格式
                    file.filePath = fileutils.opj(dest_path)
                if not self._treeCtrl.FindItem(file.filePath,folder):
                    item = self._treeCtrl.AppendItem(folder, os.path.basename(file.filePath), file)
                    addList.append(item)
                self._treeCtrl.item(folder, open=True)
            range_value += 1
            que.put((range_value,filePath))
            assert(type(range_value) == int and range_value > 0)
            if progress_ui.is_cancel:
                utils.get_logger().info("user stop import code files")
                break
        # sort folders with new items
        parentList = []
        for item in addList:
            parentItem = self._treeCtrl.parent(item)
            if parentItem not in parentList:
                parentList.append(parentItem)
        for parentItem in parentList:
            self._treeCtrl.SortChildren(parentItem)
            self._treeCtrl.item(parentItem, open=True)

    def OnUpdate(self, sender = None, hint = None):
        if core.View.OnUpdate(self, sender, hint):
            return
        
        if hint:
            if hint[0] == consts.PROJECT_ADD_COMMAND_NAME:
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                newFilePaths = hint[2]  # need to be added and selected, and sorted
                oldFilePaths = hint[3]  # need to be selected
                
                project = projectDoc.GetModel()
                projectDir = project.homeDir
                rootItem = self._treeCtrl.GetRootItem()
                    
                # add new folders and new items
                addList = []                    
                for filePath in newFilePaths:
                    file = project.FindFile(filePath)
                    if file:
                        folderPath = file.logicalFolder
                        if folderPath:
                            if os.path.basename(filePath).lower() == self.PACKAGE_INIT_FILE:
                                self._treeCtrl.AddPackageFolder(folderPath)
                            else:
                                self._treeCtrl.AddFolder(folderPath)
                            folder = self._treeCtrl.FindFolder(folderPath)
                        else:
                            folder = rootItem
                        if folderPath is None:
                            folderPath = ""
                        dest_path = os.path.join(projectDir,folderPath,os.path.basename(filePath))
                        if not parserutils.ComparePath(filePath,dest_path):
                            if os.path.exists(dest_path):
                                #the dest file is already in the project
                                if project.FindFile(dest_path):
                                    project.RemoveFile(file)
                                if importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_YES or \
                                            importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_NO:
                                    prompt_dlg = ui_common.PromptmessageBox(GetApp().GetTopWindow(),_("Project File Exists"),\
                                            _("The file %s is already exist in project ,Do You Want to overwrite it?") % filePath)
                                    status = prompt_dlg.ShowModal()
                                    importfiles.DEFAULT_PROMPT_MESSAGE_ID = status
                            if importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_YESTOALL or\
                                importfiles.DEFAULT_PROMPT_MESSAGE_ID == constants.ID_YES:
                                try:
                                    shutil.copyfile(filePath,dest_path)
                                except Exception as e:
                                    messagebox.showerror(GetApp().GetAppName(),str(e))
                                    return
                            file.filePath = dest_path
                        if not self._treeCtrl.FindItem(file.filePath,folder):
                            #如果是虚拟文件,则返回为None
                            item = self._treeCtrl.AppendItem(folder, os.path.basename(file.filePath), file)
                            if item is not None:
                                addList.append(item)
                        self._treeCtrl.item(folder, open=True)
                # sort folders with new items
                parentList = []
                for item in addList:
                    parentItem = self._treeCtrl.parent(item)
                    if parentItem not in parentList:
                        parentList.append(parentItem)
                for parentItem in parentList:
                    self._treeCtrl.SortChildren(parentItem)

                # select all the items user wanted to add
                lastItem = None
                for filePath in (oldFilePaths + newFilePaths):
                    item = self._treeCtrl.FindItem(filePath)
                    if item:
                        self._treeCtrl.SelectItem(item)
                        lastItem = item
                        
                if lastItem:        
                    self._treeCtrl.see(lastItem)
                return
                
            elif hint[0] == consts.PROJECT_ADD_PROGRESS_COMMAND_NAME:
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                newFilePaths = hint[2]  # need to be added and selected, and sorted
                range_value = hint[3]  # need to be selected
                progress_ui = hint[4]
                que = hint[5]
                self.AddProgressFiles(newFilePaths,range_value,projectDoc,progress_ui,que)
                return

            elif hint[0] == "remove":
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
             
                filePaths = hint[2]
                for filePath in filePaths:
                    item = self._treeCtrl.FindItem(filePath)
                    if item:
                        self._treeCtrl.delete(item)
                return
                
            elif hint[0] == "rename":
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                    
                self._treeCtrl.Freeze()
                try:
                    item = self._treeCtrl.FindItem(hint[2])
                    self._treeCtrl.SetItemText(item, os.path.basename(hint[3]))
                    self._treeCtrl.EnsureVisible(item)
                finally:
                    self._treeCtrl.Thaw()
                return
                
            elif hint[0] == "rename folder":
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                    
                self._treeCtrl.Freeze()
                try:
                    item = self._treeCtrl.FindFolder(hint[2])
                    if item:
                        self._treeCtrl.UnselectAll()
                        self._treeCtrl.SetItemText(item, os.path.basename(hint[3]))
                        self._treeCtrl.SortChildren(self._treeCtrl.GetItemParent(item))
                        self._treeCtrl.SelectItem(item)
                        self._treeCtrl.EnsureVisible(item)
                finally:
                    self._treeCtrl.Thaw()
                return
     

    def RemoveProjectUpdate(self, projectDoc):
        """ Called by service after deleting a project, need to remove from project choices """
        i = self._projectChoice.FindString(self._MakeProjectName(projectDoc))
        self._projectChoice.Delete(i)

        numProj = self._projectChoice.GetCount()
        if i >= numProj:
            i = numProj - 1
        if i >= 0:
            self._projectChoice.SetSelection(i)
        self._documents.remove(self._document)
        wx.GetApp().GetDocumentManager().CloseDocument(projectDoc, False)
        self._document = None
        self.OnProjectSelect()
        
    def ReloadDocuments(self):
        names = []
        for document in self._documents:
            names.append(self._MakeProjectName(document))
        self._prject_browser.project_combox['values'] = names


    def RemoveCurrentDocumentUpdate(self, i=-1):
        """ Called by service after deleting a project, need to remove from project choices """
        i = self._prject_browser.project_combox.current()
        self._documents.remove(self._document)
        self.ReloadDocuments()
        numProj = len(self._documents)
        if i >= numProj:
            i = numProj - 1
        if i >= 0:
            self._prject_browser.project_combox.current(i)
        self._document = None
        self.ProjectSelect()
 
    def CloseProject(self):
        projectDoc = self.GetDocument()
        if projectDoc:
            openDocs = self.GetDocumentManager().GetDocuments()
            #先关闭所有项目打开文档
            for openDoc in openDocs[:]:  # need to make a copy, as each file closes we're off by one
                if projectDoc == openDoc:  # close project last
                    continue
                    
                if projectDoc == self._prject_browser.FindProjectFromMapping(openDoc):
                    if not self.GetDocumentManager().CloseDocument(openDoc, False):
                        return
                    
                    self._prject_browser.RemoveProjectMapping(openDoc)
                    if hasattr(openDoc, "GetModel"):
                        self._prject_browser.RemoveProjectMapping(openDoc.GetModel())
            #delete project regkey config
           ## wx.ConfigBase_Get().DeleteGroup(getProjectKeyName(projectDoc.GetModel().Id))
            if self.GetDocumentManager().CloseDocument(projectDoc, False):
                projectDoc.document_watcher.RemoveFileDoc(projectDoc)
                self.RemoveCurrentDocumentUpdate()
            if not self.GetDocument():
                self.AddProjectRoot(_("Projects"))
            
    def OnResourceViewToolClicked(self, event):
        id = event.GetId()
        if id == ResourceView.REFRESH_PATH_ID or id == ResourceView.ADD_FOLDER_ID:
            return self.dir_ctrl.ProcessEvent(event)
            
    def SetProjectStartupFile(self):
        item = self._treeCtrl.GetSingleSelectItem()
        self.SetProjectStartupFileItem(item)
        
    def SetProjectStartupFileItem(self,item):
        if item == self._bold_item:
            return
        if self._bold_item is not None:
            self._treeCtrl.SetItemBold(self._bold_item ,False)
        filePath = self._GetItemFile(item)
        pjfile = self.GetDocument().GetModel().FindFile(filePath)
        self._treeCtrl.SetItemBold(item)
        self._bold_item = item
        self.GetDocument().GetModel().StartupFile = pjfile
        self.GetDocument().Modify(True)

    def OpenProject(self,project_path):
        docs = GetApp().GetDocumentManager().CreateDocument(project_path, core.DOC_SILENT|core.DOC_OPEN_ONCE)
        if not docs:  # project already open
            self.SetProject(project_path)
        elif docs:
            if docs[0] not in self.GetDocumentManager().GetDocuments():
                utils.get_logger().error('open project %s error',project_path)
                return
            AddProjectMapping(docs[0])
                
    def SaveProject(self):
        doc = self.GetDocument()
        if doc.IsModified():
            GetApp().configure(cursor="circle")
            GetApp().GetTopWindow().PushStatusText(_("Project is saving..."))
            if doc.OnSaveDocument(doc.GetFilename()):
                GetApp().GetTopWindow().PushStatusText(_("Project save success."))
            else:
                GetApp().GetTopWindow().PushStatusText(_("Project save failed."))
            GetApp().configure(cursor="")
            
    def CleanProject(self):
        project_doc = self.GetDocument()
        path = os.path.dirname(project_doc.GetFilename())
        #
        GetApp().configure(cursor="circle")
        for root,path,files in os.walk(path):
            for filename in files:
                fullpath = os.path.join(root,filename)
                ext = strutils.get_file_extension(fullpath)
                #清理项目的二进制文件
                if ext in project_doc.BIN_FILE_EXTS:
                    GetApp().GetTopWindow().PushStatusText(_("Cleaning \"%s\".") % fullpath)
                    fileutils.safe_remove(fullpath)
        GetApp().GetTopWindow().PushStatusText(_("Clean Completed."))
        GetApp().configure(cursor="")
        
    def ArchiveProject(self):
        GetApp().configure(cursor="circle")
        doc = self.GetDocument()
        path = os.path.dirname(doc.GetFilename())
        try:
            GetApp().GetTopWindow().PushStatusText(_("Archiving..."))
            datetime_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
            zip_name = doc.GetModel().Name + "_" + datetime_str + ".zip"
            zip_path = doc.ArchiveProject(os.path.join(path,zip_name))
            messagebox.showinfo(_("Archive Success"),_("Success archived to %s") % zip_path)
            GetApp().GetTopWindow().PushStatusText(_("Success archived to %s") % zip_path)
        except Exception as e:
            utils.get_logger().exception("")
            messagebox.showerror(_("Archive Error"),str(e))
            GetApp().GetTopWindow().PushStatusText(_("Archive Error"))
        GetApp().configure(cursor="")

    def ImportFilesToProject(self):
        items = self._treeCtrl.selection()
        if items:
            item = items[0]
        else:
            item = self._treeCtrl.GetRootItem()
        folderPath = self._GetItemFolderPath(item)
        frame = importfiles.ImportfilesDialog(GetApp().GetTopWindow(),folderPath)
        if frame.ShowModal() == constants.ID_OK:
            if not self._treeCtrl.IsExpanded(item):
                self._treeCtrl.Expand(item)

    #----------------------------------------------------------------------------
    # Display Methods
    #----------------------------------------------------------------------------

    def IsShown(self):
        return GetApp().MainFrame.IsViewShown(consts.PROJECT_VIEW_NAME)


    def Hide(self):
        self.Show(False)


    def Show(self, show = True):
        pass
        #GetApp().MainFrame.ShowView(consts.PROJECT_VIEW_NAME)
       # if wx.GetApp().IsMDI():
        #    mdiParentFrame = wx.GetApp().GetTopWindow()
        #    mdiParentFrame.ShowEmbeddedWindow(self.GetFrame(), show)


    #----------------------------------------------------------------------------
    # Methods for ProjectDocument and ProjectService to call
    #----------------------------------------------------------------------------

    def SetProject(self, projectPath):
        if self._prject_browser.IsLoading:
            utils.get_logger().info("app is loading projects at startup ,do not load project document %s at this time",projectPath)
            return
            
        #打开项目文件时强制显示项目视图窗口,不生成事件
        GetApp().MainFrame.GetProjectView(show=True,generate_event=False)
        curSel = self._prject_browser.project_combox.current()
        for i in range(len(self._prject_browser.project_combox['values'])):
            document = self._documents[i]
            if document.GetFilename() == projectPath:
                if curSel != i:  # don't reload if already loaded
                    utils.get_logger().info("switch to and load project document %s",projectPath)
                    self._prject_browser.project_combox.current(i)
                    self.SetDocument(document)
                    self.LoadProject(document)
                    #self._projectChoice.SetToolTipString(document.GetFilename())
                break

    def GetSelectedFile(self):
        for item in self._treeCtrl.selection():
            filePath = self._GetItemFilePath(item)
            if filePath:
                return filePath
        return None


    def GetSelectedFiles(self):
        filePaths = []
        for item in self._treeCtrl.GetSelections():
            filePath = self._GetItemFilePath(item)
            if filePath and filePath not in filePaths:
                filePaths.append(filePath)
        return filePaths


    def GetSelectedPhysicalFolder(self):
        if self.GetMode() == ProjectView.PROJECT_VIEW:
            return None
        else:
            for item in self._treeCtrl.GetSelections():
                if not self._IsItemFile(item):
                    filePath = self._GetItemFolderPath(item)
                    if filePath:
                        return filePath
            return None


    def GetSelectedProject(self):
        document = self.GetDocument()
        if document:
            return document.GetFilename()
        else:
            return None
            
    def GetProjectSelection(self,document):
        for i in range(len(self._prject_browser.project_combox['values'])):
            project = self._documents[i]
            if document == project:
                return i
        return -1

    def AddProjectToView(self, document):
        #check the project is already exist or not
        index = self.GetProjectSelection(document)
        #if proejct not exist,add the new document
        if index == -1:
            index = self._prject_browser.AddProject(self._MakeProjectName(document))
            self._documents.append(document)
        self._prject_browser.project_combox.current(index)
        self.ProjectSelect()
        
    def LoadDocuments(self):
        self._projectChoice.Clear()
        for document in self._documents:
            i = self._projectChoice.Append(self._MakeProjectName(document),getProjectBitmap(), document)
            if document == self.GetDocument():
                self._projectChoice.SetSelection(i)
                
    def AddProjectRoot(self,document_or_name):
        self._prject_browser.clear()
        #这里针对python2和python3中各自的string类型进行了区分:在python2中,使用的为basestring;在python3中,使用的为str
        if isinstance(document_or_name,six.string_types[0]):
            name = document_or_name
            text = name
        else:
            document = document_or_name
            text = document.GetModel().Name
        root_item = self._treeCtrl.insert("", "end", text=text,image=self._treeCtrl.GetProjectIcon())
        return root_item
        
    def AddFolderItem(self,document,folderPath):
        return self._treeCtrl.AddFolder(folderPath)

    def LoadProject(self, document):
        GetApp().configure(cursor="circle")
        try:
            #切换项目时加粗的节点重置为空,如果项目设置有启动文件,则将该启动文件节点加粗
            self._bold_item = None
            rootItem = self.AddProjectRoot(document)
            if document:
                docFilePath = document.GetFilename()
                folders = document.GetModel().logicalFolders
                folders.sort()
                folderItems = []
                for folderPath in folders:
                    folderItems = folderItems + self.AddFolderItem(document,folderPath)
                                            
                for file in document.GetModel()._files:
                    folder = file.logicalFolder
                    if folder:
                        folderTree = folder.split('/')
                        item = rootItem
                        for folderName in folderTree:
                            found = False
                            for child in self._treeCtrl.get_children(item):
                                if self._treeCtrl.item(child, "text") == folderName:
                                    item = child 
                                    found = True
                                    break
                                
                            if not found:
                                #print "error folder '%s' not found for %s" % (folder, file.filePath)
                                break
                    else:
                        item = rootItem
                        
                    fileItem = self._treeCtrl.AppendItem(item, os.path.basename(file.filePath), file)
                    startupFile = document.GetModel().RunInfo.StartupFile
                    #设置项目启动
                    if startupFile and document.GetModel().fullPath(startupFile) == file.filePath:
                        self._bold_item = fileItem
                        self._treeCtrl.SetItemBold(fileItem)
                        document.GetModel().StartupFile = file
                    
                self._treeCtrl.SortChildren(rootItem)
                for item in folderItems:
                    self._treeCtrl.SortChildren(item)
                    
                if utils.profile_get_int("LoadFolderState", True):
                    self.LoadFolderState()
    
                self._treeCtrl.focus_set()
                child = self._treeCtrl.GetFirstChild(self._treeCtrl.GetRootItem())
                if child:
                    self._treeCtrl.see(child)
        finally:
            GetApp().configure(cursor="")

    def ProjectHasFocus(self):
        """ Does Project Choice have focus """
        return (wx.Window.FindFocus() == self._projectChoice)


    def FilesHasFocus(self):
        """ Does Project Tree have focus """
        winWithFocus = wx.Window.FindFocus()
        if not winWithFocus:
            return False
        while winWithFocus:
            if winWithFocus == self._treeCtrl:
                return True
            winWithFocus = winWithFocus.GetParent()
        return False


    def ClearFolderState(self):
        config = GetApp().GetConfig()
        config.DeleteGroup(getProjectKeyName(self.GetDocument()))
        

    def SaveFolderState(self, event=None):
        """ 保存项目文件夹打开或关闭状态 """

        if self._loading:
            return
            
        folderList = []
        folderItemList = self._GetFolderItems(self._treeCtrl.GetRootItem())
        for item in folderItemList:
            #判断节点是否处于展开状态,如果是,则保存展开状态
            if self._treeCtrl.item(item, "open"):
                folderList.append(self._GetItemFolderPath(item))
        utils.profile_set(getProjectKeyName(self.GetDocument()), repr(folderList))


    def LoadFolderState(self):
        """ 加载项目文件夹打开或关闭状态"""
        self._loading = True
      
        config = GetApp().GetConfig()
        openFolderData = config.Read(getProjectKeyName(self.GetDocument()), "")
        if openFolderData:
            folderList = eval(openFolderData)
            folderItemList = self._GetFolderItems(self._treeCtrl.GetRootItem())
            for item in folderItemList:
                folderPath = self._GetItemFolderPath(item)
                if folderPath in folderList:
                    #展开节点
                    self._treeCtrl.item(item, open=True)
                else:
                    #关闭节点
                    self._treeCtrl.item(item, open=False)
        self._loading = False


    #----------------------------------------------------------------------------
    # Control events
    #----------------------------------------------------------------------------            
    def OnAddNewFile(self):
        items = self._treeCtrl.selection()
        if items:
            item = items[0]
            folderPath = self._GetItemFolderPath(item)
        else:
            folderPath = ""
        dlg = newfile.NewFileDialog(self.GetFrame(),_("New FileType"),folderPath)
        if dlg.ShowModal() == constants.ID_OK:
            if self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectAddFilesCommand(self.GetDocument(), [dlg.file_path], folderPath=folderPath)):
                self._prject_browser.OpenSelection()

    def OnAddFolder(self):
        if self.GetDocument():
            items = self._treeCtrl.selection()
            if items:
                item = items[0]
                if self._IsItemFile(item):
                    item = self._treeCtrl.parent(item)
                    
                folderDir = self._GetItemFolderPath(item)
            else:
                folderDir = ""
                
            if folderDir:
                folderDir += "/"
            folderPath = "%sUntitled" % folderDir
            i = 1
            while self._treeCtrl.FindFolder(folderPath):
                i += 1
                folderPath = "%sUntitled%s" % (folderDir, i)
            projectdir = self.GetDocument().GetModel().homeDir
            destfolderPath = os.path.join(projectdir,folderPath)
            try:
                os.mkdir(destfolderPath)
            except Exception as e:
                messagebox.showerror(GetApp().GetAppName(),str(e),parent= self.GetFrame())
                return
            self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectAddFolderCommand(self, self.GetDocument(), folderPath))
            #空文件夹下创建一个虚拟文件,防止空文件夹节点被删除
            dummy_file = os.path.join(destfolderPath,consts.DUMMY_NODE_TEXT)
            self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectAddFilesCommand(self.GetDocument(),[dummy_file],folderPath))
           # self._treeCtrl.UnselectAll()
            item = self._treeCtrl.FindFolder(folderPath)
            self._treeCtrl.selection_set(item)
            self._treeCtrl.focus(item)
            self._treeCtrl.see(item)
            self.OnRename()

    def AddFolder(self, folderPath):
        self._treeCtrl.AddFolder(folderPath)
        return True

    def DeleteFolder(self, folderPath,delete_folder_files=True):
        if delete_folder_files:
            projectdir = self.GetDocument().GetModel().homeDir
            folder_local_path = os.path.join(projectdir,folderPath)
            if os.path.exists(folder_local_path):
                try:
                    fileutils.RemoveDir(folder_local_path)
                except Exception as e:
                    messagebox.showerror( _("Delete Folder"),"Could not delete '%s'.  %s" % (os.path.basename(folder_local_path), e),
                                              parent= self.GetFrame())
                    return
        item = self._treeCtrl.FindFolder(folderPath)
        self.DeleteFolderItems(item)
        self._treeCtrl.delete(item)
        return True
        
    def DeleteFolderItems(self,folder_item):
        files = []
        items = self._treeCtrl.get_children(folder_item)
        for item in items:
            if self._treeCtrl.GetChildrenCount(item):
                self.DeleteFolderItems(item)
            else:
                file = self._GetItemFile(item)
                files.append(file)
        if files:
            self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectRemoveFilesCommand(self.GetDocument(), files))

    def OnAddFileToProject(self):
        project_template = self.GetDocumentManager().FindTemplateForTestPath(consts.PROJECT_EXTENSION)
        #注意这里最好不要设置initialdir,会自动选择上一次打开的目录
        descrs = strutils.gen_file_filters(project_template.GetDocumentType())
        paths = filedialog.askopenfilename(
                master=self._prject_browser,
                filetypes=descrs,
                multiple=True
        )
        if not paths:
            return
        newPaths = []
        #必须先格式化所有路径
        for path in paths:
            newPaths.append(fileutils.opj(path))
        folderPath = None
        item = self._treeCtrl.GetSingleSelectItem()
        if item:
            if not self._IsItemFile(item):
                folderPath = self._GetItemFolderPath(item)
        self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectAddFilesCommand(self.GetDocument(), newPaths, folderPath=folderPath))
        self.Activate()  # after add, should put focus on project editor


    def OnAddDirToProject(self):
        class AddDirProjectDialog(ui_base.CommonModaldialog):
            
            def __init__(self, parent,view):
                self._view = view
                ui_base.CommonModaldialog.__init__(self, parent)
                self.title(_("Add Directory Files to Project"))
                row = ttk.Frame(self.main_frame)
                ttk.Label(row, text=_("Directory:")).pack(side=tk.LEFT)
                self.dir_var = tk.StringVar(value=os.path.dirname(self._view.GetDocument().GetFilename()))
                dirCtrl = ttk.Entry(row, textvariable=self.dir_var)
                dirCtrl.pack(side=tk.LEFT,fill="x",expand=1)
               # dirCtrl.SetToolTipString(dirCtrl.GetValue())
                findDirButton = ttk.Button(row,text=_("Browse..."),command=self.OnBrowseButton)
                findDirButton.pack(side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0))
                row.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
                self.visibleTemplates = []
                for template in self._view.GetDocumentManager()._templates:
                    if template.IsVisible() and not isinstance(template,ProjectTemplate):
                        self.visibleTemplates.append(template)

                choices = []
                descr = ''
                for template in self.visibleTemplates:
                    if len(descr) > 0:
                        descr = descr + _('|')
                    descr = _(template.GetDescription()) + " (" + template.GetFileFilter() + ")"
                    choices.append(descr)
                choices.insert(0, _("All Files") + "(*.*)")  # first item
                row = ttk.Frame(self.main_frame)
                ttk.Label(row,text=_("Files of type:")).pack(side=tk.LEFT)
                self.filter_var = tk.StringVar()
                self.filterChoice = ttk.Combobox(row,  values=choices,textvariable=self.filter_var)
                self.filterChoice.current(0)
                self.filterChoice['state'] = 'readonly'
                self.filterChoice.pack(side=tk.LEFT,fill="x",expand=1)
                row.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
                misc.create_tooltip(self.filterChoice,_("Select file type filter."))
                self.subfolderChkVar = tk.IntVar(value=True)
                subfolderCtrl = ttk.Checkbutton(self.main_frame, text=_("Add files from subdirectories"),variable=self.subfolderChkVar).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
               # subfolderCtrl.SetValue(True)
                self.AddokcancelButton()

            def OnBrowseButton(self):
                path = filedialog.askdirectory(title=_("Choose a directory:"))
                if not path:
                    return
                self.dir_var.set(fileutils.opj(path))

            def _ok(self):
                index = self.filterChoice.current()
                self.template = None
                lastIndex = len(self.filterChoice['values']) -1
                if index and index != lastIndex:  # if not All or Any
                    self.template = self.visibleTemplates[index-1]
                ui_base.CommonModaldialog._ok(self)

        dlg = AddDirProjectDialog(GetApp().GetTopWindow(),self)
        status = dlg.ShowModal()
        if status == constants.ID_OK:
            if not os.path.exists(dlg.dir_var.get()):
                messagebox.showinfo(GetApp().GetAppName(),
                                       _("directory '%s' does not exist.") % dlg.dir_var.get(),
                                       parent=self.GetFrame(),
                                       )
                return

        if status == constants.ID_OK:
            GetApp().configure(cursor="circle")

            try:
                doc = self.GetDocument()
                searchSubfolders = dlg.subfolderChkVar.get()
                dirString = dlg.dir_var.get()
    
                if os.path.isfile(dirString):
                    # If they pick a file explicitly, we won't prevent them from adding it even if it doesn't match the filter.
                    # We'll assume they know what they're doing.
                    paths = [dirString]
                else:
                    paths = []
                    template = dlg.template
                    # do search in files on disk
                    for root, dirs, files in os.walk(dirString):
                        if not searchSubfolders and root != dirString:
                            break
    
                        for name in files:
                            if template is None:  # All
                                filename = os.path.join(root, name)
                                # if already in project, don't add it, otherwise undo will remove it from project even though it was already in it.
                                if not doc.IsFileInProject(filename):
                                    paths.append(filename)
                            else:  # use selected filter
                                if template.FileMatchesTemplate(name):
                                    filename = os.path.join(root, name)
                                    # if already in project, don't add it, otherwise undo will remove it from project even though it was already in it.
                                    if not doc.IsFileInProject(filename):
                                        paths.append(filename)
    
                folderPath = None
                selections = self._treeCtrl.selection()
                if selections:
                    item = selections[0]
                    if not self._IsItemFile(item):
                        folderPath = self._GetItemFolderPath(item)

                doc.GetCommandProcessor().Submit(projectcommand.ProjectAddFilesCommand(doc, paths, folderPath=folderPath))
                self.Activate()  # after add, should put focus on project editor
                
            finally:
                GetApp().configure(cursor="")


    def DoAddFilesToProject(self, filePaths, folderPath):
        # method used by Drag-n-Drop to add files to current Project
        self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectAddFilesCommand(self.GetDocument(), filePaths, folderPath))

    def OnRename(self):
        items = self._treeCtrl.selection()
        if not items:
            return
        item = items[0]
        if utils.is_linux():
            text = tkSimpleDialog.askstring(
                _("Enter New Name"),
                _("Enter New Name"),
                initialvalue=self._treeCtrl.item(item,"text"),
                parent=self.GetFrame()
            )
            if not text:
                return
            self.ChangeLabel(item, text)
        else:
            if items:
                self._treeCtrl.EditLabel(item)

    def OnEndLabelEdit(self, item,newName):
        if item == self._treeCtrl.GetRootItem():
            if not newName:
                #wx.MessageBox(_("project name could not be empty"),style=wx.OK|wx.ICON_ERROR)
                return
            else:
                #检查项目名称是否改变
                if self.GetDocument().GetModel().Name != newName:
                    self.GetDocument().GetModel().Name = newName
                    self.GetDocument().Modify(True)
                    #修改节点文本
                    self._treeCtrl.item(item,text=newName)
            return
        
        if not self.ChangeLabel(item, newName):
            return
            

    def ChangeLabel(self, item, newName):
        if not newName:
            return False
        if self._IsItemFile(item):
            oldFilePath = self._GetItemFilePath(item)
            newFilePath = os.path.join(os.path.dirname(oldFilePath), newName)
            doc = self.GetDocument()
            parent_item = self._treeCtrl.parent(item)
            if not doc.GetCommandProcessor().Submit(projectcommand.ProjectRenameFileCommand(doc, oldFilePath, newFilePath)):
                return False
            self._treeCtrl.SortChildren(self._treeCtrl.parent(parent_item))
        else:
            oldFolderPath = self._GetItemFolderPath(item)
            newFolderPath = os.path.dirname(oldFolderPath)
            if newFolderPath:
                newFolderPath += "/"
            newFolderPath += newName
            if newFolderPath == oldFolderPath:
                return True
            if self._treeCtrl.FindFolder(newFolderPath):
                messagebox.showwarning(_("Rename Folder"),_("Folder '%s' already exists.") % newName,parent=self.GetFrame())
                return False
            doc = self.GetDocument()
            if not doc.GetCommandProcessor().Submit(projectcommand.ProjectRenameFolderCommand(doc, oldFolderPath, newFolderPath)):
                return False
            self._treeCtrl.SortChildren(self._treeCtrl.parent(item))
            #should delete the folder item ,other it will have double folder item
            self._treeCtrl.Delete(item)

        return True

    def CanPaste(self):
        hasFilesInClipboard = False
        if not GetApp().TheClipboard.IsOpened():
            return hasFilesInClipboard
            
        fileDataObject = core.JsonDataobject()
        hasFilesInClipboard = GetApp().TheClipboard.GetData(fileDataObject)
        return hasFilesInClipboard
        
    def CopyFileItem(self,action):
        fileDataObject = core.JsonDataobject()
        items = self._treeCtrl.selection()
        file_items = []
        for item in items:
            filePath = self._GetItemFilePath(item)
            if filePath:
                d = {
                    'filePath':filePath,
                    'action':action,
                    'fileType':'file'
                }
                file_items.append(d)
        fileDataObject.SetData(file_items)
        if fileDataObject.GetDataSize() > 0 and GetApp().TheClipboard.Open():
            GetApp().TheClipboard.SetData(fileDataObject)

    def OnCut(self):
        self.CopyFileItem(self.CUT_FILE_TYPE)
        self.RemoveFromProject()

    def OnCopy(self):
        self.CopyFileItem(self.COPY_FILE_TYPE)
        
    def CopyToDest(self,src_path,file_name,dest_path,action_type):
        dest_file_path = os.path.join(dest_path,file_name)
        if not os.path.exists(dest_file_path):
            if action_type == self.COPY_FILE_TYPE:
                shutil.copy(src_path,dest_file_path)
            elif action_type == self.CUT_FILE_TYPE:
                shutil.move(src_path,dest_file_path)
            return dest_file_path
        src_dir_path = os.path.dirname(src_path)
        if not parserutils.ComparePath(src_dir_path,dest_path):
            if action_type == self.COPY_FILE_TYPE:
                ret = messagebox.askyesno(_("Copy File"),_("Dest file is already exist,Do you want to overwrite it?"),parent=self.GetFrame())
                if ret == True:
                    shutil.copy(src_path,dest_file_path)
            elif action_type == self.CUT_FILE_TYPE:
                ret = messagebox.askyesno(_("Move File"),_("Dest file is already exist,Do you want to overwrite it?"),parent=self.GetFrame())
                if ret == True:
                    shutil.move(src_path,dest_file_path)
            return dest_file_path
        if action_type == self.CUT_FILE_TYPE:
            return dest_file_path
        file_ext = strutils.get_file_extension(file_name)
        filename_without_ext = strutils.get_filename_without_ext(file_name)
        if sysutilslib.is_windows():
            dest_file_name = _("%s - Copy.%s") % (filename_without_ext,file_ext)
            dest_file_path = os.path.join(dest_path,dest_file_name)
            if os.path.exists(dest_file_path):
                i = 2
                while os.path.exists(dest_file_path):
                    dest_file_name = _("%s - Copy (%d).%s") % (filename_without_ext,i,file_ext)
                    dest_file_path = os.path.join(dest_path,dest_file_name)
                    i += 1
        else:
            dest_file_name = _("%s (copy).%s") % (filename_without_ext,file_ext)
            dest_file_path = os.path.join(dest_path,dest_file_name)
            if os.path.exists(dest_file_path):
                i = 2
                while os.path.exists(dest_file_path):
                    if i == 2:
                        dest_file_name = _("%s (another copy).%s") % (filename_without_ext,file_ext)
                    elif i == 3:
                        dest_file_name = _("%s (%drd copy).%s") % (filename_without_ext,i,file_ext)
                    else:
                        dest_file_name = _("%s (%dth copy).%s") % (filename_without_ext,i,file_ext)
                    dest_file_path = os.path.join(dest_path,dest_file_name)
                    i += 1
        shutil.copy(src_path,dest_file_path)
        return dest_file_path

    def OnPaste(self):
        if GetApp().TheClipboard.Open():
            paste_items = []
            fileDataObject = core.JsonDataobject()
            if GetApp().TheClipboard.GetData(fileDataObject):
                folderPath = None
                dest_files = []
                item = self._treeCtrl.GetSingleSelectItem()
                if item:
                    folderPath = self._GetItemFolderPath(item)
                destFolderPath = os.path.join(self.GetDocument().GetModel().homeDir,folderPath)
                for src_file in fileDataObject.GetData():
                    filepath =  src_file['filePath']
                    action = src_file['action']
                    filename = os.path.basename(filepath)
                    if not os.path.exists(filepath):
                        messagebox.showerror(GetApp().GetAppName(),_("The item '%s' does not exist in the project directory.It may have been moved,renamed or deleted.") % filename,parent= self.GetFrame())
                        return
                    try:
                        if action == self.COPY_FILE_TYPE:
                            dest_file_path = self.CopyToDest(filepath,filename,destFolderPath,self.COPY_FILE_TYPE)
                            dest_files.append(dest_file_path)
                        elif action == self.CUT_FILE_TYPE:
                            dest_file_path = self.CopyToDest(filepath,filename,destFolderPath,self.CUT_FILE_TYPE)
                            dest_files.append(dest_file_path)
                        else:
                            assert(False)
                    except Exception as e:
                        messagebox.showerror(GetApp().GetAppName(),str(e),parent= self.GetFrame())
                        return
                self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectAddFilesCommand(self.GetDocument(), dest_files, folderPath))
                paste_item = self._treeCtrl.GetSingleSelectItem()
                paste_items.append(paste_item)
            GetApp().TheClipboard.Close()
           # for select_item in paste_items:
             #   self._treeCtrl.selection_set(select_item)

    def RemoveFromProject(self):
        items = self._treeCtrl.selection()
        files = []
        for item in items:
            if not self._IsItemFile(item):
                folderPath = self._GetItemFolderPath(item)
                self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectRemoveFolderCommand(self, self.GetDocument(), folderPath))
            else:
                file = self._GetItemFile(item)
                if file:
                    files.append(file)
        if files:
            self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectRemoveFilesCommand(self.GetDocument(), files))
        
    def GetOpenDocument(self,filepath):
        openDocs = self.GetDocumentManager().GetDocuments()[:]  # need copy or docs shift when closed
        for d in openDocs:
            if parserutils.ComparePath(d.GetFilename(),filepath):
                return d
        return None

    def DeleteFromProject(self):
        is_file_selected = False
        is_folder_selected = False
        if self._HasFilesSelected():
            is_file_selected = True
        if self._HasFoldersSelected():
            is_folder_selected = True
        if is_file_selected and not is_folder_selected:
            yesNoMsg = messagebox.askyesno(_("Delete Files"),_("Delete cannot be reversed.\n\nRemove the selected files from the\nproject and file system permanently?"),
                         parent=self.GetFrame())
        elif is_folder_selected and not is_file_selected:
            yesNoMsg = messagebox.askyesno(_("Delete Folder"),_("Delete cannot be reversed.\n\nRemove the selected folder and its files from the\nproject and file system permanently?"),
                         parent=self.GetFrame())
        elif is_folder_selected and is_file_selected:
            yesNoMsg = messagebox.askyesno(_("Delete Folder And Files"),_("Delete cannot be reversed.\n\nRemove the selected folder and files from the\nproject and file system permanently?"),
             parent=self.GetFrame())
        if yesNoMsg == False:
            return
        items = self._treeCtrl.selection()
        delFiles = []
        for item in items:
            if self._IsItemFile(item):
                filePath = self._GetItemFilePath(item)
                if filePath and filePath not in delFiles:
                    # remove selected files from file system
                    if os.path.exists(filePath):
                        try:
                            #close the open document first if file opened
                            open_doc =  self.GetOpenDocument(filePath)
                            if open_doc:
                                open_doc.Modify(False)  # make sure it doesn't ask to save the file
                                self.GetDocumentManager().CloseDocument(open_doc, True)
                            os.remove(filePath)
                        except:
                            wx.MessageBox("Could not delete '%s'.  %s" % (os.path.basename(filePath), sys.exc_value),
                                          _("Delete File"),
                                          wx.OK | wx.ICON_ERROR,
                                          self.GetFrame())
                            return
                    # remove selected files from project
                    self.GetDocument().RemoveFiles([filePath])
                    delFiles.append(filePath)
            else:
                file_items = self._GetFolderFileItems(item)
                for fileItem in file_items:
                    filePath = self._GetItemFilePath(fileItem)
                    open_doc = self.GetOpenDocument(filePath)
                    if open_doc:
                        open_doc.Modify(False)  # make sure it doesn't ask to save the file
                        self.GetDocumentManager().CloseDocument(open_doc, True)
                folderPath = self._GetItemFolderPath(item)
                self.GetDocument().GetCommandProcessor().Submit(projectcommand.ProjectRemoveFolderCommand(self, self.GetDocument(), folderPath,True))
            
    def DeleteProject(self, noPrompt=False, closeFiles=True, delFiles=True):
        
        class DeleteProjectDialog(ui_base.CommonModaldialog):
        
            def __init__(self, parent, doc):
                ui_base.CommonModaldialog.__init__(self, parent)
                self.title(_("Delete Project"))
                ttk.Label(self.main_frame,text=_("Delete cannot be reversed.\nDeleted files are removed from the file system permanently.\n\nThe project file '%s' will be closed and deleted.") % os.path.basename(doc.GetFilename())).\
                    pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y))
                self._delFilesChkVar = tk.IntVar(value=True)
                delFilesCtrl = ttk.Checkbutton(self.main_frame,text=_("Delete all files in project"),variable=self._delFilesChkVar)
                delFilesCtrl.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
                misc.create_tooltip(delFilesCtrl,_("Deletes files from disk, whether open or closed"))
                
                self._closeDeletedChkVar = tk.IntVar(value=True)
                closeDeletedCtrl = ttk.Checkbutton(self.main_frame,text=_("Close open files belonging to project"),variable=self._closeDeletedChkVar)
                closeDeletedCtrl.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
                misc.create_tooltip(closeDeletedCtrl,_("Closes open editors for files belonging to project"))
                self.AddokcancelButton()

        doc = self.GetDocument()
        if not noPrompt:
            dlg = DeleteProjectDialog(self.GetFrame(), doc)
            status = dlg.ShowModal()
            delFiles = dlg._delFilesChkVar.get()
            closeFiles = dlg._closeDeletedChkVar.get()
            if status == constants.ID_CANCEL:
                return

        if closeFiles or delFiles:
            filesInProject = doc.GetFiles()
            # don't remove self prematurely
            filePath = doc.GetFilename()
            if filePath in filesInProject:
                filesInProject.remove(filePath)
            
            # don't close/delete files outside of project's directory
            homeDir = doc.GetModel().homeDir + os.sep
            for filePath in filesInProject[:]:
                fileDir = os.path.dirname(filePath) + os.sep
                if not fileDir.startswith(homeDir):  
                    filesInProject.remove(filePath)

        if closeFiles:
            # close any open views of documents in the project
            openDocs = self.GetDocumentManager().GetDocuments()[:]  # need copy or docs shift when closed
            for d in openDocs:
                if d.GetFilename() in filesInProject:
                    d.Modify(False)  # make sure it doesn't ask to save the file
                    if isinstance(d.GetDocumentTemplate(), ProjectTemplate):  # if project, remove from project list drop down
                        if self.GetDocumentManager().CloseDocument(d, True):
                            self.RemoveProjectUpdate(d)
                    else:  # regular file
                        self.GetDocumentManager().CloseDocument(d, True)
                
        # remove files in project from file system
        if delFiles:
            dirPaths = []
            for filePath in filesInProject:
                if os.path.isfile(filePath):
                    try:
                        dirPath = os.path.dirname(filePath)
                        if dirPath not in dirPaths:
                            dirPaths.append(dirPath)
                            
                        os.remove(filePath)
                    except:
                        wx.MessageBox("Could not delete file '%s'.\n%s" % (filePath, sys.exc_value),
                                      _("Delete Project"),
                                      wx.OK | wx.ICON_ERROR,
                                      self.GetFrame())
                                      
        filePath = doc.GetFilename()
        
        self.ClearFolderState()  # remove from registry folder settings
        #delete project regkey config
        GetApp().GetConfig().DeleteGroup(getProjectKeyName(doc))

        # close project
        if doc:            
            doc.Modify(False)  # make sure it doesn't ask to save the project
            if self.GetDocumentManager().CloseDocument(doc, True):
                self.RemoveCurrentDocumentUpdate()
            doc.document_watcher.RemoveFileDoc(doc)

        # remove project file
        if delFiles:
            dirPath = os.path.dirname(filePath)
            if dirPath not in dirPaths:
                dirPaths.append(dirPath)
        if os.path.isfile(filePath):
            try:
                os.remove(filePath)
            except:
                wx.MessageBox("Could not delete project file '%s'.\n%s" % (filePath, sys.exc_value),
                              _("Delete Prjoect"),
                              wx.OK | wx.ICON_EXCLAMATION,
                              self.GetFrame())
            
        # remove empty directories from file system
        if delFiles:
            dirPaths.sort()     # sorting puts parent directories ahead of child directories
            dirPaths.reverse()  # remove child directories first

            for dirPath in dirPaths:
                if os.path.isdir(dirPath):
                    files = os.listdir(dirPath)
                    if not files:
                        try:
                            os.rmdir(dirPath)
                        except:
                            wx.MessageBox("Could not delete empty directory '%s'.\n%s" % (dirPath, sys.exc_value),
                                          _("Delete Project"),
                                          wx.OK | wx.ICON_EXCLAMATION,
                                          self.GetFrame())
        

    def OnKeyPressed(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_DELETE:
            self.RemoveFromProject(event)
        else:
            event.Skip()


    def OnSelectAll(self, event):
        project = self.GetDocument()
        if project:
            self.DoSelectAll(self._treeCtrl.GetRootItem())


    def DoSelectAll(self, parentItem):
        (child, cookie) = self._treeCtrl.GetFirstChild(parentItem)
        while child.IsOk():
            if self._IsItemFile(child):
                self._treeCtrl.SelectItem(child)
            else:
                self.DoSelectAll(child)
            (child, cookie) = self._treeCtrl.GetNextChild(parentItem, cookie)

    def GetOpenDocumentTemplate(self,project_file):
        template = None
        document_template_name = utils.profile_get(self.GetDocument().GetFileKey(project_file,"Open"),"")
        filename = os.path.basename(project_file.filePath)
        if not document_template_name:
            document_template_name = utils.profile_get("Open/filenames/%s" % filename,"")
            if not document_template_name:
                document_template_name = utils.profile_get("Open/extensions/%s" % strutils.get_file_extension(filename),"")
        if document_template_name:
            template = wx.GetApp().GetDocumentManager().FindTemplateForDocumentType(document_template_name)
        return template
        
    def OnOpenSelectionWith(self, event):
        item_file = self._GetItemFile(self._treeCtrl.GetSingleSelectItem())
        selected_file_path = item_file.filePath
        dlg = ProjectUI.EditorSelectionDialog(wx.GetApp().GetTopWindow(),-1,_("Editor Selection"),item_file,self.GetDocument())
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            found_view = utils.GetOpenView(selected_file_path)
            if found_view:
                ret = wx.MessageBox(_("The document \"%s\" is already open,Do you want to close it?") %selected_file_path,style=wx.YES_NO|wx.ICON_QUESTION)
                if ret == wx.YES:
                    found_view.Close()
                    document = found_view.GetDocument()
                    if document in self.GetDocumentManager().GetDocuments():
                        document.Destroy()
                    frame = found_view.GetFrame()
                    if frame:
                        frame.Destroy()
                else:
                    return
            doc = self.GetDocumentManager().CreateTemplateDocument(dlg.selected_template,selected_file_path, wx.lib.docview.DOC_SILENT)
            if doc is not None and dlg._is_changed and utils.GetOpenView(selected_file_path):
                iconIndex = self._treeCtrl.GetTemplateIconIndex(dlg.selected_template)
                if dlg.OpenwithMode == dlg.OPEN_WITH_FILE_PATH:
                    utils.ProfileSet(self.GetDocument().GetFileKey(item_file,"Open"),\
                                     dlg.selected_template.GetDocumentName())
                    file_template = wx.GetApp().GetDocumentManager().FindTemplateForPath(selected_file_path)
                    if file_template != dlg.selected_template:
                        item = self._treeCtrl.GetSelections()[0]
                        if iconIndex != -1:
                            self._treeCtrl.SetItemImage(item, iconIndex, wx.TreeItemIcon_Normal)
                            self._treeCtrl.SetItemImage(item, iconIndex, wx.TreeItemIcon_Expanded)
                        
                elif dlg.OpenwithMode == dlg.OPEN_WITH_FILE_NAME:
                    filename = os.path.basename(selected_file_path)
                    utils.ProfileSet("Open/filenames/%s" % filename,dlg.selected_template.GetDocumentName())
                    if iconIndex != -1:
                        self.ChangeItemsImageWithFilename(self._treeCtrl.GetRootItem(),filename,iconIndex)
                elif dlg.OpenwithMode == dlg.OPEN_WITH_FILE_EXTENSION:
                    extension = strutils.GetFileExt(os.path.basename(selected_file_path))
                    utils.ProfileSet("Open/extensions/%s" % extension,dlg.selected_template.GetDocumentName())
                    if iconIndex != -1:
                        self.ChangeItemsImageWithExtension(self._treeCtrl.GetRootItem(),extension,iconIndex)
                else:
                    assert(False)
        dlg.Destroy()
        

    def ChangeItemsImageWithFilename(self,parent_item,filename,icon_index):
        if parent_item is None:
            return
        (item, cookie) = self._treeCtrl.GetFirstChild(parent_item)
        while item:
            if self._IsItemFile(item):
                file_name = self._treeCtrl.GetItemText(item)
                if file_name == filename:
                    self._treeCtrl.SetItemImage(item, icon_index, wx.TreeItemIcon_Normal)
                    self._treeCtrl.SetItemImage(item, icon_index, wx.TreeItemIcon_Expanded)
            self.ChangeItemsImageWithFilename(item,filename,icon_index)
            (item, cookie) = self._treeCtrl.GetNextChild(parent_item, cookie)

    #----------------------------------------------------------------------------
    # Convenience methods
    #----------------------------------------------------------------------------

    def _HasFiles(self):
        if not self._treeCtrl:
            return False
        return self._treeCtrl.GetCount() > 1    #  1 item = root item, don't count as having files


    def _HasFilesSelected(self):
        if not self._treeCtrl:
            return False
        items = self._treeCtrl.selection()
        if not items:
            return False
        for item in items:
            if self._IsItemFile(item):
                return True
        return False


    def _HasFoldersSelected(self):
        if not self._treeCtrl:
            return False
        items = self._treeCtrl.selection()
        if not items:
            return False
        for item in items:
            if not self._IsItemFile(item):
                return True
        return False


    def _MakeProjectName(self, project):
        return project.GetPrintableName()


    def _GetItemFilePath(self, item):
        filePath = self._GetItemFile(item)
        if filePath:
            return filePath
        else:
            return None


    def _GetItemFolderPath(self, item):
        rootItem = self._treeCtrl.GetRootItem()
        if item == rootItem:
            return ""
            
        if self._IsItemFile(item):
            item = self._treeCtrl.parent(item)
        
        folderPath = ""
        while item != rootItem:
            if folderPath:
                folderPath = self._treeCtrl.item(item,"text") + "/" + folderPath
            else:
                folderPath = self._treeCtrl.item(item,"text")
            #获取父节点
            item = self._treeCtrl.parent(item)
            
        return folderPath

            
    def _GetItemFile(self, item):
        return self._treeCtrl.GetPyData(item)


    def _IsItemFile(self, item):
        return self._GetItemFile(item) != None


    def _IsItemProcessModelFile(self, item):
        if ACTIVEGRID_BASE_IDE:
            return False

        if self._IsItemFile(item):
            filepath = self._GetItemFilePath(item)
            ext = None
            for template in self.GetDocumentManager().GetTemplates():
                if template.GetDocumentType() == ProcessModelEditor.ProcessModelDocument:
                    ext = template.GetDefaultExtension()
                    break;
            if not ext:
                return False

            if filepath.endswith(ext):
                return True

        return False

    def _GetFolderItems(self, parentItem):
        folderItems = []
        childrenItems = self._treeCtrl.get_children(parentItem)
        for childItem in childrenItems:
            if not self._IsItemFile(childItem):
                folderItems.append(childItem)
                folderItems += self._GetFolderItems(childItem)
        return folderItems
        
    def _GetFolderFileItems(self, parentItem):
        fileItems = []
        childrenItems = self._treeCtrl.get_children(parentItem)
        for childItem in childrenItems:
            if self._IsItemFile(childItem):
                fileItems.append(childItem)
            else:
                fileItems.extend(self._GetFolderFileItems(childItem))
        return fileItems
        
    def check_for_external_changes(self):
        if self._asking_about_external_change:
            return
        self._asking_about_external_change = True
        if self._alarm_event == filewatcher.FileEventHandler.FILE_MODIFY_EVENT:
            ret = messagebox.askyesno(_("Reload Project.."),_("Project File \"%s\" has already been modified outside,Do you want to reload It?") % self.GetDocument().GetFilename(),parent=self.GetFrame())
            if ret == True:
                document = self.GetDocument()
                document.OnOpenDocument(document.GetFilename())
                
        elif self._alarm_event == filewatcher.FileEventHandler.FILE_MOVED_EVENT or \
             self._alarm_event == filewatcher.FileEventHandler.FILE_DELETED_EVENT:
            ret = messagebox.askyesno(_("Project not exist.."),_("Project File \"%s\" has already been moved or deleted outside,Do you want to close this Project?") % self.GetDocument().GetFilename(),parent=self.GetFrame())
            document = self.GetDocument()
            if ret == True:
                self.CloseProject()
            else:
                document.Modify(True)
                
        self._asking_about_external_change = False
        misc.AlarmEventView.check_for_external_changes(self)
                
    def UpdateUI(self, command_id):
        if command_id in[constants.ID_CLOSE_PROJECT,constants.ID_SAVE_PROJECT ,constants.ID_DELETE_PROJECT,constants.ID_CLEAN_PROJECT,\
                         constants.ID_ARCHIVE_PROJECT,constants.ID_IMPORT_FILES,constants.ID_ADD_FILES_TO_PROJECT,constants.ID_ADD_DIR_FILES_TO_PROJECT,\
                         constants.ID_PROPERTIES,constants.ID_OPEN_FOLDER_PATH,constants.ID_ADD_FOLDER,constants.ID_ADD_NEW_FILE]:
            return self.GetDocument() is not None
        elif command_id == constants.ID_ADD_CURRENT_FILE_TO_PROJECT:
            return self.GetDocument() is not None and GetApp().MainFrame.GetNotebook().get_current_editor() is not None
        return False
        
    def OnAddCurrentFileToProject(self):
        text_view = GetApp().MainFrame.GetNotebook().get_current_editor().GetView()
        doc = text_view.GetDocument()
        filepath = doc.GetFilename()
        projectDoc = self.GetDocument()
        if projectDoc.IsFileInProject(filepath):
            messagebox.showwarning(GetApp().GetAppName(),_("Current document is already in the project"))
            return
        folderPath = None
        item = self._treeCtrl.GetSingleSelectItem()
        if item:
            folderPath = self._GetItemFolderPath(item)
        if projectDoc.GetCommandProcessor().Submit(projectcommand.ProjectAddFilesCommand(projectDoc, [filepath],folderPath=folderPath)):
            AddProjectMapping(doc, projectDoc)
            self.Activate()  # after add, should put focus on project editor
            if folderPath is None:
                folderPath = ""
            newFilePath = os.path.join(projectDoc.GetModel().homeDir,folderPath,os.path.basename(filepath))
            if not os.path.exists(newFilePath):
                return
            if not parserutils.ComparePath(newFilePath,filepath):
                openDoc = doc.GetOpenDocument(newFilePath)
                if openDoc:
                    messagebox.showwarning(GetApp().GetAppName(),_("Project file is already opened"))
                    openDoc.GetFirstView().GetFrame().SetFocus()
                    return
                doc.FileWatcher.StopWatchFile(doc)
                doc.SetFilename(newFilePath)
                doc.FileWatcher.StartWatchFile(doc)
            doc.SetDocumentModificationDate()

class ProjectFileDropTarget(newTkDnD.FileDropTarget):

    def __init__(self, view):
        newTkDnD.FileDropTarget.__init__(self)
        self._view = view

    def OnDropFiles(self, x, y, filePaths):
        #添加到项目中的文件
        addto_project_filePaths = []
        for filePath in filePaths:
            #项目文件直接打开
            if filePath.endswith(consts.PROJECT_EXTENSION):
                self._view.OpenProject(filePath)
            else:
                addto_project_filePaths.append(filePath)
        """ Do actual work of dropping files into project """
        if self._view.GetDocument():
            if not addto_project_filePaths:
                return False
            folderPath = None
            folderItem = self._view._treeCtrl.GetSingleSelectItem()
            if folderItem:
                folderPath = self._view._GetItemFolderPath(folderItem)
            self._view.DoAddFilesToProject(addto_project_filePaths, folderPath)
            return True
        else:
            if addto_project_filePaths:
                messagebox.showwinfo(GetApp().GetAppName(),_('There is no available project yet.'),self._view.GetFrame())
        return False


    def OnDragOver(self, x, y, default):
        """ Feedback to show copy cursor if copy is allowed """
        if self._view.GetDocument():  # only allow drop if project exists
            return wx.DragCopy
        return wx.DragNone

class ProjectOptionsPanel(ui_utils.BaseConfigurationPanel):


    def __init__(self, master,**kwargs):
        ui_utils.BaseConfigurationPanel.__init__(self,master=master,**kwargs)
        self.projectsavedoc_chkvar = tk.IntVar(value=utils.profile_get_int(consts.PROJECT_DOCS_SAVED_KEY, True))
        projSaveDocsCheckBox = ttk.Checkbutton(self, text=_("Remember open projects"),variable=self.projectsavedoc_chkvar)
        projSaveDocsCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        self.promptSavedoc_chkvar = tk.IntVar(value=utils.profile_get_int("PromptSaveProjectFile", True))
        promptSaveCheckBox = ttk.Checkbutton(self, text=_("Warn when run and save modify project files"),variable=self.promptSavedoc_chkvar)
        promptSaveCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        self.loadFolderState_chkvar = tk.IntVar(value=utils.profile_get_int("LoadFolderState", True))
        loadFolderStateCheckBox = ttk.Checkbutton(self, text=_("Load folder state when open project"),variable=self.loadFolderState_chkvar)
        loadFolderStateCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
##        if not ACTIVEGRID_BASE_IDE:
##            self._projShowWelcomeCheckBox = wx.CheckBox(self, -1, _("Show Welcome Dialog"))
##            self._projShowWelcomeCheckBox.SetValue(config.ReadInt("RunWelcomeDialog2", True))
##            projectSizer.Add(self._projShowWelcomeCheckBox, 0, wx.ALL, HALF_SPACE)
##            
##            sizer = wx.BoxSizer(wx.HORIZONTAL)
##            sizer.Add(wx.StaticText(self, -1, _("Default language for projects:")), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, HALF_SPACE)
##            self._langCtrl = wx.Choice(self, -1, choices=projectmodel.LANGUAGE_LIST)            
##            self._langCtrl.SetStringSelection(config.Read(APP_LAST_LANGUAGE, projectmodel.LANGUAGE_DEFAULT))
##            self._langCtrl.SetToolTipString(_("Programming language to be used throughout the project."))
##            sizer.Add(self._langCtrl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, MAC_RIGHT_BORDER)
##            projectSizer.Add(sizer, 0, wx.ALL, HALF_SPACE)

    def OnUseSashSelect(self, event):
        if not self._useSashMessageShown:
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("Document Options")
            wx.MessageBox("Project window embedded mode changes will not appear until the application is restarted.",
                          msgTitle,
                          wx.OK | wx.ICON_INFORMATION,
                          self.GetParent())
            self._useSashMessageShown = True


    def OnOK(self, optionsDialog):
        utils.profile_set(consts.PROJECT_DOCS_SAVED_KEY, self.projectsavedoc_chkvar.get())
        utils.profile_set("PromptSaveProjectFile", self.promptSavedoc_chkvar.get())
        utils.profile_set("LoadFolderState", self.loadFolderState_chkvar.get())
       # if not ACTIVEGRID_BASE_IDE:
         #   config.WriteInt("RunWelcomeDialog2", self._projShowWelcomeCheckBox.GetValue())
          #  config.Write(APP_LAST_LANGUAGE, self._langCtrl.GetStringSelection())
        return True


    def GetIcon(self):
        return getProjectIcon()

