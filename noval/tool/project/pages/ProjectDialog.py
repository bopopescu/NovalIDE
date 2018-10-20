import wx
from noval.tool.consts import SPACE,HALF_SPACE,_
import noval.tool.images as images
import os
import noval.util.fileutils as fileutils
import noval.tool.syntax.syntax as syntax
import noval.tool.syntax.lang as lang
import noval.util.strutils as strutils

class ProjectFolderPathDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,project_model):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        self._current_project = project_model
        rootPath = project_model.homeDir
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        self._treeCtrl = wx.TreeCtrl(self,size=(300,500),style=wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE)
        iconList = wx.ImageList(16, 16, initialCount = 5)
        folder_bmp = images.load("packagefolder_obj.gif")
        self.FolderIdx = iconList.Add(folder_bmp)
        self._treeCtrl.AssignImageList(iconList)
        boxsizer.Add(self._treeCtrl, 1, wx.EXPAND|wx.BOTTOM, SPACE)
        root_item = self._treeCtrl.AddRoot(os.path.basename(rootPath))
        self._treeCtrl.SetPyData(root_item,rootPath)
        self._treeCtrl.SetItemImage(root_item,self.FolderIdx,wx.TreeItemIcon_Normal)
        self.ListDirItem(root_item,rootPath)
        self._treeCtrl.Expand(root_item)

        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP,SPACE)

        self.SetSizer(boxsizer)
        self.Fit()

    def ListDirItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isdir(file_path) and not fileutils.is_file_hiden(file_path):
                item = self._treeCtrl.AppendItem(parent_item, f)
                self._treeCtrl.SetItemImage(item,self.FolderIdx,wx.TreeItemIcon_Normal)
                self.ListDirItem(item,file_path)
                self._treeCtrl.SetPyData(item,file_path)

    def OnOKClick(self,event):
        path = fileutils.getRelativePath(self._treeCtrl.\
                    GetPyData(self._treeCtrl.GetSelection()),\
                            self._current_project.homeDir)
        self.selected_path = path
        self.EndModal(wx.ID_OK)

class SelectModuleFileDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,project_model,is_startup=False,filters=[]):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        self.module_file = None
        if filters == []:
            filters = syntax.LexerManager().GetLexer(lang.ID_LANG_PYTHON).Exts
        self.filters = filters
        self.is_startup = is_startup
        self._current_project = project_model
        rootPath = project_model.homeDir
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        self._treeCtrl = wx.TreeCtrl(self,size=(300,500),style=wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE)
        wx.EVT_TREE_ITEM_ACTIVATED(self._treeCtrl, self._treeCtrl.GetId(), self.OnOKClick)
        iconList = wx.ImageList(16, 16, initialCount = 3)
        folder_bmp = images.load("packagefolder_obj.gif")
        self.FolderIdx = iconList.Add(folder_bmp)

        python_file_bmp = images.load("python_module.png")
        self.PythonFileIdx = iconList.Add(python_file_bmp)
        
        zip_file_bmp = images.load("project/zip.png")
        self.ZipFileIdx = iconList.Add(zip_file_bmp)

        self._treeCtrl.AssignImageList(iconList)
        boxsizer.Add(self._treeCtrl, 1, wx.EXPAND|wx.BOTTOM, SPACE)
        root_item = self._treeCtrl.AddRoot(os.path.basename(rootPath))
        self._treeCtrl.SetItemImage(root_item,self.FolderIdx,wx.TreeItemIcon_Normal)
        self.ListDirItem(root_item,rootPath)
        self._treeCtrl.Expand(root_item)

        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP,SPACE)

        self.SetSizer(boxsizer)
        self.Fit()

    def ListDirItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isfile(file_path) and self.IsFileFiltered(file_path):
                pj_file = self._current_project.FindFile(file_path)
                if pj_file:
                    item = self._treeCtrl.AppendItem(parent_item, f)
                    if fileutils.is_python_file(file_path):
                        self._treeCtrl.SetItemImage(item,self.PythonFileIdx,wx.TreeItemIcon_Normal)
                    else:
                        self._treeCtrl.SetItemImage(item,self.ZipFileIdx,wx.TreeItemIcon_Normal)
                    self._treeCtrl.SetPyData(item,pj_file)
                    if pj_file.IsStartup and self.is_startup:
                        self._treeCtrl.SetItemBold(item)
            elif os.path.isdir(file_path) and not fileutils.is_file_hiden(file_path):
                item = self._treeCtrl.AppendItem(parent_item, f)
                self._treeCtrl.SetItemImage(item,self.FolderIdx,wx.TreeItemIcon_Normal)
                self.ListDirItem(item,file_path)

    def OnOKClick(self,event):
        pj_file = self._treeCtrl.GetPyData(self._treeCtrl.GetSelection())
        if pj_file is None:
            wx.MessageBox(_("Please select a file"))
            return
        self.module_file = pj_file
        self.EndModal(wx.ID_OK)
        
    def IsFileFiltered(self,file_path):
        file_ext = strutils.GetFileExt(file_path)
        return file_ext in self.filters