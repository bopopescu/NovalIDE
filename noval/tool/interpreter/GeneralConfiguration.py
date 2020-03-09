import wx
from noval.tool.consts import SPACE,HALF_SPACE,_,ERROR_OK,UPDATE_ONCE_STARTUP,\
        UPDATE_ONCE_DAY,UPDATE_ONCE_WEEK,UPDATE_ONCE_MONTH,NEVER_UPDATE_ONCE
import noval.util.utils as utils
import noval.tool.PythonEditor as PythonEditor
import noval.tool.interpreter.InterpreterManager as interpretermanager
import noval.parser.intellisence as intellisence
import noval.util.sysutils as sysutilslib
import noval.util.fileutils as fileutils
import noval.parser.factory as factory
import os

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
        box_sizer.Add(self._showBuiltinInterpreterWindowCheckBox, 0, wx.LEFT|wx.BOTTOM, SPACE)
        
        self._createIntellienseDatabaseCheckBox = wx.CheckBox(self, -1, _("Automatically generate intellisence database when add interpreter"))
        self._createIntellienseDatabaseCheckBox.SetValue(utils.ProfileGetInt("AutoGenerateDatabase",True))
        box_sizer.Add(self._createIntellienseDatabaseCheckBox, 0, wx.LEFT, SPACE)
        

        sbox = wx.StaticBox(self, -1, _("Intellisence database update interval"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        self.updateEveryStartupRadioBtn = wx.RadioButton(self,-1, label = _("Once when startup") ,style = wx.RB_GROUP)
        sboxSizer.Add(self.updateEveryStartupRadioBtn,0,flag=wx.TOP,border=0)
        
        self.updateEveryDayRadioBtn = wx.RadioButton(self,-1, label = _("Once a day"))
        sboxSizer.Add(self.updateEveryDayRadioBtn,0,flag=wx.TOP,border=HALF_SPACE)
        self.updateEveryWeekRadioBtn = wx.RadioButton(self,-1, label = _("Once a week"))
        sboxSizer.Add(self.updateEveryWeekRadioBtn,0,flag=wx.TOP,border=HALF_SPACE)
        self.updateEveryMonthRadioBtn = wx.RadioButton(self,-1, label = _("Once a month"))
        sboxSizer.Add(self.updateEveryMonthRadioBtn,0,flag=wx.TOP,border=HALF_SPACE)
        self.neverUpdateRadioBtn = wx.RadioButton(self,-1, label = _("Never"))
        sboxSizer.Add(self.neverUpdateRadioBtn,0,flag=wx.TOP|wx.BOTTOM,border=HALF_SPACE)
        
        box_sizer.Add(sboxSizer, 0, flag=wx.TOP|wx.LEFT|wx.EXPAND,border=SPACE)
        
        if wx.GetApp().GetDebug():
            
            sbox = wx.StaticBox(self, -1, _("Intellisence database location"))
            sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
            
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            interpreterLabelText = wx.StaticText(self, -1, _("Interpreter:"))
            lineSizer.Add(interpreterLabelText,0,flag=wx.LEFT,border=SPACE)
            choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
            self.interpreterCombo = wx.ComboBox(self, -1,size=(-1,-1),choices=choices, style = wx.CB_READONLY)
            if len(choices) > 0:
                self.interpreterCombo.SetSelection(default_selection)
            self.interpreterCombo.Bind(wx.EVT_COMBOBOX, self.OnSelectInterpreter) 
            lineSizer.Add(self.interpreterCombo,1,flag=wx.LEFT|wx.EXPAND,border=SPACE)
            sboxSizer.Add(lineSizer,0,flag=wx.TOP|wx.BOTTOM,border=HALF_SPACE)
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            locationLabelText = wx.StaticText(self, -1, _("Database Location:"))
            lineSizer.Add(locationLabelText,0,flag=wx.LEFT,border=SPACE)
            self.locationControl = wx.TextCtrl(self, -1)
            self.locationControl.Enable(False)
            lineSizer.Add(self.locationControl,1,flag=wx.LEFT|wx.EXPAND,border=SPACE)
            sboxSizer.Add(lineSizer,0,flag=wx.TOP|wx.BOTTOM|wx.EXPAND|wx.RIGHT,border=HALF_SPACE)
            
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            into_file_explower_btn = wx.Button(self, -1, _("Into file explorer"))
            wx.EVT_BUTTON(into_file_explower_btn, -1, self.IntoFileExplorer)
            lineSizer.Add(into_file_explower_btn, 0,flag=wx.LEFT, border=SPACE) 
            
            copy_path_btn = wx.Button(self, -1, _("Copy path"))
            wx.EVT_BUTTON(copy_path_btn, -1, self.CopyDatabasePath)
            lineSizer.Add(copy_path_btn, 0,flag=wx.LEFT, border=SPACE) 
            
            database_version_btn = wx.Button(self, -1, _("Database version"))
            wx.EVT_BUTTON(database_version_btn, -1, self.GetDatabaseVersion)
            lineSizer.Add(database_version_btn, 0,flag=wx.LEFT, border=SPACE)
            
            last_update_btn = wx.Button(self, -1, _("Last update time"))
            wx.EVT_BUTTON(last_update_btn, -1, self.GetLastUpdateTime)
            lineSizer.Add(last_update_btn, 0,flag=wx.LEFT, border=SPACE) 
            
            clear_data_btn = wx.Button(self, -1, _("Clear data"))
            wx.EVT_BUTTON(clear_data_btn, -1, self.ClearIntellisenceData)
            lineSizer.Add(clear_data_btn, 0,flag=wx.LEFT, border=SPACE) 
            sboxSizer.Add(lineSizer,0,flag=wx.TOP|wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT,border=HALF_SPACE)
            
            box_sizer.Add(sboxSizer, 0, flag=wx.TOP|wx.LEFT|wx.EXPAND,border=SPACE)
            self.OnSelectInterpreter(None)
        self.SetSizer(box_sizer)
        self.Layout()
        self.SetUpdateIntervalOption()
        
    def IntoFileExplorer(self,event):
        location = self.locationControl.GetValue()
        err_code,msg = fileutils.open_file_directory(location)
        if err_code != ERROR_OK:
            wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
        
    def CopyDatabasePath(self,event):
        path = self.locationControl.GetValue()
        sysutilslib.CopyToClipboard(path)
        wx.MessageBox(_("Copied to clipboard"))
        
    def GetDatabaseVersion(self,event):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        try:
            intellisence_data_path = intellisence.IntellisenceManager().\
                        GetInterpreterIntellisenceDataPath(interpreter)
            database_version = factory.LoadDatabaseVersion(intellisence_data_path)
            wx.MessageBox(database_version)
        except Exception as e:
            wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)
        
    def GetLastUpdateTime(self,event):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        try:
            intellisence_data_path = intellisence.IntellisenceManager().\
                        GetInterpreterIntellisenceDataPath(interpreter)
            last_update_time = factory.GetLastUpdateTime(intellisence_data_path)
            wx.MessageBox(last_update_time)
        except Exception as e:
            wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)
        
    def ClearIntellisenceData(self,event):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        intellisence_data_path = intellisence.IntellisenceManager().\
                    GetInterpreterIntellisenceDataPath(interpreter)
        for f in os.listdir(intellisence_data_path):
            file_path = os.path.join(intellisence_data_path,f)
            os.remove(file_path)
        
    def GetCurrentInterpreter(self):
        selection = self.interpreterCombo.GetSelection()
        if -1 == selection:
            return None
        interpreter = interpretermanager.InterpreterManager().interpreters[selection]
        return interpreter
        
    def OnSelectInterpreter(self,event):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        database_path = intellisence.IntellisenceManager().GetInterpreterDatabasePath(interpreter)
        self.locationControl.SetValue(database_path)
        
    def GetUpdateIntervalOption(self):
        if self.updateEveryDayRadioBtn.GetValue():
            return UPDATE_ONCE_DAY
        elif self.updateEveryMonthRadioBtn.GetValue():
            return UPDATE_ONCE_MONTH
        elif self.updateEveryWeekRadioBtn.GetValue():
            return UPDATE_ONCE_WEEK
        elif self.updateEveryStartupRadioBtn.GetValue():
            return UPDATE_ONCE_STARTUP
        return NEVER_UPDATE_ONCE
        
    def SetUpdateIntervalOption(self):
        
        update_interval_option = utils.ProfileGetInt("DatabaseUpdateInterval",UPDATE_ONCE_STARTUP)
        if update_interval_option == UPDATE_ONCE_DAY:
            self.updateEveryDayRadioBtn.SetValue(True)
        elif update_interval_option == UPDATE_ONCE_MONTH:
            self.updateEveryMonthRadioBtn.SetValue(True)
        elif update_interval_option == UPDATE_ONCE_WEEK:
            self.updateEveryWeekRadioBtn.SetValue(True)
        elif update_interval_option == UPDATE_ONCE_STARTUP:
            self.updateEveryStartupRadioBtn.SetValue(True)
        else:
            self.neverUpdateRadioBtn.SetValue(True)
        
    def OnOK(self,optionsDialog):
        utils.ProfileSet("WarnInterpreterPath",int(self._warnInterpreterPathCheckBox.GetValue()))
        pythonService = wx.GetApp().GetService(PythonEditor.PythonService)
        pythonService.ShowWindow(self._showBuiltinInterpreterWindowCheckBox.GetValue())
        utils.ProfileSet(pythonService.GetServiceName() + "Shown",int(self._showBuiltinInterpreterWindowCheckBox.GetValue()))
        utils.ProfileSet("DatabaseUpdateInterval",self.GetUpdateIntervalOption())
        utils.ProfileSet("AutoGenerateDatabase",int(self._createIntellienseDatabaseCheckBox.GetValue()))
        return True

    def IsAutoGenerateDatabase(self):
        return self._createIntellienseDatabaseCheckBox.GetValue()