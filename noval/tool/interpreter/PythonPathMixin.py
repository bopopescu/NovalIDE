import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import wx.lib.agw.flatmenu as flatmenu
import noval.tool.images as images
import noval.util.fileutils as fileutils
import noval.util.sysutils as sysutils
import noval.parser.utils as parserutils
import locale

ID_GOTO_PATH = wx.NewId()
ID_REMOVE_PATH = wx.NewId()

class BasePythonPathPanel:
    """description of class"""

    ID_NEW_ZIP = wx.NewId()
    ID_NEW_EGG = wx.NewId()
    ID_NEW_WHEEL = wx.NewId()
    
    def InitUI(self,hide_tree_root=False):
        self.Sizer = wx.BoxSizer()
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        if not hide_tree_root:
            self.tree_ctrl = wx.TreeCtrl(self, -1, style = wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE)
        else:
            self.tree_ctrl = wx.TreeCtrl(self,size=(300,-1),style=wx.TR_NO_LINES|wx.TR_HIDE_ROOT|wx.TR_DEFAULT_STYLE)
        il = wx.ImageList(16,16,initialCount = 1)
        self.LibraryIconIdx = il.Add(images.load("library_obj.gif"))
        self.tree_ctrl.AssignImageList(il)
        wx.EVT_RIGHT_DOWN(self.tree_ctrl, self.OnRightClick)
        left_sizer.Add(self.tree_ctrl, 1,  wx.EXPAND)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.add_path_btn = wx.Button(self, -1, _("Add Path.."))
        wx.EVT_BUTTON(self.add_path_btn, -1, self.AddNewPath)
        right_sizer.Add(self.add_path_btn, 0, wx.TOP|wx.EXPAND, SPACE*3)
        
        self.add_file_btn = wx.Button(self, -1, _("Add File..."))
        wx.EVT_BUTTON(self.add_file_btn, -1, self.PopFileMenu)
        right_sizer.Add(self.add_file_btn, 0, wx.TOP|wx.EXPAND, SPACE)
        
        self.remove_path_btn = wx.Button(self, -1, _("Remove Path..."))
        wx.EVT_BUTTON(self.remove_path_btn, -1, self.RemovePath)
        right_sizer.Add(self.remove_path_btn, 0, wx.TOP|wx.EXPAND, SPACE)
        
        self.Sizer.Add(left_sizer, 1, wx.EXPAND|wx.RIGHT,HALF_SPACE)
        self.Sizer.Add(right_sizer, 0,wx.EXPAND|wx.LEFT|wx.RIGHT,HALF_SPACE)
        
        self._popUpMenu = None
       
        self.Fit()
        

    def PopFileMenu(self,event):
        
        btn = event.GetEventObject()
        # Create the popup menu
        self.CreatePopupMenu()
        # Position the menu:
        # The menu should be positioned at the bottom left corner of the button.
        btnSize = btn.GetSize()
        btnPt = btn.GetPosition()
        # Since the btnPt (button position) is in client coordinates, 
        # and the menu coordinates is relative to screen we convert
        # the coords
        # A nice feature with the Popup menu, is the ability to provide an 
        # object that we wish to handle the menu events, in this case we
        # pass 'self'
        # if we wish the menu to appear under the button, we provide its height
        if isinstance(self._popUpMenu,flatmenu.FlatMenu):
            btnPt = btn.GetParent().ClientToScreen(btnPt)
            self._popUpMenu.SetOwnerHeight(btnSize.y)
            self._popUpMenu.Popup(wx.Point(btnPt.x, btnPt.y), self)
        else:
            self.PopupMenu(self._popUpMenu, wx.Point(btnPt.x, btnPt.y+btnSize.height))
        
    def CreatePopupMenu(self):
        if not self._popUpMenu:
            if sysutils.isWindows():
                self._popUpMenu = flatmenu.FlatMenu()
                menuItem = flatmenu.FlatMenuItem(self._popUpMenu, self.ID_NEW_ZIP, _("Add Zip File"), "", wx.ITEM_NORMAL)
                self.Bind(flatmenu.EVT_FLAT_MENU_SELECTED, self.AddNewFilePath, id = self.ID_NEW_ZIP)
                self._popUpMenu.AppendItem(menuItem)
                menuItem = flatmenu.FlatMenuItem(self._popUpMenu, self.ID_NEW_EGG, _("Add Egg File"), "", wx.ITEM_NORMAL)
                self.Bind(flatmenu.EVT_FLAT_MENU_SELECTED, self.AddNewFilePath, id = self.ID_NEW_EGG)
                self._popUpMenu.AppendItem(menuItem)
                menuItem = flatmenu.FlatMenuItem(self._popUpMenu, self.ID_NEW_WHEEL, _("Add Wheel File"), "", wx.ITEM_NORMAL)
                self.Bind(flatmenu.EVT_FLAT_MENU_SELECTED, self.AddNewFilePath, id = self.ID_NEW_WHEEL)
                self._popUpMenu.AppendItem(menuItem)
            else:
                self._popUpMenu = wx.Menu()
                menuItem = wx.MenuItem(self._popUpMenu, self.ID_NEW_ZIP, _("Add Zip File"), "", wx.ITEM_NORMAL)
                wx.EVT_MENU(self, self.ID_NEW_ZIP,self.AddNewFilePath)
                self._popUpMenu.AppendItem(menuItem)
                menuItem = wx.MenuItem(self._popUpMenu,self.ID_NEW_EGG, _("Add Egg File"), "", wx.ITEM_NORMAL)
                wx.EVT_MENU(self,self.ID_NEW_EGG,self.AddNewFilePath)
                self._popUpMenu.AppendItem(menuItem)
                menuItem = wx.MenuItem(self._popUpMenu,self.ID_NEW_WHEEL, _("Add Wheel File"), "", wx.ITEM_NORMAL)
                wx.EVT_MENU(self,self.ID_NEW_WHEEL,self.AddNewFilePath)
                self._popUpMenu.AppendItem(menuItem)
                

    def AddNewFilePath(self,event):
        id = event.GetId()
        if id == self.ID_NEW_ZIP:
            descr = _("Zip File") + " (*.zip)|*.zip"
            title = _("Choose a Zip File")
        elif id == self.ID_NEW_EGG:
            descr = _("Egg File") + " (*.egg)|*.egg"
            title = _("Choose a Egg File")
        elif id == self.ID_NEW_WHEEL:
            descr = _("Wheel File") + " (*.whl)|*.whl"
            title = _("Choose a Wheel File")
        dlg = wx.FileDialog(self,title ,
                       wildcard = descr,
                       style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        dlg.Destroy()
        if self.CheckPathExist(path):
            wx.MessageBox(_("Path already exist"),_("Add Path"),wx.OK,self)
            return
        item = self.tree_ctrl.AppendItem(self.tree_ctrl.GetRootItem(),path)
        self.tree_ctrl.SetItemImage(item,self.LibraryIconIdx,wx.TreeItemIcon_Normal)

    def AddNewPath(self,event):
        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(),
                        _("Choose a directory to Add"), 
                        style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        if self.CheckPathExist(path):
            wx.MessageBox(_("Path already exist"),_("Add Path"),wx.OK,self)
            return
        dlg.Destroy()
        item = self.tree_ctrl.AppendItem(self.tree_ctrl.GetRootItem(),path)
        self.tree_ctrl.SetItemImage(item,self.LibraryIconIdx,wx.TreeItemIcon_Normal)
        
    def OnRightClick(self, event):
        
        if self.tree_ctrl.GetSelection() == self.tree_ctrl.GetRootItem():
            return
        x, y = event.GetPosition()
        menu = wx.Menu()
        menu.Append(ID_GOTO_PATH, _("&Goto Path"))
        #must not use name ProcessEvent,otherwise will invoke flatmenu pop event invalid
        wx.EVT_MENU(self, ID_GOTO_PATH, self.TreeCtrlEvent)
        
        menu.Append(ID_REMOVE_PATH, _("&Remove Path"))
        wx.EVT_MENU(self, ID_REMOVE_PATH, self.TreeCtrlEvent)
        
        self.tree_ctrl.PopupMenu(menu,wx.Point(x, y))
        menu.Destroy()
        
    def TreeCtrlEvent(self, event): 
        id = event.GetId()
        if id == ID_GOTO_PATH:
            item = self.tree_ctrl.GetSelection()
            if item is not None and item.IsOk():
                fileutils.open_file_directory(self.tree_ctrl.GetItemText(item))
            return True
        elif id == ID_REMOVE_PATH:
            self.RemovePath(event)
            return True
        else:
            return True
        
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
        
    def GetPathList(self):
        path_list = []
        root_item = self.tree_ctrl.GetRootItem()
        (item, cookie) = self.tree_ctrl.GetFirstChild(root_item)
        while item:
            path = self.tree_ctrl.GetItemText(item)
            #should avoid environment contain unicode string,such as u'xxx'
            path_list.append(str(path))
            (item, cookie) = self.tree_ctrl.GetNextChild(root_item, cookie)
        return path_list

    def RemovePath(self,event):
        item = self.tree_ctrl.GetSelection()
        if item is None or not item.IsOk():
            return
        self.tree_ctrl.Delete(item)

    def ConvertPath(self,path):
        sys_encoding = locale.getdefaultlocale()[1]
        try:
            return path.encode(sys_encoding)
        except:
            try:
                return path.decode(sys_encoding)
            except:
                return path