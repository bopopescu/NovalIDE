#----------------------------------------------------------------------------
# Name:         OutlineService.py
# Purpose:      Outline View Service for pydocview
#
# Author:       Morgan Hua
#
# Created:      8/3/04
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.lib.docview
import wx.lib.pydocview
import Service
import noval.util.sysutils as sysutilslib
import os
import noval.util.WxThreadSafe as WxThreadSafe
import noval.parser.config as parserconfig
from noval.tool.consts import _,SPACE,HALF_SPACE
from noval.util import utils
#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------
SORT_BY_NONE = 0
SORT_BY_LINE = 1
SORT_BY_NAME = 2
SORT_BY_TYPE = 3

class OutlineView(Service.ServiceView):
    """ Reusable Outline View for any document.
        As a default, it uses a modified tree control (OutlineTreeCtrl) that allows sorting.
        Subclass OutlineTreeCtrl to customize the tree control and call SetTreeCtrl to install a customized tree control.
        When an item is selected, the document view is called back (with DoSelectCallback) to highlight and display the corresponding item in the document view.
    """

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self, service):
        Service.ServiceView.__init__(self, service)
        self._actionOnSelect = True


    def _CreateControl(self, parent, id):
        treeCtrl = OutlineTreeCtrl(parent, id)
        wx.EVT_TREE_SEL_CHANGED(treeCtrl, treeCtrl.GetId(), self.DoSelection)
        wx.EVT_SET_FOCUS(treeCtrl, self.DoSelection)
        wx.EVT_ENTER_WINDOW(treeCtrl, treeCtrl.CallDoLoadOutlineCallback)
        wx.EVT_RIGHT_DOWN(treeCtrl, self.OnRightClick)

        return treeCtrl


    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------

    def OnRightClick(self, event):
        menu = wx.Menu()

        menu.AppendRadioItem(OutlineService.SORT_BY_NONE, _("Unsorted"), _("Display items in original order"))
        menu.AppendRadioItem(OutlineService.SORT_BY_LINE, _("Sort By Line"), _("Display items in line order"))
        menu.AppendRadioItem(OutlineService.SORT_BY_TYPE, _("Sort By Type"), _("Display items in item type"))
        menu.AppendRadioItem(OutlineService.SORT_BY_NAME, _("Sort By Name(A-Z)"), _("Display items in name order"))

        config = wx.ConfigBase_Get()
        sort = config.ReadInt("OutlineSort", SORT_BY_NONE)
        if sort == SORT_BY_NONE:
            menu.Check(OutlineService.SORT_BY_NONE, True)
        elif sort == SORT_BY_LINE:
            menu.Check(OutlineService.SORT_BY_LINE, True)
        elif sort == SORT_BY_NAME:
            menu.Check(OutlineService.SORT_BY_NAME, True)
        elif sort == SORT_BY_TYPE:
            menu.Check(OutlineService.SORT_BY_TYPE, True)

        self.GetControl().PopupMenu(menu, event.GetPosition())
        menu.Destroy()


    #----------------------------------------------------------------------------
    # Tree Methods
    #----------------------------------------------------------------------------

    def DoSelection(self, event):
        if not self._actionOnSelect:
            return
        item = self.GetControl().GetSelection()
        if item:
            self.GetControl().CallDoSelectCallback(item)
        event.Skip()


    def ResumeActionOnSelect(self):
        self._actionOnSelect = True


    def StopActionOnSelect(self):
        self._actionOnSelect = False


    def SetTreeCtrl(self, tree):
        self.SetControl(tree)
        wx.EVT_TREE_SEL_CHANGED(self.GetControl(), self.GetControl().GetId(), self.DoSelection)
        wx.EVT_ENTER_WINDOW(self.GetControl(), treeCtrl.CallDoLoadOutlineCallback)
        wx.EVT_RIGHT_DOWN(self.GetControl(), self.OnRightClick)


    def GetTreeCtrl(self):
        return self.GetControl()


    def OnSort(self, sortOrder):
        treeCtrl = self.GetControl()
        treeCtrl.SetSortOrder(sortOrder)
        treeCtrl.SortAllChildren(treeCtrl.GetRootItem())


    def ClearTreeCtrl(self):
        if self.GetControl():
            self.GetControl().DeleteAllItems()


    def GetExpansionState(self):
        expanded = []

        treeCtrl = self.GetControl()
        if not treeCtrl:
            return expanded

        parentItem = treeCtrl.GetRootItem()

        if not parentItem:
            return expanded

        if not treeCtrl.IsExpanded(parentItem):
            return expanded

        expanded.append(treeCtrl.GetItemText(parentItem))

        (child, cookie) = treeCtrl.GetFirstChild(parentItem)
        while child.IsOk():
            if treeCtrl.IsExpanded(child):
                expanded.append(treeCtrl.GetItemText(child))
            (child, cookie) = treeCtrl.GetNextChild(parentItem, cookie)
        return expanded


    def SetExpansionState(self, expanded):
        if not expanded or len(expanded) == 0:
            return

        treeCtrl = self.GetControl()
        
        parentItem = treeCtrl.GetRootItem()
        if not parentItem:
            return
            
        if expanded[0] != treeCtrl.GetItemText(parentItem):
            return

        (child, cookie) = treeCtrl.GetFirstChild(parentItem)
        while child.IsOk():
            if treeCtrl.GetItemText(child) in expanded:
                treeCtrl.Expand(child)
            (child, cookie) = treeCtrl.GetNextChild(parentItem, cookie)

        treeCtrl.EnsureVisible(parentItem)


class OutlineTreeCtrl(wx.TreeCtrl):
    """ Default Tree Control Class for OutlineView.
        This class has the added functionality of sorting by the labels
    """


    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    ORIG_ORDER = 0
    VIEW = 1
    CALLBACKDATA = 2
    
    DISPLAY_ITEM_NAME = 0
    DISPLAY_ITEM_LINE = 1
    DISPLAY_ITEM_CLASS_BASE = 2
    DISPLAY_ITEM_FUNCTION_PARAMETER = 4

    #----------------------------------------------------------------------------
    # Overridden Methods
    #----------------------------------------------------------------------------

    def __init__(self, parent, id, style=wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE):
        wx.TreeCtrl.__init__(self, parent, id, style = style)
        self._origOrderIndex = 0
        self._sortOrder = SORT_BY_NONE
        self._display_item_flag = OutlineTreeCtrl.DISPLAY_ITEM_NAME
        if utils.ProfileGetInt("OutlineShowLineNumber", True):
            self._display_item_flag |= OutlineTreeCtrl.DISPLAY_ITEM_LINE
            
        if utils.ProfileGetInt("OutlineShowParameter", False):
            self._display_item_flag |= OutlineTreeCtrl.DISPLAY_ITEM_FUNCTION_PARAMETER
            
        if utils.ProfileGetInt("OutlineShowBaseClass", False):
            self._display_item_flag |= OutlineTreeCtrl.DISPLAY_ITEM_CLASS_BASE
        
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        modulebmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "module.png")
        modulebmp = wx.Bitmap(modulebmp_path, wx.BITMAP_TYPE_PNG)
        self.ModuleIdx = il.Add(modulebmp)

        funcbmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "func.png")
        funcbmp = wx.Bitmap(funcbmp_path, wx.BITMAP_TYPE_PNG)
        self.FuncIdx = il.Add(funcbmp)

        classbmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "class.png")
        classbmp = wx.Bitmap(classbmp_path, wx.BITMAP_TYPE_PNG)
        self.ClassIdx = il.Add(classbmp)

        propertybmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "property.png")
        propertybmp = wx.Bitmap(propertybmp_path, wx.BITMAP_TYPE_PNG)
        self.PropertyIdx = il.Add(propertybmp)
        
        importbmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "import.png")
        importbmp = wx.Bitmap(importbmp_path, wx.BITMAP_TYPE_PNG)
        self.ImportIdx = il.Add(importbmp)
        
        from_importbmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "from_import.png")
        from_import_bmp = wx.Bitmap(from_importbmp_path, wx.BITMAP_TYPE_PNG)
        self.FromImportIdx = il.Add(from_import_bmp)
        
        mainfunction_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "mainfunction.gif")
        mainfunction_image = wx.Image(mainfunction_image_path, wx.BITMAP_TYPE_ANY)
        self.MainFunctionIdx = il.Add(wx.BitmapFromImage(mainfunction_image))

        self.SetImageList(il)
        self.il = il

    def DeleteAllItems(self):
        self._origOrderIndex = 0
        wx.TreeCtrl.DeleteAllItems(self)


    #----------------------------------------------------------------------------
    # Sort Methods
    #----------------------------------------------------------------------------

    def SetSortOrder(self, sortOrder = SORT_BY_NONE):
        """ Sort Order constants are defined at top of file """
        self._sortOrder = sortOrder


    def OnCompareItems(self, item1, item2):
        if self._sortOrder == SORT_BY_LINE:
            data_1 = self.GetPyData(item1)[2]
            data_2 = self.GetPyData(item2)[2]
            return cmp(data_1.Line, data_2.Line)  # sort A-Z
        elif self._sortOrder == SORT_BY_NAME:
            return cmp(self.GetItemText(item1).lower(), self.GetItemText(item2).lower())  # sort Z-A
        elif self._sortOrder == SORT_BY_TYPE:
            data_1 = self.GetPyData(item1)[2]
            data_2 = self.GetPyData(item2)[2]
            return cmp(data_1.Type, data_2.Type)
        else:
            return (self.GetPyData(item1)[self.ORIG_ORDER] > self.GetPyData(item2)[self.ORIG_ORDER]) # unsorted


    def SortAllChildren(self, parentItem):
        if parentItem and self.GetChildrenCount(parentItem, False):
            self.SortChildren(parentItem)
            (child, cookie) = self.GetFirstChild(parentItem)
            while child.IsOk():
                self.SortAllChildren(child)
                (child, cookie) = self.GetNextChild(parentItem, cookie)


    #----------------------------------------------------------------------------
    # Select Callback Methods
    #----------------------------------------------------------------------------

    def CallDoSelectCallback(self, item):
        """ Invoke the DoSelectCallback of the given view to highlight text in the document view
        """
        data = self.GetPyData(item)
        if not data:
            return

        view = data[self.VIEW]
        cbdata = data[self.CALLBACKDATA]
        if view:
            view.DoSelectCallback(cbdata)

    def FindNodeItem(self,item,node):
        data = self.GetPyData(item)
        cbdata = data[self.CALLBACKDATA]
        if cbdata == node:
            return item
            
        if self.ItemHasChildren(item):
            child, cookie = self.GetFirstChild(item)
            while child.IsOk():
                find_item = self.FindNodeItem(child, node)
                if find_item is not None:
                    return find_item
                child, cookie = self.GetNextChild(item, cookie)
        return None
        
    @WxThreadSafe.call_after
    def SelectClosestItem(self, node):
        
        item = self.FindNodeItem(self.GetRootItem(),node)
        if item != None:
            os_view = wx.GetApp().GetService(OutlineService).GetView()
            if os_view:
               os_view.StopActionOnSelect()
            self.SelectItem(item)
            if os_view:
               os_view.ResumeActionOnSelect()

    def FindDistanceToTreeItems(self, item, position, distances, items):
        data = self.GetPyData(item)
        this_dist = 1000000
        if data and data[2]:
            positionTuple = data[2]
            if position >= positionTuple[1]:
                items.append(item)
                distances.append(position - positionTuple[1])

        if self.ItemHasChildren(item):
            child, cookie = self.GetFirstChild(item)
            while child.IsOk():
                self.FindDistanceToTreeItems(child, position, distances, items)
                child, cookie = self.GetNextChild(item, cookie)
        return False


    def SetDoSelectCallback(self, item, view, callbackdata):
        """ When an item in the outline view is selected,
        a method is called to select the respective text in the document view.
        The view must define the method DoSelectCallback(self, data) in order for this to work
        """
        self.SetPyData(item, (self._origOrderIndex, view, callbackdata))
        self._origOrderIndex = self._origOrderIndex + 1


    def CallDoLoadOutlineCallback(self, event):
        """ Invoke the DoLoadOutlineCallback
        """
        rootItem = self.GetRootItem()
        if rootItem:
            data = self.GetPyData(rootItem)
            if data:
                view = data[self.VIEW]
                if view and view.DoLoadOutlineCallback():
                    self.SortAllChildren(self.GetRootItem())


    def GetCallbackView(self):
        rootItem = self.GetRootItem()
        if rootItem:
            return self.GetPyData(rootItem)[self.VIEW]
        else:
            return None
            
    @WxThreadSafe.call_after
    def LoadModuleAst(self,module_scope,module_analyzer,outlineService,lineNum):
        #should freeze control to prevent update and treectrl flick
        view = module_analyzer.View
        self.Freeze()
        self.DeleteAllItems()
        rootItem = self.AddRoot(module_scope.Module.Name)
        self.SetItemImage(rootItem,self.ModuleIdx,wx.TreeItemIcon_Normal)
        self.SetDoSelectCallback(rootItem, view, module_scope.Module)
        self.TranverseItem(module_analyzer,module_scope.Module,rootItem)
        if not module_analyzer.IsAnalyzingStopped():
            self.Expand(rootItem)
            #use thaw to update freezw control
            self.Thaw()
            if lineNum >= 0:
                outlineService.SyncToPosition(view,lineNum)
        module_analyzer.FinishAnalyzing()
        outlineService.GetView().OnSort(wx.ConfigBase_Get().ReadInt("OutlineSort", SORT_BY_NONE))
        
    def TranverseItem(self,module_analyzer,node,parent):
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
                
                item = self.AppendItem(parent, display_name)
                self.SetItemImage(item,self.FuncIdx,wx.TreeItemIcon_Normal)
                self.SetDoSelectCallback(item, view, child)
            elif child.Type == parserconfig.NODE_CLASSDEF_TYPE:
                if self._display_item_flag & self.DISPLAY_ITEM_CLASS_BASE:
                    if len(child.Bases) > 0:
                        base_str = ",".join(child.Bases)
                        display_name = "%s(%s)" % (child.Name,base_str)
                    
                if self._display_item_flag & self.DISPLAY_ITEM_LINE:
                    display_name = "%s[%d]" % (display_name,child.Line)
                    
                item = self.AppendItem(parent, display_name)
                self.SetItemImage(item,self.ClassIdx,wx.TreeItemIcon_Normal)
                self.SetDoSelectCallback(item, view, child)
                self.TranverseItem(module_analyzer,child,item)
            else:
                if self._display_item_flag & self.DISPLAY_ITEM_LINE:
                    display_name = "%s[%d]" % (display_name,child.Line)
                if child.Type == parserconfig.NODE_OBJECT_PROPERTY or \
                            child.Type == parserconfig.NODE_ASSIGN_TYPE:
                    item = self.AppendItem(parent, display_name)
                    self.SetItemImage(item,self.PropertyIdx,wx.TreeItemIcon_Normal)
                    self.SetDoSelectCallback(item, view, child)
                elif child.Type == parserconfig.NODE_IMPORT_TYPE:
                    display_name = child.Name
                    if child.AsName is not None:
                        display_name = child.AsName
                    if self._display_item_flag & self.DISPLAY_ITEM_LINE:
                        display_name = "%s[%d]" % (display_name,child.Line)
                    item = self.AppendItem(parent,display_name)
                    self.SetItemImage(item,self.ImportIdx,wx.TreeItemIcon_Normal)
                    self.SetDoSelectCallback(item, view, child)
                elif child.Type == parserconfig.NODE_FROMIMPORT_TYPE:
                    from_import_item = self.AppendItem(parent,display_name)
                    self.SetItemImage(from_import_item,self.FromImportIdx,wx.TreeItemIcon_Normal)
                    self.SetDoSelectCallback(from_import_item, view, child)
                    for node_import in child.Childs:
                        name = node_import.Name
                        if node_import.AsName is not None:
                            name = node_import.AsName
                        import_item = self.AppendItem(from_import_item,name)
                        self.SetItemImage(import_item,self.ImportIdx,wx.TreeItemIcon_Normal)
                        self.SetDoSelectCallback(import_item, view, node_import)
                elif child.Type == parserconfig.NODE_MAIN_FUNCTION_TYPE:
                    item = self.AppendItem(parent, display_name)
                    self.SetItemImage(item,self.MainFunctionIdx,wx.TreeItemIcon_Normal)
                    self.SetDoSelectCallback(item, view, child)


class OutlineService(Service.Service):


    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    SHOW_WINDOW = wx.NewId()  # keep this line for each subclass, need unique ID for each Service
    SORT = wx.NewId()
    SORT_BY_LINE = wx.NewId()
    SORT_BY_NAME = wx.NewId()
    SORT_BY_NONE = wx.NewId()
    SORT_BY_TYPE = wx.NewId()


    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self, serviceName, embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM):
        Service.Service.__init__(self, serviceName, embeddedWindowLocation,icon_path="outline.ico")
        self._validViewTypes = []


    def _CreateView(self):
        return OutlineView(self)


    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        Service.Service.InstallControls(self, frame, menuBar, toolBar, statusBar, document)

        wx.EVT_MENU(frame, OutlineService.SORT_BY_LINE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, OutlineService.SORT_BY_LINE, frame.ProcessUpdateUIEvent)
        wx.EVT_MENU(frame, OutlineService.SORT_BY_NAME, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, OutlineService.SORT_BY_NAME, frame.ProcessUpdateUIEvent)
        wx.EVT_MENU(frame, OutlineService.SORT_BY_NONE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, OutlineService.SORT_BY_NONE, frame.ProcessUpdateUIEvent)
        wx.EVT_MENU(frame, OutlineService.SORT_BY_TYPE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, OutlineService.SORT_BY_TYPE, frame.ProcessUpdateUIEvent)


        if wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return True

        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))
        self._outlineSortMenu = wx.Menu()
        self._outlineSortMenu.AppendRadioItem(OutlineService.SORT_BY_NONE, _("Unsorted"), _("Display items in original order"))
        self._outlineSortMenu.AppendRadioItem(OutlineService.SORT_BY_LINE, _("Sort By Line"), _("Display items in line order"))
        self._outlineSortMenu.AppendRadioItem(OutlineService.SORT_BY_TYPE, _("Sort By Type"), _("Display items in item type"))
        self._outlineSortMenu.AppendRadioItem(OutlineService.SORT_BY_NAME, _("Sort By Name(A-Z)"), _("Display items in name order"))
        viewMenu.AppendMenu(wx.NewId(), _("Outline Sort"), self._outlineSortMenu)

        return True


    #----------------------------------------------------------------------------
    # Event Processing Methods
    #----------------------------------------------------------------------------

    def ProcessEvent(self, event):
        if Service.Service.ProcessEvent(self, event):
            return True

        id = event.GetId()
        if id in [OutlineService.SORT_BY_LINE,OutlineService.SORT_BY_NAME,OutlineService.SORT_BY_NONE,OutlineService.SORT_BY_TYPE]:
            self.OnSort(event)
            return True
        else:
            return False


    def ProcessUpdateUIEvent(self, event):
        if Service.Service.ProcessUpdateUIEvent(self, event):
            return True

        id = event.GetId()
        if id == OutlineService.SORT_BY_LINE:
            event.Enable(True)

            config = wx.ConfigBase_Get()
            sort = config.ReadInt("OutlineSort", SORT_BY_NONE)
            if sort == SORT_BY_LINE:
                self._outlineSortMenu.Check(OutlineService.SORT_BY_LINE, True)
            else:
                self._outlineSortMenu.Check(OutlineService.SORT_BY_LINE, False)

            return True
        elif id == OutlineService.SORT_BY_NAME:
            event.Enable(True)

            config = wx.ConfigBase_Get()
            sort = config.ReadInt("OutlineSort", SORT_BY_NONE)
            if sort == SORT_BY_NAME:
                self._outlineSortMenu.Check(OutlineService.SORT_BY_NAME, True)
            else:
                self._outlineSortMenu.Check(OutlineService.SORT_BY_NAME, False)

            return True
        elif id == OutlineService.SORT_BY_NONE:
            event.Enable(True)

            config = wx.ConfigBase_Get()
            sort = config.ReadInt("OutlineSort", SORT_BY_NONE)
            if sort == SORT_BY_NONE:
                self._outlineSortMenu.Check(OutlineService.SORT_BY_NONE, True)
            else:
                self._outlineSortMenu.Check(OutlineService.SORT_BY_NONE, False)

            return True

        elif id == OutlineService.SORT_BY_TYPE:
            event.Enable(True)

            config = wx.ConfigBase_Get()
            sort = config.ReadInt("OutlineSort", SORT_BY_NONE)
            if sort == SORT_BY_TYPE:
                self._outlineSortMenu.Check(OutlineService.SORT_BY_TYPE, True)
            else:
                self._outlineSortMenu.Check(OutlineService.SORT_BY_TYPE, False)

            return True
        else:
            return False


    def OnSort(self, event):
        id = event.GetId()
        sort = SORT_BY_NONE
        if id == OutlineService.SORT_BY_LINE:
            sort = SORT_BY_LINE
        elif id == OutlineService.SORT_BY_NAME:
            sort = SORT_BY_NAME
        elif id == OutlineService.SORT_BY_NONE:
            sort = SORT_BY_NONE
        elif id == OutlineService.SORT_BY_TYPE:
            sort = SORT_BY_TYPE
        wx.ConfigBase_Get().WriteInt("OutlineSort", sort)
        self.GetView().OnSort(sort)

    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------

    def LoadOutline(self, view, lineNum=-1, force=False):
        if not self.GetView():
            return

        if hasattr(view, "DoLoadOutlineCallback"):
            self.SaveExpansionState()
            if view.DoLoadOutlineCallback(force=force,lineNum=lineNum):
                self.GetView().OnSort(wx.ConfigBase_Get().ReadInt("OutlineSort", SORT_BY_NONE))
                self.LoadExpansionState()
            else:
                self.SyncToPosition(view,lineNum)

    def SyncToPosition(self, view,lineNum):
        if not self.GetView():
            return
        if lineNum >= 0 and view.ModuleScope is not None:
            scope = view.ModuleScope.FindScope(lineNum)
            if scope.Parent is None:
                return
            self.GetView().GetTreeCtrl().SelectClosestItem(scope.Node)

    def OnCloseFrame(self, event):
        self.StopTimer()
        Service.Service.OnCloseFrame(self, event)
        self.SaveExpansionState(clear = True)

        return True


    def SaveExpansionState(self, clear = False):
        if clear:
            expanded = []
        elif self.GetView():
            expanded = self.GetView().GetExpansionState()
        wx.ConfigBase_Get().Write("OutlineLastExpanded", expanded.__repr__())


    def LoadExpansionState(self):
        expanded = wx.ConfigBase_Get().Read("OutlineLastExpanded")
        if expanded:
            self.GetView().SetExpansionState(eval(expanded))


    #----------------------------------------------------------------------------
    # Timer Methods
    #----------------------------------------------------------------------------

    def StartBackgroundTimer(self):
        self._timer = wx.PyTimer(self.DoBackgroundRefresh)
        self._timer.Start(250)

    def StopTimer(self):
        self._timer.Stop()

    def DoBackgroundRefresh(self):
        """ Refresh the outline view periodically """
        self.StopTimer()
        
        foundRegisteredView = False
        if self.GetView():
            currView = self.GetActiveView()
            if currView:
                for viewType in self._validViewTypes:
                    if isinstance(currView, viewType):
                        self.LoadOutline(currView)
                        foundRegisteredView = True
                        break

            if not foundRegisteredView:
                self.GetView().ClearTreeCtrl()
                    
        self._timer.Start(1000) # 1 second interval


    def AddViewTypeForBackgroundHandler(self, viewType):
        self._validViewTypes.append(viewType)


    def GetViewTypesForBackgroundHandler(self):
        return self._validViewTypes


    def RemoveViewTypeForBackgroundHandler(self, viewType):
        self._validViewTypes.remove(viewType)


class OutlineOptionsPanel(wx.Panel):
    """
    """
    def __init__(self, parent, id,size):
        wx.Panel.__init__(self, parent, id,size=size)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        optionsSizer = wx.BoxSizer(wx.VERTICAL)
        config = wx.ConfigBase_Get()
        self._showLineNumberCheckBox = wx.CheckBox(self, -1, _("Show Line Number"))
        self._showLineNumberCheckBox.SetValue(config.ReadInt("OutlineShowLineNumber", True))
        optionsSizer.Add(self._showLineNumberCheckBox, 0, wx.ALL, HALF_SPACE)

        self._showParameterCheckBox = wx.CheckBox(self, -1, _("Show parameter of function"))
        self._showParameterCheckBox.SetValue(config.ReadInt("OutlineShowParameter", False))
        optionsSizer.Add(self._showParameterCheckBox, 0, wx.ALL, HALF_SPACE)
        
        self._showClassBaseCheckBox = wx.CheckBox(self, -1, _("Show base classes of class"))
        self._showClassBaseCheckBox.SetValue(config.ReadInt("OutlineShowBaseClass", False))
        optionsSizer.Add(self._showClassBaseCheckBox, 0, wx.ALL, HALF_SPACE)
        
        main_sizer.Add(optionsSizer, 0, wx.ALL|wx.EXPAND, SPACE)
        self.SetSizer(main_sizer)
        self.Layout()
        
    def OnOK(self, optionsDialog):
        config = wx.ConfigBase_Get()
        config.WriteInt("OutlineShowLineNumber", self._showLineNumberCheckBox.GetValue())
        config.WriteInt("OutlineShowParameter", self._showParameterCheckBox.GetValue())
        config.WriteInt("OutlineShowBaseClass", self._showClassBaseCheckBox.GetValue())
        
        display_item_flag = OutlineTreeCtrl.DISPLAY_ITEM_NAME
        if self._showLineNumberCheckBox.GetValue():
            display_item_flag |= OutlineTreeCtrl.DISPLAY_ITEM_LINE
            
        if self._showParameterCheckBox.GetValue():
            display_item_flag |= OutlineTreeCtrl.DISPLAY_ITEM_FUNCTION_PARAMETER
            
        if self._showClassBaseCheckBox.GetValue():
            display_item_flag |= OutlineTreeCtrl.DISPLAY_ITEM_CLASS_BASE
        
        outline_view = wx.GetApp().GetService(OutlineService).GetView()
        if display_item_flag != outline_view.GetTreeCtrl()._display_item_flag:
            outline_view.GetTreeCtrl()._display_item_flag = display_item_flag
            active_text_view = Service.Service.GetActiveView()
            if active_text_view != None and hasattr(active_text_view,"DoLoadOutlineCallback"):
                active_text_view.DoLoadOutlineCallback(True)
        return True
        
