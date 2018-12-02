import wx
import wx.lib.pydocview
import wx.lib.langlistctrl as langlist
import noval.util.sysutils as sysutilslib
import glob
import wx.combo
import os
import consts
from Validator import NumValidator

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
        
        optionsBorderSizer = wx.BoxSizer(wx.VERTICAL)
        optionsSizer = wx.BoxSizer(wx.VERTICAL)

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
        
        optionsBorderSizer.Add(optionsSizer, 0, wx.ALL|wx.EXPAND, SPACE)
        self.SetSizer(optionsBorderSizer)
        self.Layout()
        self.checkEnableMRU(None)

    def checkEnableMRU(self,event):
        enableMRU = self._enableMRUCheckBox.GetValue()
        self._mru_ctrl.Enable(enableMRU)

    def OnOK(self, optionsDialog):
        """
        Updates the config based on the selections in the options panel.
        """
        config = wx.ConfigBase_Get()
        config.WriteInt("ShowTipAtStartup", self._showTipsCheckBox.GetValue())
        config.WriteInt(consts.CHECK_UPDATE_ATSTARTUP_KEY, self._chkUpdateCheckBox.GetValue())
        if self.language_combox.GetValue() != config.Read("Language",""):
            wx.MessageBox(_("Language changes will not appear until the application is restarted."),
              _("Language Options"),
              wx.OK | wx.ICON_INFORMATION,
              self.GetParent())
        config.Write("Language",self.language_combox.GetValue())
        config.Write("MRULength",self._mru_ctrl.GetValue())
        config.WriteInt("EnableMRU",self._enableMRUCheckBox.GetValue())
        
        return True


    def GetIcon(self):
        """ Return icon for options panel on the Mac. """
        return wx.GetApp().GetDefaultIcon()
