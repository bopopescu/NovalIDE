# -*- coding: utf-8 -*-
from noval import GetApp,_
import os
import noval.consts as consts
import re
import tkinter as tk
from tkinter import ttk,messagebox
import sys
from noval.util import utils
import noval.ui_base as ui_base
import noval.ttkwidgets.treeviewframe as treeviewframe
from noval.python.parser.utils import py_sorted
import getpass
import noval.project.baseviewer as baseviewer
import noval.constants as constants

PROJECT_NAME_VARIABLE = "ProjectName"
PROJECT_PATH_VARIABLE = "ProjectPath"
PROJECT_DIR_VARIABLE = "ProjectDir"
PROJECT_FILENAME_VARIABLE = "ProjectFileName"
PROJECT_GUID_VARIABLE = "ProjectGuid"
PROJECT_EXT_VARIABLE = "ProjectExtension"


PRJECT_VARIABLES_MANAGER = {}


def GetProjectVariableManager(current_project=None):
    if current_project is None:
        current_project = GetApp().MainFrame.GetProjectView(generate_event=False).GetCurrentProject()
    if current_project is None:
        current_project = baseviewer.ProjectDocument.GetUnProjectDocument()
    name = current_project.GetModel().name
    if name not in PRJECT_VARIABLES_MANAGER:
        PRJECT_VARIABLES_MANAGER[name] = VariablesManager(current_project)
    return PRJECT_VARIABLES_MANAGER[name]

def FormatVariableName(name):
    return "${%s}" % name
        
class VariablesManager():
    
    def __init__(self,current_project=None,**kwargs):
        self._current_project = current_project
        
        self._variables = {}
        if self._current_project is not None:
            project_path = self._current_project.GetFilename()
            self._variables[PROJECT_NAME_VARIABLE] = self._current_project.GetModel().Name
            self._variables[PROJECT_PATH_VARIABLE] = project_path
            self._variables[PROJECT_DIR_VARIABLE] = os.path.dirname(project_path)
            self._variables[PROJECT_FILENAME_VARIABLE] = os.path.basename(project_path)
            self._variables[PROJECT_EXT_VARIABLE] = consts.PROJECT_EXTENSION
            self._variables[PROJECT_GUID_VARIABLE] = self._current_project.GetModel().Id
   
        self._variables.update(self.GetGlobalVariables(**kwargs))
        
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
                raise RuntimeError(_("Could not evaluate the expression variable of \"%s\"") % name)
            else:
                format_name = FormatVariableName(name)
                src_text = src_text.replace(format_name,self.GetVariable(name))
        return src_text
        
    @staticmethod
    def EmumSystemEnviroment():
        d = {}
        for env in os.environ:
            d[env] = os.environ[env]
        return d
            
    @classmethod
    def GetGlobalVariables(cls,**kwargs):
        d = cls.EmumSystemEnviroment()
        d.update(kwargs)
        d["Platform"] = sys.platform
        d["ApplicationName"] = GetApp().GetAppName()
        d["ApplicationPath"] = sys.executable
        d["InstallPath"] = utils.get_app_path()
        if not 'USER' in d:
            d['USER'] = getpass.getuser()
        return d
        
    def AddVariable(self,name,value):
        if name in self._variables:
            return
        self._variables[name] = value

class NewVariableDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_("Name")+ ":").pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        self.name_var = tk.StringVar()
        key_ctrl = ttk.Entry(row,textvariable=self.name_var)
        key_ctrl.pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        row.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_("Value:")).pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        self.value_var = tk.StringVar()
        value_ctrl = ttk.Entry(row,textvariable=self.value_var)
        value_ctrl.pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        row.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AddokcancelButton()

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
        self.listview = treeviewframe.TreeViewFrame(self.main_frame,columns=columns,height=20,show="headings",displaycolumns=(0,1))
        self.listview.pack(fill="both",expand=1)
        self.listview.tree.bind('<Double-Button-1>',self._ok)
        
        for column in columns:
            self.listview.tree.heading(column, text=_(column))
            
        self.SetVariables()
        
        new_button = ttk.Button(self.main_frame, text=_("New"), command=self.NewVariable)
        new_button.pack(fill="x",side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        
        self.AddokcancelButton(side=tk.LEFT)
        self.ok_button.configure(text=_("&Insert"),default="active")
        self.FormatTkButtonText(self.ok_button)

    def SeachVariable(self,*args):
        search_name = self.search_variable_var.get().strip()
        self._clear_tree()
        self.SetVariables(search_name)

    def _clear_tree(self):
        for child_id in self.listview.tree.get_children():
            self.listview.tree.delete(child_id)
            
    def GetVariableList(self):
        #以变量名升序排列
        def comp_key(x,y):
            if x.lower() > y.lower():
                return -1
            return 1
        project_variable_manager = GetProjectVariableManager(self.current_project_document)
        valirable_name_list = py_sorted(project_variable_manager.Variables.keys(),cmp_func=comp_key)
        return valirable_name_list
        
    def SetVariables(self,filter_name = ""):
        project_variable_manager = GetProjectVariableManager(self.current_project_document)
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

    def NewVariable(self):
        dlg = NewVariableDialog(self,_("New Variable"))
        status = dlg.ShowModal()
        name = dlg.name_var.get().strip()
        value = dlg.value_var.get().strip()
        if status == constants.ID_OK and name and value:
            self.AddVariable(name,value)
        
    def AddVariable(self,name,value):
        global PRJECT_VARIABLES_MANAGER
        variable_name = FormatVariableName(name)
        for child_id in self.listview.tree.get_children():
            if self.listview.tree.item(child_id)['values'][0] == variable_name:
                ret = messagebox.askyesno(_("Warning"),_("variable name has already exist in variable list,Do you wann't to overwrite it?"),parent=self)
                if ret == False:
                    return
                else:
                    self.listview.tree.delete(child_id)
                    break
        project_variable_manager = VariablesManager(self.current_project_document,**{name:value})
        PRJECT_VARIABLES_MANAGER[self.current_project_document.GetModel().name] = project_variable_manager
        self.listview.tree.insert("",0,values=(variable_name,project_variable_manager.GetVariable(name)))
        project_variable_manager.AddVariable(name,value)