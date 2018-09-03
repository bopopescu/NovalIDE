import wx
import wx.lib.pydocview
from noval.tool.consts import SPACE,HALF_SPACE,_,ERROR_OK
import wx.lib.agw.customtreectrl as CT
import os
import noval.util.sysutils as sysutilslib
import noval.util.fileutils as fileutils
import time
import noval.tool.images as images
import ProjectEditor
import noval.util.utils as utils

RESOURCE_ITEM_NAME = "Resource"
DEBUG_RUN_ITEM_NAME = "Debug/Run Settings"
INTERPRETER_ITEM_NAME = "Interpreter"
PYTHONPATH_ITEM_NAME = "PythonPath"
PROJECT_REFERENCE_ITEM_NAME = "Project References"
#set the max width of location label,to avoid too long
MAX_LOCATION_LABEL_WIDTH  = 500

class FileProertyPage(wx.Panel):
    """description of class"""
    
    def __init__(self,parent,dlg_id,size,selected_item):
        wx.Panel.__init__(self, parent, dlg_id,size=size)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        filePropertiesService = wx.GetApp().GetService(FilePropertiesService)
        current_project_document = filePropertiesService._current_project_document
        
        relative_path = ""
        path = ""
        type_name = ""
        project_path = os.path.dirname(current_project_document.GetFilename())
        is_file = False
        project_view = current_project_document.GetFirstView()
        if selected_item == project_view._treeCtrl.GetRootItem():
            path = current_project_document.GetFilename()
            type_name = _("Project")
            relative_path = os.path.basename(path)
        elif project_view._IsItemFile(selected_item):
            path = project_view._GetItemFilePath(selected_item)
            template = wx.GetApp().GetDocumentManager().FindTemplateForPath(path)
            type_name = _("File") + "(%s)" % template.GetDescription()
            relative_path = path.replace(project_path,"").lstrip(os.sep)
            is_file = True
        else:
            relative_path = project_view._GetItemFolderPath(selected_item)
            type_name = _("Folder")
            path = os.path.join(project_path,relative_path)
        
        mtime_show_label = wx.StaticText(self, -1, _("Modified:"))
        max_width = mtime_show_label.GetSize().GetWidth()
            
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Path:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
        lineSizer.Add(wx.StaticText(self, -1, fileutils.opj(relative_path)),  1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Type:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
        lineSizer.Add(wx.StaticText(self, -1, type_name),  1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Location:"),size=(max_width,-1)),0,flag=wx.LEFT|wx.ALIGN_CENTER,border=SPACE)
        self.dest_path = fileutils.opj(path)
        self.location_label_ctrl = wx.StaticText(self, -1, self.dest_path)
        location_text_size = self.location_label_ctrl.GetTextExtent(self.dest_path)
        location_text_width = location_text_size[0]
        #the location label width is too long,ellipisis the text
        if location_text_width > MAX_LOCATION_LABEL_WIDTH:
            postend_ellipsis_text = "..."
            show_path = self.dest_path[:len(self.dest_path)*2/3] + postend_ellipsis_text
            limit_text_width = self.location_label_ctrl.GetTextExtent(show_path)[0] + HALF_SPACE
            self.location_label_ctrl.SetInitialSize((limit_text_width,location_text_size[1]),)
            self.location_label_ctrl.SetLabel(show_path)

        lineSizer.Add(self.location_label_ctrl,  0,flag=wx.LEFT|wx.ALIGN_CENTER,border=HALF_SPACE)
        into_btn = wx.BitmapButton(self,-1,images.load("into.png"))
        into_btn.SetToolTipString(_("Into file explorer"))
        into_btn.Bind(wx.EVT_BUTTON, self.IntoExplorer)
        lineSizer.Add(into_btn,  0,flag=wx.LEFT,border=SPACE)
        
        copy_btn = wx.BitmapButton(self,-1,images.load("copy.png"))
        copy_btn.SetToolTipString(_("Copy path"))
        copy_btn.Bind(wx.EVT_BUTTON, self.CopyPath)
        lineSizer.Add(copy_btn,  0,flag=wx.LEFT,border=HALF_SPACE)
        
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        
        is_path_exist = os.path.exists(path)
        show_label_text = ""
        if not is_path_exist:
            show_label_text = _("resource does not exist") 
        if is_file:
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            lineSizer.Add(wx.StaticText(self, -1, _("Size:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
            if is_path_exist:
                show_label_text = str(os.path.getsize(path))+ _(" Bytes")
            size_label_ctrl = wx.StaticText(self, -1, show_label_text)
            if not is_path_exist:
                size_label_ctrl.SetForegroundColour((255,0,0)) 
            lineSizer.Add(size_label_ctrl,  1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
            box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
            
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Created:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
        if is_path_exist:
            show_label_text = time.ctime(os.path.getctime(path))
        ctime_lable_ctrl = wx.StaticText(self, -1, show_label_text)
        if not is_path_exist:
            ctime_lable_ctrl.SetForegroundColour((255,0,0)) 
        lineSizer.Add(ctime_lable_ctrl,1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)

        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(mtime_show_label,0,flag=wx.LEFT,border=SPACE)
        if is_path_exist:
            show_label_text = time.ctime(os.path.getmtime(path))
        mtime_label_ctrl = wx.StaticText(self, -1,show_label_text)
        if not is_path_exist:
            mtime_label_ctrl.SetForegroundColour((255,0,0)) 
        lineSizer.Add(mtime_label_ctrl,1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Accessed:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
        if is_path_exist:
            show_label_text = time.ctime(os.path.getatime(path))
        atime_label_ctrl = wx.StaticText(self, -1,show_label_text)
        if not is_path_exist:
            atime_label_ctrl.SetForegroundColour((255,0,0)) 
        lineSizer.Add(atime_label_ctrl,1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        
        self.SetSizer(box_sizer) 
        #should use Layout ,could not use Fit method
        self.Layout()
        
    def IntoExplorer(self,event):
        location = self.dest_path
        err_code,msg = fileutils.open_file_directory(location)
        if err_code != ERROR_OK:
            wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
            
    def CopyPath(self,event):
        path = self.dest_path
        sysutilslib.CopyToClipboard(path)
        wx.MessageBox(_("Copied to clipboard"))
        
    def OnOK(self,optionsDialog):
        return True

class PyDebugRunProertyPage(wx.Panel):
    """description of class"""
    def __init__(self,parent,dlg_id,size,selected_item):
        wx.Panel.__init__(self, parent, dlg_id,size=size)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
    def OnOK(self,optionsDialog):
        return True

class PythonInterpreterPage(wx.Panel):
    def __init__(self,parent,dlg_id,size,selected_item):
        wx.Panel.__init__(self, parent, dlg_id,size=size)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
    def OnOK(self,optionsDialog):
        return True

class PythonPathPage(wx.Panel):
    def __init__(self,parent,dlg_id,size,selected_item):
        wx.Panel.__init__(self, parent, dlg_id,size=size)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
    def OnOK(self,optionsDialog):
        return True

class ProjectReferrencePage(wx.Panel):
    def __init__(self,parent,dlg_id,size,selected_item):
        wx.Panel.__init__(self, parent, dlg_id,size=size)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        
        boxsizer.Add(wx.StaticText(self, -1, _("The Reference Projects:"), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.LEFT|wx.TOP,border=SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.listbox = wx.CheckListBox(self,-1,size=(-1,300),choices=[])
        lineSizer.Add(self.listbox,1,flag = wx.EXPAND|wx.LEFT,border = SPACE)
        
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.select_all_btn = wx.Button(self, -1, _("Select All"))
        wx.EVT_BUTTON(self.select_all_btn, -1, self.SelectAll)
        rightSizer.Add(self.select_all_btn, 0,flag=wx.TOP, border=SPACE)
        
        self.unselect_all_btn = wx.Button(self, -1, _("UnSelect All"))
        wx.EVT_BUTTON(self.unselect_all_btn, -1, self.UnSelectAll)
        rightSizer.Add(self.unselect_all_btn, 0,flag=wx.TOP, border=SPACE)
        
        lineSizer.Add(rightSizer,0,flag = wx.EXPAND|wx.LEFT,border = HALF_SPACE)
        
        boxsizer.Add(lineSizer,0,flag = wx.TOP|wx.EXPAND,border = SPACE)
        self.SetSizer(boxsizer)
        #should use Layout ,could not use Fit method
        self.Layout()
        self.LoadProjects()
        
    def OnOK(self,optionsDialog):
        return True
        
    def SelectAll(self,event):
        for i in range(self.listbox.GetCount()):
            if not self.listbox.IsChecked(i):
                self.listbox.Check(i,True)
        
    def UnSelectAll(self,event):
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                self.listbox.Check(i,False)
        
    def LoadProjects(self):
        projectService = wx.GetApp().GetService(ProjectEditor.ProjectService)
        current_project_document = projectService.GetCurrentProject()
        for document in projectService.GetView().Documents:
            if document == current_project_document:
                continue
            self.listbox.Append(document.GetModel().Name)

class FilePropertiesService(wx.lib.pydocview.DocOptionsService):
    """
    Service that installs under the File menu to show the properties of the file associated
    with the current document.
    """

    PROPERTIES_ID = wx.NewId()
   #### PROJECT_PROPERTIES_ID = wx.NewId()

    def __init__(self):
        """
        Initializes the PropertyService.
        """
        wx.lib.pydocview.DocOptionsService.__init__(self,False,supportedModes=wx.lib.docview.DOC_MDI)
        self._optionsPanels = {}
        self.names = []
        self.category_list = []
        self.AddOptionsPanel(RESOURCE_ITEM_NAME,FileProertyPage)
        self.AddOptionsPanel(DEBUG_RUN_ITEM_NAME,PyDebugRunProertyPage)
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

    def ShowPropertiesDialog(self, project_document,selected_item):
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
            self.AddOptionsPanel(INTERPRETER_ITEM_NAME,PythonInterpreterPage)
            self.AddOptionsPanel(PYTHONPATH_ITEM_NAME,PythonPathPage)
            self.AddOptionsPanel(PROJECT_REFERENCE_ITEM_NAME,ProjectReferrencePage)
            is_project = True
        elif project_view._IsItemFile(selected_item):
            title = _("File Property")
            file_path = project_view._GetItemFilePath(selected_item)
        else:
            title = _("Folder Property")
            file_path = project_view._GetItemFolderPath(selected_item)
            
        self.names = self.GetNames(is_project)
        filePropertiesDialog = PropertyDialog(wx.GetApp().GetTopWindow(),title, self.names,self._optionsPanels,self._docManager,selected_item)
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
    PANEL_WIDITH = 650
    PANEL_HEIGHT = 580

    def __init__(self, parent, title,names, category_dct, docManager,selected_item):
        """
        Initializes the options dialog with a notebook page that contains new
        instances of the passed optionsPanelClasses.
        """
        wx.Dialog.__init__(self, parent, -1, title)

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
        selection = utils.ProfileGet(current_project_document.GetKey("Selection"),"")
        for name in names:
            item = self.tree.AppendItem(self.root,_(name))
            self.tree.SetPyData(item,name)
            optionsPanelClass = category_dct[name]
            option_panel = optionsPanelClass(self,-1,size=(self.PANEL_WIDITH,self.PANEL_HEIGHT),selected_item = self._selected_project_item)
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
        
        filePropertiesService = wx.GetApp().GetService(FilePropertiesService)
        current_project_document = filePropertiesService._current_project_document
        if current_project_document is not None:
            utils.ProfileSet(current_project_document.GetKey("Selection"),text)
        self.EndModal(wx.ID_OK)