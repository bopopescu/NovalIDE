# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        menu.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-16
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
import noval.consts as consts
from noval import _,GetApp
import collections
from noval.binds import *
import noval.util.utils as utils
import copy
import os
import noval.misc as misc

MenuItem = collections.namedtuple("MenuItem", ["id","label","accelerator","image","tester"])


class KeyBinder(object):
    """Class for managing keybinding configurations"""
    cprofile = None # Current Profile Name String
    key_binds = copy.copy(DEFAULT_KEY_BINDS) # Active Profile (dict)

    def __init__(self):
        """Create the KeyBinder object"""
        object.__init__(self)
        # Attributes
        self.cache = None
        
    def GetCachedir(self):
        if self.cache is None:
            self.cache = os.path.join(utils.get_user_data_path(),consts.USER_CACHE_DIR)
        return self.cache
        
    @classmethod
    def CheckKeybindsConflict(cls):
        '''
            检查快捷键冲突
        '''
        accels = list(cls.key_binds.values())
        for accel in accels:
            temp_list = accels
            temp_list.remove(accel)
            if temp_list.count(accel) != 0:
                raise RuntimeError("accelerator %s is conflicted...." % accel)

    def GetBinding(self, item_id,accelerator=None):
        """
            获取菜单id对应的快捷键,并转化成tk内部识别的快捷键组合
        @param item_id: Menu Item Id
        @return: string,string

        """
        if accelerator is None:
            #如果用户没有指定快捷键则从配置字典中加载是否存在快捷键
            accelerator = self.GetRawBinding(item_id)
        if accelerator is not None:
            #将快捷键转换成tkinter识别的快捷键字符串,如Ctrl+O转换成<Control-o>
            sequence = misc.accelerator_to_sequence(accelerator)
            return accelerator,sequence
        return None,None

    @classmethod
    def GetCurrentProfile(cls):
        """Get the name of the currently set key profile if one exists
        @param cls: Class Object
        @return: string or None

        """
        return cls.cprofile

    @classmethod
    def GetCurrentProfileDict(cls):
        """Get the dictionary of keybindings
        @param cls: Class Object
        @return: dict

        """
        return cls.keyprofile

    @staticmethod
    def GetKeyProfiles():
        """Get the list of available key profiles
        @return: list of strings

        """
        recs = util.GetResourceFiles(u'cache', trim=True, get_all=False,
                                     suffix='.ekeys', title=False)
        if recs == -1:
            recs = list()

        tmp = util.GetResourceFiles(u'ekeys', True, True, '.ekeys', False)
        if tmp != -1:
            recs.extend(tmp)

        return recs

    def GetProfilePath(self, pname):
        """Get the full path to the given keyprofile
        @param pname: profile name
        @return: string or None
        @note: expects unique name for each profile in the case that
               a name exists in both the user and system paths the one
               found on the user path will be returned.

        """
        if pname is None:
            return None

        rname = None
        for rec in self.GetKeyProfiles():
            if rec.lower() == pname.lower():
                rname = rec
                break

        # Must be a new profile
        if rname is None:
            rname = pname

        kprof = u"%s%s.ekeys" % (ed_glob.CONFIG['CACHE_DIR'], rname)
        if not os.path.exists(kprof):
            # Must be a system supplied keyprofile
            rname = u"%s%s.ekeys" % (ed_glob.CONFIG['KEYPROF_DIR'], rname)
            if not os.path.exists(rname):
                # Doesn't exist at syspath either so instead assume it is a new
                # custom user defined key profile.
                rname = kprof
        else:
            rname = kprof

        return rname

    @classmethod
    def GetRawBinding(cls, item_id):
        """Get the raw key binding tuple
        @param cls: Class Object
        @param item_id: MenuItem Id
        @return: tuple

        """
        return cls.key_binds.get(item_id, None)

    @classmethod
    def FindMenuId(cls, keyb):
        """Find the menu item ID that the
        keybinding is currently associated with.
        @param cls: Class Object
        @param keyb: tuple of unicode (u'Ctrl', u'C')
        @return: int (-1 if not found)

        """
        menu_id = -1
        for key, val in cls.keyprofile.iteritems():
            if val == keyb:
                menu_id = key
                break
        return menu_id

    @classmethod
    def LoadDefaults(cls):
        """Load the default key profile"""
        cls.keyprofile = dict(_DEFAULT_BINDING)
        cls.cprofile = None

    def LoadKeyProfile(self, pname):
        """Load a key profile from profile directory into the binder
        by name.
        @param pname: name of key profile to load

        """
        if pname is None:
            ppath = None
        else:
            ppath = self.GetProfilePath(pname)
        self.LoadKeyProfileFile(ppath)

    def LoadKeyProfileFile(self, path):
        """Load a key profile from the given path
        @param path: full path to file

        """
        keydict = dict()
        pname = None
        if path:
            pname = os.path.basename(path)
            pname = pname.rsplit('.', 1)[0]

        if pname is not None and os.path.exists(path):
            reader = util.GetFileReader(path)
            if reader != -1:
                util.Log("[keybinder][info] Loading KeyProfile: %s" % path)
                for line in reader:
                    parts = line.split(u'=', 1)
                    # Check that the line was formatted properly
                    if len(parts) == 2:
                        # Try to find the ID value
                        item_id = _GetValueFromStr(parts[0])
                        if item_id is not None:
                            tmp = [ part.strip()
                                    for part in parts[1].split(u'+')
                                    if len(part.strip()) ]

                            # Do some checking if the binding is valid
                            nctrl = len([key for key in tmp
                                         if key not in (u'Ctrl', u'Alt', u'Shift')])
                            if nctrl:
                                if parts[1].strip().endswith(u'++'):
                                    tmp.append(u'+')
                                kb = tuple(tmp)
                                if kb in keydict.values():
                                    for mid, b in keydict.iteritems():
                                        if kb == b:
                                            del keydict[mid]
                                            break
                                keydict[item_id] = tuple(tmp)
                            else:
                                # Invalid key binding
                                continue

                reader.close()
                KeyBinder.keyprofile = keydict
                KeyBinder.cprofile = pname
                return
            else:
                util.Log("[keybinder][err] Couldn't read %s" % path)
        elif pname is not None:
            # Fallback to default keybindings
            util.Log("[keybinder][err] Failed to load bindings from %s" % pname)

        util.Log("[keybinder][info] Loading Default Keybindings")
        KeyBinder.LoadDefaults()

    def SaveKeyProfile(self):
        """Save the current key profile to disk"""
        if KeyBinder.cprofile is None:
            util.Log("[keybinder][warn] No keyprofile is set, cant save")
        else:
            ppath = self.GetProfilePath(KeyBinder.cprofile)
            writer = util.GetFileWriter(ppath)
            if writer != -1:
                itemlst = list()
                for item in KeyBinder.keyprofile.keys():
                    itemlst.append(u"%s=%s%s" % (_FindStringRep(item),
                                                self.GetBinding(item).lstrip(),
                                                os.linesep))
                writer.writelines(sorted(itemlst))
                writer.close()
            else:
                util.Log("[keybinder][err] Failed to open %s for writing" % ppath)

    @classmethod
    def SetBinding(cls, item_id, keys):
        """Set the keybinding of a menu id
        @param cls: Class Object
        @param item_id: item to set
        @param keys: string or list of key strings ['Ctrl', 'S']

        """
        if isinstance(keys, basestring):
            keys = [ key.strip() for key in keys.split(u'+')
                     if len(key.strip())]
            keys = tuple(keys)

        if len(keys):
            # Check for an existing binding
            menu_id = cls.FindMenuId(keys)
            if menu_id != -1:
                del cls.keyprofile[menu_id]
            # Set the binding
            cls.keyprofile[item_id] = keys
        elif item_id in cls.keyprofile:
            # Clear the binding
            del cls.keyprofile[item_id]
        else:
            pass

    @classmethod
    def SetProfileName(cls, pname):
        """Set the name of the current profile
        @param cls: Class Object
        @param pname: name to set profile to

        """
        cls.cprofile = pname

    @classmethod
    def SetProfileDict(cls, keyprofile):
        """Set the keyprofile using a dictionary of id => bindings
        @param cls: Class Object
        @param keyprofile: { menu_id : (u'Ctrl', u'C'), }

        """
        cls.keyprofile = keyprofile

class PopupMenu(tk.Menu):
    """Custom wxMenu class that makes it easier to customize and access items.

    """
    def __init__(self,master=None,**kw):
        """Initialize a Menu Object
        @param title: menu title string
        @param style: type of menu to create

        """
        tk.Menu.__init__(self,master=master,tearoff=False,**kw)
        self.images = []
        self._items = []
        self._submenus = []
        
    def GetMenuData(self,id_,text,handler,img,accelerator,kind,variable,tester):
        text = MenubarMixin.FormatMenuName(text)
        menu_item = MenuItem(id_,text,accelerator,img,tester)
        kwargs = dict(label=text,command=handler)
        
        if img is not None:
            #设置图像在文字的左边
            kwargs.update(dict(image=img,compound=tk.LEFT))
            #tkinter并不保存图像,必须在此处添加到图片列表以便永久保存
            self.images.append(img)
        if accelerator is not None:
            kwargs.update(dict(accelerator=accelerator))
        if kind == consts.CHECK_MENU_ITEM_KIND or kind == consts.RADIO_MENU_ITEM_KIND:
            #设置复选或者单选菜单关联变量,鼠标点击菜单时相应的变量值会改变
            if variable is not None:
                kwargs.update(dict(variable = variable))
        return menu_item,kwargs
        
    def Append(self, id_, text, helpstr=u'', handler=None,img=None,accelerator=None,\
               kind=consts.NORMAL_MENU_ITEM_KIND,variable=None,tester=None,**extra_args):
        """Append a MenuItem
        @param id_: New MenuItem ID
        @keyword text: Menu Label
        @keyword helpstr: Help String
        @keyword kind: MenuItem type
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider

        """
        menu_item,kwargs = self.GetMenuData(id_,text,handler,img,accelerator,kind,variable,tester)
        kwargs.update(extra_args)
        self._items.append(menu_item)
        if kind == consts.NORMAL_MENU_ITEM_KIND:
            self.add_command(**kwargs)
        elif kind == consts.CHECK_MENU_ITEM_KIND:
            self.add_checkbutton(**kwargs)
        elif kind == consts.RADIO_MENU_ITEM_KIND:
            self.add_radiobutton(**kwargs)

    def AppendMenuItem(self, item,handler=None,**kwargs):
        """Appends a MenuItem to the menu and adds an associated
        bitmap if one is available, unless use_bmp is set to false.
        @param item: wx.MenuItem
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider

        """
        #用户如果指定快捷键使用用户指定的快捷键
        if 'accelerator' not in kwargs:
            accelerator=item.accelerator
        else:
            accelerator=kwargs.get('accelerator')

        #用户如果指定tester函数使用用户指定的tester函数
        if 'tester' not in kwargs:
            tester=item.tester
        else:
            tester=kwargs.get('tester')

        #用户如果指定图标使用用户指定的图标
        if 'image' not in kwargs:
            image=item.image
        else:
            image=kwargs.get('image')

        self.Append(item.id,item.label,handler=handler,img = image,accelerator=accelerator,tester=tester)

    def AppendMenu(self,id_, text,menu):
        text = MenubarMixin.FormatMenuName(text)
        self._submenus.append((id_,menu))
        menu_menu_item = MenuItem(id_,text,None,None,None)
        self._items.append(menu_menu_item)
        self.add_cascade(label= text, menu=menu)
        
    def InsertMenu(self,pos,id_, text,menu):
        text = MenubarMixin.FormatMenuName(text)
        self._submenus.append((id_,menu))
        menu_menu_item = MenuItem(id_,text,None,None,None)
        self._items.insert(pos,menu_menu_item)
        self.insert(
            pos,
            "cascade",
            label= text,
            menu=menu
        )
        return menu_menu_item
        
    def InsertMenuAfter(self,item_id,id_, text,menu):
        '''
            插入某个子菜单
        '''
        pos = -1
        for i,menu_item in enumerate(self._items):
            if menu_item.id == item_id:
                pos = i
                break
        if pos >-1:
            mitem = self.InsertMenu(pos + 1, id_, text, menu)
        else:
            mitem = self.AppendMenu(id_, text,menu)
        return mitem
        
    def GetMenu(self,id_):
        for menu in self._submenus:
            if menu[0] == id_:
                return menu[1]
        return None
        
    def Insert(self, pos, id_, text, helpstr=u'', handler=None,img=None,accelerator=None,\
               kind=consts.NORMAL_MENU_ITEM_KIND,variable=None,tester=None):
        """Insert an item at position and attach a bitmap
        if one is available.
        @param pos: Position to insert new item at
        @param id_: New MenuItem ID
        @keyword label: Menu Label
        @keyword helpstr: Help String
        @keyword kind: MenuItem type
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider
        插入某个菜单项
        """
        if pos == -1:
            return self.Append(id_, text, helpstr, handler, img,accelerator,kind,variable,tester)
        menu_item,kwargs = self.GetMenuData(id_,text,handler,img,accelerator,kind,variable,tester)
        self._items.insert(pos,menu_item)
        self.insert(
            pos,
            "checkbutton" if kind == consts.CHECK_MENU_ITEM_KIND  else "command",
            **kwargs
        )
        return menu_item

    def InsertAfter(self, item_id, id_, text, helpstr=u'', handler=None,img=None,accelerator=None,\
               kind=consts.NORMAL_MENU_ITEM_KIND,variable=None,tester=None):
        """Inserts the given item after the specified item id in
        the menu. If the id cannot be found then the item will appended
        to the end of the menu.
        @param item_id: Menu ID to insert after
        @param id_: New MenuItem ID
        @keyword label: Menu Label
        @keyword helpstr: Help String
        @keyword kind: MenuItem type
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider
        @return: the inserted menu item

        """
        pos = -1
        for i,menu_item in enumerate(self._items):
            if menu_item.id == item_id:
                pos = i
                break
        if pos >-1:
            mitem = self.Insert(pos + 1, id_, text, helpstr, handler, img,accelerator,kind,variable,tester)
        else:
            mitem = self.Append(id_, text, helpstr, handler, img,accelerator,kind,variable,tester)
        return mitem

    def InsertBefore(self, item_id, id_, text, helpstr=u'', handler=None,img=None,accelerator=None,\
               kind=consts.NORMAL_MENU_ITEM_KIND,variable=None,tester=None):
        """Inserts the given item before the specified item id in
        the menu. If the id cannot be found then the item will appended
        to the end of the menu.
        @param item_id: Menu ID to insert new item before
        @param id_: New MenuItem ID
        @keyword label: Menu Label
        @keyword helpstr: Help String
        @keyword kind: MenuItem type
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider
        @return: menu item that was inserted

        """
        pos = -1
        for i,menu_item in enumerate(self._items):
            if menu_item.id == item_id:
                pos = i
                break
        if pos >-1:
            mitem = self.Insert(pos, id_, text, helpstr, handler, img,accelerator,kind,variable,tester)
        else:
            mitem = self.Append(id_, text, helpstr, handler, img,accelerator,kind,variable,tester)
        return mitem

    def InsertAlpha(self, id_, label=u'', helpstr=u'', after=0, use_bmp=True):
        """Attempts to insert the new menuitem into the menu
        alphabetically. The optional parameter 'after' is used
        specify an item id to start the alphabetical lookup after.
        Otherwise the lookup begins from the first item in the menu.
        @param id_: New MenuItem ID
        @keyword label: Menu Label
        @keyword helpstr: Help String
        @keyword kind: MenuItem type
        @keyword after: id of item to start alpha lookup after
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider
        @return: menu item that was inserted

        """
        if after:
            start = False
        else:
            start = True
        last_ind = self.GetMenuItemCount() - 1
        pos = last_ind
        for item in range(self.GetMenuItemCount()):
            mitem = self.FindItemByPosition(item)
            if mitem.IsSeparator():
                continue

            mlabel = mitem.GetItemLabel()
            if after and mitem.GetId() == after:
                start = True
                continue
            if after and not start:
                continue
            if label < mlabel:
                pos = item
                break

        l_item = self.FindItemByPosition(last_ind)
        if pos == last_ind and (l_item.IsSeparator() or label > mlabel):
            mitem = self.Append(id_, label, helpstr, kind, use_bmp)
        else:
            mitem = self.Insert(pos, id_, label, helpstr, kind, use_bmp)
        return mitem

    def RemoveItemByName(self, name):
        """Removes an item by the label. It will remove the first
        item matching the given name in the menu, the matching is
        case sensitive. The return value is the either the id of the
        removed item or None if the item was not found.
        @param name: name of item to remove
        @return: id of removed item or None if not found

        """
        menu_id = None
        for pos in range(self.GetMenuItemCount()):
            item = self.FindItemByPosition(pos)
            if name == item.GetLabel():
                menu_id = item.GetId()
                self.Remove(menu_id)
                break
        return menu_id
        
    def FindMenuItem(self,menu_id):
        for menu_item in self._items:
            if menu_item.id == menu_id:
                return menu_item
        return None
        
    def GetMenuIndex(self,id_):
        for i,menu_item in enumerate(self._items):
            if menu_item.id == id_:
                return i
        return -1
        
    def add_separator(self):
        empty_menu_item = MenuItem(-1,"",None,None,None)
        self._items.append(empty_menu_item)
        tk.Menu.add_separator(self)
        
    def GetItemCount(self):
        return len(self._items)

    def delete(self,start,end="end"):
        if end == "end":
            end_index = len(self._items) -1
        else:
            end_index = end
        
        #倒序删除,防止数组越界或者索引错误
        for i in range(end_index,start-1,-1):
            item = self._items[i]
            del self._items[i]
        tk.Menu.delete(self,start,end)
        
    def configure(self, cnf=None, **kw):
        #更新菜单主题颜色时同时更新子菜单的主题颜色
        for submenu in self._submenus:
            submenu[1].configure(cnf,**kw)
        tk.Menu.configure(self, cnf, **kw)
        
    def GetMenuhandler(self,menu_id):
        index = self.GetMenuIndex(menu_id)
        if -1 == index:
            return None
        return self.entrycget(index, "command")
        
    def _update_menu(self):
        '''
            弹出菜单时更新菜单的可用状态
        '''
        if self.index("end") is None:
            return
        for i in range(self.index("end") + 1):
            item_data = self.entryconfigure(i)
            #菜单下面的子菜单
            if 'menu' in item_data:
                menu_item = self._items[i]
                menu_id = menu_item.id
                submenu = self.GetMenu(menu_id)
                #更新子菜单
                submenu._update_menu()
            elif "label" in item_data:
                menu_item = self._items[i]
                tester = menu_item.tester
                #根据菜单回调函数返回bool值设置菜单是否是灰色状态
                if tester and not tester():
                    self.entryconfigure(i, state=tk.DISABLED)
                else:
                    self.entryconfigure(i, state=tk.NORMAL)
                    
    def Enable(self,menu_id,enabled=True):
        for i in range(self.index("end") + 1):
            item_data = self.entryconfigure(i)
            if "label" in item_data:
                menu_item = self._items[i]
                if menu_id == menu_item.id:
                    if not enabled:
                        self.entryconfigure(i, state=tk.DISABLED)
                    else:
                        self.entryconfigure(i, state=tk.NORMAL)
                        

class CustomMenubar(ttk.Frame):
    '''
        自定义菜单栏menubar,可以随ui的主题改变而改变,默认菜单栏不会随ui的主题颜色改变,默认是白色背景
        这个可以随ui的主题改变而改变菜单栏的背景色
    '''
    def __init__(self, master):
        ttk.Frame.__init__(self, master, style="CustomMenubar.TFrame")
        self._opened_menu = None

        ttk.Style().map(
            "CustomMenubarLabel.TLabel",
            background=[
                ("!active", misc.lookup_style_option("Menubar", "background", "gray")),
                (
                    "active",
                    misc.lookup_style_option("Menubar", "activebackground", "LightYellow"),
                ),
            ],
            foreground=[
                ("!active", misc.lookup_style_option("Menubar", "foreground", "black")),
                ("active", misc.lookup_style_option("Menubar", "activeforeground", "black")),
            ],
        )

    def add_cascade(self, label, menu):
        label_widget = ttk.Label(
            self,
            style="CustomMenubarLabel.TLabel",
            text=label,
            padding=[6, 3, 6, 2],
            font="TkDefaultFont",
        )

        if len(self._menus) == 0:
            #菜单栏的第一项距离IDE左边框的左边距,要和工具栏的左边距保持一致
            padx = (0, 0)
        else:
            padx = 0

        label_widget.grid(row=0, column=len(self._menus), padx=padx)

        def enter(event):
            label_widget.state(("active",))

            # Don't know how to open this menu when another menu is open
            # another tk_popup just doesn't work unless old menu is closed by click or Esc
            # https://stackoverflow.com/questions/38081470/is-there-a-way-to-know-if-tkinter-optionmenu-dropdown-is-active
            # unpost doesn't work in Win and Mac: https://www.tcl.tk/man/tcl8.5/TkCmd/menu.htm#M62
            # print("ENTER", menu, self._opened_menu)
            if self._opened_menu is not None:
                self._opened_menu.unpost()
                click(event)

        def leave(event):
            label_widget.state(("!active",))

        def click(event):
            try:
                # print("Before")
                self._opened_menu = menu
                menu.tk_popup(
                    label_widget.winfo_rootx(),
                    label_widget.winfo_rooty() + label_widget.winfo_height(),
                )
            finally:
                # print("After")
                self._opened_menu = None

        label_widget.bind("<Enter>", enter, True)
        label_widget.bind("<Leave>", leave, True)
        label_widget.bind("<1>", click, True)
        
        

class MenubarMixin:
    """Custom menubar to allow for easier access and updating
    of menu components.
    @todo: redo all of this

    """
    keybinder = KeyBinder()

    def __init__(self):
        if GetApp().GetDebug():
            #调试模式时检查快捷键是否有冲突
            self.keybinder.CheckKeybindsConflict()
        #tkinter默认绑定了F10快捷键,需要先解绑F10才能重新绑定F10
        GetApp().unbind_all("<F10>")
        self._menus = []

    def GetMenuByName(self,menu_name):
        format_menu_name = self.FormatMenuName(menu_name)
        for menu_info in self._menus:
            if menu_info[1] == format_menu_name:
                return menu_info[2]
        raise RuntimeError("menu %s is not exist in menubar" % menu_name)
        
    def GetMenu(self,menu_name):
        menu_name = self.FormatMenuName(menu_name)
        if not self.FindMenuByName(menu_name):
            menu = PopupMenu(self)
            #设置菜单状态更新的命令
            menu["postcommand"] = lambda: menu._update_menu()
            self.add_cascade(label= menu_name, menu=menu)
            self._menus.append((len(self._menus),menu_name,menu))
        return self.GetMenuByName(menu_name)

    def GetFileMenu(self):
        return self.GetMenu(_("&File"))
        
    def GetEditMenu(self):
        return self.GetMenu(_("&Edit"))
        
    def GetViewMenu(self):
        return self.GetMenu(_("&View"))
        
    def GetFormatMenu(self):
        return self.GetMenu(_("&Format"))
        
    def GetProjectMenu(self):
        self.GetMenu(_("&Project"))
        #menu = tk.Menu(self,tearoff=False)
        #self.InsertMenu(0,_("&Project"),menu)
        
    def GetRunMenu(self):
        return self.GetMenu(_("&Run"))
        
    def GetToolsMenu(self):
        return self.GetMenu(_("&Tools"))
        
   # def GetWindowsMenu(self):
    #    return self.GetMenuByName(_(WINDOWS_MENU_ORIG_NAME))

    def GetHelpMenu(self):
        return self.GetMenu(_("&Help"))
        
    @staticmethod
    def FormatMenuName(menu_name):
        if menu_name.find("&") != -1:
            menu_name = menu_name.replace("&","")
        return menu_name
        
    def GetMenuIndexByName(self,menu_name):
        menu = self.GetMenuByName(menu_name)
        return self.GetMenuIndex(menu)
        
    def GetMenuIndex(self,menu):
        for menu_info in self._menus:
            if menu_info[2] == menu:
                return menu_info[0]
        raise RuntimeError("Couldn't find menu")
        
    def GetMenuByIndex(self,menu_index):
        return self._menus[menu_index]
        
    def FindMenu(self,menu):
        for menu_info in self._menus:
            if menu_info[2] == menu:
                return True
        return False

    def FindMenuByName(self,menu_name):
        for menu_info in self._menus:
            if menu_info[1] == menu_name:
                return True
        return False
        
    def InsertMenu(self,menu_index,menu_name,menu):
        assert(menu_index >= 0 and isinstance(menu_index,int))
        menu_name = self.FormatMenuName(menu_name)
        self.insert(menu_index + 1,"cascade",label=menu_name,menu=menu)
        assert(not self.FindMenu(menu))
        self._menus.insert(menu_index,(menu_index,menu_name,menu))
        assert(self.FindMenu(menu))
        assert(self.GetMenuIndex(menu) == menu_index)

    def FindItemById(self,id):
        '''
            根据菜单id在菜单栏的所有菜单中查找对应的项
        '''
        for _,_,menu in self._menus:
            menu_item = menu.FindMenuItem(id)
            if menu_item:
                return menu_item
        return None
        
    def GetMenuhandler(self,menu_name,menu_id):
        menu = self.GetMenu(menu_name)
        return menu.GetMenuhandler(menu_id)
        


class DefaultMenuBar(tk.Menu,MenubarMixin):
    '''
        默认菜单栏,不能随ui主题颜色改变更改背景色
    '''
    def __init__(self, master,**kwargs):
        tk.Menu.__init__(self,master,**kwargs)
        MenubarMixin.__init__(self)
        
class ThemeMenuBar(CustomMenubar,MenubarMixin):
    '''
        自定义菜单栏,能随ui主题颜色改变更改背景色
    '''
    def __init__(self, master):
        CustomMenubar.__init__(self,master)
        MenubarMixin.__init__(self)