# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        editor.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-02-15
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import _,GetApp
import noval.python.project.model as pyprojectlib
from noval.project.baseviewer import *
import tkinter as tk
from tkinter import ttk
import noval.consts as consts
import noval.ttkwidgets.linklabel as linklabel
import noval.python.interpreter.InterpreterManager as interpretermanager
from noval.python.project.runconfig import PythonProjectConfiguration,PythonRunconfig
import os
import noval.python.parser.utils as dirutils
import noval.project.command as command
from noval.project.templatemanager import ProjectTemplateManager
import noval.iface as iface
import noval.plugin as plugin
import noval.ui_common as ui_common

class PythonProjectDocument(ProjectDocument):

    #pyc和pyo二进制文件类型禁止添加到项目中
    BIN_FILE_EXTS = ['pyc','pyo']
    def __init__(self, model=None):
        ProjectDocument.__init__(self,model)
        
    @staticmethod
    def GetProjectModel():
        return pyprojectlib.PythonProject()

    def GetRunConfiguration(self,start_up_file):
        file_key = self.GetFileKey(start_up_file)
        run_configuration_name = utils.profile_get(file_key + "/RunConfigurationName","")
        return run_configuration_name
        
    def GetRunParameter(self,start_up_file):
        #check the run configuration first,if exist,use run configuration
        run_configuration_name = self.GetRunConfiguration(start_up_file)
        if run_configuration_name:
            file_configuration = RunConfiguration.FileConfiguration(self,start_up_file)
            run_configuration = file_configuration.LoadConfiguration(run_configuration_name)
            try:
                return run_configuration.GetRunParameter()
            except PromptErrorException as e:
                wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR)
                return None
            

        use_argument = utils.profile_get_int(self.GetFileKey(start_up_file,"UseArgument"),True)
        if use_argument:
            initialArgs = utils.profile_get(self.GetFileKey(start_up_file,"RunArguments"),"")
        else:
            initialArgs = ''
        python_path = utils.profile_get(self.GetFileKey(start_up_file,"PythonPath"),"")
        startIn = utils.profile_get(self.GetFileKey(start_up_file,"RunStartIn"),"")
        if startIn == '':
            startIn = os.path.dirname(self.GetFilename())
        env = {}
        paths = set()
        path_post_end = utils.profile_get_int(self.GetKey("PythonPathPostpend"), True)
        if path_post_end:
            paths.add(str(os.path.dirname(self.GetFilename())))
        #should avoid environment contain unicode string,such as u'xxx'
        if len(python_path) > 0:
            paths.add(str(python_path))
        env[consts.PYTHON_PATH_NAME] = os.pathsep.join(list(paths))
        return PythonRunconfig(GetApp().GetCurrentInterpreter(),start_up_file.filePath,initialArgs,env,startIn,project=self)
        

class PythonProjectTemplate(ProjectTemplate):
    
    def CreateDocument(self, path, flags):
        return ProjectTemplate.CreateDocument(self,path,flags,wizard_cls=NewPythonProjectWizard)

class NewPythonProjectWizard(NewProjectWizard):
    def LoadDefaultProjectTemplates(self):
        pass
        
class PythonProjectNameLocationPage(ProjectNameLocationPage):
    def __init__(self,master):
        ProjectNameLocationPage.__init__(self,master,add_bottom_page=False)
        
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=4, sticky="nsew")
        self.pythonpath_chkvar = tk.IntVar(value=PythonProjectConfiguration.PROJECT_SRC_PATH_ADD_TO_PYTHONPATH)
        self.add_src_radiobutton = ttk.Radiobutton(
            sizer_frame, text=_("Create %s Folder And Add it to the PYTHONPATH") % PythonProjectConfiguration.DEFAULT_PROJECT_SRC_PATH, variable=self.pythonpath_chkvar,\
                        value=PythonProjectConfiguration.PROJECT_SRC_PATH_ADD_TO_PYTHONPATH
        )
        self.add_src_radiobutton.pack(fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.add_project_path_radiobutton = ttk.Radiobutton(
            sizer_frame, text=_("Add Project Directory to the PYTHONPATH"), variable=self.pythonpath_chkvar,\
                        value=PythonProjectConfiguration.PROJECT_PATH_ADD_TO_PYTHONPATH
        )
        self.add_project_path_radiobutton.pack(fill="x")
        
        self.configure_no_path_radiobutton = ttk.Radiobutton(
            sizer_frame, text=_("Don't Configure PYTHONPATH(later manually configure it)"), variable=self.pythonpath_chkvar,\
                        value=PythonProjectConfiguration.NONE_PATH_ADD_TO_PYTHONPATH
        )
        self.configure_no_path_radiobutton.pack(fill="x")

        ProjectNameLocationPage.CreateBottomPage(self,chk_box_row=5)
        
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=7, sticky="nsew")
        separator = ttk.Separator(sizer_frame, orient = tk.HORIZONTAL)
        separator.pack(side=tk.LEFT,fill="x",expand=1)

    def CreateTopPage(self):
        sizer_frame = ProjectNameLocationPage.CreateTopPage(self)
        self.interpreter_label = ttk.Label(sizer_frame, text=_("Interpreter:"))
        self.interpreter_label.grid(column=0, row=2, sticky="nsew")
        self.interpreter_entry_var = tk.StringVar()
        self.interpreter_combo = ttk.Combobox(sizer_frame, textvariable=self.interpreter_entry_var)
        names = interpretermanager.InterpreterManager().GetInterpreterNames()
        self.interpreter_combo.grid(column=1, row=2, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X/2,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.interpreter_combo.state(['readonly'])
        self.interpreter_combo['values'] = names
        self.interpreter_combo.current(0)
            
        link_label = linklabel.LinkLabel(sizer_frame,text=_("Configuration"),normal_color='royal blue',hover_color='blue',clicked_color='purple')
        link_label.bind("<Button-1>", self.OpenInterpreterConfiguration)
        link_label.grid(column=2, row=2, sticky="nsew",padx=(consts.DEFAUT_CONTRL_PAD_X/2,0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        

    def OpenInterpreterConfiguration(self,*args):
        ui_common.ShowInterpreterConfigurationPage()
        
    def Finish(self):
        if not ProjectNameLocationPage.Finish(self):
            return False
        dirName = self.GetProjectLocation()
        #创建Src文件夹
        if self.pythonpath_chkvar.get() == PythonProjectConfiguration.PROJECT_SRC_PATH_ADD_TO_PYTHONPATH:
            project_src_path = os.path.join(dirName,PythonProjectConfiguration.DEFAULT_PROJECT_SRC_PATH)
            if not os.path.exists(project_src_path):
                dirutils.MakeDirs(project_src_path)
            
        if self._project_configuration.PythonpathMode == PythonProjectConfiguration.PROJECT_SRC_PATH_ADD_TO_PYTHONPATH:
            view = GetApp().MainFrame.GetProjectView().GetView()
            doc = view.GetDocument()
            doc.GetCommandProcessor().Submit(command.ProjectAddFolderCommand(view, doc, PythonProjectConfiguration.DEFAULT_PROJECT_SRC_PATH))
        
        return True
        
    def GetPojectConfiguration(self):
        return PythonProjectConfiguration(self.name_var.get(),self.dir_entry_var.get(),\
                                          self.interpreter_entry_var.get(),self.project_dir_chkvar.get(),self.pythonpath_chkvar.get())

class PythonProjectView(ProjectView):
    
    PACKAGE_INIT_FILE = "__init__.py"
   
    def __init__(self, frame):
        ProjectView.__init__(self,frame)
        
    def AddFolderItem(self,document,folderPath):
        destfolderPath = os.path.join(document.GetModel().homeDir,folderPath)
        packageFilePath = os.path.join(destfolderPath,self.PACKAGE_INIT_FILE)
        is_package = False
        #判断文件夹下__init__.py文件是否存在,如果存在则为包文件夹
        if os.path.exists(packageFilePath):
            is_package = True
        #普通文件夹
        if not is_package:
            return ProjectView.AddFolderItem(self,document,folderPath)
        #包文件夹
        return self._treeCtrl.AddPackageFolder(folderPath)
        

    def OnAddPackageFolder(self,event):
        if self.GetDocument():
            items = self._treeCtrl.GetSelections()
            if items:
                item = items[0]
                if self._IsItemFile(item):
                    item = self._treeCtrl.GetItemParent(item)
                    
                folderDir = self._GetItemFolderPath(item)
            else:
                folderDir = ""
                
            if folderDir:
                folderDir += "/"
            folderPath = "%sPackage" % folderDir
            i = 1
            while self._treeCtrl.FindFolder(folderPath):
                i += 1
                folderPath = "%sPackage%s" % (folderDir, i)
            projectdir = self.GetDocument().GetModel().homeDir
            destpackagePath = os.path.join(projectdir,folderPath)
            try:
                os.mkdir(destpackagePath)
            except Exception as e:
                wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)
                return
            self.GetDocument().GetCommandProcessor().Submit(ProjectAddFolderCommand(self, self.GetDocument(), folderPath,True))
            destpackageFile = os.path.join(destpackagePath,self.PACKAGE_INIT_FILE)
            with open(destpackageFile,"w") as f:
                self.GetDocument().GetCommandProcessor().Submit(ProjectAddFilesCommand(self.GetDocument(),[destpackageFile],folderPath))
            self._treeCtrl.UnselectAll()
            item = self._treeCtrl.FindFolder(folderPath)
            self._treeCtrl.SelectItem(item)
            self._treeCtrl.EnsureVisible(item)
            self.OnRename()
        
class DefaultProjectTemplateLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        ProjectTemplateManager().AddProjectTemplate(_("Gernal"),_("Empty Project"),[PythonProjectNameLocationPage,])
        ProjectTemplateManager().AddProjectTemplate(_("Gernal"),_("New Project From Existing Code"),\
                    ["noval.python.project.viewer.PythonProjectNameLocationPage",("noval.project.importfiles.ImportfilesPage",{'rejects':PythonProjectDocument.BIN_FILE_EXTS})])

consts.DEFAULT_PLUGINS += ('noval.python.project.viewer.DefaultProjectTemplateLoader',)