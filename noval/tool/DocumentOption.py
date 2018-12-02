import wx
from consts import _,HALF_SPACE,SPACE,EDITOR_CONTENT_PANE_NAME,TabAlignTop,TabAlignBottom,DEFAULT_FILE_ENCODING_KEY,\
        REMBER_FILE_KEY,CHECK_EOL_KEY,DEFAULT_DOCUMENT_TYPE_NAME
import noval.tool.aui as aui
import sys
import codecs
import noval.util.utils as utils
import locale

def GetEncodings():
    """Get a list of possible encodings to try from the locale information
    @return: list of strings

    """
    encodings = list()
    try:
        encodings.append(locale.getpreferredencoding())
    except:
        pass
    encodings.append('ascii')
    encodings.append('utf-8')

    try:
        if hasattr(locale, 'nl_langinfo'):
            encodings.append(locale.nl_langinfo(locale.CODESET))
    except:
        pass
    try:
        encodings.append(locale.getlocale()[1])
    except:
        pass
    try:
        encodings.append(locale.getdefaultlocale()[1])
    except:
        pass
    encodings.append(sys.getfilesystemencoding())
    encodings.append('utf-16')
    encodings.append('utf-16-le') # for files without BOM...
    encodings.append('latin-1')
    encodings.append('gbk')
    encodings.append('gb18030')
    encodings.append('gb2312')
    encodings.append('big5')

    # Normalize all names
    normlist = [ enc for enc in encodings if enc]
    # Clean the list for duplicates and None values
    rlist = list()
    codec_list = list()
    for enc in normlist:
        if enc is not None and len(enc):
            enc = enc.lower()
            if enc not in rlist:
                try:
                    ctmp = codecs.lookup(enc)
                    if ctmp.name not in codec_list:
                        codec_list.append(ctmp.name)
                        rlist.append(enc)
                except LookupError:
                    pass
    return rlist

class DocumentOptionsPanel(wx.Panel):
    """
    A general options panel that is used in the OptionDialog to configure the
    generic properties of a pydocview application, such as "show tips at startup"
    and whether to use SDI or MDI for the application.
    """


    TabArts = [aui.AuiDefaultTabArt, aui.AuiSimpleTabArt, aui.VC71TabArt, aui.FF2TabArt,
                aui.VC8TabArt, aui.ChromeTabArt]
                
    TabsStyles = ['Glossy Theme','Simple Theme','VC71 Theme','Firefox 2 Theme'\
                       ,'VC8 Theme','Chrome Theme']

    def __init__(self, parent, id,size):
        wx.Panel.__init__(self, parent, id,size=size)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        optionsSizer = wx.BoxSizer(wx.VERTICAL)
        config = wx.ConfigBase_Get()
        if self._AllowModeChanges():
            supportedModes = self.GetParent().GetService().GetSupportedModes()
            choices = []
            self._sdiChoice = _("Show each document in its own window")
            self._mdiChoice = _("Show all documents in a single window with tabs")
            self._winMdiChoice = _("Show all documents in a single window with child windows")
            if supportedModes & wx.lib.docview.DOC_SDI:
                choices.append(self._sdiChoice)
            choices.append(self._mdiChoice)
            if wx.Platform == "__WXMSW__":
                choices.append(self._winMdiChoice)
            self._documentRadioBox = wx.RadioBox(self, -1, _("Document Display Style"),size=(-1,-1),
                                          choices = choices,
                                          majorDimension=1,
                                          )
            if config.ReadInt("UseWinMDI", False):
                self._documentRadioBox.SetStringSelection(self._winMdiChoice)
            elif config.ReadInt("UseMDI", True):
                self._documentRadioBox.SetStringSelection(self._mdiChoice)
            else:
                self._documentRadioBox.SetStringSelection(self._sdiChoice)
            def OnDocumentInterfaceSelect(event):
                if not self._documentInterfaceMessageShown:
                    msgTitle = wx.GetApp().GetAppName()
                    if not msgTitle:
                        msgTitle = _("Document Options")
                    wx.MessageBox(_("Document interface changes will not appear until the application is restarted."),
                                  msgTitle,
                                  wx.OK | wx.ICON_INFORMATION,
                                  self.GetParent())
                    self._documentInterfaceMessageShown = True
            wx.EVT_RADIOBOX(self, self._documentRadioBox.GetId(), OnDocumentInterfaceSelect)
            

        if self._AllowModeChanges():
            optionsSizer.Add(self._documentRadioBox, 0, wx.ALL|wx.EXPAND, HALF_SPACE)
                    
        if wx.GetApp().GetUseTabbedMDI():
            self._tabAlignmentRadioBox = wx.RadioBox(self, -1, _("Tabs Alignment"),size=(-1,-1),
                        choices = [_('Align top of document'),_('Align bottom of document')],
                            majorDimension=1,
                    )
            tabs_alignment = config.ReadInt("TabsAlignment",TabAlignTop)
            if tabs_alignment == TabAlignBottom:
                self._tabAlignmentRadioBox.SetStringSelection(_('Align bottom of document'))
            elif tabs_alignment == TabAlignTop:
                self._tabAlignmentRadioBox.SetStringSelection(_('Align top of document'))
            optionsSizer.Add(self._tabAlignmentRadioBox, 0, wx.ALL|wx.EXPAND, HALF_SPACE)
            
            lsizer = wx.BoxSizer(wx.HORIZONTAL)
            self.tabs_styles_combo = wx.ComboBox(self, -1,choices = self.TabsStyles,value="", \
                                style = wx.CB_READONLY)
            lsizer.AddMany([(wx.StaticText(self, label=_("Tabs style list") + u": "),
                             0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                            (self.tabs_styles_combo,
                             0, wx.ALIGN_CENTER_VERTICAL)])
            optionsSizer.Add(lsizer, 0, wx.ALL, HALF_SPACE)
            tab_art_index = config.ReadInt("TabStyle",self.TabArts.index(aui.ChromeTabArt))
            self.tabs_styles_combo.SetSelection(tab_art_index)
            self._showCloseBtnCheckBox = wx.CheckBox(self, -1, _("Show close button on tabs"))
            self._showCloseBtnCheckBox.SetValue(config.ReadInt("ShowCloseButton",True))
            optionsSizer.Add(self._showCloseBtnCheckBox, 0, wx.ALL, HALF_SPACE)
            
        lsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.encodings_combo = wx.ComboBox(self, -1,choices = GetEncodings(),value=config.Read(DEFAULT_FILE_ENCODING_KEY,""), \
                            style = wx.CB_READONLY)
        lsizer.AddMany([(wx.StaticText(self, label=_("File Default Encoding") + u": "),
                         0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                        (self.encodings_combo,
                         0, wx.ALIGN_CENTER_VERTICAL)])
        optionsSizer.Add(lsizer, 0, wx.ALL, HALF_SPACE)

        self._chkEOLCheckBox = wx.CheckBox(self, -1, _("Warn when mixed eol characters are detected"))
        self._chkEOLCheckBox.SetValue(config.ReadInt(CHECK_EOL_KEY, True))
        optionsSizer.Add(self._chkEOLCheckBox, 0, wx.ALL, HALF_SPACE)
        
        self._remberCheckBox = wx.CheckBox(self, -1, _("Remember File Position"))
        self._remberCheckBox.SetValue(config.ReadInt(REMBER_FILE_KEY, True))
        optionsSizer.Add(self._remberCheckBox, 0, wx.ALL, HALF_SPACE)
        
        lsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.document_types_combox = wx.ComboBox(self, -1,choices=[],style= wx.CB_READONLY)
        lsizer.AddMany([(wx.StaticText(self, label=_("Default New Document Type") + u": "),
                         0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                        (self.document_types_combox,
                         0, wx.ALIGN_CENTER_VERTICAL)])
        self.InitDocumentTypes()

        optionsSizer.Add(lsizer, 0, wx.ALL, HALF_SPACE)
        
        main_sizer.Add(optionsSizer, 0, wx.ALL|wx.EXPAND, SPACE)
        self.SetSizer(main_sizer)
        self.Layout()
        self._documentInterfaceMessageShown = False

    def _AllowModeChanges(self):
        supportedModes = self.GetParent().GetService().GetSupportedModes()
        return supportedModes & wx.lib.docview.DOC_SDI and supportedModes & wx.lib.docview.DOC_MDI or wx.Platform == "__WXMSW__" and supportedModes & wx.lib.docview.DOC_MDI  # More than one mode is supported, allow selection

    def OnOK(self, optionsDialog):
        """
        Updates the config based on the selections in the options panel.
        """
        config = wx.ConfigBase_Get()
        if self._AllowModeChanges():
            config.WriteInt("UseMDI", (self._documentRadioBox.GetStringSelection() == self._mdiChoice))
            config.WriteInt("UseWinMDI", (self._documentRadioBox.GetStringSelection() == self._winMdiChoice))
            
        if wx.GetApp().GetUseTabbedMDI():
            config.WriteInt("ShowCloseButton",self._showCloseBtnCheckBox.GetValue())
            config.WriteInt("TabStyle",self.tabs_styles_combo.GetSelection())
            if self._tabAlignmentRadioBox.GetStringSelection() == _('Align bottom of document'):
                config.WriteInt("TabsAlignment",TabAlignBottom)
            else:
                config.WriteInt("TabsAlignment",TabAlignTop)
            self.OnNotebookFlag()
            
        config.Write(DEFAULT_FILE_ENCODING_KEY,self.encodings_combo.GetValue())
        config.WriteInt(REMBER_FILE_KEY, self._remberCheckBox.GetValue())
        config.WriteInt(CHECK_EOL_KEY, self._chkEOLCheckBox.GetValue())
        sel = self.document_types_combox.GetSelection()
        if sel != -1:
            template = self.document_types_combox.GetClientData(sel)
            config.Write("DefaultDocumentType",template.GetDocumentName())
        return True
        
    def OnNotebookFlag(self):
        notebook_style = wx.GetApp().MainFrame._notebook_style
        notebook_style &= ~(aui.AUI_NB_CLOSE_ON_ACTIVE_TAB|aui.AUI_NB_TOP|aui.AUI_NB_BOTTOM|aui.AUI_NB_CLOSE_BUTTON)
        if self._showCloseBtnCheckBox.GetValue():
            notebook_style ^= aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
        else:
            notebook_style ^= aui.AUI_NB_CLOSE_BUTTON

        all_panes = wx.GetApp().MainFrame._mgr.GetAllPanes()
        sel = self.tabs_styles_combo.GetSelection()
        art_provider = self.TabArts[sel]
        for pane in all_panes:
            if isinstance(pane.window, aui.AuiNotebook):
                if not pane.name == EDITOR_CONTENT_PANE_NAME:
                    continue
                nb = pane.window
                if self._tabAlignmentRadioBox.GetStringSelection() == _('Align bottom of document'):
                    notebook_style &= ~aui.AUI_NB_TOP
                    notebook_style ^= aui.AUI_NB_BOTTOM
                else:
                    notebook_style &= ~aui.AUI_NB_BOTTOM
                    notebook_style ^= aui.AUI_NB_TOP
                nb.SetAGWWindowStyleFlag(notebook_style)
                nb.SetArtProvider(art_provider())
                    
                nb.Refresh()
                nb.Update()

    def InitDocumentTypes(self):
        document_type_name = utils.ProfileGet("DefaultDocumentType",DEFAULT_DOCUMENT_TYPE_NAME)
        templates = []
        for temp in wx.GetApp().GetDocumentManager().GetTemplates():
            #filter image document and any file document
            if temp.IsVisible() and temp.IsNewable():
                templates.append(temp)
        for temp in templates:
            i = self.document_types_combox.Append(_(temp.GetDescription()))
            if document_type_name == temp.GetDocumentName():
                self.document_types_combox.SetSelection(i)
            self.document_types_combox.SetClientData(i,temp)
