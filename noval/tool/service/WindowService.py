import wx
import wx.lib.pydocview
from noval.tool.consts import _,SPACE,HALF_SPACE
from noval.tool.Validator import NumValidator
import noval.util.utils as utils
import noval.util.constants as constants

MAX_WINDOW_MENU_NUM_ITEMS = 30

class WindowMenuService(wx.lib.pydocview.WindowMenuService):
    """description of class"""
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        wx.lib.pydocview.WindowMenuService.InstallControls(self,frame,menuBar,toolBar,statusBar,document)
        windowMenu = menuBar.GetWindowsMenu()
        windowMenu.Append(constants.ID_CLOSE_ALL,_("Close All"),_("Close all open documents"))
        wx.EVT_MENU(frame, constants.ID_CLOSE_ALL, frame.ProcessEvent)
        
        if wx.GetApp().GetUseTabbedMDI():
            windowMenu.Append(constants.ID_RESTORE_WINDOW_LAYOUT,_("&Restore Default Layout"),_("Restore default layout of main frame"))
            wx.EVT_MENU(frame, constants.ID_RESTORE_WINDOW_LAYOUT, frame.ProcessEvent)
            wx.EVT_MENU(frame, self.SELECT_MORE_WINDOWS_ID, frame.ProcessEvent)
            
    def ProcessEvent(self, event):
        """
        Processes a Window menu event.
        """
        id = event.GetId()
        if id == constants.ID_RESTORE_WINDOW_LAYOUT:
            ret = wx.MessageBox(_("Are you sure want to restore the default window layout?"), wx.GetApp().GetAppName(),
                               wx.YES_NO  | wx.ICON_QUESTION,wx.GetApp().MainFrame)
            if ret == wx.YES:
                wx.GetApp().MainFrame.LoadDefaultPerspective()
            return True
        elif id == constants.ID_CLOSE_ALL:
            wx.GetApp().MainFrame.OnCloseAllDocs(event)
            return True
        else:
            return wx.lib.pydocview.WindowMenuService.ProcessEvent(self,event)
            

    def BuildWindowMenu(self, currentFrame):
        """
        Builds the Window menu and adds menu items for all of the open documents in the DocManager.
        """
        if wx.GetApp().GetUseTabbedMDI():
            currentFrame = wx.GetApp().GetTopWindow()

        windowMenuIndex = currentFrame.GetMenuBar().FindMenu(_("&Window"))
        windowMenu = currentFrame.GetMenuBar().GetMenu(windowMenuIndex)

        if wx.GetApp().GetUseTabbedMDI():
            notebook = wx.GetApp().GetTopWindow()._notebook
            numPages = notebook.GetPageCount()

            for id in self._selectWinIds:
                item = windowMenu.FindItemById(id)
                if item:
                    windowMenu.DeleteItem(item)
        
            if windowMenu.FindItemById(self.SELECT_MORE_WINDOWS_ID):
                windowMenu.Remove(self.SELECT_MORE_WINDOWS_ID)
            if numPages == 0 and self._sep:
                windowMenu.DeleteItem(self._sep)
                self._sep = None

            if numPages > len(self._selectWinIds):
                for i in range(len(self._selectWinIds), numPages):
                    self._selectWinIds.append(wx.NewId())
                    wx.EVT_MENU(currentFrame, self._selectWinIds[i], self.OnCtrlKeySelect)
                    
            for i in range(0, min(numPages,utils.ProfileGetInt("WindowMenuDisplayNumber",wx.lib.pydocview.WINDOW_MENU_NUM_ITEMS))):
                if i == 0 and not self._sep:
                    self._sep = windowMenu.AppendSeparator()
                if i < 9:
                    menuLabel = "%s\tCtrl+%s" % (notebook.GetPageText(i), i+1)
                else:
                    menuLabel = notebook.GetPageText(i)
                windowMenu.Append(self._selectWinIds[i], menuLabel)    
                
            if numPages > wx.lib.pydocview.WINDOW_MENU_NUM_ITEMS:  # Add the more items item
                if not windowMenu.FindItemById(self.SELECT_MORE_WINDOWS_ID):
                    windowMenu.Append(self.SELECT_MORE_WINDOWS_ID, _("&More Windows..."))
  

    def _GetWindowMenuFrameList(self, currentFrame=None):
        """
        Returns the Frame associated with each menu item in the Window menu.
        """
        frameList = []
        # get list of windows for documents
        for doc in self._docManager.GetDocuments():
            for view in doc.GetViews():
                if hasattr(view,"GetType"):
                    frame = view.GetFrame()
                    if frame not in frameList:
                        if frame == currentFrame and len(frameList) >= WINDOW_MENU_NUM_ITEMS:
                            frameList.insert(WINDOW_MENU_NUM_ITEMS - 1, frame)
                        else:
                            frameList.append(frame)
        return frameList  

    def OnSelectMoreWindows(self, event):
        """
        Called when the "Window/Select More Windows..." menu item is selected and enables user to
        select from the Frames that do not in the Window list.  Useful when there are more than
        10 open frames in the application.
        """
        frames = self._GetWindowMenuFrameList()  # TODO - make the current window the first one
        strings = map(lambda frame: frame.GetTitle(), frames)
        # Should preselect the current window, but not supported by wx.GetSingleChoice
        res = wx.GetSingleChoiceIndex(_("Select a window to show:"),
                                      _("Select Window"),
                                      strings,
                                      wx.GetApp().MainFrame)
        if res == -1:
            return
        frames[res].SetFocus()


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
        self._window_menu_display_number_ctrl = wx.TextCtrl(self, -1, str(config.ReadInt("WindowMenuDisplayNumber",wx.lib.pydocview.WINDOW_MENU_NUM_ITEMS)), size=(30,-1),\
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
        config.WriteInt("WindowMenuDisplayNumber", int(self._window_menu_display_number_ctrl.GetValue()))
        return True

    def ClearWindowLayoutConfiguration(self,event):
        config = wx.ConfigBase_Get()
        config.DeleteEntry("DefaultPerspective")
        config.DeleteEntry("LastPerspective")
        wx.MessageBox(_("Already Clear Window layout configuration information"))