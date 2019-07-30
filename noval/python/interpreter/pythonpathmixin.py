# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog,messagebox
from noval import NewId,_
import noval.util.fileutils as fileutils
import noval.util.apputils as sysutils
import noval.python.parser.utils as parserutils
import locale
import noval.imageutils as imageutils
import noval.consts as consts
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.menu as tkmenu

ID_GOTO_PATH = NewId()
ID_REMOVE_PATH = NewId()

ID_NEW_ZIP = NewId()
ID_NEW_EGG = NewId()
ID_NEW_WHEEL = NewId()

class PythonpathMixin:
    """description of class"""    
    def InitUI(self,hide_tree_root=False):
        self.has_root = not hide_tree_root
        self.treeview = treeviewframe.TreeViewFrame(self)
        self.treeview.tree["show"] = ("tree",)
        self.treeview.pack(side=tk.LEFT,fill="both",expand=1)
        self.LibraryIcon = imageutils.load_image("","python/library_obj.gif")
        self.treeview.tree.bind("<3>", self.OnRightClick, True)
        right_frame = ttk.Frame(self)
        self.add_path_btn = ttk.Button(right_frame, text=_("Add Path.."),command=self.AddNewPath)
        self.add_path_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))

        self.remove_path_btn = ttk.Button(right_frame, text=_("Remove Path..."),command=self.RemovePath)
        self.remove_path_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        
        self.add_file_btn = ttk.Menubutton(right_frame,
                            text=_("Add File..."),state="pressed")
        self.add_file_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        
        right_frame.pack(side=tk.LEFT,fill="y")
        self.button_menu = self.CreatePopupMenu()
        self.add_file_btn.config(menu = self.button_menu)
        self.menu = None
        
    def CreatePopupMenu(self):
        menu = tkmenu.PopupMenu()
        menuItem = tkmenu.MenuItem(ID_NEW_ZIP, _("Add Zip File"), None, None,None)
        menu.AppendMenuItem(menuItem,handler=lambda:self.AddNewFilePath(ID_NEW_ZIP))
        menuItem = tkmenu.MenuItem(ID_NEW_EGG, _("Add Egg File"), None, None,None)
        menu.AppendMenuItem(menuItem,handler=lambda:self.AddNewFilePath(ID_NEW_EGG))
        menuItem = tkmenu.MenuItem(ID_NEW_WHEEL, _("Add Wheel File"), None, None,None)
        menu.AppendMenuItem(menuItem,handler=lambda:self.AddNewFilePath(ID_NEW_WHEEL))
        return menu

    def AddNewFilePath(self,id):
        if id == ID_NEW_ZIP:
            filetypes = [(_("Zip File") ,"*.zip"),]
            title = _("Choose a Zip File")
        elif id == ID_NEW_EGG:
            filetypes = [(_("Egg File") , "*.egg"),]
            title = _("Choose a Egg File")
        elif id == ID_NEW_WHEEL:
            filetypes = [(_("Wheel File") ,"*.whl"),]
            title = _("Choose a Wheel File")
        path = filedialog.askopenfilename(title=title ,
                       filetypes = filetypes,
                       master=self)
        if not path:
            return
        self.AddPath(fileutils.opj(path))

    def AddNewPath(self):
        path = filedialog.askdirectory(title=_("Choose a directory to Add"))
        if not path:
            return
        self.AddPath(fileutils.opj(path))
        
    def AddPath(self,path):
        if self.CheckPathExist(path):
            messagebox.showinfo(_("Add Path"),_("Path already exist"),parent= self)
            return
        self.treeview.tree.insert(self.GetRootItem(),"end",text=path,image=self.LibraryIcon)
        
    def OnRightClick(self, event):
        if self.treeview.tree.selection()[0] == self.GetRootItem():
            return
        if self.menu is None:
            self.menu = tkmenu.PopupMenu()
            self.menu.Append(ID_GOTO_PATH, _("&Goto Path"),handler=lambda:self.TreeCtrlEvent(ID_GOTO_PATH))
            self.menu.Append(ID_REMOVE_PATH, _("&Remove Path"),handler=lambda:self.TreeCtrlEvent(ID_REMOVE_PATH))
        self.menu.tk_popup(event.x_root, event.y_root)

    def TreeCtrlEvent(self,id):
        '''
            右键处理事件
        '''
        if id == ID_GOTO_PATH:
            item = self.treeview.tree.selection()[0]
            fileutils.safe_open_file_directory(self.treeview.tree.item(item,"text"))
            return True
        elif id == ID_REMOVE_PATH:
            self.RemovePath()
            return True
        else:
            return True
            
    def GetRootItem(self):
        if self.has_root:
            root_item = self.treeview.tree.get_children()[0]
        else:
            root_item = ''
        return root_item
        
    def CheckPathExist(self,path):
        root_item = self.GetRootItem()
        items = self.treeview.tree.get_children(root_item)
        for item in items:
            if parserutils.ComparePath(self.treeview.tree.item(item,"text"),path):
                return True
        return False
        
    def GetPathList(self):
        path_list = []
        root_item = self.GetRootItem()
        items = self.treeview.tree.get_children(root_item)
        for item in items:
            path = self.treeview.tree.item(item,"text")
            path_list.append(path)
        return path_list

    def RemovePath(self):
        selections = self.treeview.tree.selection()
        if not selections:
            return
        for item in selections:
            self.treeview.tree.delete(item)

    def ConvertPath(self,path):
        sys_encoding = locale.getdefaultlocale()[1]
        try:
            return path.encode(sys_encoding)
        except:
            try:
                return path.decode(sys_encoding)
            except:
                return path