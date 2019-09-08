# -*- coding: utf-8 -*-
from noval import GetApp,_,NewId
import noval.util.apputils as sysutils
import noval.iface as iface
import noval.plugin as plugin
import noval.ui_base as ui_base
from tkinter import ttk,messagebox
import tkinter as tk
import noval.util.utils as utils
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.imageutils as imageutils
import noval.editor.text as texteditor
import noval.consts as consts
import noval.menu as tkmenu
import noval.constants as constants
from noval.python.parser.utils import py_sorted,py_cmp
import noval.ttkwidgets.messagedialog as messagedialog
import bz2
from xml.dom.minidom import parseString

ERROR_NAME_VALUE = "<errors:could not evaluate the value>"


def getAddWatchBitmap():
    return GetApp().GetImage("python/debugger/newWatch.png")

def getQuickAddWatchBitmap():
    return GetApp().GetImage("python/debugger/watch.png")
    
def getAddtoWatchBitmap():
    return GetApp().GetImage("python/debugger/addToWatch.png")
    
def getClearWatchBitmap():
    return GetApp().GetImage("python/debugger/delete.png")
    

class CommonWatcher:
    def GetItemIndex(self,parent,item):
        children = self.tree.get_children(parent)
        for i,child in enumerate(children):
            if child == item:
                return i
        return "end"
        
    def AppendSubTreeFromNode(self, node, name, parent, insertBefore=None):
        if insertBefore != None:
            index = self.GetItemIndex(parent,insertBefore)
            treeNode = self.tree.insert(parent, index, text=name)
        else:
            treeNode = self.tree.insert(parent,"end",text=name)
        return self.UpdateSubTreeFromNode(node,name,treeNode)
        
    def UpdateSubTreeFromNode(self, node, name, treeNode):
        '''
            单步调试过程中,不断更新监视节点的值
        '''
        tree = self.tree
        children = node.childNodes
        intro = node.getAttribute('intro')
        if intro == "True":
            #这些节点只有展开时才能实时获取监视值
            self.SetItemHasChildren(treeNode)
            self.SetPyData(treeNode, "Introspect")
        if node.getAttribute("value"):
            tree.set(treeNode, column='Value', value=self.StripOuterSingleQuotes(node.getAttribute("value")))
        for index in range(0, children.length):
            subNode = children.item(index)
            if self.HasChildren(subNode):
                self.AppendSubTreeFromNode(subNode, subNode.getAttribute("name"), treeNode)
            else:
                name = subNode.getAttribute("name")
                value = self.StripOuterSingleQuotes(subNode.getAttribute("value"))
                n = tree.insert(treeNode, "end",text=name)
                tree.set(n, value=value, column='Value')
                intro = subNode.getAttribute('intro')
                if intro == "True":
                    #这些节点只有展开时才能实时获取监视值
                    self.SetItemHasChildren(n)
                    self.SetPyData(n, "Introspect")
        if name.find('[') == -1:
            self.SortChildren(treeNode)
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

    def SortChildren(self,node):
        # update tree
        children = self.tree.get_children(node)
        ids_sorted_by_name = py_sorted(children, cmp_func=self.OnCompareItems)
        self.tree.set_children(node, *ids_sorted_by_name)
        
    def OnCompareItems(self, item1, item2):
        return py_cmp(self.tree.item(item1,"text").lower(), self.tree.item(item2,"text").lower())
        
    def SetPyData(self,item,data):
        self.tree.set(item, value=data, column='Hide')
        
    def GetPyData(self,item):
        return self.tree.item(item)['values'][1]
        
    def SetItemHasChildren(self,item):
        self.tree.insert(item,"end",text="")
        
    def GetItemChain(self, item):
        parentChain = []
        if item:
            utils.get_logger().debug('Exploding: %s' , self.tree.item(item,"text"))
            while item != self._root and item:
                text = self.tree.item(item,"text")
                utils.get_logger().debug("Appending %s,item is %s", text,item)
                parentChain.append(text)
                item = self.tree.parent(item)
            parentChain.reverse()
        return parentChain

    def ViewExpression(self,item):
        title = self.tree.item(item,"text")
        value = self.tree.item(item,"values")[0]
        dlg = messagedialog.ScrolledMessageDialog(GetApp().GetTopWindow(),title, value)
        dlg.ShowModal()
        
    def IntrospectCallback(self, is_watch=False):
        '''
            展开节点时实时获取节点的所有子节点的值
        '''
        item = self.tree.selection()[0]
        if is_watch:
            panel = "watchs"
        else:
            panel = "statckframe"
        utils.get_logger().debug("In %s introspectCallback item is %s, pydata is %s" , panel,item, self.GetPyData(item))
        if self.GetPyData(item) != "Introspect":
            return
        self._introspectItem = item
        self._parentChain = self.GetItemChain(item)
        self.OnIntrospect()

    def OnIntrospect(self):
        GetApp().configure(cursor="circle")
        try:
            try:
                frameNode = self.GetFrameNode()
                message = frameNode.getAttribute("message")
                binType = GetApp().GetDebugger()._debugger_ui.framesTab.attempt_introspection(message, self._parentChain)
                xmldoc = bz2.decompress(binType.data)
                domDoc = parseString(xmldoc)
                nodeList = domDoc.getElementsByTagName('replacement')
                replacementNode = nodeList.item(0)
                if len(replacementNode.childNodes):
                    thingToWalk = replacementNode.childNodes.item(0)
                    tree = self.tree
                    parent = tree.parent(self._introspectItem)
                    treeNode = self.AppendSubTreeFromNode(thingToWalk, thingToWalk.getAttribute('name'), parent, insertBefore=self._introspectItem)
                    if thingToWalk.getAttribute('name').find('[') == -1:
                        self.SortChildren(treeNode)
                    tree.item(treeNode,open=True)
                    tree.delete(self._introspectItem)
            except:
                utils.get_logger().exception('')

        finally:
            GetApp().configure(cursor="")
            
    def GetFrameNode(self):
        assert False, "GetFrameNode not overridden"

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
    def CreateWatch(name,expression):
        return Watch(name,expression)
        
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
        utils.profile_set(cls.WATCH_LIST_KEY, watch_list)
        
    @classmethod
    def Load(cls):
        watch_list = utils.profile_get(cls.WATCH_LIST_KEY,[])
        watchs = []
        for dct in watch_list:
            watch = Watch(dct[cls.NAME_KEY],dct[cls.EXPERSSION_KEY],dct.get(cls.SHOW_CODE_FRAME_KEY,cls.CODE_ALL_FRAMES))
            watchs.append(watch)
        return watchs

class WatchDialog(ui_base.CommonModaldialog):
    WATCH_ALL_FRAMES = "Watch in all frames"
    WATCH_THIS_FRAME = "Watch in this frame only"
    WATCH_ONCE = "Watch once and delete"
    def __init__(self, parent, title, chain,is_quick_watch=False,watch_obj=None):
        ui_base.CommonModaldialog.__init__(self, parent)
        self.title(title)
        self._chain = chain
        self._is_quick_watch = is_quick_watch
        self._watch_obj = watch_obj
        self._watch_frame_type = Watch.CODE_ALL_FRAMES
        row = ttk.Frame(self.main_frame)
        ttk.Label(row,text=_("Watch Name:")).pack(fill="x",side=tk.LEFT)
        self.nameVar = tk.StringVar()
        self._watchNameTextCtrl = ttk.Entry(row,textvariable=self.nameVar)
        self._watchNameTextCtrl.pack(fill="x",side=tk.LEFT,expand=1)
        row.pack(fill="x")
        self.nameVar.trace("w", self.SetNameValue)
        ttk.Label(self.main_frame, text=_("Expression:")).pack(fill="x")
        self._watchValueTextCtrl = texteditor.TextCtrl(self.main_frame)
        self._watchValueTextCtrl.pack(fill="both",expand=1)
        if is_quick_watch:
            self._watchValueTextCtrl['state'] = tk.DISABLED
        sbox_frame = ttk.LabelFrame(self.main_frame, text=_("Watch Information"))
        self.watchVar = tk.IntVar(value=Watch.CODE_ALL_FRAMES)
        ttk.Radiobutton(sbox_frame, variable=self.watchVar,value=Watch.CODE_ALL_FRAMES,text = WatchDialog.WATCH_ALL_FRAMES).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        ttk.Radiobutton(sbox_frame, variable=self.watchVar,value=Watch.CODE_THIS_LINE,text = WatchDialog.WATCH_THIS_FRAME).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        ttk.Radiobutton(sbox_frame, variable=self.watchVar,value=Watch.CODE_RUN_ONCE,text = WatchDialog.WATCH_ONCE).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        sbox_frame.pack(fill="x")
        
        self.AddokcancelButton()
        self.__set_properties()

    def GetSettings(self):
        watch_code_frame = self.watchVar.get()
        return Watch(self.nameVar.get(),self.expresstion,watch_code_frame)

    def GetSendFrame(self):
        return (WatchDialog.WATCH_ALL_FRAMES != self.radio_box_1.GetStringSelection())

    def GetRunOnce(self):
        return (WatchDialog.WATCH_ONCE == self.radio_box_1.GetStringSelection())

    def __set_properties(self):
        if self._watch_obj is not None:
            self._watch_frame_type = self._watch_obj.ShowCodeFrame
            self.nameVar.set(self._watch_obj.Name)
            self._watchValueTextCtrl.AddText(self._watch_obj.Expression)
        self.watchVar.set(self._watch_frame_type)
        
    def SetNameValue(self,*args):
        if self._is_quick_watch:
            self._watchValueTextCtrl['state'] = tk.NORMAL
            self._watchValueTextCtrl.set_content(self.nameVar.get())
            self._watchValueTextCtrl['state'] = tk.DISABLED
            
    def _ok(self,event=None):
        if self.nameVar.get().strip() == "":
            messagebox.showinfo( _("Add a Watch"),_("You must enter a name for the watch."))
            return
        if self._watchValueTextCtrl.GetValue() == "":
            messagebox.showinfo(_("Add a Watch"),_("You must enter some code to run for the watch."))
            return
        self.expresstion = self._watchValueTextCtrl.GetValue()
        ui_base.CommonModaldialog._ok(self)

class WatchsPanel(treeviewframe.TreeViewFrame,CommonWatcher):
    """description of class"""
    ID_ClEAR_WATCH = NewId()
    ID_ClEAR_ALL_WATCH = NewId()
    ID_EDIT_WATCH = NewId()
    ID_COPY_WATCH_EXPRESSION = NewId()
    WATCH_NAME_COLUMN_WIDTH = 150
    ID_VIEW_WATCH = NewId()
    
    def __init__(self,parent):
        treeviewframe.TreeViewFrame.__init__(self, parent,columns= ['Value','Hide'],displaycolumns=(0,))
      
        self.tree.heading("#0", text=_("Name"), anchor=tk.W)
        self.tree.heading("Value", text=_("Value"), anchor=tk.W)
            
        self.tree.column('#0',width=80,anchor='w')
        self.tree["show"] = ("headings", "tree")
        
        self.error_bmp = imageutils.load_image("","python/debugger/error.png")
        self.watch_expr_bmp = imageutils.load_image("","python/debugger/watch_exp.png")
        
        self._root = None
        self.ShowRoot()
        self.tree.bind("<3>", self.OnRightClick, True)
        self.watchs = Watch.Load()
        self.LoadWatches()
        self.menu = None
        self.tree.bind("<<TreeviewOpen>>", self.IntrospectCallback)

    def IntrospectCallback(self, event):
        '''
            展开节点时实时获取节点的所有子节点的值
        '''
        CommonWatcher.IntrospectCallback(self,True)
        
    def ShowRoot(self,show=True):
        if show:
            self._root = self.tree.insert("","end",text="Expression")
        else:
            if self._root is not None:
                self._clear_tree()
                self._root = None

    def SaveWatchs(self):
        Watch.Dump(self.watchs)        
        
    def OnRightClick(self, event):
        if not self.tree.selection():
            return
        #Refactor this...
        sel_items = self.tree.selection()
        self._introspectItem = None
        if sel_items:
            self._introspectItem = sel_items[0]
        self._parentChain = self.GetItemChain(self._introspectItem)
        watchOnly = len(self._parentChain) < 1
        #if not _WATCHES_ON and watchOnly:
         #   return
        if self.menu is None:
            self.menu = tkmenu.PopupMenu()

    #    if not hasattr(self, "watchID"):
     #       self.watchID = wx.NewId()
      #      self.Bind(wx.EVT_MENU, self.OnAddWatch, id=self.ID_ADD_WATCH)
            item = tkmenu.MenuItem(constants.ID_ADD_WATCH, _("Add a Watch"),None,getAddWatchBitmap(),None)
            self.menu.AppendMenuItem(item,handler=self.OnAddWatch)
            #menu.AppendSeparator()
            if not watchOnly:
                item = tkmenu.MenuItem(self.ID_VIEW_WATCH, _("View in Dialog"),None,None,None)
                self.menu.AppendMenuItem(item,handler=self.OnView)
                
            item = tkmenu.MenuItem(self.ID_EDIT_WATCH, _("Edit Watch"),None,None,None)
            self.menu.AppendMenuItem(item,handler=self.EditWatch)
            
            item = tkmenu.MenuItem(self.ID_COPY_WATCH_EXPRESSION, _("Copy Watch Expression"),None,None,None)
            self.menu.AppendMenuItem(item,handler=self.CopyWatchExpression)
                
            item = tkmenu.MenuItem(self.ID_ClEAR_WATCH, _("Clear"),None,getClearWatchBitmap(),None)
            self.menu.AppendMenuItem(item,handler=self.ClearWatch)
            
            item = tkmenu.MenuItem(self.ID_ClEAR_ALL_WATCH, _("Clear All"),None,None,None)
            self.menu.AppendMenuItem(item,handler=self.ClearAllWatch)

        self.menu.tk_popup(event.x_root, event.y_root)
      #  self._parentChain = None
       # self._introspectItem = None
        
    def OnAddWatch(self):
        if GetApp().GetDebugger()._debugger_ui is None:
            messagebox.showinfo(GetApp().GetAppName(),_("Debugger has been stopped."))
            return
        GetApp().GetDebugger()._debugger_ui.OnAddWatch()
        
    def ClearWatch(self):
        watch_obj = self.GetItemWatchData(self._introspectItem)
        self.watchs.remove(watch_obj)
        self.tree.delete(self._introspectItem)
        
    def _clear_tree(self):
        for child_id in self.tree.get_children():
            self.tree.delete(child_id)
            
    def OnView(self):
        self.ViewExpression(self._introspectItem)
        
    def ClearAllWatch(self):
        self._clear_tree()
        GetApp().GetDebugger()._debugger_ui.watchs = []
        self.ShowRoot(True)
        
    def EditWatch(self):
        watch_data = self.GetItemWatchData(self._introspectItem)
        index = self.GetWatchItemIndex(self._introspectItem)
        wd = WatchDialog(GetApp().GetTopWindow(), _("Edit a Watch"), None,watch_obj=watch_data)
        if wd.ShowModal() == constants.ID_OK:
            watch_obj = wd.GetSettings()
            self.item(self._introspectItem, text=watch_data.Name)
            GetApp().GetDebugger()._debugger_ui.UpdateWatch(watch_obj,self._introspectItem)
            GetApp().GetDebugger().watchs[index] = watch_obj
        
    def CopyWatchExpression(self):
        title = self.tree.item(self._introspectItem,"text")
        value = self.tree.item(self._introspectItem,"values")[0]
        utils.CopyToClipboard(title + "\t" + value)
        
    def LoadWatches(self):
        '''
            初始化监视点时调试器关闭,值是不可预测的
        '''
        self.ShowRoot(False)
        for i,watch_data in enumerate(self.watchs):
            treeNode = self.tree.insert("","end",text=watch_data.Name,image=self.error_bmp)
            self.tree.set(treeNode, value=ERROR_NAME_VALUE, column='Value')

    def UpdateWatchs(self):
        root_item = self.GetRootItem()
        childs = self.tree.get_children(root_item)
        for item in childs:
            watch_data = self.GetItemWatchData(item)
            GetApp().GetDebugger()._debugger_ui.UpdateWatch(watch_data,item)
            
    def UpdateSubTreeFromNode(self, node, name, item):
        self.DeleteItemChild(item)
        self.tree.item(item,image=self.watch_expr_bmp)
        return CommonWatcher.UpdateSubTreeFromNode(self,node,name,item)
        
    def GetRootItem(self):
        return self._root
        
    def ResetWatchs(self):
        root_item = self.GetRootItem()
        childs = self.tree.get_children(root_item)
        for item in childs:
            self.DeleteItemChild(item)
            self.tree.set(item, value=ERROR_NAME_VALUE, column='Value')
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
        if parent == self._root:
            parent = ""
        self.ShowRoot(False)
        treeNode = self.AppendSubTreeFromNode(node,watch_obj.Name,parent,insertBefore)
        self.watchs.append(watch_obj)

    def GetItemWatchData(self,treeItem):
        index = self.GetWatchItemIndex(treeItem)
        watch_data = self.watchs[index]
        return watch_data

    def GetWatchItemIndex(self,item):
        childs = self.tree.get_children()
        for i,child in enumerate(childs):
            if child == item:
                return i
        assert(False)

    def GetFrameNode(self):
        return GetApp().GetDebugger()._debugger_ui.framesTab.stackFrameTab.GetFrameNode()

class WatchsViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(consts.WATCH_TAB_NAME,WatchsPanel, _("Watchs"), "ne",image_file="python/debugger/watches.png")
        