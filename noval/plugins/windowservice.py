from noval import GetApp,_
import noval.iface as iface
import noval.plugin as plugin
import tkinter as tk
from tkinter import ttk,messagebox
import noval.preference as preference
from noval.util import utils
import noval.ui_utils as ui_utils
import noval.consts as consts

MAX_WINDOW_MENU_NUM_ITEMS = 30

##class WindowMenuService(wx.lib.pydocview.WindowMenuService):
##    """description of class"""
##    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
##        wx.lib.pydocview.WindowMenuService.InstallControls(self,frame,menuBar,toolBar,statusBar,document)
##        windowMenu = menuBar.GetWindowsMenu()
##        windowMenu.Append(constants.ID_CLOSE_ALL,_("Close All"),_("Close all open documents"))
##        wx.EVT_MENU(frame, constants.ID_CLOSE_ALL, frame.ProcessEvent)
##        
##        if wx.GetApp().GetUseTabbedMDI():
##            windowMenu.Append(constants.ID_RESTORE_WINDOW_LAYOUT,_("&Restore Default Layout"),_("Restore default layout of main frame"))
##            wx.EVT_MENU(frame, constants.ID_RESTORE_WINDOW_LAYOUT, frame.ProcessEvent)
##            wx.EVT_MENU(frame, self.SELECT_MORE_WINDOWS_ID, frame.ProcessEvent)
##            
##    def ProcessEvent(self, event):
##        """
##        Processes a Window menu event.
##        """
##        id = event.GetId()
##        if id == constants.ID_RESTORE_WINDOW_LAYOUT:
##            ret = wx.MessageBox(_("Are you sure want to restore the default window layout?"), wx.GetApp().GetAppName(),
##                               wx.YES_NO  | wx.ICON_QUESTION,wx.GetApp().MainFrame)
##            if ret == wx.YES:
##                wx.GetApp().MainFrame.LoadDefaultPerspective()
##            return True
##        elif id == constants.ID_CLOSE_ALL:
##            wx.GetApp().MainFrame.OnCloseAllDocs(event)
##            return Truefrom noval.util import utils
##        else:
##            return wx.lib.pydocview.WindowMenuService.ProcessEvent(self,event)
##            
##
##    def BuildWindowMenu(self, currentFrame):
##        """
##        Builds the Window menu and adds menu items for all of the open documents in the DocManager.
##        """
##        if wx.GetApp().GetUseTabbedMDI():
##            currentFrame = wx.GetApp().GetTopWindow()
##
##        windowMenuIndex = currentFrame.GetMenuBar().FindMenu(_("&Window"))
##        windowMenu = currentFrame.GetMenuBar().GetMenu(windowMenuIndex)
##
##        if wx.GetApp().GetUseTabbedMDI():
##            notebook = wx.GetApp().GetTopWindow()._notebook
##            numPages = notebook.GetPageCount()
##
##            for id in self._selectWinIds:
##                item = windowMenu.FindItemById(id)
##                if item:
##                    windowMenu.DeleteItem(item)
##        
##            if windowMenu.FindItemById(self.SELECT_MORE_WINfrom noval.util import utilsDOWS_ID):
##                windowMenu.Remove(self.SELECT_MORE_WINDOWS_ID)
##            if numPages == 0 and self._sep:
##                windowMenu.DeleteItem(self._sep)
##                self._sep = None
##
##            if numPages > len(self._selectWinIds):
##                for i in range(len(self._selectWinIds), numPages):
##                    self._selectWinIds.append(wx.NewId())
##                    wx.EVT_MENU(currentFrame, self._selectWinIds[i], self.OnCtrlKeySelect)
##                    
##            for i in range(0, min(numPages,utils.ProfileGetInt("WindowMenuDisplayNumber",wx.lib.pydocview.WINDOW_MENU_NUM_ITEMS))):
##                if i == 0 and not self._sep:
##                    self._sep = windowMenu.AppendSeparator()
##                if i < 9:
##                    menuLabel = "%s\tCtrl+%s" % (notebook.GetPageText(i), i+1)
##                else:from noval.util import utils
##                    menuLabel = notebook.GetPageText(i)
##                windowMenu.Append(self._selectWinIds[i], menuLabel)    
##                
##            if numPages > wx.lib.pydocview.WINDOW_MENU_NUM_ITEMS:  # Add the more items item
##                if not windowMenu.FindItemById(self.SELECT_MORE_WINDOWS_ID):
##                    windowMenu.Append(self.SELECT_MORE_WINDOWS_ID, _("&More Windows..."))
##  
##
##    def _GetWindowMenuFrameList(self, currentFrame=None):
##        """
##        Returns the Frame associated with each menu item in the Window menu.
##        """
##        frameList = []
##        # get list of windows for documents
##        for doc in self._docManager.GetDocuments():
##            for view in doc.GetViews():
##                if hasattr(view,"GetType"):
##                    frame = view.GetFrame()
##                    if frame not in frameList:
##                        if frame == currentFrame and len(framimport noval.preference as preferenceeList) >= WINDOW_MENU_NUM_ITEMS:
##                            frameList.insert(WINDOW_MENU_NUM_ITEMS - 1, frame)
##                        else:
##                            frameList.append(frame)
##        return frameList  
##
##    def OnSelectMoreWindows(self, event):
##        """
##        Called when the "Window/Select More Windows..." menu item is selected and enables user to
##        select from the Frames that do not in the Window list.  Useful when there are more than
##        10 open frames in the application.
##        """
##        frames = self._GetWindowMenuFrameList()  # TODO - make the current window the first one
##        strings = map(lambda frame: frame.GetTitle(), frames)
##        # Should preselect the current window, but not supported by wx.GetSingleChoice
##        res = wx.GetSingleChoiceIndex(_("Select a window to show:"),
##                                      _("Select Window"),
##                                      strings,
##                                      wx.GetApp().MainFrame)
##        if res == -1:
##            return
##        frames[res].SetFocus()
##

class WindowsOptionPanel(ui_utils.CommonOptionPanel):
    """
    """
    def __init__(self, parent):
        ui_utils.CommonOptionPanel.__init__(self, parent)
        
        self._loadLayoutCheckVar = tk.IntVar(value=utils.profile_get_int("LoadLastPerspective", True))
        loadLayoutCheckBox = ttk.Checkbutton(self.panel, text=_("Load the last window layout at start up"),variable=self._loadLayoutCheckVar)
        loadLayoutCheckBox.pack(fill=tk.X)

##        self._window_menu_display_number_ctrl = wx.TextCtrl(self, -1, str(config.ReadInt("WindowMenuDisplayNumber",wx.lib.pydocview.WINDOW_MENU_NUM_ITEMS)), size=(30,-1),\
##                                validator=NumValidator(_("Window Menu Display Number"),1,MAX_WINDOW_MENU_NUM_ITEMS))
##        lsizer.AddMany([(wx.StaticText(self, label=_("Number of Window menus displayed") + "(%d-%d): " % \
##                                                            (1,MAX_WINDOW_MENU_NUM_ITEMS)),
##                         0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
##                        (self._window_menu_display_number_ctrl,
##                         0, wx.ALIGN_CENTER_VERTICAL)])

        self._hideMenubarCheckVar = tk.IntVar(value=utils.profile_get_int("HideMenubarFullScreen", False))
        hideMenubarCheckBox = ttk.Checkbutton(self.panel, text= _("Hide menubar When full screen display"),variable=self._hideMenubarCheckVar)
        hideMenubarCheckBox.pack(fill=tk.X)
        
        self._useCustommenubarCheckVar = tk.IntVar(value=utils.profile_get_int("USE_CUSTOM_MENUBAR", False))
        useCustommenubarCheckBox = ttk.Checkbutton(self.panel, text= _("Use custom menubar"),variable=self._useCustommenubarCheckVar)
        useCustommenubarCheckBox.pack(fill=tk.X)
        
        row = ttk.Frame(self.panel)
        self._scaling_label = ttk.Label(row, text=_("UI scaling factor:"))
        self._scaling_label.pack(fill=tk.X,side=tk.LEFT)
        self._scaleVar = tk.StringVar(value=utils.profile_get('UI_SCALING_FACTOR',''))
        scalings = sorted({0.5, 0.75, 1.0, 1.25, 1.33, 1.5, 2.0, 2.5, 3.0, 4.0})
        combobox = ttk.Combobox(
            row,
            exportselection=False,
            textvariable=self._scaleVar,
            state="readonly",
            height=15,
            values=tuple(scalings),
        )
        combobox.pack(fill=tk.X,side=tk.LEFT)
        row.pack(fill=tk.X)
        clear_window_layout_btn = ttk.Button(self.panel, text=_("Clear Window layout configuration information"),command=self.ClearWindowLayoutConfiguration)
        clear_window_layout_btn.pack(anchor=tk.W,pady=consts.DEFAUT_HALF_CONTRL_PAD_Y)
        
    def OnOK(self, optionsDialog):
        if utils.profile_get('UI_SCALING_FACTOR','') != self._scaleVar.get():
            messagebox.showinfo(GetApp().GetAppName(),_("Scale changes will not appear until the application is restarted."),parent=self)
            
        if utils.profile_get_int('USE_CUSTOM_MENUBAR',0) != self._useCustommenubarCheckVar.get():
            messagebox.showinfo(GetApp().GetAppName(),_("Menubar changes will not appear until the application is restarted."),parent=self)
            
        utils.profile_set("LoadLastPerspective", self._loadLayoutCheckVar.get())
        utils.profile_set("HideMenubarFullScreen", self._hideMenubarCheckVar.get())
        utils.profile_set("USE_CUSTOM_MENUBAR", self._useCustommenubarCheckVar.get())
        scale = self._scaleVar.get()
        if not scale:
            scale = "default"
        utils.profile_set("UI_SCALING_FACTOR", scale)
      #  config.WriteInt("WindowMenuDisplayNumber", int(self._window_menu_display_number_ctrl.GetValue()))
        return True

    def ClearWindowLayoutConfiguration(self):
        config = GetApp().GetConfig()
        config.DeleteEntry("DefaultPerspective")
        config.DeleteEntry("LastPerspective")
        messagebox.showinfo(GetApp().GetAppName(),_("Already Clear Window layout configuration information"))
        
class WindowServiceLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        preference.PreferenceManager().AddOptionsPanelClass("Misc","Appearance",WindowsOptionPanel)

