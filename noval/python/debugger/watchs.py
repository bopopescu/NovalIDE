from noval import _,NewId
import noval.util.apputils as sysutils
import noval.ui_base as ui_base
from tkinter import ttk
import noval.util.utils as utils

ERROR_NAME_VALUE = "<errors:could not evaluate the value>"

def getAddWatchBitmap():
    return images.load("debugger/newWatch.png")

def getQuickAddWatchBitmap():
    return images.load("debugger/watch.png")
    
def getAddtoWatchBitmap():
    return images.load("debugger/addToWatch.png")
    
def getClearWatchBitmap():
    return images.load("debugger/delete.png")

class Watch:
    CODE_ALL_FRAMES = 0
    CODE_THIS_BLOCK = 1
    CODE_THIS_LINE = 2
    CODE_RUN_ONCE = 3
    
    NAME_KEY = 'name'
    EXPERSSION_KEY = 'expression'
    SHOW_CODE_FRAME_KEY = 'showcodeframe'
    #saved watches key
    WATCH_LIST_KEY = 'MasterWatches'

    def __init__(self, name, command, show_code=CODE_ALL_FRAMES):
        self._name = name
        self._command = command
        self._show_code = show_code
        
    @property
    def Name(self):
        return self._name
        
    @property
    def Expression(self):
        return self._command
        
    @property
    def ShowCodeFrame(self):
        return self._show_code
        
    @staticmethod
    def CreateWatch(name):
        return Watch(name,name)
        
    def IsRunOnce(self):
        return (self.ShowCodeFrame == self.CODE_RUN_ONCE)
        
    @classmethod
    def Dump(cls,watchs):
        watch_list = []
        for watch in watchs:
            dct = {
                cls.NAME_KEY:watch.Name,
                cls.EXPERSSION_KEY:watch.Expression,
                cls.SHOW_CODE_FRAME_KEY:watch.ShowCodeFrame,
            }
            watch_list.append(dct)
        utils.ProfileSet(cls.WATCH_LIST_KEY, watch_list.__repr__())
        
    @classmethod
    def Load(cls):
        watchs_str = utils.profile_get(cls.WATCH_LIST_KEY,"[]")
        try:
            watch_list = eval(watchs_str)
        except Exception as e:
            print (e)
            watch_list = []
        watchs = []
        for dct in watch_list:
            watch = Watch(dct[cls.NAME_KEY],dct[cls.EXPERSSION_KEY],dct.get(cls.SHOW_CODE_FRAME_KEY,cls.CODE_ALL_FRAMES))
            watchs.append(watch)
        return watchs

class WatchDialog(ui_base.CommonModaldialog):
    WATCH_ALL_FRAMES = "Watch in all frames"
    WATCH_THIS_FRAME = "Watch in this frame only"
    WATCH_ONCE = "Watch once and delete"
    
    WATCH_FRAME_TYPES = {
        Watch.CODE_ALL_FRAMES:WATCH_ALL_FRAMES,
        Watch.CODE_THIS_LINE:WATCH_THIS_FRAME,
        Watch.CODE_RUN_ONCE:WATCH_ONCE
    }
    def __init__(self, parent, title, chain,is_quick_watch=False,watch_obj=None):
        wx.Dialog.__init__(self, parent, -1, title, style=wx.DEFAULT_DIALOG_STYLE)
        self._chain = chain
        self._is_quick_watch = is_quick_watch
        self._watch_obj = watch_obj
        self._watch_frame_type = Watch.CODE_ALL_FRAMES
        self.label_2 = wx.StaticText(self, -1, _("Watch Name:"))
        self._watchNameTextCtrl = wx.TextCtrl(self, -1, "")
        self._watchNameTextCtrl.Bind(wx.EVT_TEXT,self.SetNameValue)
        self.label_3 = wx.StaticText(self, -1, _("Expression:"), style=wx.ALIGN_RIGHT)
        self._watchValueTextCtrl = wx.TextCtrl(self, -1, "",size=(400,200),style = wx.TE_MULTILINE)
        if is_quick_watch:
            self._watchValueTextCtrl.Enable(False)
        self.radio_box_1 = wx.RadioBox(self, -1, _("Watch Information"), choices=[WatchDialog.WATCH_ALL_FRAMES, WatchDialog.WATCH_THIS_FRAME, WatchDialog.WATCH_ONCE], majorDimension=0, style=wx.RA_SPECIFY_ROWS)

        self._okButton = wx.Button(self, wx.ID_OK, _("&OK"))
        self._okButton.SetDefault()
        self._okButton.SetHelpText(_("The OK button completes the dialog"))
        def OnOkClick(event):
            if self._watchNameTextCtrl.GetValue() == "":
                wx.MessageBox(_("You must enter a name for the watch."), _("Add a Watch"))
                return
            if self._watchValueTextCtrl.GetValue() == "":
                wx.MessageBox(_("You must enter some code to run for the watch."), _("Add a Watch"))
                return
            self.EndModal(wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, OnOkClick, self._okButton)

        self._cancelButton = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        self._cancelButton.SetHelpText(_("The Cancel button cancels the dialog."))

        self.__set_properties()
        self.__do_layout()

    def GetSettings(self):
        if self.radio_box_1.GetStringSelection() == WatchDialog.WATCH_ALL_FRAMES:
            watch_code_frame = Watch.CODE_ALL_FRAMES
        elif self.radio_box_1.GetStringSelection() == WatchDialog.WATCH_THIS_FRAME:
            watch_code_frame = Watch.CODE_THIS_LINE
        elif self.radio_box_1.GetStringSelection() == WatchDialog.WATCH_ONCE:
            watch_code_frame = Watch.CODE_RUN_ONCE
        return Watch(self._watchNameTextCtrl.GetValue(),self._watchValueTextCtrl.GetValue(),watch_code_frame)

    def GetSendFrame(self):
        return (WatchDialog.WATCH_ALL_FRAMES != self.radio_box_1.GetStringSelection())

    def GetRunOnce(self):
        return (WatchDialog.WATCH_ONCE == self.radio_box_1.GetStringSelection())

    def __set_properties(self):
        ###self.SetTitle("Add a Watch")
        #self.SetSize((400, 250))
        if self._watch_obj is not None:
            self._watch_frame_type = self._watch_obj.ShowCodeFrame
            self._watchNameTextCtrl.SetValue(self._watch_obj.Name)
            self._watchValueTextCtrl.SetValue(self._watch_obj.Expression)
        self.radio_box_1.SetStringSelection(self.WATCH_FRAME_TYPES[self._watch_frame_type])

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(self.label_2, 0, wx.ALL, 0)
        lineSizer.Add(self._watchNameTextCtrl, 1, wx.EXPAND|wx.LEFT, HALF_SPACE)
        sizer_1.Add(lineSizer, 0, wx.EXPAND|wx.ALL, HALF_SPACE)
        sizer_1.Add(self.label_3, 0, wx.LEFT, HALF_SPACE)
        sizer_1.Add(self._watchValueTextCtrl, 1, wx.EXPAND|wx.ALL, HALF_SPACE)
        sizer_1.Add(self.radio_box_1, 0, wx.EXPAND|wx.ALL, HALF_SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        #set ok button default focused
        self._okButton.SetDefault()
        bsizer.AddButton(self._okButton)
        bsizer.AddButton(self._cancelButton)
        bsizer.Realize()
        sizer_1.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        
        self.SetSizer(sizer_1)
        self.Fit()
        
    def SetNameValue(self,event):
        if self._is_quick_watch:
            self._watchValueTextCtrl.SetValue(self._watchNameTextCtrl.GetValue())

class WatchsPanel(ttk.Frame):
    """description of class"""
    ID_ClEAR_WATCH = NewId()
    ID_ClEAR_ALL_WATCH = NewId()
    ID_EDIT_WATCH = NewId()
    ID_COPY_WATCH_EXPRESSION = NewId()
    WATCH_NAME_COLUMN_WIDTH = 150
    
    def __init__(self,parent,id,debuggerService):
        wx.Panel.__init__(self, parent, id)
        self._debugger_service = debuggerService
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self._treeCtrl = wx.gizmos.TreeListCtrl(self, -1, style=wx.TR_DEFAULT_STYLE| wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_HIDE_ROOT)
        self._treeCtrl.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        panel_sizer.Add(self._treeCtrl,1, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 1)
        tree = self._treeCtrl
        tree.AddColumn(_("Name"))
        tree.AddColumn(_("Value"))
        tree.SetMainColumn(0) # the one with the tree in it...
        tree.SetColumnWidth(0, self.WATCH_NAME_COLUMN_WIDTH)
        tree.SetColumnWidth(1, 300)
        
        iconList = wx.ImageList(16, 16, 3)
        error_bmp = images.load("debugger/error.png")
        self.ErrorIndex = iconList.Add(error_bmp)
        watch_expr_bmp = images.load("debugger/watch_exp.png")
        self.WatchExprIndex = iconList.Add(watch_expr_bmp)
        self._treeCtrl.AssignImageList(iconList)
        
        self._root = tree.AddRoot("Expression")
        
        self.SetSizer(panel_sizer)
        self.Fit()
        self.LoadWatches()
        
    def OnRightClick(self, event):
        #Refactor this...
        self._introspectItem = event.GetItem()
        self._parentChain = self.GetItemChain(event.GetItem())
        watchOnly = len(self._parentChain) < 1
        #if not _WATCHES_ON and watchOnly:
         #   return
        menu = wx.Menu()

        if not hasattr(self, "watchID"):
            self.watchID = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnAddWatch, id=self.watchID)
        item = wx.MenuItem(menu, self.watchID, _("Add a Watch"))
        item.SetBitmap(getAddWatchBitmap())
        menu.AppendItem(item)
        menu.AppendSeparator()
        if not watchOnly:
            if not hasattr(self, "viewID"):
                self.viewID = wx.NewId()
                self.Bind(wx.EVT_MENU, self.OnView, id=self.viewID)
            item = wx.MenuItem(menu, self.viewID, _("View in Dialog"))
            menu.AppendItem(item)
            
        item = wx.MenuItem(menu, self.ID_EDIT_WATCH, _("Edit Watch"))
        self.Bind(wx.EVT_MENU, self.EditWatch, id=self.ID_EDIT_WATCH)
        menu.AppendItem(item)
        
        item = wx.MenuItem(menu, self.ID_COPY_WATCH_EXPRESSION, _("Copy Watch Expression"))
        self.Bind(wx.EVT_MENU, self.CopyWatchExpression, id=self.ID_COPY_WATCH_EXPRESSION)
        menu.AppendItem(item)
            
        item = wx.MenuItem(menu, self.ID_ClEAR_WATCH, _("Clear"))
        item.SetBitmap(getClearWatchBitmap())
        self.Bind(wx.EVT_MENU, self.ClearWatch, id=self.ID_ClEAR_WATCH)
        menu.AppendItem(item)
        
        item = wx.MenuItem(menu, self.ID_ClEAR_ALL_WATCH, _("Clear All"))
        self.Bind(wx.EVT_MENU, self.ClearAllWatch, id=self.ID_ClEAR_ALL_WATCH)
        menu.AppendItem(item)

        offset = wx.Point(x=0, y=20)
        menuSpot = event.GetPoint() + offset
        self._treeCtrl.PopupMenu(menu, menuSpot)
        menu.Destroy()
        self._parentChain = None
        self._introspectItem = None
        

    def AppendSubTreeFromNode(self, node, name, parent, insertBefore=None):
        tree = self._treeCtrl
        if insertBefore != None:
            treeNode = tree.InsertItem(parent, insertBefore, name)
        else:
            treeNode = tree.AppendItem(parent, name)
        self._treeCtrl.SetItemImage(treeNode,self.WatchExprIndex)
        children = node.childNodes
        intro = node.getAttribute('intro')

        if intro == "True":
            tree.SetItemHasChildren(treeNode, True)
            tree.SetPyData(treeNode, "Introspect")
        if node.getAttribute("value"):
            tree.SetItemText(treeNode, self.StripOuterSingleQuotes(node.getAttribute("value")), 1)
        for index in range(0, children.length):
            subNode = children.item(index)
            if self.HasChildren(subNode):
                self.AppendSubTreeFromNode(subNode, subNode.getAttribute("name"), treeNode)
            else:
                name = subNode.getAttribute("name")
                value = self.StripOuterSingleQuotes(subNode.getAttribute("value"))
                n = tree.AppendItem(treeNode, name)
                tree.SetItemText(n, value, 1)
                intro = subNode.getAttribute('intro')
                if intro == "True":
                    tree.SetItemHasChildren(n, True)
                    tree.SetPyData(n, "Introspect")
        if name.find('[') == -1:
            self._treeCtrl.SortChildren(treeNode)
        return treeNode

    def StripOuterSingleQuotes(self, string):
        if string.startswith("'") and string.endswith("'"):
            retval =  string[1:-1]
        elif string.startswith("\"") and string.endswith("\""):
            retval = string[1:-1]
        else:
            retval = string
        if retval.startswith("u'") and retval.endswith("'"):
            retval = retval[1:]
        return retval
        
    def HasChildren(self, node):
        try:
            return node.childNodes.length > 0
        except:
            tp,val,tb=sys.exc_info()
            return False
            
    def GetItemChain(self, item):
        parentChain = []
        if item:
            utils.GetLogger().debug('Exploding: %s' , self._treeCtrl.GetItemText(item, 0))
            while item != self._root:
                text = self._treeCtrl.GetItemText(item, 0)
                utils.GetLogger().debug("Appending %s", text)
                parentChain.append(text)
                item = self._treeCtrl.GetItemParent(item)
            parentChain.reverse()
        return parentChain
        
    def OnAddWatch(self,event):
        self._debugger_service._debugger_ui.OnAddWatch(event)
        
    def OnView(self,event):
        title = self._treeCtrl.GetItemText(self._introspectItem,0)
        value = self._treeCtrl.GetItemText(self._introspectItem,1)
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, value, title, style=wx.DD_DEFAULT_STYLE | wx.RESIZE_BORDER)
        dlg.Show()
        
    def ClearWatch(self,event):
        watch_obj = self.GetItemWatchObj(self._introspectItem)
        self._debugger_service.watchs.remove(watch_obj)
        self._treeCtrl.Delete(self._introspectItem)
        self.UpdateItemData()
        
    def ClearAllWatch(self,event):
        self._treeCtrl.DeleteAllItems()
        self._debugger_service.watchs = []
        #recreate root item
        self._root = self._treeCtrl.AddRoot("Expression")
        
    def EditWatch(self,event):
        watch_obj = self.GetItemWatchObj(self._introspectItem)
        index = self._treeCtrl.GetPyData(self._introspectItem)
        wd = WatchDialog(wx.GetApp().GetTopWindow(), _("Edit a Watch"), None,watch_obj=watch_obj)
        wd.CenterOnParent()
        if wd.ShowModal() == wx.ID_OK:
            watch_obj = wd.GetSettings()
            self._treeCtrl.SetItemText(self._introspectItem, watch_obj.Name, 0)
            self._debugger_service._debugger_ui.UpdateWatch(watch_obj,self._introspectItem)
            self._debugger_service.watchs[index] = watch_obj
        
    def CopyWatchExpression(self,event):
        title = self._treeCtrl.GetItemText(self._introspectItem,0)
        value = self._treeCtrl.GetItemText(self._introspectItem,1)
        sysutils.CopyToClipboard(title + "\t" + value)
        
    def LoadWatches(self):
        watchs = self._debugger_service.watchs
        root_item = self._treeCtrl.GetRootItem()
        for i,watch_obj in enumerate(watchs):
            treeNode = self._treeCtrl.AppendItem(root_item, watch_obj.Name)
            self._treeCtrl.SetItemText(treeNode, ERROR_NAME_VALUE, 1)
            self._treeCtrl.SetItemImage(treeNode,self.ErrorIndex)
            self._treeCtrl.SetPyData(treeNode, i)

    def UpdateWatchs(self):
        root_item = self._treeCtrl.GetRootItem()
        (item, cookie) = self._treeCtrl.GetFirstChild(root_item)
        while item:
            name = self._treeCtrl.GetItemText(item)
            watch_obj = self.GetItemWatchObj(item)
            self._debugger_service._debugger_ui.UpdateWatch(watch_obj,item)
            (item, cookie) = self._treeCtrl.GetNextChild(root_item, cookie)
            
    def UpdateSubTreeFromNode(self, node, name, item):
        tree = self._treeCtrl
        children = node.childNodes
        intro = node.getAttribute('intro')
        treeNode = item
        self.DeleteItemChild(treeNode)
        self._treeCtrl.SetItemImage(treeNode,self.WatchExprIndex)
        if intro == "True":
            tree.SetItemHasChildren(treeNode, True)
            tree.SetPyData(treeNode, "Introspect")
        if node.getAttribute("value"):
            tree.SetItemText(treeNode, self.StripOuterSingleQuotes(node.getAttribute("value")), 1)
        for index in range(0, children.length):
            subNode = children.item(index)
            if self.HasChildren(subNode):
                self.AppendSubTreeFromNode(subNode, subNode.getAttribute("name"), treeNode)
            else:
                name = subNode.getAttribute("name")
                value = self.StripOuterSingleQuotes(subNode.getAttribute("value"))
                n = tree.AppendItem(treeNode, name)
                tree.SetItemText(n, value, 1)
                intro = subNode.getAttribute('intro')
                if intro == "True":
                    tree.SetItemHasChildren(n, True)
                    tree.SetPyData(n, "Introspect")
        if name.find('[') == -1:
            self._treeCtrl.SortChildren(treeNode)
        return treeNode
        
    def ResetWatchs(self):
        root_item = self._treeCtrl.GetRootItem()
        (item, cookie) = self._treeCtrl.GetFirstChild(root_item)
        while item:
            name = self._treeCtrl.GetItemText(item)
            self.DeleteItemChild(item)
            self._treeCtrl.SetItemText(item, ERROR_NAME_VALUE, 1)
            self._treeCtrl.SetItemImage(item,self.ErrorIndex)
            (item, cookie) = self._treeCtrl.GetNextChild(root_item, cookie)
            
    def DeleteItemChild(self,item):
        if self._treeCtrl.ItemHasChildren(item):
            self._treeCtrl.DeleteChildren(item)
            
    def AppendErrorWatch(self,  watch_obj, parent):
        treeNode = self._treeCtrl.AppendItem(parent, watch_obj.Name)
        self._treeCtrl.SetItemImage(treeNode,self.ErrorIndex)
        self._treeCtrl.SetItemText(treeNode, ERROR_NAME_VALUE, 1)
        self._debugger_service.AppendWatch(watch_obj)
        self.SetItemPyData(treeNode,watch_obj)
        
    def UpdateWatch(self, node, watch_obj, treeNode):
        self.UpdateSubTreeFromNode(node,watch_obj.Name,treeNode)
            
    def AddWatch(self, node, watch_obj, parent, insertBefore=None):
        treeNode = self.AppendSubTreeFromNode(node,watch_obj.Name,parent,insertBefore)
        self._debugger_service.AppendWatch(watch_obj)
        self.SetItemPyData(treeNode,watch_obj)
        
    def SetItemPyData(self,treeItem,watch_obj):
        watch_count = len(self._debugger_service.watchs) - 1
        self._treeCtrl.SetPyData(treeItem, watch_count)
        
    def GetItemWatchObj(self,treeItem):
        index = self._treeCtrl.GetPyData(treeItem)
        watch_obj = self._debugger_service.watchs[index]
        return watch_obj
        
    def UpdateItemData(self):
        root_item = self._treeCtrl.GetRootItem()
        (item, cookie) = self._treeCtrl.GetFirstChild(root_item)
        i = 0
        while item:
            self._treeCtrl.SetPyData(item, i)
            (item, cookie) = self._treeCtrl.GetNextChild(root_item, cookie)
            i += 1
        