import wx
import wx.dataview as dataview
import os
import noval.tool.consts as consts
import re
from noval.util.exceptions import PromptErrorException
import sys
from noval.util import utils

PROJECT_NAME_VARIABLE = "ProjectName"
PROJECT_PATH_VARIABLE = "ProjectPath"
PROJECT_DIR_VARIABLE = "ProjectDir"
PROJECT_FILENAME_VARIABLE = "ProjectFileName"
PROJECT_GUID_VARIABLE = "ProjectGuid"
PROJECT_EXT_VARIABLE = "ProjectExtension"

def FormatVariableName(name):
    return "${%s}" % name
        
class ProjectVariablesManager():
    
    def __init__(self,current_project):
        self._current_project = current_project
        
        self._variables = {}
        project_path = self._current_project.GetFilename()
        self._variables[PROJECT_NAME_VARIABLE] = self._current_project.GetModel().Name
        self._variables[PROJECT_PATH_VARIABLE] = project_path
        self._variables[PROJECT_DIR_VARIABLE] = os.path.dirname(project_path)
        self._variables[PROJECT_FILENAME_VARIABLE] = os.path.basename(project_path)
        self._variables[PROJECT_EXT_VARIABLE] = consts.PROJECT_EXTENSION
        self._variables[PROJECT_GUID_VARIABLE] = self._current_project.GetModel().Id
        self.EmumSystemEnviroment()
        
        self._variables["Platform"] = sys.platform
        self._variables["ApplicationName"] = wx.GetApp().GetAppName()
        self._variables["ApplicationPath"] = sys.executable
        self._variables["InstallPath"] = utils.GetMainModulePath()
        
    def GetVariable(self,name):
        return self._variables.get(name)

    @property
    def Variables(self):
        return self._variables
        
    def EvalulateValue(self,src_text):
        pattern = re.compile("(?<=\$\{)\S[^}]+(?=})")
        groups = pattern.findall(src_text)
        for name in groups:
            if name not in self._variables:
                raise PromptErrorException(consts._("Could not evaluate the expression variable of \"%s\"") % name)
            else:
                format_name = FormatVariableName(name)
                src_text = src_text.replace(format_name,self.GetVariable(name))
        return src_text
        
    def EmumSystemEnviroment(self):
        for env in os.environ:
            self._variables[env] = os.environ[env]

class VariablesDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,current_project_document = None):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        self.current_project_document = current_project_document
        
        self.search_variable_ctrl = wx.TextCtrl(self, -1, "", size=(-1,-1))
        self.Bind(wx.EVT_TEXT,self.SeachVariable)
        box_sizer.Add(self.search_variable_ctrl, 0, flag=wx.BOTTOM|wx.RIGHT|wx.EXPAND,border=consts.SPACE)
        
        self.dvlc = dataview.DataViewListCtrl(self,size=(400,380))
        self.dvlc.AppendTextColumn(consts._('Name'), width=150)
        self.dvlc.AppendTextColumn(consts._('Value'),width=250)
        dataview.EVT_DATAVIEW_ITEM_ACTIVATED(self.dvlc, -1, self.OnOKClick)
        box_sizer.Add(self.dvlc, 1, wx.EXPAND)
        self.SetVariables()
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, consts._("&Insert"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, consts._("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        box_sizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP,consts.SPACE)
        
        self.SetSizer(box_sizer) 
        self.Fit()
        
    def SeachVariable(self,event):
        search_name = self.search_variable_ctrl.GetValue().strip()
        self.dvlc.DeleteAllItems()
        self.SetVariables(search_name)
            
    def GetVariableList(self):
        def comp_key(x,y):
            if x.lower() > y.lower():
                return 1
            return -1
        project_variable_manager = ProjectVariablesManager(self.current_project_document)
        valirable_name_list = sorted(project_variable_manager.Variables.keys(),cmp=comp_key)
        return valirable_name_list
        
    def SetVariables(self,filter_name = ""):
        project_variable_manager = ProjectVariablesManager(self.current_project_document)
        valirable_name_list = self.GetVariableList()
        for name in valirable_name_list:
            if name.lower().find(filter_name.lower()) != -1 or filter_name == "":
                show_name = FormatVariableName(name)
                self.dvlc.AppendItem([show_name, project_variable_manager.GetVariable(name)])
        
    def OnOKClick(self,event):
        row = self.dvlc.GetSelectedRow()
        if row == -1:
            return
        self.selected_variable_name = self.dvlc.GetTextValue(row,0)
        self.EndModal(wx.ID_OK)