import wx
import wx.lib.pydocview
from noval.tool.consts import _,SPACE,HALF_SPACE
from noval.tool.Validator import NumValidator

MAX_WINDOW_MENU_NUM_ITEMS = 30

class WindowMenuService(wx.lib.pydocview.WindowMenuService):
    

    RESTORE_WINDOW_LAYOUT_ID = wx.NewId()
    """description of class"""
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        wx.lib.pydocview.WindowMenuService.InstallControls(self,frame,menuBar,toolBar,statusBar,document)
        

        windowMenuIndex = menuBar.FindMenu(_("&Window"))
        windowMenu = menuBar.GetMenu(windowMenuIndex)
        windowMenu.Append(wx.ID_CLOSE_ALL,_("Close All"),_("Close all open documents"))
        wx.EVT_MENU(frame, wx.ID_CLOSE_ALL, frame.ProcessEvent)
        
        if wx.GetApp().GetUseTabbedMDI():
            windowMenu.Append(self.RESTORE_WINDOW_LAYOUT_ID,_("&Restore Default Layout"),_("Restore default layout of main frame"))
            wx.EVT_MENU(frame, self.RESTORE_WINDOW_LAYOUT_ID, frame.ProcessEvent)
            

    def ProcessEvent(self, event):
        """
        Processes a Window menu event.
        """
        id = event.GetId()
        if id == self.RESTORE_WINDOW_LAYOUT_ID:
            ret = wx.MessageBox(_("Are you sure want to restore the default window layout?"), wx.GetApp().GetAppName(),
                               wx.YES_NO  | wx.ICON_QUESTION,wx.GetApp().MainFrame)
            if ret == wx.YES:
                wx.GetApp().MainFrame.LoadDefaultPerspective()
            return True
        elif id == wx.ID_CLOSE_ALL:
            wx.GetApp().MainFrame.OnCloseAllDocs(event)
            return True
        else:
            return wx.lib.pydocview.WindowMenuService.ProcessEvent(self,event)
            


class WindowsOptionsPanel(wx.Panel):
    """
    """
    def __init__(self, parent, id,size):
        wx.Panel.__init__(self, parent, id,size=size)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        optionsSizer = wx.BoxSizer(wx.VERTICAL)
        config = wx.ConfigBase_Get()
        self._loadLayoutCheckBox = wx.CheckBox(self, -1, _("Load the last window layout at start up"))
        self._loadLayoutCheckBox.SetValue(config.ReadInt("LoadLastWindowLayout", True))
        optionsSizer.Add(self._loadLayoutCheckBox, 0, wx.ALL, HALF_SPACE)
        
        lsizer = wx.BoxSizer(wx.HORIZONTAL)
        self._window_menu_display_number_ctrl = wx.TextCtrl(self, -1, config.Read("WindowMenuDisplayNumber",str(wx.lib.pydocview.WINDOW_MENU_NUM_ITEMS)), size=(30,-1),\
                                validator=NumValidator(_("Window Menu Display Number"),1,MAX_WINDOW_MENU_NUM_ITEMS))
        lsizer.AddMany([(wx.StaticText(self, label=_("Number of Window menus displayed") + "(%d-%d): " % \
                                                            (1,MAX_WINDOW_MENU_NUM_ITEMS)),
                         0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                        (self._window_menu_display_number_ctrl,
                         0, wx.ALIGN_CENTER_VERTICAL)])
        optionsSizer.Add(lsizer, 0, wx.ALL, HALF_SPACE)
        


        self._hideMenubarCheckBox = wx.CheckBox(self, -1, _("Hide menubar When full screen display"))
        self._hideMenubarCheckBox.SetValue(config.ReadInt("HideMenubarFullScreen", False))
        optionsSizer.Add(self._hideMenubarCheckBox, 0, wx.ALL, HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.clear_window_layout_btn = wx.Button(self, -1, _("Clear Window layout configuration information"))
        wx.EVT_BUTTON(self.clear_window_layout_btn, -1, self.ClearWindowLayoutConfiguration)
        lineSizer.Add(self.clear_window_layout_btn, 0, wx.ALIGN_BOTTOM, HALF_SPACE)
        optionsSizer.Add(lineSizer, 0, wx.ALL, HALF_SPACE)
        
        main_sizer.Add(optionsSizer, 0, wx.ALL|wx.EXPAND, SPACE)
        self.SetSizer(main_sizer)
        self.Layout()
        
    def OnOK(self, optionsDialog):
        config = wx.ConfigBase_Get()
        config.WriteInt("LoadLastWindowLayout", self._loadLayoutCheckBox.GetValue())
        config.WriteInt("HideMenubarFullScreen", self._hideMenubarCheckBox.GetValue())
        return True

    def ClearWindowLayoutConfiguration(self,event):
        config = wx.ConfigBase_Get()
        config.DeleteEntry("DefaultPerspective")
        config.DeleteEntry("LastPerspective")
        wx.MessageBox(_("Already Clear Window layout configuration information"))