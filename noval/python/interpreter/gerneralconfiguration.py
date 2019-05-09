from noval import _,GetApp
import tkinter as tk
from tkinter import ttk
import noval.consts as consts
import noval.util.utils as utils
import noval.python.interpreter.InterpreterManager as interpretermanager
import noval.python.parser.intellisence as intellisence
import noval.util.apputils as sysutilslib
import noval.util.fileutils as fileutils
import noval.python.parser.run as pythonrun
import os

class InterpreterGeneralConfigurationPanel(ttk.Frame):
    """description of class"""
    
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        
        self._warnInterpreterPathVar = tk.IntVar(value=utils.profile_get_int("WarnInterpreterPath", True))
        warnInterpreterPathCheckBox = ttk.Checkbutton(self, text= _("Warn when interpreter path contain no asc character on debug and run"),\
                variable=self._warnInterpreterPathVar)
        warnInterpreterPathCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
           
        self._showBuiltinInterpreterWindowVar = tk.IntVar(value=utils.profile_get_int("WarnInterpreterPath", True))
        showBuiltinInterpreterWindowCheckBox = ttk.Checkbutton(self,text=_("Show the builtin interpreter window"),variable=self._showBuiltinInterpreterWindowVar)
        showBuiltinInterpreterWindowCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        self._createIntellienseDatabaseVar = tk.IntVar(value=utils.profile_get_int("AutoGenerateDatabase", True))
        createIntellienseDatabaseCheckBox = ttk.Checkbutton(self, text=_("Automatically generate intellisence database when add interpreter"),variable=self._createIntellienseDatabaseVar)
        createIntellienseDatabaseCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        box_frame = ttk.LabelFrame(self, text=_("Intellisence database update interval"))
        box_frame.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        updateEveryStartupRadioBtn = ttk.Radiobutton(box_frame, text = _("Once when startup"))
        updateEveryStartupRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        updateEveryDayRadioBtn = ttk.Radiobutton(box_frame, text = _("Once a day"))
        updateEveryDayRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        updateEveryWeekRadioBtn = ttk.Radiobutton(box_frame,text = _("Once a week"))
        updateEveryWeekRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        updateEveryMonthRadioBtn = ttk.Radiobutton(box_frame, text = _("Once a month"))
        updateEveryMonthRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        neverUpdateRadioBtn = ttk.Radiobutton(box_frame,text = _("Never"))
        neverUpdateRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")

        if not GetApp().GetDebug():
            
            sbox = tk.labelframe(self, text=_("Intellisence database location"))
            interpreterLabelText = ttk.Label(sbox, text=_("Interpreter:"))
            choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
            self.interpreterCombo = ttk.Combobox(sbox, choices=choices)
            self.interpreterCombo.state(['readonly'])
            if len(choices) > 0:
                self.interpreterCombo.SetSelection(default_selection)
           ## self.interpreterCombo.Bind(wx.EVT_COMBOBOX, self.OnSelectInterpreter) 
            locationLabelText = ttk.Label(sbox, text=_("Database Location:"))
            self.locationControl = ttk.Entry(sbox, -1)
            self.locationControl.Enable(False)
            into_file_explower_btn = ttk.Button(self, -1, _("Into file explorer"))
            wx.EVT_BUTTON(into_file_explower_btn, -1, self.IntoFileExplorer)
            lineSizer.Add(into_file_explower_btn, 0,flag=wx.LEFT, border=SPACE) 
            
            copy_path_btn = ttk.Button(self, -1, _("Copy path"))
            wx.EVT_BUTTON(copy_path_btn, -1, self.CopyDatabasePath)
            lineSizer.Add(copy_path_btn, 0,flag=wx.LEFT, border=SPACE) 
            
            database_version_btn = ttk.Button(self, -1, _("Database version"))
            wx.EVT_BUTTON(database_version_btn, -1, self.GetDatabaseVersion)
            lineSizer.Add(database_version_btn, 0,flag=wx.LEFT, border=SPACE)
            
            last_update_btn = ttk.Button(self, -1, _("Last update time"))
            wx.EVT_BUTTON(last_update_btn, -1, self.GetLastUpdateTime)
            lineSizer.Add(last_update_btn, 0,flag=wx.LEFT, border=SPACE) 
            
            clear_data_btn = ttk.Button(self, -1, _("Clear data"))
            wx.EVT_BUTTON(clear_data_btn, -1, self.ClearIntellisenceData)
            self.OnSelectInterpreter(None)
       # self.SetUpdateIntervalOption()
        
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
        
        update_interval_option = utils.profile_get_int("DatabaseUpdateInterval",UPDATE_ONCE_STARTUP)
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