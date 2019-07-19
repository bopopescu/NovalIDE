# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        gerneralconfiguration.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-07-16
# Copyright:   (c) wukan 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from noval import _,GetApp
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import noval.consts as consts
import noval.util.utils as utils
import noval.python.interpreter.interpretermanager as interpretermanager
import noval.python.parser.intellisence as intellisence
import noval.util.apputils as sysutilslib
import noval.util.fileutils as fileutils
import noval.python.parser.run as pythonrun
import os
import noval.ui_utils as ui_utils

class InterpreterGeneralConfigurationPanel(ui_utils.BaseConfigurationPanel):
    """description of class"""
    
    def __init__(self,parent):
        ui_utils.BaseConfigurationPanel.__init__(self, parent)
        
        self._warnInterpreterPathVar = tk.IntVar(value=utils.profile_get_int("WarnInterpreterPath", True))
        warnInterpreterPathCheckBox = ttk.Checkbutton(self, text= _("Warn when interpreter path contain no asc character on debug and run"),\
                variable=self._warnInterpreterPathVar)
        warnInterpreterPathCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
           
        #是否显示内建解释器窗口,读取注册表里面存储解释器窗口是否显示的值
        self._showBuiltinInterpreterWindowVar = tk.IntVar(value=utils.profile_get_int(consts.PYTHON_INTERPRETER_VIEW_NAME + "ViewVisible", False))
        showBuiltinInterpreterWindowCheckBox = ttk.Checkbutton(self,text=_("Show the builtin interpreter window"),variable=self._showBuiltinInterpreterWindowVar)
        showBuiltinInterpreterWindowCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        self._createIntellienseDatabaseVar = tk.IntVar(value=utils.profile_get_int("AutoGenerateDatabase", True))
        createIntellienseDatabaseCheckBox = ttk.Checkbutton(self, text=_("Automatically generate intellisence database when add interpreter"),variable=self._createIntellienseDatabaseVar)
        createIntellienseDatabaseCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        box_frame = ttk.LabelFrame(self, text=_("Intellisence database update interval"))
        box_frame.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        self._update_interval_var = tk.IntVar(value=utils.profile_get_int("DatabaseUpdateInterval",consts.UPDATE_ONCE_DAY)
)
        updateEveryStartupRadioBtn = ttk.Radiobutton(box_frame, text = _("Once when startup"),value=consts.UPDATE_ONCE_STARTUP,variable=self._update_interval_var)
        updateEveryStartupRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        updateEveryDayRadioBtn = ttk.Radiobutton(box_frame, text = _("Once a day"),value=consts.UPDATE_ONCE_DAY,variable=self._update_interval_var)
        updateEveryDayRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        updateEveryWeekRadioBtn = ttk.Radiobutton(box_frame,text = _("Once a week"),value=consts.UPDATE_ONCE_WEEK,variable=self._update_interval_var)
        updateEveryWeekRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        updateEveryMonthRadioBtn = ttk.Radiobutton(box_frame, text = _("Once a month"),value=consts.UPDATE_ONCE_MONTH,variable=self._update_interval_var)
        updateEveryMonthRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        neverUpdateRadioBtn = ttk.Radiobutton(box_frame,text = _("Never"),value=consts.NEVER_UPDATE_ONCE,variable=self._update_interval_var)
        neverUpdateRadioBtn.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")

        if GetApp().GetDebug():
            sbox = ttk.LabelFrame(self, text=_("Intellisence database location"))
            sbox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
            row = ttk.Frame(sbox)
            interpreterLabelText = ttk.Label(row, text=_("Interpreter:"))
            interpreterLabelText.pack(side=tk.LEFT,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
            choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
            self.interpreterCombo = ttk.Combobox(row, values=choices)
            self.interpreterCombo.state(['readonly'])
            if len(choices) > 0:
                self.interpreterCombo.current(default_selection)
            self.interpreterCombo.bind("<<ComboboxSelected>>",self.OnSelectInterpreter)
            self.interpreterCombo.pack(side=tk.LEFT,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
            row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
            row = ttk.Frame(sbox)
            locationLabelText = ttk.Label(row, text=_("Database Location:"))
            locationLabelText.pack(side=tk.LEFT,fill="x")
            self.location_var = tk.StringVar()
            locationControl = ttk.Entry(row,textvariable=self.location_var)
            locationControl["state"] = tk.DISABLED
            locationControl.pack(side=tk.LEFT,fill="x",expand=1)
            row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
            
            row = ttk.Frame(sbox)
            into_file_explower_btn = ttk.Button(row, text=_("Into file explorer"),command=self.IntoFileExplorer)
            into_file_explower_btn.pack(side=tk.LEFT,fill="x",padx=(0,consts.DEFAUT_CONTRL_PAD_X))
            copy_path_btn = ttk.Button(row, text=_("Copy path"),command=self.CopyDatabasePath)
            copy_path_btn.pack(side=tk.LEFT,fill="x",padx=(0,consts.DEFAUT_CONTRL_PAD_X))
            database_version_btn = ttk.Button(row, text=_("Database version"),command=self.GetDatabaseVersion)
            database_version_btn.pack(side=tk.LEFT,fill="x",padx=(0,consts.DEFAUT_CONTRL_PAD_X))
            last_update_btn = ttk.Button(row, text=_("Last update time"),command=self.GetLastUpdateTime)
            last_update_btn.pack(side=tk.LEFT,fill="x",padx=(0,consts.DEFAUT_CONTRL_PAD_X))
            clear_data_btn = ttk.Button(row,text=_("Clear data"),command=self.ClearIntellisenceData)
            clear_data_btn.pack(side=tk.LEFT,fill="x",padx=(0,consts.DEFAUT_CONTRL_PAD_X))
            row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
            self.OnSelectInterpreter()
       # self.SetUpdateIntervalOption()
        
    def IntoFileExplorer(self):
        location = self.location_var.get()
        fileutils.open_file_directory(location)
        
    def CopyDatabasePath(self):
        path = self.location_var.get()
        sysutilslib.CopyToClipboard(path)
        messagebox.showinfo("",_("Copied to clipboard"))
        
    def GetDatabaseVersion(self):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        try:
            intellisence_data_path = intellisence.IntellisenceManager().\
                        GetInterpreterIntellisenceDataPath(interpreter)
            database_version = pythonrun.LoadDatabaseVersion(intellisence_data_path)
            messagebox.showinfo("",database_version)
        except Exception as e:
            messagebox.showerror("",str(e))
        
    def GetLastUpdateTime(self):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        try:
            intellisence_data_path = intellisence.IntellisenceManager().\
                        GetInterpreterIntellisenceDataPath(interpreter)
            last_update_time = pythonrun.GetLastUpdateTime(intellisence_data_path)
            messagebox.showinfo("",last_update_time)
        except Exception as e:
            messagebox.showerror("",str(e))
        
    def ClearIntellisenceData(self):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        intellisence_data_path = intellisence.IntellisenceManager().\
                    GetInterpreterIntellisenceDataPath(interpreter)
        for f in os.listdir(intellisence_data_path):
            file_path = os.path.join(intellisence_data_path,f)
            os.remove(file_path)
        
    def GetCurrentInterpreter(self):
        selection = self.interpreterCombo.current()
        if -1 == selection:
            return None
        interpreter = interpretermanager.InterpreterManager().interpreters[selection]
        return interpreter
        
    def OnSelectInterpreter(self,event=None):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        database_path = intellisence.IntellisenceManager().GetInterpreterDatabasePath(interpreter)
        self.location_var.set(database_path)
        
    def GetUpdateIntervalOption(self):
        return self._update_interval_var.get()
        
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
        utils.profile_set("WarnInterpreterPath",int(self._warnInterpreterPathVar.get()))
        GetApp().MainFrame.ShowView(consts.PYTHON_INTERPRETER_VIEW_NAME,hidden=not self._showBuiltinInterpreterWindowVar.get(),toogle_visibility_flag=True)
        utils.profile_set(consts.PYTHON_INTERPRETER_VIEW_NAME + "ViewVisible",int(self._showBuiltinInterpreterWindowVar.get()))
        utils.profile_set("DatabaseUpdateInterval",self.GetUpdateIntervalOption())
        utils.profile_set("AutoGenerateDatabase",int(self._createIntellienseDatabaseVar.get()))
        return True

    def IsAutoGenerateDatabase(self):
        return self._createIntellienseDatabaseVar.get()