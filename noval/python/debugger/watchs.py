from noval import GetApp,_,NewId
import noval.util.apputils as sysutils
import noval.iface as iface
import noval.plugin as plugin
import noval.ui_base as ui_base
from tkinter import ttk
import tkinter as tk
import noval.util.utils as utils
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.imageutils as imageutils
import noval.editor.text as texteditor
import noval.consts as consts
import noval.menu as tkmenu

ERROR_NAME_VALUE = "<errors:could not evaluate the value>"
WATCH_TAB_NAME = "Watchs"

def getAddWatchBitmap():
    return GetApp().GetImage("python/debugger/newWatch.png")

def getQuickAddWatchBitmap():
    return GetApp().GetImage("python/debugger/watch.png")
    
def getAddtoWatchBitmap():
    return GetApp().GetImage("python/debugger/addToWatch.png")
    
def getClearWatchBitmap():
    return GetApp().GetImage("python/debugger/delete.png")

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
        ui_base.CommonModaldialog.__init__(self, parent)
        self.title(title)
        self._chain = chain
        self._is_quick_watch = is_quick_watch
        self._watch_obj = watch_obj
        self._watch_frame_type = Watch.CODE_ALL_FRAMES
        row = ttk.Frame(self.main_frame)
        ttk.Label(row,text=_("Watch Name:")).pack(fill="x",side=tk.LEFT)
        self._watchNameTextCtrl = ttk.Entry(row)
        self._watchNameTextCtrl.pack(fill="x",side=tk.LEFT,expand=1)
        row.pack(fill="x")
       # self._watchNameTextCtrl.Bind(wx.EVT_TEXT,self.SetNameValue)
        ttk.Label(self.main_frame, text=_("Expression:")).pack(fill="x")
        self._watchValueTextCtrl = texteditor.TextCtrl(self.main_frame)
        self._watchValueTextCtrl.pack(fill="both",expand=1)
        if is_quick_watch:
            self._watchValueTextCtrl['state'] = tk.DISABLED
      #  self.radio_box_1 = ttk.Radiobutton(self, text=_("Watch Information"), choices=[WatchDialog.WATCH_ALL_FRAMES, WatchDialog.WATCH_THIS_FRAME, WatchDialog.WATCH_ONCE], majorDimension=0, style=wx.RA_SPECIFY_ROWS)

        sbox_frame = ttk.LabelFrame(self.main_frame, text=_("Watch Information"))
        self.watchallVar = tk.IntVar(value=False)
        ttk.Radiobutton(sbox_frame, variable=self.watchallVar,text = WatchDialog.WATCH_ALL_FRAMES).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        self.watchthisVar = tk.IntVar(value=False)
        ttk.Radiobutton(sbox_frame, variable=self.watchthisVar,text = WatchDialog.WATCH_THIS_FRAME).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.watchonceVar = tk.IntVar(value=False)
        ttk.Radiobutton(sbox_frame, variable=self.watchonceVar,text = WatchDialog.WATCH_ONCE).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        sbox_frame.pack(fill="x")
        
        self.AddokcancelButton()
        #self.__set_properties()

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
        
    def SetNameValue(self,event):
        if self._is_quick_watch:
            self._watchValueTextCtrl.SetValue(self._watchNameTextCtrl.GetValue())
            

    def _ok(self,event=None):
        if self._watchNameTextCtrl.GetValue() == "":
            wx.MessageBox(_("You must enter a name for the watch."), _("Add a Watch"))
            return
        if self._watchValueTextCtrl.GetValue() == "":
            wx.MessageBox(_("You must enter some code to run for the watch."), _("Add a Watch"))
            return
        self.EndModal(wx.ID_OK)

class WatchsPanel(treeviewframe.TreeViewFrame):
    """description of class"""
    ID_ClEAR_WATCH = NewId()
    ID_ClEAR_ALL_WATCH = NewId()
    ID_EDIT_WATCH = NewId()
    ID_COPY_WATCH_EXPRESSION = NewId()
    WATCH_NAME_COLUMN_WIDTH = 150
    
    def __init__(self,parent):
        treeviewframe.TreeViewFrame.__init__(self, parent,columns= ['Value'],displaycolumns=(0,))
      
        self.tree.heading("#0", text=_("Name"), anchor=tk.W)
        self.tree.heading("Value", text=_("Value"), anchor=tk.W)
            
        self.tree.column('#0',width=80,anchor='w')
        self.tree["show"] = ("headings", "tree")
        
        self.error_bmp = imageutils.load_image("","python/debugger/error.png")
        self.watch_expr_bmp = imageutils.load_image("","python/debugger/watch_exp.png")
        
        self._root = self.tree.insert("","end",text="Expression")
        self.tree.bind("<3>", self.OnRightClick, True)
        #self.LoadWatches()
        
    def OnRightClick(self, event):
        #Refactor this...
        sel_items = self.tree.selection()
        self._introspectItem = None
        if sel_items:
            self._introspectItem = sel_items[0]
        self._parentChain = self.GetItemChain(self._introspectItem)
        watchOnly = len(self._parentChain) < 1
        #if not _WATCHES_ON and watchOnly:
         #   return
        menu = tkmenu.PopupMenu()

        if not hasattr(self, "watchID"):
            self.watchID = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnAddWatch, id=self.watchID)
        item = tkmenu.MenuItem(menu, self.watchID, _("Add a Watch"))
        item.SetBitmap(getAddWatchBitmap())
        menu.AppendItem(item)
        menu.AppendSeparator()
        if not watchOnly:
            if not hasattr(self, "viewID"):
                self.viewID = wx.NewId()
                self.Bind(wx.EVT_MENU, self.OnView, id=self.viewID)
            item = tkmenu.MenuItem(menu, self.viewID, _("View in Dialog"))
            menu.AppendItem(item)
            
        item = tkmenu.MenuItem(menu, self.ID_EDIT_WATCH, _("Edit Watch"))
        self.Bind(wx.EVT_MENU, self.EditWatch, id=self.ID_EDIT_WATCH)
        menu.AppendItem(item)
        
        item = tkmenu.MenuItem(menu, self.ID_COPY_WATCH_EXPRESSION, _("Copy Watch Expression"))
        self.Bind(wx.EVT_MENU, self.CopyWatchExpression, id=self.ID_COPY_WATCH_EXPRESSION)
        menu.AppendItem(item)
            
        item = tkmenu.MenuItem(menu, self.ID_ClEAR_WATCH, _("Clear"))
        item.SetBitmap(getClearWatchBitmap())
        self.Bind(wx.EVT_MENU, self.ClearWatch, id=self.ID_ClEAR_WATCH)
        menu.AppendItem(item)
        
        item = tkmenu.MenuItem(menu, self.ID_ClEAR_ALL_WATCH, _("Clear All"))
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
            utils.get_logger().debug('Exploding: %s' , self._treeCtrl.GetItemText(item, 0))
            while item != self._root:
                text = self._treeCtrl.GetItemText(item, 0)
                utils.get_logger().debug("Appending %s", text)
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
        watchs = GetApp().GetDebugger().watchs
        root_item = self.GetRootItem()
        for i,watch_data in enumerate(watchs):
            treeNode = self._treeCtrl.AppendItem(root_item, watch_data.Name)
            self._treeCtrl.SetItemText(treeNode, ERROR_NAME_VALUE, 1)
            self._treeCtrl.SetItemImage(treeNode,self.ErrorIndex)
            self._treeCtrl.SetPyData(treeNode, i)

    def UpdateWatchs(self):
        root_item = self.GetRootItem()
        childs = self.tree.get_children(root_item)
        for item in childs:
            watch_data = self.GetItemWatchData(item)
            self._debugger_service._debugger_ui.UpdateWatch(watch_data,item)
            
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
        
    def GetRootItem(self):
        childs = self.tree.get_children()
        return childs[0]
        
    def ResetWatchs(self):
        root_item = self.GetRootItem()
        childs = self.tree.get_children(root_item)
        for item in childs:
            self.DeleteItemChild(item)
            self.tree.item(item, text=ERROR_NAME_VALUE)
            self.tree.item(item, image=self.error_bmp)
            
    def DeleteItemChild(self,item):
        childs = self.tree.get_children(item)
        if childs:
            for child in childs:
                self.tree.delete(child)
            
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
        
    def GetItemWatchData(self,treeItem):
        index = self._treeCtrl.GetPyData(treeItem)
        watch_data = self._debugger_service.watchs[index]
        return watch_data
        
    def UpdateItemData(self):
        root_item = self._treeCtrl.GetRootItem()
        (item, cookie) = self._treeCtrl.GetFirstChild(root_item)
        i = 0
        while item:
            self._treeCtrl.SetPyData(item, i)
            (item, cookie) = self._treeCtrl.GetNextChild(root_item, cookie)
            i += 1
            

class WatchsViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(WATCH_TAB_NAME,WatchsPanel, _("Watchs"), "ne",image_file="python/debugger/watches.png")
        