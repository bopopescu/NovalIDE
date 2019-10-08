# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        find.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-14
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import _,GetApp
import tkinter as tk
from tkinter import ttk
import re
import os
import noval.util.apputils as sysutilslib
import noval.consts as consts
import noval.util.utils as utils
import noval.editor.text as texteditor

#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------

#这些常量为保存在配置文件中的键值
FIND_MATCHPATTERN = "FindMatchPattern"
FIND_MATCHPATTERN_LIST = "FindMatchPatterns"
FIND_MATCHREPLACE = "FindMatchReplace"
FIND_MATCHCASE = "FindMatchCase"
FIND_MATCHWHOLEWORD = "FindMatchWholeWordOnly"
FIND_MATCHREGEXPR = "FindMatchRegularExpr"
FIND_MATCHWRAP = "FindMatchWrap"
FIND_MATCHUPDOWN = "FindMatchUpDown"

FR_DOWN = 1
FR_WHOLEWORD = 2
FR_MATCHCASE = 4
FR_REGEXP = max([FR_WHOLEWORD, FR_MATCHCASE, FR_DOWN]) << 1
FR_WRAP = FR_REGEXP << 1


_active_find_dialog = None
_active_find_replace_dialog = None

class FindtextCombo(ttk.Combobox):
    def __init__(self,master,findString="",**kw):
        if not findString:
            findString = CURERNT_FIND_OPTION.findstr
            #如果没有则从配置中查找存储的上次查找的文本
            if not findString:
                findString = utils.profile_get(FIND_MATCHPATTERN, "")
        #去除搜索文本的换行符,运行文本末尾有空格
        strip_find_text = findString.split('\n')[0].rstrip('\r')
        self.find_entry_var = tk.StringVar(value=strip_find_text)
        ttk.Combobox.__init__(self,master,textvariable=self.find_entry_var,**kw)
        
    def save_match_patters(self):
        values = self['values']
        if not values:
            values = []
        values = list(values)
        if self.find_entry_var.get() and not self.find_entry_var.get() in values:
            values.insert(0,self.find_entry_var.get())
        #最多存储50个单词
        utils.profile_set(FIND_MATCHPATTERN_LIST, values[0:20])
        
    def load_match_patters(self):
        find_string_list = utils.profile_get(FIND_MATCHPATTERN_LIST, [])
        self['values'] = find_string_list

class FindOpt:
    def __init__(self,findstr,match_case=False,match_whole_word=False,wrap=True,down=True,regex=False):
        self.findstr = findstr
        self.match_case = match_case
        self.match_whole_word = match_whole_word
        self.wrap = wrap
        self.down = down
        self.regex = regex
        
CURERNT_FIND_OPTION = FindOpt('')
        
class FindDialog(tk.Toplevel):
    last_searched_word = None
    
    def __init__(self, master,findString="",replace=False):
        tk.Toplevel.__init__(self, master, takefocus=1)
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        #查找焦点文本控件
        self.text = None
        # set up window display
        self.geometry(
            "+%d+%d"
            % (
                master.winfo_rootx() + master.winfo_width() // 2,
                master.winfo_rooty() + master.winfo_height() // 2 - 150,
            )
        )

        self.title(_("Find"))
        self.resizable(height=tk.FALSE, width=tk.FALSE)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._ok)

        # Find text label
        self.find_label = ttk.Label(self.main_frame, text=_("Find what:"))
        self.find_label.grid(
            column=0, row=0, sticky="w", padx=(consts.DEFAUT_CONTRL_PAD_X, 0), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0)
        )
        
        #是否有指定的查找文本,则使用上一次的查找文本
        if not findString:
            findString = CURERNT_FIND_OPTION.findstr
            #如果没有则从配置中查找存储的上次查找的文本
            if not findString:
                findString = utils.profile_get(FIND_MATCHPATTERN, "")

        # Find text field
        self.find_entry = FindtextCombo(self.main_frame,findString)
        self.find_entry_var = self.find_entry.find_entry_var
        self.find_entry.grid(
            column=1, row=0, padx=(0, consts.DEFAUT_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0)
        )

        # Info text label (invisible by default, used to tell user that searched string was not found etc)
        self.infotext_label_var = tk.StringVar()
        self.infotext_label_var.set("")
        self.infotext_label = ttk.Label(
            self.main_frame, textvariable=self.infotext_label_var, foreground="red"
        )  # TODO - style to conf
        infotext_label_row = 1
        if replace:
            infotext_label_row = 2
        self.infotext_label.grid(column=0,columnspan=2, row=infotext_label_row,  pady=3, padx=(consts.DEFAUT_CONTRL_PAD_X, 0))
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=1, column=0, sticky="nsew")

        # Case checkbox
        self.case_var = tk.IntVar(value=CURERNT_FIND_OPTION.match_case)
        self.case_checkbutton = ttk.Checkbutton(
            bottom_frame, text=_("Case sensitive"), variable=self.case_var
        )
        self.case_checkbutton.grid(column=0, row=0, padx=(consts.DEFAUT_CONTRL_PAD_X, 0),sticky="w")
        
        self.whole_word_var = tk.IntVar(value=CURERNT_FIND_OPTION.match_whole_word)
        self.whole_word_checkbutton = ttk.Checkbutton(
            bottom_frame, text=_("Match whole word"), variable=self.whole_word_var
        )
        self.whole_word_checkbutton.grid(column=0, row=1, padx=(consts.DEFAUT_CONTRL_PAD_X, 0),sticky="w")
        
        self.regular_var = tk.IntVar(value=CURERNT_FIND_OPTION.regex)
        self.regular_checkbutton = ttk.Checkbutton(
            bottom_frame, text=_("Regular expression"), variable=self.regular_var
        )
        self.regular_checkbutton.grid(column=0, row=2, padx=(consts.DEFAUT_CONTRL_PAD_X, 0),sticky="w")
        
        self.wrap_var = tk.IntVar(value=CURERNT_FIND_OPTION.wrap)
        self.wrap_checkbutton = ttk.Checkbutton(
            bottom_frame, text=_("Wrap"), variable=self.wrap_var
        )
        self.wrap_checkbutton.grid(column=0, row=3, padx=(consts.DEFAUT_CONTRL_PAD_X, 0),sticky="w",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))

        group_frame = ttk.LabelFrame(
                bottom_frame, borderwidth=2, relief=tk.GROOVE, text=_("Direction"))
        group_frame.grid(column=1, row=0, rowspan=4,padx=(consts.DEFAUT_CONTRL_PAD_X, 0), \
                         pady=(0, consts.DEFAUT_CONTRL_PAD_Y),sticky="n")
        # Direction radiobuttons
        self.direction_var = tk.IntVar(value=CURERNT_FIND_OPTION.down)
        self.up_radiobutton = ttk.Radiobutton(
            group_frame, text=_("Up"), variable=self.direction_var, value=not CURERNT_FIND_OPTION.down
        )
        self.up_radiobutton.grid(column=1, row=3, pady=(0, consts.DEFAUT_CONTRL_PAD_Y))
        self.down_radiobutton = ttk.Radiobutton(
            group_frame, text=_("Down"), variable=self.direction_var, value=CURERNT_FIND_OPTION.down
        )
        self.down_radiobutton.grid(column=2, row=3, pady=(0, consts.DEFAUT_CONTRL_PAD_Y))
        self.down_radiobutton.invoke()

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=0, column=1,rowspan=2, sticky="nsew")
        # Find button - goes to the next occurrence
        self.find_button = ttk.Button(
            self.right_frame, text=_("Find Next"), command=self._perform_find, default="active"
        )
        self.find_button.grid(
            column=0, row=0, sticky=tk.W + tk.E, pady=(consts.DEFAUT_CONTRL_PAD_Y, 0), padx=(0, consts.DEFAUT_CONTRL_PAD_X)
        )
        self.find_button.config(state="disabled")
        if not replace:
            self.AddCancelButton()

        # create bindings
        self.bind("<Escape>", self._ok)
        self.find_entry_var.trace("w", self._update_button_statuses)
        self.find_entry.bind("<Return>", self._perform_find, True)
        self.bind("<F3>", self._perform_find, True)
        self.find_entry.bind("<KP_Enter>", self._perform_find, True)
        #根据查找文本是否为空更新查找按钮状态,如果是替换对话框,则在其初始化函数中更新
        #此处不更新
        if not replace:
            self._update_button_statuses()
            self.LoadConfig()

        self.focus_set()

    def AddCancelButton(self,row=1):
        cancel_button = ttk.Button(self.right_frame, text=_("Cancel"), command=self._ok)
        cancel_button.grid(
            column=0, row=row, sticky=tk.W + tk.E, pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y, 0), padx=(0, consts.DEFAUT_CONTRL_PAD_X)
        )

    def focus_set(self):
        self.find_entry.focus_set()
        self.find_entry.selection_range(0, tk.END)

    # callback for text modifications on the find entry object, used to dynamically enable and disable buttons
    def _update_button_statuses(self, *args):
        find_text = self.find_entry_var.get()
        if len(find_text) == 0:
            self.find_button.config(state="disabled")
        else:
            self.find_button.config(state="normal")

    # returns whether the next search is case sensitive based on the current value of the case sensitivity checkbox
    def _is_search_case_sensitive(self):
        return self.case_var.get() != 0

    # returns whether the current search is a repeat of the last searched based on all significant values
    def _repeats_last_search(self, tofind):
        return (
            tofind == FindDialog.last_searched_word
            and self.last_processed_indexes is not None
            and self.last_search_case == self._is_search_case_sensitive()
        )

    def GetFindTextOption(self):
        global CURERNT_FIND_OPTION
        findstr = self.find_entry_var.get()
        CURERNT_FIND_OPTION.findstr = findstr
        CURERNT_FIND_OPTION.match_case = self.case_var.get()
        CURERNT_FIND_OPTION.match_whole_word = self.whole_word_var.get()
        CURERNT_FIND_OPTION.regex = self.regular_var.get()
        CURERNT_FIND_OPTION.down = self.direction_var.get()
        CURERNT_FIND_OPTION.wrap = self.wrap_var.get()
        
    def GetCtrl(self) :
        current_view = GetApp().GetDocumentManager().GetCurrentView()
        if isinstance(current_view,texteditor.TextView) or isinstance(current_view,GetApp().GetDebugviewClass()):
            self.text = current_view.GetCtrl()
        return self.text
        
    def _perform_find(self, event=None):
        self.do_find()

    def do_find(self,ok=0):
        self.GetCtrl()
        if self.text is None:
            self.infotext_label_var.set("current view is not a text or debugger view")
            return
        self.GetFindTextOption()
        self.infotext_label_var.set("")  # reset the info label text
        tofind = self.find_entry.get()  # get the text to find
        if len(tofind) == 0:  # in the case of empty string, cancel
            return  # TODO - set warning text to info label?
        res = self.text.do_find(CURERNT_FIND_OPTION,ok=ok)
        if res:
            self.text.find_and_select(res)
            if CURERNT_FIND_OPTION.wrap:
                self.text.do_wrap_search(self.infotext_label_var)
            #单词查找到则添加到单词列表中去
            values = self.find_entry['values']
            if not values:
                values = []
             #需要将存储的tuple类型转换成list类型
            values = list(values)
            if tofind not in values:
                values.insert(0,tofind)
            self.find_entry['values'] = values
            #查找文本移动光标时同时更新状态栏显示的行列号
            current_view = GetApp().GetDocumentManager().GetCurrentView()
            if hasattr(current_view,"set_line_and_column"):
                current_view.set_line_and_column()
        else:
            self.infotext_label_var.set(_("The specified text was not found!"))
            self.text.bell()
            return False
        return True

    def _ok(self, event=None):
        """Called when the window is closed. responsible for handling all cleanup."""
        self.SaveConfig()
        self._remove_all_tags()
        self.destroy()

        global _active_find_dialog
        _active_find_dialog = None
        

    def SaveConfig(self):
        """ Save find/replace patterns and search flags to registry. """
        utils.profile_set(FIND_MATCHPATTERN, self.find_entry_var.get())
        utils.profile_set(FIND_MATCHCASE, self.case_var.get())
        utils.profile_set(FIND_MATCHWHOLEWORD, self.whole_word_var.get())
        utils.profile_set(FIND_MATCHREGEXPR, self.regular_var.get())
        utils.profile_set(FIND_MATCHWRAP, self.wrap_var.get())
        utils.profile_set(FIND_MATCHUPDOWN, self.direction_var.get())
        self.find_entry.save_match_patters()

    def LoadConfig(self):
        #如果未有指定字符串,从配置中加载上一次查找的字符串
        if not self.find_entry_var.get():
            self.find_entry_var.set(utils.profile_get(FIND_MATCHPATTERN,''))
        self.case_var.set(utils.profile_get_int(FIND_MATCHCASE,False))
        self.whole_word_var.set(utils.profile_get_int(FIND_MATCHWHOLEWORD,False))
        self.regular_var.set(utils.profile_get_int(FIND_MATCHREGEXPR,False))
        self.wrap_var.set(utils.profile_get_int(FIND_MATCHWRAP,True))
        self.direction_var.set(utils.profile_get_int(FIND_MATCHUPDOWN,True))
        self.find_entry.load_match_patters()


    # removes the active tag and all passive tags
    def _remove_all_tags(self):
        pass

    # finds and tags all occurences of the searched term
    def _find_and_tag_all(self, tofind, force=False):
        # TODO - to be improved so only whole words are matched - surrounded by whitespace, parentheses, brackets, colons, semicolons, points, plus, minus

        if (
            self._repeats_last_search(tofind) and not force
        ):  # nothing to do, all passive tags already set
            return

        currentpos = 1.0
        end = self.codeview.GetCtrl().index("end")

        # searches and tags until the end of codeview
        while True:
            currentpos = self.codeview.GetCtrl().search(
                tofind, currentpos, end, nocase=not self._is_search_case_sensitive()
            )
            if currentpos == "":
                break

            endpos = self.codeview.GetCtrl().index("%s+%dc" % (currentpos, len(tofind)))
            self.passive_found_tags.add((currentpos, endpos))
            self.codeview.GetCtrl().tag_add("found", currentpos, endpos)

            currentpos = self.codeview.GetCtrl().index("%s+1c" % currentpos)

class FindReplaceDialog(FindDialog):
    """ Find/Replace Dialog with regular expression matching and wrap to top/bottom of file. """

    def __init__(self, parent,  findString=None):
        FindDialog.__init__(self, parent,findString,replace=True)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)
        # Replace text label
        self.replace_label = ttk.Label(self.main_frame, text=_("Replace with:"))
        self.replace_label.grid(column=0, row=1, sticky="w", padx=(consts.DEFAUT_CONTRL_PAD_X, 0))

        # Replace text field
        self.replvar = tk.StringVar()
        self.replace_entry = ttk.Entry(self.main_frame,textvariable=self.replvar)
        self.replace_entry.grid(column=1, row=1,sticky="nsew", padx=(0, consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))

        # Replace button - replaces the current occurrence, if it exists
        self.replace_and_find_button = ttk.Button(
            self.right_frame, text=_("Replace"), command=self._perform_replace
        )
        self.replace_and_find_button.grid(column=0, row=1, sticky=tk.W + tk.E, padx=(0, consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y, 0))
        self.replace_and_find_button.config(state="disabled")

        # Replace all button - replaces all occurrences
        self.replace_all_button = ttk.Button(
            self.right_frame, text=_("Replace All"), command=self._perform_replace_all
        )  # TODO - text to resources
        self.replace_all_button.grid(
            column=0, row=2, sticky=tk.W + tk.E, padx=(0, consts.DEFAUT_CONTRL_PAD_X), pady=( consts.DEFAUT_HALF_CONTRL_PAD_Y,0)
        )
        if FindDialog.last_searched_word == None:
            self.replace_all_button.config(state="disabled")
        self.AddCancelButton(row=3)
        #根据查找文本是否为空更新查找以及替换按钮状态
        self._update_button_statuses()
        #替换字符串时需要设置ok标志为1
        self.ok = 1
        self.LoadConfig()
        
    def GetCtrl(self) :
        current_view = GetApp().GetDocumentManager().GetCurrentView()
        if isinstance(current_view,texteditor.TextView):
            self.text = current_view.GetCtrl()
        return self.text

    def SaveConfig(self):
        """ Save find/replace patterns and search flags to registry. """
        FindDialog.SaveConfig(self)
        utils.profile_set(FIND_MATCHREPLACE, self.replvar.get())
        
    def LoadConfig(self):
        FindDialog.LoadConfig(self)
        self.replvar.set(utils.profile_get(FIND_MATCHREPLACE,''))

    def _update_button_statuses(self, *args):
        #先更新查找按钮状态
        FindDialog._update_button_statuses(self,*args)
        find_text = self.find_entry_var.get()
        #再更新替换按钮状态
        if len(find_text) == 0:
            self.replace_and_find_button.config(state="disabled")
            self.replace_all_button.config(state="disabled")
        else:
            self.replace_all_button.config(state="normal")
            self.replace_and_find_button.config(state="normal")

    def _ok(self, event=None):
        """Called when the window is closed. responsible for handling all cleanup."""
        self.SaveConfig()
        self._remove_all_tags()
        self.destroy()
        #对话框关闭时销毁实例,下次重新启动一个新实例
        global _active_find_replace_dialog
        _active_find_replace_dialog = None

    # performs the replace operation - replaces the currently active found word with what is entered in the replace field
    def _perform_replace(self):
        if self.do_find(self.ok):
            if self.do_replace():   # Only find next match if replace succeeded.
                                    # A bad re can cause a it to fail.
                #替换之后再查找一次
                self.do_find(0)
        

    def do_find(self,ok=0):
        if FindDialog.do_find(self,ok):
            self.ok = 1
            return True
        else:
            return False

    def _replace_expand(self, m, repl):
        """ Helper function for expanding a regular expression
            in the replace field, if needed. """
        if CURERNT_FIND_OPTION.regex:
            try:
                new = m.expand(repl)
            except re.error:
                new = None
        else:
            new = repl
        return new
        
    def do_replace(self):
        text = self.text
        prog = text.getprog()
        if not prog:
            return False
        first,last = text.get_selection()
        pos = first
        line, col = text.get_line_col(pos)
        chars = text.get("%d.0" % line, "%d.0" % (line+1))
        m = prog.match(chars, col)
        if not prog:
            return False
        new = self._replace_expand(m, self.replvar.get())
        if new is None:
            return False
        text.mark_set("insert", first)
        if m.group():
            text.delete(first, last)
        if new:
            text.insert(first, new)
        self.ok = 0
        return True
        

    # replaces all occurences of the search string with the replace string
    def _perform_replace_all(self):
        repl = self.replvar.get()
        if not FindDialog.do_find(self):
            return
        text = self.text
        text.tag_remove("sel", "1.0", "end")
        text.tag_remove("hit", "1.0", "end")
        line = 1
        col = 1
        ok = 1
        first = last = None
        text.SetOption(CURERNT_FIND_OPTION)
        prog = text.getprog()
        while 1:
            res = text.search_forward(prog, line, col, 0, ok)
            if not res:
                break
            line, m = res
            chars = text.get("%d.0" % line, "%d.0" % (line+1))
            orig = m.group()
            new = self._replace_expand(m, repl)
            if new is None:
                break
            i, j = m.span()
            first = "%d.%d" % (line, i)
            last = "%d.%d" % (line, j)
            if new == orig:
                text.mark_set("insert", last)
            else:
                text.mark_set("insert", first)
                if first != last:
                    text.delete(first, last)
                if new:
                    text.insert(first, new)
            col = i + len(new)
            ok = 0

def ShowFindReplaceDialog(master,replace=False,findString=""):
    if replace:
        global _active_find_replace_dialog
        if _active_find_replace_dialog == None:
            _active_find_replace_dialog = FindReplaceDialog(master,findString)
    else:
        global _active_find_dialog
        if _active_find_dialog == None:
            _active_find_dialog = FindDialog(master,findString)
