from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
import os
import noval.core as core
import noval.imageutils as imageutils
from dummy.userdb import UserDataDb
import tkinter as tk
from tkinter import ttk
from cefpython3 import cefpython as cef
import noval.toolbar as toolbar
from pkg_resources import resource_filename
try:
    import tkSimpleDialog
except ImportError:
    import tkinter.simpledialog as tkSimpleDialog

WindowUtils = cef.WindowUtils()
IMAGE_EXT = ".png" if tk.TkVersion > 8.5 else ".gif"

INTERNAL_WEB_BROWSER = 16
APPLICATION_STARTUP_PAGE = 32

IS_CEF_INITIALIZED = False

class WebDocument(core.Document):
    def OnOpenDocument(self, filename):
        return True
        

class LoadHandler(object):

    def __init__(self, browser_frame):
        self.browser_frame = browser_frame

    def OnLoadStart(self, browser, **_):
        if self.browser_frame.web_view.navigation_bar:
            self.browser_frame.web_view.navigation_bar.set_url(browser.GetUrl())


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
        self.browser_frame.focus_set()
        
class BrowserFrame(ttk.Frame):

    def __init__(self, master, url,view,navigation_bar=None):
        self.navigation_bar = navigation_bar
        self.closing = False
        self.browser = None
        self.url = url
        self.web_view = view
        ttk.Frame.__init__(self, master)
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        self.bind("<Configure>", self.on_configure)
        self.focus_set()
        
    def SetUrl(self,url):
        self.url = url

    def embed_browser(self):
        window_info = cef.WindowInfo()
        rect = [0, 0, self.winfo_width(), self.winfo_height()]
        window_info.SetAsChild(self.get_window_handle(), rect)
        self.browser = cef.CreateBrowserSync(window_info,
                                             url=self.url)
        assert self.browser
        self.browser.SetClientHandler(LoadHandler(self))
        self.browser.SetClientHandler(FocusHandler(self))
        self.message_loop_work()

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
            self.embed_browser()

    def on_root_configure(self):
        # Root <Configure> event will be called when top window is moved
        if self.browser:
            self.browser.NotifyMoveOrResizeStarted()

    def on_mainframe_configure(self, width, height):
        if self.browser:
            if utils.is_windows():
                WindowUtils.OnSize(self.get_window_handle(), 0, 0, 0)
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
        if not IS_CEF_INITIALIZED:
            cef.Initialize()
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
        if flags & INTERNAL_WEB_BROWSER:
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
        pass

class WebBrowserPlugin(plugin.Plugin):
    """plugin description here..."""
    ID_WEB_BROWSER = NewId()
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing WebBrowser plugin")
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
        GetApp().InsertCommand(constants.ID_PLUGIN,self.ID_WEB_BROWSER,_("&Tools"),_("&Web Browser"),handler=self.GotoDefaultWebsite,pos="before")
        self.GotoStartupPage()
        
    def GotoDefaultWebsite(self):
        self.GotoWebView(UserDataDb.HOST_SERVER_ADDR)
        
    def GotoWebView(self,web_addr):
        webViewTemplate = GetApp().GetDocumentManager().FindTemplateForTestPath(".com")
        doc = GetApp().GetDocumentManager().CreateTemplateDocument(webViewTemplate,_("Internal Web Browser"), core.DOC_SILENT|core.DOC_OPEN_ONCE|INTERNAL_WEB_BROWSER)
        if doc:
            doc.GetFirstView().LoadUrl(web_addr)
        
    def GotoStartupPage(self):
        webViewTemplate = GetApp().GetDocumentManager().FindTemplateForTestPath(".com")
        doc = GetApp().GetDocumentManager().CreateTemplateDocument(webViewTemplate,_("Startup Page"), core.DOC_SILENT|core.DOC_OPEN_ONCE|APPLICATION_STARTUP_PAGE)
        doc.GetFirstView().LoadUrl(r'D:\env\project\Noval\template.xml')

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
        
    def HookExit(self):
        cef.Shutdown()
    
class NavigationBar(toolbar.ToolBar):
    
    ID_OPEN_URL = NewId()
    ID_GO_BACK = NewId()
    ID_GO_FORWARD = NewId()
    ID_RELOAD = NewId()
    ID_STOP = NewId()
    def __init__(self, master,view):
        self.web_view = view
        self.back_state = tk.NONE
        self.forward_state = tk.NONE
        self.back_image = None
        self.forward_image = None
        self.reload_image = None
        self.go_image = None
        self.stop_image = None

        toolbar.ToolBar.__init__(self, master)
        path = resource_filename(__name__,'')
        resources = os.path.join(path, "resources")
        
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
            
        group_frame = self.pack_slaves()[0]
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
        self.master.master.focus_force()

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