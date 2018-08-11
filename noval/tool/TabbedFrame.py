import os
import wx.lib.pydocview
import wx
import noval.util.sysutils as sysutilslib
import noval.util.fileutils as fileutils
import noval.util.strutils as strutils
import noval.tool.syntax.lang as lang
import noval.tool.syntax.syntax as syntax
import consts
import noval.tool.NavigationService
import noval.util.appdirs as appdirs
from wx.lib.pubsub import pub as Publisher

_ = wx.GetTranslation


class MessageNotification():

    def RegisterMsg(self):
        Publisher.subscribe(self.OnUpdatePosCache,noval.tool.NavigationService.NOVAL_MSG_UI_STC_POS_JUMPED)

    def OnUpdatePosCache(self, msg):
        """Update the position cache for buffer position changes
        @param msg: message data

        """
        data = msg
        if data.has_key('prepos'):
            noval.tool.NavigationService.NavigationService.DocMgr.AddNaviPosition(data['fname'], data['prepos'])
        noval.tool.NavigationService.NavigationService.DocMgr.AddNaviPosition(data['fname'], data['pos'])

class IDEDocTabbedParentFrame(wx.lib.pydocview.DocTabbedParentFrame,MessageNotification):
    
    # wxBug: Need this for linux. The status bar created in pydocview is
    # replaced in IDE.py with the status bar for the code editor. On windows
    # this works just fine, but on linux the pydocview status bar shows up near
    # the top of the screen instead of disappearing. 

    def __init__(self, docManager, frame, id, title, pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_FRAME_STYLE, name = "DocTabbedParentFrame", embeddedWindows = 0, minSize=20):
        wx.lib.pydocview.DocTabbedParentFrame.__init__(self,docManager,frame,id,title,pos,size,style,name,embeddedWindows,minSize)
        wx.EVT_MENU_RANGE(self, consts.ID_MRU_FILE1, consts.ID_MRU_FILE20, self.OnMRUFile)
        self.RegisterMsg()
        self._current_document = None
    
    def CreateDefaultStatusBar(self):
       pass
       
    def CreateDefaultToolBar(self):
        """
        Creates the default ToolBar.
        """
        app_image_path = appdirs.GetAppImageDirLocation()
        self._toolBar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        
        toolbar_image_path = os.path.join(app_image_path, "toolbar")
        
        tb_new_image = wx.Image(os.path.join(toolbar_image_path,"new.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_NEW, wx.BitmapFromImage(tb_new_image), _("New"), _("Creates a new document"))
        
        tb_open_image = wx.Image(os.path.join(toolbar_image_path,"open.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_OPEN, wx.BitmapFromImage(tb_open_image), _("Open"), _("Opens an existing document"))
        
        tb_save_image = wx.Image(os.path.join(toolbar_image_path,"save.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_SAVE, wx.BitmapFromImage(tb_save_image), _("Save"), _("Saves the active document"))
        
        tb_saveall_image = wx.Image(os.path.join(toolbar_image_path,"saveall.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.lib.pydocview.SAVEALL_ID, wx.BitmapFromImage(tb_saveall_image), _("Save All"), _("Saves all the active documents"))
        self._toolBar.AddSeparator()
        
        tb_print_image = wx.Image(os.path.join(toolbar_image_path,"print.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_PRINT, wx.BitmapFromImage(tb_print_image), _("Print"), _("Displays full pages"))
        
        tb_preview_image = wx.Image(os.path.join(toolbar_image_path,"preview.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_PREVIEW, wx.BitmapFromImage(tb_preview_image), _("Print Preview"), _("Prints the active document"))
        self._toolBar.AddSeparator()
        
        tb_cut_image = wx.Image(os.path.join(toolbar_image_path,"cut.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_CUT, wx.BitmapFromImage(tb_cut_image), _("Cut"), _("Cuts the selection and puts it on the Clipboard"))
            
        tb_copy_image = wx.Image(os.path.join(toolbar_image_path,"copy.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_COPY, wx.BitmapFromImage(tb_copy_image), _("Copy"), _("Copies the selection and puts it on the Clipboard"))
            
        tb_paste_image = wx.Image(os.path.join(toolbar_image_path,"paste.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_PASTE, wx.BitmapFromImage(tb_paste_image), _("Paste"), _("Inserts Clipboard contents"))
        
        tb_undo_image = wx.Image(os.path.join(toolbar_image_path,"undo.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_UNDO, wx.BitmapFromImage(tb_undo_image), _("Undo"), _("Reverses the last action"))
        
        tb_redo_image = wx.Image(os.path.join(toolbar_image_path,"redo.png"),wx.BITMAP_TYPE_ANY)
        self._toolBar.AddSimpleTool(wx.ID_REDO, wx.BitmapFromImage(tb_redo_image), _("Redo"), _("Reverses the last undo"))
        self._toolBar.Realize()
        self._toolBar.Show(wx.ConfigBase_Get().ReadInt("ViewToolBar", True))

        return self._toolBar
        

    def CreateDefaultMenuBar(self, sdi=False):
        """
        Creates the default MenuBar.  Contains File, Edit, View, Tools, and Help menus.
        """
        if sysutilslib.isWindows():
            menuBar = wx.MenuBar()
            
            app_image_path = appdirs.GetAppImageDirLocation()

            fileMenu = wx.Menu()
            item = wx.MenuItem(fileMenu,wx.ID_NEW,_("&New...\tCtrl+N"), _("Creates a new document"), wx.ITEM_NORMAL)
            item.SetBitmap(self._toolBar.FindById(wx.ID_NEW).GetBitmap())
            fileMenu.AppendItem(item)
            
            item = wx.MenuItem(fileMenu,wx.ID_OPEN, _("&Open...\tCtrl+O"), _("Opens an existing document"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_OPEN).GetBitmap())
            fileMenu.AppendItem(item)
            
            fileMenu.Append(wx.ID_CLOSE, _("&Close\tCtrl+W"), _("Closes the active document"))
            if not sdi:
                fileMenu.Append(wx.ID_CLOSE_ALL, _("Close A&ll"), _("Closes all open documents"))
            fileMenu.AppendSeparator()
            
            item = wx.MenuItem(fileMenu,wx.ID_SAVE, _("&Save\tCtrl+S"), _("Saves the active document"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_SAVE).GetBitmap())
            fileMenu.AppendItem(item)
            
            fileMenu.Append(wx.ID_SAVEAS, _("Save &As..."), _("Saves the active document with a new name"))
            
            item = wx.MenuItem(fileMenu,wx.lib.pydocview.SAVEALL_ID, _("Save All\tCtrl+Shift+A"), _("Saves the all active documents"))
            item.SetBitmap(self._toolBar.FindById(wx.lib.pydocview.SAVEALL_ID).GetBitmap())
            fileMenu.AppendItem(item)
            
            wx.EVT_MENU(self, wx.lib.pydocview.SAVEALL_ID, self.ProcessEvent)
            wx.EVT_UPDATE_UI(self, wx.lib.pydocview.SAVEALL_ID, self.ProcessUpdateUIEvent)
            fileMenu.AppendSeparator()
            
            item = wx.MenuItem(fileMenu,wx.ID_PRINT, _("&Print\tCtrl+P"), _("Prints the active document"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_PRINT).GetBitmap())
            fileMenu.AppendItem(item)
            
            item = wx.MenuItem(fileMenu,wx.ID_PREVIEW, _("Print Pre&view"), _("Displays full pages"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_PREVIEW).GetBitmap())
            fileMenu.AppendItem(item)
            
            item = wx.MenuItem(fileMenu,wx.ID_PRINT_SETUP, _("Page Set&up"), _("Changes page layout settings"))
            page_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "page.png")
            item.SetBitmap(wx.BitmapFromImage(wx.Image(page_image_path,wx.BITMAP_TYPE_ANY)))
            fileMenu.AppendItem(item)
            
            fileMenu.AppendSeparator()
            if wx.Platform == '__WXMAC__':
                item = wx.MenuItem(fileMenu,wx.ID_EXIT, _("&Quit"), _("Closes this program"))
            else:
                item = wx.MenuItem(fileMenu,wx.ID_EXIT, _("E&xit"), _("Closes this program"))
            exit_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "exit.png")
            item.SetBitmap(wx.BitmapFromImage(wx.Image(exit_image_path,wx.BITMAP_TYPE_ANY)))
            fileMenu.AppendItem(item)
            
            self._docManager.FileHistoryUseMenu(fileMenu)
            self._docManager.FileHistoryAddFilesToMenu()
            menuBar.Append(fileMenu, _("&File"));

            editMenu = wx.Menu()
            item = wx.MenuItem(editMenu,wx.ID_UNDO, _("&Undo\tCtrl+Z"), _("Reverses the last action"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_UNDO).GetBitmap())
            editMenu.AppendItem(item)
            
            item = wx.MenuItem(editMenu,wx.ID_REDO, _("&Redo\tCtrl+Y"), _("Reverses the last undo"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_REDO).GetBitmap())
            editMenu.AppendItem(item)
            editMenu.AppendSeparator()
            #item = wxMenuItem(self.editMenu, wxID_CUT, _("Cu&t\tCtrl+X"), _("Cuts the selection and puts it on the Clipboard"))
            #item.SetBitmap(getCutBitmap())
            #editMenu.AppendItem(item)
            item = wx.MenuItem(editMenu,wx.ID_CUT, _("Cu&t\tCtrl+X"), _("Cuts the selection and puts it on the Clipboard"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_CUT).GetBitmap())
            editMenu.AppendItem(item)
            
            wx.EVT_MENU(self, wx.ID_CUT, self.ProcessEvent)
            wx.EVT_UPDATE_UI(self, wx.ID_CUT, self.ProcessUpdateUIEvent)
            item = wx.MenuItem(editMenu,wx.ID_COPY, _("&Copy\tCtrl+C"), _("Copies the selection and puts it on the Clipboard"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_COPY).GetBitmap())
            editMenu.AppendItem(item)
            
            wx.EVT_MENU(self, wx.ID_COPY, self.ProcessEvent)
            wx.EVT_UPDATE_UI(self, wx.ID_COPY, self.ProcessUpdateUIEvent)
            item = wx.MenuItem(editMenu,wx.ID_PASTE, _("&Paste\tCtrl+V"), _("Inserts Clipboard contents"))
            item.SetBitmap(self._toolBar.FindById(wx.ID_PASTE).GetBitmap())
            editMenu.AppendItem(item)
            
            wx.EVT_MENU(self, wx.ID_PASTE, self.ProcessEvent)
            wx.EVT_UPDATE_UI(self, wx.ID_PASTE, self.ProcessUpdateUIEvent)
            editMenu.Append(wx.ID_CLEAR, _("&Delete"), _("Erases the selection"))
            wx.EVT_MENU(self, wx.ID_CLEAR, self.ProcessEvent)
            wx.EVT_UPDATE_UI(self, wx.ID_CLEAR, self.ProcessUpdateUIEvent)
            editMenu.AppendSeparator()
            editMenu.Append(wx.ID_SELECTALL, _("Select A&ll\tCtrl+A"), _("Selects all available data"))
            wx.EVT_MENU(self, wx.ID_SELECTALL, self.ProcessEvent)
            wx.EVT_UPDATE_UI(self, wx.ID_SELECTALL, self.ProcessUpdateUIEvent)
            menuBar.Append(editMenu, _("&Edit"))
            if sdi:
                if self.GetDocument() and self.GetDocument().GetCommandProcessor():
                    self.GetDocument().GetCommandProcessor().SetEditMenu(editMenu)

            viewMenu = wx.Menu()
            viewMenu.AppendCheckItem(wx.lib.pydocview.VIEW_TOOLBAR_ID, _("&Toolbar"), _("Shows or hides the toolbar"))
            wx.EVT_MENU(self, wx.lib.pydocview.VIEW_TOOLBAR_ID, self.OnViewToolBar)
            wx.EVT_UPDATE_UI(self, wx.lib.pydocview.VIEW_TOOLBAR_ID, self.OnUpdateViewToolBar)
            viewMenu.AppendCheckItem(wx.lib.pydocview.VIEW_STATUSBAR_ID, _("&Status Bar"), _("Shows or hides the status bar"))
            wx.EVT_MENU(self, wx.lib.pydocview.VIEW_STATUSBAR_ID, self.OnViewStatusBar)
            wx.EVT_UPDATE_UI(self, wx.lib.pydocview.VIEW_STATUSBAR_ID, self.OnUpdateViewStatusBar)
            menuBar.Append(viewMenu, _("&View"))

            helpMenu = wx.Menu()
            item = wx.MenuItem(helpMenu,wx.ID_ABOUT, _(_("About %s") % wx.GetApp().GetAppName()), _("Displays program information, version number, and copyright"))
            item.SetBitmap(wx.BitmapFromImage(wx.Image(os.path.join(app_image_path,"about.png"),wx.BITMAP_TYPE_ANY)))
            helpMenu.AppendItem(item)
            menuBar.Append(helpMenu, _("&Help"))

            wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)
            wx.EVT_UPDATE_UI(self, wx.ID_ABOUT, self.ProcessUpdateUIEvent)  # Using ID_ABOUT to update the window menu, the window menu items are not triggering

            if sdi:  # TODO: Is this really needed?
                wx.EVT_COMMAND_FIND_CLOSE(self, -1, self.ProcessEvent)
                
            return menuBar
        else:
            return wx.lib.pydocview.DocTabbedParentFrame.CreateDefaultMenuBar(self)
 
    def AppendMenuItem(self,menu,name,callback,separator=False):
       id = wx.NewId()
       menu.Append(id,name)
       wx.EVT_MENU(self, id, callback)       
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

    def OnNotebookRightClick(self, event):
        """
        Handles right clicks for the notebook, enabling users to either close
        a tab or select from the available documents if the user clicks on the
        notebook's white space.
        """
        index, type = self._notebook.HitTest(event.GetPosition())
        menu = wx.Menu()
        x, y = event.GetX(), event.GetY()
        menuBar = self.GetMenuBar()
        if index > -1:
            view = self._notebook.GetPage(index).GetView()
            self._current_document = view.GetDocument()
            if view.GetType() == consts.TEXT_VIEW:
                app_image_path = appdirs.GetAppImageDirLocation()
                new_id = wx.NewId()
                item = wx.MenuItem(menu,new_id,_("New Module"), _("Creates a new python module"), wx.ITEM_NORMAL)
                item.SetBitmap(wx.BitmapFromImage(wx.Image(os.path.join(app_image_path,"new.png"),wx.BITMAP_TYPE_ANY)))
                wx.EVT_MENU(self, new_id, self.OnNewModule)
                menu.AppendItem(item)
                
                menu_item = menuBar.FindItemById(wx.ID_SAVE)
                accel = menu_item.GetAccel()
                new_id = wx.NewId()
                item = wx.MenuItem(menu,new_id,menu_item.GetLabel() + "\t" + accel.ToString(), kind = wx.ITEM_NORMAL)
                ###caller must delete the pointer manually
                del accel
                item.SetBitmap(menu_item.GetBitmap())
                wx.EVT_MENU(self, new_id, self.OnSaveFileDocument)
                menu.AppendItem(item)
                
                menu_item = menuBar.FindItemById(wx.ID_SAVEAS)
                new_id = wx.NewId()
                item = wx.MenuItem(menu,new_id,menu_item.GetLabel(), kind = wx.ITEM_NORMAL)
                wx.EVT_MENU(self, new_id, self.OnSaveFileAsDocument)
                menu.AppendItem(item)
            
            menu_item = menuBar.FindItemById(wx.ID_CLOSE)
            accel = menu_item.GetAccel()
            label = menu_item.GetLabel()
            if accel is not None:
                label += "\t" + accel.ToString()
                ###caller must delete the pointer manually
                del accel
            new_id = wx.NewId()
            item = wx.MenuItem(menu,new_id, label , kind = wx.ITEM_NORMAL)
            wx.EVT_MENU(self, new_id, self.OnCloseDoc)
            menu.AppendItem(item)
            
            menu_item = menuBar.FindItemById(wx.ID_CLOSE_ALL)
            item = wx.MenuItem(menu,wx.ID_CLOSE_ALL,menu_item.GetLabel(), kind = wx.ITEM_NORMAL)
            wx.EVT_MENU(self, wx.ID_CLOSE_ALL, self.OnCloseAllDocs)
            menu.AppendItem(item)

            if self._notebook.GetPageCount() > 1:
                item_name = _("Close All but \"%s\"") % self._current_document.GetPrintableName()
                self.AppendMenuItem(menu,item_name,self.OnCloseAllWithoutDoc,True)
                tabsMenu = wx.Menu()
                menu.AppendMenu(wx.NewId(), _("Select Tab"), tabsMenu)
            if view.GetType() == consts.TEXT_VIEW:
                self.AppendMenuItem(menu,_("Open Path in Explorer"),self.OnOpenPathInExplorer)
                self.AppendMenuItem(menu,_("Open Path in Terminator"),self.OnOpenPathInTerminator)
            self.AppendMenuItem(menu,_("Copy Path"),self.OnCopyFilePath)
            self.AppendMenuItem(menu,_("Copy Name"),self.OnCopyFileName)
            if view.GetType() == consts.TEXT_VIEW and view.GetLangId() == lang.ID_LANG_PYTHON:
                self.AppendMenuItem(menu,_("Copy Module Name"),self.OnCopyModuleName)
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

    def OnNotebookMouseOver(self, event):
        index, type = self._notebook.HitTest(event.GetPosition())
        if index > -1:
            doc = self._notebook.GetPage(index).GetView().GetDocument()
            self._notebook.SetToolTip(wx.ToolTip(doc.GetFilename()))
        else:
            self._notebook.SetToolTip(wx.ToolTip(""))
        event.Skip()

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
        wx.lib.pydocview.DocTabbedParentFrame.OnCloseWindow(self,event)
        noval.tool.NavigationService.NavigationService.DocMgr.WriteBook()

class IDEMDIParentFrame(wx.lib.pydocview.DocMDIParentFrame,MessageNotification):
    
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
        noval.tool.NavigationService.NavigationService.DocMgr.WriteBook()
        wx.lib.pydocview.DocMDIParentFrame.OnCloseWindow(self,event)