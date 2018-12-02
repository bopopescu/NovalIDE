import wx
import wx.lib.agw.aui as aui
import TabCtrl
import wx.lib.agw.aui.framemanager as framemanager
import noval.util.utils as utils
import noval.tool.consts as consts


class IDEAuiNotebook(aui.AuiNotebook):
    def OnTabRightDown(self, event):
        """
        Handles right clicks for the notebook, enabling users to either close
        a tab or select from the available documents if the user clicks on the
        notebook's white space.
        """
        aui.AuiNotebook.OnTabRightDown(self, event)
        x,y = event.X,event.Y
        index = event.GetSelection()
        menu = wx.Menu()
        menuBar = wx.GetApp().GetTopWindow().GetMenuBar()
        if utils.ProfileGetInt("TabsAlignment",consts.TabAlignTop) == consts.TabAlignBottom:
            wx.GetApp().MainFrame.PopupTabMenu(index,x,self.GetSize().GetHeight() - y)
        else:
            wx.GetApp().MainFrame.PopupTabMenu(index,x,y)

    def GetActiveTabCtrl(self):
        """
        Returns the active tab control. It is called to determine which control
        gets new windows being added.
        """

        if self._curpage >= 0 and self._curpage < self._tabs.GetPageCount():

            # find the tab ctrl with the current page
            ctrl, idx = self.FindTab(self._tabs.GetPage(self._curpage).window)
            if ctrl:
                return ctrl

        # no current page, just find the first tab ctrl
        all_panes = self._mgr.GetAllPanes()
        for pane in all_panes:
            if pane.name == "dummy":
                continue

            tabframe = pane.window
            return tabframe._tabs

        # If there is no tabframe at all, create one
        tabframe = aui.TabFrame(self)
        tabframe.SetTabCtrlHeight(self._tab_ctrl_height)
        self._tab_id_counter += 1
        tabframe._tabs = TabCtrl.IDEAuiTabCtrl(self, self._tab_id_counter)

        tabframe._tabs.SetAGWFlags(self._agwFlags)
        tabframe._tabs.SetArtProvider(self._tabs.GetArtProvider().Clone())
        self._mgr.AddPane(tabframe, framemanager.AuiPaneInfo().Center().CaptionVisible(False).
                          PaneBorder((self._agwFlags & aui.AUI_NB_SUB_NOTEBOOK) == 0))

        self._mgr.Update()

        return tabframe._tabs