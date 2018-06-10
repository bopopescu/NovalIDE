import wx
import wx.lib.buttons
from noval.tool.consts import SPACE,HALF_SPACE,_
import os
import noval.util.sysutils as sysutilslib
import xml.etree.ElementTree as ET
import noval.tool.GeneralOption as GeneralOption
from bz2 import BZ2File
import ProjectEditor
if not sysutilslib.isWindows():
    import noval.tool.FileObserver as FileObserver

COMMON_MASK_COLOR = wx.Colour(255, 0, 255)

def opj(path):
    """Convert paths to the platform-specific separator"""
    st = apply(os.path.join, tuple(path.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        st = '/' + st
    return st
    

class FileTemplateDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,file_templates):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=(550,400))
        self._file_templates = file_templates
        
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.lc = wx.ListCtrl(self, -1, size=(500,200),style = wx.LC_REPORT|wx.BORDER_THEME)
        lineSizer.Add(self.lc,1,flag = wx.EXPAND,border=0)
        
        self.lc.InsertColumn(0, _("Name"))
        self.lc.InsertColumn(1, _("Category"))
        
        self.lc.SetColumnWidth(0, 300)
        self.lc.SetColumnWidth(1,150)
        for file_template in self._file_templates:
            index = self.lc.InsertStringItem(self.lc.GetItemCount(), file_template.get('Name','')); 
            self.lc.SetStringItem(index, 1, file_template.get('Category',''))
        
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.ALL,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        add_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "template","add.ico")
        add_bmp = wx.BitmapFromImage(wx.Image(add_bmp_path,wx.BITMAP_TYPE_ANY))
        self.new_btn = wx.Button(self,-1, _("New"))
        self.new_btn.SetBitmap(add_bmp,wx.LEFT)
        lineSizer.Add(self.new_btn, 0,flag=wx.LEFT, border=SPACE)
        
        delete_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "template","delete.ico")
        delete_bmp = wx.BitmapFromImage(wx.Image(delete_bmp_path,wx.BITMAP_TYPE_ANY))
        self.delete_btn = wx.Button(self,-1, _("Delete"))
        self.delete_btn.SetBitmap(delete_bmp,wx.LEFT)
        lineSizer.Add(self.delete_btn, 0,flag=wx.LEFT, border=SPACE)
        
        up_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "template","up.ico")
        up_bmp = wx.BitmapFromImage(wx.Image(up_bmp_path,wx.BITMAP_TYPE_ANY))
        self.up_btn = wx.Button(self,-1, _("Up"))
        self.up_btn.SetBitmap(up_bmp,wx.LEFT)
        lineSizer.Add(self.up_btn, 0,flag=wx.LEFT, border=SPACE)
        
        down_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "template","down.ico")
        down_bmp = wx.BitmapFromImage(wx.Image(down_bmp_path,wx.BITMAP_TYPE_ANY))
        self.down_btn = wx.Button(self,-1, _("Down"))
        self.down_btn.SetBitmap(down_bmp,wx.LEFT)
        lineSizer.Add(self.down_btn, 0,flag=wx.LEFT, border=SPACE)
        
        refresh_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "template","refresh.ico")
        refresh_bmp = wx.BitmapFromImage(wx.Image(refresh_bmp_path,wx.BITMAP_TYPE_ANY))
        self.refresh_btn = wx.Button(self,-1, _("Refresh"))
        self.refresh_btn.SetBitmap(refresh_bmp,wx.LEFT)
        lineSizer.Add(self.refresh_btn, 0,flag=wx.LEFT, border=SPACE)
        
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.ALL,border = SPACE)
        
        sbox = wx.StaticBox(self, -1, _("Template Property"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Name")), 0,wx.ALIGN_CENTER | wx.LEFT, SPACE)
        self.name_ctrl = wx.TextCtrl(self, -1, "",size=(-1,-1))
        lineSizer.Add(self.name_ctrl, 1, wx.LEFT|wx.EXPAND, SPACE)
        
        lineSizer.Add(wx.StaticText(self, -1, _("Category")), 0,wx.ALIGN_CENTER | wx.LEFT, SPACE)
        self.category_ctrl = wx.TextCtrl(self, -1, "",size=(-1,-1))
        lineSizer.Add(self.category_ctrl, 1, wx.LEFT|wx.EXPAND, SPACE)
        
        sboxSizer.Add(lineSizer,flag=wx.LEFT|wx.TOP, border=SPACE)
        
        boxsizer.Add(sboxSizer,0,flag = wx.EXPAND|wx.ALL,border = SPACE)
        
        self.SetSizer(boxsizer)
        self.Fit()


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
        
        large_view_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "ViewLarge.ico")
        large_view_image = wx.Image(large_view_image_path,wx.BITMAP_TYPE_ANY)
        
        self._largeviewBtn = wx.lib.buttons.GenBitmapToggleButton(self, -1, wx.BitmapFromImage(large_view_image), size=(16,16))
        lineSizer.Add(self._largeviewBtn,0,flag=wx.RIGHT,border = HALF_SPACE)
        self._largeviewBtn.SetToolTipString(_("Listed as Large Icon"))
        self.Bind(wx.EVT_BUTTON, self.OnSelectMode, self._largeviewBtn)
        self._largeviewBtn.SetToggle(True)
        
        small_view_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "ViewSmall.ico")
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
##        edit_btn = wx.Button(self, -1, _("&Edit"))
##        wx.EVT_BUTTON(edit_btn, -1, self.OnEditTemplate)
##        lineSizer.Add(edit_btn,0,flag = wx.LEFT,border = SPACE)
        
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
        self.LoadFileTypes()
        self.LoadFileTemplate()
        
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
        dlg.ShowModal()
        
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
        default_name = data['DefaultName']
        content = data['Content'].strip()
        content_zip_path = opj(os.path.join(sysutilslib.mainModuleDir,content))
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
            try:
                if item.tag == "Icon":
                    small_icon_path = os.path.join(sysutilslib.mainModuleDir,item.get('Small',""))
                    if not os.path.exists(small_icon_path):
                        continue
                    small_icon = wx.Image(small_icon_path, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
                    index = self.small_iconList.AddWithColourMask(small_icon,COMMON_MASK_COLOR)
                    large_icon_path = os.path.join(sysutilslib.mainModuleDir,item.get('Large',""))
                    if not os.path.exists(large_icon_path):
                        continue
                    large_icon = wx.Image(large_icon_path, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
                    index = self.large_iconList.AddWithColourMask(large_icon,COMMON_MASK_COLOR)
                    file_type['ImageIndex'] = index
                else:
                    file_type[item.tag] = item.text
            except Exception as e:
                continue
        return file_type
        
    def LoadFileTypes(self):
        try:
            file_template_path = os.path.join(sysutilslib.mainModuleDir, "template.xml")
            tree = ET.parse(file_template_path)
            doc = tree.getroot()
            root_item = self.treeCtrl.AddRoot(_("FileTypes"))
        except Exception as e:
            wx.MessageBox(_("Load Template File Error.%s") % e,style=wx.OK | wx.ICON_ERROR)
            return
        
        config = wx.ConfigBase_Get()
        langId = GeneralOption.GetLangId(config.Read("Language",sysutilslib.GetLangConfig()))
        lang = wx.Locale.GetLanguageInfo(langId).CanonicalName
        for element in doc.getchildren():
            if element.tag == lang:
                for node in element.getchildren():
                    value_type = node.get('value')
                    item = self.treeCtrl.AppendItem(root_item,value_type)
                    file_types = []
                    for child in node.getchildren():
                        file_type = self.GetFileTypeTemplate(child)
                        file_types.append(file_type)
                        file_type.update({
                            'Category':value_type
                        })
                        self.file_templates.append(file_type)
                    self.treeCtrl.SetPyData(item,file_types)
                    self.treeCtrl.SelectItem(item)