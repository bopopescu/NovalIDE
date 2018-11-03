#----------------------------------------------------------------------------
# Name:         IDE.py
# Purpose:      IDE using Python extensions to the wxWindows docview framework
#
# Author:       Peter Yared
#
# Created:      5/15/03
# Copyright:    (c) 2003-2005 ActiveGrid, Inc.
# CVS-ID:       $Id$
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.lib.docview
import wx.lib.pydocview
import sys
import wx.grid
import os.path
import noval.util.sysutils as sysutilslib
import noval.util.appdirs as appdirs
import noval.util.logger as logger
import shutil
import interpreter.InterpreterManager as interpretermanager,interpreter.Interpreter as Interpreter
import noval.parser.intellisence as intellisence
import noval.tool.syntax.lang as lang
from consts import _,ID_MRU_FILE1,PROJECT_EXTENSION,\
        PROJECT_SHORT_EXTENSION,DEFAULT_MRU_FILE_NUM,CHECK_UPDATE_ATSTARTUP_KEY,DEFAULT_DOCUMENT_TYPE_NAME,\
        APPLICATION_NAME,DEBUG_APPLICATION_NAME
from noval.util import strutils
import noval.parser.utils as parserutils
from noval.dummy.userdb import UserDataDb
from noval.tool.syntax import synglob
import images
from noval.util import utils
import NewDocument

# Required for Unicode support with python
# site.py sets this, but Windows builds don't have site.py because of py2exe problems
# If site.py has already run, then the setdefaultencoding function will have been deleted.
if hasattr(sys,"setdefaultencoding"):
    sys.setdefaultencoding("utf-8")

ACTIVEGRID_BASE_IDE = False 
USE_OLD_PROJECTS = False
#----------------------------------------------------------------------------
# Helper functions for command line args
#----------------------------------------------------------------------------

# Since Windows accept command line options with '/', but this character
# is used to denote absolute path names on other platforms, we need to
# conditionally handle '/' style arguments on Windows only.
def printArg(argname):
    output = "'-" + argname + "'"
    if wx.Platform == "__WXMSW__":
        output = output + " or '/" + argname + "'"        
    return output
        
def isInArgs(argname, argv):
    result = False
    if ("-" + argname) in argv:
        result = True
    if wx.Platform == "__WXMSW__" and ("/" + argname) in argv:
        result = True        
    return result

# The default log action in wx is to prompt with a big message box
# which is often inappropriate (for example, if the clipboard data
# is not readable on Mac, we'll get one of these messages repeatedly)
# so just log the errors instead.
# NOTE: This does NOT supress fatal system errors. Only non-fatal ones.
class AppLog(wx.PyLog):
    def __init__(self):
        wx.PyLog.__init__(self)
        self.items = []
        
    def DoLogString(self, message, timeStamp):
        self.items.append(str(timeStamp) + u" " + message.decode())

#----------------------------------------------------------------------------
# Classes
#----------------------------------------------------------------------------
class IDEApplication(wx.lib.pydocview.DocApp):

    def __init__(self, redirect=False):
        wx.lib.pydocview.DocApp.__init__(self, redirect=redirect)

    def OnInit(self):
        global ACTIVEGRID_BASE_IDE
        global USE_OLD_PROJECTS
        args = sys.argv

        #init ide logger
        log_mode = logger.LOG_MODE_IDE

        # Suppress non-fatal errors that might prompt the user even in cases
        # when the error does not impact them.
        #the log will redirect to NovalIDE.exe.log when convert into windows exe with py2exe
        wx.Log_SetActiveTarget(AppLog())
        if "-h" in args or "-help" in args or "--help" in args\
            or (wx.Platform == "__WXMSW__" and "/help" in args):
            print "Usage: ActiveGridAppBuilder.py [options] [filenames]\n"
            # Mac doesn't really support multiple instances for GUI apps
            # and since we haven't got time to test this thoroughly I'm 
            # disabling it for now.
            if wx.Platform != "__WXMAC__":
                print "    option " + printArg("multiple") + " to allow multiple instances of application."
            print "    option " + printArg("debug") + " for debug mode."
            print "    option '-h' or " + printArg("help") + " to show usage information for command."
            print "    option " + printArg("baseide") + " for base IDE mode."
            print "    [filenames] is an optional list of files you want to open when application starts."
            return False
        elif isInArgs("dev", args):
            self.SetAppName("NovalBuilderDev")
            self.SetDebug(False)
        elif isInArgs("debug", args):
            self.SetAppName(DEBUG_APPLICATION_NAME)
            self.SetDebug(True)
            ACTIVEGRID_BASE_IDE = True
            log_mode = logger.LOG_MODE_TESTRUN
            self.SetSingleInstance(False)
        elif isInArgs("baseide", args):
            self.SetAppName(APPLICATION_NAME)
            ACTIVEGRID_BASE_IDE = True
        elif isInArgs("tools", args):
            USE_OLD_PROJECTS = True
        else:
            self.SetAppName(APPLICATION_NAME)
            self.SetDebug(False)
        if isInArgs("multiple", args) and wx.Platform != "__WXMAC__":
            self.SetSingleInstance(False)
            
        logger.initLogging(log_mode)
           
        if not wx.lib.pydocview.DocApp.OnInit(self):
            return False

        self.ShowSplash(getIDESplashBitmap())

        import STCTextEditor
        import service.TextService as TextService
        import service.FindInDirService as FindInDirService
        import service.MarkerService as MarkerService
        import project.project as projectlib
        import project.ProjectEditor as ProjectEditor
        import PythonEditor
        import service.OutlineService as OutlineService
        import XmlEditor
        import HtmlEditor
        import service.MessageService as MessageService
        import ImageEditor
        import PerlEditor
        import wx.lib.ogl as ogl
        import debugger.DebuggerService as DebuggerService
        import AboutDialog
        import service.SVNService as SVNService
        import service.ExtensionService as ExtensionService
        import service.CompletionService as CompletionService
        import GeneralOption
        import service.OptionService as OptionService
        import service.navigation.NavigationService as NavigationService
        import TabbedFrame
        import interpreter.InterpreterConfigruation as interpreterconfigruation
        import interpreter.GeneralConfiguration as generalconfiguration
        import ColorFont
        import project.Property as Property
        import service.logs.LogService as LogService
                            
        _EDIT_LAYOUTS = True
        self._open_project_path = None                        

        # This creates some pens and brushes that the OGL library uses.
        # It should be called after the app object has been created, but
        # before OGL is used.
        ogl.OGLInitialize()

        config = wx.Config(self.GetAppName(), style = wx.CONFIG_USE_LOCAL_FILE)
        if not config.Exists("MDIFrameMaximized"):  # Make the initial MDI frame maximize as default
            config.WriteInt("MDIFrameMaximized", True)
        # Make the outline embedded window show as default
        if not config.ReadInt("MDIEmbedRightVisible",True) and config.ReadInt("OutlineShown",True):
            config.WriteInt("MDIEmbedRightVisible", True)

        ##my_locale must be set as app member property,otherwise it will only workable when app start up
        ##it will not workable after app start up,the translation also will not work
        lang_id = GeneralOption.GetLangId(config.Read("Language",sysutilslib.GetLangConfig()))
        if wx.Locale.IsAvailable(lang_id):
            self.my_locale = wx.Locale(lang_id)
            if self.my_locale.IsOk():
                self.my_locale.AddCatalogLookupPathPrefix(os.path.join(sysutilslib.mainModuleDir,'noval','locale'))
                ibRet = self.my_locale.AddCatalog(APPLICATION_NAME.lower())
                ibRet = self.my_locale.AddCatalog("wxstd")
                self.my_locale.AddCatalog("wxstock")

        docManager = IDEDocManager(flags = self.GetDefaultDocManagerFlags())
        self.SetDocumentManager(docManager)

        # Note:  These templates must be initialized in display order for the "Files of type" dropdown for the "File | Open..." dialog
        defaultTemplate = wx.lib.docview.DocTemplate(docManager,
                _("Any File"),
                "*.*",
                os.getcwd(),
                ".txt",
                "Text Document",
                _("Text Editor"),
                STCTextEditor.TextDocument,
                STCTextEditor.TextView,
                wx.lib.docview.TEMPLATE_INVISIBLE,
                icon = images.getBlankIcon())
        docManager.AssociateTemplate(defaultTemplate)
        
        webViewTemplate = wx.lib.docview.DocTemplate(docManager,
                _("WebView"),
                "*.com;*.org",
                os.getcwd(),
                ".com",
                "WebView Document",
                _("Internal Web Browser"),
                HtmlEditor.WebDocument,
                HtmlEditor.WebView,
                wx.lib.docview.TEMPLATE_INVISIBLE,
                icon = images.getWebIcon())
        docManager.AssociateTemplate(webViewTemplate)

        imageTemplate = wx.lib.docview.DocTemplate(docManager,
                _("Image File"),
                "*.bmp;*.ico;*.gif;*.jpg;*.jpeg;*.png",
                os.getcwd(),
                ".png",
                "Image Document",
                _("Image Viewer"),
                ImageEditor.ImageDocument,
                ImageEditor.ImageView,
                #could not be newable
                wx.lib.docview.TEMPLATE_NO_CREATE,
                icon = ImageEditor.getImageIcon())
        docManager.AssociateTemplate(imageTemplate)

        projectTemplate = ProjectEditor.ProjectTemplate(docManager,
                _("Project File"),
                "*%s" % PROJECT_EXTENSION,
                os.getcwd(),
                PROJECT_EXTENSION,
                "Project Document",
                _("Project Resolver"),
                ProjectEditor.ProjectDocument,
                ProjectEditor.ProjectView,
             ###   wx.lib.docview.TEMPLATE_NO_CREATE,
                icon = ProjectEditor.getProjectIcon())
        docManager.AssociateTemplate(projectTemplate)
        
        synglob.LexerFactory().CreateLexerTemplates(docManager)
        
        pythonService           = self.InstallService(PythonEditor.PythonService("Python Interpreter",embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        if not ACTIVEGRID_BASE_IDE:
            propertyService     = self.InstallService(PropertyService.PropertyService("Properties", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT))
        projectService          = self.InstallService(ProjectEditor.ProjectService("Projects/Resources View", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_LEFT))
        findService             = self.InstallService(FindInDirService.FindInDirService())
        if not ACTIVEGRID_BASE_IDE:
            webBrowserService   = self.InstallService(WebBrowserService.WebBrowserService())  # this must be before webServerService since it sets the proxy environment variable that is needed by the webServerService.
            webServerService    = self.InstallService(WebServerService.WebServerService())  # this must be after webBrowserService since that service sets the proxy environment variables.
        outlineService          = self.InstallService(OutlineService.OutlineService("Outline", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT))
        filePropertiesService   = self.InstallService(Property.FilePropertiesService())
        markerService           = self.InstallService(MarkerService.MarkerService())
        textService             = self.InstallService(TextService.TextService())
        perlService             = self.InstallService(PerlEditor.PerlService())
        comletionService        = self.InstallService(CompletionService.CompletionService())
        navigationService       = self.InstallService(NavigationService.NavigationService())
        messageService          = self.InstallService(MessageService.MessageService("Search Results", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
    ##    outputService          = self.InstallService(OutputService.OutputService("Output", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        debuggerService         = self.InstallService(DebuggerService.DebuggerService("Debugger", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        extensionService        = self.InstallService(ExtensionService.ExtensionService())
        optionsService          = self.InstallService(OptionService.OptionsService())
        aboutService            = self.InstallService(wx.lib.pydocview.AboutService(AboutDialog.AboutDialog))
     ###   svnService              = self.InstallService(SVNService.SVNService())
        if not ACTIVEGRID_BASE_IDE:
            helpPath = os.path.join(sysutilslib.mainModuleDir, "activegrid", "tool", "data", "AGDeveloperGuideWebHelp", "AGDeveloperGuideWebHelp.hhp")
            helpService             = self.InstallService(HelpService.HelpService(helpPath))
        if self.GetUseTabbedMDI():
            windowService       = self.InstallService(wx.lib.pydocview.WindowMenuService())
        if wx.GetApp().GetDebug():
            loggingService          = self.InstallService(LogService.LogService())
        
        # order of these added determines display order of Options Panels
        optionsService.AddOptionsPanel(OptionService.ENVIRONMENT_OPTION_NAME,OptionService.PROJECT_ITEM_NAME,ProjectEditor.ProjectOptionsPanel)
       ## optionsService.AddOptionsPanel(DebuggerService.DebuggerOptionsPanel)
        optionsService.AddOptionsPanel(OptionService.ENVIRONMENT_OPTION_NAME,OptionService.TEXT_ITEM_NAME,STCTextEditor.TextOptionsPanel)
        optionsService.AddOptionsPanel(OptionService.ENVIRONMENT_OPTION_NAME,OptionService.FONTS_CORLORS_ITEM_NAME,ColorFont.ColorFontOptionsPanel)
        optionsService.AddOptionsPanel(OptionService.INTERPRETER_OPTION_NAME,OptionService.GENERAL_ITEM_NAME,generalconfiguration.InterpreterGeneralConfigurationPanel)
        optionsService.AddOptionsPanel(OptionService.INTERPRETER_OPTION_NAME,OptionService.INTERPRETER_CONFIGURATIONS_ITEM_NAME,interpreterconfigruation.InterpreterConfigurationPanel)
  ##      optionsService.AddOptionsPanel(SVNService.SVNOptionsPanel)
        optionsService.AddOptionsPanel(OptionService.OTHER_OPTION_NAME,OptionService.EXTENSION_ITEM_NAME,ExtensionService.ExtensionOptionsPanel)

        filePropertiesService.AddCustomEventHandler(projectService)

        outlineService.AddViewTypeForBackgroundHandler(PythonEditor.PythonView)
        outlineService.AddViewTypeForBackgroundHandler(ProjectEditor.ProjectView) # special case, don't clear outline if in project
        outlineService.AddViewTypeForBackgroundHandler(MessageService.MessageView) # special case, don't clear outline if in message window
        if not ACTIVEGRID_BASE_IDE:
            outlineService.AddViewTypeForBackgroundHandler(DataModelEditor.DataModelView)
            outlineService.AddViewTypeForBackgroundHandler(ProcessModelEditor.ProcessModelView)
            outlineService.AddViewTypeForBackgroundHandler(PropertyService.PropertyView) # special case, don't clear outline if in property window
        outlineService.StartBackgroundTimer()
    
        iconPath = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "noval.ico")
        self.SetDefaultIcon(wx.Icon(iconPath, wx.BITMAP_TYPE_ICO))
        if not ACTIVEGRID_BASE_IDE:
            embeddedWindows = wx.lib.pydocview.EMBEDDED_WINDOW_TOPLEFT | wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOMLEFT |wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM | wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT
        else:
            embeddedWindows = wx.lib.pydocview.EMBEDDED_WINDOW_LEFT | wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT |wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM
        if self.GetUseTabbedMDI():
            self.frame = TabbedFrame.IDEDocTabbedParentFrame(docManager, None, -1, wx.GetApp().GetAppName(), embeddedWindows=embeddedWindows, minSize=150)
        else:
            self.frame = TabbedFrame.IDEMDIParentFrame(docManager, None, -1, wx.GetApp().GetAppName(), embeddedWindows=embeddedWindows, minSize=150)
        self.frame.Show(True)
        self.toolbar = self.frame.GetToolBar()
        self.toolbar_combox = self.toolbar.FindControl(DebuggerService.DebuggerService.COMBO_INTERPRETERS_ID)

        wx.lib.pydocview.DocApp.CloseSplash(self)
        self.OpenCommandLineArgs()
        
        if not projectService.LoadSavedProjects() and not docManager.GetDocuments() and self.IsSDI():  # Have to open something if it's SDI and there are no projects...
            projectTemplate.CreateDocument('', wx.lib.docview.DOC_NEW).OnNewDocument()
            
        interpretermanager.InterpreterManager().LoadDefaultInterpreter()
        self.AddInterpreters()
        projectService.SetCurrentProject()
        intellisence.IntellisenceManager().generate_default_intellisence_data()

        self.ShowTipfOfDay()
        if config.ReadInt(CHECK_UPDATE_ATSTARTUP_KEY, True):
            wx.CallAfter(self.CheckUpdate,extensionService)
        wx.UpdateUIEvent.SetUpdateInterval(1000)  # Overhead of updating menus was too much.  Change to update every n milliseconds.
        return True
        

    def CheckUpdate(self,extensionService):
        extensionService.CheckAppUpdate(True)

    def ShowTipfOfDay(self,must_display=False):
        docManager = self.GetDocumentManager()
        tips_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "data", "tips.txt")
        # wxBug: On Mac, having the updates fire while the tip dialog is at front
        # for some reason messes up menu updates. This seems a low-level wxWidgets bug,
        # so until I track this down, turn off UI updates while the tip dialog is showing.
        if os.path.isfile(tips_path):
            config = wx.ConfigBase_Get()
            index = config.ReadInt("TipIndex", 0)
            if must_display:
                showTip = config.ReadInt("ShowTipAtStartup", 1)
                showTipResult = wx.ShowTip(docManager.FindSuitableParent(), wx.CreateFileTipProvider(tips_path, index), showAtStartup = showTip)
                if showTipResult != showTip:
                    config.WriteInt("ShowTipAtStartup", showTipResult)
            else:
                self.ShowTip(docManager.FindSuitableParent(), wx.CreateFileTipProvider(tips_path, index))
    
    @property
    def MainFrame(self):
        return self.frame
    @property       
    def ToolbarCombox(self):
        return self.toolbar_combox
        
    def GetCurrentInterpreter(self):
        return interpretermanager.InterpreterManager.GetCurrentInterpreter()
        
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
                
    def GotoView(self,file_path,lineNum,pos=-1):
        file_path = os.path.abspath(file_path)
        foundView = utils.GetOpenView(file_path)
        if not foundView:
            doc = self.GetDocumentManager().CreateDocument(file_path, wx.lib.docview.DOC_SILENT)
            if doc is None:
                return
            foundView = doc.GetFirstView()

        if foundView:
            foundView.GetFrame().SetFocus()
            foundView.Activate()
            if not hasattr(foundView,"GotoLine"):
                return
            if pos == -1:
                foundView.GotoLine(lineNum)
                startPos = foundView.PositionFromLine(lineNum)
                lineText = foundView.GetCtrl().GetLine(lineNum - 1)
                foundView.SetSelection(startPos, startPos + len(lineText.rstrip("\n")))
            else:
                lineNum = foundView.LineFromPosition(pos)
                foundView.GetCtrl().GotoPos(pos)
            if foundView.GetLangId() == lang.ID_LANG_PYTHON:
                import service.OutlineService as OutlineService
                self.GetService(OutlineService.OutlineService).LoadOutline(foundView, lineNum=lineNum)


    def GotoViewPos(self,file_path,lineNum,col=0):
        file_path = os.path.abspath(file_path)
        foundView = utils.GetOpenView(file_path)
        if not foundView:
            doc = self.GetDocumentManager().CreateDocument(file_path, wx.lib.docview.DOC_SILENT)
            if doc is None:
                return
            foundView = doc.GetFirstView()

        if foundView:
            foundView.GetFrame().SetFocus()
            foundView.Activate()
            startPos = foundView.PositionFromLine(lineNum)
            foundView.GotoPos(startPos+col)
            if foundView.GetLangId() == lang.ID_LANG_PYTHON:
                import service.OutlineService as OutlineService
                self.GetService(OutlineService.OutlineService).LoadOutline(foundView, lineNum=lineNum)
                
    def AddInterpreters(self):
        cb = self.ToolbarCombox
        cb.Clear()
        for interpreter in interpretermanager.InterpreterManager().interpreters:
            cb.Append(interpreter.Name,interpreter)
        cb.Append(_("Configuration"),)
        self.SetCurrentInterpreter()
        
    def OnExit(self):
        intellisence.IntellisenceManager().Stop()
        UserDataDb.get_db().RecordEnd()
        wx.lib.pydocview.DocApp.OnExit(self)
        
    def ShowSplash(self, image):
        """
        Shows a splash window with the given image.  Input parameter 'image' can either be a wx.Bitmap or a filename.
        """
        wx.lib.pydocview.DocApp.ShowSplash(self,image)
        #should pause a moment to show splash image on linux os,otherwise it will show white background on linux
        wx.Yield()
    
    @property
    def OpenProjectPath(self):
        return self._open_project_path
        
    def OpenCommandLineArgs(self):
        """
        Called to open files that have been passed to the application from the
        command line.
        """
        args = sys.argv[1:]
        for arg in args:
            if (wx.Platform != "__WXMSW__" or arg[0] != "/") and arg[0] != '-' and os.path.exists(arg):
                if sysutilslib.isWindows():
                    arg = arg.decode("gbk")
                else:
                    arg = arg.decode("utf-8")
                self.GetDocumentManager().CreateDocument(os.path.normpath(arg), wx.lib.docview.DOC_SILENT)
                if strutils.GetFileExt(arg) == PROJECT_SHORT_EXTENSION:
                    self._open_project_path = arg
        

class IDEDocManager(wx.lib.docview.DocManager):

    # Overriding default document creation.
    def OnFileNew(self, event):
        self.CreateDocument('', wx.lib.docview.DOC_NEW)

    def SelectDocumentPath(self, templates, flags, save):
        """
        Under Windows, pops up a file selector with a list of filters
        corresponding to document templates. The wxDocTemplate corresponding
        to the selected file's extension is returned.

        On other platforms, if there is more than one document template a
        choice list is popped up, followed by a file selector.

        This function is used in wxDocManager.CreateDocument.
        """
        descr = ''
        for temp in templates:
            if temp.IsVisible():
                if len(descr) > 0:
                    descr = descr + '|'
                descr = descr + _(temp.GetDescription()) + " (" + temp.GetFileFilter() + ") |" + temp.GetFileFilter()  # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
        if sysutilslib.isWindows():
            descr = _("All Files") + "(*.*)|*.*|%s" % descr  # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
        else:
            descr = _("All Files") +  "(*)|*|%s" % descr 
            
        dlg = wx.FileDialog(self.FindSuitableParent(),
                               _("Select a File"),
                               wildcard=descr,
                               style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        # dlg.CenterOnParent()  # wxBug: caused crash with wx.FileDialog
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else:
            path = None
        dlg.Destroy()
            
        if path:  
            theTemplate = self.FindTemplateForPath(path)
            return (theTemplate, path)
        
        return (None, None)       

    def OnFileSaveAs(self, event):
        doc = self.GetCurrentDocument()
        if not doc:
            return
        self.SaveAsDocument(doc)
            
    def SaveAsDocument(self,doc):
        old_file_path = doc.GetFilename()
        if not doc.SaveAs():
            return
        new_file_path = doc.GetFilename()
        #if save as file is the same file as before,don't remove the old file watcher
        if doc.IsWatched and not parserutils.ComparePath(new_file_path,old_file_path):
            doc.FileWatcher.RemoveFile(old_file_path)

    def OnPrintSetup(self, event):
        data = wx.PageSetupDialogData()
        data.SetMarginTopLeft( (15, 15) )
        data.SetMarginBottomRight( (15, 15) )
        #data.SetDefaultMinMargins(True)
        data.SetPaperId(wx.PAPER_LETTER)
        dlg = wx.PageSetupDialog(wx.GetApp().GetTopWindow(), data)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetPageSetupData()
            tl = data.GetMarginTopLeft()
            br = data.GetMarginBottomRight()
        dlg.Destroy()

    def OnCreateFileHistory(self):
        """
        A hook to allow a derived class to create a different type of file
        history. Called from Initialize.
        """
        max_files = int(wx.ConfigBase_Get().Read("MRULength",str(DEFAULT_MRU_FILE_NUM)))
        enableMRU = wx.ConfigBase_Get().ReadInt("EnableMRU", True)
        if enableMRU:
            self._fileHistory = wx.FileHistory(maxFiles=max_files,idBase=ID_MRU_FILE1)
            
    def SelectDocumentType(self, temps, sort=False):
        """
        Returns a document template by asking the user (if there is more than
        one template). This function is used in wxDocManager.CreateDocument.

        Parameters

        templates - list of templates from which to choose a desired template.

        sort - If more than one template is passed in in templates, then this
        parameter indicates whether the list of templates that the user will
        have to choose from is sorted or not when shown the choice box dialog.
        Default is false.
        """
        templates = []
        for temp in temps:
            if temp.IsVisible():
                want = True
                for temp2 in templates:
                    if temp.GetDocumentName() == temp2.GetDocumentName() and temp.GetViewName() == temp2.GetViewName():
                        want = False
                        break
                if want:
                    templates.append(temp)

        if len(templates) == 0:
            return None
        elif len(templates) == 1:
            return templates[0]

        if sort:
            def tempcmp(a, b):
                return cmp(a.GetDescription(), b.GetDescription())
            templates.sort(tempcmp)


        default_document_type = utils.ProfileGet("DefaultDocumentType",DEFAULT_DOCUMENT_TYPE_NAME)
        default_document_template = self.FindTemplateForDocumentType(default_document_type)
        strings = []
        default_document_selection = -1
        for i,temp in enumerate(templates):
            if temp == default_document_template:
                default_document_selection = i
            strings.append(_(temp.GetDescription()))
            
        res = NewDocument.GetNewDocumentChoiceIndex(self.FindSuitableParent(),strings,default_document_selection)
        if res == -1:
            return None
        return templates[res]
        

    def FindTemplateForDocumentType(self, document_type):
        """
        Given a path, try to find template that matches the extension. This is
        only an approximate method of finding a template for creating a
        document.
        
        Note this wxPython verson looks for and returns a default template if no specific template is found.
        """
        default = None
        for temp in self._templates:
            if temp.GetDocumentName() == document_type:
                return temp
        return default
        
    def CreateTemplateDocument(self, template,path, flags=0):
        #the document has been opened,switch to the document view
        if path and flags & wx.lib.docview.DOC_OPEN_ONCE:
            found_view = utils.GetOpenView(path)
            if found_view:
                if found_view and found_view.GetFrame() and not (flags & wx.lib.docview.DOC_NO_VIEW):
                    found_view.GetFrame().SetFocus()  # Not in wxWindows code but useful nonetheless
                    if hasattr(found_view.GetFrame(), "IsIconized") and found_view.GetFrame().IsIconized():  # Not in wxWindows code but useful nonetheless
                        found_view.GetFrame().Iconize(False)
                return None
                
        doc = template.CreateDocument(path, flags)
        if doc:
            doc.SetDocumentName(template.GetDocumentName())
            doc.SetDocumentTemplate(template)
            if not doc.OnOpenDocument(path):
                frame = doc.GetFirstView().GetFrame()
                doc.DeleteAllViews()  # Implicitly deleted by DeleteAllViews
                if frame:
                    frame.Destroy() # DeleteAllViews doesn't get rid of the frame, so we'll explicitly destroy it.
                return None
            self.AddFileToHistory(path)
        return doc

#----------------------------------------------------------------------

def getIDESplashBitmap():
    return images.load("tt.png")


