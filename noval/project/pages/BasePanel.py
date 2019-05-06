import wx
import os

class BasePanel(wx.Panel):
    """description of class"""
    
    def __init__(self,filePropertiesService,parent,dlg_id,size,selected_item):
        wx.Panel.__init__(self, parent, dlg_id,size=size)
        self.current_project_document = filePropertiesService._current_project_document
        
    @property
    def ProjectDocument(self):
        return self.current_project_document
        
    def GetProjectName(self):
        return self.current_project_document.GetModel().Name
        
    def GetProjectFilename(self,proj_file):
        return os.path.basename(proj_file.filePath)