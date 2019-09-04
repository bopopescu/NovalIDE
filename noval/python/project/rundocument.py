# -*- coding: utf-8 -*-
from noval import _
from noval.project.document import ProjectDocument
from noval.python.debugger.executor import *
from noval.python.debugger.commandproperty import *
import noval.python.project.model as pyprojectlib
import noval.python.pyutils as pyutils
import uuid
from noval.python.debugger.commandui import *
import noval.python.project.runconfiguration as runconfiguration
import noval.consts as consts

'''
    运行python文件或者项目
    按运行模式分为运行:单个文件和项目
'''

class PythonProjectDocument(ProjectDocument):
    def __init__(self, model=None):
        ProjectDocument.__init__(self,model)
        
    @staticmethod
    def GetProjectModel():
        return pyprojectlib.PythonProject()

    def GetFileRunConfiguration(self,run_file):
        '''
            获取单个文件的运行配置,单个文件有多个运行配置,每个运行配置的运行方式是不同的
        '''
        file_key = self.GetFileKey(run_file)
        run_configuration_name = utils.profile_get(file_key + "/RunConfigurationName","")
        return run_configuration_name
        
    def GetRunfileParameter(self,run_file):
        '''
            获取项目要运行单个python文件的运行参数
        '''
        #优先查找运行文件的运行配置,如果存在,则使用运行配置里面的运行文件参数
        run_configuration_name = self.GetFileRunConfiguration(run_file)
        if run_configuration_name:
            file_configuration = runconfiguration.FileConfiguration(self,run_file)
            run_configuration = file_configuration.LoadConfiguration(run_configuration_name)
            try:
                return run_configuration.GetRunParameter()
            except PromptErrorException as e:
                wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR)
                return None
            
        #再获取通过运行菜单->配置参数和环境变量显示的对话框里面设置的运行文件参数
        use_argument = utils.profile_get_int(self.GetFileKey(run_file,"UseArgument"),True)
        if use_argument:
            initialArgs = utils.profile_get(self.GetFileKey(run_file,"RunArguments"),"")
        else:
            initialArgs = ''
        python_path = utils.profile_get(self.GetFileKey(run_file,"PythonPath"),"")
        startIn = utils.profile_get(self.GetFileKey(run_file,"RunStartIn"),"")
        if startIn == '':
            startIn = os.path.dirname(self.GetFilename())
        env = {}
        paths = set()
        path_post_end = utils.profile_get_int(self.GetKey("PythonPathPostpend"), True)
        if path_post_end:
            paths.add(str(os.path.dirname(self.GetFilename())))
        #should avoid environment contain unicode string,such as u'xxx'
        if len(python_path) > 0:
            paths.add(str(python_path))
        env[consts.PYTHON_PATH_NAME] = os.pathsep.join(list(paths))
        #获取项目的运行配置类
        return self.GetRunconfigClass()(GetApp().GetCurrentInterpreter(),run_file.filePath,initialArgs,env,startIn,project=self)

    def SaveRunParameter(self,run_parameter):
        project_name = os.path.basename(self.GetFilename())
        utils.profile_set(self.GetKey("LastRunProject"), project_name)
        utils.profile_set(self.GetKey("LastRunFile"), run_parameter.FilePath)
        # Don't update the arguments or starting directory unless we're runing python.
        utils.profile_set(self.GetKey("LastRunArguments"), run_parameter.Arg)
        utils.profile_set(self.GetKey("LastRunStartIn"), run_parameter.StartupPath)
        if run_parameter.Environment is not None and consts.PYTHON_PATH_NAME in run_parameter.Environment:
            utils.profile_set(self.GetKey("LastPythonPath"),run_parameter.Environment[consts.PYTHON_PATH_NAME])

    def DebugRunBuiltin(self,run_parameter):
        fileToRun = run_parameter.FilePath
        GetApp().MainFrame.ShowView(consts.PYTHON_INTERPRETER_VIEW_NAME,toogle_visibility_flag=True)
        python_interpreter_view = GetApp().MainFrame.GetCommonView(consts.PYTHON_INTERPRETER_VIEW_NAME)
        old_argv = sys.argv
        environment,initialArgs = run_parameter.Environment,run_parameter.Arg
        sys.argv = [fileToRun]
        command = 'execfile(r"%s")' % fileToRun
        python_interpreter_view.run(command)
        sys.argv = old_argv
        
    def GetRunConfiguration(self,run_file=None):
        '''
            获取项目的当前运行配置,也就是默认启动文件的运行配置
        '''
        if run_file is None:
            run_configuration_key = self.GetKey()
        else:
            run_configuration_key = self.GetFileKey(run_file)
        run_configuration_name = utils.profile_get(run_configuration_key + "/RunConfigurationName","")
        return run_configuration_name
        
    def GetFileRunParameter(self,filetoRun=None,is_break_debug=False):
        #when there is not project or run file is not in current project
        # run one single python file
        #在项目中运行其他项目的文件,则不能获取当前项目的运行配置,以及当前项目为空时,都按运行单个python文件模式来处理
        if self.GetModel().Id == ProjectDocument.UNPROJECT_MODEL_ID or (filetoRun is not None and self.GetModel().FindFile(filetoRun) is None):
            doc_view = self.GetDebugger().GetActiveView()
            if doc_view:
                document = doc_view.GetDocument()
                if not document.Save() or document.IsNewDocument:
                    return None
                if self.GetDebugger().IsFileContainBreakPoints(document) or is_break_debug:
                    messagebox.showwarning(GetApp().GetAppName(),_("Debugger can only run in active project"))
            else:
                return None
            run_parameter = document.GetRunParameter()
        #获取当前项目的运行配置
        else:
            #run project
            if filetoRun is None:
                #default run project start up file
                run_file = self.GetandSetProjectStartupfile()
            else:
                run_file = self.GetModel().FindFile(filetoRun)
            if not run_file:
                return None
            self.PromptToSaveFiles()
            #获取启动文件的运行参数
            run_parameter = self.GetRunfileParameter(run_file)
        return run_parameter

    def IsProjectContainBreakPoints(self):
        masterBPDict = GetApp().MainFrame.GetView(consts.BREAKPOINTS_TAB_NAME).GetMasterBreakpointDict()
        for key in masterBPDict:
            if self.GetModel().FindFile(key) and len(masterBPDict[key]) > 0:
                return True
        return False
        
    def GetRunParameter(self,filetoRun=None,is_break_debug=False):
        '''
            @is_break_debug:user force to debug breakpoint or not
        '''
        if not PythonExecutor.GetPythonExecutablePath():
            return None
        is_debug_breakpoint = False
        #load project configuration first,if have one run configuration,the run it
        run_configuration_name = self.GetRunConfiguration()
        #if user force run one project file ,then will not run configuration from config
        if filetoRun is None and run_configuration_name:
            project_configuration = runconfiguration.ProjectConfiguration(self)
            run_configuration = project_configuration.LoadConfiguration(run_configuration_name)
            #if run configuration name does not exist,then run in normal
            if not run_configuration:
                run_parameter = self.GetFileRunParameter(filetoRun,is_break_debug)
            else:
                run_parameter = run_configuration.GetRunParameter()
        else:
            run_parameter = self.GetFileRunParameter(filetoRun,is_break_debug)
        
        #invalid run parameter
        if run_parameter is None:
                return None
                    
        #check project files has breakpoint,if has one breakpoint,then run in debugger mode
        if self.IsProjectContainBreakPoints():
            is_debug_breakpoint = True
            
        run_parameter = pyutils.get_override_runparameter(run_parameter)
        run_parameter.IsBreakPointDebug = is_debug_breakpoint
        return run_parameter
        
    def Debug(self):
        run_parameter = self.GetRunParameter()
        if run_parameter is None:
            return
        if not run_parameter.IsBreakPointDebug:
            self.DebugRunScript(run_parameter)
        else:
            self.DebugrunBreakpoint(run_parameter)
        self.GetDebugger().AppendRunParameter(run_parameter)
            
    def DebugRunScript(self,run_parameter):
        if run_parameter.Interpreter.IsBuiltIn:
            self.DebugRunBuiltin(run_parameter)
            return
        fileToRun = run_parameter.FilePath
        shortFile = os.path.basename(fileToRun)
        view = GetApp().MainFrame.AddView("Debugger"+ str(uuid.uuid1()).lower(),RunCommandUI,_("Running: ") + shortFile,"s",visible_by_default=True,\
                                   image_file="python/debugger/debug.ico",debugger=self.GetDebugger(), run_parameter=run_parameter,visible_in_menu=False)
        page = view['instance']
        page.Execute()
        GetApp().GetDocumentManager().ActivateView(self.GetDebugger().GetView())
       

    def RunWithoutDebug(self,filetoRun=None):
        run_parameter = self.GetRunParameter(filetoRun)
        if run_parameter is None:
            return
        run_parameter.IsBreakPointDebug = False
        self.DebugRunScript(run_parameter)
        self.GetDebugger().AppendRunParameter(run_parameter)
        
    def Run(self,filetoRun=None):
        run_parameter = self.GetRunParameter(filetoRun)
        if run_parameter is None:
            return
        self.RunScript(run_parameter)
        self.GetDebugger().AppendRunParameter(run_parameter)
            
    def RunScript(self,run_parameter):
        interpreter = run_parameter.Interpreter
        #内建解释器只能调试代码,不能在终端中运行
        if interpreter.IsBuiltIn:
            return
        executor = PythonrunExecutor(run_parameter)
        executor.Execute()
            
    def GetLastRunParameter(self,is_debug):
        if not PythonExecutor.GetPythonExecutablePath():
            return None
        dlg_title = _('Run File')
        btn_name = _("Run")
        if is_debug:
           dlg_title = _('Debug File')
           btn_name = _("Debug")
        dlg = CommandPropertiesDialog(GetApp().GetTopWindow(),dlg_title, self, okButtonName=btn_name, debugging=is_debug,is_last_config=True)
        showDialog = dlg.MustShowDialog()
        is_parameter_save = False
        if showDialog and dlg.ShowModal() == constants.ID_OK:
            projectDocument, fileToDebug, initialArgs, startIn, isPython, environment = dlg.GetSettings()
            #when show run dialog first,need to save parameter
            is_parameter_save = True
        #直接从配置中读取运行参数,不显示对话框
        elif not showDialog:
            #隐藏窗口
            dlg.withdraw()
            projectDocument, fileToDebug, initialArgs, startIn, isPython, environment = dlg.GetSettings()
            dlg.destroy()
        #取消
        else:
            dlg.destroy()
            return None
        if self.GetFilename() != consts.NOT_IN_ANY_PROJECT and self.IsProjectContainBreakPoints():
            is_debug_breakpoint = True
        else:
            is_debug_breakpoint = False
        run_parameter = runconfig.PythonRunconfig(GetApp().GetCurrentInterpreter(),\
                            fileToDebug,initialArgs,environment,startIn,is_debug_breakpoint)
        if is_parameter_save:
            self.SaveRunParameter(run_parameter)
        return run_parameter
            
    def DebugRunLast(self):
        run_parameter = self.GetLastRunParameter(True)
        if run_parameter is None:
            return
        run_parameter = pyutils.get_override_runparameter(run_parameter)
        if not run_parameter.IsBreakPointDebug:
            self.DebugRunScript(run_parameter)
        else:
            self.DebugRunScriptBreakPoint(run_parameter)
       
    def RunLast(self):
        run_parameter = self.GetLastRunParameter(False)
        if run_parameter is None:
            return
        run_parameter = pyutils.get_override_runparameter(run_parameter)
        self.RunScript(run_parameter)

    def SetParameterAndEnvironment(self):
        dlg = CommandPropertiesDialog(GetApp().GetTopWindow(), _('Set Parameter And Environment'), self,okButtonName=_("&OK"))
        dlg.ShowModal()


    def BreakintoDebugger(self,filetoRun=None):
        run_parameter = self.GetRunParameter(filetoRun,is_break_debug=True)
        #debugger must run in project
        if run_parameter is None or run_parameter.Project is None:
            return
        run_parameter.IsBreakPointDebug = True
        self.DebugrunBreakpoint(run_parameter,autoContinue=False)
        
    def DebugrunBreakpoint(self,run_parameter,autoContinue=True):
        '''
            autoContinue可以让断点调式是否会在开始中断
        '''
        if BaseDebuggerUI.DebuggerRunning():
            messagebox.showinfo( _("Debugger Running"),_("A debugger is already running. Please shut down the other debugger first."))
            return
        host = utils.profile_get("DebuggerHostName", DEFAULT_HOST)
        if not host:
            wx.MessageBox(_("No debugger host set. Please go to Tools->Options->Debugger and set one."), _("No Debugger Host"))
            return
        fileToRun = run_parameter.FilePath
        shortFile = os.path.basename(fileToRun)
        view = GetApp().MainFrame.AddView("Debugger"+ str(uuid.uuid1()).lower(),PythonDebuggerUI,_("Debugging: ") + shortFile,"s",visible_by_default=True,\
                                   image_file="python/debugger/debugger.png",debugger=self.GetDebugger(), run_parameter=run_parameter,visible_in_menu=False,autoContinue=autoContinue)
        page = view['instance']
        page.Execute()
        self.GetDebugger().SetDebuggerUI(page)
        GetApp().GetDocumentManager().ActivateView(self.GetDebugger().GetView())