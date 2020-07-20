# -*- coding: utf-8 -*-
import sys
from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
import noval.consts as consts
import noval.util.strutils as strutils
import os
import noval.core as core
import noval.imageutils as imageutils
from dummy.userdb import UserDataDb
import tkinter as tk
from tkinter import ttk,messagebox
import noval.toolbar as toolbar
try:
    import tkSimpleDialog
except ImportError:
    import tkinter.simpledialog as tkSimpleDialog
import ctypes
from pkg_resources import resource_filename,_manager
import threading
import base64
from bs4 import Tag
import noval.ui_utils as ui_utils
import noval.preference as preference
import webbrowser
import noval.util.urlutils as urlutils
import noval.plugins.update as update
import noval.util.downutils as downutils
import noval.util.fileutils as fileutils
from noval.python.plugins.pip_gui import PluginsPipDialog
import json
import zipimport
import noval.python.interpreter.pythonpackages as pythonpackages
GetApp().AddMessageCatalog('openwebbrowser', __name__)
from openwebbrowser.welcome_html_code import *
PLUGIN_INSTANCE = None

egg_path = 'cefpython3-66.0-py3.6.egg'
cache_path = _manager.get_cache_path(egg_path, '')
pkg_path = resource_filename(__name__,'')
if utils.is_windows():
    sys.path.append(cache_path)
try:
    from cefpython3 import cefpython as cef
except:
    pass
    
IS_INSTALLING_CEF = False
    
def InstallCef():
    global IS_INSTALLING_CEF
    if utils.is_windows():
        def finish_download(zip_path):
            global IS_INSTALLING_CEF
            utils.update_statusbar(_('start unzip cefpython3 component'))
            try:
                z = zipimport.zipimporter(zip_path)
                z.load_module("cefpython3")
            except:
                pass
            finally:
                IS_INSTALLING_CEF = False
            if os.path.exists(cache_path):
                utils.update_statusbar(_('unzip cefpython3 component finished'))
                utils.update_statusbar(_('install cefpython3 component success...'))
            else:
                utils.update_statusbar(_('unzip cefpython3 component failed'))
                utils.update_statusbar(_('install cefpython3 component failed...'))
                messagebox.showerror(_("Error"),_('install cefpython3 component failed,Please wait for next launch to install it'))

            
        download_url = '%s/api/download' % (UserDataDb.HOST_SERVER_ADDR)
        payload = dict(tool=egg_path)
        utils.update_statusbar(_('installing cefpython3 component...'))
        IS_INSTALLING_CEF = True
        try:
            downutils.download_file(download_url,call_back=finish_download,show_progress_dlg=False,**payload)
        except:
            IS_INSTALLING_CEF = False
            utils.update_statusbar(_('install cefpython3 component failed...'))
    else:
        pip_source_path = utils.get_config_value('virtual_env','pip_source_path',default_value=pythonpackages.InstallPackagesDialog.SOURCE_LIST[6])
        command = "%s -m pip install --user cefpython3 -i %s --trusted-host %s" % (sys.executable,pip_source_path,pythonpackages.url_parse_host(pip_source_path))
        os.system(command)
        IS_INSTALLING_CEF = True
        
def CheckCef():
    try:
        from cefpython3 import cefpython as cef
        return True
    except ModuleNotFoundError:
        InstallCef()
        return False
    except:
        utils.get_logger().exception('')
        return False
IMAGE_EXT = ".png" if tk.TkVersion > 8.5 else ".gif"

INTERNAL_WEB_BROWSER = 16
APPLICATION_STARTUP_PAGE = 32

IS_CEF_INITIALIZED = False

APP_UPDATE_COMMAND = 'command:workbench.action.app.update'
FEEDS_OPEN_URL_COMMAND = 'command:workbench.action.feeds.openurl'

class StartupOptionPanel(ui_utils.CommonOptionPanel):
    """
    """
    def __init__(self, parent):
        ui_utils.CommonOptionPanel.__init__(self, parent)
        self._showWelcomePageVar = tk.IntVar(value=utils.profile_get_int(consts.SHOW_WELCOME_PAGE_KEY, True))
        showWelcomePageCheckBox = ttk.Checkbutton(self.panel,text=_("Show start page on startup"),variable=self._showWelcomePageVar)
        showWelcomePageCheckBox.pack(fill=tk.X)
        
        row = ttk.Frame(self.panel)
        self.mru_var = tk.IntVar(value=utils.profile_get_int(consts.RECENTPROJECT_LENGTH_KEY,consts.DEFAULT_MRU_PROJECT_NUM))
        #验证历史文件个数文本控件输入是否合法
        validate_cmd = self.register(self.validateMRUInput)
        self.mru_project_ctrl = ttk.Entry(row,validate = 'key', textvariable=self.mru_var,validatecommand = (validate_cmd, '%P'))
        ttk.Label(row, text=_("Project History length on start page") + "(%d-%d): " % \
                                                            (1,consts.MAX_MRU_PROJECT_LIMIT)).pack(side=tk.LEFT)
        self.mru_project_ctrl.pack(side=tk.LEFT)
        row.pack(fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))

    def OnOK(self, optionsDialog):
        utils.profile_set(consts.SHOW_WELCOME_PAGE_KEY, self._showWelcomePageVar.get())
        utils.profile_set(consts.RECENTPROJECT_LENGTH_KEY,self.mru_var.get())
        return True
        
    def validateMRUInput(self,contents):
        if not contents.isdigit():
            self.mru_project_ctrl.bell()
            return False
        return True
        
def html_to_data_uri(html, js_callback=None):
    # This function is called in two ways:
    # 1. From Python: in this case value is returned
    # 2. From Javascript: in this case value cannot be returned because
    #    inter-process messaging is asynchronous, so must return value
    #    by calling js_callback.
    html = html.encode("utf-8", "replace")
    b64 = base64.b64encode(html).decode("utf-8", "replace")
    ret = "data:text/html;base64,{data}".format(data=b64)
    if js_callback:
        js_print(js_callback.GetFrame().GetBrowser(),
                 "Python", "html_to_data_uri",
                 "Called from Javascript. Will call Javascript callback now.")
        js_callback.Call(ret)
    else:
        return ret

class WebDocument(core.Document):
    def OnOpenDocument(self, filename):
        return True
        

class LoadHandler(object):

    def __init__(self, browser_frame):
        self.browser_frame = browser_frame

    def OnLoadStart(self, browser, **_):
        if self.browser_frame.web_view.navigation_bar:
            self.browser_frame.web_view.navigation_bar.set_url(browser.GetUrl())
            
    def OnLoadEnd(self,browser,**kwargs):
        print (kwargs)
        if not self.browser_frame.web_view.navigation_bar:
            print ("load url end....")
            if kwargs.get('http_code') == 200:
                PLUGIN_INSTANCE.LoadAsync(self.browser_frame)
        
    def OnLoadError(self,browser,**kwargs):
        print ("load url %s error...."%browser.GetUrl())
        print (kwargs)
        print ("-----------------------------")


class FocusHandler(object):

    def __init__(self, browser_frame):
        self.browser_frame = browser_frame

    def OnTakeFocus(self, next_component, **_):
        utils.get_logger().debug("FocusHandler.OnTakeFocus, next={next}"
                     .format(next=next_component))

    def OnSetFocus(self, source, **_):
        utils.get_logger().debug("FocusHandler.OnSetFocus, source={source}"
                     .format(source=source))
        return False

    def OnGotFocus(self, **_):
        """Fix CEF focus issues (#255). Call browser frame's focus_set
           to get rid of type cursor in url entry widget."""
        utils.get_logger().debug("FocusHandler.OnGotFocus")
        #self.browser_frame.focus_set()
    
@utils.call_after_with_arg(1) 
def ShowPluginManagerDlg():
    plugin_dlg = PluginsPipDialog(GetApp().GetTopWindow(),package_count=0)
    plugin_dlg.ShowModal()
    
@utils.call_after_with_arg(1) 
def ShowErrorMessageDialog(title,msg):
    messagebox.showerror(title,msg)
        
class Command(object):
    def action(self, msg):
        if msg == 'command:workbench.action.project.openProject':
            GetApp().MainFrame.GetProjectView().OpenProject()
        elif msg == 'command:workbench.action.project.newProject':
            GetApp().MainFrame.GetProjectView().NewProject()
        elif msg == "command:workbench.action.help.register_or_login":
            GetApp().Registerorlogin()
        elif msg == "command:workbench.action.help.ManagePlugins":
            ShowPluginManagerDlg()
        elif msg.find(APP_UPDATE_COMMAND) != -1:
            app_version = msg.replace(APP_UPDATE_COMMAND+":","")
            update.UpdateApp(app_version)
        elif msg.find(FEEDS_OPEN_URL_COMMAND) != -1:
            url,feed_id = msg.replace(FEEDS_OPEN_URL_COMMAND+":","").split('|')
            webbrowser.open(url)
            if feed_id == "...":
                return
            api_addr = '%s/api/feed/open' % (UserDataDb.HOST_SERVER_ADDR)
            urlutils.RequestData(api_addr,method="post",arg = {'feed_id':feed_id})        
        elif msg == "command:workbench.action.help.openCodeRepositoryURL":
            webbrowser.open("https://gitee.com/wekay/NovalIDE")
        elif msg == "command:workbench.action.help.openDocumentationUrl":
            webbrowser.open("https://wekay.gitee.io/novalide")
        elif msg == "command:workbench.action.help.keybindingsReference":
            webbrowser.open("http://www.novalide.com/media/document/shortcuts.pdf")
        elif msg == "command:workbench.action.help.openIntroductoryVideosUrl":
            webbrowser.open("https://wekay.gitee.io/novalide/zh/getstarted/introductory/")
        elif msg == "command:workbench.action.help.openTipsAndTricksUrl":
            webbrowser.open("https://wekay.gitee.io/novalide/zh/getstarted/tips/")
        else:
            project_path = msg.split(':')[-1].replace('/',os.sep).replace('|',":")
            if not os.path.exists(project_path):
                GetApp().GetDocumentManager().RemoveProjectFromHistory(project_path)
                ShowErrorMessageDialog(GetApp().GetAppName(),_("The project '%s' doesn't exist and couldn't be opened!") % project_path)
            else:
                GetApp().GetDocumentManager().CreateDocument(project_path, core.DOC_SILENT)
        
class BrowserFrame(ttk.Frame):

    def __init__(self, main, url,view,navigation_bar=None):
        self.navigation_bar = navigation_bar
        self.closing = False
        self.browser = None
        self.url = url
        self.web_view = view
        ttk.Frame.__init__(self, main)
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        self.bind("<Configure>", self.on_configure)
        self.focus_set()
        
    def SetUrl(self,url):
        self.url = url
        
    def SetClientHandler(self):
        self.browser.SetClientHandler(LoadHandler(self))
        self.browser.SetClientHandler(FocusHandler(self))
        
    def CreateBrowserAsync(self,window_info,url):
        self.browser = cef.CreateBrowserSync(window_info,
                                             url=url)
        assert self.browser
        self.SetClientHandler()
        js = cef.JavascriptBindings()
        js.SetObject('Command', Command())
        self.browser.SetJavascriptBindings(js)
        
        
    def embed_browser_sync(self):
        '''
            这是在单线程中创建cef浏览器对象
        '''
        window_info = cef.WindowInfo()
        rect = [0, 0, self.winfo_width(), self.winfo_height()]
        window_info.SetAsChild(self.get_window_handle(), rect)
        self.browser = cef.CreateBrowserSync(window_info,
                                             url=self.url)
        assert self.browser
        self.SetClientHandler()
        js = cef.JavascriptBindings()
        js.SetObject('Command', Command())
        self.browser.SetJavascriptBindings(js)
        #消息循环
        #在UI线程创建browser不使用消息循环,只有在单线程时才使用
        self.message_loop_work()

    def embed_browser(self):
        window_info = cef.WindowInfo()
        rect = [0, 0, self.winfo_width(), self.winfo_height()]
        window_info.SetAsChild(self.get_window_handle(), rect)
        #设置以UI线程来创建浏览器,void cef.PostTask(线程，funcName, [params...]),传入funcName函数的参数不能是关键字
        cef.PostTask(cef.TID_UI, self.CreateBrowserAsync, window_info, self.url)

    def get_window_handle(self):
        if self.winfo_id() > 0:
            return self.winfo_id()
        else:
            raise Exception("Couldn't obtain window handle")

    def message_loop_work(self):
        cef.MessageLoopWork()
        self.after(10, self.message_loop_work)

    def on_configure(self, _):
        if not self.browser:
            #windows系统使用UI线程来创建浏览器
            if utils.is_windows():
                self.embed_browser()
            else:
                #linux系统使用单线程来创建浏览器
                self.embed_browser_sync()

    def on_root_configure(self):
        # Root <Configure> event will be called when top window is moved
        if self.browser:
            self.browser.NotifyMoveOrResizeStarted()

    def on_mainframe_configure(self, width, height):
        if self.browser:
            if utils.is_windows():
               ctypes.windll.user32.SetWindowPos(
                    self.browser.GetWindowHandle(), 0,
                    0, 0, width, height, 0x0002)
            elif utils.is_linux():
                self.browser.SetBounds(0, 0, width, height)
            self.browser.NotifyMoveOrResizeStarted()

    def on_focus_in(self, _):
        utils.get_logger().debug("BrowserFrame.on_focus_in")
        if self.browser:
            self.browser.SetFocus(True)

    def on_focus_out(self, _):
        utils.get_logger().debug("BrowserFrame.on_focus_out")
        if self.browser:
            self.browser.SetFocus(False)

    def on_root_close(self):
        if self.browser:
            self.browser.CloseBrowser(True)
            self.clear_browser_references()
        self.destroy()

    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.browser = None


class WebView(core.View):

    def __init__(self):
        global IS_CEF_INITIALIZED
        core.View.__init__(self)
        self.browser_frame = None
        self.navigation_bar = None
        self.start_url = ''
        self.zoom_level = 0
        if not IS_CEF_INITIALIZED:
            settings = {
                'locale':GetApp().locale.GetLanguageCanonicalName(),
                'single_process':True
            }
            if utils.is_windows():
                settings.update({
                    'multi_threaded_message_loop':True,
                    "locales_dir_path": os.path.join(cache_path,"cefpython3","locales"),
                    "browser_subprocess_path": os.path.join(cache_path,"cefpython3","subprocess.exe"),
                    "resources_dir_path":os.path.join(cache_path,"cefpython3",'resources')
                    })
            cef.Initialize(settings=settings)
            IS_CEF_INITIALIZED = True
        
    def OnClose(self, deleteWindow = True):
        self.Activate(False)
        if deleteWindow and self.GetFrame():
            self.GetFrame().Destroy()
        return True
    
    def set_line_and_column(self):
        GetApp().MainFrame.GetStatusBar().Reset()
        
    def LoadUrl(self,url):
        self.get_browser_frame().SetUrl(url)
        
    def OnCreate(self, doc, flags):
        template = doc.GetDocumentTemplate()
        template_icon = template.GetIcon()
        if flags & APPLICATION_STARTUP_PAGE:
            template.SetIcon(None)
        frame = GetApp().CreateDocumentFrame(self, doc, flags)
        template.SetIcon(template_icon)
        frame.bind("<Configure>", self.on_configure)
        browser_row = 0
        if not (flags & APPLICATION_STARTUP_PAGE) and not (flags & INTERNAL_WEB_BROWSER):
            self.start_url = doc.GetFilename()
            if utils.is_linux() and os.path.isfile(self.start_url):
                self.start_url = "file://" + self.start_url
        if not (flags & APPLICATION_STARTUP_PAGE):
            self.navigation_bar = NavigationBar(frame,self)
            self.navigation_bar.grid(row=0, column=0,
                                     sticky=(tk.N + tk.S + tk.E + tk.W))
            frame.rowconfigure(0, weight=0)
            frame.columnconfigure(0, weight=0)
            browser_row += 1
        self.browser_frame = BrowserFrame(frame,self.start_url,self,self.navigation_bar)      
        self.browser_frame.grid(row=browser_row, column=0,
                                 sticky=(tk.N + tk.S + tk.E + tk.W))
        frame.rowconfigure(browser_row, weight=1)
        frame.columnconfigure(0, weight=1)
        return True
        
    def on_configure(self, event):
        utils.get_logger().debug("MainFrame.on_configure")
        if self.browser_frame:
            width = event.width
            height = event.height
            if self.navigation_bar:
                height = height - self.navigation_bar.winfo_height()
            self.browser_frame.on_mainframe_configure(width, height)
        
    def UpdateUI(self, command_id):
        if command_id in [constants.ID_CLOSE,constants.ID_CLOSE_ALL]:
            return True
        return core.View.UpdateUI(self,command_id)
        
    def get_browser(self):
        if self.browser_frame:
            return self.browser_frame.browser
        return None

    def get_browser_frame(self):
        if self.browser_frame:
            return self.browser_frame
        return None
        
    def ZoomView(self,delta=0):
        if self.zoom_level >= 15 and delta > 0:
            return
        elif self.zoom_level <= -10 and delta < 0:
            return
        self.zoom_level += delta
        if self.browser_frame:
            self.get_browser().SetZoomLevel(self.zoom_level)

class WebBrowserPlugin(plugin.Plugin):
    """plugin description here..."""
    ID_WEB_BROWSER = NewId()
    ID_SHOW_WELCOME_PAGE = NewId()
    plugin.Implements(iface.MainWindowI)
    NEWS = "news"
    LEARN = "learn"
    DEFAULT_NEWS_NUM = 3
    DEFAULT_LEARN_NUM = 3
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing WebBrowser plugin")
        if not CheckCef():
            utils.get_logger().error("cefpython component is not success installled...")
            return
        global PLUGIN_INSTANCE
        webViewTemplate = core.DocTemplate(GetApp().GetDocumentManager(),
                _("WebView"),
                "*.com;*.org",
                os.getcwd(),
                ".com",
                "WebView Document",
                _("Internal Web Browser"),
                WebDocument,
                WebView,
                core.TEMPLATE_INVISIBLE,
                icon = imageutils.load_image("","web.png"))
        GetApp().GetDocumentManager().AssociateTemplate(webViewTemplate)
        GetApp().MainFrame.GetProjectView(False).tree.RebuildLookupIcon()
        GetApp().InsertCommand(constants.ID_PLUGIN,self.ID_WEB_BROWSER,_("&Tools"),_("&Web Browser"),handler=self.GotoDefaultWebsite,pos="before",\
                               image=webViewTemplate.GetIcon())
        GetApp().bind(constants.CHANGE_APPLICATION_LOOK_EVT, self.UpdateWelcomeTheme,True)
        PLUGIN_INSTANCE = self
        image_path = os.path.join(pkg_path, "resources","start.png")
        GetApp().InsertCommand(constants.ID_CHECK_UPDATE,self.ID_SHOW_WELCOME_PAGE,_("&Help"),_("Start Page"),handler=self.ShowWelcomePage,pos="before",\
                               image=GetApp().GetImage(image_path))
        preference.PreferenceManager().AddOptionsPanelClass(preference.ENVIRONMENT_OPTION_NAME,"Start Page",StartupOptionPanel)
        self.is_initialized = True
        self.app_update_params = {'has_new':False}
        self.feeds = []
        
    def InitNum(self):
        self.number = {
            self.NEWS:0,
            self.LEARN:0
        }
        if self.app_update_params['has_new']:
            self.number[self.NEWS] += 1
        
    def LoadNews(self,frame):
        def add_id(d):
            d.update({'id':'...'})
            return d
            
        self.CheckAppUpdate(self.app_update_params,frame)
        self.GetFeeds()
        utils.get_logger().info("get feeds count from sever is %d",len(self.feeds))
        if len(self.feeds) < (self.DEFAULT_NEWS_NUM + self.DEFAULT_LEARN_NUM):
            data = self.LoadDefaultFeeds()
            data = list(map(add_id,data))
            self.feeds.extend(data)
            utils.get_logger().info("get feeds count from sever is not enough,now feeds number is %d",len(self.feeds))
        self.CreateFeedNews(frame)
        
    def LoadDefaultFeeds(self):
        feeds_file = os.path.join(pkg_path,"feeds.json")
        try:
            with open(feeds_file,encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
        
    def LoadAsync(self,frame):
        self.InitNum()
        self.LoadRecent(frame)
        t = threading.Thread(target=self.LoadNews,args=(frame,))
        t.start()
                
    def UpdateWelcomeTheme(self,event):
        theme = event.get('theme')
        if self.is_initialized:
            if utils.profile_get_int(consts.SHOW_WELCOME_PAGE_KEY, True):
                self.GotoStartupPage(theme)
            else:
                t = threading.Thread(target=self.CheckAppUpdate,args=(self.app_update_params,))
                t.start()
            self.is_initialized = False
        else:
            start_doc = GetApp().GetDocumentManager().GetDocument(_("Start Page"))
            if start_doc:
                self.LoadStartupPage(start_doc,theme)
        
    def ShowWelcomePage(self):
        self.GotoStartupPage(GetApp().theme_value.get())
        
    def GotoDefaultWebsite(self):
        self.GotoWebView(UserDataDb.HOST_SERVER_ADDR)
        
    def GotoWebView(self,web_addr):
        webViewTemplate = GetApp().GetDocumentManager().FindTemplateForTestPath(".com")
        doc = GetApp().GetDocumentManager().CreateTemplateDocument(webViewTemplate,_("Internal Web Browser"), core.DOC_SILENT|core.DOC_OPEN_ONCE|INTERNAL_WEB_BROWSER)
        if doc:
            doc.GetFirstView().LoadUrl(web_addr)
        
    def GotoStartupPage(self,theme):
        webViewTemplate = GetApp().GetDocumentManager().FindTemplateForTestPath(".com")
        doc = GetApp().GetDocumentManager().CreateTemplateDocument(webViewTemplate,_("Start Page"), core.DOC_SILENT|core.DOC_OPEN_ONCE|APPLICATION_STARTUP_PAGE)
        self.LoadStartupPage(doc,theme)
        
    def LoadStartupPage(self,doc,theme):
        t = threading.Thread(target=self.OpenStartupPage,args=(doc,theme))
        t.start()
        
    def LoadRecentProjects(self):
        recent_projects = []
        projectHistory = GetApp().GetDocumentManager().GetProjectHistory()
        file_size = projectHistory.GetCurrentSize()
        for i in range(file_size):
            path = projectHistory.GetHistoryFile(i)
            recent_projects.append(path)
        return recent_projects
        
    def LoadRecent(self,frame):
        recent_projects = self.LoadRecentProjects()
        if recent_projects == []:
            frame.browser.ExecuteFunction('SetEmptyProject')
        else:
            project_html_content = ''
            for recent_project in recent_projects:
                recent_project_path = recent_project.replace(":","|").replace("\\",'/')
                li = Tag(name='li',attrs={'class':'path'})
                a = Tag(name='a',attrs={'href':'javascript:void(0)','title':recent_project,'onclick':"Command.action('command:workbench.action.project.openRecentProject:%s')"%recent_project_path})
                a.string = os.path.basename(recent_project)
                li.append(a)
                project_html_content += li.prettify()
                project_html_content += "\n"
            frame.browser.ExecuteFunction('LoadProjects', project_html_content)
        if utils.is_windows():
            frame.on_mainframe_configure(frame.winfo_width(),frame.winfo_height())
        
    def GetFeeds(self):
        api_addr = '%s/api/feed/items' % (UserDataDb.HOST_SERVER_ADDR)
        app_version = utils.get_app_version()
        utils.get_logger().info("start get feeds from sever ...")
        data = urlutils.RequestData(api_addr,timeout=3,arg = {'app_version':app_version})
        if data is None:
            utils.get_logger().error("get feeds from sever error....")
            return
        self.feeds = data['feeds']
        utils.get_logger().info("get feeds from sever success....")
        
    def CreateFeedNews(self,frame):
        news_html_content = ''
        
        if self.app_update_params['has_new']:
            click_event = "Command.action('%s:%s')"%(APP_UPDATE_COMMAND,self.app_update_params['app_version'])
            div = self.CreateNews(self.app_update_params['title'],self.app_update_params['subcontent'],click_event)
            news_html_content += div.prettify()
            news_html_content += "\n"
            self.number[self.NEWS] += 1
            
        learn_html_content = ''
        for feed in self.feeds:
            click_event = "Command.action('%s:%s|%s')"%(FEEDS_OPEN_URL_COMMAND,feed['url'],feed['id'])
            div = self.CreateNews(feed['title'],feed['subcontent'],click_event)
            if feed['category'] == self.NEWS and self.number[self.NEWS] < self.DEFAULT_NEWS_NUM:
                news_html_content += div.prettify()
                news_html_content += "\n"
                self.number[self.NEWS] += 1
            elif feed['category'] == self.LEARN and self.number[self.LEARN] < self.DEFAULT_LEARN_NUM:
                learn_html_content += div.prettify()
                learn_html_content += "\n"
                self.number[self.LEARN] += 1
        if news_html_content:
            frame.browser.ExecuteFunction('LoadNews', news_html_content)
        if learn_html_content:
            frame.browser.ExecuteFunction('LoadLearn', learn_html_content)
        #必须显示调用该函数以避免js函数执行无法生效的BUG
        if utils.is_windows():
            frame.on_mainframe_configure(frame.winfo_width(),frame.winfo_height())
        
    def CreateNews(self,title,subcontent,click_event):
        div = Tag(name='div',attrs={'class':'item showLanguageExtensions'})
        btn = Tag(name='button',attrs={'role':'group','data-href':"command:workbench.extensions.action.showLanguageExtensions",'onclick':click_event})
        h3 = Tag(name="h3",attrs={'class':'caption'})
        h3.string = title
        span = Tag(name="span",attrs={'class':'detail'})
        span.string = subcontent
        div.append(btn)
        btn.append(h3)
        btn.append(span)
        return div
        
    def OpenStartupPage(self,doc,theme):
        welcome_html_url = html_to_data_uri(html_code)
        doc.GetFirstView().LoadUrl(welcome_html_url)

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """
        return "1.2.3"

    def InstallHook(self):
        """Override in subclasses to allow the plugin to be loaded
        dynamically.
        @return: None

        """
        CheckCef()
        
    def CanUninstall(self):
        return False

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
        
    def HookExit(self,exit):
        ''''''
        if not exit:
            if IS_INSTALLING_CEF:
                utils.update_statusbar(_('installing cefpython3 component...'))
                messagebox.showinfo(GetApp().GetAppName(),_('Application is installing cef component.Please wait for a monment to exit!'))
                return False
            return True
        else:
            try:
                cef.PostTask(cef.TID_UI, cef.Shutdown)
            finally:
                return True
        
    def CheckAppUpdate(self,params={},frame=None):
        api_addr = '%s/api/update/app' % (UserDataDb.HOST_SERVER_ADDR)
        app_version = utils.get_app_version()
        utils.get_logger().info("start check app update info from server...")
        data = urlutils.RequestData(api_addr,timeout=3,arg = {'app_version':app_version,'is_dev':int(utils.is_dev())})
        if data is None:
            utils.get_logger().error("check app update info error from server...")
            return
        force_show_welcome = data['force_show_welcome']
        if force_show_welcome and not utils.profile_get_int(consts.SHOW_WELCOME_PAGE_KEY, True):
            utils.profile_set(consts.SHOW_WELCOME_PAGE_KEY, True)
        utils.get_logger().info("check app update info success from server...")
        #have update
        if data['code'] == 1:
            new_version = data['new_version']
            update_msg = data['update_msg']
            msg =  _("this lastest version '%s' is available,click here to update it") % new_version
            params['has_new'] = True
            params['title'] = msg
            params['subcontent'] = update_msg
            params['app_version'] = new_version
            if frame is None:
                update.CheckAppupdateInfo(data)
    
    
class NavigationBar(toolbar.ToolBar):
    
    ID_OPEN_URL = NewId()
    ID_GO_BACK = NewId()
    ID_GO_FORWARD = NewId()
    ID_RELOAD = NewId()
    ID_STOP = NewId()
    def __init__(self, main,view):
        self.web_view = view
        self.back_state = tk.NONE
        self.forward_state = tk.NONE
        self.back_image = None
        self.forward_image = None
        self.reload_image = None
        self.go_image = None
        self.stop_image = None

        toolbar.ToolBar.__init__(self, main)
        resources = os.path.join(pkg_path, "resources")
        
        go_png = os.path.join(resources, "go"+IMAGE_EXT)
        if os.path.exists(go_png):
            self.go_image = tk.PhotoImage(file=go_png)
            
        self.AddButton(self.ID_OPEN_URL, self.go_image, _('Open URL'),self.GoUrl)
        # Back button
        back_png = os.path.join(resources, "back"+IMAGE_EXT)
        if os.path.exists(back_png):
            self.back_image = tk.PhotoImage(file=back_png)

        self.back_button = self.AddButton(self.ID_GO_BACK, self.back_image, _('Go Back'),self.go_back)

        # Forward button
        forward_png = os.path.join(resources, "forward"+IMAGE_EXT)
        if os.path.exists(forward_png):
            self.forward_image = tk.PhotoImage(file=forward_png)

        self.forward_button = self.AddButton(self.ID_GO_FORWARD, self.forward_image, _('Go Forward'),self.go_forward)
        
        # Forward button
        stop_png = os.path.join(resources, "stop"+IMAGE_EXT)
        if os.path.exists(stop_png):
            self.stop_image = tk.PhotoImage(file=stop_png)

        self.AddButton(self.ID_STOP, self.stop_image, _('Stop'),self.Stop)
        # Reload button
        reload_png = os.path.join(resources, "reload"+IMAGE_EXT)
        if os.path.exists(reload_png):
            self.reload_image = tk.PhotoImage(file=reload_png)

        self.reload_button = self.AddButton(self.ID_RELOAD, self.reload_image, _('Reload'),self.reload)
        
        self.AddLabel(text=_("URL:"))
        self.url_entry = self.AddCombox(state=None)
        self.url_entry.bind("<FocusIn>", self.on_url_focus_in)
        self.url_entry.bind("<FocusOut>", self.on_url_focus_out)
        self.url_entry.bind("<Return>", self.on_load_url)
        self.url_entry.bind("<Button-1>", self.on_button1)
        self.url_entry.bind("<<ComboboxSelected>>",self.on_load_url)
            
        group_frame = self.pack_subordinates()[0]
        self.url_entry.grid(row=0, column=6, sticky="nsew", padx=5)
        group_frame.pack(fill="x",side=tk.LEFT,expand=1)
        group_frame.columnconfigure(6, weight=1)

        # Update state of buttons
        self.update_state()
        
    def GoUrl(self):
        url = tkSimpleDialog.askstring(
            _("Open URL:"),
            _("Enter a full URL or local path")
        )
        if not url:
            return
            
        if utils.is_linux() and os.path.isfile(url):
            url = "file://" + url
        self.load_url(url)

    def go_back(self):
        if self.web_view.get_browser():
            self.web_view.get_browser().GoBack()

    def go_forward(self):
        if self.web_view.get_browser():
            self.web_view.get_browser().GoForward()

    def reload(self):
        if self.web_view.get_browser():
            self.web_view.get_browser().Reload()

    def set_url(self, url):
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        values = set(self.url_entry['values'])
        values.add(url)
        self.url_entry['values'] = tuple(values)

    def on_url_focus_in(self, _):
        utils.get_logger().debug("NavigationBar.on_url_focus_in")

    def on_url_focus_out(self, _):
        utils.get_logger().debug("NavigationBar.on_url_focus_out")
        
    def Stop(self):
        self.web_view.get_browser().StopLoad()

    def on_load_url(self, _):
        self.load_url(self.url_entry.get())
        
    def load_url(self,url):
        if self.web_view.get_browser():
            self.web_view.get_browser().StopLoad()
            self.web_view.get_browser().LoadUrl(url)

    def on_button1(self, _):
        """Fix CEF focus issues (#255). See also FocusHandler.OnGotFocus."""
        utils.get_logger().debug("NavigationBar.on_button1")
        self.main.main.focus_force()

    def update_state(self):
        browser = self.web_view.get_browser()
        if not browser:
            if self.back_state != tk.DISABLED:
                self.back_button.config(state=tk.DISABLED)
                self.back_state = tk.DISABLED
            if self.forward_state != tk.DISABLED:
                self.forward_button.config(state=tk.DISABLED)
                self.forward_state = tk.DISABLED
            self.after(100, self.update_state)
            return
        if browser.CanGoBack():
            if self.back_state != tk.NORMAL:
                self.back_button.config(state=tk.NORMAL)
                self.back_state = tk.NORMAL
        else:
            if self.back_state != tk.DISABLED:
                self.back_button.config(state=tk.DISABLED)
                self.back_state = tk.DISABLED
        if browser.CanGoForward():
            if self.forward_state != tk.NORMAL:
                self.forward_button.config(state=tk.NORMAL)
                self.forward_state = tk.NORMAL
        else:
            if self.forward_state != tk.DISABLED:
                self.forward_button.config(state=tk.DISABLED)
                self.forward_state = tk.DISABLED
        self.after(100, self.update_state)