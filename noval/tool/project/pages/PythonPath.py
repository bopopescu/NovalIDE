import wx
from noval.tool.consts import SPACE,HALF_SPACE,_
import wx.dataview as dataview
import noval.tool.images as images
import os
import noval.parser.utils as parserutils
import noval.util.sysutils as sysutils
import wx.lib.agw.flatmenu as flatmenu
import noval.tool.project.PythonVariables as PythonVariables
import ProjectDialog
import BasePanel
import noval.util.utils as utils
import EnvironmentMixin
import noval.tool.interpreter.PythonPathMixin as PythonPathMixin

class InternalPathPage(wx.Panel):
    
    ID_NEW_ZIP = wx.NewId()
    ID_NEW_EGG = wx.NewId()
    ID_NEW_WHEEL = wx.NewId()
    def __init__(self,parent,project_document):
        wx.Panel.__init__(self, parent)
        self.current_project_document = project_document
        self.Sizer = wx.BoxSizer()
        
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.tree_ctrl = wx.TreeCtrl(self,size=(300,-1),style=wx.TR_NO_LINES|wx.TR_HIDE_ROOT|wx.TR_DEFAULT_STYLE)
        left_sizer.Add(self.tree_ctrl, 1,  wx.EXPAND)
        
        iconList = wx.ImageList(16, 16, initialCount = 1)
        folder_bmp = images.load("packagefolder_obj.gif")
        self.FolderIdx = iconList.Add(folder_bmp)
        self.tree_ctrl.AssignImageList(iconList)
        self.tree_ctrl.AddRoot("InternalPathList")
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.add_path_btn = wx.Button(self, -1, _("Add Path.."))
        wx.EVT_BUTTON(self.add_path_btn, -1, self.AddNewPath)
        right_sizer.Add(self.add_path_btn, 0, wx.TOP|wx.EXPAND, SPACE*3)
        
        self.add_file_btn = wx.Button(self, -1, _("Add File..."))
        wx.EVT_BUTTON(self.add_file_btn, -1, self.AddNewFilePath)
        right_sizer.Add(self.add_file_btn, 0, wx.TOP|wx.EXPAND, SPACE)
        
        self.remove_path_btn = wx.Button(self, -1, _("Remove Path..."))
        wx.EVT_BUTTON(self.remove_path_btn, -1, self.RemovePath)
        right_sizer.Add(self.remove_path_btn, 0, wx.TOP|wx.EXPAND, SPACE)
        
        self.Sizer.Add(left_sizer, 1, wx.EXPAND|wx.RIGHT,HALF_SPACE)
        self.Sizer.Add(right_sizer, 0,wx.EXPAND|wx.LEFT|wx.RIGHT,HALF_SPACE)
        
        self.Fit()
        self.AppendPathPath()
        
    def AppendPathPath(self):
        path_str = utils.ProfileGet(self.GetParent().GetParent().ProjectDocument.GetKey() + "/InternalPath","[]")
        try:
            python_path_list = eval(path_str)
        except:
            python_path_list = []
        for path in python_path_list:
            item = self.tree_ctrl.AppendItem(self.tree_ctrl.GetRootItem(), path)
            self.tree_ctrl.SetItemImage(item,self.FolderIdx,wx.TreeItemIcon_Normal)

    def AddNewFilePath(self,event):
        
        dlg = ProjectDialog.SelectModuleFileDialog(self,-1,_("Select Zip/Egg/Wheel File"),self.current_project_document.GetModel(),False,['egg','zip','whl'])
        if dlg.ShowModal() == wx.ID_OK:
            main_module_path = os.path.join(PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE) , self.current_project_document.\
                    GetModel().GetRelativePath(dlg.module_file))
            if self.CheckPathExist(main_module_path):
                wx.MessageBox(_("Path already exist"),_("Add Path"),wx.OK,self)
            else:
                item = self.tree_ctrl.AppendItem(self.tree_ctrl.GetRootItem(),main_module_path)
                self.tree_ctrl.SetItemImage(item,self.FolderIdx,wx.TreeItemIcon_Normal)
        dlg.Destroy()
        
    def RemovePath(self,event):
        item = self.tree_ctrl.GetSelection()
        if item is None or not item.IsOk():
            return
        self.tree_ctrl.Delete(item)
        
    def AddNewPath(self,event):
        dlg = ProjectDialog.ProjectFolderPathDialog(self,-1,_("Select Internal Path"),self.current_project_document.GetModel())
        if dlg.ShowModal() == wx.ID_OK:
            selected_path = dlg.selected_path
            if selected_path is not None:
                selected_path = os.path.join(PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE) , selected_path)
            else:
                selected_path = PythonVariables.FormatVariableName(PythonVariables.PROJECT_DIR_VARIABLE)
            if self.CheckPathExist(selected_path):
                wx.MessageBox(_("Path already exist"),_("Add Path"),wx.OK,self)
            else:
                item = self.tree_ctrl.AppendItem(self.tree_ctrl.GetRootItem(), selected_path)
                self.tree_ctrl.SetItemImage(item,self.FolderIdx,wx.TreeItemIcon_Normal)
        dlg.Destroy()
        
    def CheckPathExist(self,path):
        items = []
        root_item = self.tree_ctrl.GetRootItem()
        (item, cookie) = self.tree_ctrl.GetFirstChild(root_item)
        while item:
            items.append(item)
            (item, cookie) = self.tree_ctrl.GetNextChild(root_item, cookie)
        
        for item in items:
            if parserutils.ComparePath(self.tree_ctrl.GetItemText(item),path):
                return True
        return False
        
    def GetPythonPathList(self,use_raw_path=False):
        python_path_list = []
        root_item = self.tree_ctrl.GetRootItem()
        (item, cookie) = self.tree_ctrl.GetFirstChild(root_item)
        while item:
            text = self.tree_ctrl.GetItemText(item)
            if use_raw_path:
                python_path_list.append(text)
            else:
                python_variable_manager = PythonVariables.ProjectVariablesManager(self.current_project_document)
                path = python_variable_manager.EvalulateValue(text)
                python_path_list.append(str(path))
            (item, cookie) = self.tree_ctrl.GetNextChild(root_item, cookie)
        return python_path_list

class ExternalPathPage(wx.Panel,PythonPathMixin.BasePythonPathPanel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.InitUI(True)
        self.tree_ctrl.AddRoot("ExternalPathList")
        self.AppendPathPath()
        
    def AppendPathPath(self):
        path_str = utils.ProfileGet(self.GetParent().GetParent().ProjectDocument.GetKey() + "/ExternalPath","[]")
        try:
            python_path_list = eval(path_str)
        except:
            python_path_list = []
        for path in python_path_list:
            item = self.tree_ctrl.AppendItem(self.tree_ctrl.GetRootItem(), path)
            self.tree_ctrl.SetItemImage(item,self.LibraryIconIdx,wx.TreeItemIcon_Normal)
        
    def GetPythonPathList(self):
        python_path_list = self.GetPathList()
        return python_path_list

class EnvironmentPage(wx.Panel,EnvironmentMixin.BaseEnvironmentUI):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.InitUI()
        self.LoadEnviron()
        self.UpdateUI(None)
        
    def LoadEnviron(self):
        environ_str = utils.ProfileGet(self.GetParent().GetParent().ProjectDocument.GetKey() + "/Environment","{}")
        try:
            environ = eval(environ_str)
        except:
            environ = {}
        for env in environ:
            self.dvlc.AppendItem([env,environ[env]])

class PythonPathPanel(BasePanel.BasePanel):
    def __init__(self,filePropertiesService,parent,dlg_id,size,selected_item):
        BasePanel.BasePanel.__init__(self,filePropertiesService, parent, dlg_id,size,selected_item)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        nb = wx.Notebook(self,-1,size = (-1,350))
        iconList = wx.ImageList(16, 16, 3)
        internal_path_icon = images.load_icon("openpath.gif")
        InternalPathIconIndex = iconList.AddIcon(internal_path_icon)
        external_path_icon = images.load_icon("jar_l_obj.gif")
        ExternalPathIconIndex = iconList.AddIcon(external_path_icon)
        environment_icon = images.load_icon("environment.png")
        EnvironmentIconIndex = iconList.AddIcon(environment_icon)
        nb.AssignImageList(iconList)
        
        pythonpath_StaticText = wx.StaticText(self, -1, _("The final PYTHONPATH used for a launch is composed of paths defined here,joined with the paths defined by the selected interpreter.\n"))
        box_sizer.Add(pythonpath_StaticText,0,flag=wx.LEFT|wx.TOP,border=SPACE)
        
        count = nb.GetPageCount()
        self.internal_path_panel = InternalPathPage(nb,self.current_project_document)
        nb.AddPage(self.internal_path_panel, _("Internal Path"))
        nb.SetPageImage(count,InternalPathIconIndex)
        count = nb.GetPageCount()
        self.external_path_panel = ExternalPathPage(nb)
        nb.AddPage(self.external_path_panel, _("External Path"))
        nb.SetPageImage(count,ExternalPathIconIndex)
        count = nb.GetPageCount()
        self.environment_panel = EnvironmentPage(nb)
        nb.AddPage(self.environment_panel, _("Environment"))
        nb.SetPageImage(count,EnvironmentIconIndex)
        box_sizer.Add(nb, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, SPACE)
        self.SetSizer(box_sizer)
        #should use Layout ,could not use Fit method
        self.Layout()
        
    def OnOK(self,optionsDialog):
        
        internal_path_list = self.internal_path_panel.GetPythonPathList(True)
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/InternalPath",internal_path_list.__repr__())
            
        external_path_list = self.external_path_panel.GetPythonPathList()
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/ExternalPath",external_path_list.__repr__())
            
        environment_list = self.environment_panel.GetEnviron()
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/Environment",environment_list.__repr__())

        return True

    def GetPythonPathList(self):
        python_path_list = self.internal_path_panel.GetPythonPathList()
        python_path_list.extend(self.external_path_panel.GetPythonPathList())
        return python_path_list