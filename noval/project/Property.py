import wx
import wx.lib.pydocview
from noval.tool.consts import SPACE,HALF_SPACE,_,RESOURCE_ITEM_NAME,DEBUG_RUN_ITEM_NAME,\
            INTERPRETER_ITEM_NAME,PYTHONPATH_ITEM_NAME,PROJECT_REFERENCE_ITEM_NAME
import wx.lib.agw.customtreectrl as CT
import os
import noval.util.sysutils as sysutilslib
import noval.util.fileutils as fileutils
import ProjectEditor
import noval.util.utils as utils
from pages import *

class FilePropertiesService(wx.lib.pydocview.DocOptionsService):
    """
    Service that installs under the File menu to show the properties of the file associated
    with the current document.
    """

    PROPERTIES_ID = wx.NewId()

    def __init__(self):
        """
        Initializes the PropertyService.
        """
        wx.lib.pydocview.DocOptionsService.__init__(self,False,supportedModes=wx.lib.docview.DOC_MDI)
        self._optionsPanels = {}
        self.names = []
        self.category_list = []
        self.AddOptionsPanel(RESOURCE_ITEM_NAME,FileProertyPanel)
        self.AddOptionsPanel(DEBUG_RUN_ITEM_NAME,PyDebugRunProertyPanel)
        self._customEventHandlers = []
        self._current_project_document = None

    def AddOptionsPanel(self,name,optionsPanelClass):
        self._optionsPanels[name] = optionsPanelClass

    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        """
        Installs a File/Properties menu item.
        """
        fileMenu = menuBar.GetMenu(menuBar.FindMenu(_("&File")))
        exitMenuItemPos = self.GetMenuItemPos(fileMenu, wx.ID_EXIT)
        fileMenu.InsertSeparator(exitMenuItemPos)
        fileMenu.Insert(exitMenuItemPos, FilePropertiesService.PROPERTIES_ID, _("&Properties"), _("Show file properties"))
        wx.EVT_MENU(frame, FilePropertiesService.PROPERTIES_ID, self.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FilePropertiesService.PROPERTIES_ID, self.ProcessUpdateUIEvent)

    def ProcessEvent(self, event):
        """
        Detects when the File/Properties menu item is selected.
        """
        id = event.GetId()
        if id == FilePropertiesService.PROPERTIES_ID:
            for eventHandler in self._customEventHandlers:
                if eventHandler.ProcessEvent(event):
                    return True

            self.ShowPropertiesDialog()
            return True
        else:
            return False

    def ProcessUpdateUIEvent(self, event):
        """
        Updates the File/Properties menu item.
        """
        id = event.GetId()
        if id == FilePropertiesService.PROPERTIES_ID:
            for eventHandler in self._customEventHandlers:
                if eventHandler.ProcessUpdateUIEvent(event):
                    return True

            event.Enable(wx.GetApp().GetDocumentManager().GetCurrentDocument() != None)
            return True
        else:
            return False
            
    def GetNames(self,is_project):
        names = []
        names.append(RESOURCE_ITEM_NAME)
        names.append(DEBUG_RUN_ITEM_NAME)
        if is_project:
            names.append(INTERPRETER_ITEM_NAME)
            names.append(PYTHONPATH_ITEM_NAME)
            names.append(PROJECT_REFERENCE_ITEM_NAME)
        return names

    def ShowPropertiesDialog(self, project_document,selected_item,option_name=None):
        """
        Shows the PropertiesDialog for the specified file.
        """
        if not project_document:
            return
        self._current_project_document = project_document
        is_project = False
        project_view = project_document.GetFirstView()
        if selected_item == project_view._treeCtrl.GetRootItem():
            title = _("Project Property")
            file_path = project_document.GetFilename()
            self.AddOptionsPanel(INTERPRETER_ITEM_NAME,PythonInterpreterPanel)
            self.AddOptionsPanel(PYTHONPATH_ITEM_NAME,PythonPathPanel)
            self.AddOptionsPanel(PROJECT_REFERENCE_ITEM_NAME,ProjectReferrencePanel)
            is_project = True
        elif project_view._IsItemFile(selected_item):
            title = _("File Property")
            file_path = project_view._GetItemFilePath(selected_item)
        else:
            title = _("Folder Property")
            file_path = project_view._GetItemFolderPath(selected_item)
            
        self.names = self.GetNames(is_project)
        filePropertiesDialog = PropertyDialog(wx.GetApp().GetTopWindow(),title, self,selected_item,option_name)
        filePropertiesDialog.CenterOnParent()
        filePropertiesDialog.ShowModal()
        filePropertiesDialog.Destroy()


    def GetCustomEventHandlers(self):
        """
        Returns the custom event handlers for the PropertyService.
        """
        return self._customEventHandlers


    def AddCustomEventHandler(self, handler):
        """
        Adds a custom event handlers for the PropertyService.  A custom event handler enables
        a different dialog to be provided for a particular file.
        """
        self._customEventHandlers.append(handler)


    def RemoveCustomEventHandler(self, handler):
        """
        Removes a custom event handler from the PropertyService.
        """
        self._customEventHandlers.remove(handler)


    def chopPath(self, text, length=36):
        """
        Simple version of textwrap.  textwrap.fill() unfortunately chops lines at spaces
        and creates odd word boundaries.  Instead, we will chop the path without regard to
        spaces, but pay attention to path delimiters.
        """
        chopped = ""
        textLen = len(text)
        start = 0

        while start < textLen:
            end = start + length
            if end > textLen:
                end = textLen

            # see if we can find a delimiter to chop the path
            if end < textLen:
                lastSep = text.rfind(os.sep, start, end + 1)
                if lastSep != -1 and lastSep != start:
                    end = lastSep

            if len(chopped):
                chopped = chopped + '\n' + text[start:end]
            else:
                chopped = text[start:end]

            start = end

        return chopped
        
class PropertyDialog(wx.Dialog):
    """
    A default options dialog used by the OptionsService that hosts a notebook
    tab of options panels.
    """
    PANEL_WIDITH = 550
    PANEL_HEIGHT = 500

    def __init__(self, parent, title,filePropertiesService,selected_item,option_name=None):
        """
        Initializes the options dialog with a notebook page that contains new
        instances of the passed optionsPanelClasses.
        """
        wx.Dialog.__init__(self, parent, -1, title)
        self.filePropertiesService = filePropertiesService
        category_dct = filePropertiesService._optionsPanels
        names = filePropertiesService.names
        docManager = filePropertiesService._docManager

        self._optionsPanels = {}
        self.current_panel = None
        self.current_item = None
        self._docManager = docManager
        self._selected_project_item = selected_item

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)
            
        self.tree = CT.CustomTreeCtrl(self,size=(200,self.PANEL_HEIGHT) ,style = wx.BORDER_THEME,agwStyle = wx.TR_DEFAULT_STYLE|wx.TR_NO_BUTTONS|wx.TR_HIDE_ROOT)
        self.tree.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX))
        tree_sizer.Add(self.tree, 0, wx.ALL, 0)
        wx.EVT_TREE_SEL_CHANGED(self.tree,self.tree.GetId(),self.DoSelection)

        line_sizer.Add(tree_sizer, 0, wx.TOP|wx.LEFT, SPACE)
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        line_sizer.Add(self.panel_sizer, 0, wx.RIGHT|wx.EXPAND, SPACE)
        sizer.Add(line_sizer, 0, wx.ALL | wx.EXPAND, -1)
        
        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND |wx.LEFT,SPACE + 200)

        bitmap_plus = os.path.normpath(os.path.join(sysutilslib.mainModuleDir,"noval" ,"tool","bmp_source","plus.png"))
        bitmap_minus = os.path.normpath(os.path.join(sysutilslib.mainModuleDir, "noval" ,"tool","bmp_source","minus.png"))
        bitmap = wx.Bitmap(bitmap_plus, wx.BITMAP_TYPE_PNG)
        width = bitmap.GetWidth()
        
        il = wx.ImageList(width, width)
        #must add bitmap to imagelist twice
        il.Add(wx.Bitmap(bitmap_plus, wx.BITMAP_TYPE_PNG))
        il.Add(wx.Bitmap(bitmap_plus, wx.BITMAP_TYPE_PNG))
        il.Add(wx.Bitmap(bitmap_minus, wx.BITMAP_TYPE_PNG))
        il.Add(wx.Bitmap(bitmap_minus, wx.BITMAP_TYPE_PNG))

        self.tree.il = il                
        self.tree.SetButtonsImageList(il)
        self.root = self.tree.AddRoot("TheRoot")
        
        current_project_document = wx.GetApp().GetService(ProjectEditor.ProjectService).GetCurrentProject()
        ##force select one option
        if option_name:
            selection = option_name
        else:
            selection = utils.ProfileGet(current_project_document.GetKey("Selection"),"")
        for name in names:
            item = self.tree.AppendItem(self.root,_(name))
            self.tree.SetPyData(item,name)
            optionsPanelClass = category_dct[name]
            option_panel = optionsPanelClass(self.filePropertiesService,self,-1,size=(self.PANEL_WIDITH,self.PANEL_HEIGHT),selected_item = self._selected_project_item)
            option_panel.Hide()
            self._optionsPanels[name] = option_panel
            #select the default item,to avoid select no item
            if name == RESOURCE_ITEM_NAME:
                self.tree.SelectItem(item)
            if name == selection:
                self.tree.SelectItem(item)

        sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP, HALF_SPACE)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
        wx.CallAfter(self.DoRefresh)

    def DoSelection(self,event):
        sel = self.tree.GetSelection()
        if self.tree.GetChildrenCount(sel) > 0:
            (item, cookie) = self.tree.GetFirstChild(sel)
            sel = item
        text = self.tree.GetPyData(sel)
        panel = self._optionsPanels[text]
        if self.current_item is not None and sel != self.current_item:
            if not self.current_panel.Validate():
                self.tree.SelectItem(self.current_item)
                return 
        if self.current_panel is not None and panel != self.current_panel:
            self.current_panel.Hide()
        self.current_panel = panel
        self.current_item = sel        
        self.current_panel.Show()
        if not self.panel_sizer.GetItem(self.current_panel):
            self.panel_sizer.Insert(0,self.current_panel,0,wx.ALL|wx.EXPAND,0)
            
        self.Layout()
        self.Fit()

    def DoRefresh(self):
        """
        wxBug: On Windows XP when using a multiline notebook the default page doesn't get
        drawn, but it works when using a single line notebook.
        """
        self.Refresh()


    def GetDocManager(self):
        """
        Returns the document manager passed to the OptionsDialog constructor.
        """
        return self._docManager


    def OnOK(self, event):
        """
        Calls the OnOK method of all of the OptionDialog's embedded panels
        """
        if not self.current_panel.Validate():
            return
        for name in self._optionsPanels:
            optionsPanel = self._optionsPanels[name]
            if not optionsPanel.OnOK(self):
                return
        sel = self.tree.GetSelection()
        text = self.tree.GetPyData(sel)
        current_project_document = self.filePropertiesService._current_project_document
        if current_project_document is not None:
            utils.ProfileSet(current_project_document.GetKey("Selection"),text)
        self.EndModal(wx.ID_OK)
        
    def GetPanel(self,option_name):
        return self._optionsPanels[option_name]
        
    def HasPanel(self,option_name):
        return self._optionsPanels.has_key(option_name)