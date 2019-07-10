from noval import GetApp,_
import os
import noval.consts as consts
import re
import tkinter as tk
from tkinter import ttk
#from noval.util.exceptions import PromptErrorException
import sys
from noval.util import utils
import noval.ui_base as ui_base
import noval.ttkwidgets.treeviewframe as treeviewframe
from noval.python.parser.utils import py_sorted

PROJECT_NAME_VARIABLE = "ProjectName"
PROJECT_PATH_VARIABLE = "ProjectPath"
PROJECT_DIR_VARIABLE = "ProjectDir"
PROJECT_FILENAME_VARIABLE = "ProjectFileName"
PROJECT_GUID_VARIABLE = "ProjectGuid"
PROJECT_EXT_VARIABLE = "ProjectExtension"

def FormatVariableName(name):
    return "${%s}" % name
        
class VariablesManager():
    
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
        self._variables["ApplicationName"] = GetApp().GetAppName()
        self._variables["ApplicationPath"] = sys.executable
        self._variables["InstallPath"] = utils.get_app_path()
        
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

class VariablesDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title,current_project_document = None):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
      
        ttk.Label(self.main_frame, text=_("Input the variable name:")).pack(fill="x")
        self.current_project_document = current_project_document
        
        self.search_variable_var = tk.StringVar()
        search_variable_ctrl = ttk.Entry(self.main_frame,textvariable=self.search_variable_var)
        search_variable_ctrl.pack(fill="x")
        self.search_variable_var.trace("w", self.SeachVariable)
        columns = ['Name','Value']
        self.listview = treeviewframe.TreeViewFrame(self.main_frame,columns=columns,height=20,show="headings")
        self.listview.pack(fill="both",expand=1)
        self.listview.tree.bind('<Double-Button-1>',self._ok)
        self.SetVariables()
        self.AddokcancelButton()
        self.ok_button.configure(text=_("&Insert"),default="active")

    def SeachVariable(self,*args):
        search_name = self.search_variable_var.get().strip()
        self._clear_tree()
        self.SetVariables(search_name)

    def _clear_tree(self):
        for child_id in self.listview.tree.get_children():
            self.listview.tree.delete(child_id)
            
    def GetVariableList(self):
        def comp_key(x,y):
            if x.lower() > y.lower():
                return 1
            return -1
        project_variable_manager = VariablesManager(self.current_project_document)
        valirable_name_list = py_sorted(project_variable_manager.Variables.keys(),cmp_func=comp_key)
        return valirable_name_list
        
    def SetVariables(self,filter_name = ""):
        project_variable_manager = VariablesManager(self.current_project_document)
        valirable_name_list = self.GetVariableList()
        for name in valirable_name_list:
            if name.lower().find(filter_name.lower()) != -1 or filter_name == "":
                show_name = FormatVariableName(name)
                self.listview.tree.insert("",0,values=(show_name,project_variable_manager.GetVariable(name)))
        
    def _ok(self,event=None):
        selections = self.listview.tree.selection()
        if not selections:
            return
        self.selected_variable_name = self.listview.tree.item(selections[0])['values'][0]
        ui_base.CommonModaldialog._ok(self)