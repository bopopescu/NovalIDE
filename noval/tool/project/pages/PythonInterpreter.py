import wx
from noval.tool.consts import SPACE,HALF_SPACE,_
import noval.tool.interpreter.InterpreterManager as interpretermanager
import wx.lib.agw.hyperlink as hl
import noval.tool.service.OptionService as OptionService
import BasePanel
import noval.util.utils as utils

class PythonInterpreterPanel(BasePanel.BasePanel):
    def __init__(self,filePropertiesService,parent,dlg_id,size,selected_item):
        BasePanel.BasePanel.__init__(self,filePropertiesService, parent, dlg_id,size,selected_item)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        interpreterLabelText = wx.StaticText(self, -1, _("Interpreter:"))
        lineSizer.Add(interpreterLabelText,0,flag=wx.LEFT,border=SPACE)
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        self.interpreterCombo = wx.ComboBox(self, -1,size=(-1,-1),choices=choices, style = wx.CB_READONLY)
        if len(choices) > 0:
            self.interpreterCombo.SetSelection(default_selection)
        
        lineSizer.Add(self.interpreterCombo,1,flag=wx.LEFT|wx.EXPAND,border=HALF_SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.TOP,border = SPACE)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        hyperLinkCtrl = hl.HyperLinkCtrl(self, wx.ID_ANY, _("Click to configure interpreters not listed"))
        hyperLinkCtrl.SetColours("BLUE", "BLUE", "BLUE")
        hyperLinkCtrl.AutoBrowse(False)
        hyperLinkCtrl.SetBold(True)
        lineSizer.Add(hyperLinkCtrl,1,flag=wx.LEFT|wx.EXPAND,border=SPACE)
        box_sizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT|wx.TOP,border = HALF_SPACE)
        ###hyperLinkCtrl.SetToolTip(wx.ToolTip(_("Click to Configure Interpreters")))
        self.Bind(hl.EVT_HYPERLINK_LEFT, self.GotoInterpreterConfiguration,hyperLinkCtrl)
        self.SetSizer(box_sizer)
        #should use Layout ,could not use Fit method
        self.Layout()
        
        project_interpreter_name = utils.ProfileGet(self.ProjectDocument.GetKey() + "/Interpreter","")
        if project_interpreter_name:
            self.interpreterCombo.SetValue(project_interpreter_name)
        
    def OnOK(self,optionsDialog):
        utils.ProfileSet(self.ProjectDocument.GetKey() + "/Interpreter",self.interpreterCombo.GetValue())
        return True
        
    def GotoInterpreterConfiguration(self,event):
        option_service = wx.GetApp().GetService(OptionService.OptionsService)
        option_service.OnOption(option_name = OptionService.GetOptionName(OptionService.INTERPRETER_OPTION_NAME,OptionService.INTERPRETER_CONFIGURATIONS_ITEM_NAME))
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        self.interpreterCombo.Clear()
        if len(choices) > 0:
            self.interpreterCombo.InsertItems(choices,0)
            self.interpreterCombo.SetSelection(default_selection)
            wx.GetApp().AddInterpreters()
