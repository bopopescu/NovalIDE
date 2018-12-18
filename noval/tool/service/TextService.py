import wx
import wx.lib.pydocview
import Service
import noval.tool.syntax.lang as lang
import datetime
import getpass
import os
import noval.util.strutils as strutils
import noval.util.sysutils as sysutilslib
import noval.tool.consts as consts
from noval.tool.syntax import syntax
import noval.util.constants as constants
_ = constants._

#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------
CHOOSE_FONT_ID = wx.NewId()
WORD_WRAP_ID = wx.NewId()
TEXT_STATUS_BAR_ID = wx.NewId()

SPACE = 10
HALF_SPACE = 5
class EncodingDeclareDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=(-1,150))
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.name_ctrl = wx.TextCtrl(self, -1, "# -*- coding: utf-8 -*-",size=(100,-1))
        self.name_ctrl.Enable(False)
        contentSizer.Add(self.name_ctrl, 0, wx.ALL|wx.EXPAND , SPACE)
        self.check_box = wx.CheckBox(self, -1,_("Edit"))
        self.Bind(wx.EVT_CHECKBOX,self.onChecked) 
        contentSizer.Add(self.check_box, 0, wx.BOTTOM|wx.LEFT, SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&Insert"))
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,SPACE)
        self.SetSizer(contentSizer)

    def onChecked(self,event):
        self.name_ctrl.Enable(event.GetEventObject().GetValue())

class TextStatusBar(wx.StatusBar):

    TEXT_MODE_PANEL = 1
    DOCUMENT_ENCODING_PANEL = 2
    LINE_NUMBER_PANEL = 3
    COLUMN_NUMBER_PANEL = 4

    # wxBug: Would be nice to show num key status in statusbar, but can't figure out how to detect if it is enabled or disabled
    def __init__(self, parent, id, style = wx.ST_SIZEGRIP, name = "statusBar"):
        wx.StatusBar.__init__(self, parent, id, style, name)
        self.SetFieldsCount(5)
        self.SetStatusWidths([-1, 50, 80,50, 55])
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnStatusBarLeftDclick) 
        
    def SetDocumentEncoding(self,encoding):
        self.SetStatusText(encoding.upper(), TextStatusBar.DOCUMENT_ENCODING_PANEL)

    def SetInsertMode(self, insert = True):
        if insert:
            newText = _("Ins")
        else:
            newText = _("Over")
        if self.GetStatusText(TextStatusBar.TEXT_MODE_PANEL) != newText:     # wxBug: Need to check if the text has changed, otherwise it flickers under win32
            self.SetStatusText(newText, TextStatusBar.TEXT_MODE_PANEL)

    def SetLineNumber(self, lineNumber):
        newText = _("Ln %i") % lineNumber
        if self.GetStatusText(TextStatusBar.LINE_NUMBER_PANEL) != newText:
            self.SetStatusText(newText, TextStatusBar.LINE_NUMBER_PANEL)

    def SetColumnNumber(self, colNumber):
        newText = _("Col %i") % colNumber
        if self.GetStatusText(TextStatusBar.COLUMN_NUMBER_PANEL) != newText:
            self.SetStatusText(newText, TextStatusBar.COLUMN_NUMBER_PANEL)
            
    def OnStatusBarLeftDclick(self,event):
        panel = self.GetPaneAtPosition(event.GetPosition())
        if panel < 0:
            return
        view = wx.GetApp().GetDocumentManager().GetCurrentView()
        if not view or not hasattr(view,"OnGotoLine"):
            return

        if panel == TextStatusBar.TEXT_MODE_PANEL:
            if view.GetCtrl().GetOvertype():
                self.SetInsertMode(True)
                view.GetCtrl().SetOvertype(False)
            else:
                self.SetInsertMode(False)
                view.GetCtrl().SetOvertype(True)
        elif panel == TextStatusBar.LINE_NUMBER_PANEL or \
             panel == TextStatusBar.COLUMN_NUMBER_PANEL:
            view.OnGotoLine(None)
 
    def GetPaneAtPosition(self,point):
        for i in range(self.GetFieldsCount()):
            rect = self.GetFieldRect(i)
            if rect.Contains(point):
                return i
        return -1
        
    def Reset(self):
        self.SetStatusText("", 0)
        self.SetStatusText("", TextStatusBar.TEXT_MODE_PANEL)
        self.SetStatusText("", TextStatusBar.DOCUMENT_ENCODING_PANEL)
        self.SetStatusText("", TextStatusBar.LINE_NUMBER_PANEL)
        self.SetStatusText("", TextStatusBar.COLUMN_NUMBER_PANEL)
        

class TextService(Service.BaseService):

    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        if document and document.GetDocumentTemplate().GetDocumentType() != TextDocument:
            return
        if not document and wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return

        statusBar = TextStatusBar(frame, TEXT_STATUS_BAR_ID)
        frame.SetStatusBar(statusBar)
        wx.EVT_UPDATE_UI(frame, TEXT_STATUS_BAR_ID, frame.ProcessUpdateUIEvent)

        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))

        viewMenu.AppendSeparator()
        textMenu = wx.Menu()
        textMenu.AppendCheckItem(constants.ID_VIEW_WHITESPACE, _("&View Whitespace"), _("Shows or hides whitespace"))
        wx.EVT_MENU(frame, constants.ID_VIEW_WHITESPACE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_VIEW_WHITESPACE, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(constants.ID_VIEW_EOL, _("&View End of Line Markers"), _("Shows or hides indicators at the end of each line"))
        wx.EVT_MENU(frame, constants.ID_VIEW_EOL, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_VIEW_EOL, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(constants.ID_VIEW_INDENTATION_GUIDES, _("&View Indentation Guides"), _("Shows or hides indentations"))
        wx.EVT_MENU(frame, constants.ID_VIEW_INDENTATION_GUIDES, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_VIEW_INDENTATION_GUIDES, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(constants.ID_VIEW_RIGHT_EDGE, _("&View Right Edge"), _("Shows or hides the right edge marker"))
        wx.EVT_MENU(frame, constants.ID_VIEW_RIGHT_EDGE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_VIEW_RIGHT_EDGE, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(constants.ID_VIEW_LINE_NUMBERS, _("&View Line Numbers"), _("Shows or hides the line numbers"))
        wx.EVT_MENU(frame, constants.ID_VIEW_LINE_NUMBERS, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_VIEW_LINE_NUMBERS, frame.ProcessUpdateUIEvent)
        
        viewMenu.AppendMenu(constants.ID_TEXT, _("&Text"), textMenu)
        wx.EVT_UPDATE_UI(frame, constants.ID_TEXT, frame.ProcessUpdateUIEvent)
        
        isWindows = (wx.Platform == '__WXMSW__')

        zoomMenu = wx.Menu()
        zoomMenu.Append(constants.ID_ZOOM_NORMAL, _("Normal Size"), _("Sets the document to its normal size"))
        wx.EVT_MENU(frame, constants.ID_ZOOM_NORMAL, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_ZOOM_NORMAL, frame.ProcessUpdateUIEvent)
        if isWindows:
            item = wx.MenuItem(zoomMenu,constants.ID_ZOOM_IN, _("Zoom In\tCtrl+Page Up"), _("Zooms the document to a larger size"))
        else:
            item = wx.MenuItem(zoomMenu,constants.ID_ZOOM_IN, _("Zoom In"), _("Zooms the document to a larger size"))
        item.SetBitmap(getZoomInBitmap())
        zoomMenu.AppendItem(item)
        wx.EVT_MENU(frame, constants.ID_ZOOM_IN, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_ZOOM_IN, frame.ProcessUpdateUIEvent)
        if isWindows:
            item = wx.MenuItem(zoomMenu,constants.ID_ZOOM_OUT, _("Zoom Out\tCtrl+Page Down"), _("Zooms the document to a smaller size"))
        else:
            item = wx.MenuItem(zoomMenu,constants.ID_ZOOM_OUT, _("Zoom Out"), _("Zooms the document to a smaller size"))
        item.SetBitmap(getZoomOutBitmap())
        zoomMenu.AppendItem(item)
        wx.EVT_MENU(frame, constants.ID_ZOOM_OUT, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_ZOOM_OUT, frame.ProcessUpdateUIEvent)
        
        viewMenu.AppendMenu(constants.ID_ZOOM, _("&Zoom"), zoomMenu)
        wx.EVT_UPDATE_UI(frame, constants.ID_ZOOM, frame.ProcessUpdateUIEvent)

        formatMenuIndex = menuBar.FindMenu(_("&Format"))
        if formatMenuIndex > -1:
            formatMenu = menuBar.GetMenu(formatMenuIndex)
        else:
            formatMenu = wx.Menu()
        if not menuBar.FindItemById(CHOOSE_FONT_ID):
            formatMenu.Append(CHOOSE_FONT_ID, _("&Font..."), _("Sets the font to use"))
            wx.EVT_MENU(frame, CHOOSE_FONT_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, CHOOSE_FONT_ID, frame.ProcessUpdateUIEvent)
        if not menuBar.FindItemById(WORD_WRAP_ID):
            formatMenu.AppendCheckItem(WORD_WRAP_ID, _("Word Wrap"), _("Wraps text horizontally when checked"))
            wx.EVT_MENU(frame, WORD_WRAP_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, WORD_WRAP_ID, frame.ProcessUpdateUIEvent)
        if formatMenuIndex == -1:
            viewMenuIndex = menuBar.FindMenu(_("&View"))
            menuBar.Insert(viewMenuIndex + 1, formatMenu, _("&Format"))

        editMenu = menuBar.GetMenu(menuBar.FindMenu(_("&Edit")))

        insertMenu = wx.Menu()
        insertMenu.Append(constants.ID_INSERT_DATETIME, _("Insert Datetime"), _("Insert Datetime to Current Document"))
        wx.EVT_MENU(frame, constants.ID_INSERT_DATETIME, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_INSERT_DATETIME, frame.ProcessUpdateUIEvent)
        insertMenu.Append(constants.ID_INSERT_COMMENT_TEMPLATE, _("Insert Comment Template"), _("Insert Comment Template to Current Document"))
        wx.EVT_MENU(frame, constants.ID_INSERT_COMMENT_TEMPLATE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_INSERT_COMMENT_TEMPLATE, frame.ProcessUpdateUIEvent)

        insertMenu.Append(constants.ID_INSERT_FILE_CONTENT, _("Insert File Content"), _("Insert File Content to Current Document"))
        wx.EVT_MENU(frame, constants.ID_INSERT_FILE_CONTENT, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_INSERT_FILE_CONTENT, frame.ProcessUpdateUIEvent)

        insertMenu.Append(constants.ID_INSERT_DECLARE_ENCODING, _("Insert Encoding Declare"), _("Insert Encoding Declare to Current Document"))
        wx.EVT_MENU(frame, constants.ID_INSERT_DECLARE_ENCODING, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_INSERT_DECLARE_ENCODING, frame.ProcessUpdateUIEvent)
        editMenu.AppendMenu(constants.ID_INSERT_TEXT, _("&Insert"), insertMenu)
        wx.EVT_UPDATE_UI(frame, constants.ID_INSERT_TEXT, frame.ProcessUpdateUIEvent)

        advanceMenu = wx.Menu()
        item = wx.MenuItem(advanceMenu,constants.ID_UPPERCASE, _("Conert To UPPERCASE\tCtrl+Shift+U"), _("Convert Upper Word to Lower Word"))
        uppercase_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "uppercase.png")
        item.SetBitmap(wx.BitmapFromImage(wx.Image(uppercase_image_path,wx.BITMAP_TYPE_ANY)))
        advanceMenu.AppendItem(item)
            
        wx.EVT_MENU(frame, constants.ID_UPPERCASE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_UPPERCASE, frame.ProcessUpdateUIEvent)
        item = wx.MenuItem(advanceMenu,constants.ID_LOWERCASE, _("Conert To lowercase\tCtrl+U"), _("Convert Lower Word to Upper Word"))
        lowercase_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "lowercase.png")
        item.SetBitmap(wx.BitmapFromImage(wx.Image(lowercase_image_path,wx.BITMAP_TYPE_ANY)))
        advanceMenu.AppendItem(item)
        
        wx.EVT_MENU(frame, constants.ID_LOWERCASE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_LOWERCASE, frame.ProcessUpdateUIEvent)

        advanceMenu.Append(constants.ID_TAB_SPACE, _("Tabs To Spaces"), _("Convert tabs to spaces in selected/all text"))
        wx.EVT_MENU(frame, constants.ID_TAB_SPACE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_TAB_SPACE, frame.ProcessUpdateUIEvent)
        advanceMenu.Append(constants.ID_SPACE_TAB, _("Spaces To Tabs"), _("Convert spaces to tabs in selected/all text"))
        wx.EVT_MENU(frame, constants.ID_SPACE_TAB, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_SPACE_TAB, frame.ProcessUpdateUIEvent)

        editMenu.AppendMenu(constants.ID_EDIT_ADVANCE, _("&Advance"), advanceMenu)
        wx.EVT_UPDATE_UI(frame, constants.ID_EDIT_ADVANCE, frame.ProcessUpdateUIEvent)

        # wxBug: wxToolBar::GetToolPos doesn't exist, need it to find cut tool and then insert find in front of it.
        toolBar.AddSeparator()
        toolBar.AddTool(constants.ID_ZOOM_IN, getZoomInBitmap(), shortHelpString = _("Zoom In"), longHelpString = _("Zooms the document to a larger size"))
        toolBar.AddTool(constants.ID_ZOOM_OUT, getZoomOutBitmap(), shortHelpString = _("Zoom Out"), longHelpString = _("Zooms the document to a smaller size"))
        toolBar.Realize()

    def ProcessEvent(self, event):
        id = event.GetId()
        text_view = self.GetActiveView()
        if id == constants.ID_UPPERCASE:
            text_view.GetCtrl().UpperCase()
            return True
        elif id == constants.ID_LOWERCASE:
            text_view.GetCtrl().LowerCase()
            return True
        elif id == constants.ID_INSERT_DATETIME:
            text_view.AddText(str(datetime.datetime.now().date()))
            return True
        elif id == constants.ID_INSERT_COMMENT_TEMPLATE:
            file_name = os.path.basename(text_view.GetDocument().GetFilename())
            now_time = datetime.datetime.now()
            langid = text_view.GetLangId()
            lexer = syntax.LexerManager().GetLexer(langid)
            comment_template = lexer.GetCommentTemplate()
            if comment_template is not None:
                comment_template_content = comment_template.format(File=file_name,Author=getpass.getuser(),Date=now_time.date(),Year=now_time.date().year)
                text_view.GetCtrl().GotoPos(0)
                text_view.AddText(comment_template_content)
            return True
        elif id == constants.ID_INSERT_FILE_CONTENT:
            dlg = wx.FileDialog(wx.GetApp().GetTopWindow(),_("Select File Path"),
                                wildcard="All|*.*",style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                with open(path) as f:
                    text_view.AddText(f.read())
            return True
        elif id == constants.ID_INSERT_DECLARE_ENCODING:
            if text_view.GetLangId() == lang.ID_LANG_PYTHON:
                self.InsertEncodingDeclare(text_view)
            return True
        elif id == constants.ID_TAB_SPACE or id == constants.ID_SPACE_TAB:
            self.ConvertWhitespace(text_view,id)
        else:
            return False

    def InsertEncodingDeclare(self,text_view = None):
        if text_view is None:
            text_view = self.GetActiveView()
        
        lines = text_view.GetTopLines(consts.ENCODING_DECLARE_LINE_NUM)
        coding_name,line_num = strutils.get_python_coding_declare(lines)
        if  coding_name is not None:
            ret = wx.MessageBox(_("The Python Document have already declare coding,Do you want to overwrite it?"),_("Declare Encoding"),wx.YES_NO|wx.ICON_QUESTION,\
                text_view.GetFrame())
            if ret == wx.YES:
                text_view.GetCtrl().SetSelection(text_view.GetCtrl().PositionFromLine(line_num),text_view.GetCtrl().PositionFromLine(line_num+1))
                text_view.GetCtrl().DeleteBack()
            else:
                return True
                
        dlg = EncodingDeclareDialog(wx.GetApp().GetTopWindow(),-1,_("Declare Encoding"))
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            text_view.GetCtrl().GotoPos(0)
            text_view.AddText(dlg.name_ctrl.GetValue() + "\n")
            return True
        return False

    def ProcessUpdateUIEvent(self, event):
        text_view = self.GetActiveView()
      #  if text_view is None:
       #     event.Enable(False)
        #    return True
        id = event.GetId()
        if (id == constants.ID_TEXT
        or id == constants.ID_VIEW_WHITESPACE
        or id == constants.ID_VIEW_EOL
        or id == constants.ID_VIEW_INDENTATION_GUIDES
        or id == constants.ID_VIEW_RIGHT_EDGE
        or id == constants.ID_VIEW_LINE_NUMBERS
        or id == constants.ID_ZOOM
        or id == constants.ID_ZOOM_NORMAL
        or id == constants.ID_ZOOM_IN
        or id == constants.ID_ZOOM_OUT
        or id == CHOOSE_FONT_ID
        or id == WORD_WRAP_ID
        or id == constants.ID_INSERT_TEXT
        or id == constants.ID_EDIT_ADVANCE):
            event.Enable(False)
            return True
        elif id == constants.ID_UPPERCASE \
                or id == constants.ID_LOWERCASE:
            event.Enable(text_view is not None and text_view.HasSelection())
            return True
        elif id == constants.ID_INSERT_COMMENT_TEMPLATE:
            if text_view is not None:
                langid = text_view.GetLangId()
                lexer = syntax.LexerManager().GetLexer(langid)
                enabled = lexer.IsCommentTemplateEnable()
            else:
                enabled = False
            event.Enable(enabled )
            return True
        elif id == constants.ID_INSERT_DECLARE_ENCODING:
            if text_view is not None:
                langid = text_view.GetLangId()
                enabled = (langid == lang.ID_LANG_PYTHON)
            else:
                enabled = False
            event.Enable(enabled )
        else:
            return False


    def ConvertWhitespace(self, text_view,mode_id):
        """Convert whitespace from using tabs to spaces or visa versa
        @param mode_id: id of conversion mode

        """
        if mode_id not in (constants.ID_TAB_SPACE, constants.ID_SPACE_TAB):
            return

        text_ctrl = text_view.GetCtrl()
        tabw = text_ctrl.GetIndent()
        pos = text_ctrl.GetCurrentPos()
        sel = text_ctrl.GetSelectedText()
        if mode_id == constants.ID_TAB_SPACE:
            cmd = (u"\t", u" " * tabw)
            tabs = False
        else:
            cmd = (" " * tabw, u"\t")
            tabs = True

        if sel != wx.EmptyString:
            text_ctrl.ReplaceSelection(sel.replace(cmd[0], cmd[1]))
        else:
            text_ctrl.BeginUndoAction()
            part1 = text_ctrl.GetTextRange(0, pos).replace(cmd[0], cmd[1])
            tmptxt = text_ctrl.GetTextRange(pos, text_ctrl.GetLength()).replace(cmd[0], \
                                                                      cmd[1])
            text_ctrl.SetText(part1 + tmptxt)
            text_ctrl.GotoPos(len(part1))
            text_ctrl.SetUseTabs(tabs)
            text_ctrl.EndUndoAction()

from wx import ImageFromStream, BitmapFromImage
import cStringIO
#----------------------------------------------------------------------------
# Menu Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
#----------------------------------------------------------------------
def getZoomInBitmap():
    zoomin_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source","toolbar","zoomin.png")
    zoomin_image = wx.Image(zoomin_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(zoomin_image)

#----------------------------------------------------------------------

def getZoomOutBitmap():
    zoomout_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source","toolbar","zoomout.png")
    zoomout_image = wx.Image(zoomout_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(zoomout_image)

    return ImageFromStream(stream)
