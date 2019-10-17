# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        core.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-08
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from __future__ import print_function
from noval import GetApp,_,NewId
import tkinter as tk
from tkinter import filedialog,messagebox,ttk
import tempfile
import mmap
import noval
import sys
import noval.util.apputils as apputils
import noval.util.strutils as strutils
import noval.util.check as check
import noval.util.timer as timer
import pickle
import time
import noval.util.utils as utils
import os
import noval.util.fileutils as fileutils
import noval.consts as consts
import noval.ui_base as ui_base
import shutil
import noval.newTkDnD as newTkDnD
import noval.ui_utils as ui_utils
#python2原装的tkinter多线程支持不好
#mtTkinter包装tkinter以支持多线程,在python2.7中使用
#python3的tkinter很好地支持多线程,所有不需要再额外包装
if utils.is_py2():
    from noval.mttkinter import mtTkinter
import json
try:
    import StringIO
except:
    import io as StringIO

TEMPLATE_VISIBLE = 1
#不可见模板,不会在文件对话框中出现
TEMPLATE_INVISIBLE = 2
#不能新建的文档类型,例如图片文件等
TEMPLATE_NO_CREATE = (4 | TEMPLATE_VISIBLE)
DEFAULT_TEMPLATE_FLAGS = TEMPLATE_VISIBLE

#新建文档类型
DOC_NEW = 1
#静默打开文档,适用于双击打开文件,不需要打开文件对话框
DOC_SILENT = 2
#相同路径的文档只打开一次
DOC_OPEN_ONCE = 4
DOC_NO_VIEW = 8
DEFAULT_DOCMAN_FLAGS = DOC_OPEN_ONCE

ID_MRU_FILE1 = -1


#初始化历史文件菜单id,必须保证id的连续性
def InitMRUIds():
    global ID_MRU_FILE1
    for i in range(consts.MAX_MRU_FILE_LIMIT):
        if i == 0:
            ID_MRU_FILE1 = NewId()
        else:
            NewId()


class App(tk.Tk):
    
    def __init__(self,is_debug=False):
        kwargs = {
            'className':"NovalIDE"
        }
        #打印多线程调试信息
        if utils.is_py2():
            kwargs.update({'mt_debug':True})
        tk.Tk.__init__(self,**kwargs)
        noval._AppInstance = self
        self._debug = is_debug
        self._singleInstance = True
        self._splash = None
        self.locale = noval.Locale(noval.ui_lang.LANGUAGE_DEFAULT)
        self.frame = None
        self._clip_board = None
        #是否全屏显示
        self._is_full_screen = False
        self.initializing = False
        #初始化历史文件菜单id列表,文件id的值必须是连续增长的
        InitMRUIds()
        self._BootstrapApp()
        #重写主窗口右上角X关闭按钮事件,等同于点击退出菜单
        self.protocol("WM_DELETE_WINDOW", self.Quit)
        
    def InitTkDnd(self):
        '''
            初始化拖拽对象
        '''
        self.dnd = newTkDnD.TkDND(self)
        #加载tkdnd模块失败
        if not self._tkdnd_loaded:
            self.dnd = None
        
    def MaxmizeWindow(self):
        #设置windows下启动时窗口最大化
        if utils.is_windows():
            self.state("zoomed")
        else:
            #设置linux下启动时窗口最大化
            #self.attributes("-fullscreen", True)
            w = self.winfo_screenwidth()
            h = self.winfo_screenheight()
            self.geometry("%dx%d" %(w, h))
        
    def GetLocale(self):
        return self.locale

    def OpenCommandLineArgs(self):
        """
        Called to open files that have been passed to the application from the
        command line.
        """
        args = sys.argv[1:]
        self.OpenFileWithArgs(args)

    def OpenFileWithArgs(self,args):
        for arg in args:
            if (not apputils.is_windows() or arg[0] != "/") and arg[0] != '-' and os.path.exists(arg):
                self.GetDocumentManager().CreateDocument(os.path.normpath(arg), DOC_SILENT)

    def GetDocumentManager(self):
        """
        Returns the document manager associated to the DocApp.
        """
        return self._docManager

    def SetDocumentManager(self, docManager):
        """
        Sets the document manager associated with the DocApp and loads the
        DocApp's file history into the document manager.
        """
        self._docManager = docManager
        config = self.GetConfig()
        #加载历史文件记录
        self.GetDocumentManager().FileHistoryLoad(config)

    def ShowTip(self, frame, tipProvider):
        """
        Shows the tip window, generally this is called when an application starts.
        A wx.TipProvider must be passed.
        """
        config = wx.ConfigBase_Get()
        showTip = config.ReadInt("ShowTipAtStartup", 1)
        if showTip:
            index = config.ReadInt("TipIndex", 0)
            showTipResult = wx.ShowTip(wx.GetApp().GetTopWindow(), tipProvider, showAtStartup = showTip)
            if showTipResult != showTip:
                config.WriteInt("ShowTipAtStartup", showTipResult)

    def GetDebug(self):
        """
        Returns True if the application is in debug mode.
        """
        return self._debug

    def SetDebug(self, debug):
        """
        Sets the application's debug mode.
        """
        self._debug = debug
        
    def SetAppName(self,app_name):
        self._app_name = app_name
        self.title(self._app_name)
        
    def GetAppName(self):
        return self._app_name

    def GetSingleInstance(self):
        """
        Returns True if the application is in single instance mode.  Used to determine if multiple instances of the application is allowed to launch.
        """
        return self._singleInstance

    def SetSingleInstance(self, singleInstance):
        """
        Sets application's single instance mode.
        """
        self._singleInstance = singleInstance

    def OnInit(self):
        """
        Initializes the App.
        """

        if not hasattr(self, "_debug"):  # only set if not already initialized
            self._debug = False
        if not hasattr(self, "_singleInstance"):  # only set if not already initialized
            self._singleInstance = True
        # if _singleInstance is TRUE only allow one single instance of app to run.
        # When user tries to run a second instance of the app, abort startup,
        # But if user also specifies files to open in command line, send message to running app to open those files
        self.initializing = True
        if self._singleInstance:
            # create shared memory temporary file
            if apputils.is_windows():
                tfile = tempfile.TemporaryFile(prefix="ag", suffix="tmp")
                fno = tfile.fileno()
                self._sharedMemory = mmap.mmap(fno, 1024, "shared_memory")
            else:
                tfile = open(os.path.join(tempfile.gettempdir(), tempfile.gettempprefix() + self.GetAppName() + "NovalSharedMemory"), 'w+b')
                if utils.is_py2():
                    tfile.write("*")
                    tfile.seek(1024)
                    tfile.write(" ")
                elif utils.is_py3_plus():
                    tfile.write(bytes("*",'ascii'))
                    tfile.seek(1024)
                    tfile.write(bytes(" ",'ascii'))
                tfile.flush()
                fno = tfile.fileno()
                self._sharedMemory = mmap.mmap(fno, 1024)

            self._singleInstanceChecker = check.SingleInstanceChecker()
            #仅允许一个实例运行
            if self._singleInstanceChecker.IsAnotherRunning():
                utils.get_logger().info('another instance is running,exit now....')
                # have running single instance open file arguments
                
                data = pickle.dumps(sys.argv[1:])
                while 1:
                    self._sharedMemory.seek(0)
                    marker = self._sharedMemory.read_byte()
                    #ord是将asc字符转换成数字,chr是将数字转换成asc字符
                    if marker == '\0' or marker == ord('\0') or marker == '*' or marker == ord('*'):        # available buffer
                        self._sharedMemory.seek(0)
                        if type(marker) == int:
                            self._sharedMemory.write_byte(ord('-'))     # set writing marker
                            self._sharedMemory.write(data)  # write files we tried to open to shared memory
                            self._sharedMemory.seek(0)
                            self._sharedMemory.write_byte(ord('+'))     # set finished writing marker
                        elif type(marker) == str:
                            self._sharedMemory.write_byte('-')     # set writing marker
                            self._sharedMemory.write(data)  # write files we tried to open to shared memory
                            self._sharedMemory.seek(0)
                            self._sharedMemory.write_byte('+')     # set finished writing marker
                        self._sharedMemory.flush()
                        break
                    else:
                        time.sleep(1)  # give enough time for buffer to be available

                return False
            else:
                self.DoBackgroundListenAndLoad()

        return True
        
    #统计程序启动时间
    @utils.compute_run_time
    def _BootstrapApp(self):
        if not self.OnInit():
            self.destroy()
            sys.exit(0)

    def DoBackgroundListenAndLoad(self):
        """
        Open any files specified in the given command line argument passed in via shared memory
        """
        if not hasattr(self, "_singleInstanceChecker"):
            utils.get_logger().warn('application has been quit,stop background listen and load')
            return
        self.after(1000,self.DoBackgroundListenAndLoad)
        self._sharedMemory.seek(0)
        byte = self._sharedMemory.read_byte()
        if  byte == '+' or byte == ord('+'):  # available data
            data = self._sharedMemory.read(1024-1)
            self._sharedMemory.seek(0)
            if utils.is_py2():
                self._sharedMemory.write_byte("*")
            elif utils.is_py3_plus():
                self._sharedMemory.write_byte(ord("*"))     # finished reading, set buffer free marker
            self._sharedMemory.flush()
            args = pickle.loads(data)
            self.OpenFileWithArgs(args)
            # force display of running app
            self.RaiseWindow()
        
    def GetConfig(self):
        return self._config
        
    def SetDefaultIcon(self, img):
        """
        Sets the application's default icon.
        """
      #  self.tk.call('wm', 'iconphoto', self._w, img)
        #default表示设置所有对话框默认图标为app图标
        self.tk.call('wm', 'iconphoto', self._w, '-default', img)
    
    def Quit(self):
        self._docManager.FileHistorySave(GetApp().GetConfig())
        if hasattr(self, "_singleInstanceChecker"):
            self._sharedMemory.close()
            del self._singleInstanceChecker
        #在使用mtTkinter来启动线程后,退出程序时不能调用quit方法,否则会让程序卡死
        if utils.is_py2():
            tk.Tk.destroy(self)
        else:
            tk.Tk.quit(self)

    def RaiseWindow(self, force=True):
        '''
            将程序窗口置于桌面前台
        '''
        # Looks like at least on Windows all following is required
        # for ensuring the window gets focus
        # (deiconify, ..., iconify, deiconify)
        self.deiconify()
        if force:
            self.attributes("-topmost", True)
            self.after_idle(self.attributes, "-topmost", False)
            self.lift()
            if not utils.is_linux():
                # http://stackoverflow.com/a/13867710/261181
                #最小化窗口
                self.iconify()
                self.deiconify()
        self.focus_set()

    def CreateDocumentFrame(self, view, doc, flags, id = -1, title = ""):
        """
        Called by the DocManager to create and return a new Frame for a Document.
        Chooses whether to create an MDIChildFrame or SDI Frame based on the
        DocManager's flags.
        """
        frame = self.CreateTabbedDocumentFrame(doc, view, id, title)
        #if not frame.GetIcon() and self._defaultIcon:
         #   frame.SetIcon(self.GetDefaultIcon())
        view.SetFrame(frame)
        return frame

    def CreateTabbedDocumentFrame(self, doc, view, id=-1, title=""):
        """
        Creates and returns an MDI Document Frame for a Tabbed MDI view
        """
        frame = DocTabbedChildFrame(doc, view, self.MainFrame, id, title)
        return frame
        
    def GetTopWindow(self):
        return self.frame

    def ShowSplash(self, image_path):
        """
        Shows a splash window with the given image.  Input parameter 'image' can either be a wx.Bitmap or a filename.
        """
        self._splash = ui_base.SplashScreen(self,image_path)
        self._splash.Show()
        #隐藏主窗口
        self.withdraw()
        self.attributes("-alpha", 0)
        

    def CloseSplash(self):
        """
        Closes the splash window.
        """
        if self._splash:
            self._splash.Close()
            
    def GetIDESplashBitmap(self):
        return None
        
    def GetDefaultPaneWidth(self):
        return int(self.winfo_screenwidth()/6)
        
    def GetDefaultPaneHeight(self):
        return int(self.winfo_screenheight()/7)
        
    def ToggleFullScreen(self):
        self._is_full_screen = not self._is_full_screen
        self.attributes("-fullscreen", self._is_full_screen)

    @property
    def IsFullScreen(self):
        return self._is_full_screen
        
    @property
    def TheClipboard(self):
        if self._clip_board is None:
            self._clip_board = Clipboard()
        return self._clip_board
        
class DocManager(object):

    def __init__(self, flags=DEFAULT_DOCMAN_FLAGS, initialize=True):
        """
        Constructor. Create a document manager instance dynamically near the
        start of your application before doing any document or view operations.

        flags is used in the Python version to indicate whether the document
        manager is in DOC_SDI or DOC_MDI mode.

        If initialize is true, the Initialize function will be called to
        create a default history list object. If you derive from wxDocManager,
        you may wish to call the base constructor with false, and then call
        Initialize in your own constructor, to allow your own Initialize or
        OnCreateFileHistory functions to be called.
        """

            
        self._defaultDocumentNameCounter = 1
        self._flags = flags
        self._currentView = None
        self._lastActiveView = None
        self._maxDocsOpen = 10000
        self._fileHistory = None
        self._templates = []
        self._docs = []
        self._lastDirectory = ""
        
        if initialize:
            #初始化历史文件存储列表
            self.Initialize()

    def GetFlags(self):
        """
        Returns the document manager's flags.  This method has been
        added to wxPython and is not in wxWindows.
        """
        return self._flags

    def CloseDocument(self, doc, force=True):
        """
        Closes the specified document.
        """
        if doc.Close() or force:
            doc.DeleteAllViews()
            if doc in self._docs:
                doc.Destroy()
            return True
        return False


    def CloseDocuments(self, force=True):
        """
        Closes all currently opened documents.
        """
        for document in self._docs[::-1]:  # Close in lifo (reverse) order.  We clone the list to make sure we go through all docs even as they are deleted
            if not self.CloseDocument(document, force):
                return False
           # if document:
            #    document.DeleteAllViews() # Implicitly delete the document when the last view is removed
        return True


    def Clear(self, force=True):
        """
        Closes all currently opened document by callling CloseDocuments and
        clears the document manager's templates.
        """
        if not self.CloseDocuments(force):
            return False
        self._templates = []
        return True


    def Initialize(self):
        """
        Initializes data; currently just calls OnCreateFileHistory. Some data
        cannot always be initialized in the constructor because the programmer
        must be given the opportunity to override functionality. In fact
        Initialize is called from the wxDocManager constructor, but this can
        be vetoed by passing false to the second argument, allowing the
        derived class's constructor to call Initialize, possibly calling a
        different OnCreateFileHistory from the default.

        The bottom line: if you're not deriving from Initialize, forget it and
        construct wxDocManager with no arguments.
        """
        self.OnCreateFileHistory()
        return True
        
    def GetDocument(self,filename):
        foundDoc = None
        openDocs = self.GetDocuments()
        for openDoc in openDocs:
            if os.path.normcase(openDoc.GetFilename()) == os.path.normcase(filename):
                foundDoc = openDoc
                break
        return foundDoc

    def OnCreateFileHistory(self):
        """
        A hook to allow a derived class to create a different type of file
        history. Called from Initialize.
        """
        self._fileHistory = wx.FileHistory()

    def GetCurrentView(self):
        """
        Returns the currently active view.
        """
        if self._currentView:
            return self._currentView
        if len(self._docs) == 1:
            return self._docs[0].GetFirstView()
        return None


    def GetLastActiveView(self):
        """
        Returns the last active view.  This is used in the SDI framework where dialogs can be mistaken for a view
        and causes the framework to deactivete the current view.  This happens when something like a custom dialog box used
        to operate on the current view is shown.
        """
        if len(self._docs) >= 1:
            return self._lastActiveView
        else:
            return None

    def SelectDocumentPath(self, templates, flags, save):
        """
        Under Windows, pops up a file selector with a list of filters
        corresponding to document templates. The wxDocTemplate corresponding
        to the selected file's extension is returned.

        On other platforms, if there is more than one document template a
        choice list is popped up, followed by a file selector.

        This function is used in wxDocManager.CreateDocument.
        """
        descrs = strutils.gen_file_filters()
        #注意这里最好不要设置initialdir,会自动选择上一次打开的目录
        paths = filedialog.askopenfilename(
                master=GetApp(),
                filetypes=descrs,
                multiple=True
        )
        path_templates = []
        if paths:
            for path in paths:
                #将路径转换成操作系统下标准的路径格式
                path = os.path.abspath(path)
                theTemplate = self.FindTemplateForPath(path)
                path_templates.append((theTemplate, path),)
        
        return path_templates      

    def OnFileSaveAs(self, event):
        doc = self.GetCurrentDocument()
        if not doc:
            return
        doc.SaveAs()

    def OnCreateFileHistory(self):
        """
        A hook to allow a derived class to create a different type of file
        history. Called from Initialize.
        """
        max_files = utils.profile_get_int(consts.MRU_LENGTH_KEY,consts.DEFAULT_MRU_FILE_NUM)
        if max_files > consts.MAX_MRU_FILE_LIMIT:
            max_files = consts.MAX_MRU_FILE_LIMIT
        enableMRU = utils.profile_get_int(consts.ENABLE_MRU_KEY, True)
        if enableMRU:
            self._fileHistory = ui_utils.FileHistory(maxFiles=max_files,idBase=ID_MRU_FILE1)
            
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


        default_document_type = utils.profile_get(consts.DEFAULT_DOCUMENT_TYPE_KEY,GetApp().GetDefaultTextDocumentType())
        default_document_template = self.FindTemplateForDocumentType(default_document_type)
        strings = []
        default_document_selection = -1
        for i,temp in enumerate(templates):
            if temp == default_document_template:
                default_document_selection = i
            strings.append(temp.GetDescription())
            
        res = ui_base.GetNewDocumentChoiceIndex(GetApp(),strings,default_document_selection)
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
        if path and flags & DOC_OPEN_ONCE:
            found_view = self.GetDocument(path)
            if found_view:
                if found_view and found_view.GetFrame() and not (flags & DOC_NO_VIEW):
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
        

    def CreateDocument(self, path, flags=0):
        """
        Creates a new document in a manner determined by the flags parameter,
        which can be:

        wx.lib.docview.DOC_NEW Creates a fresh document.
        wx.lib.docview.DOC_SILENT Silently loads the given document file.

        If wx.lib.docview.DOC_NEW is present, a new document will be created and returned,
        possibly after asking the user for a template to use if there is more
        than one document template. If wx.lib.docview.DOC_SILENT is present, a new document
        will be created and the given file loaded into it. If neither of these
        flags is present, the user will be presented with a file selector for
        the file to load, and the template to use will be determined by the
        extension (Windows) or by popping up a template choice list (other
        platforms).

        If the maximum number of documents has been reached, this function
        will delete the oldest currently loaded document before creating a new
        one.

        wxPython version supports the document manager's wx.lib.docview.DOC_OPEN_ONCE
        and wx.lib.docview.DOC_NO_VIEW flag.
        
        if wx.lib.docview.DOC_OPEN_ONCE is present, trying to open the same file multiple 
        times will just return the same document.
        if wx.lib.docview.DOC_NO_VIEW is present, opening a file will generate the document,
        but not generate a corresponding view.
            manager里面CreateDocument除了创建文档,还加载文档内容
            template里面CreateDocument只是创建文档对象,并没有加载文档内容
        """
        templates = []
        for temp in self._templates:
            if temp.IsVisible():
                templates.append(temp)
        if len(templates) == 0:
            utils.get_logger().error("app has no visible templates")
            return []

        if len(self.GetDocuments()) >= self._maxDocsOpen:
           doc = self.GetDocuments()[0]
           if not self.CloseDocument(doc, False):
               return []

        if flags & DOC_NEW:
            for temp in templates[:]:
                if not temp.IsNewable():
                    templates.remove(temp)
            if len(templates) == 1:
                temp = templates[0]
            else:
                temp = self.SelectDocumentType(templates)
            if temp:
                newDoc = temp.CreateDocument(path, flags)
                if newDoc:
                    newDoc.SetDocumentName(temp.GetDocumentName())
                    newDoc.SetDocumentTemplate(temp)
                    newDoc.OnNewDocument()
                return newDoc
            else:
                return None

        if path and flags & DOC_SILENT:
            temp = self.FindTemplateForPath(path)
            path_templates = [(temp,path),]
        else:
            path_templates = self.SelectDocumentPath(templates, path, flags)
            
        ret_docs = []

        for temp, path in path_templates:
            # Existing document
            if path and self.GetFlags() & DOC_OPEN_ONCE:
                doc_exists = False
                for document in self._docs:
                    if document.GetFilename() and os.path.normcase(document.GetFilename()) == os.path.normcase(path):
                        """ check for file modification outside of application """
                        if not document.IsDocumentModificationDateCorrect():
                            msgTitle = GetApp().GetAppName()
                            if not msgTitle:
                                msgTitle = _("Warning")
                            shortName = document.GetPrintableName()
                            answer = messagebox.askyesno(_("Reload.."),_("File \"%s\" has already been modified outside,Do You Want to reload it?") % shortName)
                            if answer == True:
                               if not self.CloseDocument(document, False):
                                   messagebox.showwarning(msgTitle,_("Couldn't reload '%s'.  Unable to close current '%s'.") % (shortName, shortName))
                                   return None
                               return self.CreateDocument(path, flags)
                            else:  # don't ask again
                                document.SetDocumentModificationDate()

                        firstView = document.GetFirstView()
                        if not firstView and not (flags & wx.lib.docview.DOC_NO_VIEW):
                            document.GetDocumentTemplate().CreateView(document, flags)
                            document.UpdateAllViews()
                            firstView = document.GetFirstView()
                            
                        if firstView and firstView.GetFrame() and not (flags & DOC_NO_VIEW):
                            firstView.GetFrame().SetFocus()  # Not in wxWindows code but useful nonetheless
                            if hasattr(firstView.GetFrame(), "IsIconized") and firstView.GetFrame().IsIconized():  # Not in wxWindows code but useful nonetheless
                                firstView.GetFrame().Iconize(False)
                        ###return None
                        doc_exists = True
                        ret_docs.append(document)
                        break

            if temp and not doc_exists:
                newDoc = temp.CreateDocument(path, flags)
                #创建文档成功
                if newDoc:
                    newDoc.SetDocumentName(temp.GetDocumentName())
                    newDoc.SetDocumentTemplate(temp)
                    if not newDoc.OnOpenDocument(path):
                        frame = newDoc.GetFirstView().GetFrame()
                        #这里销毁文档的时候有可能已经把文档框架对象也同时销毁了
                        newDoc.DeleteAllViews()  # Implicitly deleted by DeleteAllViews
                        if frame:
                            #这里销毁文档框架的时候需要判断文档框架是否已经不存在了
                            frame.Destroy() # DeleteAllViews doesn't get rid of the frame, so we'll explicitly destroy it.
                        return []
                    self.AddFileToHistory(path)
                    ret_docs.append(newDoc)

        return ret_docs
        

    def CreateView(self, doc, flags=0):
        """
        Creates a new view for the given document. If more than one view is
        allowed for the document (by virtue of multiple templates mentioning
        the same document type), a choice of view is presented to the user.
        """
        templates = []
        for temp in self._templates:
            if temp.IsVisible():
                if temp.GetDocumentName() == doc.GetDocumentName():
                    templates.append(temp)
        if len(templates) == 0:
            return None

        if len(templates) == 1:
            temp = templates[0]
            view = temp.CreateView(doc, flags)
            if view:
                view.SetViewName(temp.GetViewName())
            return view

        temp = SelectViewType(templates)
        if temp:
            view = temp.CreateView(doc, flags)
            if view:
                view.SetViewName(temp.GetViewName())
            return view
        else:
            return None
            

    def GetCurrentDocument(self):
        """
        Returns the document associated with the currently active view (if any).
        """
        view = self.GetCurrentView()
        if view:
            return view.GetDocument()
        else:
            return None
            

    def AddFileToHistory(self, fileName):
        """
        Adds a file to the file history list, if we have a pointer to an
        appropriate file menu.
        """
        if self._fileHistory is not None:
            self._fileHistory.AddFileToHistory(fileName)


    def RemoveFileFromHistory(self, i):
        """
        Removes a file from the file history list, if we have a pointer to an
        appropriate file menu.
        """
        if self._fileHistory:
            self._fileHistory.RemoveFileFromHistory(i)


    def GetFileHistory(self):
        """
        Returns the file history.
        """
        return self._fileHistory


    def GetHistoryFile(self, i):
        """
        Returns the file at index i from the file history.
        """
        if self._fileHistory:
            return self._fileHistory.GetHistoryFile(i)
        else:
            return None


    def FileHistoryUseMenu(self, menu):
        """
        Use this menu for appending recently-visited document filenames, for
        convenient access. Calling this function with a valid menu enables the
        history list functionality.

        Note that you can add multiple menus using this function, to be
        managed by the file history object.
        """
        if self._fileHistory is not None:
            self._fileHistory.UseMenu(menu)
            

    def FileHistoryRemoveMenu(self, menu):
        """
        Removes the given menu from the list of menus managed by the file
        history object.
        """
        if self._fileHistory:
            self._fileHistory.RemoveMenu(menu)


    def FileHistoryLoad(self, config):
        """
        Loads the file history from a config object.
        """
        if self._fileHistory is not None:
            self._fileHistory.Load(config)


    def FileHistorySave(self, config):
        """
        Saves the file history into a config object. This must be called
        explicitly by the application.
        """
        if self._fileHistory:
            self._fileHistory.Save(config)
            

    def FileHistoryAddFilesToMenu(self, menu=None):
        """
        Appends the files in the history list, to all menus managed by the
        file history object.

        If menu is specified, appends the files in the history list to the
        given menu only.
        """
        if self._fileHistory is not None:
            if menu:
                self._fileHistory.AddFilesToThisMenu(menu)
            else:
                self._fileHistory.AddFilesToMenu()


    def GetHistoryFilesCount(self):
        """
        Returns the number of files currently stored in the file history.
        """
        if self._fileHistory:
            return self._fileHistory.GetNoHistoryFiles()
        else:
            return 0
            

    def FindTemplateForPath(self, path):
        """
        Given a path, try to find template that matches the extension. This is
        only an approximate method of finding a template for creating a
        document.
        
        Note this wxPython verson looks for and returns a default template if no specific template is found.
        """
        default = None
        for temp in self._templates:
            if temp.FileMatchesTemplate(path):
                return temp
                
            if "*.*" in temp.GetFileFilter():
                default = temp
        return default
        
    def FindTemplateForTestPath(self, ext):
        '''
            根据扩展名获取对应的模板,通过扩展名组成一个测试文件名来获取对应的模板
        '''
        assert("." in ext)
        return self.FindTemplateForPath("test"+ext)

    def SelectViewType(self, temps, sort=False):
        """
        Returns a document template by asking the user (if there is more than one template), displaying a list of valid views. This function is used in wxDocManager::CreateView. The dialog normally will not appear because the array of templates only contains those relevant to the document in question, and often there will only be one such.
        """
        templates = []
        strings = []
        for temp in temps:
            if temp.IsVisible() and temp.GetViewTypeName():
                if temp.GetViewName() not in strings:
                    templates.append(temp)
                    strings.append(temp.GetViewTypeName())

        if len(templates) == 0:
            return None
        elif len(templates) == 1:
            return templates[0]

        if sort:
            def tempcmp(a, b):
                return cmp(a.GetViewTypeName(), b.GetViewTypeName())
            templates.sort(tempcmp)

        res = wx.GetSingleChoiceIndex(_("Select a document view:"),
                                      _("Views"),
                                      strings,
                                      self.FindSuitableParent())
        if res == -1:
            return None
        return templates[res]


    def GetTemplates(self):
        """
        Returns the document manager's template list.  This method has been added to
        wxPython and is not in wxWindows.
        """
        return self._templates

    def AssociateTemplate(self, docTemplate):
        """
        Adds the template to the document manager's template list.
        """
        if docTemplate not in self._templates:
            self._templates.append(docTemplate)


    def DisassociateTemplate(self, docTemplate):
        """
        Removes the template from the list of templates.
        """
        self._templates.remove(docTemplate)


    def AddDocument(self, document):
        """
        Adds the document to the list of documents.
        """
        if document not in self._docs:
            self._docs.append(document)


    def RemoveDocument(self, doc):
        """
        Removes the document from the list of documents.
        """
        if doc in self._docs:
            self._docs.remove(doc)


    def ActivateView(self, view, activate=True, deleting=False):
        """
        Sets the current view.
        """
        if activate:
            self._currentView = view
            self._lastActiveView = view
        else:
            self._currentView = None


    def GetMaxDocsOpen(self):
        """
        Returns the number of documents that can be open simultaneously.
        """
        return self._maxDocsOpen


    def SetMaxDocsOpen(self, maxDocsOpen):
        """
        Sets the maximum number of documents that can be open at a time. By
        default, this is 10,000. If you set it to 1, existing documents will
        be saved and deleted when the user tries to open or create a new one
        (similar to the behaviour of Windows Write, for example). Allowing
        multiple documents gives behaviour more akin to MS Word and other
        Multiple Document Interface applications.
        """
        self._maxDocsOpen = maxDocsOpen


    def GetDocuments(self):
        """
        Returns the list of documents.
        """
        return self._docs
        

    def MakeDefaultName(self):
        """
        Returns a suitable default name. This is implemented by appending an
        integer counter to the string "Untitled" and incrementing the counter.
        """
        name = _("Untitled %d") % self._defaultDocumentNameCounter
        self._defaultDocumentNameCounter = self._defaultDocumentNameCounter + 1
        return name

class DocTemplate(object):
    """
    The wxDocTemplate class is used to model the relationship between a
    document class and a view class.
    """


    def __init__(self, manager, description, filter, dir, ext, docTypeName, viewTypeName, docType, viewType, flags=DEFAULT_TEMPLATE_FLAGS, icon=None):
        """
        Constructor. Create instances dynamically near the start of your
        application after creating a wxDocManager instance, and before doing
        any document or view operations.

        manager is the document manager object which manages this template.

        description is a short description of what the template is for. This
        string will be displayed in the file filter list of Windows file
        selectors.

        filter is an appropriate file filter such as \*.txt.

        dir is the default directory to use for file selectors.

        ext is the default file extension (such as txt).

        docTypeName is a name that should be unique for a given type of
        document, used for gathering a list of views relevant to a
        particular document.

        viewTypeName is a name that should be unique for a given view.

        docClass is a Python class. If this is not supplied, you will need to
        derive a new wxDocTemplate class and override the CreateDocument
        member to return a new document instance on demand.

        viewClass is a Python class. If this is not supplied, you will need to
        derive a new wxDocTemplate class and override the CreateView member to
        return a new view instance on demand.

        flags is a bit list of the following:
        wx.TEMPLATE_VISIBLE The template may be displayed to the user in
        dialogs.

        wx.TEMPLATE_INVISIBLE The template may not be displayed to the user in
        dialogs.

        wx.DEFAULT_TEMPLATE_FLAGS Defined as wxTEMPLATE_VISIBLE.
        """
        self._docManager = manager
        self._description = description
        self._fileFilter = filter
        self._directory = dir
        self._defaultExt = ext
        self._docTypeName = docTypeName
        self._viewTypeName = viewTypeName
        self._docType = docType
        self._viewType = viewType
        self._flags = flags
        self._icon = icon

        self._docManager.AssociateTemplate(self)


    def GetDefaultExtension(self):
        """
        Returns the default file extension for the document data, as passed to
        the document template constructor.
        """
        return self._defaultExt


    def SetDefaultExtension(self, defaultExt):
        """
        Sets the default file extension.
        """
        self._defaultExt = defaultExt


    def GetDescription(self):
        """
        Returns the text description of this template, as passed to the
        document template constructor.
        """
        return self._description


    def SetDescription(self, description):
        """
        Sets the template description.
        """
        self._description = description


    def GetDirectory(self):
        """
        Returns the default directory, as passed to the document template
        constructor.
        """
        return self._directory


    def SetDirectory(self, dir):
        """
        Sets the default directory.
        """
        self._directory = dir


    def GetDocumentManager(self):
        """
        Returns the document manager instance for which this template was
        created.
        """
        return self._docManager


    def SetDocumentManager(self, manager):
        """
        Sets the document manager instance for which this template was
        created. Should not be called by the application.
        """
        self._docManager = manager


    def GetFileFilter(self):
        """
        Returns the file filter, as passed to the document template
        constructor.
        """
        return self._fileFilter


    def SetFileFilter(self, filter):
        """
        Sets the file filter.
        """
        self._fileFilter = filter


    def GetFlags(self):
        """
        Returns the flags, as passed to the document template constructor.
        (see the constructor description for more details).
        """
        return self._flags


    def SetFlags(self, flags):
        """
        Sets the internal document template flags (see the constructor
        description for more details).
        """
        self._flags = flags


    def GetIcon(self):
        """
        Returns the icon, as passed to the document template
        constructor.  This method has been added to wxPython and is
        not in wxWindows.
        """
        return self._icon


    def SetIcon(self, flags):
        """
        Sets the icon.  This method has been added to wxPython and is not
        in wxWindows.
        """
        self._icon = icon


    def GetDocumentType(self):
        """
        Returns the Python document class, as passed to the document template
        constructor.
        """
        return self._docType


    def GetViewType(self):
        """
        Returns the Python view class, as passed to the document template
        constructor.
        """
        return self._viewType


    def IsVisible(self):
        """
        Returns true if the document template can be shown in user dialogs,
        false otherwise.
        """
        return (self._flags & TEMPLATE_VISIBLE) == TEMPLATE_VISIBLE


    def IsNewable(self):
        """
        Returns true if the document template can be shown in "New" dialogs,
        false otherwise.
        
        This method has been added to wxPython and is not in wxWindows.
        """
        return (self._flags & TEMPLATE_NO_CREATE) != TEMPLATE_NO_CREATE
        

    def GetDocumentName(self):
        """
        Returns the document type name, as passed to the document template
        constructor.
        """
        return self._docTypeName


    def GetViewName(self):
        """
        Returns the view type name, as passed to the document template
        constructor.
        """
        return self._viewTypeName


    def CreateDocument(self, path, flags):
        """
        Creates a new instance of the associated document class. If you have
        not supplied a class to the template constructor, you will need to
        override this function to return an appropriate document instance.
            这里CreateDocument只是创建文档对象,并不加载文档内容
        """
        doc = self._docType()
        doc.SetFilename(path)
        doc.SetDocumentTemplate(self)
        self.GetDocumentManager().AddDocument(doc)
        if doc.OnCreate(path, flags):
            return doc
        else:
            if doc in self.GetDocumentManager().GetDocuments():
                doc.DeleteAllViews()
            return None


    def CreateView(self, doc, flags):
        """
        Creates a new instance of the associated document view. If you have
        not supplied a class to the template constructor, you will need to
        override this function to return an appropriate view instance.
        """
        view = self._viewType()
        view.SetDocument(doc)
        if view.OnCreate(doc, flags):
            return view
        else:
            view.Destroy()
            return None


    def FileMatchesTemplate(self, path):
        """
        Returns True if the path's extension matches one of this template's
        file filter extensions.
        """
        ext = strutils.get_file_extension(path,has_dot=True)
        if not ext: return False
        
        extList = self.GetFileFilter().replace('*','').split(';')
        return ext in extList
        


class Document(object):
    """
    The document class can be used to model an application's file-based data. It
    is part of the document/view framework supported by wxWindows, and cooperates
    with the wxView, wxDocTemplate and wxDocManager classes.
    
    Note this wxPython version also keeps track of the modification date of the
    document and if it changes on disk outside of the application, we will warn the
    user before saving to avoid clobbering the file.
    """


    def __init__(self, parent=None):
        """
        Constructor.  Define your own default constructor to initialize
        application-specific data.
        """
        self._documentParent = parent
        self._documentTemplate = None
        self._commandProcessor = None
        self._savedYet = False
        self._writeable = True

        self._documentTitle = None
        self._documentFile = None
        self._documentTypeName = None
        self._documentModified = False
        self._documentModificationDate = None
        self._documentViews = []

    def GetFilename(self):
        """
        Gets the filename associated with this document, or "" if none is
        associated.
        """
        return self._documentFile

    def GetTitle(self):
        """
        Gets the title for this document. The document title is used for an
        associated frame (if any), and is usually constructed by the framework
        from the filename.
        """
        return self._documentTitle


    def SetTitle(self, title):
        """
        Sets the title for this document. The document title is used for an
        associated frame (if any), and is usually constructed by the framework
        from the filename.
        """
        self._documentTitle = title


    def GetDocumentName(self):
        """
        The document type name given to the wxDocTemplate constructor,
        copied to this document when the document is created. If several
        document templates are created that use the same document type, this
        variable is used in wxDocManager::CreateView to collate a list of
        alternative view types that can be used on this kind of document.
        """
        return self._documentTypeName


    def SetDocumentName(self, name):
        """
        Sets he document type name given to the wxDocTemplate constructor,
        copied to this document when the document is created. If several
        document templates are created that use the same document type, this
        variable is used in wxDocManager::CreateView to collate a list of
        alternative view types that can be used on this kind of document. Do
        not change the value of this variable.
        """
        self._documentTypeName = name


    def GetDocumentSaved(self):
        """
        Returns True if the document has been saved.  This method has been
        added to wxPython and is not in wxWindows.
        """
        return self._savedYet


    def SetDocumentSaved(self, saved=True):
        """
        Sets whether the document has been saved.  This method has been
        added to wxPython and is not in wxWindows.
        """
        self._savedYet = saved


    def IsModified(self):
        """
        Returns true if the document has been modified since the last save,
        false otherwise. You may need to override this if your document view
        maintains its own record of being modified (for example if using
        wxTextWindow to view and edit the document).
        """
        return self._documentModified


    def Modify(self, modify):
        """
        Call with true to mark the document as modified since the last save,
        false otherwise. You may need to override this if your document view
        maintains its own record of being modified (for example if using
        xTextWindow to view and edit the document).
        This method has been extended to notify its views that the dirty flag has changed.
        """
        self._documentModified = modify
        self.UpdateAllViews(hint=("modify", self, self._documentModified))


    def SetDocumentModificationDate(self):
        """
        Saves the file's last modification date.
        This is used to check if the file has been modified outside of the application.
        This method has been added to wxPython and is not in wxWindows.
        """
        self._documentModificationDate = os.path.getmtime(self.GetFilename())


    def GetDocumentModificationDate(self):
        """
        Returns the file's modification date when it was loaded from disk.
        This is used to check if the file has been modified outside of the application.        
        This method has been added to wxPython and is not in wxWindows.
        """
        return self._documentModificationDate


    def IsDocumentModificationDateCorrect(self):
        """
        Returns False if the file has been modified outside of the application.
        This method has been added to wxPython and is not in wxWindows.
        """
        if not os.path.exists(self.GetFilename()):  # document must be in memory only and can't be out of date
            return True
        return self._documentModificationDate == os.path.getmtime(self.GetFilename())


    def GetViews(self):
        """
        Returns the list whose elements are the views on the document.
        """
        return self._documentViews


    def GetDocumentTemplate(self):
        """
        Returns the template that created the document.
        """
        return self._documentTemplate


    def SetDocumentTemplate(self, template):
        """
        Sets the template that created the document. Should only be called by
        the framework.
        """
        self._documentTemplate = template


    def DeleteContents(self):
        """
        Deletes the contents of the document.  Override this method as
        necessary.
        """
        return True


    def Destroy(self):
        """
        Destructor. Removes itself from the document manager.
        """
        self.DeleteContents()
        self._documentModificationDate = None
        if self.GetDocumentManager():
            self.GetDocumentManager().RemoveDocument(self)

    def Close(self):
        """
        Closes the document, by calling OnSaveModified and then (if this true)
        OnCloseDocument. This does not normally delete the document object:
        use DeleteAllViews to do this implicitly.
        """
        if self.OnSaveModified():
            if self.OnCloseDocument():
                return True
            else:
                return False
        else:
            return False

    def OnCloseDocument(self):
        """
        The default implementation calls DeleteContents (an empty
        implementation) sets the modified flag to false. Override this to
        supply additional behaviour when the document is closed with Close.
        """
        self.NotifyClosing()
        self.DeleteContents()
        self.Modify(False)
        return True


    def DeleteAllViews(self):
        """
        Calls wxView.Close and deletes each view. Deleting the final view will
        implicitly delete the document itself, because the wxView destructor
        calls RemoveView. This in turns calls wxDocument::OnChangedViewList,
        whose default implemention is to save and delete the document if no
        views exist.
        """
        manager = self.GetDocumentManager()
        for view in self._documentViews:
            if not view.Close():
                return False
        if self in manager.GetDocuments():
            self.Destroy()
        return True


    def GetFirstView(self):
        """
        A convenience function to get the first view for a document, because
        in many cases a document will only have a single view.
        """
        if len(self._documentViews) == 0:
            return None
        return self._documentViews[0]


    def GetDocumentManager(self):
        """
        Returns the associated document manager.
        """
        if self._documentTemplate:
            return self._documentTemplate.GetDocumentManager()
        return None

    def OnNewDocument(self):
        """
        The default implementation calls OnSaveModified and DeleteContents,
        makes a default title for the document, and notifies the views that
        the filename (in fact, the title) has changed.
        """
        if not self.OnSaveModified() or not self.OnCloseDocument():
            return False
        self.DeleteContents()
        self.Modify(False)
        self.SetDocumentSaved(False)
        name = self.GetDocumentManager().MakeDefaultName()
        self.SetTitle(name)
        self.SetFilename(name, notifyViews = True)

    def Save(self):
        """
        Saves the document by calling OnSaveDocument if there is an associated
        filename, or SaveAs if there is no filename.
        """
        if not self.IsModified():  # and self._savedYet:  This was here, but if it is not modified who cares if it hasn't been saved yet?
            return True

        """ 保存文件之前检测文件是否在外部改变 """
        if not self.IsDocumentModificationDateCorrect():
            msgTitle = GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("Application")
            #如果文件在外部改变,询问用户是否覆盖文件
            res = messagebox.askyesnocancel(msgTitle,_("'%s' has been modified outside of %s.  Overwrite '%s' with current changes?") % \
                                                (self.GetPrintableName(), msgTitle, self.GetPrintableName()))
            #选择否返回False
            if res == False:
                return True
            #选择是返回True
            elif res == True:
                pass
            #选择取消返回None
            else:
                return False
        
        if not self._documentFile or not self._savedYet:
            return self.SaveAs()
        return self.OnSaveDocument(self._documentFile)

    def SaveAs(self):
        """
        Prompts the user for a file to save to, and then calls OnSaveDocument.
        """
        docTemplate = self.GetDocumentTemplate()
        if not docTemplate:
            return False
        filename = filedialog.asksaveasfilename(
            master = GetApp(),
            filetypes = [strutils.get_template_filter(docTemplate),],
            defaultextension=docTemplate.GetDefaultExtension(),
            initialdir=docTemplate.GetDirectory(),
            initialfile=os.path.basename(self.GetFilename())
        )
        if filename == "":
            return False

        name, ext = os.path.splitext(filename)
        if ext == "":
            filename += '.' + docTemplate.GetDefaultExtension()

        self.SetFilename(filename)
        self.SetTitle(FileNameFromPath(filename))

        for view in self._documentViews:
            view.OnChangeFilename()

        if not self.OnSaveDocument(filename):
            return False

        if docTemplate.FileMatchesTemplate(filename):
            self.GetDocumentManager().AddFileToHistory(filename)
            
        return True

    def OnSaveDocument(self, filename):
        """
        Constructs an output file for the given filename (which must
        not be empty), and calls SaveObject. If SaveObject returns true, the
        document is set to unmodified; otherwise, an error message box is
        displayed.
        """
        if not filename:
            return False

        msgTitle = GetApp().GetAppName()
        if not msgTitle:
            msgTitle = _("File Error")

        backupFilename = None
        fileObject = None
        copied = False
        try:
            # if current file exists, move it to a safe place temporarily
            if os.path.exists(filename):

                # Check if read-only.
                if not os.access(filename, os.W_OK):
                    messagebox.showerror(msgTitle,"Could not save '%s'.  No write permission to overwrite existing file." % \
                                         fileutils.get_filename_from_path(filename))
                    return False

                i = 1
                backupFilename = "%s.bak%s" % (filename, i)
                while os.path.exists(backupFilename):
                    i += 1
                    backupFilename = "%s.bak%s" % (filename, i)
                shutil.copy(filename, backupFilename)
                copied = True

            fileObject = open(filename, 'w')
            self.SaveObject(fileObject)
            fileObject.close()
            fileObject = None
            #如果保存成功则删除备份文件
            if backupFilename:
                os.remove(backupFilename)
        except Exception as e:
            # for debugging purposes
            import traceback
            traceback.print_exc()

            if fileObject:
                fileObject.close()  # file is still open, close it, need to do this before removal 

            #如果文件保存失败,则从备份文件恢复原文件,并将备份文件删除,防止生成过多的备份文件
            if backupFilename and copied:
                shutil.copy(backupFilename,filename)
                os.remove(backupFilename)
            messagebox.showerror(msgTitle,"Could not save '%s'.  %s" % (fileutils.get_filename_from_path(filename), str(e)),parent=self.GetDocumentWindow())
            return False

        self.SetDocumentModificationDate()
        self.SetFilename(filename, True)
        self.Modify(False)
        self.SetDocumentSaved(True)
        return True

    def OnOpenDocument(self, filename):
        """
        Constructs an input file for the given filename (which must not
        be empty), and calls LoadObject. If LoadObject returns true, the
        document is set to unmodified; otherwise, an error message box is
        displayed. The document's views are notified that the filename has
        changed, to give windows an opportunity to update their titles. All of
        the document's views are then updated.
        """
        if not self.OnSaveModified():
            return False

        msgTitle = GetApp().GetAppName()
        if not msgTitle:
            msgTitle = _("File Error")

        if utils.is_py2():
            fileObject = file(filename, 'r')
        elif utils.is_py3_plus():
            fileObject = open(filename)
        try:
            self.LoadObject(fileObject)
            fileObject.close()
            fileObject = None
        except:
            # for debugging purposes
            import traceback
            traceback.print_exc()

            if fileObject:
                fileObject.close()  # file is still open, close it 

            wx.MessageBox("Could not open '%s'.  %s" % (FileNameFromPath(filename), sys.exc_value),
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION,
                          self.GetDocumentWindow())
            return False

        self.SetDocumentModificationDate()
        self.SetFilename(filename, True)
        self.Modify(False)
        self.SetDocumentSaved(True)
        self.UpdateAllViews()
        return True


    def LoadObject(self, file):
        """
        Override this function and call it from your own LoadObject before
        loading your own data. LoadObject is called by the framework
        automatically when the document contents need to be loaded.

        Note that the wxPython version simply sends you a Python file object,
        so you can use pickle.
        """
        return True


    def SaveObject(self, file):
        """
        Override this function and call it from your own SaveObject before
        saving your own data. SaveObject is called by the framework
        automatically when the document contents need to be saved.

        Note that the wxPython version simply sends you a Python file object,
        so you can use pickle.
        """
        return True


    def Revert(self):
        """
        Override this function to revert the document to its last saved state.
        """
        return False


    def GetPrintableName(self):
        """
        Copies a suitable document name into the supplied name buffer.
        The default function uses the title, or if there is no title, uses the
        filename; or if no filename, the string 'Untitled'.
        """
        if self._documentTitle:
            return self._documentTitle
        elif self._documentFile:
            return fileutils.get_filename_from_path(self._documentFile)
        else:
            return _("Untitled")


    def GetDocumentWindow(self):
        """
        Intended to return a suitable window for using as a parent for
        document-related dialog boxes. By default, uses the frame associated
        with the first view.
        """
        if len(self._documentViews) > 0:
            return self._documentViews[0].GetFrame()
        else:
            return GetApp().GetTopWindow()

    def OnSaveModified(self):
        """
        If the document has been modified, prompts the user to ask if the
        changes should be changed. If the user replies Yes, the Save function
        is called. If No, the document is marked as unmodified and the
        function succeeds. If Cancel, the function fails.
        """
        if not self.IsModified():
            return True

        """ check for file modification outside of application """
        if not self.IsDocumentModificationDateCorrect():
            msgTitle = GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("Warning")
            #如果文件在外部改变,询问用户是否覆盖文件
            res = messagebox.askyesnocancel(msgTitle,_("'%s' has been modified outside of %s.  Overwrite '%s' with current changes?") % \
                                                (self.GetPrintableName(), msgTitle, self.GetPrintableName()))
    
            if res == False:
                self.Modify(False)
                return True
            elif res == True:
                return Document.Save(self)
            else: # elif res == wx.CANCEL:
                return False

        msgTitle = GetApp().GetAppName()
        if not msgTitle:
            msgTitle = _("Warning")
        #关闭文档之前询问用户是否保存修改
        answer = messagebox.askyesnocancel(msgTitle,_("Save changes to '%s'?") % self.GetPrintableName())
        if answer == False:
            self.Modify(False)
            return True
        elif answer == True:
            return self.Save()
        else: # elif res == wx.CANCEL:
            return False

    def AddView(self, view):
        """
        If the view is not already in the list of views, adds the view and
        calls OnChangedViewList.
        """
        if not view in self._documentViews:
            self._documentViews.append(view)
            self.OnChangedViewList()
        return True


    def RemoveView(self, view):
        """
        Removes the view from the document's list of views, and calls
        OnChangedViewList.
        """
        if view in self._documentViews:
            self._documentViews.remove(view)
            self.OnChangedViewList()
        return True


    def OnCreate(self, path, flags):
        """
        The default implementation calls DeleteContents (an empty
        implementation) sets the modified flag to false. Override this to
        supply additional behaviour when the document is opened with Open.
        """
        if flags & DOC_NO_VIEW:
            return True
        return self.GetDocumentTemplate().CreateView(self, flags)


    def OnChangedViewList(self):
        """
        Called when a view is added to or deleted from this document. The
        default implementation saves and deletes the document if no views
        exist (the last one has just been removed).
        """
        if len(self._documentViews) == 0:
            if self.OnSaveModified():
                pass # C version does a delete but Python will garbage collect


    def UpdateAllViews(self, sender = None, hint = None):
        """
        Updates all views. If sender is non-NULL, does not update this view.
        hint represents optional information to allow a view to optimize its
        update.
        """
        for view in self._documentViews:
            if view != sender:
                view.OnUpdate(sender, hint)

    def NotifyClosing(self):
        """
        Notifies the views that the document is going to close.
        """
        for view in self._documentViews:
            view.OnClosingDocument()


    def SetFilename(self, filename, notifyViews = False):
        """
        Sets the filename for this document. Usually called by the framework.
        If notifyViews is true, wxView.OnChangeFilename is called for all
        views.
        """
        self._documentFile = filename
        if notifyViews:
            for view in self._documentViews:
                view.OnChangeFilename()


    def GetWriteable(self):
        """
        Returns true if the document can be written to its accociated file path.
        This method has been added to wxPython and is not in wxWindows.
        """
        if not self._writeable:
            return False 
        if not self._documentFile:  # Doesn't exist, do a save as
            return True
        else:
            return os.access(self._documentFile, os.W_OK)


    def SetWriteable(self, writeable):
        """
        Set to False if the document can not be saved.  This will disable the ID_SAVE_AS
        event and is useful for custom documents that should not be saveable.  The ID_SAVE
        event can be disabled by never Modifying the document.  This method has been added
        to wxPython and is not in wxWindows.
        """
        self._writeable = writeable


class View(object):
    """
    The view class can be used to model the viewing and editing component of
    an application's file-based data. It is part of the document/view
    framework supported by wxWindows, and cooperates with the wxDocument,
    wxDocTemplate and wxDocManager classes.
    """

    def __init__(self):
        """
        Constructor. Define your own default constructor to initialize
        application-specific data.
        """
        self._viewDocument = None
        self._viewFrame = None


    def Destroy(self):
        """
        Destructor. Removes itself from the document's list of views.
        """
        if self._viewDocument:
            self._viewDocument.RemoveView(self)

    def OnActivateView(self, activate, activeView, deactiveView):
        """
        Called when a view is activated by means of wxView::Activate. The
        default implementation does nothing.
        """
        pass

    def OnClosingDocument(self):
        """
        Override this to clean up the view when the document is being closed.
        The default implementation does nothing.
        """
        pass


    def UpdateUI(self, command_id):
        return False

    def OnPrint(self, dc, info):
        """
        Override this to print the view for the printing framework.  The
        default implementation calls View.OnDraw.
        """
        self.OnDraw(dc)

    def OnUpdate(self, sender, hint):
        """
        Called when the view should be updated. sender is a pointer to the
        view that sent the update request, or NULL if no single view requested
        the update (for instance, when the document is opened). hint is as yet
        unused but may in future contain application-specific information for
        making updating more efficient.
        """
        if hint:
            if hint[0] == "modify":  # if dirty flag changed, update the view's displayed title
                frame = self.GetFrame()
                if frame and hasattr(frame, "OnTitleIsModified"):
                    frame.OnTitleIsModified()
                    return True
        return False

    def OnChangeFilename(self):
        """
        Called when the filename has changed. The default implementation
        constructs a suitable title and sets the title of the view frame (if
        any).
        """
        if self.GetFrame():
            appName = GetApp().GetAppName()
            if not self.GetDocument():
                if appName:
                    title = appName
                else:
                    return
            else:
                title = ''
                self.GetFrame().SetTitle(title + self.GetDocument().GetPrintableName())

    def GetDocument(self):
        """
        Returns the document associated with the view.
        """
        return self._viewDocument

    def SetDocument(self, doc):
        """
        Associates the given document with the view. Normally called by the
        framework.
        """
        self._viewDocument = doc
        if doc:
            doc.AddView(self)


    def GetViewName(self):
        """
        Gets the name associated with the view (passed to the wxDocTemplate
        constructor). Not currently used by the framework.
        """
        return self._viewTypeName


    def SetViewName(self, name):
        """
        Sets the view type name. Should only be called by the framework.
        """
        self._viewTypeName = name


    def Close(self, deleteWindow=True):
        """
        Closes the view by calling OnClose. If deleteWindow is true, this
        function should delete the window associated with the view.
        """
        if self.OnClose(deleteWindow = deleteWindow):
            return True
        else:
            return False


    def Activate(self, activate=True):
        """
        Call this from your view frame's OnActivate member to tell the
        framework which view is currently active. If your windowing system
        doesn't call OnActivate, you may need to call this function from
        OnMenuCommand or any place where you know the view must be active, and
        the framework will need to get the current view.

        The prepackaged view frame wxDocChildFrame calls wxView.Activate from
        its OnActivate member and from its OnMenuCommand member.
        """
        if self.GetDocument() and self.GetDocumentManager():
            self.OnActivateView(activate, self, self.GetDocumentManager().GetCurrentView())
            self.GetDocumentManager().ActivateView(self, activate)


    def OnClose(self, deleteWindow=True):
        """
        Implements closing behaviour. The default implementation calls
        wxDocument.Close to close the associated document. Does not delete the
        view. The application may wish to do some cleaning up operations in
        this function, if a call to wxDocument::Close succeeded. For example,
        if your application's all share the same window, you need to
        disassociate the window from the view and perhaps clear the window. If
        deleteWindow is true, delete the frame associated with the view.
        """
        if self.GetDocument():
            return self.GetDocument().Close()
        else:
            return True


    def OnCreate(self, doc, flags):
        """
        wxDocManager or wxDocument creates a wxView via a wxDocTemplate. Just
        after the wxDocTemplate creates the wxView, it calls wxView::OnCreate.
        In its OnCreate member function, the wxView can create a
        wxDocChildFrame or a derived class. This wxDocChildFrame provides user
        interface elements to view and/or edit the contents of the wxDocument.

        By default, simply returns true. If the function returns false, the
        view will be deleted.
        """
        return True


    def OnCreatePrintout(self):
        """
        Returns a wxPrintout object for the purposes of printing. It should
        create a new object every time it is called; the framework will delete
        objects it creates.

        By default, this function returns an instance of wxDocPrintout, which
        prints and previews one page by calling wxView.OnDraw.

        Override to return an instance of a class other than wxDocPrintout.
        """
        return DocPrintout(self, self.GetDocument().GetPrintableName())


    def GetFrame(self):
        """
        Gets the frame associated with the view (if any). Note that this
        "frame" is not a wxFrame at all in the generic MDI implementation
        which uses the notebook pages instead of the frames and this is why
        this method returns a wxWindow and not a wxFrame.
        """
        return self._viewFrame


    def SetFrame(self, frame):
        """
        Sets the frame associated with this view. The application should call
        this if possible, to tell the view about the frame.  See GetFrame for
        the explanation about the mismatch between the "Frame" in the method
        name and the type of its parameter.
        """
        self._viewFrame = frame


    def GetDocumentManager(self):
        """
        Returns the document manager instance associated with this view.
        """
        if self._viewDocument:
            return self.GetDocument().GetDocumentManager()
        else:
            return None
            
    def SetFocus(self):
        pass
        #if self.GetFrame() is None:
         #   return
        #self.GetFrame().SetFocus()
        
    def DoFind(self):
        pass

class DocTabbedChildFrame(ttk.Frame):
    """
    The wxDocMDIChildFrame class provides a default frame for displaying
    documents on separate windows. This class can only be used for MDI child
    frames.

    The class is part of the document/view framework supported by wxWindows,
    and cooperates with the wxView, wxDocument, wxDocManager and wxDocTemplate
    classes.
    """

    def __init__(self, doc, view, frame, id, title):
        """
        Constructor.  Note that the event table must be rebuilt for the
        frame since the EvtHandler is not virtual.
        """
        ttk.Frame.__init__(self, frame.GetNotebook())
        self._childDocument = doc
        self._childView = view
        frame.AddNotebookPage(self, doc.GetPrintableName(),doc.GetFilename())
        if view:
            view.SetFrame(self)

    def GetIcon(self):
        """
        Dummy method since the icon of tabbed frames are managed by the notebook.
        """
        return None


    def SetIcon(self, icon):
        """
        Dummy method since the icon of tabbed frames are managed by the notebook.
        """
        pass

    def Destroy(self):
        """
        Removes the current notebook page.
        """
        GetApp().GetTopWindow().RemoveNotebookPage(self)

    def SetFocus(self):
        """
        Activates the current notebook page.
        """
        GetApp().GetTopWindow().ActivateNotebookPage(self)

    def Activate(self):  # Need this in case there are embedded sash windows and such, OnActivate is not getting called
        """
        Activates the current view.
        """
        # Called by Project Editor
        if self._childView:
            self._childView.Activate(True)

    def GetTitle(self):
        """
        Returns the frame's title.
        """
        return GetApp().GetTopWindow().GetNotebookPageTitle(self)

    def SetTitle(self, title):
        """
        Sets the frame's title.
        """
        GetApp().GetTopWindow().SetNotebookPageTitle(self, title)

    def OnTitleIsModified(self):
        """
        Add/remove to the frame's title an indication that the document is dirty.
        If the document is dirty, an '*' is appended to the title
        """
        title = self.GetTitle()
        if title:
            if self.GetDocument().IsModified():
                if not title.endswith("*"):
                    title = title + "*"
                    self.SetTitle(title)
            else:
                if title.endswith("*"):
                    title = title[:-1]
                    self.SetTitle(title)

    def GetDocument(self):
        """
        Returns the document associated with this frame.
        """
        return self._childDocument

    def SetDocument(self, document):
        """
        Sets the document for this frame.
        """
        self._childDocument = document

    def GetView(self):
        """
        Returns the view associated with this frame.
        """
        return self._childView


    def SetView(self, view):
        """
        Sets the view for this frame.
        """
        self._childView = view
        

class DocFrameFileDropTarget(newTkDnD.FileDropTarget):
    """
    Class used to handle drops into the document frame.
    """

    def __init__(self, docManager, docFrame):
        """
        Initializes the FileDropTarget class with the active docManager and the docFrame.
        """
        newTkDnD.FileDropTarget.__init__(self)
        self._docManager = docManager
        self._docFrame = docFrame


    def OnDropFiles(self, x, y, filenames):
        """
        Called when files are dropped in the drop target and tells the docManager to open
        the files.
        """
        try:
            for filename in filenames:
                self._docManager.CreateDocument(filename, DOC_SILENT)
        except Exception as e:
            msgTitle = GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            messagebox.showerror(msgTitle,_("Could not open '%s':  %s") % (fileutils.get_filename_from_path(filename), e))
            

class DataObject(object):
    
    def __init__(self,data_type="str"): 
        self._data_type = data_type
        self._data = ''

    def SetData(self,data):
        self._data = data

    def GetData(self):
        return self._data
        
    def GetDataSize(self):
        return len(self._data)
        
    @property
    def RawData(self):
        return self._data
        
    @RawData.setter
    def RawData(self,data):
        self._data = data

class JsonDataobject(DataObject):
    
    def __init__(self): 
        DataObject.__init__(self,data_type="json")

    def SetData(self,data):
        DataObject.SetData(self,json.dumps(data))

    def GetData(self):
        data = DataObject.GetData(self)
        d = json.loads(data)
        return json.loads(data)
            
class Clipboard(object):
    def __init__(self):
        self._is_opened = False
        
    def Open(self):
        if self._is_opened:
            return True
        self.buf = StringIO.StringIO()
        self._is_opened = True
        return self._is_opened

    def Close(self):
        self.buf.close()
        self._is_opened = False

    def IsOpened(self):
        return self._is_opened

    def AddData(self,data_ojbect):
        self.buf.write(data_ojbect.RawData)

    def SetData(self,data_ojbect):
        self.Clear()
        self.AddData(data_ojbect)

    def GetData(self,data_ojbect):
        if not self.buf.getvalue():
            return False
        data_ojbect.RawData = self.buf.getvalue()
        return True

    def Clear(self):
        self.buf.truncate(0)
        self.buf.seek(0)

    def Flush(self):
        self.buf.flush()

    def Get(*args, **kwargs):
        """
        Get() -> Clipboard

        Returns global instance (wxTheClipboard) of the object.
        """
        return _misc_.Clipboard_Get(*args, **kwargs)