# -*- coding: utf-8 -*-
from noval import GetApp,_
import noval.iface as iface
import noval.plugin as plugin
from noval.project.basebrowser import *
import noval.consts as consts
import os
import noval.python.project.viewer as projectviewer

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

class ProjectViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(consts.PROJECT_VIEW_NAME,ProjectBrowser, _("Project Browser"), "nw",default_position_key="A",image_file="project/project_view.ico")


consts.DEFAULT_PLUGINS += ("noval.python.project.browser.ProjectViewLoader",)