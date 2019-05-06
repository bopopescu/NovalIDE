#-------------------------------------------------------------------------------
# Name:        generalopt.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-04-18
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import _
import tkinter as tk
from tkinter import ttk
import noval.util.apputils as apputils
import glob
import os
import noval.consts as consts
import noval.util.utils as utils


OPT_NO_OP    = 0
OPT_DESCRIPT = 1

MIN_MRU_FILE_LIMIT = 1
MAX_MRU_FILE_LIMIT = 20

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

class GeneralOptionPanel(ttk.Frame):
    """
    A general options panel that is used in the OptionDialog to configure the
    generic properties of a pydocview application, such as "show tips at startup"
    and whether to use SDI or MDI for the application.
    """


    def __init__(self, master, **kwargs):
        """
        Initializes the panel by adding an "Options" folder tab to the parent notebook and
        populating the panel with the generic properties of a pydocview application.
        """
        ttk.Frame.__init__(self,master=master,**kwargs)
        
       # self._showTipsCheckBox = wx.CheckBox(self, -1, _("Show tips at start up"))
        #self._showTipsCheckBox.SetValue(config.ReadInt("ShowTipAtStartup", True))
        self.checkupdate_var = tk.IntVar(value=utils.profile_get_int(consts.CHECK_UPDATE_ATSTARTUP_KEY, True))
        chkUpdateCheckBox = ttk.Checkbutton(self, text=_("Check update at start up"),variable=self.checkupdate_var)
        chkUpdateCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y))

        row = ttk.Frame(self)
        self.language_combox = ttk.Combobox(row,text=utils.profile_get("Language",""))
        ttk.Label(row, text=_("Language") + u": ").pack(side=tk.LEFT,fill="x")
        self.language_combox.pack(side=tk.LEFT,fill="x")
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.enablemru_var = tk.IntVar(value=utils.profile_get_int(consts.ENABLE_MRU_KEY, True))
        enableMRUCheckBox = ttk.Checkbutton(self, text=_("Enable MRU Menu"),variable=self.enablemru_var)
        enableMRUCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
###        self.Bind(wx.EVT_CHECKBOX,self.checkEnableMRU,self._enableMRUCheckBox)

        row = ttk.Frame(self)
        self._mru_ctrl = ttk.Entry(row, text=str(utils.profile_get_int(consts.MRU_LENGTH_KEY,consts.DEFAULT_MRU_FILE_NUM)))
        ttk.Label(row, text=_("File History length in MRU Files") + "(%d-%d): " % \
                                                            (MIN_MRU_FILE_LIMIT,MAX_MRU_FILE_LIMIT)).pack(side=tk.LEFT)
        self._mru_ctrl.pack(side=tk.LEFT)
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
       ### self.checkEnableMRU(None)

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
        config.Write(consts.MRU_LENGTH_KEY,self._mru_ctrl.GetValue())
        config.WriteInt(consts.ENABLE_MRU_KEY,self._enableMRUCheckBox.GetValue())
        
        return True


    def GetIcon(self):
        """ Return icon for options panel on the Mac. """
        return wx.GetApp().GetDefaultIcon()
