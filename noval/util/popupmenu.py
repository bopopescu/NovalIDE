import wx
import noval.util.sysutils as sysutilslib

class PopupMenu(wx.Menu):
    """Custom wxMenu class that makes it easier to customize and access items.

    """
    def __init__(self, title=wx.EmptyString, style=0,toolbar=None):
        """Initialize a Menu Object
        @param title: menu title string
        @param style: type of menu to create

        """
        super(PopupMenu, self).__init__(title, style)
        self._toolbar = toolbar

    def Append(self, id_, text=u'', helpstr=u'', \
               kind=wx.ITEM_NORMAL, use_bmp=True):
        """Append a MenuItem
        @param id_: New MenuItem ID
        @keyword text: Menu Label
        @keyword helpstr: Help String
        @keyword kind: MenuItem type
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider

        """
        item = wx.MenuItem(self, id_, text, helpstr, kind)
        self.AppendItem(item, use_bmp)
        return item

    def AppendEx(self, id_, text=u'', helpstr=u'',
                 kind=wx.ITEM_NORMAL, use_bmp=True):
        """Like L{Append} but automatically applies keybindings to text
        based on item id.

        """
        binding = EdMenuBar.keybinder.GetBinding(id_)
        item = self.Append(id_, text+binding, helpstr, kind, use_bmp)
        return item

    def AppendItem(self, item, use_bmp=True):
        """Appends a MenuItem to the menu and adds an associated
        bitmap if one is available, unless use_bmp is set to false.
        @param item: wx.MenuItem
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider

        """
        if use_bmp and item.GetKind() == wx.ITEM_NORMAL and sysutilslib.isWindows():
            self.SetItemBitmap(item)
        super(PopupMenu, self).AppendItem(item)

    def Insert(self, pos, id_, text=u'', helpstr=u'', \
               kind=wx.ITEM_NORMAL, use_bmp=True):
        """Insert an item at position and attach a bitmap
        if one is available.
        @param pos: Position to insert new item at
        @param id_: New MenuItem ID
        @keyword label: Menu Label
        @keyword helpstr: Help String
        @keyword kind: MenuItem type
        @keyword use_bmp: try and set a bitmap if an appropriate one is
                          available in the ArtProvider

        """
        item = super(PopupMenu, self).Insert(pos, id_, text, helpstr, kind)
        if use_bmp and kind == wx.ITEM_NORMAL and sysutilslib.isWindows():
            self.SetItemBitmap(item)
        return item

    def InsertAfter(self, item_id, id_, label=u'', helpstr=u'',
                    kind=wx.ITEM_NORMAL, use_bmp=True):
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
        pos = None
        for item in xrange(self.GetMenuItemCount()):
            mitem = self.FindItemByPosition(item)
            if mitem.GetId() == item_id:
                pos = item
                break
        if pos:
            mitem = self.Insert(pos + 1, id_, label, helpstr, kind, use_bmp)
        else:
            mitem = self.Append(id_, label, helpstr, kind, use_bmp)
        return mitem

    def InsertBefore(self, item_id, id_, label=u'', helpstr=u'',
                    kind=wx.ITEM_NORMAL, use_bmp=True):
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
        pos = None
        for item in xrange(self.GetMenuItemCount()):
            mitem = self.FindItemByPosition(item)
            if mitem.GetId() == item_id:
                pos = item
                break
        if pos:
            mitem = self.Insert(pos, id_, label, helpstr, kind, use_bmp)
        else:
            mitem = self.Append(id_, label, helpstr, kind, use_bmp)
        return mitem

    def InsertAlpha(self, id_, label=u'', helpstr=u'',
                    kind=wx.ITEM_NORMAL, after=0, use_bmp=True):
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

    def SetItemBitmap(self, item):
        """Sets the MenuItems bitmap by getting the id from the
        artprovider if one exists.
        @param item: item to set bitmap for

        """
        bmp = wx.NullBitmap
        if self._toolbar is not None:
            tb_item = self._toolbar.FindById(item.GetId())
            if tb_item is not None:
                bmp = tb_item.GetBitmap()
        if bmp.IsNull():
            bmp = wx.ArtProvider.GetBitmap(str(item.GetId()), wx.ART_MENU)
        if not bmp.IsNull():
            item.SetBitmap(bmp)
            
