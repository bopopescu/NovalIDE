# -*- coding: utf-8 -*-
from noval import GetApp,_,NewId
import noval.iface as iface
import noval.plugin as plugin
from noval.project.basebrowser import *
import noval.consts as consts
import os
import noval.python.project.viewer as projectviewer
import noval.python.project.rundocument as runprojectdocument

class PythonProjectTreeCtrl(ProjectTreeCtrl):
    #----------------------------------------------------------------------------
    # Overridden Methods
    #----------------------------------------------------------------------------

    def __init__(self, master, **kw):
        ProjectTreeCtrl.__init__(self,master,**kw)
        
    def AppendPackageFolder(self, parent, folderName):
        '''
            包文件夹节点图标和普通文件夹图标不一样
        '''
        item = self.insert(parent, "end", text=folderName, image=self._packageFolderImage)
        return item
        
    def AddPackageFolder(self, folderPath):
        '''
            添加包文件夹
        '''
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
                    item = self.AppendPackageFolder(item, folderName)
                    folderItems.append(item)

        return folderItems


class ProjectBrowser(BaseProjectbrowser):
    """description of class"""

    def BuildFileList(self,file_list):
        '''put the package __init__.py to the first item'''
        package_initfile_path = None
        for file_path in file_list:
            if os.path.basename(file_path).lower() == projectviewer.PythonProjectView.PACKAGE_INIT_FILE:
                package_initfile_path = file_path
                file_list.remove(file_path)
                break
        if package_initfile_path is not None:
            file_list.insert(0,package_initfile_path)
            
    def GetProjectTreectrl(self,**tree_kw):
        return PythonProjectTreeCtrl(self,
            yscrollcommand=self.vert_scrollbar.set,**tree_kw)
            
    def CreateView(self):
        return projectviewer.PythonProjectView(self)
        
    def Run(self):
        self.GetView().Run()
        
    def DebugRun(self):
        self.GetView().DebugRun()
        
    def BreakintoDebugger(self):
        self.GetView().BreakintoDebugger()

    def GetPopupFileMenu(self,item):
        menu = BaseProjectbrowser.GetPopupFileMenu(self,item)
        tree_item = self.tree.GetSingleSelectItem()
        filePath = self.GetView()._GetItemFilePath(tree_item)
##        itemIDs = []
        if self.GetView()._IsItemFile(tree_item) and fileutils.is_python_file(filePath):
            
            menuBar = GetApp().Menubar
            menu_item = menuBar.FindItemById(constants.ID_RUN)
            menu.InsertAfter(constants.ID_REMOVE_FROM_PROJECT,constants.ID_RUN,menu_item.label,img=menu_item.image,handler=lambda:self.ProcessEvent(constants.ID_RUN))
            
            debug_menu = tkmenu.PopupMenu()
            
            debug_menu_id = NewId()
            menu.InsertMenuAfter(constants.ID_RUN,debug_menu_id,_("Debug"),debug_menu)
            menu_item = menuBar.FindItemById(constants.ID_DEBUG)
            debug_menu.AppendMenuItem(menu_item,handler=lambda:self.ProcessEvent(constants.ID_DEBUG))
            
            item = tkmenu.MenuItem(constants.ID_BREAK_INTO_DEBUGGER,_("&Break into Debugger"), None,None,None)
            debug_menu.AppendMenuItem(item,handler=lambda:self.ProcessEvent(constants.ID_BREAK_INTO_DEBUGGER))
            
            menu.InsertAfter(debug_menu_id,constants.ID_SET_PROJECT_STARTUP_FILE,_("Set as Startup File..."),handler=lambda:self.ProcessEvent(constants.ID_SET_PROJECT_STARTUP_FILE))
 
        return menu

    def ProcessEvent(self, id):
        if id == constants.ID_SET_PROJECT_STARTUP_FILE:
            self.GetView().SetProjectStartupFile()
            return True
        elif id == constants.ID_RUN:
            self.Run()
            return True
        elif id == constants.ID_DEBUG:
            self.DebugRun()
            return True
        elif id == constants.ID_BREAK_INTO_DEBUGGER:
            self.BreakintoDebugger()
            return True
        elif id == constants.ID_ADD_PACKAGE_FOLDER:
            self.GetView().OnAddPackageFolder()
            return True
        else:
            return BaseProjectbrowser.ProcessEvent(self,id)

    def _InitCommands(self):
        BaseProjectbrowser._InitCommands(self)
        GetApp().InsertCommand(constants.ID_ADD_FOLDER,constants.ID_ADD_PACKAGE_FOLDER,_("&Project"),_("New Package Folder"),image=GetApp().GetImage("project/python/package.png"),\
                               handler=lambda:self.ProcessEvent(constants.ID_ADD_PACKAGE_FOLDER),tester=lambda:self.GetView().UpdateUI(constants.ID_ADD_PACKAGE_FOLDER))
        
    def GetPopupFolderItemIds(self):
        folder_item_ids = BaseProjectbrowser.GetPopupFolderItemIds(self)
        i = folder_item_ids.index(constants.ID_ADD_FOLDER)
        folder_item_ids.insert(i+1,constants.ID_ADD_PACKAGE_FOLDER)
        return folder_item_ids

    def GetPopupProjectItemIds(self):
        project_item_ids = BaseProjectbrowser.GetPopupProjectItemIds(self)
        if constants.ID_ADD_FOLDER in project_item_ids:
            i = project_item_ids.index(constants.ID_ADD_FOLDER)
            project_item_ids.insert(i+1,constants.ID_ADD_PACKAGE_FOLDER)
        return project_item_ids
    
class ProjectViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        #更改默认项目模板类
        GetApp().project_template_class = projectviewer.PythonProjectTemplate
        GetApp().project_document_class = runprojectdocument.PythonProjectDocument
        GetApp().project_view_class = projectviewer.PythonProjectView
        #此处创建项目模板,时机最佳
        GetApp().CreateProjectTemplate()
        GetApp().MainFrame.AddView(consts.PROJECT_VIEW_NAME,ProjectBrowser, _("Project Browser"), "nw",default_position_key="A",image_file="project/project_view.ico")


