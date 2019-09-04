from noval import _,GetApp
import tkinter as tk
from tkinter import ttk
import sys
import codecs
import noval.util.utils as utils
import locale
import noval.consts as consts
import noval.ui_utils as ui_utils

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

class DocumentOptionsPanel(ui_utils.BaseConfigurationPanel):
    """
    A general options panel that is used in the OptionDialog to configure the
    generic properties of a pydocview application, such as "show tips at startup"
    and whether to use SDI or MDI for the application.
    """

    def __init__(self, parent):
        ui_utils.BaseConfigurationPanel.__init__(self, parent)
      #  self.checkupdate_var = tk.IntVar(value=utils.profile_get_int(consts.CHECK_UPDATE_ATSTARTUP_KEY, True))
       # self._showCloseBtnCheckBox = ttk.Checkbutton(self, -1, _("Show close button on tabs"))
        #chkUpdateCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y))
        #elf._showCloseBtnCheckBox.SetValue(config.ReadInt("ShowCloseButton",True))
        
        self._remberCheckVar = tk.IntVar(value=utils.profile_get_int(consts.REMBER_FILE_KEY, True))
        remberCheckBox = ttk.Checkbutton(self, text=_("Remember File Position"),variable=self._remberCheckVar)
        remberCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y))
        row = ttk.Frame(self)
        self.encodings_combo = ttk.Combobox(row, values = GetEncodings(),value=utils.profile_get(consts.DEFAULT_FILE_ENCODING_KEY,""), \
                            state = "readonly")
        ttk.Label(row, text=_("File Default Encoding") + u": ").pack(side=tk.LEFT,fill="x")
        self.encodings_combo.pack(side=tk.LEFT,fill="x")
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
        self._chkModifyCheckVar = tk.IntVar(value=utils.profile_get_int("CheckFileModify", True))
        chkModifyCheckBox = ttk.Checkbutton(self, text=_("Check if on disk file has been modified by others"),variable=self._chkModifyCheckVar)
        chkModifyCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        self._chkEOLCheckVar = tk.IntVar(value=utils.profile_get_int("check_mixed_eol", False))
        chkEOLCheckBox = ttk.Checkbutton(self, text=_("Warn when mixed eol characters are detected"),variable=self._chkEOLCheckVar)
        chkEOLCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        row = ttk.Frame(self)
        document_type_names,index,self.templates = self.GetDocumentTypes()
        self.document_types_combox = ttk.Combobox(row, values=document_type_names,state = "readonly")
        self.document_types_combox.current(index)
        ttk.Label(row, text=_("Default New Document Type") + u": ").pack(side=tk.LEFT,fill="x")
        self.document_types_combox.pack(side=tk.LEFT,fill="x")
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y)     

    def OnOK(self, optionsDialog):
        """
        Updates the config based on the selections in the options panel.
        """
    #    config.Write(DEFAULT_FILE_ENCODING_KEY,self.encodings_combo.GetValue())
        utils.profile_set(consts.REMBER_FILE_KEY, self._remberCheckVar.get())
        utils.profile_set("CheckFileModify", self._chkModifyCheckVar.get())
       # utils.profile_set(consts.CHECK_EOL_KEY, self._chkEOLCheckBox.GetValue())
        template = self.templates[self.document_types_combox.current()]
        utils.profile_set("DefaultDocumentType",template.GetDocumentName())
        utils.profile_set("check_mixed_eol",self._chkEOLCheckVar.get())
        return True

    def GetDocumentTypes(self):
        type_names = []
        default_document_typename = utils.profile_get("DefaultDocumentType",GetApp().GetDefaultTextDocumentType())
        current_document_typename = ''
        templates = []
        for temp in GetApp().GetDocumentManager().GetTemplates():
            #filter image document and any file document
            if temp.IsVisible() and temp.IsNewable():
                templates.append(temp)
        for temp in templates:
            descr = temp.GetDescription()
            if  default_document_typename == temp.GetDocumentName():
                current_document_typename = _(descr)
            type_names.append(_(descr))
        return type_names,type_names.index(current_document_typename),templates