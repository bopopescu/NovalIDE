import wx
from noval.tool.consts import SPACE,HALF_SPACE,_
import noval.util.utils as utils
import noval.tool.PythonEditor as PythonEditor

class InterpreterGeneralConfigurationPanel(wx.Panel):
    """description of class"""
    
    def __init__(self,parent,dlg_id,size):
        wx.Panel.__init__(self, parent, dlg_id,size=size)
        
        self._warnInterpreterPathCheckBox = wx.CheckBox(self, -1, _("Warn when interpreter path contain no asc character on debug and run"))
        self._warnInterpreterPathCheckBox.SetValue(utils.ProfileGetInt("WarnInterpreterPath", True))
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(self._warnInterpreterPathCheckBox, 0, wx.ALL, SPACE)
        
        self._showBuiltinInterpreterWindowCheckBox = wx.CheckBox(self, -1, _("Show the builtin interpreter window"))
        self._showBuiltinInterpreterWindowCheckBox.SetValue(utils.ProfileGetInt(wx.GetApp().GetService(PythonEditor.PythonService).GetServiceName() + "Shown", True))
        box_sizer.Add(self._showBuiltinInterpreterWindowCheckBox, 0, wx.LEFT, SPACE)
        self.SetSizer(box_sizer)
        self.Layout()
        
    def OnOK(self,optionsDialog):
        utils.ProfileSet("WarnInterpreterPath",int(self._warnInterpreterPathCheckBox.GetValue()))
        pythonService = wx.GetApp().GetService(PythonEditor.PythonService)
        pythonService.ShowWindow(self._showBuiltinInterpreterWindowCheckBox.GetValue())
        utils.ProfileSet(pythonService.GetServiceName() + "Shown",int(self._showBuiltinInterpreterWindowCheckBox.GetValue()))
        return True
