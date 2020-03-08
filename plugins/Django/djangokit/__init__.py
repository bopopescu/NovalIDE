from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
import djangokit.django as dj
from noval.project.templatemanager import ProjectTemplateManager
import os
from tkinter import ttk,messagebox
import noval.consts as consts
import noval.menu as tkmenu
import tkinter.simpledialog as tkSimpleDialog
import noval.project.command as command

class DjangoPlugin(plugin.Plugin):
    """plugin description here..."""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing Django plugin....")
        ProjectTemplateManager().AddProjectTemplate("Python/Web",_("Django"),[(dj.DjangoProjectNameLocationPage,{'startup_path':'${ProjectDir}/manage.py','enable_set_startup':False,'project_dir_checked':False,'enable_create_project_dir':False}),dj.DjangoInformationPage])
        GetApp().bind(constants.PROJECTVIEW_POPUP_ROOT_MENU_EVT, self.AppenRootMenu,True)
        
    def AppenRootMenu(self, event):
        menu = event.get('menu')
        if self.GetProjectDocument().__class__.__name__ != "DjangoProjectDocument":
            submenu = menu.GetMenuByname(_("Convert to"))
            if not submenu:
                menu.add_separator()
                submenu = tkmenu.PopupMenu()
                menu.AppendMenu(NewId(),_("Convert to"),submenu)
            submenu.Append(NewId(),_("Django Project"),handler=self.Convertto) 
        else:
            submenu = tkmenu.PopupMenu()
            menu.AppendMenu(NewId(),_("Django"),submenu)
            submenu.Append(NewId(),_("New app"),handler=self.NewApp)
            submenu.Append(NewId(),_("Run in debugger"),handler=self.RunIndebugger)
            submenu.Append(NewId(),_("Run in terminal"),handler=self.RunInterminal)
            submenu.Append(NewId(),_("Configuration"),handler=self.Configuration)
            
    def Configuration(self):
        self.GetProjectFrame().OnProjectProperties(item_name="Django option")
            
    def NewApp(self):
        app_name = tkSimpleDialog.askstring(
            "New App",
            "Provide app name",
        )
        if not app_name:
            return
        doc = self.GetProjectDocument()
        doc.NewApp(app_name)

    def RunIndebugger(self):
        ''''''
        self.GetProjectDocument().RunIndebugger()
        
    def RunInterminal(self):
        ''''''
        self.GetProjectDocument().RunInterminal()

        
    def Convertto(self):
        find = False
        project_doc = self.GetProjectDocument()
        for root,dir,files in os.walk(project_doc.GetPath()):
            for filename in files:
                if filename == "manage.py":
                    fullpath = os.path.join(root,filename)
                    if messagebox.askyesno(GetApp().GetAppName(),"Does file '%s' is the startup file of your django project?"%fullpath):
                        item = self.GetProjectFrame().GetView()._treeCtrl.FindItem(fullpath)
                        self.GetProjectFrame().GetView()._treeCtrl.selection_set(item)
                        self.GetProjectFrame().GetView().SetProjectStartupFileItem(item)
                        find = True
                    break
        if not find:
            messagebox.showerror(GetApp().GetAppName(),"could not find manage.py in your project!!")
            return
        project_doc.GetModel()._runinfo.DocumentTemplate = "djangokit.django.DjangoProjectTemplate"
        project_doc.Modify(True)
        project_doc.Save()
        assert(project_doc.NeedConvertto(project_doc.GetModel()))
        project_doc.ConvertTo(project_doc.GetModel(),project_doc.GetFilename())
        self.GetProjectFrame().GetView().SetDocument(project_doc)
        self.GetProjectFrame().CloseProject()
        
        project_doc = self.GetProjectDocument()
        project_doc.SaveDebugRunConfiguration()

    def GetProjectFrame(self):
        return GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME)
        
    def GetProjectDocument(self):
        project_browser = self.GetProjectFrame()
        return project_browser.GetView().GetDocument()
            
    def GetMinVersion(self):
        return '1.2.1'

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
    