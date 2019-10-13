# -*- coding: utf-8 -*-
from noval import GetApp,_
import tkinter as tk
from tkinter import messagebox
import noval.constants as constants
import noval.ttkwidgets.listboxframe as listboxframe
import noval.ui_utils as ui_utils
import noval.util.utils as utils

# TODO: adjust the window position in cases where it's too close to bottom or right edge - but make sure the current line is shown
"""Completions get computed on the backend, therefore getting the completions is
asynchronous.
"""

class Completer(listboxframe.ListboxFrame):
    def __init__(self, text):
        listboxframe.ListboxFrame.__init__(
            self,
            master=text,
            listbox_class=ui_utils.ThemedListbox,
            font="SmallEditorFont",
            activestyle="dotbox",
            exportselection=False,
        )
        #设置鼠标样式
        self.listbox.configure(cursor="arrow")
        self.vert_scrollbar.configure(cursor="arrow")

        self.text = text
        #单词列表
        self.completions = []
        #补全单词时,已经输入的单词长度,插入单词时不需要插入全部单词,而是只插入未补全的单词
        self._typedlen = 0

        self.doc_label = tk.Label(
            master=text, text="Aaappiiiii", bg="#ffffe0", justify="left", anchor="nw"
        )

        # Auto indenter will eat up returns, therefore I need to raise the priority
        # of this binding
        self.text_priority_bindtag = "completable" + str(self.text.winfo_id())
        self.text.bindtags((self.text_priority_bindtag,) + self.text.bindtags())
        self.text.bind_class(
            self.text_priority_bindtag, "<Key>", self._on_text_keypress, True
        )
        #单击文本框时,关闭智能提示
        self.text.bind("<1>", self.on_text_click)
        # for cases when Listbox gets focus
        #按Esc建关闭智能提示
        self.listbox.bind("<Escape>", self._close)
        #按回车键插入选中内容
        self.listbox.bind("<Return>", self._insert_current_selection)
        #双击listbox插入选中内容
        self.listbox.bind("<Double-Button-1>", self._insert_current_selection)

    def _present_completions(self, completions,replaceLen):
        self.completions = completions
        self._typedlen = replaceLen
        # present
        if len(completions) == 0:
            self._close()
        elif len(completions) == 1:
            self._insert_completion(completions[0])  # insert the only completion
            self._close()
        else:
            self._show_box(completions)

    def _show_box(self, completions):
        self.listbox.delete(0, self.listbox.size())
        self.listbox.insert(0, *completions)
        self.listbox.activate(0)
        self.listbox.selection_set(0)

        # place box
        if not self._is_visible():

            # _, _, _, list_box_height = self.bbox(0)
            height = 100  # min(150, list_box_height * len(completions) * 1.15)
            typed_name_length = 0
            text_box_x, text_box_y, _, text_box_height = self.text.bbox(
                "insert-%dc" % typed_name_length
            )

            # should the box appear below or above cursor?
            space_below = self.master.winfo_height() - text_box_y - text_box_height
            space_above = text_box_y

            if space_below >= height or space_below > space_above:
                height = min(height, space_below)
                y = text_box_y + text_box_height
            else:
                height = min(height, space_above)
                y = text_box_y - height

            width = 400
            self.place(x=text_box_x, y=y, width=width, height=height)

            self._update_doc()

    def _update_doc(self):
        return
        c = self._get_selected_completion()

        if c is None:
            self.doc_label["text"] = ""
            self.doc_label.place_forget()
        else:
            docstring = c.get("docstring", None)
            if docstring:
                self.doc_label["text"] = docstring
                self.doc_label.place(
                    x=self.winfo_x() + self.winfo_width(),
                    y=self.winfo_y(),
                    width=400,
                    height=self.winfo_height(),
                )
            else:
                self.doc_label["text"] = ""
                self.doc_label.place_forget()

    def _is_visible(self):
        return self.winfo_ismapped()

    def _insert_completion(self, completion):
        typed_prefix = self.text.get("insert-{}c".format(self._typedlen), "insert")
        if self._is_visible():
            self._close()

        if not completion.startswith(typed_prefix):
            # eg. case of the prefix was not correct
            self.text.delete("insert-{}c".format(self._typedlen), "insert")
            self.text.insert("insert", completion)
        else:
            self.text.insert("insert", completion[self._typedlen:])

    def _move_selection(self, delta):
        selected = self.listbox.curselection()
        if len(selected) == 0:
            index = 0
        else:
            index = selected[0]

        index += delta
        index = max(0, min(self.listbox.size() - 1, index))

        self.listbox.selection_clear(0, self.listbox.size() - 1)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)
        self._update_doc()

    def _get_position(self):
        return map(int, self.text.index("insert").split("."))

    def _on_text_keypress(self, event=None):
        if not self._is_visible():
            return None
        if event.keysym == "Escape":
            self._close()
            return "break"
        elif event.keysym in ["Up", "KP_Up"]:
            self._move_selection(-1)
            return "break"
        elif event.keysym in ["Down", "KP_Down"]:
            self._move_selection(1)
            return "break"
        elif event.keysym in ["Return", "KP_Enter", "Tab"]:
            assert self.listbox.size() > 0
            self._insert_current_selection()
            return "break"
        else:
            #根据输入内容匹配列表框关键字
            is_back_space = event.keysym == "BackSpace"
            if event.char in self.text.DEFAULT_WORD_CHARS or is_back_space:
                type_word = self.GetInputword()
                if event.char in self.text.DEFAULT_WORD_CHARS:
                    word = type_word + event.char
                else:
                    word = type_word[0:-1]
                sel = self.GetInputSelection(word)
                #如果退格非asc字符,比如空格,换行符等,则关闭提示
                if sel >=0 and (type_word or not is_back_space):
                    self._typedlen = len(word)
                    if len(self.listbox.curselection()) > 0:
                        self.listbox.selection_clear(0, self.listbox.size() - 1)
                    self.listbox.activate(sel)
                    self.listbox.selection_set(sel)
                    self.listbox.see(sel)
                else:
                    #未匹配到关键字则关闭提示
                    self._typedlen = 0
                    self._close()
        return None

    def GetInputword(self):
        line,col = self.text.GetCurrentPos()
        if line == 0 and col == 0:
            return ''
        if self.text.GetCharAt(line,col) == '.':
            col = col - 1
            hint = None
        else:
            hint = ''
            
        validLetters = self.text.DEFAULT_WORD_CHARS
        word = ''
        while (True):
            col = col - 1
            if col < 0:
                break
            char = self.text.GetCharAt(line,col)
            if char not in validLetters:
                break
            word = char + word
        return word

    def GetInputSelection(self,word):
        if word == "":
            return 0
        for i,completion in enumerate(self.completions):
            lower_text = completion.lower()
            if lower_text.startswith(word.lower()):
                return i
        return -1

    def _insert_current_selection(self, event=None):
        self._insert_completion(self._get_selected_completion())

    def _get_selected_completion(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return None
        return self.completions[sel[0]]

    def _close(self, event=None):
        self.place_forget()
        self.doc_label.place_forget()
        self.text.focus_set()

    def on_text_click(self, event=None):
        if self._is_visible():
            self._close()


class ShellCompleter(Completer):
    def _bind_result_event(self):
        # TODO: remove binding when editor gets closed
        get_workbench().bind(
            "shell_autocomplete_response", self._handle_backend_response, True
        )

    def handle_autocomplete_request(self):
        source = self._get_prefix()

        get_runner().send_command(InlineCommand("shell_autocomplete", source=source))

    def _handle_backend_response(self, msg):
        # check if the response is relevant for current state
        if msg.source != self._get_prefix():
            self._close()
        else:
            self._present_completions(msg.completions)

    def _get_prefix(self):
        return self.text.get("input_start", "insert")  # TODO: allow multiple line input

def patched_perform_midline_tab(text, event):
    '''
        实现tab键自动完成单词的功能
    '''
    if utils.profile_get_int("TextTabCompletion",True):
        if not text.has_selection():
            GetApp().MainFrame.GetNotebook().AutocompShow()
            return "break"
        else:
            return None

    return text.perform_smart_tab(event)
