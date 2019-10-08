# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        findindir.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-14
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import _,GetApp
import os
from os.path import join
import re
import noval.misc as misc
import noval.util.strutils as strutils
import time
import threading
import noval.util.fileutils as fileutils
import tkinter as tk
from tkinter import ttk,filedialog
import noval.consts as consts
import noval.syntax.syntax as syntax
import noval.find.find as findtext
import noval.util.utils as utils
import noval.ui_base as ui_base
import queue
import noval.util.singleton as singleton
from noval.project.document import ProjectDocument

#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------
FILENAME_MARKER = "Found in file: "
PROJECT_MARKER = "Searching project: "
FILE_MARKER = "Searching file: "
FIND_MATCHDIR = "FindMatchDir"
FIND_MATCHDIRSUBFOLDERS = "FindMatchDirSubfolders"

def _open(filename):
    if utils.is_py2():
        f = open(filename, 'r')
    else:
        f = open(filename, 'r',errors='replace')
    return f
    

class FindDirOption:
    def __init__(self,find_text_option,path,recursive=True,search_hidden=False,file_type_list=[]):
        self.find_option = find_text_option
        self.path = path
        self.recursive = recursive
        self.search_hidden = search_hidden
        self.file_types = file_type_list
        
FIND_DIR_OPTION = FindDirOption(findtext.CURERNT_FIND_OPTION,"")
    
@singleton.Singleton
class FindIndirService:
    
    LINE_PREFIX = "Line "
    #设置文件查找队列最大长度
    MAX_LIMIT_LIST_FILE_LENGTH = 1000
    
    def __init__(self):
        self.progress_dlg = None
        self._is_searching_text = False
        #总的文件查找个数,用来设置进度条的最大值
        self.total_find_filecount = 0
        
    def FindIndir(self,find_dir_option,result_view):
        #创建一个消息队列
        self.notify_queue = queue.Queue()
        self.progress_dlg = None
        self.total_find_filecount = 0
        #3秒后才显示进度条对话框,如果在此时间内搜索文本操作已经完成,则不会显示进度条对话框
        GetApp().MainFrame.after(3000,self.ShowSearchProgressDialog)
        t = threading.Thread(target=self.FindTextIndir,args = (find_dir_option,result_view,self.notify_queue))
        t.start()

    def ShowSearchProgressDialog(self):
        #如果搜索文本操作已经完成,则不会显示进度条对话框
        if self._is_searching_text:
            dlg = SearchProgressDialog(GetApp(),self.notify_queue,maximum=self.total_find_filecount)
            self.progress_dlg = dlg
            dlg.ShowModal()

    def FindTextIndir(self,find_dir_option,view,que):
        #设置正在搜索文本
        self._is_searching_text = True
        total_found_line = 0
        list_files = []
        cur_pos = 0
        # do search in files on disk
        for root, dirs, files in os.walk(find_dir_option.path):
            if self.progress_dlg is not None and not self.progress_dlg.keep_going:
                break
            #是否搜索子目录
            if not find_dir_option.recursive and root != find_dir_option.path:
                break
            #是否搜索隐藏目录
            if not find_dir_option.search_hidden and fileutils.is_file_path_hidden(root):
               # utils.get_logger().debug('search path %s is hidden',root)
                continue
            for name in files:
                #后缀文件名列表为空表示搜索所有后缀的文件
                if find_dir_option.file_types != []:
                    file_ext = strutils.get_file_extension(name)
                    #查找时过滤文件后缀名
                    if file_ext not in find_dir_option.file_types:
              #          utils.get_logger().debug('search path %s/%s extension %s is filtered',root,name,file_ext)
                        continue
                filename = os.path.join(root, name)
                #是否搜索隐藏文件
                if not find_dir_option.search_hidden and fileutils.is_file_path_hidden(filename):
             #       utils.get_logger().debug('search file %s is hidden',filename)
                    break
                list_files.append(filename)
                self.total_find_filecount += 1
                if len(list_files) >= self.MAX_LIMIT_LIST_FILE_LENGTH:
                    if self.IsProgressRunning():
                        self.progress_dlg.SetRange(self.total_find_filecount)
                    found_line,cur_pos = self.FindTextInFiles(find_dir_option.find_option,view,list_files,cur_pos,que)
                    total_found_line += found_line
                    list_files = []
        #处理一些队列末尾的文件查找
        if self.total_find_filecount > 0 and len(list_files) >0:
            if self.IsProgressRunning():
                self.progress_dlg.SetRange(self.total_find_filecount)
            found_line,cur_pos = self.FindTextInFiles(find_dir_option.find_option,view,list_files,cur_pos,que)
            total_found_line += found_line
        self._is_searching_text = False
        #结束进度条的标志
        que.put((None,None))
        utils.get_logger().debug('find %d results in %d files',total_found_line,self.total_find_filecount)
        view.AddLine(_("Search completed,Find total %d results.") % total_found_line)
        
    def IsProgressRunning(self):
        if self.progress_dlg is not None and self.progress_dlg.keep_going:
            return True
        return False
        
    def FindTextInFiles(self,find_text_option,view,list_files,cur_pos,que):
        '''
            在文件列表中查找文本,将查找结果插入到队列当中,进度条界面会读取队列当中的内容
            并设置查找进度
        '''
        assert(cur_pos >=0)
        found_line = 0
        for list_file in list_files:
            #只有进度条显示,并且点击取消按钮时才退出
            if self.progress_dlg is not None and not self.progress_dlg.keep_going:
                break
            found_line += self.FindTextInFile(list_file,find_text_option,view)
            utils.get_logger().debug('find %s in file %s %d results',find_text_option.findstr,list_file,found_line)
            msg=_("search file:%s") % list_file
            que.put((cur_pos,msg))
            cur_pos += 1
        return found_line,cur_pos

    def FindTextInFile(self,filename,find_text_option,view):
        '''
            在单个文件中查找文本
        '''
        findString = find_text_option.findstr
        matchCase = find_text_option.match_case
        wholeWord = find_text_option.match_whole_word
        regExpr = find_text_option.regex
        found_line = 0
        try:
            docFile=_open(filename)
        except IOError as e:
            utils.get_logger().debug("Warning, unable to read file: '%s'.  %s",filename, str(e))
            return found_line
        needToDisplayFilename = True
        #遍历列表序号从1开始 
        for lineNum, line in enumerate(docFile, 1):
            count, foundStart, foundEnd, newText = self.DoFind(findString, None, line, 0, 0, True, matchCase, wholeWord, regExpr)
            if count != -1:
                if needToDisplayFilename:
                    view.AddLine(FILENAME_MARKER + filename + "\n")
                    needToDisplayFilename = False
                line = self.LINE_PREFIX + str(lineNum) + ":" + line
                #限制一行文本的长度
                if len(line) > self.MAX_LIMIT_LIST_FILE_LENGTH:
                    line = line[0:self.MAX_LIMIT_LIST_FILE_LENGTH]
                view.AddLine(line)
                found_line += 1
        if not needToDisplayFilename:
            view.AddLine("\n")
        view.ScrolltoEnd()
        return found_line
        

    def DoFind(self, findString, replaceString, text, startLoc, endLoc, down, matchCase, wholeWord, regExpr = False, replace = False, replaceAll = False, wrap = False):
        """
            在一行文本中查找要找的文本
            Do the actual work of the find/replace.
        
            Returns the tuple (count, start, end, newText).
            count = number of string replacements
            start = start position of found string
            end = end position of found string
            newText = new replaced text 
        """
        flags = 0
        if regExpr:
            pattern = findString
        else:
            pattern = re.escape(findString)  # Treat the strings as a literal string
        if not matchCase:
            flags = re.IGNORECASE
        if wholeWord:
            pattern = r"\b%s\b" % pattern
            
        try:
            reg = re.compile(pattern, flags)
        except:
            # syntax error of some sort
            import sys
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("Regular Expression Search")
            wx.MessageBox(_("Invalid regular expression \"%s\". %s") % (pattern, sys.exc_value),
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION,
                          self.GetView())
            return FIND_SYNTAXERROR, None, None, None

        if replaceAll:
            newText, count = reg.subn(replaceString, text)
            if count == 0:
                return -1, None, None, None
            else:
                return count, None, None, newText

        start = -1
        if down:
            match = reg.search(text, endLoc)
            if match == None:
                if wrap:  # try again, but this time from top of file
                    match = reg.search(text, 0)
                    if match == None:
                        return -1, None, None, None
                else:
                    return -1, None, None, None
            start = match.start()
            end = match.end()
        else:
            match = reg.search(text)
            if match == None:
                return -1, None, None, None
            found = None
            i, j = match.span()
            while i < startLoc and j <= startLoc:
                found = match
                if i == j:
                    j = j + 1
                match = reg.search(text, j)
                if match == None:
                    break
                i, j = match.span()
            if found == None:
                if wrap:  # try again, but this time from bottom of file
                    match = reg.search(text, startLoc)
                    if match == None:
                        return -1, None, None, None
                    found = None
                    i, j = match.span()
                    end = len(text)
                    while i < end and j <= end:
                        found = match
                        if i == j:
                            j = j + 1
                        match = reg.search(text, j)
                        if match == None:
                            break
                        i, j = match.span()
                    if found == None:
                        return -1, None, None, None
                else:
                    return -1, None, None, None
            start = found.start()
            end = found.end()

        if replace and start != -1:
            newText, count = reg.subn(replaceString, text, 1)
            return count, start, end, newText

        return 0, start, end, None

    def DoFindIn(self, findString, matchCase, wholeWord, regExpr, result_view,currFileOnly=False):
        '''
            在当前文档中或所有项目文档中查找文本
        '''
        result_view.ClearLines()
        current_docview = None
        current_editor = GetApp().MainFrame.GetNotebook().get_current_editor()
        if current_editor is not None:
            current_docview = current_editor.GetView()
        if current_docview:
            currDoc = current_docview.GetDocument()
        else:
            currDoc = None
        #仅查找当前文件
        if currFileOnly:
            if currDoc:
                projectFilenames = [currDoc.GetFilename()]
                result_view.AddLine(FILE_MARKER + currDoc.GetFilename() + "\n\n")
            else:
                projectFilenames = []
        else:
            #查找当前项目的所有文件
            project_browser = GetApp().MainFrame.GetProjectView()
            projectFilenames = project_browser.GetFilesFromCurrentProject()
            projView = project_browser.GetView()
            if projView:
                projName = fileutils.get_filename_from_path(projView.GetDocument().GetFilename())
                result_view.AddLine(PROJECT_MARKER + projName + "\n\n")

        found_line = 0
        #先查找在编辑器中打开的文本,因为这些文本内容可能已经和实际存储的文件不一致了
        openDocs = GetApp().GetDocumentManager().GetDocuments()
        #python3 filter不返回列表,返回filter对象,需要手动转换成list
        openDocsInProject = list(filter(lambda openDoc: openDoc.GetFilename() in projectFilenames, openDocs))
        if currDoc and currDoc in openDocsInProject:
            # make sure current document is searched first.
            openDocsInProject.remove(currDoc)
            openDocsInProject.insert(0, currDoc)
            
        utils.get_logger().debug("start to search text for open project docs")
        for openDoc in openDocsInProject:
            if isinstance(openDoc, ProjectDocument):  # don't search project model
                continue

            openDocView = openDoc.GetFirstView()
            # some views don't have a in memory text object to search through such as the PM and the DM
            # even if they do have a non-text searchable object, how do we display it in the message window?
            if not hasattr(openDocView, "GetValue"):
                continue
            line_count = openDocView.GetCtrl().GetLineCount()
            needToDisplayFilename = True
            for lineNum in range(line_count):
                line_text = openDocView.GetCtrl().GetLineText(lineNum+1)
                count, foundStart, foundEnd, newText = self.DoFind(findString, None, line_text, 0, 0, True, matchCase, wholeWord, regExpr)
                if count != -1:
                    if needToDisplayFilename:
                        result_view.AddLine(FILENAME_MARKER + openDoc.GetFilename() + "\n")
                        needToDisplayFilename = False

                    line = self.LINE_PREFIX + str(lineNum+1) + ":" + line_text
                    result_view.AddLine(line)
                    found_line += 1
            if not needToDisplayFilename:
                result_view.AddLine("\n")
                
        utils.get_logger().debug("end to search text for open project docs")
        openDocNames = list(map(lambda openDoc: openDoc.GetFilename(), openDocs))
        #再查找所有项目中未打开的文件,按照查找文件的方式查找文本
        filenames = filter(lambda filename: filename not in openDocNames, projectFilenames)
        utils.get_logger().debug("start to search text for closed project docs")
        for filename in filenames:
            try:
                docFile = _open(filename)
            except IOError:
                continue

            lineNum = 1
            needToDisplayFilename = True
            line = docFile.readline()
            while line:
                count, foundStart, foundEnd, newText = self.DoFind(findString, None, line, 0, 0, True, matchCase, wholeWord, regExpr)
                if count != -1:
                    if needToDisplayFilename:
                        result_view.AddLine(FILENAME_MARKER + filename + "\n")
                        needToDisplayFilename = False
                    line = self.LINE_PREFIX + repr(lineNum).zfill(4) + ":" + line
                    result_view.AddLine(line)
                    found_line += 1
                line = docFile.readline()
                lineNum += 1
            if not needToDisplayFilename:
                result_view.AddLine("\n")
        utils.get_logger().debug("end to search text for closed project docs")
        result_view.AddLine(_("Search for '%s' completed, Find total %d results.") % (findString,found_line))
        
    def FindInfile(self,find_text_option,result_view):
        '''
            在当前文件中查找
        '''
        findString = find_text_option.findstr
        matchCase = find_text_option.match_case
        wholeWord = find_text_option.match_whole_word
        regExpr = find_text_option.regex
        self.DoFindIn(findString, matchCase, wholeWord, regExpr, currFileOnly=True,result_view=result_view)

    def FindInproject(self,find_text_option,result_view):
        '''
            在当前项目中查找
        '''
        findString = find_text_option.findstr
        matchCase = find_text_option.match_case
        wholeWord = find_text_option.match_whole_word
        regExpr = find_text_option.regex
        self.DoFindIn(findString, matchCase, wholeWord, regExpr,result_view=result_view)
        

class FindIndirDialog(ui_base.CommonModaldialog):
    
    def __init__(self, master,findString=''):
        ui_base.CommonModaldialog.__init__(self, master, takefocus=1)
        self.title(_("Find in Directory"))
        self.resizable(height=tk.FALSE, width=tk.FALSE)
        self.default_extentsion = "." + syntax.SyntaxThemeManager().GetLexer(GetApp().GetDefaultLangId()).GetDefaultExt()
        #隐藏最小化按钮
        self.transient(master)
        top_frame = ttk.Frame(self)
        top_frame.grid(column=0, row=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        
        self.find_indir_label = ttk.Label(top_frame, text=_("Directory:"))
        self.find_indir_label.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        # Find text field
        self.path_entry_var = tk.StringVar(value=FIND_DIR_OPTION.path)
        self.path_entry = ttk.Entry(top_frame, textvariable=self.path_entry_var)
        self.path_entry.pack(side=tk.LEFT,fill="x",expand=1,padx=(0,0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.browser_button = ttk.Button(
            top_frame, text=_("Browse..."), command=self.BrowsePath
        )
        self.browser_button.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        self.recursive_var = tk.IntVar()
        self.search_child_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Search in subdirectories"), variable=self.recursive_var
        )
        self.search_child_checkbutton.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.search_hidden_var = tk.IntVar()
        self.search_hidden_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Search hidden files"), variable=self.search_hidden_var
        )
        self.search_hidden_checkbutton.pack(fill="x",side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=2, sticky="nsew")
        separator = ttk.Separator(sizer_frame, orient = tk.HORIZONTAL)
        separator.pack(expand=1, fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))

        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=3, sticky="nsew")
        self.find_label = ttk.Label(sizer_frame,text=_("Find what:"),)
        self.find_label.pack(fill="x", side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y, 0))

        self.find_entry = findtext.FindtextCombo(sizer_frame,findString)
        self.find_entry_var = self.find_entry.find_entry_var
        self.find_entry_var.trace("w", self._update_button_statuses)
        self.find_entry.pack(fill="x",side=tk.LEFT, padx=(0, consts.DEFAUT_HALF_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        

        self.filetypes_label = ttk.Label(sizer_frame,text=_("File types:"))
        self.filetypes_label.pack(fill="x", side=tk.LEFT,padx=(0,0),pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y, 0))
        
        self.filetypes_entry_var = tk.StringVar(value="*" + self.default_extentsion)
        self.filetypes_entry = ttk.Entry(sizer_frame, textvariable=self.filetypes_entry_var,width=8)
        self.filetypes_entry.pack(fill="x",side=tk.LEFT,padx=(0, 0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        misc.create_tooltip(self.filetypes_entry,_("Multiple file types seperated by semicolon"))
        

        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=4, sticky="nsew")
        self.case_var = tk.IntVar(value=findtext.CURERNT_FIND_OPTION.match_case)
        self.case_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Case sensitive"), variable=self.case_var
        )
        self.case_checkbutton.pack(fill="x", padx=(consts.DEFAUT_CONTRL_PAD_X, 0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.whole_word_var = tk.IntVar(value=findtext.CURERNT_FIND_OPTION.match_whole_word)
        self.whole_word_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Match whole word"), variable=self.whole_word_var
        )
        self.whole_word_checkbutton.pack(fill="x", padx=(consts.DEFAUT_CONTRL_PAD_X, 0))
        
        self.regular_var = tk.IntVar(value=findtext.CURERNT_FIND_OPTION.regex)
        self.regular_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Regular expression"), variable=self.regular_var
        )
        self.regular_checkbutton.pack(fill="x", padx=(consts.DEFAUT_CONTRL_PAD_X, 0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
        right_frame = ttk.Frame(self)
        right_frame.grid(column=1, row=0, sticky="nsew",rowspan=5)
        
        self.search_button = ttk.Button(
            right_frame, text=_("Find"), command=self.FindIndir, default="active"
        )
        self.search_button.pack(fill="x",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,consts.DEFAUT_HALF_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.cancel_button = ttk.Button(
            right_frame, text=_("Cancel"), command=self.Close
        )
        self.cancel_button.pack(fill="x",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,consts.DEFAUT_HALF_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.bind("<Return>", self.FindIndir, True)
        self._update_button_statuses()
        self.LoadConfig()

    def Close(self):
        self.SaveConfig()
        self.destroy()

    def SaveConfig(self):
        """ Save find/replace patterns and search flags to registry. """
        utils.profile_set(findtext.FIND_MATCHPATTERN, self.find_entry_var.get())
        utils.profile_set(findtext.FIND_MATCHCASE, self.case_var.get())
        utils.profile_set(findtext.FIND_MATCHWHOLEWORD, self.whole_word_var.get())
        utils.profile_set(findtext.FIND_MATCHREGEXPR, self.regular_var.get())
        utils.profile_set(FIND_MATCHDIR,self.path_entry_var.get())
        utils.profile_set(FIND_MATCHDIRSUBFOLDERS,self.recursive_var.get())
        self.find_entry.save_match_patters()

    def LoadConfig(self):
        #如果未有指定字符串,从配置中加载上一次查找的字符串
        if not self.find_entry_var.get():
            self.find_entry_var.set(utils.profile_get(findtext.FIND_MATCHPATTERN,''))
        self.case_var.set(utils.profile_get_int(findtext.FIND_MATCHCASE,False))
        self.whole_word_var.set(utils.profile_get_int(findtext.FIND_MATCHWHOLEWORD,False))
        self.regular_var.set(utils.profile_get_int(findtext.FIND_MATCHREGEXPR,False))
        self.path_entry_var.set(utils.profile_get(FIND_MATCHDIR,""))
        self.recursive_var.set(utils.profile_get_int(FIND_MATCHDIRSUBFOLDERS,False))
        self.find_entry.load_match_patters()
        
    def BrowsePath(self):
        path = filedialog.askdirectory()
        if path:
            #必须转换一下路径为系统标准路径格式
            path = fileutils.opj(path)
            self.path_entry_var.set(path)
            

    def GetFileTypeList(self,file_type_str):
        if file_type_str == "" or file_type_str == "*.*" or file_type_str=="*":
            return []
        type_parts = file_type_str.split(";")
        return [part.replace("*.","") for part in type_parts]
        
            
    def FindIndir(self,event=None):
        global FIND_DIR_OPTION
        
        path = self.path_entry_var.get()
        findstr = self.find_entry_var.get()
        if findstr == "" or str(self.search_button['state']) == tk.DISABLED:
            return
        FIND_DIR_OPTION.find_option.findstr = findstr
        FIND_DIR_OPTION.path = path
        FIND_DIR_OPTION.recursive = self.recursive_var.get()
        FIND_DIR_OPTION.search_hidden = self.search_hidden_var.get()
        FIND_DIR_OPTION.find_option.match_case = self.case_var.get()
        FIND_DIR_OPTION.find_option.match_whole_word = self.whole_word_var.get()
        FIND_DIR_OPTION.find_option.regex = self.regular_var.get()
        FIND_DIR_OPTION.file_types = self.GetFileTypeList(self.filetypes_entry_var.get().strip())
        
        result_view = GetApp().MainFrame.GetSearchresultsView()
        result_view.ClearLines()
        result_view.AddLine(_("Searching for '%s' in '%s'\n\n") % (findstr, path))
        findserivice = FindIndirService()
        if os.path.isfile(path):
            findserivice.FindTextInFile(path,FIND_DIR_OPTION.find_option,result_view)
        else:
            findserivice.FindIndir(FIND_DIR_OPTION,result_view)
        self.Close()
        
    def _update_button_statuses(self, *args):
        find_text = self.find_entry_var.get()
        if len(find_text) == 0:
            self.search_button.config(state="disabled")
        else:
            self.search_button.config(state="normal")

class SearchProgressDialog(ui_base.GenericProgressDialog):
    
    def __init__(self,master,que,maximum):
        ui_base.GenericProgressDialog.__init__(self, master,_("Find Text In Directory"), maximum=maximum,info=_("Please wait a minute for end find text"))
        self.notify_queue = que
        self.process_msg()
        
    def process_msg(self):
        self.master.after(400,self.process_msg)
        while not self.notify_queue.empty():
            try:
                msg = self.notify_queue.get()
                if msg[0] == None:
                    self.destroy()
                else:
                    cur_val,filename = msg
                    self.SetValue(cur_val)
                    self.SetInfo(filename)

            except queue.Empty:
                pass


class FindInfileDialog(ui_base.CommonModaldialog):
    
    def __init__(self, master,findString = ""):
        ui_base.CommonModaldialog.__init__(self, master, takefocus=1)
        self.UpdateTitle()
        self.resizable(height=tk.FALSE, width=tk.FALSE)
        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=0, sticky="nsew")
        self.find_label = ttk.Label(sizer_frame,text=_("Find what:"),)
        self.find_label.pack(fill="x", side=tk.LEFT,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y, 0))

        
        self.find_entry = findtext.FindtextCombo(sizer_frame,findString)
        self.find_entry_var = self.find_entry.find_entry_var
        self.find_entry_var.trace("w", self._update_button_statuses)
        self.find_entry.pack(fill="x",side=tk.LEFT, padx=(0, consts.DEFAUT_HALF_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))

        sizer_frame = ttk.Frame(self)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        self.case_var = tk.IntVar(value=findtext.CURERNT_FIND_OPTION.match_case)
        self.case_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Case sensitive"), variable=self.case_var
        )
        self.case_checkbutton.pack(fill="x", padx=(consts.DEFAUT_CONTRL_PAD_X, 0),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.whole_word_var = tk.IntVar(value=findtext.CURERNT_FIND_OPTION.match_whole_word)
        self.whole_word_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Match whole word"), variable=self.whole_word_var
        )
        self.whole_word_checkbutton.pack(fill="x", padx=(consts.DEFAUT_CONTRL_PAD_X, 0))
        
        self.regular_var = tk.IntVar(value=findtext.CURERNT_FIND_OPTION.regex)
        self.regular_checkbutton = ttk.Checkbutton(
            sizer_frame, text=_("Regular expression"), variable=self.regular_var
        )
        self.regular_checkbutton.pack(fill="x", padx=(consts.DEFAUT_CONTRL_PAD_X, 0),pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
        right_frame = ttk.Frame(self)
        right_frame.grid(column=1, row=0, sticky="nsew",rowspan=5)
        
        self.search_button = ttk.Button(
            right_frame, text=_("Find"), command=self.FindText, default="active"
        )
        self.search_button.pack(fill="x",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,consts.DEFAUT_HALF_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.cancel_button = ttk.Button(
            right_frame, text=_("Cancel"), command=self.destroy
        )
        self.cancel_button.pack(fill="x",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,consts.DEFAUT_HALF_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.bind("<Return>", self.FindText, True)
        self._update_button_statuses()
        self.LoadConfig()
        
    def IsFindAvailable(self):
        '''
            按回车键执行查找时检测按钮是否可用
        '''
        return str(self.search_button['state']) == tk.NORMAL and self.find_entry_var.get() != '' 
        
    def UpdateTitle(self):
        self.dlg_title = _("Find in File")
        self.title(self.dlg_title)
        
    def FindText(self,event=None):
        if not self.IsFindAvailable():
            return
        self.GetFindTextOption()
        FindIndirService().FindInfile(findtext.CURERNT_FIND_OPTION,GetApp().MainFrame.GetSearchresultsView())
        self.destroy()
        
    def destroy(self):
        self.SaveConfig()
        ui_base.CommonModaldialog.destroy(self)
        
    def GetFindTextOption(self):
        findstr = self.find_entry_var.get()
        findtext.CURERNT_FIND_OPTION.findstr = findstr
        findtext.CURERNT_FIND_OPTION.match_case = self.case_var.get()
        findtext.CURERNT_FIND_OPTION.match_whole_word = self.whole_word_var.get()
        findtext.CURERNT_FIND_OPTION.regex = self.regular_var.get()
        
    def _update_button_statuses(self, *args):
        find_text = self.find_entry_var.get()
        if len(find_text) == 0:
            self.search_button.config(state="disabled")
        else:
            self.search_button.config(state="normal")

    def SaveConfig(self):
        """ Save find/replace patterns and search flags to registry. """
        utils.profile_set(findtext.FIND_MATCHPATTERN, self.find_entry_var.get())
        utils.profile_set(findtext.FIND_MATCHCASE, self.case_var.get())
        utils.profile_set(findtext.FIND_MATCHWHOLEWORD, self.whole_word_var.get())
        utils.profile_set(findtext.FIND_MATCHREGEXPR, self.regular_var.get())
        self.find_entry.save_match_patters()

    def LoadConfig(self):
        #如果未有指定字符串,从配置中加载上一次查找的字符串
        if not self.find_entry_var.get():
            self.find_entry_var.set(utils.profile_get(findtext.FIND_MATCHPATTERN,''))
        self.case_var.set(utils.profile_get_int(findtext.FIND_MATCHCASE,False))
        self.whole_word_var.set(utils.profile_get_int(findtext.FIND_MATCHWHOLEWORD,False))
        self.regular_var.set(utils.profile_get_int(findtext.FIND_MATCHREGEXPR,False))
        self.find_entry.load_match_patters()

class FindInprojectDialog(FindInfileDialog):
    
    def __init__(self, master,findString):
        FindInfileDialog.__init__(self,master,findString)
        
    def UpdateTitle(self):
        self.dlg_title = _("Find in Project")
        self.title(self.dlg_title)
        
    def FindText(self,event=None):
        if not self.IsFindAvailable():
            return
        self.GetFindTextOption()
        FindIndirService().FindInproject(findtext.CURERNT_FIND_OPTION,GetApp().MainFrame.GetSearchresultsView())
        self.destroy()

def ShowFindIndirDialog(master,editor):
    if editor == None or not hasattr(editor.GetView(),"GetCtrl"):
        findString = ''
    else:
        findString = editor.GetView().GetCtrl().GetSelectionText()
        
    dlg = FindIndirDialog(master,findString)
    dlg.ShowModal()

def ShowFindInfileDialog(master):
    findString = master.GetView().GetCtrl().GetSelectionText()
    dlg = FindInfileDialog(master,findString)
    dlg.ShowModal()

def ShowFindInprojectDialog(master,editor):
    if editor == None or not hasattr(editor.GetView(),"GetCtrl"):
        findString = ''
    else:
        findString = editor.GetView().GetCtrl().GetSelectionText()
    dlg = FindInprojectDialog(master,findString)
    dlg.ShowModal()
