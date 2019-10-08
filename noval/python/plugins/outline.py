# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        outline.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-11
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk
import noval.ui_base as ui_base
import noval.iface as iface
import noval.plugin as plugin
import noval.consts as consts
import noval.imageutils as imageutils
import noval.python.parser.config as parserconfig
import noval.syntax.lang as lang
import noval.util.utils as utils
import noval.menu as tkmenu
import noval.constants as constants
import noval.python.pyeditor as pyeditor
import noval.preference as preference
import noval.ui_utils as ui_utils

class PythonOutlineView(ui_base.OutlineView):
    
    DISPLAY_ITEM_NAME = 0
    DISPLAY_ITEM_LINE = 1
    DISPLAY_ITEM_CLASS_BASE = 2
    DISPLAY_ITEM_FUNCTION_PARAMETER = 4
    
    def __init__(self, master):
        ui_base.OutlineView.__init__(self, master)
        self.func_image = imageutils.load_image("","python/outline/func.png")
        self.class_image = imageutils.load_image("","python/outline/class.png")
        self.property_image = imageutils.load_image("","python/outline/property.png")
        self.import_image = imageutils.load_image("","python/outline/import.png")
        self.from_import_image = imageutils.load_image("","python/outline/from_import.png")
        self.mainfunction_image = imageutils.load_image("","python/outline/mainfunction.gif")
        self._display_item_flag = self.DISPLAY_ITEM_NAME
        #显示行号
        if utils.profile_get_int("OutlineShowLineNumber", True):
            self._display_item_flag |= self.DISPLAY_ITEM_LINE
        #显示参数
        if utils.profile_get_int("OutlineShowParameter", False):
            self._display_item_flag |= self.DISPLAY_ITEM_FUNCTION_PARAMETER
        #显示基类
        if utils.profile_get_int("OutlineShowBaseClass", False):
            self._display_item_flag |= self.DISPLAY_ITEM_CLASS_BASE

    def _update_frame_contents(self, event=None):
        editor = GetApp().MainFrame.GetNotebook().get_current_editor()
        if editor is None:
            current_view = None
        else:
            current_view = editor.GetView()
        self.LoadOutLine(current_view)
        
    def LoadOutLine(self,currView,lineNum=-1):
        foundRegisteredView = False
        if currView:
            #是否是允许在大纲显示的视图类型
            if self.IsValidViewType(currView):
                if not currView.GetDocument()._is_loading_doc:
                    currView.LoadOutLine(self,lineNum=lineNum)
                    self.SetCallbackView(currView)
                    foundRegisteredView = True
                else:
                    utils.get_logger().debug("%s is loading document,will not load outline",currView.GetDocument().GetFilename())
               
        #不支持显示大纲视图的文档类型,大纲内容显示为空
        if not foundRegisteredView:
            self.SetCallbackView(None)
            self._clear_tree()


    def SyncToPosition(self, view,lineNum):
        if lineNum >= 0 and view.ModuleScope is not None:
            scope = view.ModuleScope.FindScope(lineNum)
            if scope.Parent is None:
                return
            self.SelectAndFindNodeItem(scope.Node)
            
    def SelectAndFindNodeItem(self,node):
        line = node.Line
        col = node.Col
        node_id = self.FindNodeItem(None,line,col)
        if node_id is not None:
            self.tree.focus(node_id)
            self.tree.see(node_id)
            self.tree.selection_set(node_id)
        
    def FindNodeItem(self,item,line,col):
        items = self.tree.get_children(item)
        for item in items:
            lineno,column = self.tree.item(item)["values"][0:2]
            if line == lineno and column == col:
                return item
            else:
                found = self.FindNodeItem(item,line,col)
                if found:
                    return found
        return None

    # clears the tree by deleting all items
    def _on_select(self, event):
        editor = GetApp().MainFrame.GetNotebook().get_current_editor()
        if editor:
            code_view = editor.GetView()
            lineno = self.tree.item(self.tree.focus())["values"][0]
            index = code_view.GetCtrl().index(str(lineno) + ".0")
            code_view.GetCtrl().see(
                index
            )  # make sure that the double-clicked item is visible
            code_view.GetCtrl().select_lines(lineno, lineno)
            
    def LoadModuleAst(self,module_scope,module_analyzer,lineNum=-1):
        view = module_analyzer.View
        self._clear_tree()
        self.TranverseItem(module_analyzer,module_scope.Module,"")
        module_analyzer.FinishAnalyzing()
        self.Sort(self._sortOrder)
        if lineNum >= 0:
            self.SyncToPosition(view,lineNum)
        
    def TranverseItem(self,module_analyzer,node,parent=""):
        view = module_analyzer.View
        for child in node.Childs:
            if module_analyzer.IsAnalyzingStopped():
                break
            display_name = child.Name
            if child.Type == parserconfig.NODE_FUNCDEF_TYPE:
                if self._display_item_flag & self.DISPLAY_ITEM_FUNCTION_PARAMETER:
                    arg_list = [arg.Name for arg in child.Args]
                    arg_str = ",".join(arg_list)
                    display_name = "%s(%s)" % (child.Name,arg_str)
                    
                if self._display_item_flag & self.DISPLAY_ITEM_LINE:
                    display_name = "%s[%d]" % (display_name,child.Line)
                current = self.tree.insert(
                    parent, "end", text=display_name, values=(child.Line,child.Col,child.Type), image=self.func_image
                )
            elif child.Type == parserconfig.NODE_CLASSDEF_TYPE:
                if self._display_item_flag & self.DISPLAY_ITEM_CLASS_BASE:
                    if len(child.Bases) > 0:
                        base_str = ",".join(child.Bases)
                        display_name = "%s(%s)" % (child.Name,base_str)
                    
                if self._display_item_flag & self.DISPLAY_ITEM_LINE:
                    display_name = "%s[%d]" % (display_name,child.Line)
                current = self.tree.insert(parent, "end", text=display_name, values=(child.Line,child.Col,child.Type), image=self.class_image)
                self.TranverseItem(module_analyzer,child,current)
            else:
                if self._display_item_flag & self.DISPLAY_ITEM_LINE:
                    display_name = "%s[%d]" % (display_name,child.Line)
                if child.Type == parserconfig.NODE_CLASS_PROPERTY or \
                            child.Type == parserconfig.NODE_ASSIGN_TYPE:
                    current = self.tree.insert(
                        parent, "end", text=display_name, values=(child.Line,child.Col,child.Type), image=self.property_image
                    )
                elif child.Type == parserconfig.NODE_IMPORT_TYPE:
                    display_name = child.Name
                    if child.AsName is not None:
                        display_name = child.AsName
                    if self._display_item_flag & self.DISPLAY_ITEM_LINE:
                        display_name = "%s[%d]" % (display_name,child.Line)
                    current = self.tree.insert(
                        parent, "end", text=display_name, values=(child.Line,child.Col,child.Type), image=self.import_image
                    )
                elif child.Type == parserconfig.NODE_FROMIMPORT_TYPE:
                    current = self.tree.insert(
                        parent, "end", text=display_name, values=(child.Line,child.Col,child.Type), image=self.from_import_image
                    )
                    for node_import in child.Childs:
                        name = node_import.Name
                        if node_import.AsName is not None:
                            name = node_import.AsName
                        current = self.tree.insert(
                            current, "end", text=name, values=(child.Line,child.Col,child.Type), image=self.import_image
                        )
                elif child.Type == parserconfig.NODE_MAIN_FUNCTION_TYPE:
                    current = self.tree.insert(
                        parent, "end", text=display_name, values=(child.Line,child.Col,child.Type), image=self.mainfunction_image
                    )


def OutlineSort(outline_sort_id):
    sort_order = ui_base.OutlineView.SORT_BY_NONE
    if outline_sort_id == constants.ID_SORT_BY_LINE:
        sort_order = ui_base.OutlineView.SORT_BY_LINE
    elif outline_sort_id == constants.ID_SORT_BY_TYPE:
        sort_order = ui_base.OutlineView.SORT_BY_TYPE
    elif outline_sort_id == constants.ID_SORT_BY_NAME:
        sort_order = ui_base.OutlineView.SORT_BY_NAME
    GetApp().MainFrame.GetView(consts.OUTLINE_VIEW_NAME).Sort(sort_order)
    
class OutlineOptionPanel(ui_utils.CommonOptionPanel):
    """
    """
    def __init__(self, parent):
        ui_utils.CommonOptionPanel.__init__(self, parent)
        self._showLineNumberCheckVar = tk.IntVar(value=utils.profile_get_int("OutlineShowLineNumber", True))
        showLineNumberCheckBox = ttk.Checkbutton(self.panel,text=_("Show Line Number"),variable=self._showLineNumberCheckVar)
        showLineNumberCheckBox.pack(fill=tk.X)

        self._showParameterCheckVar = tk.IntVar(value=utils.profile_get_int("OutlineShowParameter", False))
        showParameterCheckBox = ttk.Checkbutton(self.panel,text=_("Show parameter of function"),variable=self._showParameterCheckVar)
        showParameterCheckBox.pack(fill=tk.X)
        
        self._showClassBaseCheckVar = tk.IntVar(value=utils.profile_get_int("OutlineShowBaseClass", False))
        showClassBaseCheckBox = ttk.Checkbutton(self.panel, text=_("Show base classes of class"),variable=self._showClassBaseCheckVar)
        showClassBaseCheckBox.pack(fill=tk.X)

    def OnOK(self, optionsDialog):
  
        utils.profile_set("OutlineShowLineNumber", self._showLineNumberCheckVar.get())
        utils.profile_set("OutlineShowParameter", self._showParameterCheckVar.get())
        utils.profile_set("OutlineShowBaseClass", self._showClassBaseCheckVar.get())
        
        display_item_flag = PythonOutlineView.DISPLAY_ITEM_NAME
        if self._showLineNumberCheckVar.get():
            display_item_flag |= PythonOutlineView.DISPLAY_ITEM_LINE
            
        if self._showParameterCheckVar.get():
            display_item_flag |= PythonOutlineView.DISPLAY_ITEM_FUNCTION_PARAMETER
            
        if self._showClassBaseCheckVar.get():
            display_item_flag |= PythonOutlineView.DISPLAY_ITEM_CLASS_BASE
        
        outline_view = GetApp().MainFrame.GetView(consts.OUTLINE_VIEW_NAME)
        if display_item_flag != outline_view._display_item_flag:
            outline_view._display_item_flag = display_item_flag
            active_text_view = GetApp().GetDocumentManager().GetCurrentView()
            if active_text_view != None and hasattr(active_text_view,"LoadOutLine"):
                active_text_view.LoadOutLine(outline_view,True)
        return True
        
    
class PythonOutlineViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(consts.OUTLINE_VIEW_NAME,PythonOutlineView, _("Outline"), "ne",image_file="python/outline/outline.ico")
        view_menu = GetApp().Menubar.GetMenu(_("&View"))
        outline_menu = tkmenu.PopupMenu()
        self.outline_sort_var = tk.IntVar(value=utils.profile_get_int("OutlineSort", ui_base.OutlineView.SORT_BY_NONE))
        view_menu.InsertMenuAfter(constants.ID_ZOOM,constants.ID_OUTLINE_SORT,_("Outline Sort"),outline_menu)

        #设置Python文本视图在大纲中显示语法树
        GetApp().MainFrame.GetView(consts.OUTLINE_VIEW_NAME).AddViewTypeForBackgroundHandler(pyeditor.PythonView)
        
        GetApp().AddMenuCommand(constants.ID_SORT_BY_NONE,outline_menu,_("Unsorted"),lambda:OutlineSort(constants.ID_SORT_BY_NONE),\
                                default_command=True,default_tester=True,kind=consts.RADIO_MENU_ITEM_KIND,variable=self.outline_sort_var,value=ui_base.OutlineView.SORT_BY_NONE)
        GetApp().AddMenuCommand(constants.ID_SORT_BY_LINE,outline_menu,_("Sort By Line"),lambda:OutlineSort(constants.ID_SORT_BY_LINE),\
                                default_command=True,default_tester=True,kind=consts.RADIO_MENU_ITEM_KIND,variable=self.outline_sort_var,value=ui_base.OutlineView.SORT_BY_LINE)
        GetApp().AddMenuCommand(constants.ID_SORT_BY_TYPE,outline_menu,_("Sort By Type"),lambda:OutlineSort(constants.ID_SORT_BY_TYPE),\
                                default_command=True,default_tester=True,kind=consts.RADIO_MENU_ITEM_KIND,variable=self.outline_sort_var,value=ui_base.OutlineView.SORT_BY_TYPE)
        GetApp().AddMenuCommand(constants.ID_SORT_BY_NAME,outline_menu,_("Sort By Name(A-Z)"),lambda:OutlineSort(constants.ID_SORT_BY_NAME),\
                                default_command=True,default_tester=True,kind=consts.RADIO_MENU_ITEM_KIND,variable=self.outline_sort_var,value=ui_base.OutlineView.SORT_BY_NAME)
        #首选项显示面板                
        preference.PreferenceManager().AddOptionsPanelClass("Misc","Outline",OutlineOptionPanel)
