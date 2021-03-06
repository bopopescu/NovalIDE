#--------------------------------------------------------------------------#
# Dependancies
import tkinter as tk
from tkinter import ttk,messagebox
from noval import _
import noval.util.utils as utils
import noval.project.wizard as projectwizard
from noval.project.baseconfig import *
from noval.python.project.viewer import *
from noval.python.project.rundocument import *
import noval.consts as consts
import noval.imageutils as imageutils
import os
import noval.util.strutils as strutils
import noval.python.parser.utils as parserutils
from noval.project.executor import *
import noval.terminal as terminal
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.ttkwidgets.checklistbox as checklistbox
import noval.editor.text as texteditor
import noval.ttkwidgets.textframe as textframe
from pkg_resources import resource_filename
from bz2 import BZ2File
import noval.project.command as command
import noval.util.compat as compat
import noval.python.parser.utils as dirutils
import noval.python.project.runconfiguration as runconfiguration
import json
import io as cStringIO
import noval.misc as misc
import noval.python.pyutils as pyutils
from noval.python.project.model import *
import noval.python.interpreter.interpretermanager as interpretermanager

class PyPIOptionPanel(pyutils.PythonBaseConfigurationPanel):
    
    ZIP_FILE_EXTENSION = 0
    EGG_FILE_EXTENSION = 1
    WHEEL_FILE_EXTENSION = 2
    def __init__(self,parent,item,current_project,**kwargs):
        pyutils.PythonBaseConfigurationPanel.__init__(self,parent,current_project)
        self.columnconfigure(1, weight=1)
        self.current_project = current_project
        self.item = item

        self.output_default_var = tk.IntVar(value=self.ZIP_FILE_EXTENSION)
        sbox = ttk.LabelFrame(self, text=_("Output file extension:"))
        self.zip_btn = ttk.Radiobutton(sbox,text=_('Zip'),variable=self.output_default_var,value=self.ZIP_FILE_EXTENSION)
        self.zip_btn.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        self.whl_btn = ttk.Radiobutton(sbox,text=_('Wheel'),variable=self.output_default_var,value=self.WHEEL_FILE_EXTENSION)
        self.whl_btn.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        ttk.Radiobutton(sbox,text=_('Egg'),variable=self.output_default_var,value=self.EGG_FILE_EXTENSION).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        sbox.pack(fill="x")
        self.DisableNoPythonfile(item)
        
    def OnOK(self,optionsDialog=None):
        self.current_project.SaveBuildConfiguration(self.GetItemFile(self.item),self.GetBuildArgs(),self.GetBuildArgs(),self.current_project.GetModel().interpreter.name)
        return True
        
    def GetBuildArgs(self):
        if self.output_default_var.get() == self.ZIP_FILE_EXTENSION:
            return 'sdist'
        elif self.output_default_var.get() == self.EGG_FILE_EXTENSION:
            return 'bdist_egg'
        elif self.output_default_var.get() == self.WHEEL_FILE_EXTENSION:
            return 'bdist_wheel'
        

class NovalPluginOptionPanel(PyPIOptionPanel):
    def __init__(self,parent,item,current_project,**kwargs):
        PyPIOptionPanel.__init__(self,parent,item,current_project,**kwargs)
        self.output_default_var.set(PyPIOptionPanel.EGG_FILE_EXTENSION)
        self.zip_btn['state'] = tk.DISABLED
        self.whl_btn['state'] = tk.DISABLED
        
    def OnOK(self,optionsDialog=None):
        self.current_project.SaveBuildConfiguration(self.GetItemFile(self.item),"bdist_novalplugin_egg",self.GetBuildArgs(),self.current_project.GetModel().interpreter.name)
        return True

class PyPIProject(PythonProject):
    def __init__(self):
        super(PyPIProject,self).__init__()
        self._runinfo.DocumentTemplate = "pypi.pypi.PyPIProjectTemplate"
        

class NovalPluginProject(PythonProject):
    def __init__(self):
        super(NovalPluginProject,self).__init__()
        self._runinfo.DocumentTemplate = "pypi.pypi.NovalPluginProjectTemplate"

class PyPIProjectDocument(PythonProjectDocument):

    def __init__(self, model=None):
        PythonProjectDocument.__init__(self,model)

    @staticmethod
    def GetProjectModel():
        return PyPIProject()
        
    def CleanProject(self):
        PythonProjectDocument.CleanProject(self)
        self.CleanBuilddir()
        self.CleanOutput()

    def CleanBuilddir(self):
        project_path = self.GetPath()
        build_dir = os.path.join(project_path,'build')
        self.Cleandir(build_dir)
        
    def GetDistPath(self):
        dist_path = os.path.join(self.GetPath(),'dist')
        return dist_path
        
    def GetProjectStartupFile(self):
        startup_file = self.GetandSetProjectStartupfile()
        return startup_file
            
    def GetProjectDocInterpreter(self):
        return self.GetandSetProjectDocInterpreter()

    def GetEgg(self):
        dist_path = self.GetDistPath()
        startup_file = self.GetProjectStartupFile()
        if startup_file is None:
            return None,None,None
        interpreter = self.GetProjectDocInterpreter()
        if not interpreter:
            return None,None,None
        cmd = "%s %s --help --fullname"%(interpreter.Path,startup_file.filePath)
        output = utils.GetCommandOutput(cmd,cwd=self.GetPath())
        fullname = output.strip()
        utils.get_logger().info("interpreter %s minorversion is %s--------------",interpreter.Name,interpreter.MinorVersion)
        if not interpreter.MinorVersion:
            interpreter.GetMinorVersion()
            interpretermanager.InterpreterManager().SavePythonInterpretersConfig()
        egg_path = "%s/%s-py%s.egg"%(dist_path,fullname,interpreter.MinorVersion)
        plugin_name = fullname.split("-")[0]
        version = fullname.split("-")[1]
        return egg_path,plugin_name,version
        
    def CleanOutput(self):
        egg_path = self.GetEgg()[0]
        utils.get_logger().info('egg path is %s----------',egg_path)
        self.Cleanfile(egg_path)
        
    def SaveBuildConfiguration(self,main_module_file,configuration_name,build_args,interpreter_name):
        file_configuration = runconfiguration.FileConfiguration(self,main_module_file)
        file_configuration_list = [configuration_name]
        pj_file_key = file_configuration.GetRootKeyPath()
        #update file configuration list
        utils.profile_set(pj_file_key + "/ConfigurationList",file_configuration_list)
        args = {
            runconfiguration.StartupConfiguration.CONFIGURATION_NAME:runconfiguration.StartupConfiguration(self,main_module_file, 0, ''),
            runconfiguration.AugumentsConfiguration.CONFIGURATION_NAME:runconfiguration.AugumentsConfiguration(self,main_module_file,'',build_args),
            runconfiguration.InterpreterConfiguration.CONFIGURATION_NAME:runconfiguration.InterpreterConfiguration(self,main_module_file,interpreter_name),
            runconfiguration.EnvironmentConfiguration.CONFIGURATION_NAME:runconfiguration.EnvironmentConfiguration(self,main_module_file,{}),
        }
        
        run_configuration = runconfiguration.RunConfiguration(configuration_name,**args)
        run_configuration.SaveConfiguration()
        run_configuration_name = "setup.py/" + configuration_name
        utils.profile_set(self.GetKey() + "/ConfigurationList",[run_configuration_name])
        utils.profile_set(self.GetKey()  + "/RunConfigurationName",run_configuration_name)
        

class NovalPluginProjectDocument(PyPIProjectDocument):
    
    @staticmethod
    def GetProjectModel():
        return NovalPluginProject()

class PyPIProjectTemplate(PythonProjectTemplate):
    @staticmethod
    def CreateProjectTemplate():
        projectTemplate = PyPIProjectTemplate(GetApp().GetDocumentManager(),
                _("Project File"),
                "*%s" % consts.PROJECT_EXTENSION,
                os.getcwd(),
                consts.PROJECT_EXTENSION,
                "PyPIProject Document",
                _("PyPIProject Viewer"),
                PyPIProjectDocument,
                PythonProjectView,
                icon = imageutils.getProjectIcon())
        GetApp().GetDocumentManager().DisassociateTemplate(projectTemplate)
        return projectTemplate
        
    def GetPropertiPages(self):
        return PythonProjectTemplate.GetPropertiPages(self) + [("PyPI option","file","pypi.pypi.PyPIOptionPanel")]
        

class NovalPluginProjectTemplate(PyPIProjectTemplate):
    @staticmethod
    def CreateProjectTemplate():
        projectTemplate = NovalPluginProjectTemplate(GetApp().GetDocumentManager(),
                _("Project File"),
                "*%s" % consts.PROJECT_EXTENSION,
                os.getcwd(),
                consts.PROJECT_EXTENSION,
                "NovalPluginProject Document",
                _("NovalPluginProject Viewer"),
                NovalPluginProjectDocument,
                PythonProjectView,
                icon = imageutils.getProjectIcon())
        GetApp().GetDocumentManager().DisassociateTemplate(projectTemplate)
        return projectTemplate
        
    def GetPropertiPages(self):
        return PythonProjectTemplate.GetPropertiPages(self) + [("PyPI option","file","pypi.pypi.NovalPluginOptionPanel")]

class PypiProjectNameLocationPage(BasePythonProjectNameLocationPage):

    def __init__(self,master,**kwargs):
        BasePythonProjectNameLocationPage.__init__(self,master,**kwargs)
        self.can_finish = False
        
    def GetProjectTemplate(self):
        return PyPIProjectTemplate.CreateProjectTemplate()
        

class NovalPluginProjectNameLocationPage(PypiProjectNameLocationPage):
    
    def GetProjectTemplate(self):
        return NovalPluginProjectTemplate.CreateProjectTemplate()
        

class PypiPackageInformationPage(projectwizard.BitmapTitledContainerWizardPage):
    """Creates the pypi interface
    @todo: Dissable << and >> when floating values are present
    @todo: When integer values overflow display convert to scientific notation
    @todo: Keybindings to numpad and enter key

    """
    def __init__(self, parent):
        """Initialiases the calculators main interface"""
        projectwizard.BitmapTitledContainerWizardPage.__init__(self, parent,("PyPI Project Wizard"),_("PyPI Package Information\nPlease Set Base Information of PyPI Package"),"python_logo.png")
        self.can_finish = True
        self.template_file = 'package_template.tar.bz2'
        
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        
        sizer_frame.columnconfigure(1, weight=1)

        ttk.Label(sizer_frame,text=_('Package Name:')).grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.name_var)
        name_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Package Version:')).grid(column=0, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.version_var = tk.StringVar()
        version_entry = ttk.Entry(sizer_frame,textvariable=self.version_var)
        version_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
      
        ttk.Label(sizer_frame,text=_('Package Description:')).grid(column=0, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.description_var = tk.StringVar()
        description_entry = ttk.Entry(sizer_frame,textvariable=self.description_var)
        description_entry.grid(column=1, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Package Author:')).grid(column=0, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.author_var = tk.StringVar()
        author_entry = ttk.Entry(sizer_frame,textvariable=self.author_var)
        author_entry.grid(column=1, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Author Email:')).grid(column=0, row=4, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(sizer_frame,textvariable=self.email_var)
        email_entry.grid(column=1, row=4, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Package Website:')).grid(column=0, row=5, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.website_var = tk.StringVar()
        website_entry = ttk.Entry(sizer_frame,textvariable=self.website_var)
        website_entry.grid(column=1, row=5, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,consts.DEFAUT_CONTRL_PAD_Y))
        return sizer_frame
        
    def Validate(self):
        if self.name_var.get().strip() == "":
            messagebox.showerror(GetApp().GetAppName(),_("Please provide a package name."),parent=self)
            return False
            
        if self.version_var.get().strip() == "":
            messagebox.showerror(GetApp().GetAppName(),_("Please provide a package version."),parent=self)
            return False
        return True
        
    def ReplaceLine(self,line,variable_name,variable_value):
        if line.find(variable_name) != -1:
            line = line.replace(variable_name,variable_value)
        return line
        
    def ReplaceVariableLine(self,line):
        next_page = self.GetNext()
        line = self.ReplaceLine(line,'{name}',self.name_var.get())
        line = self.ReplaceLine(line,'{version}',self.version_var.get())
        line = self.ReplaceLine(line,'{description}',self.description_var.get())
        line = self.ReplaceLine(line,'{author}',self.author_var.get())
        line = self.ReplaceLine(line,'{email}',self.email_var.get())
        line = self.ReplaceLine(line,'{url}',self.website_var.get())
        if next_page is not None:
            line = self.ReplaceLine(line,'{license}',next_page.license_var.get())
            line = self.ReplaceLine(line,'{keywords}',next_page.GetKeywords())
            line = self.ReplaceLine(line,'{install_requires}',next_page.GetInstallRequires())
            line = self.ReplaceLine(line,'{classifiers}',next_page.GetClassifiers())
        return line
        
    def GetBuildArgs(self):
        return 'sdist'
        
    def GetRunConfigurationName(self):
        return self.GetBuildArgs()

    def Finish(self):
        path = resource_filename(__name__,'')
        content_zip_path = os.path.join(path,self.template_file)
        prev_page = self.GetPrev()
        project_path = prev_page.GetProjectLocation()
        setup_path = os.path.join(project_path,"setup.py")
        view = GetApp().MainFrame.GetProjectView().GetView()
        doc = view.GetDocument()
        try:
            with open(setup_path,"w") as fp:
                try:
                    with BZ2File(content_zip_path,"r") as f:
                        for i,line in enumerate(f):
                            if i == 0:
                                continue
                            if utils.is_py3_plus():
                                line = compat.ensure_string(line)
                            line = self.ReplaceVariableLine(line)
                            fp.write(line.strip('\0').strip('\r').strip('\n'))
                            fp.write('\n')
                except Exception as e:
                    utils.get_logger().exception('')
                    messagebox.showerror(GetApp().GetAppName(),_("Load File Template Content Error.%s") % e)
                    return False
            folderPath =  self.name_var.get().lower()
            destpackagePath = os.path.join(project_path,folderPath)
            dirutils.MakeDirs(destpackagePath)
            doc.GetCommandProcessor().Submit(command.ProjectAddPackagefolderCommand(view, doc,folderPath))
            self.destpackageFile = os.path.join(destpackagePath,PythonProjectView.PACKAGE_INIT_FILE)
            with open(self.destpackageFile,"w") as f:
                doc.GetCommandProcessor().Submit(command.ProjectAddFilesCommand(doc,[self.destpackageFile],folderPath))
            doc.GetCommandProcessor().Submit(command.ProjectAddFilesCommand(doc,[setup_path],None))
            main_module_file = doc.GetModel().FindFile(setup_path)
            doc.SaveBuildConfiguration(main_module_file,self.GetRunConfigurationName(),self.GetBuildArgs(),prev_page.interpreter_entry_var.get())
        except Exception as e:
            utils.get_logger().exception('')
            messagebox.showerror(GetApp().GetAppName(),_("New File Error.%s") % e)
            return False
        view.SetProjectStartupFile()
        return True
        

class PypiPackageToolInformationPage(PypiPackageInformationPage):
    
    def __init__(self, parent):
        PypiPackageInformationPage.__init__(self,parent)
        self.template_file = 'package_tool_template.tar.bz2'
    
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = PypiPackageInformationPage.CreateContent(self,content_frame,**kwargs)
        ttk.Label(sizer_frame,text=_('Environment:')).grid(column=0, row=6, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        environments = ('Console','GUI')
        self.environment_var = tk.StringVar(value=environments[0])
        environment_entry = ttk.Combobox(sizer_frame,textvariable=self.environment_var,values=environments,state="readonly")
        environment_entry.grid(column=1, row=6, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        ttk.Label(sizer_frame,text=_('Tool Name:')).grid(column=0, row=7, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,consts.DEFAUT_CONTRL_PAD_Y))
        self.tool_name_var = tk.StringVar()
        tool_entry = ttk.Entry(sizer_frame,textvariable=self.tool_name_var)
        misc.create_tooltip(tool_entry,_('the executable name of package tool'))
        tool_entry.grid(column=1, row=7, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,consts.DEFAUT_CONTRL_PAD_Y))
        
    def ReplaceVariableLine(self,line):
        line = PypiPackageInformationPage.ReplaceVariableLine(self,line)
        if self.environment_var.get() == 'Console':
            entry_point = "console_scripts"
        else:
            entry_point = "gui_scripts"
        line = self.ReplaceLine(line,'{entry_point}',entry_point)
        line = self.ReplaceLine(line,'{tool_name}',self.tool_name_var.get())
        line = self.ReplaceLine(line,'{module_name}',self.name_var.get().lower())
        line = self.ReplaceLine(line,'{module_func}',"main")
        return line
        
    def Validate(self):
        if not PypiPackageInformationPage.Validate(self):
            return False
        if self.tool_name_var.get().strip() == "":
            messagebox.showerror(GetApp().GetAppName(),_("Please provide a package tool name."),parent=self)
            return False
        return True        

class NovalPluginInformationPage(PypiPackageInformationPage):
    
    plugin_template_content = '''from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants


class {PluginName}Plugin(plugin.Plugin):
    """plugin description here..."""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing {PluginName} plugin")
        

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """

    def InstallHook(self):
        """Override in subclasses to allow the plugin to be loaded
        dynamically.
        @return: None

        """
        pass

    def UninstallHook(self):
        pass

    def EnableHook(self):
        pass
        
    def DisableHook(self):
        pass
        
    def GetFree(self):
        return True
        
    def GetPrice(self):
        pass
    '''
    
    def __init__(self, parent):
        """Initialiases the calculators main interface"""
        projectwizard.BitmapTitledContainerWizardPage.__init__(self, parent,("Noval Plugin Wizard"),_("Noval Plugin Information\nPlease Set Base Information of Noval Plugin"),"python_logo.png")
        self.can_finish = True
        self.template_file = 'package_tool_template.tar.bz2'
    
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        
        sizer_frame.columnconfigure(1, weight=1)

        ttk.Label(sizer_frame,text=_('Plugin Name:')).grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.name_var)
        name_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Plugin Version:')).grid(column=0, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.version_var = tk.StringVar()
        version_entry = ttk.Entry(sizer_frame,textvariable=self.version_var)
        version_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
      
        ttk.Label(sizer_frame,text=_('Plugin Description:')).grid(column=0, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.description_var = tk.StringVar()
        description_entry = ttk.Entry(sizer_frame,textvariable=self.description_var)
        description_entry.grid(column=1, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Plugin Author:')).grid(column=0, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.author_var = tk.StringVar()
        author_entry = ttk.Entry(sizer_frame,textvariable=self.author_var)
        author_entry.grid(column=1, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Author Email:')).grid(column=0, row=4, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(sizer_frame,textvariable=self.email_var)
        email_entry.grid(column=1, row=4, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Plugin Website:')).grid(column=0, row=5, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.website_var = tk.StringVar()
        website_entry = ttk.Entry(sizer_frame,textvariable=self.website_var)
        website_entry.grid(column=1, row=5, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,consts.DEFAUT_CONTRL_PAD_Y))
        return sizer_frame

    def ReplaceVariableLine(self,line):
        line = PypiPackageInformationPage.ReplaceVariableLine(self,line)
        line = self.ReplaceLine(line,'{license}','Mulan')
        line = self.ReplaceLine(line,'{keywords}','')
        line = self.ReplaceLine(line,'{install_requires}','[]')
        line = self.ReplaceLine(line,'{classifiers}','')
        line = self.ReplaceLine(line,'{entry_point}','Noval.plugins')
        line = self.ReplaceLine(line,'{tool_name}',self.name_var.get().strip())
        line = self.ReplaceLine(line,'{module_name}',self.name_var.get().strip().lower())
        line = self.ReplaceLine(line,'{module_func}',self.name_var.get().strip() + "Plugin")
        return line
        
    def Finish(self):
        PypiPackageInformationPage.Finish(self)
        with open(self.destpackageFile,"w") as f:
            content = self.plugin_template_content.format(PluginName=self.name_var.get().strip())
            f.write(content)
        return True
        
    def GetBuildArgs(self):
        return 'bdist_egg'
        
    def GetRunConfigurationName(self):
        return "bdist_novalplugin_egg"
        

class NovalFileExtensionPluginInformationPage(NovalPluginInformationPage):
    plugin_template_content = NovalPluginInformationPage.plugin_template_content + '''
    def GetFileExtension(self):
        return '{file_extension}'
    '''
    
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = NovalPluginInformationPage.CreateContent(self,content_frame,**kwargs)
        ttk.Label(sizer_frame,text=_('File Extension:')).grid(column=0, row=6, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.file_extension_var = tk.StringVar()
        file_extension_entry = ttk.Entry(sizer_frame,textvariable=self.file_extension_var)
        file_extension_entry.grid(column=1, row=6, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,consts.DEFAUT_CONTRL_PAD_Y))
        
    def Finish(self):
        PypiPackageInformationPage.Finish(self)
        with open(self.destpackageFile,"w") as f:
            content = self.plugin_template_content.format(PluginName=self.name_var.get().strip(),file_extension=self.file_extension_var.get().strip())
            f.write(content)
        return True
        
class PypiOptionPage(projectwizard.BitmapTitledContainerWizardPage):
    """Creates the calculators interface
    @todo: Dissable << and >> when floating values are present
    @todo: When integer values overflow display convert to scientific notation
    @todo: Keybindings to numpad and enter key

    """
    def __init__(self, parent):
        """Initialiases the calculators main interface"""
        projectwizard.BitmapTitledContainerWizardPage.__init__(self, parent,("PyPI Project Wizard"),_("Setup Options\nPlease Specify option of your package setup"),"python_logo.png")
        self.can_finish = True
        
    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        
        sizer_frame.columnconfigure(1, weight=1)
  
        ttk.Label(sizer_frame,text=_('Keywords:')).grid(column=0, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(sizer_frame,textvariable=self.keyword_var)
        misc.create_tooltip(keyword_entry,_('multi keywords seperated by comma'))
        keyword_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        ttk.Label(sizer_frame,text=_('Require Packages:')).grid(column=0, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.install_requires_var = tk.StringVar()
        install_requires_entry = ttk.Entry(sizer_frame,textvariable=self.install_requires_var)
        misc.create_tooltip(install_requires_entry,_('multi packages seperated by comma'))
        install_requires_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('License:')).grid(column=0, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.license_var = tk.StringVar()
        licenses = ('GPL','LGPL','AGPL','Apache','MIT','BSD','EPL','MPL','Mulan')
        license_entry = ttk.Combobox(sizer_frame,textvariable=self.license_var,values=licenses)
        license_entry.grid(column=1, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        ttk.Label(sizer_frame,text=_('Python Version:')).grid(column=0, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        versions = ('2.7','3','3.5','3.6','3.7')
        check_listbox_view = treeviewframe.TreeViewFrame(sizer_frame,treeview_class=checklistbox.CheckListbox,borderwidth=1,relief="solid",height=4)
        self.version_listbox = check_listbox_view.tree
        check_listbox_view.grid(column=1, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        for version in versions:
            self.version_listbox.Append('Python '+version)
            
        ttk.Label(sizer_frame,text=_('Os Platform:')).grid(column=0, row=4, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        platforms = ('OS Independent','Windows','MacOS','Linux')
        check_listbox_view = treeviewframe.TreeViewFrame(sizer_frame,treeview_class=checklistbox.CheckListbox,borderwidth=1,relief="solid",height=4)
        self.platform_listbox = check_listbox_view.tree
        check_listbox_view.grid(column=1, row=4, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        for platform in platforms:
            self.platform_listbox.Append(platform)
        
        ttk.Label(sizer_frame,text=_('Package Long Description:')).grid(column=0, row=5, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        text_frame = textframe.TextFrame(sizer_frame,text_class=texteditor.TextCtrl,height=10,show_scrollbar=False,borderwidth=1,relief="solid")
        self.description_text = text_frame.text
        text_frame.grid(column=1, row=5, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

    def Finish(self):
        return True

    def GetClassifiers(self):
        classifiers =  [
            'Development Status :: 4 - Beta',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy'
        ]
        classifiers.extend(self.GetOperatingSystem())
        classifiers.extend(self.GetPythonVersions())
        output = cStringIO.StringIO()
        json.dump(classifiers,output,indent=12)
        return output.getvalue().lstrip('[').rstrip(']').strip()
        
    def GetInstallRequires(self):
        return str(self.install_requires_var.get().split(','))
        
    def GetKeywords(self):
        return ' '.join(self.keyword_var.get().split(','))
        
    def GetOperatingSystem(self):
        op_strs = []
        for i in range(self.platform_listbox.GetCount()):
            if self.platform_listbox.IsChecked(i):
                op_str = 'Operating System :: %s'%self.platform_listbox.GetString(i)
                op_strs.append(op_str)
        return op_strs
        
    def GetPythonVersions(self):
        version_strs = []
        for i in range(self.version_listbox.GetCount()):
            if self.version_listbox.IsChecked(i):
                ver_str = 'Programming Language :: Python :: %s'%self.version_listbox.GetString(i).replace('Python ',"")
                version_strs.append(ver_str)
        return version_strs