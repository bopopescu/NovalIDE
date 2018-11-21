import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import ProjectEditor
import noval.tool.HtmlEditor as HtmlEditor
import os
import noval.util.strutils as strutils
import noval.util.utils as utils
import noval.util.sysutils as sysutilslib

class PromptMessageDialog(wx.Dialog):
    
    DEFAULT_PROMPT_MESSAGE_ID = wx.ID_YES
    def __init__(self,parent,dlg_id,title,msg):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        #-- icon and message --#
        msgSizer = wx.BoxSizer(wx.HORIZONTAL)
        # icon #
        artID = wx.ART_QUESTION

        bmp = wx.ArtProvider_GetBitmap(artID, wx.ART_MESSAGE_BOX, (48, 48))
        bmpIcon = wx.StaticBitmap(self, -1, bmp)
        msgSizer.Add(bmpIcon, 0, wx.ALIGN_CENTRE | wx.ALL, HALF_SPACE)
        # msg #
        txtMsg = wx.StaticText(self, -1, msg, style=wx.ALIGN_CENTRE)
        msgSizer.Add(txtMsg, 0, wx.ALIGN_CENTRE | wx.ALL, HALF_SPACE)
        sizer.Add(msgSizer, 0, wx.ALIGN_CENTRE, HALF_SPACE)
        line = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALL, HALF_SPACE)
        #-- buttons --#
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        btnYes = wx.Button(self, wx.ID_YES, _('Yes'))
        btnSizer.Add(btnYes, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_YES, self.OnBtnClick)
        
        btnNo = wx.Button(self, wx.ID_NO, _('No'))
        btnSizer.Add(btnNo, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
                    
        wx.EVT_BUTTON(self, wx.ID_YESTOALL, self.OnBtnClick)
                           
        btnYesAll = wx.Button(self, wx.ID_YESTOALL, _('YestoAll'))
        btnSizer.Add(btnYesAll, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_NO, self.OnBtnClick)
        btnNoAll = wx.Button(self, wx.ID_NOTOALL, _('NotoAll'))
        btnSizer.Add(btnNoAll, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_NOTOALL, self.OnBtnClick)


        sizer.Add(btnSizer, 0, wx.ALIGN_CENTRE | wx.TOP|wx.BOTTOM, SPACE)
        #--
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        self.Fit()

    def OnBtnClick(self,event):
        self.EndModal(event.GetId())
        

class FileFilterDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,filters):
        self.filters = filters
        wx.Dialog.__init__(self,parent,dlg_id,title)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        
        boxsizer.Add(wx.StaticText(self, -1, _("Please select file types to to allow added to project:"), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.ALL,border=SPACE)
        
        self.listbox = wx.CheckListBox(self,-1,size=(230,320),choices=[])
        boxsizer.Add(self.listbox,0,flag = wx.EXPAND|wx.BOTTOM|wx.RIGHT,border = SPACE)
        
        boxsizer.Add(wx.StaticText(self, -1, _("Other File Extensions:(seperated by ';')"), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.BOTTOM|wx.RIGHT,border=SPACE)
                        
        self.other_extensions_ctrl = wx.TextCtrl(self, -1, "", size=(-1,-1))
        boxsizer.Add(self.other_extensions_ctrl, 0, flag=wx.BOTTOM|wx.RIGHT|wx.EXPAND,border=SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        self.SetSizer(boxsizer)
        self.Fit()
        self.InitFilters()
        
    def OnOKClick(self,event):
        filters = []
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
               filters.append(self.listbox.GetString(i))
        extension_value = self.other_extensions_ctrl.GetValue().strip()
        if extension_value != "":
            extensions = extension_value.split(";")
            filters.extend(extensions)
        self.filters = [str(fitler.replace("*","").replace(".","")) for fitler in filters]
        self.EndModal(wx.ID_OK)
        
    def InitFilters(self):
        descr = ''
        for temp in wx.GetApp().GetDocumentManager().GetTemplates():
            if temp.IsVisible() and temp.GetDocumentType() != ProjectEditor.ProjectDocument:
                filters = temp.GetFileFilter().split(";")
                for filter in filters:
                    i = self.listbox.Append(filter)
                    if str(filter.replace("*","").replace(".","")) in self.filters:
                        self.listbox.Check(i)

class EditorSelectionDialog(wx.Dialog):
    
    OPEN_WITH_FILE_PATH = 1
    OPEN_WITH_FILE_NAME = 2
    OPEN_WITH_FILE_EXTENSION = 3
    def __init__(self,parent,dlg_id,title,selected_item_file,project_document):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        self._project_file = selected_item_file
        self._file_path = selected_item_file.filePath
        self._open_with_mode = self.OPEN_WITH_FILE_PATH
        self._is_changed = False
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        boxsizer.Add(wx.StaticText(self, -1, _("Choose an editor you want to open") \
                                   + " '%s':" % os.path.basename(self._file_path), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.ALL,border=SPACE)
        self.lc = wx.ListCtrl(self, -1, size=(-1,400),style = wx.LC_LIST)
        wx.EVT_LIST_ITEM_ACTIVATED(self.lc, self.lc.GetId(), self.OnOKClick)
        il = wx.ImageList(16, 16)
        self.templates = self.GetTemplates()
        for temp in self.templates:
            icon = temp.GetIcon()
            iconIndex = il.AddIcon(icon)
        self.lc.AssignImageList(il, wx.IMAGE_LIST_SMALL)
        document_template_name = utils.ProfileGet(project_document.GetFileKey(self._project_file,"Open"),"")
        
        filename = os.path.basename(self._file_path)
        if not document_template_name:
            document_template_name = utils.ProfileGet("Open/filenames/%s" % filename,"")
            if not document_template_name:
                document_template_name = utils.ProfileGet("Open/extensions/%s" % strutils.GetFileExt(filename),"")
                if document_template_name:
                    self._open_with_mode = self.OPEN_WITH_FILE_EXTENSION
            else:
                self._open_with_mode = self.OPEN_WITH_FILE_NAME
                
        self._document_template_name = document_template_name
        
        for i,temp in enumerate(self.templates):
            show_name = temp.GetViewName()
            if 0 == i:
                show_name += (" (" + _("Default") + ")")
            self.lc.InsertImageStringItem( i,show_name ,i)
            if document_template_name == temp.GetDocumentName():
                self.lc.Select(i)
        if document_template_name == "":
            self._document_template_name = self.templates[0].GetDocumentName()
            self.lc.Select(0)
            
        boxsizer.Add(self.lc,1,flag = wx.EXPAND|wx.RIGHT|wx.LEFT,border = SPACE)
        if not sysutilslib.isWindows():
            ##on linux os,the first radiobox will be selected as default within a group radiobox.
            ###so use a hidden radiobox to set as the default selected one
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            self._hiddenRadioBox = wx.RadioButton(self, -1, _("____") + " '%s'" % os.path.basename(self._file_path))
            self._hiddenRadioBox.Show(False)
            lineSizer.Add(self._hiddenRadioBox, 0,flag=wx.LEFT|wx.EXPAND,border=SPACE)
            boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE) 
            
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._applyNameRadioBox = wx.RadioButton(self, -1, _("Use this editor for all files named") + " '%s'" % os.path.basename(self._file_path))
        lineSizer.Add(self._applyNameRadioBox, 0,flag=wx.LEFT|wx.EXPAND,border=SPACE)
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE) 
        
        ext = strutils.GetFileExt(os.path.basename(self._file_path))
        if ext != "":
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            self._applyAllRadioBox = wx.RadioButton(self, -1, _("Use it for all files with extension") + " '.%s'" % ext)
            lineSizer.Add(self._applyAllRadioBox, 0,flag=wx.LEFT|wx.EXPAND,border=SPACE)
            boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP|wx.BOTTOM,border = HALF_SPACE) 
            
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP,SPACE)
        self.SetSizer(boxsizer)
        self.Fit()
        
    def GetTemplates(self):
        templates = []
        default_template = wx.GetApp().GetDocumentManager().FindTemplateForPath(self._file_path)
        for temp in wx.GetApp().GetDocumentManager().GetTemplates():
            want = False
            if temp.IsVisible() and temp.GetViewName() and temp != default_template:
                want = True
            elif not temp.IsVisible() and temp.GetViewType() == HtmlEditor.WebView:
                want = True
            if want:
                templates.append(temp)
        templates.insert(0,default_template)
        return templates
        
    @property
    def OpenwithMode(self):
        return self._open_with_mode

    def GetOpenwithMode(self):
        if self._applyNameRadioBox.GetValue():
            return self.OPEN_WITH_FILE_NAME
        elif hasattr(self,"_applyAllRadioBox") and self._applyAllRadioBox.GetValue():
            return self.OPEN_WITH_FILE_EXTENSION
        return self.OPEN_WITH_FILE_PATH
        
    def OnOKClick(self,event):
        if self.lc.GetFirstSelected() == -1:
            wx.MessageBox(_("Please choose one editor"))
            return
        self.selected_template = self.templates[self.lc.GetFirstSelected()]
        self._is_changed = False if self._open_with_mode == self.GetOpenwithMode() else True
        if not self._is_changed:
            self._is_changed =  False if self._document_template_name == self.selected_template.GetDocumentName() else True
        self._open_with_mode = self.GetOpenwithMode()
        self.EndModal(wx.ID_OK)
 