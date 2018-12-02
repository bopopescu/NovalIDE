import wx
import Singleton
from consts import _,EDITOR_CONTENT_PANE_NAME

class FullScreenDialog(wx.Dialog):
    """Navigate through Aui Panes"""
    __metaclass__ = Singleton.SingletonNew
    
    def __init__(self, parent,auiMgr):
        """Initialize the navigator window
        @param parent: parent window
        @param auiMgr: wx.aui.AuiManager
        @keyword icon: wx.Bitmap or None
        @keyword title: string (dialog title)

        """
        super(FullScreenDialog, self).__init__(parent, wx.ID_ANY,
                                               _('FullScreen Display'), style=wx.CAPTION)
        self._auimgr = auiMgr
        # Attributes
        self._close_keys = [wx.WXK_ALT, wx.WXK_CONTROL, wx.WXK_RETURN,wx.WXK_ESCAPE]
        self._listBox = None

        # Setup
        self.__DoLayout()

        # Get the panes
        # Event Handlers
        self._listBox.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self._listBox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnItemDoubleClick)

    def __del__(self):
        pass
       #### self.Destroy()

    def __DoLayout(self):
        """Layout the dialog controls
        @param icon: wx.Bitmap or None
        @param title: string

        """
        sz = wx.BoxSizer(wx.VERTICAL)
        self._listBox = wx.ListBox(self, wx.ID_ANY, wx.DefaultPosition,
                                   (180,-1), list(),
                                   wx.LB_SINGLE | wx.NO_BORDER)

        sz.Add(self._listBox, 1, wx.EXPAND)
        sz.Fit(self)
        sz.SetSizeHints(self)
        sz.Layout()
        self.Centre()
        self.SetSizer(sz)
        self.SetAutoLayout(True)

    def OnKeyUp(self, event):
        """Handles wx.EVT_KEY_UP"""
        key_code = event.GetKeyCode()
        # TODO: add setter method for setting the navigation key
        if key_code in self._close_keys:
            self.CloseDialog()
        else:
            event.Skip()

    def PopulateListControl(self):
        """Populates the L{AuiPaneNavigator} with the panes in the AuiMgr"""
        self._listBox.Clear()
        all_panes = self._auimgr.GetAllPanes()
        self._perspective = self._auimgr.SavePerspective()
        for pane in all_panes:
            if pane.name == EDITOR_CONTENT_PANE_NAME or pane.IsMinimized():
                continue
            pane.Hide()
        self._auimgr.Update()
        self._listBox.AppendItems([_("Close Show FullScreen")])

    def OnItemDoubleClick(self, event):
        """Handles the wx.EVT_LISTBOX_DCLICK event"""
        self.CloseDialog()

    def CloseDialog(self):
        """Closes the L{AuiPaneNavigator} dialog"""
        wx.GetApp().GetTopWindow().ShowFullScreen(False)
        self._auimgr.LoadPerspective(self._perspective)
        self.Close()

    def GetCloseKeys(self):
        """Get the list of keys that can dismiss the dialog
        @return: list of long (wx.WXK_*)

        """
        return self._close_keys

    def SetCloseKeys(self, keylist):
        """Set the keys that can be used to dismiss the L{AuiPaneNavigator}
        window.
        @param keylist: list of key codes

        """
        self._close_keys = keylist

    def Show(self):
        # Set focus on the list box to avoid having to click on it to change
        # the tab selection under GTK.
        self.PopulateListControl()
        self._listBox.SetFocus()
        self._listBox.SetSelection(0)
        return super(FullScreenDialog, self).Show()


