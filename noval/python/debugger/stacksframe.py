from noval import GetApp,_
import noval.iface as iface
import noval.plugin as plugin
from tkinter import ttk
import tkinter as tk
import noval.ttkwidgets.treeviewframe as treeviewframe
from noval.python.parser.utils import py_sorted,py_cmp

STACKFRAME_TAB_NAME = "StackFrame"

class StackFrameTab(ttk.Frame):
    """description of class"""

    def __init__(self, parent,**tree_kw):
        ttk.Frame.__init__(self,parent)
        row = ttk.Frame(self)
        ttk.Label(row, text=_("Stack Frame:")).pack(fill="x",side=tk.LEFT)
        self.frameValue = tk.StringVar()
        self._framesChoiceCtrl = ttk.Combobox(row,textvariable=self.frameValue)
        self._framesChoiceCtrl.state(['readonly'])
        self._framesChoiceCtrl.pack(fill="x",side=tk.LEFT,expand=1)
        row.pack(fill="x")
     #   self._framesChoiceCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnListRightClick)
      #  self.Bind(wx.EVT_CHOICE, self.ListItemSelected, self._framesChoiceCtrl)
        row = ttk.Frame(self)
        self.treeview = treeviewframe.TreeViewFrame(row, columns=["Value",'Hide'],displaycolumns=(0))
        self.tree = self.treeview.tree
        self.tree.heading("#0", text="Thing", anchor=tk.W)
        self.tree.heading("Value", text="Value", anchor=tk.W)
            
        self.tree.column('#0',width=60,anchor='w')
       # self.tree.column('1',width=70,anchor='w')
        
        self.tree["show"] = ("headings", "tree")
        self.treeview.pack(fill="both",expand=1)
        row.pack(fill="both",expand=1)
      #  self._treeCtrl.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        self._root = self.tree.insert("","end",text="Frame")
        #tree.SetPyData(self._root, "root")
        #tree.SetItemText(self._root, "", 1)
        
    def DeleteChildren(self,item):
        for child in self.tree.get_children(item):
            self.tree.delete(child)
            
    def SortChildren(self,node):
        # update tree
        children = self.tree.get_children(node)
        ids_sorted_by_name = py_sorted(children, cmp_func=self.OnCompareItems)
        self.tree.set_children(node, *ids_sorted_by_name)
        
    def OnCompareItems(self, item1, item2):
        return py_cmp(self.tree.item(item1,"text").lower(), self.tree.item(item2,"text").lower())
        
    def SetPyData(self,item,data):
        self.tree.set(item, value=data, column='Hide')

class StackframeViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(STACKFRAME_TAB_NAME,StackFrameTab, _("Stack Frame"), "se",image_file="python/debugger/flag.ico")
        