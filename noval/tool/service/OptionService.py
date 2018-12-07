import wx
import noval.tool.consts as consts
import wx.lib.agw.customtreectrl as CT
import noval.tool.GeneralOption as GeneralOption
import os
import noval.util.sysutils as sysutilslib
import noval.util.appdirs as appdirs
_ = wx.GetTranslation

##option names
ENVIRONMENT_OPTION_NAME = "Environment"
INTERPRETER_OPTION_NAME = "Interpreter"
OTHER_OPTION_NAME = "Other"

#option item names
GENERAL_ITEM_NAME = "General"
TEXT_ITEM_NAME = "Text"
PROJECT_ITEM_NAME = "Project"
FONTS_CORLORS_ITEM_NAME = "Fonts and Colors"
INTERPRETER_CONFIGURATIONS_ITEM_NAME = "Configuration List"
EXTENSION_ITEM_NAME = "Extension"

def GetOptionName(caterory,name):
    return caterory + "/" + name

class OptionsDialog(wx.Dialog):
    """
    A default options dialog used by the OptionsService that hosts a notebook
    tab of options panels.
    """
    PANEL_WIDITH = 650
    PANEL_HEIGHT = 580

    def __init__(self, parent, serivce,category_dct,category_list, docManager,selection=ENVIRONMENT_OPTION_NAME+"/"+GENERAL_ITEM_NAME):
        """
        Initializes the options dialog with a notebook page that contains new
        instances of the passed optionsPanelClasses.
        """
        wx.Dialog.__init__(self, parent, -1, _("Options"))
        self._service = serivce
        self._optionsPanels = {}
        self.current_panel = None
        self.current_item = None
        self._docManager = docManager
        self._category_list = category_list

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)
            
        self.tree = CT.CustomTreeCtrl(self,size=(200,self.PANEL_HEIGHT) ,style = wx.BORDER_THEME,agwStyle = wx.TR_DEFAULT_STYLE|wx.TR_NO_BUTTONS|wx.TR_HIDE_ROOT)
        self.tree.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX))
        tree_sizer.Add(self.tree, 0, wx.ALL, 0)
        wx.EVT_TREE_SEL_CHANGED(self.tree,self.tree.GetId(),self.DoSelection)

        line_sizer.Add(tree_sizer, 0, wx.TOP|wx.LEFT, consts.SPACE)
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        line_sizer.Add(self.panel_sizer, 0, wx.RIGHT|wx.EXPAND, consts.SPACE)
        sizer.Add(line_sizer, 0, wx.ALL | wx.EXPAND, -1)
        
        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND |wx.LEFT,consts.SPACE + 200)

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
        option_catetory,option_name = self.GetOptionNames(selection)
        for category in category_list:
            item = self.tree.AppendItem(self.root,_(category))
            self.tree.SetPyData(item,category)
            optionsPanelClasses = category_dct[category]
            for name,optionsPanelClass in optionsPanelClasses:
                option_panel = optionsPanelClass(self,-1,size=(self.PANEL_WIDITH,self.PANEL_HEIGHT))
                option_panel.Hide()
                self._optionsPanels[GetOptionName(category , name)] = option_panel
                child = self.tree.AppendItem(item,_(name))
                self.tree.SetPyData(child,name)
                #select the default item,to avoid select no item
                if name == GENERAL_ITEM_NAME and category == ENVIRONMENT_OPTION_NAME:
                    self.tree.SelectItem(child)
                if name == option_name and category == option_catetory:
                    self.tree.SelectItem(child)

        sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP, consts.HALF_SPACE)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
        wx.CallAfter(self.DoRefresh)
        
    def GetSelectOptionName(self,item):
        item_select_name = ""
        parent_item = item
        item_names = []
        while parent_item != self.tree.GetRootItem():
            item_names.append(self.tree.GetPyData(parent_item))
            parent_item = parent_item.GetParent()
        item_names.reverse()
        return '/'.join(item_names)

    def DoSelection(self,event):
        sel = self.tree.GetSelection()
        if self.tree.GetChildrenCount(sel) > 0:
            (item, cookie) = self.tree.GetFirstChild(sel)
            sel = item
        text = self.GetSelectOptionName(sel)
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
        if self.tree.GetChildrenCount(sel) > 0:
            (item, cookie) = self.tree.GetFirstChild(sel)
            sel = item
        text = self.GetSelectOptionName(sel)
        wx.ConfigBase_Get().Write("OptionName",text)
        self.EndModal(wx.ID_OK)
        
    def OnCancel(self, event):
        for name in self._optionsPanels:
            optionsPanel = self._optionsPanels[name]
            if hasattr(optionsPanel,"OnCancel") and not optionsPanel.OnCancel(self):
                return
        self.EndModal(wx.ID_CANCEL)
        
    def GetService(self):
        return self._service 
        
    def GetOptionNames(self,selection_name):
        names = selection_name.split("/")
        if 1 >= len(names):
            return "",selection_name
        return names[0],names[1]
        
    def GetOptionPanel(self,category,option_name):
        return self._optionsPanels[GetOptionName(category , option_name)]

class OptionsService(wx.lib.pydocview.DocOptionsService):
    def __init__(self,showGeneralOptions=True, supportedModes=wx.lib.docview.DOC_SDI & wx.lib.docview.DOC_MDI):
        wx.lib.pydocview.DocOptionsService.__init__(self,False,supportedModes=wx.lib.docview.DOC_MDI)
        self._optionsPanels = {}
        self.category_list = []
        self.AddOptionsPanel(ENVIRONMENT_OPTION_NAME,GENERAL_ITEM_NAME,GeneralOption.GeneralOptionsPanel)
        
    def OnOptions(self, event):
        """
        Shows the options dialog, called when the "Options" menu item is selected.
        """
        self.OnOption(option_name = wx.ConfigBase_Get().Read("OptionName",GENERAL_ITEM_NAME))
        
    def OnOption(self,option_name):
        if len(self._optionsPanels) == 0:
            return
        optionsDialog = OptionsDialog(wx.GetApp().GetTopWindow(),self, self._optionsPanels,self.category_list, self._docManager,option_name)
        optionsDialog.CenterOnParent()
        optionsDialog.ShowModal()
        optionsDialog.Destroy()
        
    def AddOptionsPanel(self,category,name,optionsPanelClass):
        
        if not self._optionsPanels.has_key(category):
            self._optionsPanels[category] = [(name,optionsPanelClass),]
            self.category_list.append(category)
        else:
            self._optionsPanels[category].append((name,optionsPanelClass),)
            
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        app_image_path = appdirs.GetAppImageDirLocation()
        toolsMenuIndex = menuBar.FindMenu(_("&Tools"))
        if toolsMenuIndex > -1:
            toolsMenu = menuBar.GetMenu(toolsMenuIndex)
        else:
            toolsMenu = wx.Menu()
        if toolsMenuIndex == -1:
            formatMenuIndex = menuBar.FindMenu(_("&Format"))
            menuBar.Insert(formatMenuIndex + 1, toolsMenu, _("&Tools"))
        if toolsMenu:
            if toolsMenu.GetMenuItemCount():
                toolsMenu.AppendSeparator()
            item = wx.MenuItem(toolsMenu,self._toolOptionsID, _("&Options..."), _("Sets options"))
            item.SetBitmap(wx.BitmapFromImage(wx.Image(os.path.join(app_image_path,"configure.png"),wx.BITMAP_TYPE_ANY)))
            toolsMenu.AppendItem(item)
            wx.EVT_MENU(frame, self._toolOptionsID, frame.ProcessEvent)
        
        
        
