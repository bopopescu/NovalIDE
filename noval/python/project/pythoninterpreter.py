from noval import _
import tkinter as tk
from tkinter import ttk
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.util.utils as utils
import noval.iface as iface
import noval.plugin as plugin
import noval.consts as consts
#import noval.tool.project.RunConfiguration as RunConfiguration
import noval.project.property as projectproperty
import noval.ui_utils as ui_utils
import noval.ttkwidgets.linklabel as linklabel


class PythonInterpreterPanel(ui_utils.BaseConfigurationPanel):
    def __init__(self,parent,item,current_project):
        ui_utils.BaseConfigurationPanel.__init__(self,parent)
        self._current_project = current_project
        row = ttk.Frame(self)
        interpreterLabelText = ttk.Label(row, text=_("Interpreter:")).pack(fill="x",side=tk.LEFT)
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        self.interpreterCombo = ttk.Combobox(row,values=choices)
        
        self.interpreterCombo.pack(fill="x",side=tk.LEFT,expand=1)

        row.pack(fill="x")
 #       if len(choices) > 0:
  #          self.interpreterCombo.select(default_selection)
        

        hyperLinkCtrl = linklabel.LinkLabel(self,text=_("Click to configure interpreters not listed"),normal_color='royal blue',hover_color='blue',clicked_color='purple')
        hyperLinkCtrl.bind("<Button-1>", self.GotoInterpreterConfiguration)
        
        hyperLinkCtrl.pack(fill="x")
        #project_interpreter_name = RunConfiguration.ProjectConfiguration.LoadProjectInterpreter(current_project.GetKey())
        #if project_interpreter_name:
         #   self.interpreterCombo.SetValue(project_interpreter_name)
        
    def OnOK(self,optionsDialog):
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/Interpreter",self.GetInterpreterName())
        return True
        
    def GotoInterpreterConfiguration(self,event):
        UICommon.ShowInterpreterOptionPage()
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        self.interpreterCombo.Clear()
        if len(choices) > 0:
            self.interpreterCombo.InsertItems(choices,0)
            self.interpreterCombo.SetSelection(default_selection)

    def GetInterpreterName(self):
        return self.interpreterCombo.GetValue()


class PythonInterpreterPageLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        projectproperty.PropertiesService().AddProjectOptionsPanel("Interpreter",PythonInterpreterPanel)

consts.DEFAULT_PLUGINS += ('noval.python.project.pythoninterpreter.PythonInterpreterPageLoader',)
