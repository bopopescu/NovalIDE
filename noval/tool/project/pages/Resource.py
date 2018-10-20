import wx
import os
from noval.tool.consts import SPACE,HALF_SPACE,_
import noval.util.fileutils as fileutils
import noval.tool.images as images
import time
import BasePanel
import noval.util.sysutils as sysutilslib

#set the max width of location label,to avoid too long
MAX_LOCATION_LABEL_WIDTH  = 500

class FileProertyPanel(BasePanel.BasePanel):
    """description of class"""
    
    def __init__(self,filePropertiesService,parent,dlg_id,size,selected_item):
        BasePanel.BasePanel.__init__(self,filePropertiesService, parent, dlg_id,size,selected_item)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        relative_path = ""
        path = ""
        type_name = ""
        project_path = os.path.dirname(self.ProjectDocument.GetFilename())
        is_file = False
        project_view = self.ProjectDocument.GetFirstView()
        if selected_item == project_view._treeCtrl.GetRootItem():
            path = self.ProjectDocument.GetFilename()
            type_name = _("Project")
            relative_path = os.path.basename(path)
        elif project_view._IsItemFile(selected_item):
            path = project_view._GetItemFilePath(selected_item)
            template = wx.GetApp().GetDocumentManager().FindTemplateForPath(path)
            type_name = _("File") + "(%s)" % _(template.GetDescription())
            relative_path = path.replace(project_path,"").lstrip(os.sep)
            is_file = True
        else:
            relative_path = project_view._GetItemFolderPath(selected_item)
            type_name = _("Folder")
            path = os.path.join(project_path,relative_path)
        
        mtime_show_label = wx.StaticText(self, -1, _("Modified:"))
        max_width = mtime_show_label.GetSize().GetWidth()
            
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Path:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
        lineSizer.Add(wx.StaticText(self, -1, fileutils.opj(relative_path)),  1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Type:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
        lineSizer.Add(wx.StaticText(self, -1, type_name),  1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Location:"),size=(max_width,-1)),0,flag=wx.LEFT|wx.ALIGN_CENTER,border=SPACE)
        self.dest_path = fileutils.opj(path)
        self.location_label_ctrl = wx.StaticText(self, -1, self.dest_path)
        location_text_size = self.location_label_ctrl.GetTextExtent(self.dest_path)
        location_text_width = location_text_size[0]
        #the location label width is too long,ellipisis the text
        if location_text_width > MAX_LOCATION_LABEL_WIDTH:
            postend_ellipsis_text = "..."
            show_path = self.dest_path[:len(self.dest_path)*2/3] + postend_ellipsis_text
            limit_text_width = self.location_label_ctrl.GetTextExtent(show_path)[0] + HALF_SPACE
            self.location_label_ctrl.SetInitialSize((limit_text_width,location_text_size[1]),)
            self.location_label_ctrl.SetLabel(show_path)

        lineSizer.Add(self.location_label_ctrl,  0,flag=wx.LEFT|wx.ALIGN_CENTER,border=HALF_SPACE)
        into_btn = wx.BitmapButton(self,-1,images.load("project/into.png"))
        into_btn.SetToolTipString(_("Into file explorer"))
        into_btn.Bind(wx.EVT_BUTTON, self.IntoExplorer)
        lineSizer.Add(into_btn,  0,flag=wx.LEFT,border=SPACE)
        
        copy_btn = wx.BitmapButton(self,-1,images.load("project/copy.png"))
        copy_btn.SetToolTipString(_("Copy path"))
        copy_btn.Bind(wx.EVT_BUTTON, self.CopyPath)
        lineSizer.Add(copy_btn,  0,flag=wx.LEFT,border=HALF_SPACE)
        
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        
        is_path_exist = os.path.exists(path)
        show_label_text = ""
        if not is_path_exist:
            show_label_text = _("resource does not exist") 
        if is_file:
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            lineSizer.Add(wx.StaticText(self, -1, _("Size:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
            if is_path_exist:
                show_label_text = str(os.path.getsize(path))+ _(" Bytes")
            size_label_ctrl = wx.StaticText(self, -1, show_label_text)
            if not is_path_exist:
                size_label_ctrl.SetForegroundColour((255,0,0)) 
            lineSizer.Add(size_label_ctrl,  1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
            box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
            
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Created:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
        if is_path_exist:
            show_label_text = time.ctime(os.path.getctime(path))
        ctime_lable_ctrl = wx.StaticText(self, -1, show_label_text)
        if not is_path_exist:
            ctime_lable_ctrl.SetForegroundColour((255,0,0)) 
        lineSizer.Add(ctime_lable_ctrl,1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)

        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(mtime_show_label,0,flag=wx.LEFT,border=SPACE)
        if is_path_exist:
            show_label_text = time.ctime(os.path.getmtime(path))
        mtime_label_ctrl = wx.StaticText(self, -1,show_label_text)
        if not is_path_exist:
            mtime_label_ctrl.SetForegroundColour((255,0,0)) 
        lineSizer.Add(mtime_label_ctrl,1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Accessed:"),size=(max_width,-1)),0,flag=wx.LEFT,border=SPACE)
        if is_path_exist:
            show_label_text = time.ctime(os.path.getatime(path))
        atime_label_ctrl = wx.StaticText(self, -1,show_label_text)
        if not is_path_exist:
            atime_label_ctrl.SetForegroundColour((255,0,0)) 
        lineSizer.Add(atime_label_ctrl,1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        
        self.SetSizer(box_sizer) 
        #should use Layout ,could not use Fit method
        self.Layout()
        
    def IntoExplorer(self,event):
        location = self.dest_path
        err_code,msg = fileutils.open_file_directory(location)
        if err_code != ERROR_OK:
            wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
            
    def CopyPath(self,event):
        path = self.dest_path
        sysutilslib.CopyToClipboard(path)
        wx.MessageBox(_("Copied to clipboard"))
        
    def OnOK(self,optionsDialog):
        return True
