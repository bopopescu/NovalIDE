import wx
import wx.lib.buttons
from noval.tool.consts import SPACE,HALF_SPACE,_,TEMPLATE_FILE_NAME,USER_CACHE_DIR
import os
import noval.util.sysutils as sysutilslib
import xml.etree.ElementTree as ET
import noval.tool.GeneralOption as GeneralOption
from bz2 import BZ2File
import ProjectEditor
import noval.util.fileutils as fileutils
import noval.tool.ColorFont as ColorFont
from noval.tool.syntax import syntax
import noval.util.appdirs as appdirs
import copy
import uuid
import noval.parser.utils as parserutils
import tarfile
import tempfile

if not sysutilslib.isWindows():
    import noval.tool.FileObserver as FileObserver

COMMON_MASK_COLOR = wx.Colour(255, 0, 255)
    

class FileTemplateDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,file_templates):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=(550,400))
        self._file_templates = copy.deepcopy(file_templates)
        
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.lc = wx.ListCtrl(self, -1, size=(500,200),style = wx.LC_REPORT|wx.BORDER_THEME)
        wx.EVT_LIST_ITEM_SELECTED(self.lc, self.lc.GetId(), self.OnSelectTemplate)
        wx.EVT_LIST_ITEM_DESELECTED(self.lc, self.lc.GetId(), self.OnUnSelectTemplate)
        lineSizer.Add(self.lc,1,flag = wx.EXPAND,border=0)
        
        self.lc.InsertColumn(0, _("Name"))
        self.lc.InsertColumn(1, _("Category"))
        
        self.lc.SetColumnWidth(0, 300)
        self.lc.SetColumnWidth(1,150)
        for i,file_template in enumerate(self._file_templates):
            index = self.lc.InsertStringItem(self.lc.GetItemCount(), file_template.get('Name',''))
            self.lc.SetStringItem(index, 1, file_template.get('Category',''))
            self.lc.SetItemData(index,i)
        
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        app_image_path = appdirs.GetAppImageDirLocation()
        
        add_bmp_path = os.path.join(app_image_path, "template","add.ico")
        add_bmp = wx.BitmapFromImage(wx.Image(add_bmp_path,wx.BITMAP_TYPE_ANY))
        self.new_btn = wx.Button(self,-1, _("New"))
        wx.EVT_BUTTON(self.new_btn, -1, self.NewItem)
        self.new_btn.SetBitmap(add_bmp,wx.LEFT)
        lineSizer.Add(self.new_btn, 0,flag=wx.LEFT, border=SPACE)
        
        delete_bmp_path = os.path.join(app_image_path, "template","delete.ico")
        delete_bmp = wx.BitmapFromImage(wx.Image(delete_bmp_path,wx.BITMAP_TYPE_ANY))
        self.delete_btn = wx.Button(self,-1, _("Delete"))
        wx.EVT_BUTTON(self.delete_btn, -1, self.DeleteItem)
        self.delete_btn.SetBitmap(delete_bmp,wx.LEFT)
        lineSizer.Add(self.delete_btn, 0,flag=wx.LEFT, border=SPACE)
        
        up_bmp_path = os.path.join(app_image_path, "template","up.ico")
        up_bmp = wx.BitmapFromImage(wx.Image(up_bmp_path,wx.BITMAP_TYPE_ANY))
        self.up_btn = wx.Button(self,-1, _("Up"))
        wx.EVT_BUTTON(self.up_btn, -1, self.UpItem)
        self.up_btn.SetBitmap(up_bmp,wx.LEFT)
        lineSizer.Add(self.up_btn, 0,flag=wx.LEFT, border=SPACE)
        
        down_bmp_path = os.path.join(app_image_path, "template","down.ico")
        down_bmp = wx.BitmapFromImage(wx.Image(down_bmp_path,wx.BITMAP_TYPE_ANY))
        self.down_btn = wx.Button(self,-1, _("Down"))
        wx.EVT_BUTTON(self.down_btn, -1, self.DownItem)
        self.down_btn.SetBitmap(down_bmp,wx.LEFT)
        lineSizer.Add(self.down_btn, 0,flag=wx.LEFT, border=SPACE)
        
        refresh_bmp_path = os.path.join(app_image_path, "template","refresh.ico")
        refresh_bmp = wx.BitmapFromImage(wx.Image(refresh_bmp_path,wx.BITMAP_TYPE_ANY))
        self.refresh_btn = wx.Button(self,-1, _("Refresh"))
        wx.EVT_BUTTON(self.refresh_btn, -1, self.RefreshItem)
        self.refresh_btn.SetBitmap(refresh_bmp,wx.LEFT)
        lineSizer.Add(self.refresh_btn, 0,flag=wx.LEFT, border=SPACE)
        
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT,border = SPACE)
        
        sbox = wx.StaticBox(self, -1, _("Template Property"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Name:")), 0,wx.ALIGN_CENTER | wx.LEFT, SPACE)
        self.name_ctrl = wx.TextCtrl(self, -1, "",size=(200,-1))
        lineSizer.Add(self.name_ctrl, 1, wx.LEFT|wx.EXPAND, 0)
        left_sizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP, border=0)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Default Extension:")), 0,wx.ALIGN_CENTER | wx.LEFT, SPACE)
        self.ext_ctrl = wx.TextCtrl(self, -1, "",size=(-1,-1))
        lineSizer.Add(self.ext_ctrl, 1, wx.LEFT|wx.EXPAND, 0)
        left_sizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP, border=HALF_SPACE)
        
        topSizer.Add(left_sizer,0,flag=wx.ALL,border = 0)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Category:")), 0,wx.ALIGN_CENTER | wx.LEFT, 3*SPACE)
        self.category_ctrl = wx.TextCtrl(self, -1, "",size=(200,-1))
        lineSizer.Add(self.category_ctrl, 1, wx.LEFT|wx.EXPAND, 0)
        right_sizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP, border=0)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Syntax Highlight:")), 0,wx.ALIGN_CENTER | wx.LEFT, SPACE)
        self._syntaxCombo = wx.ComboBox(self, -1,choices =  syntax.LexerManager().GetShowNameList(), style = wx.CB_DROPDOWN)
        lineSizer.Add(self._syntaxCombo, 1, wx.LEFT|wx.EXPAND, 0)
        right_sizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP, border=HALF_SPACE)
        
        topSizer.Add(right_sizer,1,flag=wx.EXPAND|wx.RIGHT,border = SPACE)
        
        sboxSizer.Add(topSizer,0,flag=wx.EXPAND|wx.TOP, border=HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Template Content:")), 1,wx.ALIGN_CENTER | wx.LEFT, SPACE)
        sboxSizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP, border=HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.template_code_ctrl = ColorFont.CodeSampleCtrl(self,-1,size=(500,200))
        self.template_code_ctrl.HideLineNumber()
        lineSizer.Add(self.template_code_ctrl, 1, flag =wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,border=SPACE)
        sboxSizer.Add(lineSizer,0,flag=wx.EXPAND|wx.TOP, border=HALF_SPACE)
        
        boxsizer.Add(sboxSizer,0,flag = wx.EXPAND|wx.ALL,border = SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        ok_btn.SetDefault()
        wx.EVT_BUTTON(ok_btn, wx.ID_OK, self.OnOK)
        bsizer.AddButton(ok_btn)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        
        self.SetSizer(boxsizer)
        self.Fit()
        self.UpdateUI()
        
    def UpdateUI(self):
        select_item = self.lc.GetFirstSelected()
        if select_item == -1:
            self.delete_btn.Enable(False)
            self.down_btn.Enable(False)
            self.up_btn.Enable(False)
            self.refresh_btn.Enable(False)
        else:
            self.delete_btn.Enable(True)
            if 0 == select_item:
                self.up_btn.Enable(False)
            else:
                self.up_btn.Enable(True)
            if self.lc.GetItemCount() - 1 == select_item:
                self.down_btn.Enable(False)
            else:
                self.down_btn.Enable(True)
            self.refresh_btn.Enable(True)
        
    def NewItem(self,event):
        name = self.name_ctrl.GetValue().strip()
        if name == "":
            wx.MessageBox(_("template name is empty"))
            return
        if self.IsTemplateNameExist(name):
            wx.MessageBox(_("template name '%s' already exist") % name)
            return
        category = self.category_ctrl.GetValue().strip()
        if category == "":
            wx.MessageBox(_("category is empty"))
            return
        ext = self.ext_ctrl.GetValue()
        if not ext.startswith("."):
            ext = "." + ext
        syntax_value = self._syntaxCombo.GetValue()
        code_sample_text = self.template_code_ctrl.GetText()
        try:
            user_template_path = os.path.join(appdirs.getAppDataFolder(),USER_CACHE_DIR,"template")
            parserutils.MakeDirs(user_template_path)
            template_file_path = os.path.join(user_template_path,str(uuid.uuid1()) + ".tar.bz2")
            archive = tarfile.open(template_file_path,'w:bz2')
            fd, newfname = tempfile.mkstemp(suffix=ext, text=True)
            with open(newfname, 'w') as f:
                f.write(code_sample_text)
            archive.add(newfname,arcname=os.path.basename(newfname))  # d:\myfiles contains the files to compress
            archive.close()
            template = {
                'Ext': ext,
                'Name': name,
                'Category': category,
                'Content': template_file_path.replace(appdirs.getAppDataFolder(),"").strip().lstrip(os.sep),
                'DefaultName': 'Untitle' + ext
            }
            self._file_templates.append(template)
        except IOError:
            print 'please use an administrator account'
            return
            
        pre_selection = self.lc.GetFirstSelected()
        #deselect the previous selection
        if pre_selection != -1:
            self.lc.SetItemState(pre_selection, 0, wx.LIST_STATE_SELECTED)

        i = self.lc.Append([name,category])
        self.lc.SetItemData(i,len(self._file_templates) -1)
        self.lc.Select(i)
        self.lc.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self.lc.EnsureVisible(i)
        self.UpdateUI()
            
    def OnOK(self,event):
        
        def CreateDataElement(parent,name,data):
            data_el = ET.SubElement(parent, name)
            data_el.text = data.get(name)
            
        def CreateIconDataElement(parent,name,data):
            data_el = ET.SubElement(parent, name)
            data_el.text = data.get(name)
            data_el.attrib['Large'] = data.get('LargeIconPath',"noval/tool/bmp_source/template/default.bmp")
            data_el.attrib['Small'] = data.get('SmallIconPath',"noval/tool/bmp_source/template/default-small.bmp")
            
        
        root = ET.Element('FileType')
        langId = GeneralOption.GetLangId(wx.ConfigBase_Get().Read("Language",sysutilslib.GetLangConfig()))
        lang_el = ET.SubElement(root, wx.Locale.GetLanguageInfo(langId).CanonicalName)
        for template in self._file_templates:
            template_el = ET.SubElement(lang_el, 'TemplateData')
            template_el.attrib['value'] = template.get('Category')
            data_el = ET.SubElement(template_el, 'Template')
            CreateDataElement(data_el,'Ext',template)
            CreateDataElement(data_el,'Name',template)
            CreateDataElement(data_el,'Content',template)
            CreateDataElement(data_el,'DefaultName',template)
            CreateIconDataElement(data_el,'Icon',template)
        tree = ET.ElementTree(root)
        user_template_path = os.path.join(appdirs.getAppDataFolder(),USER_CACHE_DIR,TEMPLATE_FILE_NAME)
        tree.write(user_template_path, encoding='utf-8')
        self.EndModal(wx.ID_OK)
        
    def IsTemplateNameExist(self,name):
        for file_template in self._file_templates:
            template_name = file_template.get('Name','')
            if template_name.lower() == name.lower():
                return True
        return False
        
    def DeleteItem(self,event):
        select_item = self.lc.GetFirstSelected()
        self.lc.DeleteItem(select_item)
        self._file_templates.remove(self._file_templates[select_item])
        self.UpdateUI()
        
    def UpItem(self,event):
        select_item = self.lc.GetFirstSelected()
        index = self.lc.GetItemData(select_item)
        tmp_template = self._file_templates[index]
        self._file_templates[index] = self._file_templates[index - 1]
        self._file_templates[index - 1] = tmp_template
        self.lc.DeleteItem(select_item)
        
        i = self.lc.InsertStringItem(index-1, tmp_template.get('Name',''))
        self.lc.SetStringItem(i, 1, tmp_template.get('Category',''))
        self.lc.SetItemData(i,index-1)
        self.lc.SetItemData(i+1,index)
        self.lc.Select(i)
        self.lc.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self.lc.EnsureVisible(i)
        self.UpdateUI()
        
    def DownItem(self,event):
        select_item = self.lc.GetFirstSelected()
        index = self.lc.GetItemData(select_item)
        tmp_template = self._file_templates[index]
        self._file_templates[index] = self._file_templates[index + 1]
        self._file_templates[index + 1] = tmp_template
        
        self.lc.DeleteItem(select_item)
        
        i = self.lc.InsertStringItem(index + 1, tmp_template.get('Name',''))
        self.lc.SetStringItem(i, 1, tmp_template.get('Category',''))
        self.lc.SetItemData(i,index+1)
        self.lc.SetItemData(i-1,index)
        self.lc.Select(i)
        self.lc.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self.lc.EnsureVisible(i)
        self.UpdateUI()
        
    def RefreshItem(self,event):
        self.OnSelectTemplate(event)
        
    def OnUnSelectTemplate(self,event):
        self.UpdateUI()
        
    def OnSelectTemplate(self,event):
        select_item = self.lc.GetFirstSelected()
        index = self.lc.GetItemData(select_item)
        template = self._file_templates[index]
        self.name_ctrl.SetValue(template.get('Name',''))
        self.category_ctrl.SetValue(template.get('Category',''))
        ext = template.get('Ext','')
        self.ext_ctrl.SetValue(ext)
        lexer = syntax.LexerManager().GetLexer(syntax.LexerManager().GetLangIdFromExt(ext))
        self._syntaxCombo.SetValue(lexer.GetShowName())
        content = template['Content'].strip()
        content_zip_path = fileutils.opj(os.path.join(sysutilslib.mainModuleDir,content))
        if not os.path.exists(content_zip_path):
            content_zip_path = fileutils.opj(os.path.join(appdirs.getAppDataFolder(),content))
        self.template_code_ctrl.SetText("")
        self.UpdateUI()
        try:
            with BZ2File(content_zip_path,"r") as f:
                for i,line in enumerate(f):
                    if i == 0:
                        continue
                    self.template_code_ctrl.AddText(line.strip('\0').strip('\r').strip('\n'))
                    self.template_code_ctrl.AddText('\n')
        except Exception as e:
            wx.MessageBox(_("Load File Template Content Error.%s") % e,style=wx.OK | wx.ICON_ERROR)
            return
            
        self.template_code_ctrl.SetLangLexer(lexer)


class NewFileDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,folderPath):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=(300,400))
        projectService = wx.GetApp().GetService(ProjectEditor.ProjectService)
        self.project_view = projectService.GetView()
        project_path = os.path.dirname(self.project_view.GetDocument().GetFilename())
        self.dest_path = project_path
        if folderPath != "":
            self.dest_path = os.path.join(self.dest_path,folderPath)
        if sysutilslib.isWindows():
            self.dest_path = self.dest_path.replace("/",os.sep)
            
        self.file_path = None
        
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        typeLabelText = wx.StaticText(self, -1, _('Type:'),size=(100,-1))
        lineSizer.Add(typeLabelText,0,flag=wx.LEFT,border = SPACE)
        templateLabelText = wx.StaticText(self, -1, _('Template:'),size=(100,-1))
        lineSizer.Add(templateLabelText,1,flag=wx.LEFT|wx.EXPAND,border = 4*SPACE)
        
        app_image_path = appdirs.GetAppImageDirLocation()
        
        large_view_image_path = os.path.join(app_image_path, "ViewLarge.ico")
        large_view_image = wx.Image(large_view_image_path,wx.BITMAP_TYPE_ANY)
        
        self._largeviewBtn = wx.lib.buttons.GenBitmapToggleButton(self, -1, wx.BitmapFromImage(large_view_image), size=(16,16))
        lineSizer.Add(self._largeviewBtn,0,flag=wx.RIGHT,border = HALF_SPACE)
        self._largeviewBtn.SetToolTipString(_("Listed as Large Icon"))
        self.Bind(wx.EVT_BUTTON, self.OnSelectMode, self._largeviewBtn)
        self._largeviewBtn.SetToggle(True)
        
        small_view_image_path = os.path.join(app_image_path, "ViewSmall.ico")
        small_view_image = wx.Image(small_view_image_path,wx.BITMAP_TYPE_ANY)
        self._smallviewBtn = wx.lib.buttons.GenBitmapToggleButton(self, -1, wx.BitmapFromImage(small_view_image), size=(16,16))
        lineSizer.Add(self._smallviewBtn,0,flag = wx.LEFT|wx.ALIGN_TOP|wx.RIGHT,border = SPACE)
        self._smallviewBtn.SetToolTipString(_("Listed as Samll Icon"))
        
        self.Bind(wx.EVT_BUTTON, self.OnSelectMode, self._smallviewBtn)
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.TOP,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.treeCtrl = wx.TreeCtrl(self, -1, style = wx.TR_HAS_BUTTONS | wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT,size=(130,280))
        wx.EVT_TREE_SEL_CHANGED(self.treeCtrl, self.treeCtrl.GetId(), self.OnSelItemChange)
        lineSizer.Add(self.treeCtrl,flag=wx.LEFT|wx.RIGHT,border=SPACE)
        
        self.lc = wx.ListCtrl(self, -1, size=(300,280),style = wx.LC_ICON|wx.BORDER_THEME)
        wx.EVT_LIST_ITEM_ACTIVATED(self.lc, self.lc.GetId(), self.OnOKClick)
        lineSizer.Add(self.lc,1,flag=wx.TOP|wx.EXPAND,border=0)

        self.small_iconList = wx.ImageList(16, 16)
        self.lc.AssignImageList(self.small_iconList, wx.IMAGE_LIST_SMALL)
        
        self.large_iconList = wx.ImageList(32, 32)
        self.lc.AssignImageList(self.large_iconList, wx.IMAGE_LIST_NORMAL)
        
        self.current_style = wx.LC_ICON
        
        self.SelectViewStyle(self.current_style )
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.BOTTOM|wx.TOP|wx.RIGHT,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        edit_btn = wx.Button(self, -1, _("&Edit"))
        wx.EVT_BUTTON(edit_btn, -1, self.OnEditTemplate)
        lineSizer.Add(edit_btn,0,flag = wx.LEFT,border = SPACE)
        
        self.ok_btn = wx.Button(self, wx.ID_OK, _("&Create"))
        wx.EVT_BUTTON(self.ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        self.ok_btn.SetDefault()
        lineSizer.Add(self.ok_btn,0,flag = wx.LEFT,border = SPACE*35)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        lineSizer.Add(cancel_btn,0,flag = wx.LEFT,border=SPACE)

        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.BOTTOM|wx.TOP|wx.RIGHT,border = SPACE)
        
        self.SetSizer(boxsizer)
        self.Fit()
        self.file_templates = []
        self.LoadFileTemplates()
        
    def OnSelectMode(self,event):
        btn = event.GetEventObject()
        down = event.GetIsDown()
        if btn == self._largeviewBtn:
            self._smallviewBtn.SetToggle(not down)
        else:
            self._largeviewBtn.SetToggle(not down)
            
        if not self._smallviewBtn.up:
            self.SelectViewStyle(wx.LC_SMALL_ICON)
        else:
            self.SelectViewStyle(wx.LC_ICON)
        
    def OnEditTemplate(self,event):
        dlg = FileTemplateDialog(self,-1,_("File Template"),self.file_templates)
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.file_templates = dlg._file_templates
            self.ReLoadFileTemplates()
        
    def OnOKClick(self,event):
        
        def startPathWatcher():
            if path_watcher is not None:
                path_watcher.Start()
            
        item = self.treeCtrl.GetSelection()
        select_item = self.lc.GetFirstSelected()
        if item is None or select_item == -1:
            wx.MessageBox(_("You don't select any item"))
            return
        templates = self.treeCtrl.GetPyData(item)
        index = self.lc.GetItemData(select_item)
        data = templates[index]
        default_name = data.get('DefaultName')
        if default_name is None:
            default_name = "Untitle" + data.get('Ext')
        content = data['Content'].strip()
        content_zip_path = fileutils.opj(os.path.join(sysutilslib.mainModuleDir,content))
        if not os.path.exists(content_zip_path):
            content_zip_path = fileutils.opj(os.path.join(appdirs.getAppDataFolder(),content))
        name,ext = os.path.splitext(default_name)
        i = 1
        while True:
            file_name = "%s%d%s" % (name,i,ext)
            self.file_path = os.path.join(self.dest_path,file_name)
            if not os.path.exists(self.file_path):
                break
            i += 1
        #when new file template on linux ,should stop path wather of the file teplate path
        #after create file success,then restart path watcher
        #otherwise it will alarm a modify event after the file been created
        if not sysutilslib.isWindows():
            path_watcher = None
            dir_path = os.path.dirname(self.file_path)
            if FileObserver.FileAlarmWatcher.path_watchers.has_key(dir_path):
                path_watcher = FileObserver.FileAlarmWatcher.path_watchers[dir_path]
                path_watcher.Stop()
        try:
            with open(self.file_path,"w") as fp:
                try:
                    with BZ2File(content_zip_path,"r") as f:
                        for i,line in enumerate(f):
                            if i == 0:
                                continue
                            fp.write(line.strip('\0').strip('\r').strip('\n'))
                            fp.write('\n')
                except Exception as e:
                    wx.MessageBox(_("Load File Template Content Error.%s") % e,style=wx.OK | wx.ICON_ERROR)
                    return
        except Exception as e:
            if not sysutilslib.isWindows():
                startPathWatcher()
            wx.MessageBox(_("New File Error.%s") % e,style=wx.OK | wx.ICON_ERROR)
            return
        if not sysutilslib.isWindows():
            startPathWatcher()
        self.EndModal(wx.ID_OK)
        
    def SelectViewStyle(self,style):
        if style == self.current_style:
            return
        self.lc.Freeze()
        self.LoadFileTemplate()
        self.lc.SetWindowStyleFlag(style)
        self.lc.Thaw()
        self.current_style = style
        
    def LoadFileTemplate(self):
        self.lc.DeleteAllItems()
        item = self.treeCtrl.GetSelection()
        if item is None or 0 == self.treeCtrl.GetCount():
            return
        templates = self.treeCtrl.GetPyData(item)
        for i,template in enumerate(templates):
            j = self.lc.InsertImageStringItem(i,template.get('Name',""),template.get('ImageIndex',-1))
            self.lc.SetItemData(i,i)
            
    def OnSelItemChange(self,event):
        self.LoadFileTemplate()
        
    def GetFileTypeTemplate(self,node):
        file_type = {}
        for item in node.getchildren():
            if item.tag == "Icon":
                try:
                    small_path = item.get('Small',"")
                    if os.path.isabs(small_path):
                        small_icon_path = small_path
                    else:
                        small_icon_path = os.path.join(sysutilslib.mainModuleDir,small_path)
                    file_type['SmallIconPath'] = small_icon_path
                    if not os.path.exists(small_icon_path):
                        small_icon_path = os.path.join(sysutilslib.mainModuleDir,"noval/tool/bmp_source/template/default-small.bmp")
                    small_icon = wx.Image(small_icon_path, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
                    index = self.small_iconList.AddWithColourMask(small_icon,COMMON_MASK_COLOR)
                    large_path = item.get('Large',"")
                    if os.path.isabs(large_path):
                        large_icon_path = large_path
                    else:
                        large_icon_path = os.path.join(sysutilslib.mainModuleDir,large_path)
                    file_type['LargeIconPath'] = large_icon_path
                    if not os.path.exists(large_icon_path):
                        large_icon_path = os.path.join(sysutilslib.mainModuleDir,"noval/tool/bmp_source/template/default.bmp")
                    large_icon = wx.Image(large_icon_path, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
                    index = self.large_iconList.AddWithColourMask(large_icon,COMMON_MASK_COLOR)
                    file_type['ImageIndex'] = index
                except Exception as e:
                    print e
                    continue
            else:
                file_type[item.tag] = item.text
        return file_type
        
    def LoadFileTypes(self):
        try:
            user_template_path = os.path.join(appdirs.getAppDataFolder(),USER_CACHE_DIR,TEMPLATE_FILE_NAME)
            sys_template_path = os.path.join(appdirs.GetAppLocation(), TEMPLATE_FILE_NAME)
            if os.path.exists(user_template_path):
                file_template_path = user_template_path
            elif os.path.exists(sys_template_path):
                file_template_path = sys_template_path
            tree = ET.parse(file_template_path)
            doc = tree.getroot()
            root_item = self.treeCtrl.AddRoot(_("FileTypes"))
        except Exception as e:
            wx.MessageBox(_("Load Template File Error.%s") % e,style=wx.OK | wx.ICON_ERROR)
            return
        
        config = wx.ConfigBase_Get()
        langId = GeneralOption.GetLangId(config.Read("Language",sysutilslib.GetLangConfig()))
        lang = wx.Locale.GetLanguageInfo(langId).CanonicalName
        items = {}
        for element in doc.getchildren():
            if element.tag == lang:
                for node in element.getchildren():
                    value_type = node.get('value')
                    if not items.has_key(value_type):
                        item = self.treeCtrl.AppendItem(root_item,value_type)
                        items[value_type] = item
                        file_types = []
                    else:
                        item = items[value_type]
                        file_types = self.treeCtrl.GetPyData(item)
                    for child in node.getchildren():
                        file_type = self.GetFileTypeTemplate(child)
                        file_types.append(file_type)
                        file_type.update({
                            'Category':value_type
                        })
                        self.file_templates.append(file_type)
                    self.treeCtrl.SetPyData(item,file_types)
                    self.treeCtrl.SelectItem(item)
                    
    def LoadFileTemplates(self):
        self.LoadFileTypes()
        self.LoadFileTemplate()
        
    def ReLoadFileTemplates(self):
        self.file_templates = []
        self.treeCtrl.Freeze()
        self.treeCtrl.DeleteAllItems()
        self.LoadFileTypes()
        self.LoadFileTemplate()
        self.treeCtrl.Thaw()