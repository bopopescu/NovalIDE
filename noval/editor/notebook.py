# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        notebook.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-21
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
import tkinter as tk
from noval import GetApp,_,constants,NewId
import noval.ui_base as ui_base
import noval.util.utils as utils
import noval.misc as misc
import noval.menu as tkmenu
import noval.consts as consts
import noval.imageutils as imageutils
import noval.syntax.lang as lang
import noval.core as core
import noval.syntax.syntax as syntax
import noval.util.fileutils as fileutils
from tkinter import messagebox,filedialog
import os
import noval.util.strutils as strutils
try:
    import tkSimpleDialog
except ImportError:
    import tkinter.simpledialog as tkSimpleDialog
import noval.find.find as findtext
import noval.find.findindir as findindir 
from noval.editor import text as texteditor
import noval.docposition as docposition
import noval.formatter as formatter
import datetime
import getpass

class EditorNotebook(ui_base.ClosableNotebook):
    """
    Manages opened files / modules
    """

    def __init__(self, master,**kw):
        ui_base.ClosableNotebook.__init__(self,master, padding=0,**kw)
        self._popup_index = -1
        self._current_document = None
        self._tabs_menu = None
        self.update_appearance()
        # should be in the end, so that it can be detected when
        # constructor hasn't completed yet
        self.preferred_size_in_pw = None
        #标签页右键单击事件
        self.bind("<ButtonPress-3>", self._right_btn_press, True)
        #单击鼠标中间滚轮,关闭文档标签
        self.bind("<ButtonRelease-2>", self.MouseMiddleClick, True)
        self.bind("<<NotebookTabChanged>>", self.OnTabChange, True)
        #双击标签页最大化和恢复文本编辑窗口
        self.bind("<Double-Button-1>", self.ToogleMaximizeView, True)
            
        GetApp().bind("InitTkDnd",self.SetDropTarget,True)
        self.images = []
        
    def SetDropTarget(self,event):
        
        #设置允许拖拽打开文件
        if GetApp().dnd is not None and utils.profile_get_int('ALLOW_DROP_OPENFILE',True):
            GetApp().dnd.bindtarget(self, core.DocFrameFileDropTarget(GetApp().GetDocumentManager(),self.master), 'text/uri-list')
        
    def OnTabChange(self,event):
        if self.get_current_editor() is None:
            #如果文档全部关闭了重置状态栏
            GetApp().MainFrame.GetStatusBar().Reset()
            return None
        current_view = self.get_current_editor().GetView()
        #切换标签时设置当前视图为活跃视图
        GetApp().GetDocumentManager().ActivateView(current_view)
        #设置当前视图焦点
        current_view.SetFocus()
        #设置当前行列号
        current_view.set_line_and_column()
        document = current_view.GetDocument()
        #文本视图在状态栏显示文件编码
        if isinstance(document,texteditor.TextDocument):
            GetApp().MainFrame.GetStatusBar().SetDocumentEncoding(document.file_encoding)
        GetApp().MainFrame.UpdateToolbar()

    def load_startup_files(self):
        """If no filename was sent from command line
        then load previous files (if setting allows)"""

        cmd_line_filenames = [os.path.abspath(name) for name in sys.argv[1:] if os.path.exists(name)]

        if len(cmd_line_filenames) > 0:
            filenames = cmd_line_filenames
        elif get_workbench().get_option("file.reopen_all_files"):
            filenames = get_workbench().get_option("file.open_files")
        elif get_workbench().get_option("file.current_file"):
            filenames = [get_workbench().get_option("file.current_file")]
        else:
            filenames = []

        if len(filenames) > 0:
            for filename in filenames:
                if os.path.exists(filename):
                    self.show_file(filename)

            cur_file = get_workbench().get_option("file.current_file")
            # choose correct active file
            if len(cmd_line_filenames) > 0:
                self.show_file(cmd_line_filenames[0])
            elif cur_file and os.path.exists(cur_file):
                self.show_file(cur_file)
            else:
                self._cmd_new_file()
        else:
            self._cmd_new_file()

    #重写关闭文档标签页事件,如果是文档类型的标签页除了关闭窗口之外,还要关闭打开的文档
    def close_tab(self, index):
        editor = self.get_child_by_index(index)
        if editor:
            #关闭文档同时关闭文档窗口
            editor.GetView().GetDocument().DeleteAllViews()

    def close_editor(self, editor):
        self.forget(editor)
        editor.destroy()
        
    def SaveAllFilesEnabled(self):
        if self.get_current_editor() is None:
            return False
        for editor in self.get_all_editors():
            if editor.GetView().GetDocument().IsModified():
                return True
        return False

    def _cmd_rename_file(self):
        editor = self.get_current_editor()
        old_filename = editor.get_filename()
        assert old_filename is not None

        self._cmd_save_file_as()

        if editor.get_filename() != old_filename:
            os.remove(old_filename)

    def _cmd_rename_file_enabled(self):
        return (
            self.get_current_editor()
            and self.get_current_editor().get_filename() is not None
        )

    def close_single_untitled_unmodified_editor(self):
        editors = self.winfo_children()
        if (
            len(editors) == 1
            and not editors[0].is_modified()
            and not editors[0].get_filename()
        ):
            self._cmd_close_file()

    def get_current_editor(self):
        return self.get_current_child()

    def get_all_editors(self):
        # When workspace is closing, self.winfo_children()
        # may return an unexplainable tkinter.Frame
        return [child for child in self.winfo_children() if isinstance(child, core.DocTabbedChildFrame)]

    def select_next_prev_editor(self, direction):
        cur_index = self.index(self.select())
        next_index = (cur_index + direction) % len(self.tabs())
        self.select(self.get_child_by_index(next_index))

    def update_appearance(self):
        for editor in self.winfo_children():
            editor.update_appearance()

    def update_editor_title(self, editor, title=None):
        if title is None:
            title = editor.get_title()
        self.tab(editor, text=title)

    def get_editor(self, filename, open_when_necessary=False):
        for child in self.winfo_children():
            child_filename = child.get_filename(False)
            if child_filename and is_same_path(child.get_filename(), filename):
                return child

        if open_when_necessary:
            return self._open_file(filename)
        else:
            return None

    def _right_btn_press(self, event):
        try:
            index = self.index("@%d,%d" % (event.x, event.y))
            self._popup_index = index
            self.create_tab_menu()
        except Exception:
            utils.get_logger().exception("Opening tab menu")
            
    def create_tab_menu(self):
        """
        Handles right clicks for the notebook, enabling users to either close
        a tab or select from the available documents if the user clicks on the
        notebook's white space.
        """
        if self._tabs_menu is not None:
            self._tabs_menu.destroy()
        menu = tkmenu.PopupMenu(self.winfo_toplevel(),**misc.get_style_configuration("Menu"))
        menu["postcommand"] = lambda: menu._update_menu()
        self._tabs_menu = menu
        tabsMenu = None
        if self._popup_index > -1:
            self._current_document = self.GetDocumentFromPageIndex(self._popup_index)
            view = self._current_document.GetFirstView()
            if isinstance(view,texteditor.TextView):
                menu_item = tkmenu.MenuItem(constants.ID_NEW_MODULE,_("New Module"), None,imageutils.load_image("","new.png"),None)
                menu.AppendMenuItem(menu_item,self.NewModule)
                
                menu_item = GetApp().Menubar.GetFileMenu().FindMenuItem(constants.ID_SAVE)
                assert(menu_item != None)
                menu.AppendMenuItem(menu_item,self.SaveFileDocument)
                
                menu_item = GetApp().Menubar.GetFileMenu().FindMenuItem(constants.ID_SAVEAS)
                assert(menu_item != None)
                menu.AppendMenuItem(menu_item,self.SaveAsFileDocument)
            
            menu_item = GetApp().Menubar.GetFileMenu().FindMenuItem(constants.ID_CLOSE)
            assert(menu_item != None)
            menu.AppendMenuItem(menu_item,self.CloseDoc)
            
            menu_item = GetApp().Menubar.GetFileMenu().FindMenuItem(constants.ID_CLOSE_ALL)
            assert(menu_item != None)
            menu.AppendMenuItem(menu_item,self.CloseAllDocs)

            if len(self.tabs()) > 1:
                item_name = _("Close All but \"%s\"") % self._current_document.GetPrintableName()
                menu_item = tkmenu.MenuItem(constants.ID_CLOSE_ALL_WITHOUT,item_name,None,None,None)
                menu.AppendMenuItem(menu_item,self.CloseAllWithoutDoc)
                tabsMenu = tkmenu.PopupMenu(menu)
                #menu.add_cascade(label=_("Select Tab"), menu=tabsMenu)
                menu.AppendMenu(NewId(),text=_("Select Tab"), menu=tabsMenu)
            if os.path.isabs(self._current_document.GetFilename()):
                menu_item = tkmenu.MenuItem(constants.ID_OPEN_DOCUMENT_DIRECTORY,_("Open Path in Explorer"),None,None,None)
                menu.AppendMenuItem(menu_item,self.OpenPathInExplorer)
                menu_item = tkmenu.MenuItem(constants.ID_OPEN_TERMINAL_DIRECTORY,_("Open Path in Terminator"),None,None,None)
                menu.AppendMenuItem(menu_item,self.OpenPathInTerminator)
            menu_item = tkmenu.MenuItem(constants.ID_COPY_DOCUMENT_PATH,_("Copy Path"),None,None,None)
            menu.AppendMenuItem(menu_item,self.CopyFilePath)
            menu_item = tkmenu.MenuItem(constants.ID_COPY_DOCUMENT_NAME,_("Copy Name"),None,None,None)
            menu.AppendMenuItem(menu_item,self.CopyFileName)
            if isinstance(view,texteditor.TextView) and view.GetLangId() == GetApp().GetDefaultLangId():
                menu_item = tkmenu.MenuItem(constants.ID_COPY_MODULE_NAME,_("Copy Module Name"),None,None,None)
                menu.AppendMenuItem(menu_item,self.CopyModuleName)

        if len(self.tabs()) > 1:
            for i in range(0, len(self.tabs())):
                tab_view_frame = self.get_child_by_index(i)
                tab_index = self.index(tab_view_frame)
                def open_index_tab(index=tab_index):
                    editor = self.get_child_by_index(index)
                    self.select(editor)
                    
                filename = self.tab(tab_view_frame)['text']
                template = tab_view_frame.GetView().GetDocument().GetDocumentTemplate()
                item = tkmenu.MenuItem(id,filename,None,template.GetIcon(),None)
                tabsMenu.AppendMenuItem(item,handler=open_index_tab)
                
        if not GetApp().IsFullScreen:
            menu.add_separator()
            menu_item = tkmenu.MenuItem(constants.ID_MAXIMIZE_EDITOR_WINDOW,_("Maximize Editor Window"),None,GetApp().GetImage("maximize_editor.png"),None)
            menu.AppendMenuItem(menu_item,GetApp().MainFrame.MaximizeEditor)
            menu_item = tkmenu.MenuItem(constants.ID_RESTORE_EDITOR_WINDOW,_("Restore Editor Window"),None,GetApp().GetImage("restore_editor.png"),None)
            menu.AppendMenuItem(menu_item,GetApp().MainFrame.RestoreEditor)

        menu.tk_popup(*self.winfo_toplevel().winfo_pointerxy())
        
    @misc.update_toolbar
    def CloseDoc(self):
        self._current_document.DeleteAllViews()
        
    @misc.update_toolbar
    def CloseAllDocs(self):
        self.CloseAllWithoutDoc(closeall=True)
        
    def OpenPathInExplorer(self):
        suc,msg = fileutils.open_file_directory(self._current_document.GetFilename())
        if not suc:
            messagebox.showerror(_("Error"),msg.decode(utils.get_default_encoding()))
            
    def OpenPathInTerminator(self):
        GetApp().OpenTerminator(self._current_document.GetFilename())
            
    def CopyFilePath(self):
        utils.CopyToClipboard(self._current_document.GetFilename())
        
    def CopyFileName(self):
        utils.CopyToClipboard(os.path.basename(self._current_document.GetFilename()))
        
    @misc.update_toolbar
    def NewModule(self):
        flags = core.DOC_NEW
        lexer = syntax.SyntaxThemeManager().GetLexer(lang.ID_LANG_PYTHON)
        temp = GetApp().GetDocumentManager().FindTemplateForPath("test.%s" % lexer.GetDefaultExt())
        newDoc = temp.CreateDocument("", flags)
        if newDoc:
            newDoc.SetDocumentName(temp.GetDocumentName())
            newDoc.SetDocumentTemplate(temp)
            newDoc.OnNewDocument()
            
    def SaveFileDocument(self):
        self._current_document.Save()
        
    def SaveAsFileDocument(self):
        GetApp().SaveAsDocument(self._current_document)
        
    def CopyModuleName(self):
        utils.CopyToClipboard(strutils.get_filename_without_ext(self._current_document.GetFilename()))
        
    @misc.update_toolbar
    def CloseAllWithoutDoc(self):
        self.CloseAllWithoutDoc(False)
        
    def CloseAllWithoutDoc(self,closeall=False):
        #倒序关闭所有文档,防止数组越界
        for i in range(len(self.tabs())-1, -1, -1): # Go from len-1 to 0
            doc = self.GetDocumentFromPageIndex(i)
            if doc != self._current_document or closeall:
                if not GetApp().GetDocumentManager().CloseDocument(doc, False):
                    break
                        
    def MouseMiddleClick(self,event):
        index = self.index("@%d,%d" % (event.x, event.y))
        self._current_document = self.GetDocumentFromPageIndex(index)
        self.CloseDoc()
            
    def GetDocumentFromPageIndex(self,index):
        if index > -1:
            view_frame = self.get_child_by_index(index)
            view = view_frame.GetView()
            return view.GetDocument()
        return None
        
    def GotoLine(self,event=None):
        if self.get_current_editor() is None:
            return
        text_view = self.get_current_editor().GetView()
        lineno = tkSimpleDialog.askinteger(_("Go to Line"),
                _("Enter line number to go to:(1-%d)") % text_view.GetCtrl().GetLineCount(),parent=self.get_current_editor())
        if lineno is None:
            return "break"
        if lineno <= 0:
            text_view.GetCtrl().bell()
            return "break"
        text_view.GotoLine(lineno)

    def _InitCommands(self):
        GetApp().AddCommand(constants.ID_FIND,_("&Edit"),_("&Find..."),handler=lambda:self.DoFind(),image="toolbar/find.png",default_tester=True,default_command=True,include_in_toolbar=True,extra_sequences=["<<CtrlFInText>>"])
        #解除默认绑定事件,从新绑定快捷键ctrl+h的事件
        GetApp().AddCommand(constants.ID_REPLACE,_("&Edit"),_("R&eplace..."),lambda:self.DoFind(True),default_tester=True,default_command=True,extra_sequences=["<<CtrlHInText>>"])
        GetApp().AddCommand(constants.ID_GOTO_LINE,_("&Edit"),_("&Go to Line..."),self.GotoLine,image="gotoline.png",default_tester=True,default_command=True)
        GetApp().AddCommand(constants.ID_FINDFILE,_("&Edit"),_("Find in File..."),self.FindInfile,default_tester=True,default_command=True)
        GetApp().AddCommand(constants.ID_FINDALL,_("&Edit"),_("Find in Project..."),self.FindInproject,tester=lambda:GetApp().MainFrame.GetProjectView().GetCurrentProject() is not None)
        GetApp().AddCommand(constants.ID_FINDDIR,_("&Edit"),_("Find in Directory..."),self.FindIndir,add_separator=True)
        
        edit_menu = GetApp().Menubar.GetMenu(_("&Edit"))
        insert_menu = tkmenu.PopupMenu()
        edit_menu.AppendMenu(constants.ID_INSERT,_("Insert"),insert_menu)
        GetApp().AddMenuCommand(constants.ID_INSERT_DATETIME,insert_menu,_("Insert Datetime"),self.InsertDatatime,default_tester=True,default_command=True)
        GetApp().AddMenuCommand(constants.ID_INSERT_COMMENT_TEMPLATE,insert_menu,_("Insert Comment Template"),self.InsertCommentTemplate,default_tester=True,default_command=True)
        GetApp().AddMenuCommand(constants.ID_INSERT_FILE_CONTENT,insert_menu,_("Insert File Content"),self.InsertFileContent,default_tester=True,default_command=True)
        
        #解除默认绑定事件,从新绑定快捷键ctrl+k的事件
        GetApp().AddCommand(constants.ID_COMMENT_LINES,_("&Format"),_("Comment &Lines"),lambda:formatter.formatter.CommentRegion(self.get_current_editor()),image=GetApp().GetImage("comment.png"),\
                                            default_tester=True,default_command=True,extra_sequences=["<<CtrlKInText>>"])
        GetApp().AddCommand(constants.ID_UNCOMMENT_LINES,_("&Format"),_("&Uncomment Lines"),lambda:formatter.formatter.UncommentRegion(self.get_current_editor()),image=GetApp().GetImage("uncomment.png"),\
                                            default_tester=True,default_command=True)
           
        GetApp().AddCommand(constants.ID_INDENT_LINES,_("&Format"),_("&Indent Lines"),lambda:formatter.formatter.CommentRegion(self.get_current_editor()),image=GetApp().GetImage("indent.png"),\
                                            default_tester=True,default_command=True)
        GetApp().AddCommand(constants.ID_DEDENT_LINES,_("&Format"),_("&Dedent Lines"),lambda:formatter.formatter.UncommentRegion(self.get_current_editor()),image=GetApp().GetImage("dedent.png"),\
                                            default_tester=True,default_command=True)
                
     
        view_menu = GetApp().Menubar.GetMenu(_("&View"))
        zoom_menu = tkmenu.PopupMenu()
        view_menu.AppendMenu(constants.ID_ZOOM,_("&Zoom"),zoom_menu)
        GetApp().AddMenuCommand(constants.ID_ZOOM_IN,zoom_menu,_("Zoom In"),lambda:self.ZoomView(1),image=GetApp().GetImage("toolbar/zoom_in.png"),tester=lambda: self.get_current_editor() is not None,include_in_toolbar=True)
        GetApp().AddMenuCommand(constants.ID_ZOOM_OUT,zoom_menu,_("Zoom Out"),lambda:self.ZoomView(-1),image=GetApp().GetImage("toolbar/zoom_out.png"),tester=lambda: self.get_current_editor() is not None,include_in_toolbar=True)
               
        outline_menu = tkmenu.PopupMenu()
        self.outline_sort_var = tk.IntVar(value=utils.profile_get_int("OutlineSort", ui_base.OutlineView.SORT_BY_NONE))
        view_menu.AppendMenu(constants.ID_OUTLINE_SORT,_("Outline Sort"),outline_menu)
        
        GetApp().AddMenuCommand(constants.ID_SORT_BY_NONE,outline_menu,_("Unsorted"),lambda:self.OutlineSort(constants.ID_SORT_BY_NONE),\
                                tester=lambda: self.get_current_editor() is not None,kind=consts.RADIO_MENU_ITEM_KIND,variable=self.outline_sort_var,value=ui_base.OutlineView.SORT_BY_NONE)
        GetApp().AddMenuCommand(constants.ID_SORT_BY_LINE,outline_menu,_("Sort By Line"),lambda:self.OutlineSort(constants.ID_SORT_BY_LINE),\
                                tester=lambda: self.get_current_editor() is not None,kind=consts.RADIO_MENU_ITEM_KIND,variable=self.outline_sort_var,value=ui_base.OutlineView.SORT_BY_LINE)
        GetApp().AddMenuCommand(constants.ID_SORT_BY_TYPE,outline_menu,_("Sort By Type"),lambda:self.OutlineSort(constants.ID_SORT_BY_TYPE),\
                                tester=lambda: self.get_current_editor() is not None,kind=consts.RADIO_MENU_ITEM_KIND,variable=self.outline_sort_var,value=ui_base.OutlineView.SORT_BY_TYPE)
        GetApp().AddMenuCommand(constants.ID_SORT_BY_NAME,outline_menu,_("Sort By Name(A-Z)"),lambda:self.OutlineSort(constants.ID_SORT_BY_NAME),\
                                tester=lambda: self.get_current_editor() is not None,kind=consts.RADIO_MENU_ITEM_KIND,variable=self.outline_sort_var,value=ui_base.OutlineView.SORT_BY_NAME)
        
        
        GetApp().AddCommand(constants.ID_PRE_POS,_("&View"),_("Previous Position"),self.GotoPrePos,image=GetApp().GetImage("toolbar/go_prev.png"),\
                            tester=lambda:docposition.DocMgr.CanNavigatePrev(),include_in_toolbar=True)
        GetApp().AddCommand(constants.ID_NEXT_POS,_("&View"),_("Next Position"),self.GotoNextPos,image=GetApp().GetImage("toolbar/go_next.png"),\
                            tester=lambda:docposition.DocMgr.CanNavigateNext(),include_in_toolbar=True)
                            

    @misc.update_toolbar
    def GotoNextPos(self):
        fname, line,col = (None, None,None)
        cname, cline,ccol = (None, None,None)
        editor  = self.get_current_editor()
        if editor is not None:
            text_view = editor.GetView()
            cname = text_view.GetDocument().GetFilename()
            cline = text_view.GetCtrl().GetCurrentLine()
            ccol = text_view.GetCtrl().GetCurrentColumn()
        if docposition.DocMgr.CanNavigateNext():
            fname, line,col = docposition.DocMgr.GetNextNaviPos()
            if (fname, line,col) == (cname, cline,ccol):
                fname, line,col = (None, None,None)
                tmp = docposition.DocMgr.GetNextNaviPos()
                if tmp is not None:
                    fname, line,col = tmp
                    
        if fname is not None:
            #跳转到位置时不需追踪位置了
            GetApp().GotoView(fname,line,colno=col,trace_track=False)
        
    @misc.update_toolbar
    def GotoPrePos(self):
        fname, line,col = (None, None,None)
        cname, cline,ccol = (None, None,None)
        editor  = self.get_current_editor()
        if editor is not None:
            text_view = editor.GetView()
            cname = text_view.GetDocument().GetFilename()
            cline = text_view.GetCtrl().GetCurrentLine()
            ccol = text_view.GetCtrl().GetCurrentColumn()

        if docposition.DocMgr.CanNavigatePrev():
            fname, line,col = docposition.DocMgr.GetPreviousNaviPos()
            if (fname, line,col) == (cname, cline,ccol):
                fname, line,col = (None, None,None)
                tmp = docposition.DocMgr.GetPreviousNaviPos()
                if tmp is not None:
                    fname, line,col = tmp
                    
        if fname is not None:
            #跳转到位置时不需追踪位置了
            GetApp().GotoView(fname,line,colno=col,trace_track=False)
        
    def ZoomView(self,delta=0):
        self.get_current_editor().GetView().UpdateFontSize(delta)
        
    def DoFind(self,replace=False):
        findtext.ShowFindReplaceDialog(GetApp(),replace=replace)
        
    def FindIndir(self):
        findindir.ShowFindIndirDialog(GetApp(),self.get_current_editor())
        
    def FindInfile(self):
        findindir.ShowFindInfileDialog(self.get_current_editor())
        
    def FindInproject(self):
        findindir.ShowFindInprojectDialog(GetApp(),self.get_current_editor())
        
    def OutlineSort(self,outline_sort_id):
        sort_order = ui_base.OutlineView.SORT_BY_NONE
        if outline_sort_id == constants.ID_SORT_BY_LINE:
            sort_order = ui_base.OutlineView.SORT_BY_LINE
        elif outline_sort_id == constants.ID_SORT_BY_TYPE:
            sort_order = ui_base.OutlineView.SORT_BY_TYPE
        elif outline_sort_id == constants.ID_SORT_BY_NAME:
            sort_order = ui_base.OutlineView.SORT_BY_NAME
        GetApp().MainFrame.GetOutlineView().Sort(sort_order)
        
    def InsertDatatime(self):
        self.get_current_editor().GetView().AddText(str(datetime.datetime.now().date()))
        
    def InsertCommentTemplate(self):
        text_view = self.get_current_editor().GetView()
        file_name = os.path.basename(text_view.GetDocument().GetFilename())
        now_time = datetime.datetime.now()
        langid = text_view.GetLangId()
        lexer = syntax.SyntaxThemeManager().GetLexer(langid)
        comment_template = lexer.GetCommentTemplate()
        if comment_template is not None:
            comment_template_content = comment_template.format(File=file_name,Author=getpass.getuser(),Date=now_time.date(),Year=now_time.date().year)
            text_view.GetCtrl().GotoPos(0,0)
            text_view.AddText(comment_template_content)
            
    def InsertFileContent(self):
        path = filedialog.askopenfilename(
            master=self,
            filetypes=[(_("All Files"),".*"),],
            initialdir=os.getcwd()
            )
        if not path:
            return
        with open(path) as f:
            self.get_current_editor().GetView().AddText(f.read())
            
    def ToogleMaximizeView(self,event):
        GetApp().MainFrame.ToogleMaximizeView()
        
        