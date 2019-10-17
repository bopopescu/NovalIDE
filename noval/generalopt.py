# -*- coding: utf-8 -*-
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
from noval import _,Locale,GetApp
import tkinter as tk
from tkinter import ttk,messagebox
import noval.util.apputils as apputils
import glob
import os
import noval.consts as consts
import noval.util.utils as utils
import noval.ui_lang as ui_lang
import noval.ui_utils as ui_utils

MIN_MRU_FILE_LIMIT = 1
MAX_MRU_FILE_LIMIT = 20

def GetAvailLocales():
    """Gets a list of the available locales that have been installed
    for the editor. Returning a list of strings that represent the
    canonical names of each language.
    @return: list of all available local/languages available

    """
    avail_loc = list()
    loc = glob.glob(os.path.join(apputils.mainModuleDir,'locale', "*"))
    for path in loc:
        the_path = os.path.join(path, "LC_MESSAGES", consts.APPLICATION_NAME.lower() + ".mo")
        if os.path.exists(the_path):
            avail_loc.append(os.path.basename(path))
    return avail_loc

def GetLocaleDict(loc_list):
    """Takes a list of cannonical locale names and by default returns a
    dictionary of available language values using the canonical name as
    the key. Supplying the Option OPT_DESCRIPT will return a dictionary
    of language id's with languages description as the key.
    @param loc_list: list of locals
    @keyword opt: option for configuring return data
    @return: dict of locales mapped to wx.LANGUAGE_*** values

    """
    lang_dict = dict()
    for lang in [x for x in dir(ui_lang) if x.startswith("LANGUAGE_")]:
        langId = getattr(ui_lang, lang)
        langOk = Locale.IsAvailable(langId)
        if langOk:
            loc_i = Locale(langId)
            if loc_i.GetLanguageCanonicalName() in loc_list:
                lang_dict[loc_i.GetLanguageName()] = langId
    return lang_dict

def GetLangName(langId):
    """Gets the ID of a language from the description string. If the
    language cannot be found the function simply returns the default language
    @param lang_n: Canonical name of a language
    @return: wx.LANGUAGE_*** id of language

    """
    langOk = Locale.IsAvailable(langId)
    if not langOk:
        raise RuntimeError("unknown lang id %d",langId)
        
    loc_i = Locale(langId)
    return loc_i.GetLanguageName()
    
def GetLangList():
    lang_list = []
    available_locales = GetAvailLocales()
    lang_ids = GetLocaleDict(available_locales).values()
    for i,lang_id in enumerate(lang_ids):
        loc_i = Locale(lang_id)
        lang_list.append((i,lang_id,loc_i.GetLanguageName()),)
    return lang_list

class GeneralOptionPanel(ui_utils.BaseConfigurationPanel):
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
        ui_utils.BaseConfigurationPanel.__init__(self,master=master,**kwargs)
        
       # self._showTipsCheckBox = wx.CheckBox(self, -1, _("Show tips at start up"))
        #self._showTipsCheckBox.SetValue(config.ReadInt("ShowTipAtStartup", True))
        self.checkupdate_var = tk.IntVar(value=utils.profile_get_int(consts.CHECK_UPDATE_ATSTARTUP_KEY, True))
        chkUpdateCheckBox = ttk.Checkbutton(self, text=_("Check update at start up"),variable=self.checkupdate_var)
        chkUpdateCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        self.check_plugin_update_var = tk.IntVar(value=utils.profile_get_int("CheckPluginUpdate", True))
        chkplugin_UpdateCheckBox = ttk.Checkbutton(self, text=_("Check plugin update at start up"),variable=self.check_plugin_update_var)
        chkplugin_UpdateCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")

        row = ttk.Frame(self)
        self.lang_list = GetLangList()
        values = [_(lang[2]) for lang in self.lang_list]
        self.lang_id = utils.profile_get_int(consts.LANGUANGE_ID_KEY,-1)
        try:
            #安装包选择中文安装界面时,没有写入注册表,这里修复在界面的语言框里面显示为空的问题
            if self.lang_id == -1 and GetApp().locale.LangId != ui_lang.LANGUAGE_DEFAULT:
                self.lang_id = GetApp().locale.LangId
            lang_name = GetLangName(self.lang_id)
            #显示翻译后的语言名称
            lang = _(lang_name)
        except RuntimeError as e:
            utils.get_logger().error(e)
            lang = ""
        self.language_var = tk.StringVar(value=lang)
        self.language_combox = ttk.Combobox(row,textvariable=self.language_var,values=values,state="readonly")
        ttk.Label(row, text=_("Language") + u": ").pack(side=tk.LEFT,fill="x")
        self.language_combox.pack(side=tk.LEFT,fill="x")
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.enablemru_var = tk.IntVar(value=utils.profile_get_int(consts.ENABLE_MRU_KEY, True))
        enableMRUCheckBox = ttk.Checkbutton(self, text=_("Enable MRU Menu"),variable=self.enablemru_var,command=self.checkEnableMRU)
        enableMRUCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")

        row = ttk.Frame(self)
        self.mru_var = tk.IntVar(value=utils.profile_get_int(consts.MRU_LENGTH_KEY,consts.DEFAULT_MRU_FILE_NUM))
        #验证历史文件个数文本控件输入是否合法
        validate_cmd = self.register(self.validateMRUInput)
        self.mru_ctrl = ttk.Entry(row,validate = 'key', textvariable=self.mru_var,validatecommand = (validate_cmd, '%P'))
        ttk.Label(row, text=_("File History length in MRU Files") + "(%d-%d): " % \
                                                            (MIN_MRU_FILE_LIMIT,MAX_MRU_FILE_LIMIT)).pack(side=tk.LEFT)
        self.mru_ctrl.pack(side=tk.LEFT)
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))

        self.redirect_output_var = tk.IntVar(value=utils.profile_get_int("RedirectTkException", True if GetApp().GetDebug() else False))
        redirectOutputCheckBox = ttk.Checkbutton(self, text=_("Redirect Application exception output to Message dialog"),variable=self.redirect_output_var)
        redirectOutputCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")

        self.checkEnableMRU()
       
    def validateMRUInput(self,contents):
        if not contents.isdigit():
            self.mru_ctrl.bell()
            return False
        return True

    def checkEnableMRU(self):
        enableMRU = self.enablemru_var.get()
        if enableMRU:
            self.mru_ctrl["state"] = "normal"
        else:
            self.mru_ctrl["state"] = tk.DISABLED

    def GetLangId(self):
        current = self.language_combox.current()
        if current == -1:
            return -1
        for i,lang in enumerate(self.lang_list):
            if i == current:
                return lang[1]

    def OnOK(self, optionsDialog):
        """
        Updates the config based on the selections in the options panel.
        """
        if self.enablemru_var.get() and self.mru_var.get() > consts.MAX_MRU_FILE_LIMIT:
            messagebox.showerror(GetApp().GetAppName(),_("MRU Length must not be greater than %d")%consts.MAX_MRU_FILE_LIMIT,parent=self)
            return False
            
        if self.enablemru_var.get() and self.mru_var.get() < 1:
            messagebox.showerror(GetApp().GetAppName(),_("MRU Length must not be less than 1"),parent=self)
            return False
            
       # utils.WriteInt("ShowTipAtStartup", self._showTipsCheckBox.GetValue())
        utils.profile_set(consts.CHECK_UPDATE_ATSTARTUP_KEY, self.checkupdate_var.get())
        if self.GetLangId() != self.lang_id:
            messagebox.showinfo(_("Language Options"),_("Language changes will not appear until the application is restarted."),parent=self)
            utils.profile_set(consts.LANGUANGE_ID_KEY,self.GetLangId())
        utils.profile_set(consts.MRU_LENGTH_KEY,self.mru_var.get())
        utils.profile_set(consts.ENABLE_MRU_KEY,self.enablemru_var.get())
        utils.profile_set("RedirectTkException",self.redirect_output_var.get())
        utils.profile_set("CheckPluginUpdate",self.check_plugin_update_var.get())
        return True

    def GetIcon(self):
        """ Return icon for options panel on the Mac. """
        return wx.GetApp().GetDefaultIcon()
