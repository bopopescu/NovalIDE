# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        pyide.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-10
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import _,consts
from tkinter import messagebox
import noval.ide as ide
import sys
import noval.util.apputils as apputils
import noval.util.appdirs as appdirs
import noval.util.logger as logger
import shutil
import noval.python.interpreter.InterpreterManager as interpretermanager,\
        noval.python.interpreter.Interpreter as Interpreter
import noval.python.parser.intellisence as intellisence
from noval.util import strutils
import noval.python.parser.utils as parserutils
import noval.imageutils as imageutils
from noval.util import utils
import noval.constants as constants
from pkg_resources import resource_filename
import noval.model as model
import os
from dummy.userdb import UserDataDb
import noval.project.baseviewer as baseprojectviewer
import noval.python.project.viewer as projectviewer
from noval.syntax import synglob
import noval.syntax.lang as lang
import noval.ui_utils as ui_utils
import subprocess
import noval.util.fileutils as fileutils
import noval.terminal as terminal
import noval.python.unittest as unittest
import noval.python.pyeditor as pyeditor
import noval.preference as preference
import noval.python.interpreter.gerneralconfiguration as interpretergerneralconfiguration
import noval.python.interpreter.InterpreterConfigruation as InterpreterConfigruation
#这些导入模块未被引用,用于py2exe打包模块进library.zip里面去
import noval.python.outline
import noval.python.project.browser
import noval.python.pyshell
import noval.python.debugger.Debugger as Debugger
import noval.ui_common as ui_common
import noval.misc as misc
_debugger = None

class PyIDEApplication(ide.IDEApplication):

    def __init__(self):
        ide.IDEApplication.__init__(self)

    def OnInit(self):
        global _debugger
        if not ide.IDEApplication.OnInit(self):
            return False
        #关闭软件启动图片
        self.CloseSplash()
        #设置Python文本视图在大纲中显示语法树
        self.MainFrame.GetOutlineView().AddViewTypeForBackgroundHandler(pyeditor.PythonView)
        
        _debugger = Debugger.Debugger()
        self.interpreter_combo = self.MainFrame.GetToolBar().AddCombox()
        self.interpreter_combo.bind("<<ComboboxSelected>>",self.OnCombo)
        
        self.LoadDefaultInterpreter()
        self.AddInterpreters()
        #projectService.SetCurrentProject()
        intellisence.IntellisenceManager().generate_default_intellisence_data()
      
        if utils.is_windows():
            self.AddCommand(constants.ID_OPEN_PYTHON_HELP,_("&Help"),_("&Python Help Document"),handler=self.OpenPythonHelpDocument,image=self.GetImage("pydoc.png"))
            
        self.AddCommand(constants.ID_GOTO_DEFINITION,_("&Edit"),_("Goto Definition"),self.GotoDefinition,default_tester=True,default_command=True)
        self.AddCommand(constants.ID_GOTO_PYTHON_WEB,_("&Help"),_("&Python Website"),handler=self.GotoPythonWebsite)
        self.AddCommand(constants.ID_UNITTEST,_("&Tools"),_("&UnitTest"),self.OnUnittestDlg,default_tester=True,default_command=True)
        self.AddCommand(constants.ID_OPEN_INTERPRETER,_("&Tools"),_("&Interpreter"),self.OpenInterpreter,image=self.GetImage("python/interpreter.png"))
        self.AddCommand(constants.ID_PREFERENCES,_("&Tools"),_("&Options..."),self.OnOptions,image=self.GetImage("prefer.png"),add_separator=True,\
                                        separator_location="top")
        edit_menu = self.Menubar.GetMenu(_("&Edit"))
        insert_menu = edit_menu.GetMenu(constants.ID_INSERT)
        self.AddMenuCommand(constants.ID_INSERT_DECLARE_ENCODING,insert_menu,_("Insert Encoding Declare"),self.InsertEncodingDeclare,default_tester=True,default_command=True)
        
        preference.PreferenceManager().AddOptionsPanel(preference.INTERPRETER_OPTION_NAME,preference.GENERAL_ITEM_NAME,interpretergerneralconfiguration.InterpreterGeneralConfigurationPanel)
        preference.PreferenceManager().AddOptionsPanel(preference.INTERPRETER_OPTION_NAME,preference.INTERPRETER_CONFIGURATIONS_ITEM_NAME,InterpreterConfigruation.InterpreterConfigurationPanel)
        return True
        
    @misc.update_toolbar
    def LoadDefaultInterpreter(self):
        interpretermanager.InterpreterManager().LoadDefaultInterpreter()
        
    def GotoDefinition(self):
        current_view = self.GetDocumentManager().GetCurrentView()
        current_view.GetCtrl().GotoDefinition()

    def OnUnittestDlg(self):
        current_view = self.GetDocumentManager().GetCurrentView()
        dlg = unittest.UnitTestDialog(current_view.GetFrame(),current_view)
        if dlg.CreateUnitTestFrame():
            dlg.ShowModal()
        
    def CreateProjectTemplate(self):
        projectTemplate = projectviewer.PythonProjectTemplate(self.GetDocumentManager(),
                _("Project File"),
                "*%s" % consts.PROJECT_EXTENSION,
                os.getcwd(),
                consts.PROJECT_EXTENSION,
                "Project Document",
                _("Project Viewer"),
                projectviewer.PythonProjectDocument,
                projectviewer.PythonProjectView,
                icon = imageutils.getProjectIcon())
        self.GetDocumentManager().AssociateTemplate(projectTemplate)
        
    def CreateLexerTemplates(self):
        ide.IDEApplication.CreateLexerTemplates(self)
        synglob.LexerFactory().CreateLexerTemplates(self.GetDocumentManager(),model.LANGUAGE_PYTHON)
        
    @property       
    def ToolbarCombox(self):
        return self.toolbar_combox
        
    def GetCurrentInterpreter(self):
        return interpretermanager.InterpreterManager().GetCurrentInterpreter()
        
    def SetCurrentInterpreter(self):
        current_interpreter = interpretermanager.InterpreterManager.GetCurrentInterpreter()
        if current_interpreter is None:
            self.toolbar_combox.SetSelection(-1)
            return
        for i in range(self.toolbar_combox.GetCount()):
            data = self.toolbar_combox.GetClientData(i)
            if data == current_interpreter:
                self.toolbar_combox.SetSelection(i)
                break
                
    def AddInterpreters(self):
        cb = self.ToolbarCombox
        cb.Clear()
        for interpreter in interpretermanager.InterpreterManager().interpreters:
            cb.Append(interpreter.Name,interpreter)
        cb.Append(_("Configuration"),)
        self.SetCurrentInterpreter()
        
    def Quit(self):
        if not self.AllowClose():
            return
        intellisence.IntellisenceManager().Stop()
        ide.IDEApplication.Quit(self)
    
    @property
    def OpenProjectPath(self):
        return self._open_project_path
        
    def GetIDESplashBitmap(self):
        return os.path.join(utils.get_app_image_location(),"tt.png")
        
    def AddInterpreters(self):
        names = interpretermanager.InterpreterManager().GetInterpreterNames()
        names.append(_("Configuration"),)
        self.interpreter_combo['values'] = names
        self.SetCurrentInterpreter()
        
    def SetCurrentInterpreter(self):
        current_interpreter = interpretermanager.InterpreterManager().GetCurrentInterpreter()
        if current_interpreter is None:
            return
        for i in range(len(self.interpreter_combo['values'])):
            data = interpretermanager.InterpreterManager().interpreters[i]
            if data == current_interpreter:
                self.interpreter_combo.current(i)
                break

    @misc.update_toolbar
    def OnCombo(self,event):
        selection = self.interpreter_combo.current()
        if selection == len(self.interpreter_combo['values']) - 1:
            pass
        #    if BaseDebuggerUI.DebuggerRunning():
         
         #       prompt = True
          #  else:
            #    UICommon.ShowInterpreterOptionPage()
            ui_common.ShowInterpreterConfigurationPage()
        else:
            interpreter = interpretermanager.InterpreterManager().interpreters[selection]
            self.SelectInterpreter(interpreter)
            if interpreter != self.GetCurrentInterpreter():
                prompt = True
            else:
                self.SelectInterpreter(interpreter)
        #if prompt:
        #    wx.MessageBox(_("Please stop the debugger first!"),style=wx.OK|wx.ICON_WARNING)
         #   wx.GetApp().SetCurrentInterpreter()

    def OpenPythonHelpDocument(self):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        if interpreter.HelpPath == "":
            return
        os.startfile(interpreter.HelpPath)
        
    def GotoPythonWebsite(self):
        os.startfile("http://www.python.org")

    def SelectInterpreter(self,interpreter):
        if interpreter != interpretermanager.InterpreterManager().GetCurrentInterpreter():
            interpretermanager.InterpreterManager().SetCurrentInterpreter(interpreter)
            if intellisence.IntellisenceManager().IsRunning:
                return
            intellisence.IntellisenceManager().load_intellisence_data(interpreter)
            
    def GetDefaultLangId(self):
        return lang.ID_LANG_PYTHON
        
    def InsertCodingDeclare(self):
        pass
        
    def OpenInterpreter(self):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            return
        try:
            if utils.is_windows():
                fileutils.start_file(interpreter.Path)
            else:
                cmd_list = ['gnome-terminal','-x','bash','-c',interpreter.Path]
                subprocess.Popen(cmd_list,shell = False)
        except Exception as e:
            wx.MessageBox(_("%s") % str(e),_("Open Error"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())

    def OpenTerminator(self,filename=None):
        if filename:
            cwd = os.path.dirname(filename)
        else:
            cwd = os.getcwd()
            
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            target_executable = None
        else:
            target_executable = interpreter.Path
        
        exe_dirs = interpreter.GetExedirs()
        env_overrides = {}
        env_overrides["PATH"] = ui_utils.get_augmented_system_path(exe_dirs) 
        explainer = os.path.join(os.path.dirname(__file__), "explain_environment.py")
        cmd = [target_executable, explainer]
        
        activate = os.path.join(os.path.dirname(target_executable), 
                                "activate.bat" if utils.is_windows()
                                else "activate")
        
        if os.path.isfile(activate):
            del env_overrides["PATH"]
            if platform.system() == "Windows":
                cmd = [activate, "&"] + cmd
            else:
                cmd = ["source", activate, ";"] + cmd 
            
        return terminal.run_in_terminal(cmd, cwd, env_overrides, True)

    def Run(self):
        _debugger.Run()
        
    def DebugRun(self):
        raise Exception("This method must be implemented in derived class")
        

    def InsertEncodingDeclare(self,text_view = None):
        if text_view is None:
            text_view = self.GetDocumentManager().GetCurrentView()
        
        lines = text_view.GetCtrl().GetTopLines(consts.ENCODING_DECLARE_LINE_NUM)
        coding_name,line_num = strutils.get_python_coding_declare(lines)
        if  coding_name is not None:
            ret = messagebox.askyesno(_("Declare Encoding"),_("The Python Document have already declare coding,Do you want to overwrite it?"),parent=text_view.GetFrame())
            if ret == True:
                text_view.SetSelection(text_view.GetCtrl().PositionFromLine(line_num),text_view.GetCtrl().PositionFromLine(line_num+1))
                text_view.GetCtrl().DeleteBack()
            else:
                return True
                
        dlg = ui_utils.EncodingDeclareDialog(text_view.GetFrame())
        if dlg.ShowModal() == constants.ID_OK:
            text_view.GetCtrl().GotoPos(0,0)
            text_view.AddText(dlg.name_var.get() + "\n")
            return True
        return False
        
    def UpdateUI(self,command_id):
        current_interpreter = self.GetCurrentInterpreter()
        #使用内建解释器时,禁止运行按钮和菜单
        if command_id == constants.ID_RUN:
            if current_interpreter is None or current_interpreter.IsBuiltIn:
                return False
        elif command_id == constants.ID_DEBUG:
            if current_interpreter is None:
                return False

        return ide.IDEApplication.UpdateUI(self,command_id)
            