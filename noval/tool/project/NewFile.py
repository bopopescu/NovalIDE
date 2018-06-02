import wx
import wx.lib.buttons
from noval.tool.consts import SPACE,HALF_SPACE,_
import os
import noval.util.sysutils as sysutilslib
import xml.etree.ElementTree as ET
import noval.tool.GeneralOption as GeneralOption
from bz2 import BZ2File
import ProjectEditor

COMMON_MASK_COLOR = wx.Colour(255, 0, 255)

def opj(path):
    """Convert paths to the platform-specific separator"""
    st = apply(os.path.join, tuple(path.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        st = '/' + st
    return st


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
        lineSizer.Add(templateLabelText,0,flag=wx.LEFT,border = 4*SPACE)
        
        large_view_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "ViewLarge.ico")
        large_view_image = wx.Image(large_view_image_path,wx.BITMAP_TYPE_ANY)
        
        self._largeviewBtn = wx.lib.buttons.GenBitmapToggleButton(self, -1, wx.BitmapFromImage(large_view_image), size=(16,16))
        lineSizer.Add(self._largeviewBtn,0,flag=wx.LEFT,border = 18*SPACE)
       # self._largeviewBtn.SetBitmapSelected(getLogicalModeOnBitmap())
        self._largeviewBtn.SetToolTipString(_("Listed as Large Icon"))
        self.Bind(wx.EVT_BUTTON, self.OnSelectMode, self._largeviewBtn)
        self._largeviewBtn.SetToggle(True)
        
        small_view_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "ViewSmall.ico")
        small_view_image = wx.Image(small_view_image_path,wx.BITMAP_TYPE_ANY)
        self._smallviewBtn = wx.lib.buttons.GenBitmapToggleButton(self, -1, wx.BitmapFromImage(small_view_image), size=(16,16))
        lineSizer.Add(self._smallviewBtn,0,flag = wx.LEFT|wx.ALIGN_TOP|wx.RIGHT,border = SPACE)
      #  self._smallviewBtn.SetBitmapSelected(getPhysicalModeOnBitmap())
        self._smallviewBtn.SetToolTipString(_("Listed as Samll Icon"))
        
        self.Bind(wx.EVT_BUTTON, self.OnSelectMode, self._smallviewBtn)
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = SPACE)
        
        #self.lc = wx.ListCtrl(self, -1, size=(500,250),style = wx.LC_SMALL_ICON)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.treeCtrl = wx.TreeCtrl(self, -1, style = wx.TR_HAS_BUTTONS | wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT,size=(130,280))
        wx.EVT_TREE_SEL_CHANGED(self.treeCtrl, self.treeCtrl.GetId(), self.OnSelItemChange)
        lineSizer.Add(self.treeCtrl,flag=wx.LEFT|wx.RIGHT,border=SPACE)
        
        self.lc = wx.ListCtrl(self, -1, size=(300,280),style = wx.LC_ICON|wx.BORDER_THEME)
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
        lineSizer.Add(self.ok_btn,0,flag = wx.LEFT,border = SPACE*20)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        lineSizer.Add(cancel_btn,0,flag = wx.LEFT,border=SPACE)

        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.BOTTOM|wx.TOP|wx.RIGHT,border = SPACE)
        
        self.SetSizer(boxsizer)
        self.Fit()
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
        pass
        
    def OnOKClick(self,event):
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
        try:
            with open(self.file_path,"w") as fp:
                with BZ2File(content_zip_path,"r") as f:
                    for i,line in enumerate(f):
                        if i == 0:
                            continue
                        fp.write(line.strip('\0'))
        except Exception as e:
            wx.MessageBox(_("Load Template File Error"),style=wx.ID_OK | wx.ICON_ERROR)
            return
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
        if item is None:
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

        file_template_path = os.path.join(sysutilslib.mainModuleDir, "template.xml")
        tree = ET.parse(file_template_path)
        doc = tree.getroot()
        root_item = self.treeCtrl.AddRoot(_("FileTypes"))
        
        config = wx.ConfigBase_Get()
        langId = GeneralOption.GetLangId(config.Read("Language",""))
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
                    self.treeCtrl.SetPyData(item,file_types)
                    self.treeCtrl.SelectItem(item)