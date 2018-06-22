import wx
import consts
import wx.lib.agw.customtreectrl as CT
import GeneralOption
import os
import noval.util.sysutils as sysutilslib
import noval.util.appdirs as appdirs
_ = wx.GetTranslation

class OptionsDialog(wx.Dialog):
    """
    A default options dialog used by the OptionsService that hosts a notebook
    tab of options panels.
    """

    def __init__(self, parent, category_dct,category_list, docManager,option_name):
        """
        Initializes the options dialog with a notebook page that contains new
        instances of the passed optionsPanelClasses.
        """
        wx.Dialog.__init__(self, parent, -1, _("Options"))

        self._optionsPanels = {}
        self.current_panel = None
        self.current_item = None
        self._docManager = docManager
        self._category_list = category_list

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)
            
        self.tree = CT.CustomTreeCtrl(self,size=(200,600) ,style = wx.BORDER_THEME,agwStyle = wx.TR_DEFAULT_STYLE|wx.TR_NO_BUTTONS|wx.TR_HIDE_ROOT)
        tree_sizer.Add(self.tree, 0, wx.ALL, 0)
        wx.EVT_TREE_SEL_CHANGED(self.tree,self.tree.GetId(),self.DoSelection)

        line_sizer.Add(tree_sizer, 0, wx.TOP|wx.LEFT, consts.SPACE)
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        line_sizer.Add(self.panel_sizer, 0, wx.RIGHT|wx.EXPAND, consts.SPACE)
        sizer.Add(line_sizer, 0, wx.ALL | wx.EXPAND, -1)
        
        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND |wx.LEFT,consts.SPACE + 200)

        bitmap_plus = os.path.normpath(os.path.join(sysutilslib.mainModuleDir,"noval" ,"tool","bmp_source","plus.ico"))
        bitmap_minus = os.path.normpath(os.path.join(sysutilslib.mainModuleDir, "noval" ,"tool","bmp_source","minus.ico"))
        bitmap = wx.Bitmap(bitmap_plus, wx.BITMAP_TYPE_ICO)
        width = bitmap.GetWidth()
        
        il = wx.ImageList(width, width)
        #must add bitmap to imagelist twice
        il.Add(wx.Bitmap(bitmap_plus, wx.BITMAP_TYPE_ICO))
        il.Add(wx.Bitmap(bitmap_plus, wx.BITMAP_TYPE_ICO))
        il.Add(wx.Bitmap(bitmap_minus, wx.BITMAP_TYPE_ICO))
        il.Add(wx.Bitmap(bitmap_minus, wx.BITMAP_TYPE_ICO))

        self.tree.il = il                
        self.tree.SetButtonsImageList(il)
        self.root = self.tree.AddRoot("TheRoot")
        for category in category_list:
            item = self.tree.AppendItem(self.root,category)
            optionsPanelClasses = category_dct[category]
            for name,optionsPanelClass in optionsPanelClasses:
                option_panel = optionsPanelClass(self,-1)
                option_panel.Hide()
                self._optionsPanels[name] = option_panel
                child = self.tree.AppendItem(item,name)
                if name == option_name:
                    self.tree.SelectItem(child)

        sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP, consts.HALF_SPACE)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
        wx.CallAfter(self.DoRefresh)

    def DoSelection(self,event):
        
        sel = self.tree.GetSelection()
        self.current_item = sel
        text = self.tree.GetItemText(sel)
        if not self._optionsPanels.has_key(text) or self.tree.GetChildrenCount(sel) > 0:
            return
        panel = self._optionsPanels[text]
        if self.current_panel is not None and panel != self.current_panel:
            self.current_panel.Hide()
        self.current_panel = panel
        self.current_panel.Show()
        if not self.panel_sizer.GetItem(self.current_panel):
            self.panel_sizer.Insert(0,self.current_panel,0,wx.ALL|wx.EXPAND,0)
            
        ##self.GetSizer().Fit(self)
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
        for name in self._optionsPanels:
            optionsPanel = self._optionsPanels[name]
            optionsPanel.OnOK(event)
            
        sel = self.tree.GetSelection()
        text = self.tree.GetItemText(sel)
        wx.ConfigBase_Get().Write("OptionName",text)
            
    def AddPage(self,panel,label):
        pass


class OptionsService(wx.lib.pydocview.DocOptionsService):
    def __init__(self,showGeneralOptions=True, supportedModes=wx.lib.docview.DOC_SDI & wx.lib.docview.DOC_MDI):
        wx.lib.pydocview.DocOptionsService.__init__(self,False,supportedModes=wx.lib.docview.DOC_MDI)
        self._optionsPanels = {}
        self.category_list = []
        self.AddOptionsPanel(_("General"),_("General"),GeneralOption.GeneralOptionsPanel)
        
    def OnOptions(self, event):
        """
        Shows the options dialog, called when the "Options" menu item is selected.
        """
        self.OnOption(option_name = wx.ConfigBase_Get().Read("OptionName",_("General")))
        
    def OnOption(self,option_name):
        if len(self._optionsPanels) == 0:
            return
        optionsDialog = OptionsDialog(wx.GetApp().GetTopWindow(), self._optionsPanels,self.category_list, self._docManager,option_name)
        optionsDialog.CenterOnParent()
        if optionsDialog.ShowModal() == wx.ID_OK:
            optionsDialog.OnOK(optionsDialog)  # wxBug: wxDialog should be calling this automatically but doesn't
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
        
        
        
