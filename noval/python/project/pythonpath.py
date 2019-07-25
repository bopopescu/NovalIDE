from noval import _,NewId
import tkinter as tk
from tkinter import ttk,messagebox
import os
import noval.consts as consts
import noval.python.parser.utils as parserutils
import noval.util.apputils as sysutils
import noval.project.variables as variablesutils
import noval.util.utils as utils
import noval.ui_utils as ui_utils
import noval.python.interpreter.pythonpathmixin as pythonpathmixin
import noval.python.project.runconfiguration as runconfiguration
import noval.project.property as projectproperty
import noval.imageutils as imageutils
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.python.pyutils as pyutils
import noval.constants as constants

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
        
        self.add_file_btn = ttk.Button(right_frame,text=_("Add File..."),command=self.AddNewFilePath)
        self.add_file_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        
        right_frame.pack(side=tk.LEFT,fill="y")
        row.pack(fill="both",expand=1)
        
        row = ttk.Frame(self)
        self._useProjectPathCheckVar = tk.IntVar(value=True)
        ttk.Checkbutton(row, text= _("Append project root path to PYTHONPATH"),variable=self._useProjectPathCheckVar).pack(fill="x",side=tk.LEFT)
        row.pack(fill="x")
        self._useProjectPathCheckVar.set(runconfiguration.ProjectConfiguration.IsAppendProjectPath(self.current_project_document.GetKey()))
        self.AppendPathPath()

    def AppendPathPath(self):
        python_path_list = runconfiguration.ProjectConfiguration.LoadProjectInternalPath(self.current_project_document.GetKey())
        for path in python_path_list:
            self.treeview.tree.insert('',"end",text=path,image=self.folder_bmp)

    def AddNewFilePath(self):
        dlg = pyutils.SelectModuleFileDialog(self,_("Select Zip/Egg/Wheel File"),self.current_project_document.GetModel(),False,['egg','zip','whl'])
        if dlg.ShowModal() == constants.ID_OK:
            main_module_path = os.path.join(variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE) , self.current_project_document.\
                    GetModel().GetRelativePath(dlg.module_file))
            if self.CheckPathExist(main_module_path):
                messagebox.showinfo(_("Add Path"),_("Path already exist"),parent= self)
            else:
               # item = self.tree_ctrl.AppendItem(self.tree_ctrl.GetRootItem(),main_module_path)
                #self.tree_ctrl.SetItemImage(item,self.FolderIdx,wx.TreeItemIcon_Normal)
                self.treeview.tree.insert('',"end",text=main_module_path,image=self.folder_bmp)
        
    def RemovePath(self):
        selections = self.treeview.tree.selection()
        if not selections:
            return
        for item in selections:
            self.treeview.tree.delete(item)
        
    def AddNewPath(self):
        dlg = pyutils.ProjectFolderPathDialog(self,_("Select Internal Path"),self.current_project_document.GetModel())
        if dlg.ShowModal() == constants.ID_OK:
            selected_path = dlg.selected_path
            if selected_path is not None:
                selected_path = os.path.join(variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE) , selected_path)
            else:
                selected_path = variablesutils.FormatVariableName(variablesutils.PROJECT_DIR_VARIABLE)
            if self.CheckPathExist(selected_path):
                messagebox.showinfo(_("Add Path"),_("Path already exist"),parent= self)
            else:
                self.treeview.tree.insert('',"end",text=selected_path,image=self.folder_bmp)
        
    def CheckPathExist(self,path):
        items = self.treeview.tree.get_children()
        for item in items:
            if parserutils.ComparePath(self.treeview.tree.item(item,"text"),path):
                return True
        return False
        
    def GetPythonPathList(self,use_raw_path=False):
        python_path_list = []
        items = self.treeview.tree.get_children()
        for item in items:
            path = self.treeview.tree.item(item,"text")
            if use_raw_path:
                python_path_list.append(path)
            else:
                python_variable_manager = variablesutils.GetProjectVariableManager(self.current_project_document)
                path = python_variable_manager.EvalulateValue(path)
                python_path_list.append(str(path))
        return python_path_list

class ExternalPathPage(ttk.Frame,pythonpathmixin.PythonpathMixin):
    def __init__(self,parent,project_document):
        ttk.Frame.__init__(self, parent)
        self.project_document = project_document
        self.InitUI(True)
        self.AppendPathPath()
        
    def AppendPathPath(self):
        python_path_list = runconfiguration.ProjectConfiguration.LoadProjectExternalPath(self.project_document.GetKey())
        for path in python_path_list:
            self.treeview.tree.insert(self.GetRootItem(),"end",text=path,image=self.LibraryIcon)
        
    def GetPythonPathList(self):
        python_path_list = self.GetPathList()
        return python_path_list
        
    def destroy(self):
        if self.menu is not None:
            self.menu.destroy()
        self.button_menu.destroy()
        ttk.Frame.destroy(self)

class EnvironmentPage(ui_utils.BaseEnvironmentUI):
    def __init__(self,parent,project_document):
        ui_utils.BaseEnvironmentUI.__init__(self, parent)
        self.project_document = project_document
        self.LoadEnviron()
        self.UpdateUI()
        
    def LoadEnviron(self):
        environ = runconfiguration.ProjectConfiguration.LoadProjectEnviron(self.project_document.GetKey())
        for key in environ:
            self.listview.tree.insert("","end",values=(key,environ[key]))

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

        self.external_path_panel = ExternalPathPage(nb,self.current_project_document)
        nb.add(self.external_path_panel, text=_("External Path"),image=self.external_path_icon,compound=tk.LEFT)

        self.environment_panel = EnvironmentPage(nb,self.current_project_document)
        nb.add(self.environment_panel, text=_("Environment"),image=self.environment_icon,compound=tk.LEFT)
        nb.pack(fill="both",expand=1)
        
    def OnOK(self,optionsDialog):
        
        internal_path_list = self.internal_path_panel.GetPythonPathList(True)
        utils.profile_set(self.current_project_document.GetKey() + "/InternalPath",internal_path_list)
        utils.profile_set(self.current_project_document.GetKey() + "/AppendProjectPath",self.internal_path_panel._useProjectPathCheckVar.get())
            
        external_path_list = self.external_path_panel.GetPythonPathList()
        utils.profile_set(self.current_project_document.GetKey() + "/ExternalPath",external_path_list.__repr__())
            
        environment_list = self.environment_panel.GetEnviron()
        utils.profile_set(self.current_project_document.GetKey() + "/Environment",environment_list.__repr__())

        return True

    def GetPythonPathList(self):
        python_path_list = self.internal_path_panel.GetPythonPathList()
        python_path_list.extend(self.external_path_panel.GetPythonPathList())
        return python_path_list
        

