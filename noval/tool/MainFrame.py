import os
import wx.lib.pydocview
import wx
import noval.util.sysutils as sysutilslib
import noval.util.fileutils as fileutils
import noval.util.strutils as strutils
import noval.tool.syntax.lang as lang
import noval.tool.syntax.syntax as syntax
import consts
import noval.tool.service.navigation.NavigationService as NavigationService
import noval.util.appdirs as appdirs
from wx.lib.pubsub import pub as Publisher
import STCTextEditor
import images
import noval.tool.service.MessageService as MessageService
import noval.tool.aui as aui
import FullScreenDialog
import DocumentOption
import noval.util.utils as utils
import noval.util.plugin as plugin
import MainWindowAddOn
import noval.util.constants as constants
from MenuBar import MainMenuBar
from noval.util.popupmenu import PopupMenu

_ = consts._


class DocFrameBase():

    def RegisterMsg(self):
        Publisher.subscribe(self.OnUpdatePosCache,NavigationService.NOVAL_MSG_UI_STC_POS_JUMPED)

    def OnUpdatePosCache(self, msg):
        """Update the position cache for buffer position changes
        @param msg: message data

        """
        data = msg
        if data.has_key('prepos'):
            NavigationService.NavigationService.DocMgr.AddNaviPosition(data['fname'], data['prepos'])
        NavigationService.NavigationService.DocMgr.AddNaviPosition(data['fname'], data['pos'])

    def GetActiveTextView(self):
        active_book = self.GetActiveChild()
        if not active_book:
            return None
        doc_view = active_book.GetView()
        return doc_view if isinstance(doc_view,STCTextEditor.TextView) else None

    def CreateIDEDefaultToolBar(self):
        """
        Creates the default ToolBar.
        """
        if sysutilslib.isWindows():
            #do not use default toolbar in windows,hide the default toolbar to show frame when mouse hover on Close,Maximize,Minimize button
            self._toolBar = wx.ToolBar(self,style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        else:
            self._toolBar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
            
        self._toolBar.AddSimpleTool(constants.ID_NEW, images.load("toolbar/new.png"), _("New"), _("Creates a new document"))
        self._toolBar.AddSimpleTool(constants.ID_OPEN, images.load("toolbar/open.png"), _("Open"), _("Opens an existing document"))
        self._toolBar.AddSimpleTool(constants.ID_SAVE, images.load("toolbar/save.png"), _("Save"), _("Saves the active document"))
        self._toolBar.AddSimpleTool(constants.ID_SAVEALL, images.load("toolbar/saveall.png"), _("Save All"), _("Saves all the active documents"))
        self._toolBar.AddSeparator()
        self._toolBar.AddSimpleTool(constants.ID_PRINT, images.load("toolbar/print.png"), _("Print"), _("Displays full pages"))
        self._toolBar.AddSimpleTool(constants.ID_PRINT_PREVIEW, images.load("toolbar/preview.png"), _("Print Preview"), _("Prints the active document"))
        self._toolBar.AddSeparator()
        self._toolBar.AddSimpleTool(constants.ID_CUT, images.load("toolbar/cut.png"), _("Cut"), _("Cuts the selection and puts it on the Clipboard"))
        self._toolBar.AddSimpleTool(constants.ID_COPY, images.load("toolbar/copy.png"), _("Copy"), _("Copies the selection and puts it on the Clipboard"))
        self._toolBar.AddSimpleTool(constants.ID_PASTE, images.load("toolbar/paste.png"), _("Paste"), _("Inserts Clipboard contents"))
        self._toolBar.AddSimpleTool(constants.ID_UNDO, images.load("toolbar/undo.png"), _("Undo"), _("Reverses the last action"))
        self._toolBar.AddSimpleTool(constants.ID_REDO, images.load("toolbar/redo.png"), _("Redo"), _("Reverses the last undo"))
        self._toolBar.Realize()
        self._toolBar.Show(wx.ConfigBase_Get().ReadInt("ViewToolBar", True))
        return self._toolBar

    def CreateIDEDefaultMenuBar(self, sdi=False):
        """
        Creates the default MenuBar.  Contains File, Edit, View, Tools, and Help menus.
        """
  
        menuBar = MainMenuBar()

        fileMenu = PopupMenu(toolbar=self._toolBar)
        item = wx.MenuItem(fileMenu,constants.ID_NEW,_("&New...\tCtrl+N"), _("Creates a new document"), wx.ITEM_NORMAL)
        item.SetBitmap(self._toolBar.FindById(constants.ID_NEW).GetBitmap())
        fileMenu.AppendItem(item)
        
        item = wx.MenuItem(fileMenu,constants.ID_OPEN, _("&Open...\tCtrl+O"), _("Opens an existing document"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_OPEN).GetBitmap())
        fileMenu.AppendItem(item)
        
        fileMenu.Append(constants.ID_CLOSE, _("&Close\tCtrl+W"), _("Closes the active document"))
        if not sdi:
            fileMenu.Append(constants.ID_CLOSE_ALL, _("Close A&ll"), _("Closes all open documents"))
        fileMenu.AppendSeparator()
        
        item = wx.MenuItem(fileMenu,constants.ID_SAVE, _("&Save\tCtrl+S"), _("Saves the active document"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_SAVE).GetBitmap())
        fileMenu.AppendItem(item)
        
        fileMenu.Append(constants.ID_SAVEAS, _("Save &As..."), _("Saves the active document with a new name"))
        
        item = wx.MenuItem(fileMenu,constants.ID_SAVEALL, _("Save All\tCtrl+Shift+A"), _("Saves the all active documents"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_SAVEALL).GetBitmap())
        fileMenu.AppendItem(item)
        
        wx.EVT_MENU(self, constants.ID_SAVEALL, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, constants.ID_SAVEALL, self.ProcessUpdateUIEvent)
        fileMenu.AppendSeparator()
        
        item = wx.MenuItem(fileMenu,constants.ID_PRINT, _("&Print\tCtrl+P"), _("Prints the active document"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_PRINT).GetBitmap())
        fileMenu.AppendItem(item)
        
        item = wx.MenuItem(fileMenu,constants.ID_PRINT_PREVIEW, _("Print Pre&view"), _("Displays full pages"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_PRINT_PREVIEW).GetBitmap())
        fileMenu.AppendItem(item)
        
        item = wx.MenuItem(fileMenu,constants.ID_PRINT_SETUP, _("Page Set&up"), _("Changes page layout settings"))
        #item.SetBitmap(images.load("page.png"))
        fileMenu.AppendItem(item)
        
        fileMenu.AppendSeparator()
        if wx.Platform == '__WXMAC__':
            item = wx.MenuItem(fileMenu,constants.ID_EXIT, _("&Quit"), _("Closes this program"))
        else:
            item = wx.MenuItem(fileMenu,constants.ID_EXIT, _("E&xit"), _("Closes this program"))
        item.SetBitmap(images.load("exit.png"))
        fileMenu.AppendItem(item)
        
        self._docManager.FileHistoryUseMenu(fileMenu)
        self._docManager.FileHistoryAddFilesToMenu()
        menuBar.Append(fileMenu, _("&File"))

        editMenu = PopupMenu(toolbar=self._toolBar)
        item = wx.MenuItem(editMenu,constants.ID_UNDO, _("&Undo\tCtrl+Z"), _("Reverses the last action"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_UNDO).GetBitmap())
        editMenu.AppendItem(item)
        
        item = wx.MenuItem(editMenu,constants.ID_REDO, _("&Redo\tCtrl+Y"), _("Reverses the last undo"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_REDO).GetBitmap())
        editMenu.AppendItem(item)
        editMenu.AppendSeparator()
        item = wx.MenuItem(editMenu,constants.ID_CUT, _("Cu&t\tCtrl+X"), _("Cuts the selection and puts it on the Clipboard"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_CUT).GetBitmap())
        editMenu.AppendItem(item)
        
        wx.EVT_MENU(self, constants.ID_CUT, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, constants.ID_CUT, self.ProcessUpdateUIEvent)
        item = wx.MenuItem(editMenu,constants.ID_COPY, _("&Copy\tCtrl+C"), _("Copies the selection and puts it on the Clipboard"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_COPY).GetBitmap())
        editMenu.AppendItem(item)
        
        wx.EVT_MENU(self, constants.ID_COPY, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, constants.ID_COPY, self.ProcessUpdateUIEvent)
        item = wx.MenuItem(editMenu,constants.ID_PASTE, _("&Paste\tCtrl+V"), _("Inserts Clipboard contents"))
        #item.SetBitmap(self._toolBar.FindById(constants.ID_PASTE).GetBitmap())
        editMenu.AppendItem(item)
        
        wx.EVT_MENU(self, constants.ID_PASTE, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, constants.ID_PASTE, self.ProcessUpdateUIEvent)
        item = wx.MenuItem(editMenu,constants.ID_CLEAR, _("&Delete"), _("Erases the selection"))
        item.SetBitmap(images.load("delete.png"))
        editMenu.AppendItem(item)
        wx.EVT_MENU(self, constants.ID_CLEAR, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, constants.ID_CLEAR, self.ProcessUpdateUIEvent)
        editMenu.AppendSeparator()
        editMenu.Append(constants.ID_SELECTALL, _("Select A&ll\tCtrl+A"), _("Selects all available data"))
        wx.EVT_MENU(self, constants.ID_SELECTALL, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, constants.ID_SELECTALL, self.ProcessUpdateUIEvent)
        menuBar.Append(editMenu, _("&Edit"))
        if sdi:
            if self.GetDocument() and self.GetDocument().GetCommandProcessor():
                self.GetDocument().GetCommandProcessor().SetEditMenu(editMenu)

        viewMenu = PopupMenu(toolbar=self._toolBar)
        viewMenu.AppendCheckItem(constants.ID_VIEW_TOOLBAR, _("&Toolbar"), _("Shows or hides the toolbar"))
        wx.EVT_MENU(self, constants.ID_VIEW_TOOLBAR, self.OnViewToolBar)
        wx.EVT_UPDATE_UI(self, constants.ID_VIEW_TOOLBAR, self.OnUpdateViewToolBar)
        viewMenu.AppendCheckItem(constants.ID_VIEW_STATUSBAR, _("&Status Bar"), _("Shows or hides the status bar"))
        wx.EVT_MENU(self, constants.ID_VIEW_STATUSBAR, self.OnViewStatusBar)
        wx.EVT_UPDATE_UI(self, constants.ID_VIEW_STATUSBAR, self.OnUpdateViewStatusBar)
        menuBar.Append(viewMenu, _(consts.VIEW_MENU_ORIG_NAME))

        helpMenu = PopupMenu(toolbar=self._toolBar)
        item = wx.MenuItem(helpMenu,constants.ID_ABOUT, _(_("About %s") % wx.GetApp().GetAppName()), _("Displays program information, version number, and copyright"))
        item.SetBitmap(images.load("about.png"))
        helpMenu.AppendItem(item)
        menuBar.Append(helpMenu, _("&Help"))

        wx.EVT_MENU(self, constants.ID_ABOUT, self.OnAbout)
        wx.EVT_UPDATE_UI(self, constants.ID_ABOUT, self.ProcessUpdateUIEvent)  # Using ID_ABOUT to update the window menu, the window menu items are not triggering

        if sdi:  # TODO: Is this really needed?
            wx.EVT_COMMAND_FIND_CLOSE(self, -1, self.ProcessEvent)
            
        return menuBar

    def _InitFrame(self, embeddedWindows, minSize):
        """
        Initializes the frame and creates the default menubar, toolbar, and status bar.
        """
        if sysutilslib.isWindows():
            self._embeddedWindows = []
            self.SetDropTarget(wx.lib.pydocview._DocFrameFileDropTarget(self._docManager, self))

            if wx.GetApp().GetDefaultIcon():
                self.SetIcon(wx.GetApp().GetDefaultIcon())

            wx.EVT_MENU(self, constants.ID_ABOUT, self.OnAbout)
            wx.EVT_SIZE(self, self.OnSize)

            self.InitializePrintData()

            toolBar = self.CreateIDEDefaultToolBar()
            #must add toobar to pane manager
            self._mgr.AddPane(toolBar, aui.AuiPaneInfo().Name(consts.TOOLBAR_PANE_NAME).
                              Top().Layer(1).CaptionVisible(False).CloseButton(False).PaneBorder(False))
            menuBar = self.CreateIDEDefaultMenuBar()
            statusBar = self.CreateDefaultStatusBar()

            config = wx.ConfigBase_Get()
            if config.ReadInt("MDIFrameMaximized", False):
                # wxBug: On maximize, statusbar leaves a residual that needs to be refereshed, happens even when user does it
                self.Maximize()

            self.CreateEmbeddedWindows(embeddedWindows, minSize)
            self._LayoutFrame()

            if wx.Platform == '__WXMAC__':
                self.SetMenuBar(menuBar)  # wxBug: Have to set the menubar at the very end or the automatic MDI "window" menu doesn't get put in the right place when the services add new menus to the menubar

            wx.GetApp().SetTopWindow(self)  # Need to do this here in case the services are looking for wx.GetApp().GetTopWindow()
            for service in wx.GetApp().GetServices():
                service.InstallControls(self, menuBar = menuBar, toolBar = toolBar, statusBar = statusBar)
                if hasattr(service, "ShowWindow"):
                    service.ShowWindow()  # instantiate service windows for correct positioning, we'll hide/show them later based on user preference
            
            if wx.Platform != '__WXMAC__':
                self.SetMenuBar(menuBar)  # wxBug: Have to set the menubar at the very end or the automatic MDI "window" menu doesn't get put in the right place when the services add new menus to the menubar

        else:
            wx.lib.pydocview.DocMDIParentFrameMixIn._InitFrame(self, embeddedWindows, minSize)
            menuBar = self.GetMenuBar()
            
        #mdi parent window does not support fullscreen and load last perspective
        if not wx.GetApp().GetUseTabbedMDI():
            return
        
        #save default frame layout only once when startup first
        if not utils.ProfileGet('DefaultPerspective',''):
            default_perspective = self._mgr.SavePerspective()
            utils.ProfileSet('DefaultPerspective',default_perspective)
            
        #load last frame layout every startup
        last_perspective = utils.ProfileGet("LastPerspective","")
        if last_perspective and utils.ProfileGetInt("LoadLastWindowLayout",True):
            self._mgr.LoadPerspective(last_perspective)
            
        #show fullscreen
        viewMenu = menuBar.GetViewMenu()
        item = wx.MenuItem(viewMenu,constants.ID_SHOW_FULLSCREEN, _("Show FullScreen"), _("Show the window in fullscreen"),kind=wx.ITEM_NORMAL  )
        item.SetBitmap(images.load("monitor.png"))
        viewMenu.AppendItem(item)
        wx.EVT_MENU(self, constants.ID_SHOW_FULLSCREEN, self.ProcessEvent)
        
    def InitPlugins(self):
        # Setup Plugins after locale as they may have resource that need to be loaded.
        plgmgr = plugin.PluginManager()
        wx.GetApp().SetPluginManager(plgmgr)
        addons = MainWindowAddOn.MainWindowAddOn(plgmgr)
        addons.Init(self)
        self._plugin_handlers['menu'].extend(addons.GetEventHandlers())
        self._plugin_handlers['ui'].extend(addons.GetEventHandlers(ui_evt=True))
        self.InitPluginMenus()

    def InitPluginMenus(self):
        for menu_item_command in self._plugin_handlers['menu']:
            wx.EVT_MENU(self, menu_item_command[0], menu_item_command[1])
            
        for menu_update_item_command in self._plugin_handlers['ui']:
            wx.EVT_UPDATE_UI(self, menu_update_item_command[0], menu_update_item_command[1])
        
class IDEDocTabbedParentFrame(wx.lib.pydocview.DocTabbedParentFrame,DocFrameBase):
    
    # wxBug: Need this for linux. The status bar created in pydocview is
    # replaced in IDE.py with the status bar for the code editor. On windows
    # this works just fine, but on linux the pydocview status bar shows up near
    # the top of the screen instead of disappearing. 

    def __init__(self, docManager, frame, id, title, pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_FRAME_STYLE, name = "DocTabbedParentFrame", embeddedWindows = 0, minSize=20):
        
        self._notebook_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_TAB_EXTERNAL_MOVE | wx.NO_BORDER|aui.AUI_NB_WINDOWLIST_BUTTON
        if utils.ProfileGetInt("TabsAlignment",consts.TabAlignTop) == consts.TabAlignBottom:
            self._notebook_style |= aui.AUI_NB_BOTTOM
        if not utils.ProfileGetInt("ShowCloseButton",True):
            self._notebook_style &= ~(aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
            self._notebook_style |= aui.AUI_NB_CLOSE_BUTTON
        ###5 is chrome style
        tab_index = utils.ProfileGetInt("TabStyle",DocumentOption.DocumentOptionsPanel.TabArts.index(aui.ChromeTabArt))
        self._notebook_theme = tab_index
        
        wx.lib.pydocview.DocTabbedParentFrame.__init__(self,docManager,frame,id,title,pos,size,style,name,embeddedWindows,minSize)
        wx.EVT_MENU_RANGE(self, consts.ID_MRU_FILE1, consts.ID_MRU_FILE20, self.OnMRUFile)
        self.RegisterMsg()
        self._current_document = None
        self._perspective = None
        self._plugin_handlers = dict(menu=list(), ui=list())
        self.InitPlugins()
    
    def CreateDefaultStatusBar(self):
       pass
       
    def GetToolBar(self):
        return self._toolBar
        
    def CreateDefaultToolBar(self):
        return DocFrameBase.CreateIDEDefaultToolBar(self)
        
    def CreateDefaultMenuBar(self):
        return DocFrameBase.CreateIDEDefaultMenuBar(self)
        
    def OnViewToolBar(self, event):
        """
        Toggles whether the ToolBar is visible.
        """
        if sysutilslib.isWindows():
            self._mgr.GetPane(consts.TOOLBAR_PANE_NAME).Show(not self._toolBar.IsShown())
            self._LayoutFrame()
        else:
            wx.lib.pydocview.DocFrameMixIn.OnViewToolBar(self,event)

    def ProcessEvent(self, event):
        if event.GetId() == constants.ID_SHOW_FULLSCREEN:
            if not self.IsFullScreen():
                if utils.ProfileGetInt("HideMenubarFullScreen", False):
                    self.ShowFullScreen(True)
                else:
                    self.ShowFullScreen(True,style = wx.FULLSCREEN_NOTOOLBAR|
                                wx.FULLSCREEN_NOSTATUSBAR|wx.FULLSCREEN_NOBORDER|wx.FULLSCREEN_NOCAPTION)
                FullScreenDialog.FullScreenDialog(self,self._mgr).Show()
            else:
                FullScreenDialog.FullScreenDialog(self,self._mgr).CloseDialog()
            return True
        else:
            return wx.lib.pydocview.DocTabbedParentFrame.ProcessEvent(self,event)
            
    def _InitFrame(self, embeddedWindows, minSize):
        DocFrameBase._InitFrame(self, embeddedWindows, minSize)
 
    def AppendMenuItem(self,id,menu,name,callback,separator=False,bmp=None):
        item = wx.MenuItem(menu,id,name,"", wx.ITEM_NORMAL)
        if bmp:
            item.SetBitmap(bmp)
        wx.EVT_MENU(self, id, callback)
        menu.AppendItem(item)   
        if separator:
            menu.AppendSeparator()
           
    def OnCloseDoc(self,event):
        self._current_document.DeleteAllViews()
        
    def OnCloseAllDocs(self,event):
        self.CloseAllWithoutDoc(closeall=True)
        self.GetStatusBar().Reset()
        
    def OnOpenPathInExplorer(self,event):
        err_code,msg = fileutils.open_file_directory(self._current_document.GetFilename())
        if err_code != consts.ERROR_OK:
            wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
            
    def OnOpenPathInTerminator(self,event):
        err_code,msg = fileutils.open_path_in_terminator(os.path.dirname(self._current_document.GetFilename()))
        if err_code != consts.ERROR_OK:
            wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
            
    def OnCopyFilePath(self,event):
        sysutilslib.CopyToClipboard(self._current_document.GetFilename())
        
    def OnCopyFileName(self,event):
        sysutilslib.CopyToClipboard(os.path.basename(self._current_document.GetFilename()))
        
    def OnNewModule(self,event):
        flags = wx.lib.docview.DOC_NEW
        lexer = syntax.LexerManager().GetLexer(lang.ID_LANG_PYTHON)
        temp = wx.GetApp().GetDocumentManager().FindTemplateForPath("test.%s" % lexer.GetDefaultExt())
        newDoc = temp.CreateDocument("", flags)
        if newDoc:
            newDoc.SetDocumentName(temp.GetDocumentName())
            newDoc.SetDocumentTemplate(temp)
            newDoc.OnNewDocument()
            
    def OnSaveFileDocument(self,event):
        self._current_document.Save()
        
    def OnSaveFileAsDocument(self,event):
        self.GetDocumentManager().SaveAsDocument(self._current_document)
        
    def OnCopyModuleName(self,event):
        sysutilslib.CopyToClipboard(strutils.GetFilenameWithoutExt(self._current_document.GetFilename()))
        
    def OnCloseAllWithoutDoc(self,event):
        self.CloseAllWithoutDoc(False)
        
    def CloseAllWithoutDoc(self,closeall=False):
        for i in range(self._notebook.GetPageCount()-1, -1, -1): # Go from len-1 to 0
                doc = self._notebook.GetPage(i).GetView().GetDocument()
                if doc != self._current_document or closeall:
                    if not self.GetDocumentManager().CloseDocument(doc, False):
                        break
                        
    def MaximizeEditorWindow(self,event):
        
        is_maximized = True
        for pane in self._mgr.GetAllPanes():
            if pane.name == consts.EDITOR_CONTENT_PANE_NAME or pane.name == consts.TOOLBAR_PANE_NAME or not pane.IsShown() or \
                    pane.IsNotebookPage() or isinstance(pane.window,aui.auibar.AuiToolBar):
                continue
            if not pane.IsMinimized():
                is_maximized = False
                break
        if not is_maximized:
            self._perspective = self._mgr.SavePerspective()
        all_panes = self._mgr.GetAllPanes()
        for pane in all_panes:
            if pane.name == consts.EDITOR_CONTENT_PANE_NAME or pane.IsMinimized() or pane.name == consts.TOOLBAR_PANE_NAME or \
                    pane.IsNotebookPage() or not pane.IsShown() or isinstance(pane.window,aui.auibar.AuiToolBar):
                continue
            self._mgr.MinimizePane(pane)
        
    def RestoreEditorWindow(self,event):
        if self._perspective is None:
            return
        self._mgr.LoadPerspective(self._perspective)
        
    def CreateNotebook(self):
        # create the notebook off-window to avoid flicker
        client_size = self.GetClientSize()
        if wx.Platform != "__WXMAC__":
            self._notebook = aui.IDEAuiNotebook(self, -1,wx.Point(client_size.x, client_size.y),
                              wx.Size(430, 200),agwStyle=self._notebook_style)
            arts = [aui.AuiDefaultTabArt, aui.AuiSimpleTabArt, aui.VC71TabArt, aui.FF2TabArt,
                    aui.VC8TabArt, aui.ChromeTabArt]

            art = arts[self._notebook_theme]()
            self._notebook.SetArtProvider(art)
            #set the notebook background as white background
            self._notebook.GetAuiManager().GetArtProvider()._background_brush = wx.WHITE_BRUSH
        else:
            self._notebook = wx.Listbook(self, wx.NewId(), style=wx.LB_LEFT)
        if wx.Platform != "__WXMAC__":
            wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self._notebook.GetId(), self.OnNotebookPageChanged)
        else:
            wx.EVT_LISTBOOK_PAGE_CHANGED(self, self._notebook.GetId(), self.OnNotebookPageChanged)
        self._notebook.SetBackgroundColour(wx.WHITE_BRUSH.GetColour())

        templates = wx.GetApp().GetDocumentManager().GetTemplates()
        iconList = wx.ImageList(16, 16, initialCount = len(templates))
        self._iconIndexLookup = []
        for template in templates:
            icon = template.GetIcon()
            if icon:
                if icon.GetHeight() != 16 or icon.GetWidth() != 16:
                    icon.SetHeight(16)
                    icon.SetWidth(16)
                    if wx.GetApp().GetDebug():
                        print "Warning: icon for '%s' isn't 16x16, not crossplatform" % template._docTypeName
                iconIndex = iconList.AddIcon(icon)
                self._iconIndexLookup.append((template, iconIndex))

        icon = wx.lib.pydocview.Blank.GetIcon()
        if icon.GetHeight() != 16 or icon.GetWidth() != 16:
            icon.SetHeight(16)
            icon.SetWidth(16)
            if wx.GetApp().GetDebug():
                print "Warning: getBlankIcon isn't 16x16, not crossplatform"
        self._blankIconIndex = iconList.AddIcon(icon)
        self._notebook.AssignImageList(iconList)
        
        self._mgr = aui.IDEAuiManager(agwFlags=aui.AUI_MGR_DEFAULT |
                                                 aui.AUI_MGR_TRANSPARENT_DRAG |
                                                 aui.AUI_MGR_TRANSPARENT_HINT |
                                                 aui.AUI_MGR_ALLOW_ACTIVE_PANE)
        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow(self)             
        self._mgr.AddPane(self._notebook, aui.AuiPaneInfo().Name(consts.EDITOR_CONTENT_PANE_NAME).
                          CenterPane().PaneBorder(True))
        self._mgr.Update()
        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)
        #close the notebook document page event
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnNotebookPageClose)

    def PopupTabMenu(self,index,x,y):
        """
        Handles right clicks for the notebook, enabling users to either close
        a tab or select from the available documents if the user clicks on the
        notebook's white space.
        """
        menu = wx.Menu()
        menuBar = self.GetMenuBar()
        if index > -1:
            view = self._notebook.GetPage(index).GetView()
            self._current_document = view.GetDocument()
            if view.GetType() == consts.TEXT_VIEW:
                item = wx.MenuItem(menu,constants.ID_NEW_MODULE,_("New Module"), _("Creates a new python module"), wx.ITEM_NORMAL)
                item.SetBitmap(images.load("new.png"))
                wx.EVT_MENU(self, constants.ID_NEW_MODULE, self.OnNewModule)
                menu.AppendItem(item)
                
                menu_item = menuBar.FindItemById(constants.ID_SAVE)
                accel = menu_item.GetAccel()
                item = wx.MenuItem(menu,constants.ID_SAVE_DOCUMENT,menu_item.GetLabel() + "\t" + accel.ToString(), kind = wx.ITEM_NORMAL)
                ###caller must delete the pointer manually
                del accel
                item.SetBitmap(menu_item.GetBitmap())
                wx.EVT_MENU(self, constants.ID_SAVE_DOCUMENT, self.OnSaveFileDocument)
                menu.AppendItem(item)
                
                menu_item = menuBar.FindItemById(constants.ID_SAVEAS)
                item = wx.MenuItem(menu,constants.ID_SAVE_AS_DOCUMENT,menu_item.GetLabel(), kind = wx.ITEM_NORMAL)
                wx.EVT_MENU(self, constants.ID_SAVE_AS_DOCUMENT, self.OnSaveFileAsDocument)
                menu.AppendItem(item)
            
            menu_item = menuBar.FindItemById(constants.ID_CLOSE)
            accel = menu_item.GetAccel()
            label = menu_item.GetLabel()
            if accel is not None:
                label += "\t" + accel.ToString()
                ###caller must delete the pointer manually
                del accel
            #we should use a new close id,not use id wx.ID_CLOSE
            item = wx.MenuItem(menu,constants.ID_CLOSE_DOCUMENT, label , kind = wx.ITEM_NORMAL)
            wx.EVT_MENU(self, constants.ID_CLOSE_DOCUMENT, self.OnCloseDoc)
            menu.AppendItem(item)
            
            menu_item = menuBar.FindItemById(constants.ID_CLOSE_ALL)
            item = wx.MenuItem(menu,constants.ID_CLOSE_ALL,menu_item.GetLabel(), kind = wx.ITEM_NORMAL)
            wx.EVT_MENU(self, constants.ID_CLOSE_ALL, self.OnCloseAllDocs)
            menu.AppendItem(item)

            if self._notebook.GetPageCount() > 1:
                item_name = _("Close All but \"%s\"") % self._current_document.GetPrintableName()
                self.AppendMenuItem(constants.ID_CLOSE_ALL_WITHOUT,menu,item_name,self.OnCloseAllWithoutDoc,True)
                tabsMenu = wx.Menu()
                menu.AppendMenu(wx.NewId(), _("Select Tab"), tabsMenu)
            if view.GetType() == consts.TEXT_VIEW or view.GetType() == consts.IMAGE_VIEW:
                self.AppendMenuItem(constants.ID_OPEN_DOCUMENT_DIRECTORY,menu,_("Open Path in Explorer"),self.OnOpenPathInExplorer)
                self.AppendMenuItem(constants.ID_OPEN_TERMINAL_DIRECTORY,menu,_("Open Path in Terminator"),self.OnOpenPathInTerminator)
            self.AppendMenuItem(constants.ID_COPY_DOCUMENT_PATH,menu,_("Copy Path"),self.OnCopyFilePath)
            self.AppendMenuItem(constants.ID_COPY_DOCUMENT_NAME,menu,_("Copy Name"),self.OnCopyFileName)
            if view.GetType() == consts.TEXT_VIEW and view.GetLangId() == lang.ID_LANG_PYTHON:
                self.AppendMenuItem(constants.ID_COPY_MODULE_NAME,menu,_("Copy Module Name"),self.OnCopyModuleName)
                

            if not self.IsFullScreen():
                menu.AppendSeparator()
                self.AppendMenuItem(constants.ID_MAXIMIZE_EDITOR_WINDOW,menu,_("Maximize Editor Window"),self.MaximizeEditorWindow,bmp=images.load("maximize_editor.png"))
                self.AppendMenuItem(constants.ID_RESTORE_EDITOR_WINDOW,menu,_("Restore Editor Window"),self.RestoreEditorWindow,bmp=images.load("restore_editor.png"))
            
        else:
            y = y - 25  # wxBug: It is offsetting click events in the blank notebook area
            tabsMenu = menu

        if self._notebook.GetPageCount() > 1:
            selectIDs = {}
            for i in range(0, self._notebook.GetPageCount()):
                id = wx.NewId()
                selectIDs[id] = i
                filename = self._notebook.GetPageText(i)
                template = wx.GetApp().GetDocumentManager().FindTemplateForPath(filename)
                item = wx.MenuItem(tabsMenu,id,filename, kind = wx.ITEM_NORMAL)
                item.SetBitmap(wx.BitmapFromIcon(template.GetIcon()))
                tabsMenu.AppendItem(item)
                def OnRightMenuSelect(event):
                    self._notebook.SetSelection(selectIDs[event.GetId()])
                wx.EVT_MENU(self, id, OnRightMenuSelect)

        self._notebook.PopupMenu(menu, wx.Point(x, y))
        menu.Destroy()

    def AddNotebookPage(self, panel, title,filename):
        """
        Adds a document page to the notebook.
        """
        #set the tooltip of documnent tabpage
        self._notebook.AddPage(panel, title,tooltip=filename)
        index = self._notebook.GetPageCount() - 1
        self._notebook.SetSelection(index)

        found = False  # Now set the icon
        template = panel.GetDocument().GetDocumentTemplate()
        if template:
            for t, iconIndex in self._iconIndexLookup:
                if t is template:
                    self._notebook.SetPageImage(index, iconIndex)
                    found = True
                    break
        if not found:
            self._notebook.SetPageImage(index, self._blankIconIndex)

        # wxBug: the wxListbook used on Mac needs its tabs list resized
        # whenever a new tab is added, but the only way to do this is
        # to resize the entire control
        if wx.Platform == "__WXMAC__":
            content_size = self._notebook.GetSize()
            self._notebook.SetSize((content_size.x+2, -1))
            self._notebook.SetSize((content_size.x, -1))

        self._notebook.Layout()

        windowMenuService = wx.GetApp().GetService(wx.lib.pydocview.WindowMenuService)
        if windowMenuService:
            windowMenuService.BuildWindowMenu(wx.GetApp().GetTopWindow())  # build file menu list when we open a file

    def SetNotebookPageTitle(self, panel, title):
        wx.lib.pydocview.DocTabbedParentFrame.SetNotebookPageTitle(self,panel,title)
        index = self.GetNotebookPageIndex(panel)
        
        if index > -1:
            #set the new document tooltip as document title
            if panel.GetDocument().GetFilename().find(os.sep) == -1:
                self._notebook.SetPageTooltip(index,title)
            #save as document change the tooltip
            elif self._notebook.GetPageTooltip(index) != panel.GetDocument().GetFilename():
                self._notebook.SetPageTooltip(index,panel.GetDocument().GetFilename())

    def OnNotebookPageClose(self,event):
        ctrl = event.GetEventObject()
        doc = ctrl.GetPage(event.GetSelection()).GetDocument()
        doc.DeleteAllViews()
        event.Veto()

    def OnMRUFile(self, event):
        """
        Opens the appropriate file when it is selected from the file history
        menu.
        """
        n = event.GetId() - consts.ID_MRU_FILE1
        filename = self._docManager.GetHistoryFile(n)
        if filename and os.path.exists(filename):
            self._docManager.CreateDocument(filename, wx.lib.docview.DOC_SILENT)
        else:
            self._docManager.RemoveFileFromHistory(n)
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            if filename:
                wx.MessageBox(_("The file '%s' doesn't exist and couldn't be opened!") % filename,
                              msgTitle,
                              wx.OK | wx.ICON_ERROR,
                              self)

    def OnCloseWindow(self, event):
        for service in wx.GetApp().GetServices():
            if not service.OnCloseFrame(event):
                return
        if self._docManager.Clear(not event.CanVeto()):
            self.Destroy()
        else:
            event.Veto()
        if utils.ProfileGetInt("LoadLastWindowLayout",True):
            utils.ProfileSet("LastPerspective",self._mgr.SavePerspective())
        NavigationService.NavigationService.DocMgr.WriteBook()

    def _LayoutFrame(self):
        """
        Lays out the frame.
        """
        self.Layout()
        self._mgr.Update()

    def OnPaneClose(self,event):
        pane = event.pane
        if isinstance(event.pane.window,aui.auibook.AuiNotebook):
            nb = event.pane.window
            window = nb.GetPage(nb.GetSelection())
            if hasattr(window, consts.DEBUGGER_PAGE_COMMON_METHOD):
                if not window.StopAndRemoveUI(None):
                    event.Veto()
                    return
            pane = self._mgr.GetPane(window)
            self._mgr.ClosePane(pane)
            self._mgr.Update()
            event.Veto()
        else:
            window = pane.window
            if hasattr(window, consts.DEBUGGER_PAGE_COMMON_METHOD):
                if not window.StopAndRemoveUI(None):
                    event.Veto()
                    
    def LoadDefaultPerspective(self):
        default_perspective = utils.ProfileGet('DefaultPerspective','')
        if default_perspective:
            self._mgr.LoadPerspective(default_perspective)
        else:
            wx.MessageBox("Could not load default perspective")
                    
class IDEMDIParentFrame(wx.lib.pydocview.DocMDIParentFrame,DocFrameBase):
    
    # wxBug: Need this for linux. The status bar created in pydocview is
    # replaced in IDE.py with the status bar for the code editor. On windows
    # this works just fine, but on linux the pydocview status bar shows up near
    # the top of the screen instead of disappearing. 

    def __init__(self, docManager, parent, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, name="DocMDIFrame", embeddedWindows=0, minSize=20):
        wx.lib.pydocview.DocMDIParentFrame.__init__(self,docManager,parent,id,title,pos,size,style,name,embeddedWindows,minSize)
        self.RegisterMsg()

    def CreateDefaultStatusBar(self):
       pass
       
    def OnCloseWindow(self, event):
        NavigationService.NavigationService.DocMgr.WriteBook()
        wx.lib.pydocview.DocMDIParentFrame.OnCloseWindow(self,event)

    def _InitFrame(self, embeddedWindows, minSize):
        self._mgr = aui.IDEAuiManager(agwFlags=aui.AUI_MGR_DEFAULT |
                                                 aui.AUI_MGR_TRANSPARENT_DRAG |
                                                 aui.AUI_MGR_TRANSPARENT_HINT |
                                                 aui.AUI_MGR_ALLOW_ACTIVE_PANE)
        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow(self)
        ###wx.lib.pydocview.DocMDIParentFrame._InitFrame(self, embeddedWindows, minSize)
        DocFrameBase._InitFrame(self, embeddedWindows, minSize)
        
    def GetToolBar(self):
        return self._toolBar

    def OnViewToolBar(self, event):
        """
        Toggles whether the ToolBar is visible.
        """
        if sysutilslib.isWindows():
            self._mgr.GetPane(consts.TOOLBAR_PANE_NAME).Show(not self._toolBar.IsShown())
            self._LayoutFrame()
        else:
            wx.lib.pydocview.DocFrameMixIn.OnViewToolBar(self,event)
            
    def _LayoutFrame(self):
        """
        Lays out the frame.
        """
        wx.LayoutAlgorithm().LayoutMDIFrame(self)
        self.GetClientWindow().Refresh()
        self._mgr.Update()

class IDEDocTabbedChildFrame(wx.lib.pydocview.DocTabbedChildFrame):
    

    def __init__(self, doc, view, frame, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, name="frame"):
        """
        Constructor.  Note that the event table must be rebuilt for the
        frame since the EvtHandler is not virtual.
        """
        wx.Panel.__init__(self, frame.GetNotebook(), id)
        self._childDocument = doc
        self._childView = view
        frame.AddNotebookPage(self, doc.GetPrintableName(),doc.GetFilename())
        if view:
            view.SetFrame(self)
    
    def ProcessEvent(self,event):
        """
        Processes an event, searching event tables and calling zero or more
        suitable event handler function(s).  Note that the ProcessEvent
        method is called from the wxPython docview framework directly since
        wxPython does not have a virtual ProcessEvent function.
        """
        if not self._childView or not self._childView.ProcessEvent(event):
            if not isinstance(event, wx.CommandEvent) or not self.GetParent() or not self.GetParent().ProcessEvent(event):
                return False
            else:
                return True
        else:
            return True