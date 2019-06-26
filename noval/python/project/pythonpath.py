from noval import _,NewId
import tkinter as tk
from tkinter import ttk
import os
import noval.iface as iface
import noval.plugin as plugin
import noval.consts as consts
import noval.python.parser.utils as parserutils
import noval.util.apputils as sysutils
#import noval.tool.project.PythonVariables as PythonVariables
#import ProjectDialog
import noval.util.utils as utils
import noval.ui_utils as ui_utils
import noval.python.interpreter.pythonpathmixin as pythonpathmixin
#import noval.tool.project.RunConfiguration as RunConfiguration
import noval.ui_utils as ui_utils
import noval.project.property as projectproperty
import noval.imageutils as imageutils
import noval.ttkwidgets.treeviewframe as treeviewframe

class InternalPathPage(ttk.Frame):
    
    ID_NEW_INTERNAL_ZIP = NewId()
    ID_NEW_INTERNAL_EGG = NewId()
    ID_NEW_INTERNAL_WHEEL = NewId()
    def __init__(self,parent,project_document):
        ttk.Frame.__init__(self, parent)
        self.current_project_document = project_document
        
        row = ttk.Frame(self)
        self.treeview = treeviewframe.TreeViewFrame(row)
        self.treeview.tree["show"] = ("tree",)
        self.treeview.pack(side=tk.LEFT,fill="both",expand=1)
        self.folder_bmp = imageutils.load_image("","packagefolder_obj.gif")
     #   self.treeview.tree.bind("<3>", self.OnRightClick, True)
        right_frame = ttk.Frame(row)
        self.add_path_btn = ttk.Button(right_frame, text=_("Add Path.."),command=self.AddNewPath)
        self.add_path_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))

        self.remove_path_btn = ttk.Button(right_frame, text=_("Remove Path..."),command=self.RemovePath)
        self.remove_path_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        
        self.add_file_btn = ttk.Button(right_frame,text=_("Add File..."),command=self.AddNewPath)
        self.add_file_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        
        right_frame.pack(side=tk.LEFT,fill="y")
        row.pack(fill="both",expand=1)
        
        row = ttk.Frame(self)
        self._useProjectPathCheckVar = tk.IntVar(value=True)
        ttk.Checkbutton(row, text= _("Append project root path to PYTHONPATH"),variable=self._useProjectPathCheckVar).pack(fill="x",side=tk.LEFT)
        row.pack(fill="x")
        #self._useProjectPathCheckBox.SetValue(RunConfiguration.ProjectConfiguration.IsAppendProjectPath(self.current_project_document.GetKey()))
       # self.AppendPathPath()

    def AppendPathPath(self):
        python_path_list = RunConfiguration.ProjectConfiguration.LoadProjectInternalPath(self.GetParent().GetParent().ProjectDocument.GetKey())
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
        ###if self._useProjectPathCheckBox.GetValue():
           ### python_path_list.append(self.current_project_document.GetPath())
        return python_path_list

class ExternalPathPage(ttk.Frame,pythonpathmixin.PythonpathMixin):
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        self.InitUI(True)
       # self.tree_ctrl.AddRoot("ExternalPathList")
       # self.AppendPathPath()
        
    def AppendPathPath(self):
        python_path_list = RunConfiguration.ProjectConfiguration.LoadProjectExternalPath(self.GetParent().GetParent().ProjectDocument.GetKey())
        for path in python_path_list:
            item = self.tree_ctrl.AppendItem(self.tree_ctrl.GetRootItem(), path)
            self.tree_ctrl.SetItemImage(item,self.LibraryIconIdx,wx.TreeItemIcon_Normal)
        
    def GetPythonPathList(self):
        python_path_list = self.GetPathList()
        return python_path_list

class EnvironmentPage(ui_utils.BaseEnvironmentUI):
    def __init__(self,parent):
        ui_utils.BaseEnvironmentUI.__init__(self, parent)
      #  self.LoadEnviron()
     #   self.UpdateUI(None)
        
    def LoadEnviron(self):
        environ = RunConfiguration.ProjectConfiguration.LoadProjectEnviron(self.GetParent().GetParent().ProjectDocument.GetKey())
        for env in environ:
            self.dvlc.AppendItem([env,environ[env]])

class PythonPathPanel(ui_utils.BaseConfigurationPanel):
    def __init__(self,parent,item,current_project):
        ui_utils.BaseConfigurationPanel.__init__(self,parent)
        self.current_project_document = current_project
        nb = ttk.Notebook(self)

        self.internal_path_icon = imageutils.load_image("","project/python/openpath.gif")
        self.external_path_icon = imageutils.load_image("","python/jar_l_obj.gif")
        self.environment_icon = imageutils.load_image("","environment.png")

    
        pythonpath_StaticText = ttk.Label(self,text=_("The final PYTHONPATH used for a launch is composed of paths defined here,joined with the paths defined by the selected interpreter.\n"))
        pythonpath_StaticText.pack(fill="x")
        
        self.internal_path_panel = InternalPathPage(nb,self.current_project_document)
        nb.add(self.internal_path_panel, text=_("Internal Path"),image=self.internal_path_icon,compound=tk.LEFT)

        self.external_path_panel = ExternalPathPage(nb)
        nb.add(self.external_path_panel, text=_("External Path"),image=self.external_path_icon,compound=tk.LEFT)

        self.environment_panel = EnvironmentPage(nb)
        nb.add(self.environment_panel, text=_("Environment"),image=self.environment_icon,compound=tk.LEFT)
        nb.pack(fill="both",expand=1)
        
    def OnOK(self,optionsDialog):
        
        internal_path_list = self.internal_path_panel.GetPythonPathList(True)
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/InternalPath",internal_path_list.__repr__())
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/AppendProjectPath",int(self.internal_path_panel._useProjectPathCheckBox.GetValue()))
            
        external_path_list = self.external_path_panel.GetPythonPathList()
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/ExternalPath",external_path_list.__repr__())
            
        environment_list = self.environment_panel.GetEnviron()
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/Environment",environment_list.__repr__())

        return True

    def GetPythonPathList(self):
        python_path_list = self.internal_path_panel.GetPythonPathList()
        python_path_list.extend(self.external_path_panel.GetPythonPathList())
        return python_path_list
        


class PythonpathPageLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        projectproperty.PropertiesService().AddProjectOptionsPanel("PythonPath",PythonPathPanel)

consts.DEFAULT_PLUGINS += ('noval.python.project.pythonpath.PythonpathPageLoader',)
