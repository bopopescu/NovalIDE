#----------------------------------------------------------------------------
# Name:         HtmlEditor.py
# Purpose:      Abstract Code Editor for pydocview tbat uses the Styled Text Control
#
# Author:       Peter Yared
#
# Created:      8/15/04
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------


import wx
import os.path
import string
import STCTextEditor
import CodeEditor
import noval.util.sysutils as sysutilslib
import images
if sysutilslib.isWindows():
    import wx.html2 as webview
else:
    import wx.html as webview
import consts

_ = wx.GetTranslation
        

class HtmlDocument(CodeEditor.CodeDocument):

    pass


class HtmlView(CodeEditor.CodeView):


    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        return HtmlCtrl


    def GetAutoCompleteHint(self):
        pos = self.GetCtrl().GetCurrentPos()
        if pos == 0:
            return None, None
            
        validLetters = string.letters + string.digits + '_!-'
        word = ''
        while (True):
            pos = pos - 1
            if pos < 0:
                break
            char = chr(self.GetCtrl().GetCharAt(pos))
            if char not in validLetters:
                break
            word = char + word
            
        return None, word
        

    def GetAutoCompleteDefaultKeywords(self):
        return HTMLKEYWORDS


##    def _CreateControl(self, parent, id):
##        import wx  # wxBug: When inlining the import of the appropriate html control below, have to specifically import wx for some reason
##        self._notebook = wx.Notebook(parent, wx.NewId(), style = wx.NB_BOTTOM)
##        self._textEditor = HtmlCtrl(self._notebook, id)
##        if wx.Platform =='__WXMSW__':
##            import wxPython.iewin
##            self._browserCtrl = wxPython.iewin.wxIEHtmlWin(self._notebook, -1, style = wx.NO_FULL_REPAINT_ON_RESIZE)
##        else:
##            import wx.html
##            self._browserCtrl = wx.html.HtmlWindow(self._notebook, -1, style = wx.NO_FULL_REPAINT_ON_RESIZE)
##        self._notebook.AddPage(self._textEditor, _("Edit"))
##        self._notebook.AddPage(self._browserCtrl, _("View"))
##        self._insertMode = True
##        wx.EVT_NOTEBOOK_PAGE_CHANGED(self._notebook, self._notebook.GetId(), self.OnNotebookChanging)
##        return self._textEditor
##
##
##    def _CreateSizer(self, frame):
##        sizer = wx.BoxSizer(wx.HORIZONTAL)
##        sizer.Add(self._notebook, 1, wx.EXPAND)
##        frame.SetSizer(sizer)
##
##
##    def OnNotebookChanging(self, event):
##        if event.GetSelection() == 0:  # Going to the edit page
##            pass  # self._textEditor.Refresh()
##        elif event.GetSelection() == 1:  # Going to the browser page
##            text = self._textEditor.GetText()
##            if wx.Platform == '__WXMSW__':
##                path = os.path.join(tempfile.gettempdir(), "temp.html")
##                file = open(path, 'w')
##                file.write(text)
##                file.close()
##                self._browserCtrl.Navigate("file://" + path)
##            else:
##                self._browserCtrl.SetPage(text)
##        event.Skip()


class HtmlService(CodeEditor.CodeService):


    def __init__(self):
        CodeEditor.CodeService.__init__(self)


class HtmlCtrl(CodeEditor.CodeCtrl):

    def __init__(self, parent, id=-1, style=wx.NO_FULL_REPAINT_ON_RESIZE):
        CodeEditor.CodeCtrl.__init__(self, parent, id, style)


    def GetMatchingBraces(self):
        return "<>[]{}()"


    def CanWordWrap(self):
        return True

    def GetFontAndColorFromConfig(self):
        return CodeEditor.CodeCtrl.GetFontAndColorFromConfig(self, configPrefix = "Html")

class WebDocument(wx.lib.docview.Document):
    def OnOpenDocument(self, filename):
        return True

class WebView(wx.lib.docview.View):

    def __init__(self):
        wx.lib.docview.View.__init__(self)
        self._ctrl = None

    def OnCreate(self, doc, flags):
        frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self.panel = wx.Panel(frame, -1)
        self.current = doc.GetFilename()
        
        if sysutilslib.isWindows():
            self.wv = webview.WebView.New(self.panel)
            self.Bind(webview.EVT_WEBVIEW_NAVIGATING, self.OnWebViewNavigating, self.wv)
            self.Bind(webview.EVT_WEBVIEW_LOADED, self.OnWebViewLoaded, self.wv)
        else:
            self.wv = webview.HtmlWindow(self.panel)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.BitmapButton(self.panel,-1,images.load("web/go.png"))
        btn.SetToolTipString(_("Open URL"))
        btn.Bind(wx.EVT_BUTTON, self.OnOpenButton)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)

        btn = wx.BitmapButton(self.panel,-1,images.load("web/go_back.png"))
        btn.SetToolTipString(_("Back"))
        btn.Bind(wx.EVT_BUTTON, self.OnPrevPageButton)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)
        btn.Bind(wx.EVT_UPDATE_UI, self.OnCheckCanGoBack)

        btn = wx.BitmapButton(self.panel,-1,images.load("web/go_forward.png"))
        btn.SetToolTipString(_("Forward"))
        btn.Bind(wx.EVT_BUTTON, self.OnNextPageButton)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)
        btn.Bind(wx.EVT_UPDATE_UI, self.OnCheckCanGoForward)

        btn = wx.BitmapButton(self.panel,-1,images.load("web/stop.png"))
        btn.SetToolTipString(_("Stop"))
        btn.Bind(wx.EVT_BUTTON, self.OnStopButton)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)

        btn = wx.BitmapButton(self.panel,-1,images.load("web/fresh.png"))
        btn.SetToolTipString(_("Refresh"))
        btn.Bind(wx.EVT_BUTTON, self.OnRefreshPageButton)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)

        txt = wx.StaticText(self.panel, -1, _("URL:"))
        btnSizer.Add(txt, 0, wx.CENTER|wx.ALL, 2)

        self.location = wx.ComboBox(
            self.panel, -1, "", style=wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER)
        self.location.AppendItems(['http://wxPython.org',
                                   'http://wxwidgets.org',
                                   'http://google.com'])
        wx.EVT_COMBOBOX(self.location,-1,self.OnLocationSelect)
        self.location.Bind(wx.EVT_TEXT_ENTER, self.OnLocationEnter)
        
        btnSizer.Add(self.location, 1, wx.EXPAND|wx.ALL, 2)
        
        if sysutilslib.isWindows():
            self.wv.LoadURL(self.current)
        else:
            self.wv.LoadPage(self.current)
        
        sizer.Add(btnSizer, 0, wx.EXPAND)
        sizer.Add(self.wv, 1, wx.EXPAND)
        self.panel.SetSizer(sizer)
        
        self._CreateSizer(frame)
        
        self.Activate()
        frame.Show(True)
        frame.Layout()
        return True

    def OnFocus(self, event):
        self.panel.SetFocus()
        event.Skip()

    def OnClose(self, deleteWindow = True):
        statusC = wx.GetApp().CloseChildDocuments(self.GetDocument())
        statusP = wx.lib.docview.View.OnClose(self, deleteWindow = deleteWindow)
        if not (statusC and statusP):
            return False
        self.Activate(False)
        if deleteWindow:
            self.GetFrame().Destroy()
        return True
        
    def _CreateSizer(self, frame):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        frame.SetSizer(sizer)

    def GetType(self):
        return consts.HTML_WEB_VIEW
        
    # WebView events
    def OnWebViewNavigating(self, evt):
        # this event happens prior to trying to get a resource
        if evt.GetURL() == 'http://www.microsoft.com/':
            if wx.MessageBox("Are you sure you want to visit Microsoft?",
                             style=wx.YES_NO|wx.ICON_QUESTION) == wx.NO:
                # This is how you can cancel loading a page.
                evt.Veto()

    def OnWebViewLoaded(self, evt):
        # The full document has loaded
        self.current = evt.GetURL()
        self.location.SetValue(self.current)

    # Control bar events
    def OnLocationSelect(self, evt):
        url = self.location.GetStringSelection()
        if sysutilslib.isWindows():
            self.wv.LoadURL(url)
        else:
            self.wv.LoadPage(url)

    def OnLocationEnter(self, evt):
        url = self.location.GetValue()
        self.location.Append(url)
        if sysutilslib.isWindows():
            self.wv.LoadURL(url)
        else:
            self.wv.LoadPage(url)

    def OnOpenButton(self, event):
        dlg = wx.TextEntryDialog(self.GetFrame(), _("Open URL:"),
                                _("Enter a full URL or local path"),
                                self.current, wx.OK|wx.CANCEL)
        dlg.CentreOnParent()

        if dlg.ShowModal() == wx.ID_OK:
            self.current = dlg.GetValue()
            if sysutilslib.isWindows():
                self.wv.LoadURL(self.current)
            else:
                self.wv.LoadPage(self.current)

        dlg.Destroy()

    def OnPrevPageButton(self, event):
        if sysutilslib.isWindows():
            self.wv.GoBack()
        else:
            self.wv.HistoryBack()

    def OnNextPageButton(self, event):
        if sysutilslib.isWindows():
            self.wv.GoForward()
        else:
            self.wv.HistoryForward()

    def OnCheckCanGoBack(self, event):
        if sysutilslib.isWindows():
            event.Enable(self.wv.CanGoBack())
        else:
            event.Enable(self.wv.HistoryCanBack())
        
    def OnCheckCanGoForward(self, event):
        if sysutilslib.isWindows():
            event.Enable(self.wv.CanGoForward())
        else:
            event.Enable(self.wv.HistoryCanForward())

    def OnStopButton(self, evt):
        if sysutilslib.isWindows():
            self.wv.Stop()

    def OnRefreshPageButton(self, evt):
        if sysutilslib.isWindows():
            self.wv.Reload()


HTMLKEYWORDS = [
        "A", "ABBR", "ACRONYM", "ADDRESS", "APPLET", "AREA", "B", "BASE", "BASEFONT", "BDO", "BIG", "BLOCKQUOTE",
        "BODY", "BR", "BUTTON", "CAPTION", "CENTER", "CITE", "CODE", "COL", "COLGROUP", "DD", "DEL", "DFN", "DIR",
        "DIV", "DL", "DT", "EM", "FIELDSET", "FONT", "FORM", "FRAME", "FRAMESET", "H1", "H2", "H3", "H4", "H5", "H6",
        "HEAD", "HR", "HTML", "I", "IFRAME", "IMG", "INPUT", "INS", "ISINDEX", "KBD", "LABEL", "LEGEND", "LI", "LINK",
        "MAP", "MENU", "META", "NOFRAMES", "NOSCRIPT", "OBJECT", "OL", "OPTGROUP", "OPTION", "P", "PARAM",
        "PRE", "Q", "S", "SAMP", "SCRIPT", "SELECT", "SMALL", "SPAN", "STRIKE", "STRONG", "STYLE", "SUB", "SUP",
        "TABLE", "TBODY", "TD", "TEXTAREA", "TFOOT", "TH", "THEAD", "TITLE", "TR", "TT", "U", "UL", "VAR", "XML",
        "XMLNS", "ACCEPT-CHARSET", "ACCEPT", "ACCESSKEY", "ACTION", "ALIGN", "ALINK", "ALT",
        "ARCHIVE", "AXIS", "BACKGROUND", "BGCOLOR", "BORDER", "CELLPADDING", "CELLSPACING", "CHAR",
        "CHAROFF", "CHARSET", "CHECKED", "CLASS", "CLASSID", "CLEAR", "CODEBASE", "CODETYPE",
        "COLOR", "COLS", "COLSPAN", "COMPACT", "CONTENT", "COORDS", "DATA", "DATAFLD", "DATAFORMATAS",
        "DATAPAGESIZE", "DATASRC", "DATETIME", "DECLARE", "DEFER", "DISABLED", "ENCTYPE",
        "EVENT", "FACE", "FOR", "FRAMEBORDER", "HEADERS", "HEIGHT", "HREF", "HREFLANG", "HSPACE",
        "HTTP-EQUIV", "ID", "ISMAP", "LANG", "LANGUAGE", "LEFTMARGIN", "LONGDESC",
        "MARGINWIDTH", "MARGINHEIGHT", "MAXLENGTH", "MEDIA", "METHOD", "MULTIPLE", "NAME", "NOHREF",
        "NORESIZE", "NOSHADE", "NOWRAP", "ONBLUR", "ONCHANGE", "ONCLICK", "ONDBLCLICK",
        "ONFOCUS", "ONKEYDOWN", "ONKEYPRESS", "ONKEYUP", "ONLOAD", "ONMOUSEDOWN", "ONMOUSEMOVE",
        "ONMOUSEOVER", "ONMOUSEOUT", "ONMOUSEUP", "ONRESET", "ONSELECT", "ONSUBMIT", "ONUNLOAD",
        "PROFILE", "PROMPT", "READONLY", "REL", "REV", "ROWS", "ROWSPAN", "RULES", "SCHEME", "SCOPE",
        "SELECTED", "SHAPE", "SIZE", "SRC", "STANDBY", "START", "SUMMARY", "TABINDEX",
        "TARGET", "TOPMARGIN", "TYPE", "USEMAP", "VALIGN", "VALUE", "VALUETYPE",
        "VERSION", "VLINK", "VSPACE", "WIDTH", "TEXT", "PASSWORD", "CHECKBOX", "RADIO", "SUBMIT", "RESET",
        "FILE", "HIDDEN", "IMAGE", "PUBLIC", "!DOCTYPE",
        "ADD_DATE", "LAST_MODIFIED", "LAST_VISIT"
    ]


#----------------------------------------------------------------------------
# Icon Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import ImageFromStream, BitmapFromImage
import cStringIO


def getHTMLData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\xeeIDAT8\x8d}\x92?h\x13a\x18\xc6\x7fw=\x8d\xb4\x98\xa9-uP\x1a\xc9p$\
\xdc`\xd0C\x8d\x8b)\xc5!Z\x11\xcc\xd0A\xd0*\xa8\x93\x8b8\x18\x11\x14RD\x07\t\
N\xfe\xc1\x0cRAtS\x1c,\xcd\x10\x8c\xd8S\xba$9"\x11L\r\x96\x92\xa4.\xda#i\xa5\
\xe7p^r\x97?\xbe\xd3\xf1~\xdf\xf3{\x9f\xe7\xbbW\xf8T(\x998j\xb9V\x07 _\xde\
\x0e\xc0\xad\x19U\xe0?%\x01\x0c\xef\x19owv\xf9\xff\x01\x96\x88N\x850\x92)\
\xf3\xde\x95s}!Rgcx\xdb\x9f\xd6\xf7Z\x13"\xa7\xcf\x00\xf4\x85t\x01\xea\x9b\
\xedV\xfa\xd53\x00\xb2z\xb3\x7f\x84\xe5Z\xbd\x15\xc1)>x,\x04\x84,\xc0\xed\'\
\xfd\x01\x9dB\xdb:\xc0\x8a\xb1E\xa3\xb2A8\xe0!\x9cL\x99\x00\x83;\x83D\x0fxQ\
\x15Y\xe8\x19\xc1\x16\xff\xfe\xf2\x11V\xaf\xb1\x03\x90G\xe0\xf5\xe7\n\xd5\
\xf58\xb0\xc4\xfc"\xbcL\xbf7c\x91#\x82h\xff\xae\xb5\xa6{\xf2\xdc\x9bi\x17\
\xf8\xc6\x85\xaf\x9c\xbf:\x03\xc0\xe8P\x82\x8bwN\xa2\xe5\x8a\xa6\xe8\x9cjW\
\xf1\xed\x1c`M\x05P\x94\xa7=\xf3\xcf\xa6&\x91\x8c_\x85\xd6c\xad\x18[\xae\x0b\
\'\xf6\xef\xe6h4\r\xc0\xcf\x1f\xd0\xa8l0:\x94 \x937\x00\xc8\xe4\r\xeb\r:\x85\
\xe3J\x0cy\xe41\xde\xb1\xbb\xd4\xbf\x97\x11\x07|\x00T\xcbz\x97\x0b\xb1\x97\
\xb5jY\xa71\xf6\x0e-Wb65\xc9\x8b\xf9\xe7,\xaenZg\xebq\xd7])\xab7\xc9\xea\xee\
\x8c\xdaB\x90\xf8u\xbde\x13n\xb6\x96I[\x08\xa2N$(~\x8b#\xfb\x12H\x1f\x1e^\
\xeaZQ-W4\x0f\x9f\xaa\x01~\x8eO\r\x92\xc9\x1b\xc8>KlC\xbc{!\x1c\xf0\xf4\x8e\
\xa0*\xb2\x90|\xb4\xcf\xe1\xa0-v\xd6\xe5\xb3\xd3\x08\x828\xd0\x8b\x01X\xcb\
\xa2\xe5J\xdc\x7f\xe0o\xc3\'\n\x84\x03\x1eb\x91C\xa8\x8a,\xfc\x05\xf6\x0e\
\xbfa\x1f\xe7Z\xfb\x00\x00\x00\x00IEND\xaeB`\x82' 


def getHTMLBitmap():
    return BitmapFromImage(getHTMLImage())

def getHTMLImage():
    stream = cStringIO.StringIO(getHTMLData())
    return ImageFromStream(stream)

def getHTMLIcon():
    return wx.IconFromBitmap(getHTMLBitmap())