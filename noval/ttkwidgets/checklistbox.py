# -*- coding: utf-8 -*-
"""
Author: Juliette Monsel
License: GNU GPLv3
Source: This repository

Treeview with checkboxes at each item and a noticeable disabled style
"""

try:
    import ttk
except ImportError:
    from tkinter import ttk

import os
import noval.ttkwidgets.checkboxtreeview as checkboxtreeview
from tkinter.ttk import Style

class CheckListbox(checkboxtreeview.CheckboxTreeview):
    """
    :class:`ttk.Treeview` widget with checkboxes left of each item.
    
    .. note::
        The checkboxes are done via the image attribute of the item, 
        so to keep the checkbox, you cannot add an image to the item.
    """

    def __init__(self, master=None, **kw):
        """
        Create a CheckboxTreeview.

        :param master: master widget
        :type master: widget
        :param kw: options to be passed on to the :class:`ttk.Treeview` initializer
        """
        checkboxtreeview.CheckboxTreeview.__init__(self, master, style_name="Checklistbox.Treeview",**kw)
        #隐藏checkbox左边距
        s = Style()
        s.layout('Checklistbox.Treeview.Item', [('Treeitem.padding',
          {'sticky': 'nswe',
           'children': [('Treeitem.image', {'side': 'left', 'sticky': ''}),
            ('Treeitem.focus',
             {'side': 'left',
              'sticky': '',
              'children': [('Treeitem.text', {'side': 'left', 'sticky': ''})]})]})])
              
    def GetCount(self):
        childs = self.get_children()
        return len(childs)
        
    def IsChecked(self,index):
        childs = self.get_children()
        item = childs[index]
        return self.IsItemChecked(item)
        
    def Append(self,name):
        self.insert("","end",text=name)
        return self.GetCount() -1
        
    def Check(self,index,checked=True):
        childs = self.get_children()
        item = childs[index]
        return self.CheckItem(item,checked)
        
    def GetString(self,index):
        childs = self.get_children()
        item = childs[index]
        return self.item(item,"text")
        
    def SetData(self,index,data):
        childs = self.get_children()
        item = childs[index]
        self.item(item,values=(data,))
        
    def GetData(self,index):
        childs = self.get_children()
        item = childs[index]
        return self.item(item)['values'][0]


   