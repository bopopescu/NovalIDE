from noval import GetApp,_
import tkinter as tk
from tkinter import messagebox
import noval.iface as iface
import noval.plugin as plugin
import noval.editor.code as codeeditor
import noval.constants as constants
import noval.ttkwidgets.listboxframe as listboxframe
import noval.ui_utils as ut_utils

# TODO: adjust the window position in cases where it's too close to bottom or right edge - but make sure the current line is shown
"""Completions get computed on the backend, therefore getting the completions is
asynchronous.
"""
#self.listview = listboxframe.ListboxFrame(self,listbox_class=ut_utils.ThemedListbox)

class Completer(listboxframe.ListboxFrame):
    def __init__(self, text):
        listboxframe.ListboxFrame.__init__(
            self,
            master=text,
            listbox_class=ut_utils.ThemedListbox,
            font="SmallEditorFont",
            activestyle="dotbox",
            exportselection=False,
        )
        self.listbox.focus_set()
        self.listbox.configure(cursor="arrow")

        self.text = text
        self.completions = []

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

        self.text.bind(
            "<<TextChange>>", self._on_text_change, True
        )  # Assuming TweakableText

        # for cases when Listbox gets focus
        self.bind("<Escape>", self._close)
        self.bind("<Return>", self._insert_current_selection)
        self.bind("<Double-Button-1>", self._insert_current_selection)
      #  self._bind_result_event()

    def _bind_result_event(self):
        # TODO: remove binding when editor gets closed
        get_workbench().bind(
            "editor_autocomplete_response", self._handle_backend_response, True
        )

    def handle_autocomplete_request(self):
        row, column = self._get_position()
        source = self.text.get("1.0", "end-1c")
        get_runner().send_command(
            InlineCommand(
                "editor_autocomplete",
                source=source,
                row=row,
                column=column,
                filename=self._get_filename(),
            )
        )

    def _handle_backend_response(self, msg):
        row, column = self._get_position()
        source = self.text.get("1.0", "end-1c")

        if msg.source != source or msg.row != row or msg.column != column:
            # situation has changed, information is obsolete
            self._close()
        elif msg.error:
            self._close()
            messagebox.showerror("Autocomplete error", msg.error, parent=get_workbench())
        else:
            self._present_completions(msg.completions)

    def _present_completions(self, completions):
        self.completions = completions
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
        typed_len = len(completion["name"]) - len(completion["complete"].strip("="))
        typed_prefix = self.text.get("insert-{}c".format(typed_len), "insert")
        get_workbench().event_generate(
            "AutocompleteInsertion",
            text_widget=self.text,
            typed_prefix=typed_prefix,
            completed_name=completion["name"],
        )

        if self._is_visible():
            self._close()

        if not completion["name"].startswith(typed_prefix):
            # eg. case of the prefix was not correct
            self.text.delete("insert-{}c".format(typed_len), "insert")
            self.text.insert("insert", completion["name"])
        else:
            self.text.insert("insert", completion["complete"])

    def _get_filename(self):
        # TODO: allow completing in shell
        if not isinstance(self.text, CodeViewText):
            return None

        codeview = self.text.master

        editor = get_workbench().get_editor_notebook().get_current_editor()
        if editor.get_code_view() is codeview:
            return editor.get_filename()
        else:
            return None

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

    def _get_request_id(self):
        return "autocomplete_" + str(self.text.winfo_id())

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
            assert self.size() > 0
            self._insert_current_selection()
            return "break"

        return None

    def _insert_current_selection(self, event=None):
        self._insert_completion(self._get_selected_completion())

    def _get_selected_completion(self):
        sel = self.curselection()
        if len(sel) != 1:
            return None

        return self.completions[sel[0]]

    def _on_text_change(self, event=None):
        if self._is_visible():
            self.handle_autocomplete_request()

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


def handle_autocomplete_request(event=None):
    if event is None:
        text = GetApp().focus_get()
    else:
        text = event.widget

    _handle_autocomplete_request_for_text(text)


def _handle_autocomplete_request_for_text(text):
    if not hasattr(text, "autocompleter"):
        if isinstance(text, codeeditor.CodeCtrl):
            text.autocompleter = Completer(text)
            #单击文本框时,关闭智能提示
            text.bind("<1>", text.autocompleter.on_text_click)
        else:
            return

    current_view = GetApp().GetDocumentManager().GetCurrentView()
    completions = current_view.GetAutoCompleteDefaultKeywords()
    print (completions)
    text.autocompleter._present_completions(completions)
    #text.autocompleter.handle_autocomplete_request()


def patched_perform_midline_tab(text, event):
    if isinstance(text, ShellText):
        option_name = "edit.tab_complete_in_shell"
    else:
        option_name = "edit.tab_complete_in_editor"

    if get_workbench().get_option(option_name):
        if not text.has_selection():
            _handle_autocomplete_request_for_text(text)
            return "break"
        else:
            return None

    return text.perform_smart_tab(event)


def load_plugin() -> None:

    get_workbench().add_command(
        "autocomplete",
        "edit",
        "Auto-complete",
        handle_autocomplete_request,
        default_sequence="<Control-space>"
        # TODO: tester
    )

    get_workbench().set_default("edit.tab_complete_in_editor", True)
    get_workbench().set_default("edit.tab_complete_in_shell", True)

    CodeViewText.perform_midline_tab = patched_perform_midline_tab  # type: ignore
    ShellText.perform_midline_tab = patched_perform_midline_tab  # type: ignore


class Autocomplete(plugin.Plugin):
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        # Add Menu
        menuBar = GetApp().Menubar
        edit_menu = menuBar.GetEditMenu()
        edit_menu.Append(constants.ID_WORD_LIST,_("Completion Word List"), ("List All Completion Word of suggestions"),handler=handle_autocomplete_request)
