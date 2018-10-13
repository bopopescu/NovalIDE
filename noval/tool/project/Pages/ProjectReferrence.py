import wx
from noval.tool.consts import SPACE,HALF_SPACE,_
import noval.tool.project as project
import BasePanel
import noval.util.utils as utils

class ProjectReferrencePanel(BasePanel.BasePanel):
    def __init__(self,filePropertiesService,parent,dlg_id,size,selected_item):
        BasePanel.BasePanel.__init__(self,filePropertiesService, parent, dlg_id,size,selected_item)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        project_StaticText = wx.StaticText(self, -1, _("Project may refer to other projects.The reference project path will append to the PYTHONPATH of current project.\n"))
        boxsizer.Add(project_StaticText,0,flag=wx.LEFT|wx.TOP,border=SPACE)
                        
        boxsizer.Add(wx.StaticText(self, -1, _("The reference projects for '%s':") % self.GetProjectName(), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.LEFT|wx.TOP,border=SPACE)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.listbox = wx.CheckListBox(self,-1,size=(-1,300),choices=[])
        lineSizer.Add(self.listbox,1,flag = wx.EXPAND|wx.LEFT,border = SPACE)
        
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.select_all_btn = wx.Button(self, -1, _("Select All"))
        wx.EVT_BUTTON(self.select_all_btn, -1, self.SelectAll)
        rightSizer.Add(self.select_all_btn, 0,flag=wx.TOP, border=0)
        
        self.unselect_all_btn = wx.Button(self, -1, _("UnSelect All"))
        wx.EVT_BUTTON(self.unselect_all_btn, -1, self.UnSelectAll)
        rightSizer.Add(self.unselect_all_btn, 0,flag=wx.TOP, border=SPACE)
        
        lineSizer.Add(rightSizer,0,flag = wx.EXPAND|wx.LEFT,border = HALF_SPACE)
        
        boxsizer.Add(lineSizer,1,flag = wx.TOP|wx.EXPAND,border = SPACE)
        self.SetSizer(boxsizer)
        #should use Layout ,could not use Fit method
        self.Layout()
        self.LoadProjects()
        
    def OnOK(self,optionsDialog):
        ref_projects = self.GetReferenceProjects()
        ref_project_names = [ref_project.GetModel().Name for ref_project in ref_projects]
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/ReferenceProjects",ref_project_names.__repr__())
        return True
        
    def SelectAll(self,event):
        for i in range(self.listbox.GetCount()):
            if not self.listbox.IsChecked(i):
                self.listbox.Check(i,True)
        
    def UnSelectAll(self,event):
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                self.listbox.Check(i,False)
        
    def LoadProjects(self):
        str_project_names = utils.ProfileGet(self.ProjectDocument.GetKey() + "/ReferenceProjects","")
        try:
            ref_project_names = eval(str_project_names)
        except:
            ref_project_names = []
        projectService = wx.GetApp().GetService(project.ProjectEditor.ProjectService)
        current_project_document = projectService.GetCurrentProject()
        for document in projectService.GetView().Documents:
            if document == current_project_document:
                continue
            project_name = document.GetModel().Name
            i = self.listbox.Append(project_name,document)
            if project_name in ref_project_names:
                self.listbox.Check(i,True)
            
    def GetReferenceProjects(self):
        projects = []
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                projects.append(self.listbox.GetClientData(i))
        return projects