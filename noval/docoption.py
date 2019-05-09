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

class DocumentOptionsPanel(ttk.Frame):
    """
    A general options panel that is used in the OptionDialog to configure the
    generic properties of a pydocview application, such as "show tips at startup"
    and whether to use SDI or MDI for the application.
    """

    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self._showCloseBtnCheckBox = ttk.Checkbutton(self, -1, _("Show close button on tabs"))
        self._showCloseBtnCheckBox.SetValue(config.ReadInt("ShowCloseButton",True))

        self.encodings_combo = ttk.Combobox(self, choices = GetEncodings(),value=config.Read(DEFAULT_FILE_ENCODING_KEY,""), \
                            style = wx.CB_READONLY)
        ttk.Label(self, text=_("File Default Encoding") + u": "))
    
        self._chkEOLCheckBox = ttk.Checkbutton(self, -1, _("Warn when mixed eol characters are detected"))
        self._chkEOLCheckBox.SetValue(config.ReadInt(CHECK_EOL_KEY, True))
        self._remberCheckBox = ttk.Checkbutton(self, -1, _("Remember File Position"))
        self._remberCheckBox.SetValue(config.ReadInt(REMBER_FILE_KEY, True))

        self.document_types_combox = wx.ComboBox(self, -1,choices=[],style= wx.CB_READONLY)
        ttk.Label(self, text=_("Default New Document Type") + u": "))
        self.InitDocumentTypes()

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
