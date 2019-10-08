# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        text.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-11
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
import tkinter as tk
from tkinter import messagebox,filedialog
from noval import GetApp,_
import noval.core as core
import noval.filewatcher as filewatcher
import codecs
import noval.python.parser.utils as parserutils
import noval.consts as consts
import os
import noval.util.fileutils as fileutils
import sys
import noval.util.utils as utils
import noval.ui_base as ui_base
from tkinter import ttk
import time
import noval.menu as tkmenu
import noval.syntax.lang as lang
import noval.util.strutils as strutils
import shutil
from noval.filewatcher import FileEventHandler
import noval.ui_common as ui_common
import noval.misc as misc
import tkinter.font as tkfont
import noval.docposition as docposition
import noval.constants as constants
import noval.python.pyutils as pyutils
import noval.ui_utils as ui_utils
import noval.syntax.syntax as syntax
import noval.find.findtext as findtext
import noval.editor.format as textformat

def classifyws(s, tabwidth):
    raw = effective = 0
    for ch in s:
        if ch == " ":
            raw = raw + 1
            effective = effective + 1
        elif ch == "\t":
            raw = raw + 1
            effective = (effective // tabwidth + 1) * tabwidth
        else:
            break
    return raw, effective
    
def index2line(index):
    return int(float(index))


def line2index(line):
    return str(float(line))

class TextDocument(core.Document):
    
    ASC_FILE_ENCODING = "ascii"
    UTF_8_FILE_ENCODING = "utf-8"
    ANSI_FILE_ENCODING = "cp936"
    
    DEFAULT_FILE_ENCODING = ASC_FILE_ENCODING
    
    def __init__(self):
        core.Document .__init__(self)
        self._inModify = False
        self.file_watcher = filewatcher.FileAlarmWatcher()
        self._is_watched = False
        self.file_encoding = GetApp().GetConfig().Read(consts.DEFAULT_FILE_ENCODING_KEY,TextDocument.DEFAULT_FILE_ENCODING)
        if self.file_encoding == "":
            self.file_encoding = TextDocument.DEFAULT_FILE_ENCODING
        self._is_new_doc = True
        self._is_loading_doc = False

    def GetSaveObject(self,filename):
        return codecs.open(filename, 'w',self.file_encoding)

    def DoSave(self):
        if self._is_watched:
            self.file_watcher.StopWatchFile(self)
        #should check document data encoding first before save document
        self.file_encoding = self.DetectDocumentEncoding()

    def GetOpenDocument(self,filepath,exclude_self=True):
        '''
            通过文件名查找打开文件
            exclude_self:是否排查自身
            
        '''
        if exclude_self and parserutils.ComparePath(self.GetFilename(),filepath):
            return None
        doc = GetApp().GetDocumentManager().GetDocument(filepath)
        return doc
        
    def SaveAs(self):
        """
        Prompts the user for a file to save to, and then calls OnSaveDocument.
        """
        docTemplate = self.GetDocumentTemplate()
        if not docTemplate:
            return False

        if docTemplate.GetDocumentType() == TextDocument and docTemplate.GetFileFilter() != "*.*":
            default_ext = ""
        else:
            default_ext = docTemplate.GetDefaultExtension()
            
        descrs = strutils.gen_file_filters()
        filename = filedialog.asksaveasfilename(
            master = GetApp(),
            filetypes=descrs,
            defaultextension=default_ext,
            initialdir=os.getcwd(),
            initialfile=os.path.basename(self.GetFilename())
        )
        if filename == "":
            return False
            
        #将路径转换成系统标志路径格式
        filename = fileutils.opj(filename)
        #检查文件名是否已经被打开的文件占用,如果占用了则不能保存文件
        if self.GetOpenDocument(filename):
            messagebox.showwarning(GetApp().GetAppName(),_("File has already been opened,could not overwrite it."))
            return False
            
        if not self.OnSaveDocument(filename):
            return False

        self.SetFilename(filename)
        self.SetTitle(fileutils.get_filename_from_path(filename))

        for view in self._documentViews:
            view.OnChangeFilename()

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

        msgTitle =  GetApp().GetAppName()
        if not msgTitle:
            msgTitle = _("File Error")

        self._is_loading_doc = False
        backupFilename = None
        fileObject = None
        copied = False
        try:
            self.DoSave()
            # if current file exists, move it to a safe place temporarily
            if os.path.exists(filename):

                # Check if read-only.
                if not os.access(filename, os.W_OK):
                    messagebox.showerror(msgTitle,"Could not save '%s'.  No write permission to overwrite existing file." % \
                                         fileutils.get_filename_from_path(filename))
                    return False

                backupFilename = "%s.bk%s" % (filename, 1)
                shutil.copy(filename, backupFilename)
                copied = True
            fileObject = self.GetSaveObject(filename)
            self.SaveObject(fileObject)
            fileObject.close()
            fileObject = None
            
            if backupFilename:
                os.remove(backupFilename)
        except Exception as e:
            utils.get_logger().exception("")
            if fileObject:
                fileObject.close()  # file is still open, close it, need to do this before removal 

            # save failed, remove copied file
            if backupFilename and copied:
                shutil.copy(backupFilename,filename)
                os.remove(backupFilename)

            messagebox.showerror(msgTitle,_("Could not save '%s':  %s") % (fileutils.get_filename_from_path(filename), e))
                          
            if not self._is_new_doc:
                self.SetDocumentModificationDate()
            return False

        self.SetFilename(filename, True)
        self.Modify(False)
        self.SetDocumentSaved(True)
        self._is_watched = True
        self._is_new_doc = False
        self.file_watcher.StartWatchFile(self)
        self.SetDocumentModificationDate()
        return True

    def DetectFileEncoding(self,filepath):

        file_encoding = TextDocument.DEFAULT_FILE_ENCODING
        try:
            with open(filepath,"rb") as f:
                data = f.read()
                result = fileutils.detect(data)
                file_encoding = result['encoding']
        except:
            utils.get_logger().exception("")
        #if detect file encoding is None,we should assume the file encoding is ansi,which cp936 encoding is instead
        if None == file_encoding or file_encoding.lower().find('iso') != -1:
            file_encoding = TextDocument.ANSI_FILE_ENCODING
        return file_encoding
        
    def DetectDocumentEncoding(self):
        view = self.GetFirstView()
        file_encoding = self.file_encoding
        #when the file encoding is accii or new document,we should check the document data contain chinese character,
        #the we should change the document encoding to utf-8 to save chinese character
        if file_encoding == self.ASC_FILE_ENCODING or self.IsNewDocument:
            guess_encoding = file_encoding.lower()
            if guess_encoding == self.ASC_FILE_ENCODING:
                guess_encoding = self.UTF_8_FILE_ENCODING
            result = fileutils.detect(view.GetValue().encode(guess_encoding))
            file_encoding = result['encoding']
            if None == file_encoding:
                file_encoding = TextDocument.ASC_FILE_ENCODING
        return file_encoding

    def OnOpenDocument(self, filename):
        """
        Constructs an input file for the given filename (which must not
        be empty), and calls LoadObject. If LoadObject returns true, the
        document is set to unmodified; otherwise, an error message box is
        displayed. The document's views are notified that the filename has
        changed, to give windows an opportunity to update their titles. All of
        the document's views are then updated.
        """
        #文件在外部改变重新打开时检查界面文本是否更改需要保存
        if not self.OnSaveModified():
            return False
        self._is_loading_doc = True
        msgTitle = GetApp().GetAppName()
        if not msgTitle:
            msgTitle = _("File Error")
        self.file_encoding = self.DetectFileEncoding(filename)
        fileObject = None
        try:
            if self.file_encoding == 'binary':
                fileObject = open(filename, 'rb')
                is_bytes = True
            else:
                fileObject = codecs.open(filename, 'r',self.file_encoding)
                is_bytes = False
            self.LoadObject(fileObject,is_bytes)
            fileObject.close()
            fileObject = None
        except Exception as e:
            utils.get_logger().exception("")
            if fileObject:
                fileObject.close()  # file is still open, close it 

            messagebox.showerror(msgTitle,_("Could not open '%s':  %s") % (fileutils.get_filename_from_path(filename), e))
            self._is_loading_doc = False
            return False

        self.SetDocumentModificationDate()
        self.SetFilename(filename, True)
        self.Modify(False)
        self.SetDocumentSaved(True)
        self.UpdateAllViews()
        self.file_watcher.AddFileDoc(self)
        self._is_watched = True
        self._is_new_doc = False
        rember_file_pos = GetApp().GetConfig().ReadInt(consts.REMBER_FILE_KEY, True)
        if rember_file_pos:
            pos = docposition.DocMgr.GetPos(filename)
            if pos[0] != None:
                self.GetFirstView().GetCtrl().GotoPos(*pos)
        self._is_loading_doc = False
        return True

    @property
    def IsWatched(self):
        return self._is_watched

    @property
    def FileWatcher(self):
        return self.file_watcher

    def SaveObject(self, fileObject):
        view = self.GetFirstView()
        fileObject.write(view.GetValue())
        view.SetModifyFalse()
        return True
        
    def LoadObject(self, fileObject,is_bytes=False):
        view = self.GetFirstView()
        data = fileObject.read()
        if is_bytes:
            view.SetBinaryValue(data)
        else:
            view.SetValue(data)
        view.SetModifyFalse()
        return True

    def IsModified(self):
        filename = self.GetFilename()
        if filename and not os.path.exists(filename) and not self._is_new_doc:
            return True
        view = self.GetFirstView()
        if view:
            return view.IsModified()
        return False
    
    @property
    def IsNewDocument(self):
        return self._is_new_doc

    def Modify(self, modify):
        if self._inModify:
            return
        self._inModify = True
        view = self.GetFirstView()
        if not modify and view:
            #设置编辑器状态为未修改
            view.SetModifyFalse()
        core.Document.Modify(self, modify) 
        self._inModify = False

class TextView(misc.AlarmEventView):
    def __init__(self):
        misc.AlarmEventView.__init__(self)
        self._textEditor = None
        self._markerCount = 0
        # Initialize the classes position manager for the first control
        # that is created only.
        if not docposition.DocMgr.IsInitialized():
            docposition.DocMgr.InitPositionCache()
         
    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        return SyntaxTextCtrl
    
    def GetLangId(self):
        return lang.ID_LANG_TXT

    def GetCtrl(self):
        return self._textEditor

    def SetCtrl(self, ctrl):
        self._textEditor = ctrl
            
    def OnCreate(self, doc, flags):
        frame = GetApp().CreateDocumentFrame(self, doc, flags)
        #wrap为None表示不允许自动换行,undo默认为False,表示禁止撤销操作,设置为True表示允许文本撤销恢复操作
        #use_edit_tester表示弹出菜单使用主编辑菜单的tester函数,use_edit_image表示使用主编辑菜单的编辑图标
        self._text_frame = ui_base.TextviewFrame(frame,text_class=self.GetCtrlClass(),\
                                font="EditorFont",horizontal_scrollbar_class=ui_common.AutoScrollbar,wrap=tk.NONE,undo=True,use_edit_tester=True,use_edit_image=True)
        self._textEditor = self._text_frame.text
        #绑定视图激活事件,鼠标松开或者键盘松开时激活文本视图
        self._textEditor.bind("<<ActivateView>>", self.ActivateView)
        self._textEditor.event_add("<<ActivateView>>","<KeyRelease>")
        self._textEditor.bind("<ButtonRelease>", self.ButtonRelease)
        #文本框按Esc键时如果处于全屏模式,则退出全屏模式
        self._textEditor.bind("<Escape>", self.ToogleFullScreen)
                            
        self._text_frame.grid(row=0, column=0, sticky=tk.NSEW, in_=frame)
        self._text_frame.home_widget = frame  # don't forget home

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        self._text_frame.text.bind("<<Modified>>", self.OnModify, True)
        self._text_frame.text.bind("<<TextChange>>", self.OnModify, True)
        #ctrl+鼠标滚轮放大缩小字体
        self._text_frame.text.bind("<Control-MouseWheel>", self._cmd_zoom_with_mouse, True)
        
        self.update_appearance()
        return True
        
    def ToogleFullScreen(self,event):
        if GetApp().IsFullScreen:
            ui_utils.GetFullscreenDialog().CloseDialog()
        
    def ButtonRelease(self,event):
        self.ActivateView(event)
        self.RecordTrack()
        
    @misc.update_toolbar
    @docposition.jumpto
    def RecordTrack(self):
        pass
        
    def ActivateView(self,event):
        self.SetFocus()
        #设置视图为活跃视图
        GetApp().GetDocumentManager().ActivateView(self)
        #设置状态栏行列号
        self.set_line_and_column()
        
    def _cmd_zoom_with_mouse(self, event):
        if event.delta > 0:
            self.UpdateFontSize(1)
        else:
            self.UpdateFontSize(-1)
        
    def set_line_and_column(self):
        #获取当前行,列位置
        line, column = self._textEditor.GetCurrentLineColumn()
        GetApp().MainFrame.status_bar.SetColumnNumber(column+1)
        GetApp().MainFrame.status_bar.SetLineNumber(line)

    def OnModify(self, event):
        self.GetDocument().Modify(self.IsModified())

    def SetValue(self, value,keep_undo=False):
        self.GetCtrl().set_content(value)
        #加载文件后需要禁止undo操作
        if not keep_undo:
            self.GetCtrl().edit_reset()
        self._text_frame.update_gutter()
        self.GetCtrl().after(100,self.CheckEol,value)
        
    def CheckEol(self,value):
        end_line = self.GetCtrl().get_line_col(self.GetCtrl().index('end'))[0]
        check_mixed_eol = utils.profile_get_int("check_mixed_eol",False)
        #检查混合行尾时检查全部行,否则只检查前10行文本作为eol的判断依据
        if not check_mixed_eol:
            end_line = min(end_line,10)
        mixed = False
        tmp = None
        line_eol = None
        for cur in range(1, end_line):
            txt = self.GetCtrl().get('%i.0' % cur, '%i.end' % cur)
            txt2 = self.GetCtrl().get('%i.0' % cur, '%i.end+1c' % cur)
            if txt.endswith(consts.EOL_DIC[consts.EOL_CR]) and txt2.endswith(consts.EOL_DIC[consts.EOL_LF]):
                self.GetCtrl().SetEol(consts.EOL_CRLF)
                line_eol = consts.EOL_CRLF
            #最后一行总是在最后添加\n换行符,故排除最后一行
            elif txt2.endswith(consts.EOL_DIC[consts.EOL_LF]) and cur != (end_line-1):
                self.GetCtrl().SetEol(consts.EOL_LF)
                line_eol = consts.EOL_LF
            elif txt.endswith(consts.EOL_DIC[consts.EOL_CR]):
                self.GetCtrl().SetEol(consts.EOL_CR)
                line_eol = consts.EOL_CR
            if check_mixed_eol:
                if line_eol and not tmp:
                    tmp = line_eol
                elif tmp:
                    if line_eol != tmp:
                        mixed = True
                        break
        if mixed:
            dlg = textformat.EOLFormatDlg(self.GetFrame(),self)
            if dlg.ShowModal() == constants.ID_OK:
                self.GetCtrl().SetEol(dlg.eol)
                self.GetCtrl().edit_modified(True)
    @docposition.jump
    def GotoLine(self,line):
        self.GetCtrl().GotoLine(line)
        self.set_line_and_column()
        
    @docposition.jump
    def GotoPos(self,line,col):
        self.GetCtrl().GotoPos(line,col)

    def IsModified(self):
        return self.GetCtrl().edit_modified()

    def SetModifyFalse(self):
        self.GetCtrl().edit_modified(False)
        
    def SetFocus(self):
        self._text_frame.focus_set()
        
    def update_appearance(self):
        self._text_frame.set_gutter_visibility(utils.profile_get_int("TextViewLineNumbers", True))
        #设置代码边界线长度
        view_right_edge = utils.profile_get_int("TextViewRightEdge", True)
        if view_right_edge:
            line_length_margin = utils.profile_get_int("TextEditorEdgeGuideWidth", consts.DEFAULT_EDGE_GUIDE_WIDTH)
        else:
            line_length_margin = 0
        self._text_frame.set_line_length_margin(line_length_margin)
        tag_current_line = utils.profile_get_int("TextHighlightCaretLine", True)
        self.GetCtrl().SetTagCurrentLine(tag_current_line)
        #更新代码着色
        self.GetCtrl().event_generate("<<UpdateAppearance>>")

    def GetValue(self):
        return self.GetCtrl().GetValue()
        
    #关闭文档以及文档标签页
    def OnClose(self, deleteWindow = True):
        if not core.View.OnClose(self, deleteWindow):
            return False
    
        document = self.GetDocument()
        if document.IsWatched:
            document.FileWatcher.RemoveFileDoc(document)
        #关闭文档时纪录当前光标位置,下次从新打开文件时定位到该位置
        if not document.IsNewDocument:
            docposition.DocMgr.AddRecord([document.GetFilename(),
                                           self.GetCtrl().GetCurrentLineColumn()])
        self.Activate(False)
        if deleteWindow and self.GetFrame():
            self.GetFrame().Destroy()

        return True

    def check_for_external_changes(self):
        if self._asking_about_external_change:
            return
        self._asking_about_external_change = True
        if self._alarm_event == FileEventHandler.FILE_MODIFY_EVENT:
            ret = messagebox.askyesno(_("Reload.."),_("File \"%s\" has already been modified outside,Do You Want to reload it?") % self.GetDocument().GetFilename(),
                                    parent = self.GetFrame())
            if ret == True:
                document = self.GetDocument()
                document.OnOpenDocument(document.GetFilename())
                
        elif self._alarm_event == FileEventHandler.FILE_MOVED_EVENT or \
                self._alarm_event == FileEventHandler.FILE_DELETED_EVENT:
            ret = messagebox.askyesno( _("Keep Document.."),_("File \"%s\" has already been moved or deleted outside,Do You Want to keep it in Editor?") % self.GetDocument().GetFilename(),
                           parent=self.GetFrame())
            document = self.GetDocument()
            if ret == True:
                document.Modify(True)
            else:
                document.DeleteAllViews()
        self._asking_about_external_change = False
        misc.AlarmEventView.check_for_external_changes(self)

    def ZoomView(self,delta = 0):
        self.UpdateFontSize(delta)

    def UpdateFontSize(self, delta = 0):
        editor_font = tkfont.nametofont("EditorFont")
        default_editor_font_size = editor_font['size']
        editor_font_size = default_editor_font_size
        if delta != 0:
            editor_font_size += delta
            self.UpdateFont(editor_font_size)
          #  editor_font['size'] = editor_font_size
           # self.GetCtrl().configure(font=editor_font)
            
    def UpdateFont(self,size=-1,font=""):
        font_list = ["EditorFont","BoldEditorFont","ItalicEditorFont","BoldItalicEditorFont"]
        for font_name in font_list:
            editor_font = tkfont.nametofont(font_name)
            if size != -1:
                editor_font['size'] = size
            if font != "":
                editor_font['family'] = font
            if font_name == "EditorFont":
                self.GetCtrl().configure(font=editor_font)
                
    def AddText(self,txt,pos=None):
        if pos == None:
            line,col = self.GetCtrl().GetCurrentLineColumn()
        else:
            line,col = pos
        self.GetCtrl().insert("insert", txt,"%d.%d" % (line,col))
        
    def UpdateUI(self, command_id):
        if command_id == constants.ID_SAVE:
            return self.GetDocument().IsModified()
        elif command_id in [constants.ID_INSERT_COMMENT_TEMPLATE,constants.ID_INSERT_DECLARE_ENCODING,constants.ID_UNITTEST,constants.ID_COMMENT_LINES,constants.ID_UNCOMMENT_LINES,\
                        constants.ID_RUN,constants.ID_DEBUG,constants.ID_GOTO_DEFINITION,constants.ID_SET_EXCEPTION_BREAKPOINT,constants.ID_STEP_INTO,constants.ID_STEP_NEXT,constants.ID_RUN_LAST,\
                    constants.ID_CHECK_SYNTAX,constants.ID_SET_PARAMETER_ENVIRONMENT,constants.ID_DEBUG_LAST,constants.ID_START_WITHOUT_DEBUG,constants.ID_AUTO_COMPLETE,constants.ID_TOGGLE_BREAKPOINT]:
            return False
        elif command_id == constants.ID_UNDO:
            return self.GetCtrl().CanUndo()
        elif command_id == constants.ID_REDO:
            return self.GetCtrl().CanRedo()
        elif command_id in[ constants.ID_CUT,constants.ID_COPY,constants.ID_CLEAR]:
            return self.GetCtrl().CanCopy()
        elif command_id == constants.ID_PASTE:
            return True
        elif command_id in [constants.ID_UPPERCASE,constants.ID_LOWERCASE,constants.ID_CLEAN_WHITESPACE,constants.ID_TAB_SPACE,constants.ID_SPACE_TAB]:
            return self.GetCtrl().HasSelection()
        elif command_id in [constants.ID_EOL_MAC,constants.ID_EOL_UNIX,constants.ID_EOL_WIN]:
            GetApp().MainFrame.GetNotebook().eol_var.set(self.GetCtrl().eol)
        return True
        
class TextCtrl(ui_base.TweakableText):
    """Text widget with extra navigation and editing aids. 
    Provides more comfortable deletion, indentation and deindentation,
    and undo handling. Not specific to Python code.
    
    Most of the code is adapted from idlelib.EditorWindow.
    use_edit_tester表示文本窗口弹出编辑菜单是否使用主编辑菜单的tester函数,默认为False
    use_edit_image表示是否使用主编辑菜单的编辑图标,默认为False
    tag_current_line:表示是否高亮当前行
    """

    def __init__(self, master=None, style="Text", tag_current_line=True,
                 indent_with_tabs=False, replace_tabs=False, cnf={},use_edit_tester=False,use_edit_image=False, **kw):
        # Parent class shouldn't autoseparate
        # TODO: take client provided autoseparators value into account
        kw["autoseparators"] = False
        self._style = style
        self._original_options = kw.copy()
        self._use_edit_tester = use_edit_tester
        self._use_edit_image = use_edit_image
        self._popup_menu = None
        
        ui_base.TweakableText.__init__(self,master=master, cnf=cnf, **kw)
        self.tabwidth = 8  # See comments in idlelib.editor.EditorWindow
        self.indent_width = 4
        self.indent_with_tabs = indent_with_tabs
        self.replace_tabs = replace_tabs
        self.eol = GetApp().MainFrame.GetNotebook().eol_var.get()

        self._last_event_kind = None
        self._last_key_time = None

        self._bind_editing_aids()
        self._bind_movement_aids()
        self._bind_selection_aids()
        self._bind_undo_aids()
        self._bind_mouse_aids()

        self._ui_theme_change_binding = self.bind(
            "<<ThemeChanged>>", self.reload_ui_theme, True
        )

        self._initial_configuration = self.configure()
        self._regular_insertwidth = self["insertwidth"]
        self._reload_theme_options()

        self.SetTagCurrentLine(tag_current_line)
        #是否高亮当前行
        self.bind("<<CursorMove>>", self._tag_current_line, True)
        self.bind("<<TextChange>>", self._tag_current_line, True)
        if tag_current_line:
            self._tag_current_line()
            
    def GetEol(self):
        return self.eol
        
    def SetEol(self,eol):
        self.eol = eol
        
    def SetTagCurrentLine(self,tag_current_line=False):
        self._should_tag_current_line = tag_current_line

    def _bind_mouse_aids(self):
        #单击鼠标右键事件
        self.bind("<Button-3>", self.on_secondary_click)

    def _bind_editing_aids(self):
        def if_not_readonly(fun):
            def dispatch(event):
                if not self.is_read_only():
                    return fun(event)
                else:
                    return "break"

            return dispatch

        self.bind("<Control-BackSpace>", if_not_readonly(self.delete_word_left), True)
        self.bind("<Control-Delete>", if_not_readonly(self.delete_word_right), True)
        
        #文本默认绑定这些快捷键事件,要禁止这些默认事件,重新绑定快捷键事件
        self.bind("<Control-d>", self._redirect_ctrld, True)
        self.bind("<Control-t>", self._redirect_ctrlt, True)
        self.bind("<Control-k>", self._redirect_ctrlk, True)
        self.bind("<Control-h>", self._redirect_ctrlh, True)
        self.bind("<Control-a>", self._redirect_ctrla, True)
        #tk8.5.15版本默认绑定了contrl-f事件,如果tk版本小于8.6.6,需要重新绑定该事件
        if strutils.compare_version(pyutils.get_tk_version_str(),("8.6.6")) < 0:
            self.bind("<Control-f>", self._redirect_ctrlf, True)
        
        self.bind("<BackSpace>", if_not_readonly(self.perform_smart_backspace), True)
        self.bind("<Return>", if_not_readonly(self.perform_return), True)
      #  self.bind("<KP_Enter>", if_not_readonly(self.perform_return), True)
        self.bind("<Tab>", if_not_readonly(self.perform_tab), True)
        try:
            # Is needed on eg. Ubuntu with Estonian keyboard
            self.bind("<ISO_Left_Tab>", if_not_readonly(self.perform_tab), True)
        except Exception:
            pass

        if utils.is_windows():
            self.bind("<KeyPress>", self._insert_untypable_characters_on_windows, True)

    def _bind_movement_aids(self):
        self.bind("<Home>", self.perform_smart_home, True)
        self.bind("<Left>", self.move_to_edge_if_selection(0), True)
        self.bind("<Right>", self.move_to_edge_if_selection(1), True)
        self.bind("<Next>", self.perform_page_down, True)
        self.bind("<Prior>", self.perform_page_up, True)

    def _bind_selection_aids(self):
        self.bind("<Control-a>", self.select_all, True)

    def _bind_undo_aids(self):
        self.bind("<<Undo>>", self._on_undo, True)
        self.bind("<<Redo>>", self._on_redo, True)
        self.bind("<<Cut>>", self._on_cut, True)
        self.bind("<<Copy>>", self._on_copy, True)
        self.bind("<<Paste>>", self._on_paste, True)
        self.bind("<FocusIn>", self._on_get_focus, True)
        self.bind("<FocusOut>", self._on_lose_focus, True)
        self.bind("<Key>", self._on_key_press, True)
        self.bind("<1>", self._on_mouse_click, True)
        self.bind("<2>", self._on_mouse_click, True)
        self.bind("<3>", self._on_mouse_click, True)

    def _redirect_ctrld(self, event):
        # I want to disable the deletion effect of Ctrl-D in the text but still
        # keep the event for other purposes
        self.event_generate("<<CtrlDInText>>")
        return "break"

    def _redirect_ctrlt(self, event):
        # I want to disable the swap effect of Ctrl-T in the text but still
        # keep the event for other purposes
        self.event_generate("<<CtrlTInText>>")
        return "break"
        
    def _redirect_ctrlf(self,event):
        self.event_generate("<<CtrlFInText>>")
        return "break"
        
    def _redirect_ctrla(self,event):
        self.event_generate("<<CtrlAInText>>")
        return "break"
        
    def _redirect_ctrlk(self, event):
        # I want to disable the swap effect of Ctrl-K in the text but still
        # keep the event for other purposes
        self.event_generate("<<CtrlKInText>>")
        return "break"
        
    def _redirect_ctrlh(self, event):
        # I want to disable the swap effect of Ctrl-H in the text but still
        # keep the event for other purposes
        self.event_generate("<<CtrlHInText>>")
        return "break"

    def tag_reset(self, tag_name):
        empty_conf = {key: "" for key in self.tag_configure(tag_name)}
        self.tag_configure(empty_conf)

    def select_lines(self, first_line, last_line):
        self.tag_remove("sel", "1.0", tk.END)
        self.tag_add("sel", "%s.0" % first_line, "%s.end" % last_line)

    def delete_word_left(self, event):
        self.event_generate("<Meta-Delete>")
        self.edit_separator()
        return "break"

    def delete_word_right(self, event):
        self.event_generate("<Meta-d>")
        self.edit_separator()
        return "break"

    def perform_smart_backspace(self, event):
        self._log_keypress_for_undo(event)

        text = self
        first, last = self.get_selection_indices()
        if first and last:
            text.delete(first, last)
            text.mark_set("insert", first)
            return "break"
        # Delete whitespace left, until hitting a real char or closest
        # preceding virtual tab stop.
        chars = text.get("insert linestart", "insert")
        if chars == "":
            if text.compare("insert", ">", "1.0"):
                # easy: delete preceding newline
                text.delete("insert-1c")
            else:
                text.bell()  # at start of buffer
            return "break"

        if (
            chars.strip() != ""
        ):  # there are non-whitespace chars somewhere to the left of the cursor
            # easy: delete preceding real char
            text.delete("insert-1c")
            self._log_keypress_for_undo(event)
            return "break"

        # Ick.  It may require *inserting* spaces if we back up over a
        # tab character!  This is written to be clear, not fast.
        have = len(chars.expandtabs(self.tabwidth))
        assert have > 0
        want = ((have - 1) // self.indent_width) * self.indent_width
        # Debug prompt is multilined....
        # if self.context_use_ps1:
        #    last_line_of_prompt = sys.ps1.split('\n')[-1]
        # else:
        last_line_of_prompt = ""
        ncharsdeleted = 0
        while 1:
            if chars == last_line_of_prompt:
                break
            chars = chars[:-1]
            ncharsdeleted = ncharsdeleted + 1
            have = len(chars.expandtabs(self.tabwidth))
            if have <= want or chars[-1] not in " \t":
                break
        text.delete("insert-%dc" % ncharsdeleted, "insert")
        if have < want:
            text.insert("insert", " " * (want - have))
        return "break"

    def perform_midline_tab(self, event=None):
        "如果要实现tab键自动完成单词功能,请重写该方法"
        #默认实现还是tab键缩进功能
        return self.perform_smart_tab(event)

    def perform_smart_tab(self, event=None):
        self._log_keypress_for_undo(event)

        # if intraline selection:
        #     delete it
        # elif multiline selection:
        #     do indent-region
        # else:
        #     indent one level

        first, last = self.get_selection_indices()
        if first and last:
            if index2line(first) != index2line(last):
                return self.indent_region(event)
            self.delete(first, last)
            self.mark_set("insert", first)
        prefix = self.get("insert linestart", "insert")
        raw, effective = classifyws(prefix, self.tabwidth)
        # tab to the next 'stop' within or to right of line's text:
        if self.indent_with_tabs:
            pad = "\t"
        else:
            effective = len(prefix.expandtabs(self.tabwidth))
            n = self.indent_width
            pad = " " * (n - effective % n)
        self.insert("insert", pad)
        self.see("insert")
        return "break"

    def get_cursor_position(self):
        return map(int, self.index("insert").split("."))

    def get_line_count(self):
        return list(map(int, self.index("end-1c").split(".")))[0]

    def perform_return(self, event):
        self.insert("insert", "\n")
        return "break"

    def GetIndent(self):
        return self.indent_width

    def perform_page_down(self, event):
        # if last line is visible then go to last line
        # (by default it doesn't move then)
        try:
            last_visible_idx = self.index("@0,%d" % self.winfo_height())
            row, _ = map(int, last_visible_idx.split("."))
            line_count = self.get_line_count()

            if (
                row == line_count or row == line_count - 1
            ):  # otherwise tk doesn't show last line
                self.mark_set("insert", "end")
        except Exception:
            traceback.print_exc()

    def perform_page_up(self, event):
        # if first line is visible then go there
        # (by default it doesn't move then)
        try:
            first_visible_idx = self.index("@0,0")
            row, _ = map(int, first_visible_idx.split("."))
            if row == 1:
                self.mark_set("insert", "1.0")
        except Exception:
            traceback.print_exc()

    def compute_smart_home_destination_index(self):
        """Is overridden in shell"""

        line = self.get("insert linestart", "insert lineend")
        for insertpt in range(len(line)):
            if line[insertpt] not in (" ", "\t"):
                break
        else:
            insertpt = len(line)

        lineat = int(self.index("insert").split(".")[1])
        if insertpt == lineat:
            insertpt = 0
        return "insert linestart+" + str(insertpt) + "c"

    def perform_smart_home(self, event):
        if (event.state & 4) != 0 and event.keysym == "Home":
            # state&4==Control. If <Control-Home>, use the Tk binding.
            return None

        dest = self.compute_smart_home_destination_index()

        if (event.state & 1) == 0:
            # shift was not pressed
            self.tag_remove("sel", "1.0", "end")
        else:
            if not self.index_sel_first():
                # there was no previous selection
                self.mark_set("my_anchor", "insert")
            else:
                if self.compare(self.index_sel_first(), "<", self.index("insert")):
                    self.mark_set("my_anchor", "sel.first")  # extend back
                else:
                    self.mark_set("my_anchor", "sel.last")  # extend forward
            first = self.index(dest)
            last = self.index("my_anchor")
            if self.compare(first, ">", last):
                first, last = last, first
            self.tag_remove("sel", "1.0", "end")
            self.tag_add("sel", first, last)
        self.mark_set("insert", dest)
        self.see("insert")
        return "break"

    def move_to_edge_if_selection(self, edge_index):
        """Cursor move begins at start or end of selection

        When a left/right cursor key is pressed create and return to Tkinter a
        function which causes a cursor move from the associated edge of the
        selection.
        """

        def move_at_edge(event):
            if (
                self.has_selection() and (event.state & 5) == 0
            ):  # no shift(==1) or control(==4) pressed
                try:
                    self.mark_set("insert", ("sel.first+1c", "sel.last-1c")[edge_index])
                except tk.TclError:
                    pass

        return move_at_edge

    def perform_tab(self, event=None):
        self._log_keypress_for_undo(event)
        if (
            event.state & 0x0001
        ):  # shift is pressed (http://stackoverflow.com/q/32426250/261181)
            return self.dedent_region(event)
        else:
            # check whether there are letters before cursor on this line
            index = self.index("insert")
            left_text = self.get(index + " linestart", index)
            if left_text.strip() == "" or self.has_selection():
                return self.perform_smart_tab(event)
            else:
                #如果tab键左边有非空白字符,调用自动完成功能
                return self.perform_midline_tab(event)

    def indent_region(self, event=None):
        return self._change_indentation(True)

    def dedent_region(self, event=None):
        return self._change_indentation(False)

    def _change_indentation(self, increase=True):
        head, tail, chars, lines = self._get_region()

        # Text widget plays tricks if selection ends on last line
        # and content doesn't end with empty line,
        text_last_line = index2line(self.index("end-1c"))
        sel_last_line = index2line(tail)
        if sel_last_line >= text_last_line:
            while not self.get(head, "end").endswith("\n\n"):
                self.insert("end", "\n")

        for pos in range(len(lines)):
            line = lines[pos]
            if line:
                raw, effective = classifyws(line, self.tabwidth)
                if increase:
                    effective = effective + self.indent_width
                else:
                    effective = max(effective - self.indent_width, 0)
                lines[pos] = self._make_blanks(effective) + line[raw:]
        self._set_region(head, tail, chars, lines)
        return "break"

    def select_all(self, event):
        self.tag_remove("sel", "1.0", tk.END)
        self.tag_add("sel", "1.0", tk.END)

    def set_read_only(self, value):
        if value == self.is_read_only():
            return

        ui_base.TweakableText.set_read_only(self, value)
        self._reload_theme_options()
        if self._should_tag_current_line:
            self._tag_current_line()

    def _reindent_to(self, column):
        # Delete from beginning of line to insert point, then reinsert
        # column logical (meaning use tabs if appropriate) spaces.
        if self.compare("insert linestart", "!=", "insert"):
            self.delete("insert linestart", "insert")
        if column:
            self.insert("insert", self._make_blanks(column))

    def _get_region(self):
        first, last = self.get_selection_indices()
        if first and last:
            head = self.index(first + " linestart")
            tail = self.index(last + "-1c lineend +1c")
        else:
            head = self.index("insert linestart")
            tail = self.index("insert lineend +1c")
        chars = self.get(head, tail)
        lines = chars.split("\n")
        return head, tail, chars, lines

    def _set_region(self, head, tail, chars, lines):
        newchars = "\n".join(lines)
        if newchars == chars:
            self.bell()
            return
        self.tag_remove("sel", "1.0", "end")
        self.mark_set("insert", head)
        self.delete(head, tail)
        self.insert(head, newchars)
        self.tag_add("sel", head, "insert")

    def _log_keypress_for_undo(self, e):
        if e is None:
            return

        # NB! this may not execute if the event is cancelled in another handler
        event_kind = self._get_event_kind(e)

        if (
            event_kind != self._last_event_kind
            or e.char in ("\r", "\n", " ", "\t")
            or e.keysym in ["Return", "KP_Enter"]
            or time.time() - self._last_key_time > 2
        ):
            self.edit_separator()

        self._last_event_kind = event_kind
        self._last_key_time = time.time()

    def _get_event_kind(self, event):
        if event.keysym in ("BackSpace", "Delete"):
            return "delete"
        elif event.char:
            return "insert"
        else:
            # eg. e.keysym in ("Left", "Up", "Right", "Down", "Home", "End", "Prior", "Next"):
            return "other_key"

    def _make_blanks(self, n):
        # Make string that displays as n leading blanks.
        if self.indent_with_tabs:
            ntabs, nspaces = divmod(n, self.tabwidth)
            return "\t" * ntabs + " " * nspaces
        else:
            return " " * n

    def _on_undo(self, e):
        self._last_event_kind = "undo"

    def _on_redo(self, e):
        self._last_event_kind = "redo"

    def _on_cut(self, e):
        self._last_event_kind = "cut"
        self.edit_separator()

    def _on_copy(self, e):
        self._last_event_kind = "copy"
        self.edit_separator()

    def _on_paste(self, e):
        if self.is_read_only():
            return
        
        try:
            if self.has_selection():
                self.direct_delete("sel.first", "sel.last")
        except Exception:
            pass

        self._last_event_kind = "paste"
        self.edit_separator()
        self.see("insert")
        self.after_idle(lambda: self.see("insert"))

    def _on_get_focus(self, e):
        self._last_event_kind = "get_focus"
        self.edit_separator()

    def _on_lose_focus(self, e):
        self._last_event_kind = "lose_focus"
        self.edit_separator()

    def _on_key_press(self, e):
        return self._log_keypress_for_undo(e)

    def _on_mouse_click(self, event):
        self.edit_separator()

    def _tag_current_line(self, event=None):
        self.tag_remove("current_line", "1.0", "end")

        # Let's show current line only with readable text
        # (this fits well with Thonny debugger,
        # otherwise debugger focus box and current line interact in an ugly way)
        if self._should_tag_current_line and not self.is_read_only():
            # we may be on the same line as with prev event but tag needs extension
            lineno = int(self.index("insert").split(".")[0])
            self.tag_add("current_line", str(lineno) + ".0", str(lineno + 1) + ".0")

    def on_secondary_click(self, event=None):
        "Use this for invoking context menu"
        self.focus_set()
        #如果弹出菜单存在,先销毁菜单
        if self._popup_menu is not None:
            self._popup_menu.destroy()
            self._popup_menu = None
            
        self.CreatePopupMenu()
        self._popup_menu.configure(misc.get_style_configuration("Menu"))
        self._popup_menu.tk_popup(event.x_root, event.y_root)
            
    def CreatePopupMenu(self):
        def default_tester():
            return False

        common_kwargs = {}
        #是否使用主编辑菜单的tester回调函数
        if not self._use_edit_tester:
            common_kwargs.update({
                'tester':default_tester,
            })
        #是否使用主编辑菜单的图标
        if not self._use_edit_image:
            common_kwargs.update({
                'image':None
            })
        self._popup_menu = tkmenu.PopupMenu(self,**misc.get_style_configuration("Menu"))
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(consts.ID_UNDO),\
                                handler=GetApp().MainFrame.CreateEditCommandHandler("<<Undo>>"),**common_kwargs)
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(consts.ID_REDO),\
                                handler=GetApp().MainFrame.CreateEditCommandHandler("<<Redo>>"),**common_kwargs)
        self._popup_menu.add_separator()

        args = {}
        if not self._use_edit_image:
            args.update({
                'image':None
            })
            
        if not self._use_edit_tester:
            args.update({
                'tester':self.CanCut,
            })
            
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(consts.ID_CUT),\
                                handler=GetApp().MainFrame.CreateEditCommandHandler("<<Cut>>"),**args)
                                
        if not self._use_edit_tester:
            args.update({
                'tester':self.CanCopy,
            })
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(consts.ID_COPY),\
                                handler=GetApp().MainFrame.CreateEditCommandHandler("<<Copy>>"),**args)
        if not self._use_edit_tester:
            args.update({
                'tester':self.CanPaste,
            })
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(consts.ID_PASTE),\
                                handler=GetApp().MainFrame.CreateEditCommandHandler("<<Paste>>"),**args)
                                
        if not self._use_edit_tester:
            args.update({
                'tester':self.CanDelete,
            })
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(consts.ID_CLEAR),\
                                handler=self.OnDelete,**args)
                                
        sel_args = {}
        if not self._use_edit_tester:
            sel_args['tester'] = None
        self._popup_menu.AppendMenuItem(GetApp().Menubar.GetEditMenu().FindMenuItem(consts.ID_SELECTALL),\
                                handler=GetApp().MainFrame.SelectAll,**sel_args)
        self._popup_menu["postcommand"] = lambda: self._popup_menu._update_menu()
        
    def OnDelete(self):
        '''
            删除选中文本
        '''
        start,end = self.get_selection()
        self.delete(start, end)
        
    def CanCut(self):
        if self.is_read_only() or self.IsStateDisabled():
            return False
        return self.HasSelection()

    def IsStateDisabled(self):
        return self['state'] == tk.DISABLED

    def CanCopy(self):
        return self.HasSelection()
        
    def CanDelete(self):
        if self.is_read_only() or self.IsStateDisabled():
            return False
        return self.HasSelection()

    def CanPaste(self):
        if self.is_read_only() or self.IsStateDisabled():
            return False
        return True

    def CanUndo(self):
        if self.is_read_only() or self.IsStateDisabled():
            return False
        return True

    def CanRedo(self):
        if self.is_read_only() or self.IsStateDisabled():
            return False
        return True
        
    def reload_ui_theme(self, event=None):
        self._reload_theme_options(force=True)

    def _reload_theme_options(self, force=False):

        style = ttk.Style()

        states = []
        if self.is_read_only():
            states.append("readonly")

        # Following crashes when a combobox is focused
        # if self.focus_get() == self:
        #    states.append("focus")

        if "background" not in self._initial_configuration or force:
            background = style.lookup(self._style, "background", states)
            if background:
                self.configure(background=background)

        if "foreground" not in self._initial_configuration or force:
            foreground = style.lookup(self._style, "foreground", states)
            if foreground:
                self.configure(foreground=foreground)
                self.configure(insertbackground=foreground)

    def _insert_untypable_characters_on_windows(self, event):
        if event.state == 131084:  # AltGr or Ctrl+Alt
            lang_id = get_keyboard_language()
            char = _windows_altgr_chars_by_lang_id_and_keycode.get(lang_id, {}).get(
                event.keycode, None
            )
            if char is not None:
                self.insert("insert", char)

    def destroy(self):
        self.unbind("<<ThemeChanged>>", self._ui_theme_change_binding)
        ui_base.TweakableText.destroy(self)

    def direct_insert(self, index, chars, tags=None, **kw):
        try:
            concrete_index = self.index(index)
            chars = self.check_convert_tabs_to_spaces(chars)
            ui_base.TweakableText.direct_insert(self,index, chars, tags, **kw)
        finally:
            GetApp().event_generate(
                "TextInsert",
                index=concrete_index,
                text=chars,
                tags=tags,
                text_widget=self,
            )
            
    def direct_delete(self, index1, index2=None, **kw):
        try:
            # index1 may be eg "sel.first" and it doesn't make sense *after* deletion
            concrete_index1 = self.index(index1)
            if index2 is not None:
                concrete_index2 = self.index(index2)
            else:
                concrete_index2 = None
            return ui_base.TweakableText.direct_delete(
                self, index1, index2=index2, **kw
            )
        finally:
            GetApp().event_generate(
                "TextDelete",
                index1=concrete_index1,
                index2=concrete_index2,
                text_widget=self,
            )
    
    def check_convert_tabs_to_spaces(self, chars):
        '''
            检查插入文本是否包含制表符, 并是否弹出警告提示
        '''
        tab_count = chars.count("\t")
        if not self.replace_tabs or tab_count == 0:
            return chars
        else:
            if messagebox.askyesno(_("Convert tabs to spaces?"),
                                   _("NovalIDE (according to Python recommendation) uses spaces for indentation, ")
                                   + _("but the text you are about to insert/open contains %d tab characters. ") % tab_count
                                   + _("To avoid confusion, it's better to convert them into spaces (unless you know they should be kept as tabs).\n\n" )
                                   + _("Do you want me to replace each tab with %d spaces?\n\n") % self.indent_width,
                                   parent=tk._default_root):
                return chars.expandtabs(self.indent_width)
            else:
                return chars

    def GetLineCount(self):
        #不使用end因为会在文件末尾默认添加一行,使用end-1c防止末尾添加行
        text_line_count = int(self.index("end-1c").split(".")[0])
        return text_line_count
        
    def GetCurrentLineColumn(self):
        line, column = self.get_line_col(self.index(tk.INSERT))
        return line,column

    def get_line_col(self,index):
        '''Return (line, col) tuple of ints from 'line.col' string.'''
        line, col = map(int, index.split(".")) # Fails on invalid index
        return line, col
    
    def GetCurrentLine(self):
        return self.GetCurrentLineColumn()[0]
        
    def GetCurrentColumn(self):
        return self.GetCurrentLineColumn()[1]
        
    def GetCurrentPos(self):
        return self.get_line_col(self.index(tk.INSERT))
        
    def GetLineText(self,line):
        return self.get("%d.0" % line,"%d.end"%line)

    def GetValue(self):
        value = self.get(
            "1.0", "end-1c"
        )  # -1c because Text always adds a newline itself

        #tkintext text控件只支持\n换行符,保存文件时,需要全部处理\r换行符
        chars = value.replace("\r", "")
        #如果是windows系统,则适应windows换行符
        if self.eol == consts.EOL_CRLF:
            chars = chars.replace("\n", "\r\n")
        return chars
        
    def GotoLine(self,lineno):
        assert(type(lineno) == int)
        if lineno <=0:
            lineno = 1
        self.mark_set("insert", "%d.0" % lineno)
        self.see("insert")
        self.focus_set()
        
    def ScrolltoEnd(self):
        '''
            滚到到文本最后一行
        '''
        self.mark_set("insert", "end")
        self.see("insert")
        
    def get_selection(self):
        '''Return tuple of 'line.col' indexes from selection or insert mark.
        '''
        try:
            first = self.index("sel.first")
            last = self.index("sel.last")
        except TclError:
            first = last = None
        if not first:
            first = self.index("insert")
        if not last:
            last = first
        return first, last
        
    def GotoPos(self,lineno,colno):
        self.mark_set("insert", "%d.%d" % (lineno,colno))
        self.see("insert")
        self.focus_set()

    def HasSelection(self):
        start,end = self.get_selection()
        return start!=end
        
    def GetTopLines(self,line_num):
        lines = []
        for i in range(line_num):
            #行号从1开始
            lines.append(self.GetLineText(i+1))
        return lines
        
    def GetSelectionText(self):
        first,last = self.get_selection()
        if first == last:
            return ''
        return self.get(first,last)

    def do_replace(self,text):
        first,last = self.get_selection()
        self.mark_set("insert", first)
        self.delete(first, last)
        if text:
            self.insert(first, text)

    def AddText(self,txt):
        self.insert("insert", txt)
        
    def tabify_region(self):
        head, tail, chars, lines = self._get_region()
        tabwidth = 4
        if tabwidth is None: return
        for pos in range(len(lines)):
            line = lines[pos]
            if line:
                raw, effective = classifyws(line, tabwidth)
                ntabs, nspaces = divmod(effective, tabwidth)
                lines[pos] = '\t' * ntabs + ' ' * nspaces + line[raw:]
        self._set_region(head, tail, chars, lines)

    def untabify_region(self):
        head, tail, chars, lines = self._get_region()
        tabwidth = 4
        if tabwidth is None: return
        for pos in range(len(lines)):
            lines[pos] = lines[pos].expandtabs(tabwidth)
        self._set_region(head, tail, chars, lines)

class SyntaxTextCtrl(TextCtrl,findtext.FindTextEngine):
    '''
        文本语法控件同时兼顾查找功能
    '''

    def __init__(self, master=None, cnf={}, **kw):
        TextCtrl.__init__(self, master, cnf=cnf, **kw)
        self.replace_tabs = utils.profile_get_int("check_text_tabs",True)
        findtext.FindTextEngine.__init__(self)
        self.UpdateSyntaxTheme()

    def UpdateSyntaxTheme(self):
        self.SetSyntax(syntax.SyntaxThemeManager().SYNTAX_THEMES)
        
    def SetSyntax(self,syntax_options):
        # apply new options
        for tag_name in syntax_options:
            if tag_name == "TEXT":
                self.configure(**syntax_options[tag_name])
                break
        self.SetOtherOptions(syntax_options)

    def SetOtherOptions(self,syntax_options):
        if "current_line" in syntax_options:
            self.tag_lower("current_line")
        self.tag_raise("sel")

    def _reload_theme_options(self,force=False):
        pass
        
class TextOptionsPanel(ui_utils.BaseConfigurationPanel):

    def __init__(self, parent,  hasWordWrap = False):
        ui_utils.BaseConfigurationPanel.__init__(self, parent)
        self._hasWordWrap = hasWordWrap
        self._hasTabs = False
        if self._hasWordWrap:
            self._wordWrapCheckBox = ttk.Checkbutton(self, text=_("Wrap words inside text area"))
            self._wordWrapCheckBox.SetValue(wx.ConfigBase_Get().ReadInt(self._configPrefix + "EditorWordWrap", False))
  #      self._viewWhitespaceCheckBox = wx.CheckBox(self, -1, _("Show whitespace"))
   #     self._viewWhitespaceCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewWhitespace", False))
    #    self._viewEOLCheckBox = wx.CheckBox(self, -1, _("Show end of line markers"))
     #   self._viewEOLCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewEOL", False))
      #  self._viewIndentationGuideCheckBox = wx.CheckBox(self, -1, _("Show indentation guides"))
       # self._viewIndentationGuideCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewIndentationGuides", False))
        self._viewRightEdgeVar = tk.IntVar(value=utils.profile_get_int("TextViewRightEdge", True))
        viewRightEdgeCheckBox = ttk.Checkbutton(self,text=_("Show right edge"),variable=self._viewRightEdgeVar,command=self.CheckViewRightEdge)
        viewRightEdgeCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        self._viewLineNumbersVar = tk.IntVar(value=utils.profile_get_int("TextViewLineNumbers", True))
        viewLineNumbersCheckBox = ttk.Checkbutton(self,text=_("Show line numbers"),variable=self._viewLineNumbersVar)
        viewLineNumbersCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")

        self._highlightCaretLineVar = tk.IntVar(value=utils.profile_get_int("TextHighlightCaretLine", True))
        highlightCaretLineCheckBox = ttk.Checkbutton(self,text=_("Highlight Caret Line"),variable=self._highlightCaretLineVar)
        highlightCaretLineCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        self._highlightParenthesesVar = tk.IntVar(value=utils.profile_get_int("TextHighlightParentheses", True))
        highlightParenthesesCheckBox = ttk.Checkbutton(self,text=_("Highlight parentheses"),variable=self._highlightParenthesesVar)
        highlightParenthesesCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        self._highlightSyntaxVar = tk.IntVar(value=utils.profile_get_int("TextHighlightSyntax", True))
        highlightSyntaxCheckBox = ttk.Checkbutton(self,text=_("Highlight syntax elements"),variable=self._highlightSyntaxVar)
        highlightSyntaxCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
  #      self._hasTabsVar = tk.IntVar(value=utils.profile_get_int("TextEditorUseTabs", False))
   #     hasTabsCheckBox = ttk.Checkbutton(self,text=_("Use spaces instead of tabs"),variable=self._hasTabsVar)
    #    hasTabsCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        self._tabCompletionVar = tk.IntVar(value=utils.profile_get_int("TextTabCompletion", True))
        tabCompletionCheckBox = ttk.Checkbutton(self,text=_("Allow code completion with tab-key"),variable=self._tabCompletionVar)
        tabCompletionCheckBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
##        row = ttk.Frame(self)
##        indentWidthLabel = ttk.Label(row,text=_("Indent Width:"))
##        indentWidthLabel.pack(side=tk.LEFT)
##        self._indentWidthVar = tk.IntVar(value = utils.profile_get_int("TextEditorIndentWidth", 4))
##        indentWidthChoice = ttk.Combobox(row, values = ["2", "4", "6", "8", "10"],textvariable=self._indentWidthVar)
##        indentWidthChoice.pack(side=tk.LEFT)
##        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.checkTabsVar = tk.IntVar(value=utils.profile_get_int("check_text_tabs", True))
        chkTabBox = ttk.Checkbutton(self, text=_("Warn when text contains Tabs"),variable=self.checkTabsVar)
        chkTabBox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        row = ttk.Frame(self)
        edgeWidthLabel = ttk.Label(row, text= _("Edge Guide Width:"))
        edgeWidthLabel.pack(side=tk.LEFT)
        self._edgeWidthVar = tk.IntVar(value = utils.profile_get_int("TextEditorEdgeGuideWidth", consts.DEFAULT_EDGE_GUIDE_WIDTH))
        self.edge_spin_ctrl = tk.Spinbox(row, from_=0, to=160,textvariable=self._edgeWidthVar)
        self.edge_spin_ctrl.pack(side=tk.LEFT)
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
##        defaultEOLModelLabel = wx.StaticText(self, -1, _("Default EOL Mode:"))
##        self.eol_model_combox = wx.ComboBox(self, -1,choices=EOLFormat.EOLFormatDlg.EOL_CHOICES,style= wx.CB_READONLY)
##        if sysutilslib.isWindows():
##            eol_mode = config.ReadInt(self._configPrefix + "EditorEOLMode", wx.stc.STC_EOL_CRLF)
##        else:
##            eol_mode = config.ReadInt(self._configPrefix + "EditorEOLMode", wx.stc.STC_EOL_LF)
##        idx = EOLFormat.EOLFormatDlg.EOL_ITEMS.index(eol_mode)
##        self.eol_model_combox.SetSelection(idx)

        self.CheckViewRightEdge()
        
    def CheckViewRightEdge(self):
        if self._viewRightEdgeVar.get():
            self.edge_spin_ctrl['state'] = tk.NORMAL
        else:
            self.edge_spin_ctrl['state'] = tk.DISABLED

    def OnOK(self, optionsDialog):
        doViewStuffUpdate = False
    #    doViewStuffUpdate = config.ReadInt(self._configPrefix + "EditorViewWhitespace", False) != self._viewWhitespaceCheckBox.GetValue()
     #   config.WriteInt(self._configPrefix + "EditorViewWhitespace", self._viewWhitespaceCheckBox.GetValue())
      #  doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorViewEOL", False) != self._viewEOLCheckBox.GetValue()
       # config.WriteInt(self._configPrefix + "EditorViewEOL", self._viewEOLCheckBox.GetValue())
        #doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorViewIndentationGuides", False) != self._viewIndentationGuideCheckBox.GetValue()
        #config.WriteInt(self._configPrefix + "EditorViewIndentationGuides", self._viewIndentationGuideCheckBox.GetValue())
        doViewStuffUpdate = doViewStuffUpdate or utils.profile_get_int("TextViewRightEdge", False) != self._viewRightEdgeVar.get()
        utils.profile_set( "TextViewRightEdge", self._viewRightEdgeVar.get())
        
        doViewStuffUpdate = doViewStuffUpdate or utils.profile_get_int("TextViewLineNumbers", True) != self._viewLineNumbersVar.get()
        utils.profile_set("TextViewLineNumbers", self._viewLineNumbersVar.get())
        
        doViewStuffUpdate = doViewStuffUpdate or utils.profile_get_int("TextHighlightCaretLine", True) != self._highlightCaretLineVar.get()
        utils.profile_set("TextHighlightCaretLine", self._highlightCaretLineVar.get())
        
        doViewStuffUpdate = doViewStuffUpdate or utils.profile_get_int("TextHighlightParentheses", True) != self._highlightParenthesesVar.get()
        utils.profile_set("TextHighlightParentheses", self._highlightParenthesesVar.get())
        
        doViewStuffUpdate = doViewStuffUpdate or utils.profile_get_int("TextHighlightSyntax", True) != self._highlightSyntaxVar.get()
        utils.profile_set("TextHighlightSyntax", self._highlightSyntaxVar.get())
        
      #  if sysutilslib.isWindows():
       #     default_eol_mode = wx.stc.STC_EOL_CRLF
        #else:
         #   default_eol_mode = wx.stc.STC_EOL_LF
        #eol_mode = EOLFormat.EOLFormatDlg.EOL_ITEMS[self.eol_model_combox.GetSelection()]
        #doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorEOLMode", default_eol_mode) != eol_mode
        #config.WriteInt(self._configPrefix + "EditorEOLMode", eol_mode)
        if self._viewRightEdgeVar.get():
            doViewStuffUpdate = doViewStuffUpdate or utils.profile_get_int("TextEditorEdgeGuideWidth", consts.DEFAULT_EDGE_GUIDE_WIDTH) != self._edgeWidthVar.get()
            utils.profile_set("TextEditorEdgeGuideWidth", self._edgeWidthVar.get())
       # if self._hasFolding:
        #    doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorViewFolding", True) != self._viewFoldingCheckBox.GetValue()
         #   config.WriteInt(self._configPrefix + "EditorViewFolding", self._viewFoldingCheckBox.GetValue())
        #if self._hasWordWrap:
          #  doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorWordWrap", False) != self._wordWrapCheckBox.GetValue()
           # config.WriteInt(self._configPrefix + "EditorWordWrap", self._wordWrapCheckBox.GetValue())
        if self._hasTabs:
            doViewStuffUpdate = doViewStuffUpdate or not config.ReadInt(self._configPrefix + "EditorUseTabs", True) != self._hasTabsCheckBox.GetValue()
            config.WriteInt(self._configPrefix + "EditorUseTabs", not self._hasTabsCheckBox.GetValue())
            newIndentWidth = int(self._indentWidthChoice.GetStringSelection())
            oldIndentWidth = config.ReadInt(self._configPrefix + "EditorIndentWidth", 4)
            if newIndentWidth != oldIndentWidth:
                doViewStuffUpdate = True
                config.WriteInt(self._configPrefix + "EditorIndentWidth", newIndentWidth)
        GetApp().MainFrame.GetNotebook().update_appearance()
        utils.profile_set("TextTabCompletion",self._tabCompletionVar.get())
        utils.profile_set("check_text_tabs",self.checkTabsVar.get())
        return True
               
         
    def GetIcon(self):
        return getTextIcon()