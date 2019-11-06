# -*- coding: utf-8 -*-
from noval import _
import tkinter as tk
from tkinter import ttk
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.util.utils as utils
import noval.consts as consts
import noval.python.project.runconfiguration as runconfiguration
import noval.project.property as projectproperty
import noval.ui_utils as ui_utils
import noval.ttkwidgets.linklabel as linklabel
import noval.ui_common as ui_common


class PythonInterpreterPanel(ui_utils.BaseConfigurationPanel):
    def __init__(self,parent,item,current_project):
        ui_utils.BaseConfigurationPanel.__init__(self,parent)
        self._current_project = current_project
        row = ttk.Frame(self)
        interpreterLabelText = ttk.Label(row, text=_("Interpreter:")).pack(fill="x",side=tk.LEFT)
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        #默认选择项目文件中指定的解释器
        interpreter_info = self._current_project.GetModel().interpreter
        if interpreter_info.name in choices:
            default_selection = choices.index(interpreter_info.name)
        self.interpreterCombo = ttk.Combobox(row,values=choices)
        self.interpreterCombo['state'] = 'readonly'
        self.interpreterCombo.pack(fill="x",side=tk.LEFT,expand=1)
        row.pack(fill="x")
        if len(choices) > 0:
            self.interpreterCombo.current(default_selection)
        hyperLinkCtrl = linklabel.LinkLabel(self,text=_("Click to configure interpreters not listed"),normal_color='royal blue',hover_color='blue',clicked_color='purple')
        hyperLinkCtrl.bind("<Button-1>", self.GotoInterpreterConfiguration)
        hyperLinkCtrl.pack(fill="x",pady=consts.DEFAUT_HALF_CONTRL_PAD_Y)
        project_interpreter_name = runconfiguration.ProjectConfiguration.LoadProjectInterpreter(current_project.GetKey())
        if project_interpreter_name and project_interpreter_name in choices:
            self.interpreterCombo.current(choices.index(project_interpreter_name))
        
    def OnOK(self,optionsDialog):
        #界面上更改解释器,项目文件中也要更改解释器信息
        if self.GetInterpreter().Name != self._current_project.GetModel().interpreter.name:
            self._current_project.GetModel().SetInterpreter(self.GetInterpreter().Name)
            self._current_project.Modify(True)
        utils.profile_set(self._current_project.GetKey() + "/Interpreter",self.GetInterpreter().Name)
        return True
        
    def GotoInterpreterConfiguration(self,event):
        if not ui_common.ShowInterpreterConfigurationPage():
            return
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        self.interpreterCombo['values'] = choices
        if len(choices) > 0:
            self.interpreterCombo.current(default_selection)

    def GetInterpreter(self):
        return interpretermanager.InterpreterManager().interpreters[self.interpreterCombo.current()]


