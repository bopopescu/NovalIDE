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

#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------
FIND_MATCHPATTERN = "FindMatchPattern"
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

class FindOpt:
    def __init__(self,findstr,match_case=False,match_whole_word=False,wrap=True,down=True,regex=False):
        self.findstr = findstr
        self.match_case = match_case
        self.match_whole_word = match_whole_word
        self.wrap = wrap
        self.down = down
        self.regex = regex
        

class FindDirOption(FindOpt):
    def __init__(self,findstr,dir_,match_case=False,match_whole_word=False,regex=False,recursive=True,search_hidden=False,file_type_list=[]):
        FindOpt.__init__(self,findstr,match_case=match_case,match_whole_word=match_whole_word,regex=regex)
        self.dirstr = dir_
        self.recursive = recursive
        self.search_hidden = search_hidden
        self.file_types = file_type_list
        

CURERNT_FIND_OPTION = FindDirOption('','')
        
class FindDialog(tk.Toplevel):
    last_searched_word = None
    
    def __init__(self, master,findString="",replace=False):
        tk.Toplevel.__init__(self, master, takefocus=1, background="pink")
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.codeview = master.GetView()

        # references to the current set of passive found tags e.g. all words that match the searched term but are not the active string
        self.passive_found_tags = set()
        self.active_found_tag = (
            None
        )  # reference to the currently active (centered) found string

        # a tuple containing the start and indexes of the last processed string
        # if the last action was find, then the end index is start index + 1
        # if the last action was replace, then the indexes correspond to the start
        # and end of the inserted word
        self.last_processed_indexes = None
        self.last_search_case = (
            None
        )  # case sensitivity value used during the last search

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
        self.find_entry_var = tk.StringVar(value=findString)
        self.find_entry = ttk.Combobox(self.main_frame, textvariable=self.find_entry_var)
        self.find_entry.grid(
            column=1, row=0, padx=(0, consts.DEFAUT_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0)
        )
        if FindDialog.last_searched_word is not None:
            self.find_entry.insert(0, FindDialog.last_searched_word)

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

        self.focus_set()

    def AddCancelButton(self,row=1):
        cancel_button = ttk.Button(self.right_frame, text=_("Cancel"), command=self._ok)
        cancel_button.grid(
            column=0, row=row, sticky=tk.W + tk.E, pady=(consts.DEFAUT_CONTRL_PAD_Y/2, 0), padx=(0, consts.DEFAUT_CONTRL_PAD_X)
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
        findstr = self.find_entry_var.get().strip()
        CURERNT_FIND_OPTION.findstr = findstr
        CURERNT_FIND_OPTION.match_case = self.case_var.get()
        CURERNT_FIND_OPTION.match_whole_word = self.whole_word_var.get()
        CURERNT_FIND_OPTION.regex = self.regular_var.get()
        CURERNT_FIND_OPTION.down = self.direction_var.get()
        CURERNT_FIND_OPTION.wrap = self.wrap_var.get()

    def _perform_find(self, event=None):
        self.GetFindTextOption()
        self.infotext_label_var.set("")  # reset the info label text
        tofind = self.find_entry.get()  # get the text to find
        if len(tofind) == 0:  # in the case of empty string, cancel
            return  # TODO - set warning text to info label?

        search_backwards = (
            self.direction_var.get() == 1
        )  # True - search backwards ('up'), False - forwards ('down')

        if self._repeats_last_search(
            tofind
        ):  # continuing previous search, find the next occurrence
            if search_backwards:
                search_start_index = self.last_processed_indexes[0]
            else:
                search_start_index = self.last_processed_indexes[1]

            if self.active_found_tag is not None:
                self.codeview.GetCtrl().tag_remove(
                    "current_found", self.active_found_tag[0], self.active_found_tag[1]
                )  # remove the active tag from the previously found string
                self.passive_found_tags.add(
                    (self.active_found_tag[0], self.active_found_tag[1])
                )  # ..and set it to passive instead
                self.codeview.GetCtrl().tag_add(
                    "found", self.active_found_tag[0], self.active_found_tag[1]
                )

        else:  # start a new search, start from the current insert line position
            if self.active_found_tag is not None:
                self.codeview.GetCtrl().tag_remove(
                    "current_found", self.active_found_tag[0], self.active_found_tag[1]
                )  # remove the previous active tag if it was present
            for tag in self.passive_found_tags:
                self.codeview.text.tag_remove(
                    "found", tag[0], tag[1]
                )  # and remove all the previous passive tags that were present
            search_start_index = self.codeview.GetCtrl().index(
                "insert"
            )  # start searching from the current insert position
            self._find_and_tag_all(
                tofind
            )  # set the passive tag to ALL found occurences
            FindDialog.last_searched_word = tofind  # set the data about last search
            self.last_search_case = self._is_search_case_sensitive()

        wordstart = self.codeview.GetCtrl().search(
            tofind,
            search_start_index,
            backwards=search_backwards,
            forwards=not search_backwards,
            nocase=not self._is_search_case_sensitive(),
        )  # performs the search and sets the start index of the found string
        if len(wordstart) == 0:
            self.infotext_label_var.set(
                "The specified text was not found!"
            )  # TODO - better text, also move it to the texts resources list
         #   self.replace_and_find_button.config(state="disabled")
          #  self.replace_button.config(state="disabled")
            return

        self.last_processed_indexes = (
            wordstart,
            self.codeview.GetCtrl().index("%s+1c" % wordstart),
        )  # sets the data about last search
        self.codeview.GetCtrl().see(wordstart)  # moves the view to the found index
        wordend = self.codeview.GetCtrl().index(
            "%s+%dc" % (wordstart, len(tofind))
        )  # calculates the end index of the found string
        self.codeview.GetCtrl().tag_add(
            "current_found", wordstart, wordend
        )  # tags the found word as active
        self.active_found_tag = (wordstart, wordend)
      #  self.replace_and_find_button.config(state="normal")
       # self.replace_button.config(state="normal")

    def _ok(self, event=None):
        """Called when the window is closed. responsible for handling all cleanup."""
        self._remove_all_tags()
        self.destroy()

        global _active_find_dialog
        _active_find_dialog = None

    # removes the active tag and all passive tags
    def _remove_all_tags(self):
        for tag in self.passive_found_tags:
            self.codeview.GetCtrl().tag_remove(
                "found", tag[0], tag[1]
            )  # removes the passive tags

        if self.active_found_tag is not None:
            self.codeview.GetCtrl().tag_remove(
                "current_found", self.active_found_tag[0], self.active_found_tag[1]
            )  # removes the currently active tag

        self.active_found_tag = None

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
        self.replace_entry = ttk.Entry(self.main_frame)
        self.replace_entry.grid(column=1, row=1,sticky="nsew", padx=(0, consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))

        # Replace button - replaces the current occurrence, if it exists
        self.replace_and_find_button = ttk.Button(
            self.right_frame, text=_("Replace"), command=self._perform_replace_and_find
        )
        self.replace_and_find_button.grid(column=0, row=1, sticky=tk.W + tk.E, padx=(0, consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y/2, 0))
        self.replace_and_find_button.config(state="disabled")

        # Replace all button - replaces all occurrences
        self.replace_all_button = ttk.Button(
            self.right_frame, text=_("Replace All"), command=self._perform_replace_all
        )  # TODO - text to resources
        self.replace_all_button.grid(
            column=0, row=2, sticky=tk.W + tk.E, padx=(0, consts.DEFAUT_CONTRL_PAD_X), pady=( consts.DEFAUT_CONTRL_PAD_Y/2,0)
        )
        if FindDialog.last_searched_word == None:
            self.replace_all_button.config(state="disabled")
        self.AddCancelButton(row=3)
        #根据查找文本是否为空更新查找以及替换按钮状态
        self._update_button_statuses()

    def SaveConfig(self):
        """ Save find/replace patterns and search flags to registry. """
        findService = wx.GetApp().GetService(FindService)
        if findService:
            findService.SaveFindConfig(self._findCtrl.GetValue(),
                                       self._wholeWordCtrl.IsChecked(),
                                       self._matchCaseCtrl.IsChecked(),
                                       self._regExprCtrl.IsChecked(),
                                       self._wrapCtrl.IsChecked(),
                                       self._radioBox.GetSelection(),
                                       self._replaceCtrl.GetValue()
                                       )
                                       

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
        self._remove_all_tags()
        self.destroy()
        #对话框关闭时销毁实例,下次重新启动一个新实例
        global _active_find_replace_dialog
        _active_find_replace_dialog = None

    # performs the replace operation - replaces the currently active found word with what is entered in the replace field
    def _perform_replace(self):

        # nothing is currently in found status
        if self.active_found_tag == None:
            return

        # get the found word bounds
        del_start = self.active_found_tag[0]
        del_end = self.active_found_tag[1]

        # erase all tags - these would not be correct anyway after new word is inserted
        self._remove_all_tags()
        toreplace = self.replace_entry.get()  # get the text to replace

        # delete the found word
        self.codeview.text.delete(del_start, del_end)
        # insert the new word
        self.codeview.text.insert(del_start, toreplace)
        # mark the inserted word boundaries
        self.last_processed_indexes = (
            del_start,
            self.codeview.text.index("%s+%dc" % (del_start, len(toreplace))),
        )

        get_workbench().event_generate(
            "Replace",
            widget=self.codeview.text,
            old_text=self.codeview.text.get(del_start, del_end),
            new_text=toreplace,
        )

    # performs the replace operation followed by a new find
    def _perform_replace_and_find(self):
        if self.active_found_tag == None:
            return
        self._perform_replace()
        self._perform_find()

    # replaces all occurences of the search string with the replace string
    def _perform_replace_all(self):

        tofind = self.find_entry.get()
        if len(tofind) == 0:
            self.infotext_label_var.set("Enter string to be replaced.")
            return

        toreplace = self.replace_entry.get()

        self._remove_all_tags()

        currentpos = 1.0
        end = self.codeview.text.index("end")

        while True:
            currentpos = self.codeview.text.search(
                tofind, currentpos, end, nocase=not self._is_search_case_sensitive()
            )
            if currentpos == "":
                break

            endpos = self.codeview.text.index("%s+%dc" % (currentpos, len(tofind)))

            self.codeview.text.delete(currentpos, endpos)

            if toreplace != "":
                self.codeview.text.insert(currentpos, toreplace)

            currentpos = self.codeview.text.index(
                "%s+%dc" % (currentpos, len(toreplace))
            )

        get_workbench().event_generate(
            "ReplaceAll", widget=self.codeview.text, old_text=tofind, new_text=toreplace
        )



def ShowFindReplaceDialog(master,findString="",replace=False):
    if replace:
        global _active_find_replace_dialog
        if _active_find_replace_dialog == None:
            _active_find_replace_dialog = FindReplaceDialog(master,findString)
    else:
        global _active_find_dialog
        if _active_find_dialog == None:
            _active_find_dialog = FindDialog(master)
