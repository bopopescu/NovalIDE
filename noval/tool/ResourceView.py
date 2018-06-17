import noval.util.sysutils as sysutils
import os
from noval.tool import Singleton
import wx
import noval.util.strutils as strutils
import noval.util.fileutils as fileutils
from consts import _,ERROR_OK


REFRESH__PATH_ID = wx.NewId()
OPEN_DIR_PATH_ID = wx.NewId()
OPEN_CMD_PATH_ID = wx.NewId()
COPY_FULLPATH_ID = wx.NewId()

if sysutils.isWindows():
    from win32com.shell import shell, shellcon
    
    def GetDriveDisplayName(path):
        return shell.SHGetFileInfo(path, 0, shellcon.SHGFI_DISPLAYNAME)[1][3]
        
    def GetRoots():
        roots = []
        import ctypes
        import os
        for i in range(65,91):
            vol = chr(i) + ':'
            if os.path.isdir(vol):
                roots.append([GetDriveDisplayName(vol),wx.ArtProvider.GetBitmap(wx.ART_HARDDISK,wx.ART_CMN_DIALOG,(16,16)),vol])
        return roots
else:
    def GetRoots():
        roots = []
        home_dir = wx.GetHomeDir()
        folder_bmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN,wx.ART_CMN_DIALOG,(16,16))
        roots.append([_("Home directory"),folder_bmp,home_dir])
        desktop_dir = home_dir + "/Desktop"
        roots.append([_("Desktop"),folder_bmp,desktop_dir])
        roots.append(["/",wx.ArtProvider.GetBitmap(wx.ART_HARDDISK,wx.ART_CMN_DIALOG,(16,16)),"/"])
        return roots
        
class ResourceTreeCtrl(wx.TreeCtrl):
    
    def __init__(self, parent, id, style):
        wx.TreeCtrl.__init__(self, parent, id, style = style)
        iconList = wx.ImageList(16, 16, -1)
        wx.EVT_TREE_ITEM_ACTIVATED(self,self.GetId(),self.ExpandDir)
        wx.EVT_TREE_ITEM_EXPANDING(self,self.GetId(), self.ExpandDir)
        
        wx.EVT_RIGHT_DOWN(self, self.OnRightClick)

        folder_bmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER,wx.ART_CMN_DIALOG,(16,16))
        self._folderClosedIconIndex = iconList.Add(folder_bmp)

        folder_open_bmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN,wx.ART_CMN_DIALOG,(16,16))
        self._folderOpenIconIndex = iconList.Add(folder_open_bmp)

        file_bmp = wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE,wx.ART_CMN_DIALOG,(16,16))
        self._fileIconIndex = iconList.Add(file_bmp)
        exe_bmp = wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE,wx.ART_CMN_DIALOG,(16,16))
        self._exeIconIndex = iconList.Add(exe_bmp)
        self._fileIconIndexLookup = {}
        self.AssignImageList(iconList)
        
    def OnRightClick(self, event):
        
        item = self.GetSelection()
        item_type,item_path = self.GetPyData(item)
        menu = wx.Menu()
        if item_type == ResourceView.DIRECTORY_RES_TYPE:
            menu.Append(REFRESH__PATH_ID, _("&Refresh"))
            wx.EVT_MENU(self, REFRESH__PATH_ID, self.ProcessEvent)
        menu.Append(OPEN_CMD_PATH_ID, _("Open Command Prompt here..."))
        wx.EVT_MENU(self, OPEN_CMD_PATH_ID, self.ProcessEvent)
        menu.Append(OPEN_DIR_PATH_ID, _("Open Path in Explorer"))
        wx.EVT_MENU(self, OPEN_DIR_PATH_ID, self.ProcessEvent)
        
        menu.Append(COPY_FULLPATH_ID, _("Copy Full Path"))
        wx.EVT_MENU(self, COPY_FULLPATH_ID, self.ProcessEvent)
        self.PopupMenu(menu, wx.Point(event.GetX(), event.GetY()))
        menu.Destroy()
            
    def ProcessEvent(self, event):
        id = event.GetId()
        item = self.GetSelection()
        item_type,item_path = self.GetPyData(item)
        if id == OPEN_CMD_PATH_ID:
            if item_type == ResourceView.DIRECTORY_RES_TYPE:
                filePath = item_path
            else:
                filePath = os.path.dirname(item_path)
            err_code,msg = fileutils.open_path_in_terminator(filePath.decode('gbk'))
            if err_code != ERROR_OK:
                wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
        elif id == OPEN_DIR_PATH_ID:
            err_code,msg = fileutils.open_file_directory(item_path)
            if err_code != ERROR_OK:
                wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
        elif id == COPY_FULLPATH_ID:
            sysutils.CopyToClipboard(item_path)
        elif id == REFRESH__PATH_ID:
            self.Freeze()
            self.DeleteChildren(item)
            ResourceView(self.GetParent()).LoadDir(item,item_path)
            if self.GetChildrenCount(item) > 0:
                self.SetItemHasChildren(item, True)
            self.Thaw()
            
    def ExpandDir(self, event):
        item = event.GetItem()
        ResourceView(self).OpenSelection(item)
        event.Skip()
        
    def GetIconIndex(self,ext):
        if ext == "":
            return self._fileIconIndex
        elif ext.lower() == "exe":
            return self._exeIconIndex
        if ext in self._fileIconIndexLookup:
            return self._fileIconIndexLookup[ext]
        return None
        
    def AddLookupIcon(self,ext,hicon):
        if hicon is None:
            return self._fileIconIndex
        index = self.ImageList.AddIcon(hicon)
        if -1 == index:
            return self._fileIconIndex
        self._fileIconIndexLookup[ext] = index
        return index
    
class ResourceView(object):
    
    DIRECTORY_RES_TYPE = 0
    FILE_RES_TYPE = 1
    __metaclass__ = Singleton.SingletonNew
    def __init__(self,view):
        self._view = view
        self._is_load = False
        self._select_index = 0
        
    @property
    def IsLoad(self):
        return self._is_load
        
    @property
    def SelectIndex(self):
        return self._select_index
        
    @SelectIndex.setter
    def SelectIndex(self,select_index):
        self._select_index = select_index
        
    def LoadRoots(self):
        roots = GetRoots()
        self._view._projectChoice.Clear()
        for root in roots:
            self._view._projectChoice.Append(root[0],root[1],root[2])
        self._view._projectChoice.SetSelection(self._select_index)

    def LoadResource(self):
        name = self._view._projectChoice.GetClientData(self._select_index)
        self.LoadRoot(name)
        self._is_load = True

    def SetRootDir(self,directory):
        if not os.path.isdir(directory):
            raise Exception("%s is not a valid directory" % directory)
        
        self._view.dir_ctrl.DeleteChildren(self._view.dir_ctrl.GetRootItem())
        self._view.dir_ctrl.DeleteAllItems()
        
        # add directory as root
        root = self._view.dir_ctrl.AddRoot(directory.replace(":",""))
        if sysutils.isWindows():
            directory += os.sep
        self.LoadDir(root, directory)
            
    def LoadRoot(self,root):
        self.SetRootDir(root)
    
    def LoadDir(self, item, directory):

        # check if directory exists and is a directory
        if not os.path.isdir(directory):
            raise Exception("%s is not a valid directory" % directory)

        # check if node already has children
        if self._view.dir_ctrl.GetChildrenCount(item) == 0:
            # get files in directory
            files = os.listdir(directory)
            # add nodes to tree
            file_count = 0
            for f in files:
                file_count += 1
                # process the file extension to build image list
                # if directory, tell tree it has children
                file_path = os.path.join(directory, f)
                if fileutils.is_file_hiden(file_path):
                    continue
                if os.path.isdir(file_path):
                    child = self._view.dir_ctrl.AppendItem(item, f,-1)
                    self._view.dir_ctrl.SetItemImage(child, \
                                     self._view.dir_ctrl._folderClosedIconIndex, wx.TreeItemIcon_Normal)
                    self._view.dir_ctrl.SetItemImage(child, \
                                     self._view.dir_ctrl._folderOpenIconIndex, wx.TreeItemIcon_Expanded)
                    self._view.dir_ctrl.SetItemHasChildren(child, True)
                    # save item path for expanding later
                    self._view.dir_ctrl.SetPyData(child, (self.DIRECTORY_RES_TYPE,file_path))
                else:
                    #this is a file type 
                    child = self._view.dir_ctrl.AppendItem(item, f,-1)
                    ext = strutils.GetFileExt(file_path)
                    iconIndex = self._view.dir_ctrl.GetIconIndex(ext)
                    if not iconIndex:
                        ft = wx.TheMimeTypesManager.GetFileTypeFromExtension(ext)
                        if ft is None:
                            iconIndex = self._view.dir_ctrl.GetIconIndex("")
                        else:
                            iconIndex = self._view.dir_ctrl.AddLookupIcon(ext,ft.GetIcon())
                            
                    self._view.dir_ctrl.SetItemImage(child, iconIndex, wx.TreeItemIcon_Normal)
                    self._view.dir_ctrl.SetItemImage(child, iconIndex, wx.TreeItemIcon_Expanded)
                    self._view.dir_ctrl.SetPyData(child, (self.FILE_RES_TYPE,file_path))
                    
            if file_count == 0:
                self._view.dir_ctrl.SetItemHasChildren(item, False)
                    
    def OpenSelection(self,item):
        item_type,item_path = self._view.dir_ctrl.GetPyData(item)
        if item_type == self.DIRECTORY_RES_TYPE:
            try:
                self.LoadDir(item,item_path)
                ##self._view.dir_ctrl.Expand(item)
            except Exception,e:
                wx.MessageBox(unicode(e),_("Open Directory Error"))
            self._view.dir_ctrl.SelectItem(item)
        else:
            if not os.path.exists(item_path):
                wx.MessageBox(_("The file '%s' doesn't exist and couldn't be opened!") % item_path.decode('gbk'),style = wx.OK | wx.ICON_ERROR)
                return
            ext = strutils.GetFileExt(item_path)
            if sysutils.IsExtSupportable(ext):
                wx.GetApp().GotoView(item_path.decode('gbk'),0)
            else:
                try:
                    fileutils.start_file(item_path)
                except:
                    pass
            