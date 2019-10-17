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
from noval import _,consts,NewId
from tkinter import messagebox
import noval.ide as ide
import noval.python.interpreter.interpretermanager as interpretermanager
from noval.util import strutils
from noval.util import utils
import noval.constants as constants
import noval.model as model
import os
import sys
import noval.syntax.lang as lang
import noval.ui_utils as ui_utils
import subprocess
import noval.util.fileutils as fileutils
import noval.terminal as terminal
import noval.ui_common as ui_common
import noval.misc as misc

class PyIDEApplication(ide.IDEApplication):

    def __init__(self):
        ide.IDEApplication.__init__(self)

    def OnInit(self):
        if not ide.IDEApplication.OnInit(self):
            return False

        #这里必须用相对导入,因为搜索路径已经添加了,如果使用长路径导入会导致IntellisenceManager的实例信息和其它地方的不一样
        import intellisence
        from noval.project.document import ProjectDocument
        import noval.python.debugger.debugger as pythondebugger
        
        self._debugger_class = pythondebugger.PythonDebugger
        
        #pyc和pyo二进制文件类型禁止添加到项目中
        ProjectDocument.BIN_FILE_EXTS = ProjectDocument.BIN_FILE_EXTS + ['pyc','pyo']
        self.interpreter_combo = self.MainFrame.GetToolBar().AddCombox()
        self.interpreter_combo.bind("<<ComboboxSelected>>",self.OnCombo)
      
        if utils.is_windows():
            self.InsertCommand(consts.ID_FEEDBACK,constants.ID_OPEN_PYTHON_HELP,_("&Help"),_("&Python Help Document"),handler=self.OpenPythonHelpDocument,image=self.GetImage("pydoc.png"),pos="before")
            
        self.AddCommand(constants.ID_GOTO_DEFINITION,_("&Edit"),_("Goto Definition"),self.GotoDefinition,default_tester=True,default_command=True)
        self.InsertCommand(consts.ID_FEEDBACK,constants.ID_GOTO_PYTHON_WEB,_("&Help"),_("&Python Website"),handler=self.GotoPythonWebsite,pos="before")
        #解释器菜单插入在插件管理菜单之前
        self.InsertCommand(consts.ID_PLUGIN,constants.ID_OPEN_INTERPRETER,_("&Tools"),_("&Interpreter"),self.OpenInterpreter,image=self.GetImage("python/interpreter.png"),pos="before")
        self.AddCommand(constants.ID_PREFERENCES,_("&Tools"),_("&Options..."),self.OnOptions,image=self.GetImage("prefer.png"),add_separator=True,\
                                        separator_location="top")
        edit_menu = self.Menubar.GetMenu(_("&Edit"))
        insert_menu = edit_menu.GetMenu(constants.ID_INSERT)
        self.AddMenuCommand(constants.ID_INSERT_DECLARE_ENCODING,insert_menu,_("Insert Encoding Declare"),self.InsertEncodingDeclare,default_tester=True,default_command=True)
        

        self.AddCommand(constants.ID_START_WITHOUT_DEBUG,_("&Run"),_("&Start Without Debugging"),self.RunWithoutDebug,default_tester=True,default_command=True)

        self.AddCommand(constants.ID_SET_EXCEPTION_BREAKPOINT,_("&Run"),_("&Exceptions..."),self.SetExceptionBreakPoint,default_tester=True,default_command=True,add_separator=True)
        self.AddCommand(constants.ID_STEP_INTO,_("&Run"),_("&Step Into"),self.StepInto,default_tester=True,default_command=True,image=self.GetImage('python/debugger/step_into.png'))
        self.AddCommand(constants.ID_STEP_NEXT,_("&Run"),_("&Step Over"),self.StepNext,default_tester=True,default_command=True,add_separator=True,image=self.GetImage('python/debugger/step_next.png'))

        self.AddCommand(constants.ID_CHECK_SYNTAX,_("&Run"),_("&Check Syntax..."),self.CheckSyntax,default_tester=True,default_command=True)
        self.AddCommand(constants.ID_SET_PARAMETER_ENVIRONMENT,_("&Run"),_("&Set Parameter And Environment"),self.SetParameterEnvironment,default_tester=True,default_command=True,image=self.GetImage('python/debugger/runconfig.png'))
        self.AddCommand(constants.ID_RUN_LAST,_("&Run"),_("&Run Using Last Settings"),self.RunLast,default_tester=True,default_command=True)
        self.AddCommand(constants.ID_DEBUG_LAST,_("&Run"),_("&Debug Using Last Settings"),self.DebugLast,default_tester=True,default_command=True,add_separator=True)    
        
        self.AddCommand(constants.ID_TOGGLE_BREAKPOINT,_("&Run"),_("&Toggle Breakpoint"),self.ToogleBreakPoint,default_tester=True,default_command=True,image=self.GetImage('python/debugger/breakpoint.png'))
        self.AddCommand(constants.ID_CLEAR_ALL_BREAKPOINTS,_("&Run"),_("&Clear All Breakpoints"),self.ClearAllBreakPoints,default_tester=True,default_command=False) 
        #关闭软件启动图片
        self.CloseSplash()
        
        self.LoadDefaultInterpreter()
        self.AddInterpreters()
        self.intellisence_mananger = intellisence.IntellisenceManager()
        self.intellisence_mananger.generate_default_intellisence_data()
        return True

    def GetInterpreterManager(self):
        return interpretermanager.InterpreterManager()
        
    @ui_utils.no_implemented_yet
    def SetExceptionBreakPoint(self):
        pass
        
    def StepNext(self):
        self.GetDebugger().StepNext()
        
    def StepInto(self):
        self.GetDebugger().StepInto()
        
    def DebugLast(self):
        self.GetDebugger().DebugLast()
        
    def RunLast(self):
        self.GetDebugger().RunLast()

    def CheckSyntax(self):
        self.GetDebugger().CheckScript()
        
    def SetParameterEnvironment(self):
        self.GetDebugger().SetParameterAndEnvironment()
        
    def ToogleBreakPoint(self):
        current_view = self.GetDocumentManager().GetCurrentView()
        #只有python文件才能设置断点
        if current_view is None or not hasattr(current_view,"ToogleBreakpoint"):
            return
        current_view.GetCtrl().ToogleBreakpoint()
        
    def ClearAllBreakPoints(self):
        self.MainFrame.GetView(consts.BREAKPOINTS_TAB_NAME).ClearAllBreakPoints()
        
    @misc.update_toolbar
    def LoadDefaultInterpreter(self):
        interpretermanager.InterpreterManager().LoadDefaultInterpreter()
        
    def GotoDefinition(self):
        current_view = self.GetDocumentManager().GetCurrentView()
        #只有python文件才能执行转到定义功能
        if current_view is None or not hasattr(current_view,"GotoDefinition"):
            return
        current_view.GotoDefinition()

    def LoadDefaultPlugins(self):
        '''
            加载python默认插件
        '''
        import noval.preference as preference
        import noval.python.interpreter.gerneralconfiguration as interpretergerneralconfiguration
        import noval.python.interpreter.interpreterconfigruation as interpreterconfigruation
        ide.IDEApplication.LoadDefaultPlugins(self)
        
        #添加Python语言仅有的首选项面板,在other面板之前
        preference.PreferenceManager().AddOptionsPanelClass(preference.INTERPRETER_OPTION_NAME,preference.GENERAL_ITEM_NAME,interpretergerneralconfiguration.InterpreterGeneralConfigurationPanel)
        preference.PreferenceManager().AddOptionsPanelClass(preference.INTERPRETER_OPTION_NAME,preference.INTERPRETER_CONFIGURATIONS_ITEM_NAME,interpreterconfigruation.InterpreterConfigurationPanel)
        
        consts.DEFAULT_PLUGINS += ("noval.python.project.browser.ProjectViewLoader",)
        consts.DEFAULT_PLUGINS += ('noval.python.plugins.pyshell.PyshellViewLoader',)
        #window面板在outline面板之前,故需在outline之前初始化
        consts.DEFAULT_PLUGINS += ('noval.plugins.windowservice.WindowServiceLoader',)
        consts.DEFAULT_PLUGINS += ('noval.python.plugins.outline.PythonOutlineViewLoader',)
        consts.DEFAULT_PLUGINS += ('noval.python.project.viewer.DefaultProjectTemplateLoader',)
        consts.DEFAULT_PLUGINS += ('noval.python.plugins.unittest.UnittestLoader',)
        consts.DEFAULT_PLUGINS += ('noval.python.debugger.watchs.WatchsViewLoader',)
        consts.DEFAULT_PLUGINS += ('noval.python.debugger.breakpoints.BreakpointsViewLoader',)
        consts.DEFAULT_PLUGINS += ('noval.python.debugger.stacksframe.StackframeViewLoader',)
        consts.DEFAULT_PLUGINS += ('noval.python.debugger.inspectconsole.InspectConsoleViewLoader',)
        consts.DEFAULT_PLUGINS += ('noval.python.plugins.pip_gui.PluginManagerGUI',)
        
    def CreateLexerTemplates(self):
        from noval.syntax import synglob
        #添加parser路径,导入模块时用相对路径即可.
        parser_path = os.path.join(utils.get_app_path(),"noval","python","parser")
        sys.path.append(parser_path)
        ide.IDEApplication.CreateLexerTemplates(self)
        synglob.LexerFactory().CreateLexerTemplates(self.GetDocumentManager(),model.LANGUAGE_PYTHON)
        
    def GetCurrentInterpreter(self):
        return interpretermanager.InterpreterManager().GetCurrentInterpreter()
                            
    def Quit(self):
        if not self.AllowClose():
            return
        self.intellisence_mananger.Stop()
        ide.IDEApplication.Quit(self)
    
    @property
    def OpenProjectPath(self):
        return self._open_project_path
        
    def GetIDESplashBitmap(self):
        return os.path.join(utils.get_app_image_location(),"python/welcome.png")
        
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
        fileutils.startfile(interpreter.HelpPath)
        
    def GotoPythonWebsite(self):
        fileutils.startfile("http://www.python.org")

    def SelectInterpreter(self,interpreter):
        if interpreter != interpretermanager.InterpreterManager().GetCurrentInterpreter():
            interpretermanager.InterpreterManager().SetCurrentInterpreter(interpreter)
            if self.intellisence_mananger.IsRunning:
                return
            self.intellisence_mananger.load_intellisence_data(interpreter)
            
    def GetDefaultLangId(self):
        return lang.ID_LANG_PYTHON
        
    def InsertCodingDeclare(self):
        pass
        
    def OpenInterpreter(self):
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            messagebox.showinfo(self.GetAppName(),_("No interpreter..."))
            return
        try:
            if utils.is_windows():
                fileutils.startfile(interpreter.Path)
            else:
                cmd_list = ['gnome-terminal','-x','bash','-c',interpreter.Path]
                subprocess.Popen(cmd_list,shell = False)
        except Exception as e:
            messagebox.showerror(_("Open Error"),_("%s") % str(e),parent=self.GetTopWindow())

    def OpenTerminator(self,filename=None):
        if filename:
            if os.path.isdir(filename):
                cwd = filename
            else:
                cwd = os.path.dirname(filename)
        else:
            cwd = os.getcwd()
        #打开终端时不嵌入解释器环境
        if not utils.profile_get_int("EmbedInterpreterInterminator", True):
            ide.IDEApplication.OpenTerminator(self,filename)
            return 
            
        interpreter = self.GetCurrentInterpreter()
        if interpreter is None:
            ide.IDEApplication.OpenTerminator(self,filename)
            return
        else:
            target_executable = interpreter.Path
        
        exe_dirs = interpreter.GetExedirs()
        env_overrides = {}
        env_overrides["PATH"] = ui_utils.get_augmented_system_path(exe_dirs) 
        #设置安装路径的环境变量,运行程序时需要在路径中移除此路径
        #python2.7中环境变量不能为unicode类型
        env_overrides['MAIN_MODULE_APTH'] = str(utils.get_app_path())
        explainer = os.path.join(os.path.dirname(__file__), "explain_environment.py")
        cmd = [target_executable, explainer]
        #检测是否虚拟解释器
        activate = os.path.join(os.path.dirname(target_executable), 
                                "activate.bat" if utils.is_windows()
                                else "activate")
        
        if os.path.isfile(activate):
            del env_overrides["PATH"]
            if utils.is_windows():
                cmd = [activate, "&"] + cmd
            else:
                cmd = ["source", activate, ";"] + cmd 
        return terminal.run_in_terminal(cmd, cwd, env_overrides, True)

    def RunWithoutDebug(self):
        self.GetDebugger().RunWithoutDebug()

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
        if command_id == constants.ID_CLEAR_ALL_BREAKPOINTS:
            return 0 != len(self.MainFrame.GetView(consts.BREAKPOINTS_TAB_NAME).GetMasterBreakpointDict())
        current_project = self.MainFrame.GetProjectView(False).GetCurrentProject()
        current_interpreter = self.GetCurrentInterpreter()
        builtin_item_ids = [constants.ID_RUN,constants.ID_SET_EXCEPTION_BREAKPOINT,constants.ID_STEP_INTO,constants.ID_STEP_NEXT,constants.ID_RUN_LAST]
        all_item_ids = builtin_item_ids + [constants.ID_SET_PARAMETER_ENVIRONMENT,constants.ID_DEBUG_LAST,constants.ID_START_WITHOUT_DEBUG]
        #使用内建解释器时,禁止运行按钮和菜单
        if command_id in builtin_item_ids:
            if current_interpreter is None or current_interpreter.IsBuiltIn:
                return False
        elif command_id in all_item_ids:
            if current_interpreter is None:
                return False
        if current_project is not None:
            if command_id in all_item_ids:
                return True
        return ide.IDEApplication.UpdateUI(self,command_id)
            