import wx
import wx.lib.agw.aui as aui
import wx.lib.agw.aui.framemanager as framemanager
from noval.tool.consts import _
import wx.lib.agw.aui.auibar as auibar
import copy

class IDEAuiManager(aui.AuiManager):
    def __init__(self, managed_window=None, agwFlags=None):
        aui.AuiManager.__init__(self,managed_window,agwFlags)
        
    def OnMotion_Other(self, event):
        """
        Sub-handler for the :meth:`OnMotion` event.

        :param `event`: a :class:`MouseEvent` to be processed.
        """
        part = self.HitTest(*event.GetPosition())
        if part and part.type == framemanager.AuiDockUIPart.typePaneButton \
           and self.IsPaneButtonVisible(part):
            if part != self._hover_button:

                if self._hover_button:
                    self.RefreshButton(self._hover_button)

                self._hover_button = part
                self.RefreshButton(part)
                
                if self._hover_button.button.button_id == framemanager.AUI_BUTTON_MINIMIZE:
                    self._frame.SetToolTip(wx.ToolTip(_("Minimize")))
                elif self._hover_button.button.button_id == framemanager.AUI_BUTTON_MAXIMIZE_RESTORE:
                    self._frame.SetToolTip(wx.ToolTip(_("Maximize")))
                elif self._hover_button.button.button_id == framemanager.AUI_BUTTON_CLOSE:
                    self._frame.SetToolTip(wx.ToolTip(_("Close")))

        else:

            if self._hover_button:
                self.RefreshButton(self._hover_button)
            else:
                event.Skip()

            self._hover_button = None
            
    def UpdateNotebook(self):
        # Workout how many notebooks we need.
        max_notebook = -1

        # destroy floating panes which have been
        # redocked or are becoming non-floating
        for paneInfo in self._panes:
            if max_notebook < paneInfo.notebook_id:
                max_notebook = paneInfo.notebook_id

        # We are the master of our domain
        extra_notebook = len(self._notebooks)
        max_notebook += 1

        for i in xrange(extra_notebook, max_notebook):
            self.CreateNotebook()

        # Remove pages from notebooks that no-longer belong there ...
        for nb, notebook in enumerate(self._notebooks):
            pages = notebook.GetPageCount()
            pageCounter, allPages = 0, pages

            # Check each tab ...
            for page in xrange(pages):

                if page >= allPages:
                    break

                window = notebook.GetPage(pageCounter)
                paneInfo = self.GetPane(window)
                if paneInfo.IsOk() and paneInfo.notebook_id != nb:
                    notebook.RemovePage(pageCounter)
                    window.Hide()
                    window.Reparent(self._frame)
                    pageCounter -= 1
                    allPages -= 1

                pageCounter += 1

            notebook.DoSizing()

        # Add notebook pages that aren't there already...
        for paneInfo in self._panes:
            if paneInfo.IsNotebookPage():

                title = (paneInfo.caption == "" and [paneInfo.name] or [paneInfo.caption])[0]

                notebook = self._notebooks[paneInfo.notebook_id]
                page_id = notebook.GetPageIndex(paneInfo.window)

                if page_id < 0:

                    paneInfo.window.Reparent(notebook)
                    notebook.AddPage(paneInfo.window, title, True, paneInfo.icon)

                # Update title and icon ...
                else:

                    notebook.SetPageText(page_id, title)
                    notebook.SetPageBitmap(page_id, paneInfo.icon)

                notebook.DoSizing()

            # Wire-up newly created notebooks
            elif paneInfo.IsNotebookControl() and not paneInfo.window:
                paneInfo.window = self._notebooks[paneInfo.notebook_id]

        # Delete empty notebooks, and convert notebooks with 1 page to
        # normal panes...
        remap_ids = [-1]*len(self._notebooks)
        nb_idx = 0

        for nb, notebook in enumerate(self._notebooks):
            if notebook.GetPageCount() == 1:

                # Convert notebook page to pane...
                window = notebook.GetPage(0)
                child_pane = self.GetPane(window)
                notebook_pane = self.GetPane(notebook)
                if child_pane.IsOk() and notebook_pane.IsOk():

                    child_pane.SetDockPos(notebook_pane)
                    child_pane.window.Hide()
                    child_pane.window.Reparent(self._frame)
                    child_pane.frame = None
                    child_pane.notebook_id = -1
                    if notebook_pane.IsFloating():
                        child_pane.Float()

                    self.DetachPane(notebook)

                    notebook.RemovePage(0)
                    notebook.Destroy()

                else:

                    raise Exception("Odd notebook docking")

            elif notebook.GetPageCount() == 0:

                self.DetachPane(notebook)
                notebook.Destroy()

            else:

                # Correct page ordering. The original wxPython code
                # for this did not work properly, and would misplace
                # windows causing errors.
                notebook.Freeze()
                self._notebooks[nb_idx] = notebook
                pages = notebook.GetPageCount()
                selected = notebook.GetPage(notebook.GetSelection())
                
                is_page_relayout = False
                pages_and_panes = []
                for idx in range(pages):
                    page = notebook.GetPage(idx)
                    pane = self.GetPane(page)
                    pages_and_panes.append((page, pane))
                sorted_pnp = sorted(pages_and_panes, key=lambda tup: tup[1].dock_pos)
                for idx,(page,pane) in enumerate(sorted_pnp):
                    #check the pane page position has been change
                    if page != notebook.GetPage(idx):
                        is_page_relayout = True
                        break
                #if the pane page position has been change,then relay out the pane pages
                if is_page_relayout:
                    # Take each page out of the notebook, group it with
                    # its current pane, and sort the list by pane.dock_pos
                    # order
                    for idx in reversed(range(pages)):
                        page = notebook.GetPage(idx)
                        pane = self.GetPane(page)
                        notebook.RemovePage(idx)

                    # Grab the attributes from the panes which are ordered
                    # correctly, and copy those attributes to the original
                    # panes. (This avoids having to change the ordering
                    # of self._panes) Then, add the page back into the notebook
                    sorted_attributes = [self.GetAttributes(tup[1])
                                         for tup in sorted_pnp]
                    for attrs, tup in zip(sorted_attributes, pages_and_panes):
                        pane = tup[1]
                        self.SetAttributes(pane, attrs)
                        notebook.AddPage(pane.window, pane.caption)

                notebook.SetSelection(notebook.GetPageIndex(selected), True)
                notebook.DoSizing()
                notebook.Thaw()

                # It's a keeper.
                remap_ids[nb] = nb_idx
                nb_idx += 1

        # Apply remap...
        nb_count = len(self._notebooks)

        if nb_count != nb_idx:

            self._notebooks = self._notebooks[0:nb_idx]
            for p in self._panes:
                if p.notebook_id >= 0:
                    p.notebook_id = remap_ids[p.notebook_id]
                    if p.IsNotebookControl():
                        p.SetNameFromNotebookId()

        # Make sure buttons are correct ...
        for notebook in self._notebooks:
            want_max = True
            want_min = True
            want_close = True

            pages = notebook.GetPageCount()
            for page in xrange(pages):

                win = notebook.GetPage(page)
                pane = self.GetPane(win)
                if pane.IsOk():

                    if not pane.HasCloseButton():
                        want_close = False
                    if not pane.HasMaximizeButton():
                        want_max = False
                    if not pane.HasMinimizeButton():
                        want_min = False

            notebook_pane = self.GetPane(notebook)
            if notebook_pane.IsOk():
                if notebook_pane.HasMinimizeButton() != want_min:
                    if want_min:
                        button = aui.AuiPaneButton(aui.AUI_BUTTON_MINIMIZE)
                        notebook_pane.state |= aui.AuiPaneInfo.buttonMinimize
                        notebook_pane.buttons.append(button)

                    # todo: remove min/max

                if notebook_pane.HasMaximizeButton() != want_max:
                    if want_max:
                        button = aui.AuiPaneButton(aui.AUI_BUTTON_MAXIMIZE_RESTORE)
                        notebook_pane.state |= aui.AuiPaneInfo.buttonMaximize
                        notebook_pane.buttons.append(button)

                    # todo: remove min/max

                if notebook_pane.HasCloseButton() != want_close:
                    if want_close:
                        button = aui.AuiPaneButton(aui.AUI_BUTTON_CLOSE)
                        notebook_pane.state |= aui.AuiPaneInfo.buttonClose
                        notebook_pane.buttons.append(button)
        self.UpdateNotebookIcons()
                        
    def UpdateNotebookIcons(self):
        #update notebook page icon
        for nb, notebook in enumerate(self._notebooks):
            notebook.Freeze()
            pages = notebook.GetPageCount()
            for idx in range(pages):
                page = notebook.GetPage(idx)
                pane = self.GetPane(page)
                service = wx.GetApp().GetInstallService(pane.name)
                if service is not None:
                    if hasattr(page,"OnSingleStep"):
                        service_icon = service.GetBreakDebugIcon()
                    else:
                        service_icon = service.GetIcon()
                    if service_icon is not None:
                        notebook.SetPageBitmap(idx, service_icon)
                else:
                    notebook.SetPageBitmap(idx, pane.icon)
            notebook.Thaw()
            
    def GetNotebookPaneId(self,notebook_id):
        pane = framemanager.GetNotebookRoot(self._panes,notebook_id)
        if pane:
            return pane.window
        return None

    def GetAnyPane(self,dock_direction):
        for paneInfo in self._panes:
            if paneInfo.dock_direction_get() == dock_direction and paneInfo.IsShown():
                return paneInfo
        return None
        
    def GetNotebookPaneDirection(self,dock_direction):
        for paneInfo in self._panes:
            if paneInfo.IsNotebookControl() and paneInfo.dock_direction_get() == dock_direction and \
                    isinstance(paneInfo.window,aui.auibook.AuiNotebook):
                return paneInfo
        return None
        

    def AddPane4(self, window, pane_info, target):
        """ See comments on :meth:`AddPane`. """
        
        # check if the pane already exists
        if not self.GetPane(pane_info.window).IsOk():
            if not self.AddPane(window, pane_info):
                return False
        paneInfo = self.GetPane(window)

        if not paneInfo.IsNotebookDockable():
            return self.AddPane1(window, pane_info)
        if not target.IsNotebookDockable() and not target.IsNotebookControl():
            return self.AddPane1(window, pane_info)

        if not target.HasNotebook():
            self.CreateNotebookBase(self._panes, target)

        # Add new item to notebook
        paneInfo.NotebookPage(target.notebook_id)

        # we also want to remove our captions sometimes
        self.RemoveAutoNBCaption(paneInfo)
        self.UpdateNotebook()

        return True
        

    def LoadPerspective(self, layout, update=True, restorecaption=False,minimize_pane=False):
        """
        Loads a layout which was saved with :meth:`SavePerspective`.

        If the `update` flag parameter is ``True``, :meth:`Update` will be
        automatically invoked, thus realizing the saved perspective on screen.

        :param string `layout`: a string which contains a saved AUI layout;
        :param bool `update`: whether to update immediately the window or not;
        :param bool `restorecaption`: ``False``, restore from persist storage,
         otherwise use the caption defined in code.
        """
        #close all docked min panes before restore perspective
        self.CloseDockedMinPanes()

        input = layout

        # check layout string version
        #    'layout1' = wxAUI 0.9.0 - wxAUI 0.9.2
        #    'layout2' = wxAUI 0.9.2 (wxWidgets 2.8)
        index = input.find("|")
        part = input[0:index].strip()
        input = input[index+1:]

        if part != "layout2":
            return False

        # mark all panes currently managed as docked and hidden
        saveCapt = {} # see restorecaption param
        for pane in self._panes:
            pane.Dock().Hide()
            saveCapt[pane.name] = pane.caption

        # clear out the dock array; this will be reconstructed
        self._docks = []

        # replace escaped characters so we can
        # split up the string easily
        input = input.replace("\\|", "\a")
        input = input.replace("\\;", "\b")

        while 1:

            pane = aui.AuiPaneInfo()
            index = input.find("|")
            pane_part = input[0:index].strip()
            input = input[index+1:]

            # if the string is empty, we're done parsing
            if pane_part == "":
                break

            if pane_part[0:9] == "dock_size":
                index = pane_part.find("=")
                val_name = pane_part[0:index]
                value = pane_part[index+1:]

                index = val_name.find("(")
                piece = val_name[index+1:]
                index = piece.find(")")
                piece = piece[0:index]

                vals = piece.split(",")
                dir = int(vals[0])
                layer = int(vals[1])
                row = int(vals[2])
                size = int(value)

                dock = aui.AuiDockInfo()
                dock.dock_direction = dir
                dock.dock_layer = layer
                dock.dock_row = row
                dock.size = size
                self._docks.append(dock)

                continue

            # Undo our escaping as LoadPaneInfo needs to take an unescaped
            # name so it can be called by external callers
            pane_part = pane_part.replace("\a", "|")
            pane_part = pane_part.replace("\b", ";")

            pane = self.LoadPaneInfo(pane_part, pane)

            p = self.GetPane(pane.name)
            # restore pane caption from code
            if restorecaption:
                if pane.name in saveCapt:
                    pane.Caption(saveCapt[pane.name])

            if not p.IsOk():
                if pane.IsNotebookControl():
                    # notebook controls - auto add...
                    self._panes.append(pane)
                    indx = self._panes.index(pane)
                else:
                    # the pane window couldn't be found
                    # in the existing layout -- skip it
                    continue

            else:
                indx = self._panes.index(p)
            pane.window = p.window
            pane.frame = p.frame
            pane.buttons = p.buttons
            self._panes[indx] = pane

            if isinstance(pane.window, auibar.AuiToolBar) and (pane.IsFloatable() or pane.IsDockable()):
                pane.window.SetGripperVisible(True)

        if minimize_pane:
            for p in self._panes:
                if p.IsMinimized():
                    self.MinimizePane(p, False)

        #update the pane icon
        for p in self._panes:
            service = wx.GetApp().GetInstallService(p.name)
            if service is not None:
                service_icon = service.GetIcon()
                if service_icon is not None:
                    p.Icon(service_icon)
                    
        if update:
            self.Update()

        return True
        
    def FindPane(self,pane):
        for paneInfo in self._panes:
            if paneInfo  == pane:
                return paneInfo
        return None
        
    def ClosePane(self, pane_info,destroy_pane_window=True):
        """
        Destroys or hides the pane depending on its flags.

        :param `pane_info`: a :class:`AuiPaneInfo` instance.
        """

        # if we were maximized, restore
        if pane_info.IsMaximized():
            self.RestorePane(pane_info)

        if pane_info.frame:
            if self._agwFlags & aui.AUI_MGR_ANIMATE_FRAMES:
                pane_info.frame.FadeOut()

        # first, hide the window
        if pane_info.window and pane_info.window.IsShown():
            pane_info.window.Show(False)

        # make sure that we are the parent of this window
        if pane_info.window and pane_info.window.GetParent() != self._frame:
            pane_info.window.Reparent(self._frame)

        # if we have a frame, destroy it
        if pane_info.frame:
            pane_info.frame.Destroy()
            pane_info.frame = None

        elif pane_info.IsNotebookPage():
            # if we are a notebook page, remove ourselves...
            # the  code would index out of bounds
            # if the last page of a sub-notebook was closed
            # because the notebook would be deleted, before this
            # code is executed.
            # This code just prevents an out-of bounds error.
            if self._notebooks:
                nid = pane_info.notebook_id
                if nid >= 0 and nid < len(self._notebooks):
                    notebook = self._notebooks[nid]
                    page_idx = notebook.GetPageIndex(pane_info.window)
                    if page_idx >= 0:
                        notebook.RemovePage(page_idx)

        # now we need to either destroy or hide the pane
        to_destroy = 0
        if pane_info.IsDestroyOnClose():
            to_destroy = pane_info.window
            self.DetachPane(to_destroy)
        else:
            if isinstance(pane_info.window, auibar.AuiToolBar) and pane_info.IsFloating():
                tb = pane_info.window
                if pane_info.dock_direction in [AUI_DOCK_LEFT, AUI_DOCK_RIGHT]:
                    tb.SetAGWWindowStyleFlag(tb.GetAGWWindowStyleFlag() | AUI_TB_VERTICAL)

            pane_info.Dock().Hide()

        if pane_info.IsNotebookControl():

            notebook = self._notebooks[pane_info.notebook_id]
            while notebook.GetPageCount():
                window = notebook.GetPage(0)
                notebook.RemovePage(0)
                info = self.GetPane(window)
                if info.IsOk():
                    info.notebook_id = -1
                    info.dock_direction = aui.AUI_DOCK_NONE
                    # Note: this could change our paneInfo reference ...
                    self.ClosePane(info)

        if to_destroy and destroy_pane_window:
            to_destroy.Destroy()
            
    def CloseDockedMinPanes(self):
        panes = copy.copy(self._panes)
        for p in panes:
            if p.name.endswith("_min"):
                p.window.Show(False)
                self.DetachPane(p.window)
                p.Show(False)
                p.Hide()