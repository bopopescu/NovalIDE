import wx
import wx.lib.pydocview
import wx.lib.langlistctrl as langlist
import noval.util.sysutils as sysutilslib
import glob
import wx.combo
import os
import sys
import codecs
import consts
from Validator import NumValidator
import noval.util.utils as utils

_ = wx.GetTranslation


OPT_NO_OP    = 0
OPT_DESCRIPT = 1

def GetAvailLocales():
    """Gets a list of the available locales that have been installed
    for the editor. Returning a list of strings that represent the
    canonical names of each language.
    @return: list of all available local/languages available

    """
    avail_loc = list()
    loc = glob.glob(os.path.join(sysutilslib.mainModuleDir,'noval','locale', "*"))
    for path in loc:
        the_path = os.path.join(path, "LC_MESSAGES", consts.APPLICATION_NAME.lower() + ".mo")
        if os.path.exists(the_path):
            avail_loc.append(os.path.basename(path))
    return avail_loc

def GetLocaleDict(loc_list, opt=OPT_NO_OP):
    """Takes a list of cannonical locale names and by default returns a
    dictionary of available language values using the canonical name as
    the key. Supplying the Option OPT_DESCRIPT will return a dictionary
    of language id's with languages description as the key.
    @param loc_list: list of locals
    @keyword opt: option for configuring return data
    @return: dict of locales mapped to wx.LANGUAGE_*** values

    """
    lang_dict = dict()
    for lang in [x for x in dir(wx) if x.startswith("LANGUAGE_")]:
        langId = getattr(wx, lang)
        langOk = False
        try:
            langOk = wx.Locale.IsAvailable(langId)
        except wx.PyAssertionError:
            continue

        if langOk:
            loc_i = wx.Locale.GetLanguageInfo(langId)
            if loc_i:
                if loc_i.CanonicalName in loc_list:
                    if opt == OPT_DESCRIPT:
                        lang_dict[loc_i.Description] = langId
                    else:
                        lang_dict[loc_i.CanonicalName] = langId
    return lang_dict

def GetLangId(lang_n):
    """Gets the ID of a language from the description string. If the
    language cannot be found the function simply returns the default language
    @param lang_n: Canonical name of a language
    @return: wx.LANGUAGE_*** id of language

    """
    if lang_n == "Default" or lang_n == '' or lang_n.lower() == "english":
        # No language set, default to English
        return wx.LANGUAGE_ENGLISH_US
    elif lang_n.lower() == "chinese":
        return wx.LANGUAGE_CHINESE_SIMPLIFIED
        
    lang_desc = GetLocaleDict(GetAvailLocales(), OPT_DESCRIPT)
    return lang_desc.get(lang_n, wx.LANGUAGE_DEFAULT)

#---- Language List Combo Box----#
class LangListCombo(wx.combo.BitmapComboBox):
    """Combines a langlist and a BitmapComboBox"""
    def __init__(self, parent, id_, default=None):
        """Creates a combobox with a list of all translations for the
        editor as well as displaying the countries flag next to the item
        in the list.

        @param default: The default item to show in the combo box

        """
        lang_ids = GetLocaleDict(GetAvailLocales()).values()
        lang_items = langlist.CreateLanguagesResourceLists(langlist.LC_ONLY, \
                                                           lang_ids)
        wx.combo.BitmapComboBox.__init__(self, parent, id_,
                                         size=wx.Size(250, 26),
                                         style=wx.CB_READONLY)
        for lang_d in lang_items[1]:
            bit_m = lang_items[0].GetBitmap(lang_items[1].index(lang_d))
            self.Append(lang_d, bit_m)

        if default:
            self.SetValue(default)
            
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

class GeneralOptionsPanel(wx.Panel):
    """
    A general options panel that is used in the OptionDialog to configure the
    generic properties of a pydocview application, such as "show tips at startup"
    and whether to use SDI or MDI for the application.
    """


    def __init__(self, parent, id,size):
        """
        Initializes the panel by adding an "Options" folder tab to the parent notebook and
        populating the panel with the generic properties of a pydocview application.
        """
        wx.Panel.__init__(self, parent, id,size=size)
        SPACE = 10
        HALF_SPACE = 5
        config = wx.ConfigBase_Get()
        self._showTipsCheckBox = wx.CheckBox(self, -1, _("Show tips at start up"))
        self._showTipsCheckBox.SetValue(config.ReadInt("ShowTipAtStartup", True))
        
        self._chkUpdateCheckBox = wx.CheckBox(self, -1, _("Check update at start up"))
        self._chkUpdateCheckBox.SetValue(config.ReadInt(consts.CHECK_UPDATE_ATSTARTUP_KEY, True))
        
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
        optionsBorderSizer = wx.BoxSizer(wx.VERTICAL)
        optionsSizer = wx.BoxSizer(wx.VERTICAL)
        if self._AllowModeChanges():
            optionsSizer.Add(self._documentRadioBox, 0, wx.LEFT|wx.EXPAND, HALF_SPACE)
        optionsSizer.Add(self._showTipsCheckBox, 0, wx.ALL, HALF_SPACE)
        optionsSizer.Add(self._chkUpdateCheckBox, 0, wx.ALL, HALF_SPACE)

        lsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.language_combox = LangListCombo(self, -1,config.Read("Language",""))
        lsizer.AddMany([(wx.StaticText(self, label=_("Language") + u": "),
                         0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                        (self.language_combox,
                         0, wx.ALIGN_CENTER_VERTICAL)])

        optionsSizer.Add(lsizer, 0, wx.ALL, HALF_SPACE)

        self._enableMRUCheckBox = wx.CheckBox(self, -1, _("Enable MRU Menu"))
        self._enableMRUCheckBox.SetValue(config.ReadInt("EnableMRU", True))
        self.Bind(wx.EVT_CHECKBOX,self.checkEnableMRU,self._enableMRUCheckBox)
        optionsSizer.Add(self._enableMRUCheckBox, 0, wx.ALL, HALF_SPACE)

        lsizer = wx.BoxSizer(wx.HORIZONTAL)
        self._mru_ctrl = wx.TextCtrl(self, -1, config.Read("MRULength",str(consts.DEFAULT_MRU_FILE_NUM)), size=(30,-1),\
                                validator=NumValidator(_("MRU Length"),consts.MIN_MRU_FILE_LIMIT,consts.MAX_MRU_FILE_LIMIT))
        lsizer.AddMany([(wx.StaticText(self, label=_("File History length in MRU Files") + "(%d-%d): " % \
                                                            (consts.MIN_MRU_FILE_LIMIT,consts.MAX_MRU_FILE_LIMIT)),
                         0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                        (self._mru_ctrl,
                         0, wx.ALIGN_CENTER_VERTICAL)])
        optionsSizer.Add(lsizer, 0, wx.ALL, HALF_SPACE)
        
        lsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.encodings_combo = wx.ComboBox(self, -1,choices = GetEncodings(),value=config.Read(consts.DEFAULT_FILE_ENCODING_KEY,""), \
                            style = wx.CB_READONLY)
        lsizer.AddMany([(wx.StaticText(self, label=_("File Default Encoding") + u": "),
                         0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                        (self.encodings_combo,
                         0, wx.ALIGN_CENTER_VERTICAL)])
        optionsSizer.Add(lsizer, 0, wx.ALL, HALF_SPACE)
        

        self._chkEOLCheckBox = wx.CheckBox(self, -1, _("Warn when mixed eol characters are detected"))
        self._chkEOLCheckBox.SetValue(config.ReadInt(consts.CHECK_EOL_KEY, True))
        optionsSizer.Add(self._chkEOLCheckBox, 0, wx.ALL, HALF_SPACE)
        
        self._remberCheckBox = wx.CheckBox(self, -1, _("Remember File Position"))
        self._remberCheckBox.SetValue(config.ReadInt(consts.REMBER_FILE_KEY, True))
        optionsSizer.Add(self._remberCheckBox, 0, wx.ALL, HALF_SPACE)
        
        lsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.document_types_combox = wx.ComboBox(self, -1,choices=[],style= wx.CB_READONLY)
        lsizer.AddMany([(wx.StaticText(self, label=_("Default New Document Type") + u": "),
                         0, wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                        (self.document_types_combox,
                         0, wx.ALIGN_CENTER_VERTICAL)])
        self.InitDocumentTypes()

        optionsSizer.Add(lsizer, 0, wx.ALL, HALF_SPACE)

        optionsBorderSizer.Add(optionsSizer, 0, wx.ALL|wx.EXPAND, SPACE)
        self.SetSizer(optionsBorderSizer)
        self.Layout()
        self._documentInterfaceMessageShown = False
        self.checkEnableMRU(None)
        
    def InitDocumentTypes(self):
        document_type_name = utils.ProfileGet("DefaultDocumentType",consts.DEFAULT_DOCUMENT_TYPE_NAME)
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

    def checkEnableMRU(self,event):
        enableMRU = self._enableMRUCheckBox.GetValue()
        self._mru_ctrl.Enable(enableMRU)

    def _AllowModeChanges(self):
        supportedModes = self.GetParent().GetService().GetSupportedModes()
        return supportedModes & wx.lib.docview.DOC_SDI and supportedModes & wx.lib.docview.DOC_MDI or wx.Platform == "__WXMSW__" and supportedModes & wx.lib.docview.DOC_MDI  # More than one mode is supported, allow selection


    def OnOK(self, optionsDialog):
        """
        Updates the config based on the selections in the options panel.
        """
        config = wx.ConfigBase_Get()
        config.WriteInt("ShowTipAtStartup", self._showTipsCheckBox.GetValue())
        config.WriteInt(consts.CHECK_UPDATE_ATSTARTUP_KEY, self._chkUpdateCheckBox.GetValue())
        config.WriteInt(consts.CHECK_EOL_KEY, self._chkEOLCheckBox.GetValue())
        if self.language_combox.GetValue() != config.Read("Language",""):
            wx.MessageBox(_("Language changes will not appear until the application is restarted."),
              _("Language Options"),
              wx.OK | wx.ICON_INFORMATION,
              self.GetParent())
        config.Write("Language",self.language_combox.GetValue())
        config.Write("MRULength",self._mru_ctrl.GetValue())
        config.WriteInt("EnableMRU",self._enableMRUCheckBox.GetValue())
        config.Write(consts.DEFAULT_FILE_ENCODING_KEY,self.encodings_combo.GetValue())
        config.WriteInt(consts.REMBER_FILE_KEY, self._remberCheckBox.GetValue())
        sel = self.document_types_combox.GetSelection()
        if sel != -1:
            template = self.document_types_combox.GetClientData(sel)
            config.Write("DefaultDocumentType",template.GetDocumentName())
        if self._AllowModeChanges():
            config.WriteInt("UseMDI", (self._documentRadioBox.GetStringSelection() == self._mdiChoice))
            config.WriteInt("UseWinMDI", (self._documentRadioBox.GetStringSelection() == self._winMdiChoice))
        return True


    def GetIcon(self):
        """ Return icon for options panel on the Mac. """
        return wx.GetApp().GetDefaultIcon()
