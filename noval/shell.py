# -*- coding: utf-8 -*-
from noval import GetApp,_,NewId
import os
import tkinter as tk
from tkinter import ttk
from noval.editor.code import CodeCtrl
from noval.editor.text import TextCtrl,index2line
import noval.util.strutils as strutils
import noval.util.utils as utils
import noval.python.pyutils as pyutils
import noval.syntax.syntax as syntax
from noval.util import hiscache
import re
from noval.util.command import *
import noval.menu as tkmenu
import noval.constants as constants
import tkinter.simpledialog as tkSimpleDialog
# NB! Don't add parens without refactoring split procedure!
OUTPUT_SPLIT_REGEX = re.compile(r"(\x1B\[[0-?]*[ -/]*[@-~]|[\a\b\r])")
SIMPLE_URL_SPLIT_REGEX = re.compile(
    r"(https?:\/\/[\w\/.:\-\?#=%]+[\w\/]|data:image\/[a-z]+;base64,[A-Za-z0-9\/=]+)"
)

class BaseShellText(CodeCtrl):
    """Passive version of ShellText. Used also for preview"""

    def __init__(self, main, view=None, cnf={}, **kw):
        self.view = view
        #use_edit_image为true表示右键编辑菜单使用默认图标
        CodeCtrl.__init__(self,main, cnf, use_edit_image=True,**kw)
        self._command_history = hiscache.HistoryCache(100)  # actually not really history, because each command occurs only once
        self._command_history_current_index = None
        self.disable_paren = True

        # logs of IO events for current toplevel block
        # (enables undoing and redoing the events)
        self._applied_io_events = []
        self._queued_io_events = []
        self._images = set()

        self._ansi_foreground = None
        self._ansi_background = None
        self._ansi_inverse = False
        self._ansi_intensity = None
        self._ansi_italic = False
        self._ansi_underline = False
        self._ansi_conceal = False
        self._ansi_strikethrough = False
        self._io_cursor_offset = 0
        self._squeeze_buttons = set()

        self.update_tty_mode()

        self.bind("<Up>", self._arrow_up, True)
        self.bind("<Down>", self._arrow_down, True)
        self.bind("<KeyPress>", self._text_key_press, True)
        self.bind("<KeyRelease>", self._text_key_release, True)

        prompt_font = tk.font.nametofont("BoldEditorFont")
        x_padding = 4
        io_vert_spacing = 10
        io_indent = 16 + x_padding
        code_indent = prompt_font.measure(">>> ") + x_padding

        self.tag_configure("command", lmargin1=code_indent, lmargin2=code_indent)
        self.tag_configure(
            "io", lmargin1=io_indent, lmargin2=io_indent, rmargin=io_indent, font="IOFont"
        )
        self.update_margin_color()

        self.tag_configure("after_io_or_value", spacing1=io_vert_spacing)
        self.tag_configure("before_io", spacing3=io_vert_spacing)

        self.tag_configure("prompt", lmargin1=x_padding, lmargin2=x_padding)
        self.tag_configure("value", lmargin1=x_padding, lmargin2=x_padding)
        self.tag_configure("restart_line", wrap="none", lmargin1=x_padding, lmargin2=x_padding)

        self.tag_configure("welcome", lmargin1=x_padding, lmargin2=x_padding)

        # Underline on the font looks better than underline on the tag,
        # therefore Shell doesn't use configured "hyperlink" style directly
        hyperlink_opts = syntax.SyntaxThemeManager().get_syntax_options_for_tag("hyperlink").copy()
        if hyperlink_opts.get("underline"):
            hyperlink_opts["font"] = "UnderlineIOFont"
            del hyperlink_opts["underline"]
        self.tag_configure("io_hyperlink", **hyperlink_opts)

        # create 3 marks: input_start shows the place where user entered but not-yet-submitted
        # input starts, output_end shows the end of last output,
        # output_insert shows where next incoming program output should be inserted
        self.mark_set("input_start", "end-1c")
        self.mark_gravity("input_start", tk.LEFT)

        self.mark_set("output_end", "end-1c")
        self.mark_gravity("output_end", tk.LEFT)

        self.mark_set("output_insert", "end-1c")
        self.mark_gravity("output_insert", tk.RIGHT)

        self.active_object_tags = set()

        self.tag_raise("io_hyperlink")
        self.tag_raise("underline")
        self.tag_raise("strikethrough")
        self.tag_raise("intense_io")
        self.tag_raise("italic_io")
        self.tag_raise("intense_italic_io")
        self.tag_raise("sel")
        self.stop_png = GetApp().GetImage("process-stop.png")

    def submit_command(self, cmd_line, tags):
        # assert get_runner().is_waiting_toplevel_command()
        self.delete("input_start", "end")
        self.insert("input_start", cmd_line, tags)
        self.see("end")
        self.mark_set("insert", "end")
        self._try_submit_input()

    def _handle_input_request(self, msg):
        self._ensure_visible()
        self.focus_set()
        self.mark_set("insert", "end")
        self.tag_remove("sel", "1.0", tk.END)
        #self._try_submit_input()  # try to use leftovers from previous request
        submittable_text = self.get_input_text()
        #输入不能用空字符串,如果为空用换行符代替
        if submittable_text == "":
            submittable_text = "\n"
        self._submit_input(submittable_text)
        self.see("end")

    def get_input_text(self):
        text = tkSimpleDialog.askstring(
            _("Enter input"),
            _("Enter the input text:")
        )
        return text

    def _handle_program_output(self, msg):
        # Discard but not too often, as toplevel response will discard anyway
        if int(float(self.index("end"))) > utils.profile_get_int("shell.max_lines",1000) + 100:
            self._discard_old_content()

        self._ensure_visible()
        self._append_to_io_queue(msg.data, msg.stream_name)

        if not self._applied_io_events:
            # this is first line of io, add padding below command line
            self.tag_add("before_io", "output_insert -1 line linestart")

        self._update_visible_io(None)

    def _handle_toplevel_response(self, msg):
        if msg.get("error"):
            self._insert_text_directly(msg["error"] + "\n", ("toplevel", "stderr"))
            self._ensure_visible()

        if "user_exception" in msg:
            self._show_user_exception(msg["user_exception"])
            self._ensure_visible()

        welcome_text = msg.get("welcome_text")
        if welcome_text and welcome_text:
            preceding = self.get("output_insert -1 c", "output_insert")
            if preceding.strip() and not preceding.endswith("\n"):
                self._insert_text_directly("\n")
            #输出欢迎信息时,重置文本以免被文本语法渲染
            if hasattr(self,"syntax_colorer"):
                self.syntax_colorer.reset = True
            self._insert_text_directly(welcome_text, ("comment",))

        if "value_info" in msg:
            num_stripped_question_marks = getattr(msg, "num_stripped_question_marks", 0)
            if num_stripped_question_marks > 0:
                # show the value in object inspector
                get_workbench().event_generate("ObjectSelect", object_id=msg["value_info"].id)
            else:
                # show the value in shell
                value_repr = strutils.shorten_repr(msg["value_info"].repr, 10000)
                if value_repr != "None":
                #    if get_workbench().in_heap_mode():
                 #       value_repr = memory.format_object_id(msg["value_info"].id)
                    object_tag = "object_" + str(msg["value_info"].id)
                    self._insert_text_directly(value_repr + "\n", ("toplevel", "value", object_tag))
                    sequence = "<Control-Button-1>"
                    self.tag_bind(
                        object_tag,
                        sequence,
                        lambda _: get_workbench().event_generate(
                            "ObjectSelect", object_id=msg["value_info"].id
                        ),
                    )

                    self.active_object_tags.add(object_tag)

        self.mark_set("output_end", self.index("end-1c"))
   #     self._discard_old_content()
        self._update_visible_io(None)
        self._reset_ansi_attributes()
        self._io_cursor_offset = 0
        self._insert_prompt()
#        self._try_submit_input()  # Trying to submit leftover code (eg. second magic command)
        self.see("end")

        # import os
        # import psutil
        # process = psutil.Process(os.getpid())
        # print("MEM", process.memory_info().rss // (1024*1024))

    def _handle_fancy_debugger_progress(self, msg):
        if msg.in_present or msg.io_symbol_count is None:
            self._update_visible_io(None)
        else:
            self._update_visible_io(msg.io_symbol_count)

    def _get_squeeze_threshold(self):
        return utils.profile_get_int("shell.squeeze_threshold",1000)

    def _append_to_io_queue(self, data, stream_name):
        if self.tty_mode:
            # Make sure ANSI CSI codes are stored as separate events
            # TODO: try to complete previously submitted incomplete code
            parts = re.split(OUTPUT_SPLIT_REGEX, data)
            for part in parts:
                if part:  # split may produce empty string in the beginning or start
                    # split the data so that very long lines separated
                    for block in re.split("(.{%d,})" % (self._get_squeeze_threshold() + 1), part):
                        if block:
                            self._queued_io_events.append((block, stream_name))
        else:
            self._queued_io_events.append((data, stream_name))

    def _update_visible_io(self, target_num_visible_chars):
        current_num_visible_chars = sum(map(lambda x: 0 if x[0] is None else len(x[0]), self._applied_io_events))

        if (
            target_num_visible_chars is not None
            and target_num_visible_chars < current_num_visible_chars
        ):
            # hard to undo complex renderings (squeezed texts and ANSI codes)
            # easier to clean everything and start again
            self._queued_io_events = self._applied_io_events + self._queued_io_events
            self._applied_io_events = []
            self.direct_delete("command_io_start", "output_end")
            current_num_visible_chars = 0
            self._reset_ansi_attributes()

        while self._queued_io_events and current_num_visible_chars != target_num_visible_chars:
            data, stream_name = self._queued_io_events.pop(0)

            if target_num_visible_chars is not None:
                leftover_count = current_num_visible_chars + len(data) - target_num_visible_chars

                if leftover_count > 0:
                    # add suffix to the queue
                    self._queued_io_events.insert(0, (data[-leftover_count:], stream_name))
                    data = data[:-leftover_count]

            self._apply_io_event(data, stream_name)
            current_num_visible_chars += len(data)

        self.mark_set("output_end", self.index("end-1c"))
        self.see("end")

    def _apply_io_event(self, data, stream_name, extra_tags=set()):
        if not data:
            return

        original_data = data

        if self.tty_mode and re.match(OUTPUT_SPLIT_REGEX, data):
            if data == "\a":
                get_workbench().bell()
            elif data == "\b":
                self._change_io_cursor_offset(-1)
            elif data == "\r":
                self._change_io_cursor_offset("line")
            elif data.endswith("D") or data.endswith("C"):
                self._change_io_cursor_offset_csi(data)
            elif stream_name == "stdout":
                # According to https://github.com/tartley/colorama/blob/master/demos/demo04.py
                # codes sent to stderr shouldn't affect later output in stdout
                # It makes sense, but Ubuntu terminal does not confirm it.
                # For now I'm just trimming stderr color codes
                self._update_ansi_attributes(data)

        else:
            tags = extra_tags | {"io", stream_name}
            if stream_name == "stdout" and self.tty_mode:
                tags |= self._get_ansi_tags()

            if len(data) > self._get_squeeze_threshold() and "\n" not in data:
                self._io_cursor_offset = 0  # ignore the effect of preceding \r and \b
                button_text = data[:40] + " …"
                btn = tk.Label(
                    self,
                    text=button_text,
                    # width=len(button_text),
                    cursor="arrow",
                    borderwidth=2,
                    relief="raised",
                    font="IOFont",
                )
                btn.bind("<1>", lambda e: self._show_squeezed_text(btn), True)
                btn.contained_text = data
                btn.tags = tags
                self._squeeze_buttons.add(btn)
                create_tooltip(btn, "%d characters squeezed. " % len(data) + "Click for details.")

                # TODO: refactor
                # (currently copied from insert_text_directly)
                self.mark_gravity("input_start", tk.RIGHT)
                self.mark_gravity("output_insert", tk.RIGHT)

                self.window_create("output_insert", window=btn)
                for tag_name in tags:
                    self.tag_add(tag_name, "output_insert -1 chars")
                data = ""

            elif self._io_cursor_offset < 0:
                overwrite_len = min(len(data), -self._io_cursor_offset)

                if 0 <= data.find("\n") < overwrite_len:
                    overwrite_len = data.find("\n")

                overwrite_data = data[:overwrite_len]
                self.direct_insert(
                    "output_insert -%d chars" % -self._io_cursor_offset, overwrite_data, tuple(tags)
                )
                del_start = self.index("output_insert -%d chars" % -self._io_cursor_offset)
                del_end = self.index(
                    "output_insert -%d chars" % (-self._io_cursor_offset - overwrite_len)
                )
                self.direct_delete(del_start, del_end)

                # compute leftover data to be printed normally
                data = data[overwrite_len:]

                if "\n" in data:
                    # cursor offset doesn't apply on new line
                    self._io_cursor_offset = 0
                else:
                    # offset becomes closer to 0
                    self._io_cursor_offset + overwrite_len

            elif self._io_cursor_offset > 0:
                # insert spaces before actual data
                # NB! Print without formatting tags
                self._insert_text_directly(" " * self._io_cursor_offset, ("io", stream_name))
                self._io_cursor_offset = 0

            if data:
                # if any data is still left, then this should be output normally
                self._insert_text_directly(data, tuple(tags))

        self._applied_io_events.append((original_data, stream_name))

    def _show_squeezed_text(self, button):
        dlg = SqueezedTextDialog(self, button)
        show_dialog(dlg)

    def _change_io_cursor_offset_csi(self, marker):
        ints = re.findall(INT_REGEX, marker)
        if len(ints) != 1:
            logging.warn("bad CSI cursor positioning: %s", marker)
            # do nothing
            return

        try:
            delta = int(ints[0])
        except ValueError:
            logging.warn("bad CSI cursor positioning: %s", marker)
            return

        if marker.endswith("D"):
            delta = -delta

        self._change_io_cursor_offset(delta)

    def _change_io_cursor_offset(self, delta):
        line = self.get("output_insert linestart", "output_insert")
        if delta == "line":
            self._io_cursor_offset = -len(line)
        else:
            self._io_cursor_offset += delta
            if self._io_cursor_offset < -len(line):
                # cap
                self._io_cursor_offset = -len(line)

    def _reset_ansi_attributes(self):
        self._ansi_foreground = None
        self._ansi_background = None
        self._ansi_inverse = False
        self._ansi_intensity = None
        self._ansi_italic = False
        self._ansi_underline = False
        self._ansi_conceal = False
        self._ansi_strikethrough = False

    def _update_ansi_attributes(self, marker):
        if not marker.endswith("m"):
            # ignore
            return

        codes = re.findall(INT_REGEX, marker)
        if not codes:
            self._reset_ansi_attributes()

        while codes:
            code = codes.pop(0)

            if code == "0":
                self._reset_ansi_attributes()
            elif code in ["1", "2"]:
                self._ansi_intensity = code
            elif code == "3":
                self._ansi_italic = True
            elif code == "4":
                self._ansi_underline = True
            elif code == "7":
                self._ansi_inverse = True
            elif code == "8":
                self._ansi_conceal = True
            elif code == "9":
                self._ansi_strikethrough = True
            elif code == "22":
                self._ansi_intensity = None
            elif code == "23":
                self._ansi_italic = False
            elif code == "24":
                self._ansi_underline = False
            elif code == "27":
                self._ansi_inverse = False
            elif code == "28":
                self._ansi_conceal = False
            elif code == "29":
                self._ansi_strikethrough = False
            if code in [
                "30",
                "31",
                "32",
                "33",
                "34",
                "35",
                "36",
                "37",
                "90",
                "91",
                "92",
                "93",
                "94",
                "95",
                "96",
                "97",
            ]:
                self._ansi_foreground = code
            elif code == "39":
                self._ansi_foreground = None
            elif code in [
                "40",
                "41",
                "42",
                "43",
                "44",
                "45",
                "46",
                "47",
                "100",
                "101",
                "102",
                "103",
                "104",
                "105",
                "106",
                "107",
            ]:
                self._ansi_background = code
            elif code == "49":
                self._ansi_background = None
            elif code in ["38", "48"]:
                # multipart code, ignore for now,
                # but make sure all arguments are ignored
                if not codes:
                    # nothing follows, ie. invalid code
                    break
                mode = codes.pop(0)
                if mode == "5":
                    # 256-color code, just ignore for now
                    if not codes:
                        break
                    codes = codes[1:]
                elif mode == "2":
                    # 24-bit code, ignore
                    if len(codes) < 3:
                        # invalid code
                        break
                    codes = codes[3:]
            else:
                # ignore other codes
                pass

    def _get_ansi_tags(self):
        result = set()

        if self._ansi_foreground:
            fg = ANSI_COLOR_NAMES[self._ansi_foreground[-1]]
            if self._ansi_intensity == "1" or self._ansi_foreground[0] == "9":
                fg = "bright_" + fg
            elif self._ansi_intensity == "2":
                fg = "dim_" + fg
        else:
            fg = "fore"
            if self._ansi_intensity == "1":
                fg = "bright_" + fg
            elif self._ansi_intensity == "2":
                fg = "dim_" + fg

        if self._ansi_background:
            bg = ANSI_COLOR_NAMES[self._ansi_background[-1]]
            if self._ansi_background.startswith("10"):
                bg = "bright_" + bg
        else:
            bg = "back"

        if self._ansi_inverse:
            result.add(fg + "_bg")
            result.add(bg + "_fg")
        else:
            if fg != "fore":
                result.add(fg + "_fg")
            if bg != "back":
                result.add(bg + "_bg")

        if self._ansi_intensity == "1" and self._ansi_italic:
            result.add("intense_italic_io")
        elif self._ansi_intensity == "1":
            result.add("intense_io")
        elif self._ansi_italic:
            result.add("italic_io")

        if self._ansi_underline:
            result.add("underline")

        if self._ansi_strikethrough:
            result.add("strikethrough")

        return result

    def _insert_prompt(self):
        # if previous output didn't put a newline, then do it now
        if not self.index("output_insert").endswith(".0"):
            self._insert_text_directly("\n", ("io",))

        prompt_tags = ("toplevel", "prompt")

        # if previous line has value or io then add little space
        prev_line = self.index("output_insert - 1 lines")
        prev_line_tags = self.tag_names(prev_line)
        if "io" in prev_line_tags or "value" in prev_line_tags:
            prompt_tags += ("after_io_or_value",)

        self._insert_text_directly(">>> ", prompt_tags)
        self.edit_reset()
        
    def show_view(self):
        pass

    def _ensure_visible(self):
        if self.winfo_ismapped():
            return

        focused_view = GetApp().focus_get()
        self.show_view()
        if focused_view is not None:
            focused_view.focus()

    def restart(self):
        self._insert_text_directly(
            # "\n============================== RESTART ==============================\n",
            "\n" + "─" * 200 + "\n",
            # "\n" + "═"*200 + "\n",
            ("magic", "restart_line"),
        )
        
    def get_runner(self):
        return None

    def intercept_insert(self, index, txt, tags=()):
        # pylint: disable=arguments-differ
        if self._editing_allowed() and self._in_current_input_range(index):
            # self._print_marks("before insert")
            # I want all marks to stay in place
            self.mark_gravity("input_start", tk.LEFT)
            self.mark_gravity("output_insert", tk.LEFT)

            if self.get_runner().is_waiting_toplevel_command():
                tags = tags + ("toplevel", "command")
            else:
                tags = tags + ("io", "stdin")

            CodeCtrl.intercept_insert(self, index, txt, tags)

            if not self.get_runner().is_waiting_toplevel_command():
                if not self._applied_io_events:
                    # tag preceding command line differently
                    self.tag_add("before_io", "input_start -1 lines linestart")

#                self._try_submit_input()

            self.see("insert")
        else:
            #禁止输入区域
            GetApp().bell()

    def intercept_delete(self, index1, index2=None, **kw):
        if index1 == "sel.first" and index2 == "sel.last" and not self.has_selection():
            return

        if (
            self._editing_allowed()
            and self._in_current_input_range(index1)
            and (index2 is None or self._in_current_input_range(index2))
        ):
            self.direct_delete(index1, index2, **kw)
        else:
            #禁止删除区域
            GetApp().bell()

    def selection_is_writable(self):
        try:
            if not self.has_selection():
                return self._in_current_input_range(self.index("insert"))
            else:
                return self._in_current_input_range(
                    self.index("sel.first")
                ) and self._in_current_input_range(self.index("sel.last"))
        except TclError:
            return True

    def perform_return(self, event):
        if get_runner().is_running():
            # if we are fixing the middle of the input string and pressing ENTER
            # then we expect the whole line to be submitted not linebreak to be inserted
            # (at least that's how IDLE works)
            self.mark_set("insert", "end")  # move cursor to the end

            # Do the return without auto indent
            EnhancedTextWithLogging.perform_return(self, event)

            self._try_submit_input()

        elif get_runner().is_waiting_toplevel_command():
            # Same with editin middle of command, but only if it's a single line command
            whole_input = self.get("input_start", "end-1c")  # asking the whole input
            if "\n" not in whole_input and self._code_is_ready_for_submission(whole_input):
                self.mark_set("insert", "end")  # move cursor to the end
                # Do the return without auto indent
                EnhancedTextWithLogging.perform_return(self, event)
            else:
                # Don't want auto indent when code is ready for submission
                source = self.get("input_start", "insert")
                tail = self.get("insert", "end")

                if self._code_is_ready_for_submission(source + "\n", tail):
                    # No auto-indent
                    EnhancedTextWithLogging.perform_return(self, event)
                else:
                    # Allow auto-indent
                    PythonText.perform_return(self, event)

            self._try_submit_input()

        return "break"

    def on_secondary_click(self, event=None):
        super().on_secondary_click(event)
        if self.view:
            self.view.menu.tk_popup(event.x_root, event.y_root)

    def _in_current_input_range(self, index):
        try:
            return self.compare(index, ">=", "input_start")
        except Exception:
            return False

    def _insert_text_directly(self, txt, tags=()):
        def _insert(txt, tags):
            if txt != "":
                self.direct_insert("output_insert", txt, tags)

        def _insert_and_highlight_urls(txt, tags):
            parts = SIMPLE_URL_SPLIT_REGEX.split(txt)
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    _insert(part, tags)
                else:
                    if part.startswith("data:image/"):
                        token = ";base64,"
                        data = part[part.index(token) + len(token) :]
                        try:
                            img = tk.PhotoImage(data=data)
                            self._images.add(img)  # to avoit it being gc-d"""
                            self.image_create("output_insert", image=img)
                            for tag in tags:
                                self.tag_add(tag, "output_insert -1 chars")
                        except TclError:
                            _insert(part, tags + ("io_hyperlink",))
                    else:
                        _insert(part, tags + ("io_hyperlink",))

        # I want the insertion to go before marks
        # self._print_marks("before output")
        self.mark_gravity("input_start", tk.RIGHT)
        self.mark_gravity("output_insert", tk.RIGHT)
        tags = tuple(tags)

        # Make stacktrace clickable
        if "stderr" in tags or "error" in tags:
            # show lines pointing to source lines as hyperlinks
            for line in txt.splitlines(True):
                parts = re.split(r"(File .* line \d+.*)$", line, maxsplit=1)
                if len(parts) == 3 and "<pyshell" not in line:
                    _insert(parts[0], tags)
                    _insert(parts[1], tags + ("io_hyperlink",))
                    _insert(parts[2], tags)
                    # self.tag_raise("io_hyperlink", "io")
                    # self.tag_raise("io_hyperlink", "stderr")
                    # self.tag_raise("io_hyperlink", "stdout")
                else:
                    _insert_and_highlight_urls(line, tags)
        else:
            _insert_and_highlight_urls(txt, tags)

        # self._print_marks("after output")
        # output_insert mark will move automatically because of its gravity

    def _try_submit_input(self):
        # see if there is already enough inputted text to submit
        input_text = self.get("input_start", "insert")
        tail = self.get("insert", "end")

        # user may have pasted more text than necessary for this request
        submittable_text = self._extract_submittable_input(input_text, tail)

        if submittable_text is not None:
            if get_runner().is_waiting_toplevel_command():
                # clean up the tail
                if len(tail) > 0:
                    assert tail.strip() == ""
                    self.delete("insert", "end-1c")

            # leftover text will be kept in widget, waiting for next request.
            start_index = self.index("input_start")
            end_index = self.index("input_start+{0}c".format(len(submittable_text)))

            # apply correct tags (if it's leftover then it doesn't have them yet)
            if get_runner().is_running():
                self.tag_add("io", start_index, end_index)
                self.tag_add("stdin", start_index, end_index)
            else:
                self.tag_add("toplevel", start_index, end_index)
                self.tag_add("command", start_index, end_index)

            # update start mark for next input range
            self.mark_set("input_start", end_index)

            # Move output_insert mark after the requested_text
            # Leftover input, if any, will stay after output_insert,
            # so that any output that will come in before
            # next input request will go before leftover text
            self.mark_set("output_insert", end_index)

            # remove tags from leftover text
            for tag in ("io", "stdin", "toplevel", "command"):
                # don't remove magic, because otherwise I can't know it's auto
                self.tag_remove(tag, end_index, "end")

            self._submit_input(submittable_text)

    def _editing_allowed(self):
        # TODO: get rid of this
        return True

    def _extract_submittable_input(self, input_text, tail):

        if get_runner().is_waiting_toplevel_command():
            if input_text.endswith("\n"):
                if input_text.strip().startswith("%") or input_text.strip().startswith("!"):
                    # if several magic command are submitted, then take only first
                    return input_text[: input_text.index("\n") + 1]
                elif self._code_is_ready_for_submission(input_text, tail):
                    return input_text
                else:
                    return None
            else:
                return None

        elif get_runner().is_running():
            i = 0
            while True:
                if i >= len(input_text):
                    return None
                elif input_text[i] == "\n":
                    return input_text[: i + 1]
                else:
                    i += 1

        return None

    def _code_is_ready_for_submission(self, source, tail=""):
        # Ready to submit if ends with empty line
        # or is complete single-line code

        if tail.strip() != "":
            return False

        # First check if it has unclosed parens, unclosed string or ending with : or \
        parser = roughparse.RoughParser(self.indent_width, self.tabwidth)
        parser.set_str(source.rstrip() + "\n")
        if parser.get_continuation_type() != roughparse.C_NONE or parser.is_block_opener():
            return False

        # Multiline compound statements need to end with empty line to be considered
        # complete.
        lines = source.splitlines()
        # strip starting empty and comment lines
        while len(lines) > 0 and (lines[0].strip().startswith("#") or lines[0].strip() == ""):
            lines.pop(0)

        compound_keywords = ["if", "while", "for", "with", "try", "def", "class", "async", "await"]
        if len(lines) > 0:
            first_word = lines[0].strip().split()[0]
            if first_word in compound_keywords and not source.replace(" ", "").replace(
                "\t", ""
            ).endswith("\n\n"):
                # last line is not empty
                return False

        return True
        
    def process_cmd_line(self,text_to_be_submitted):
        pass

    def _submit_input(self, text_to_be_submitted):
        utils.get_logger().debug(
            "SHELL: submitting %r in state %s", text_to_be_submitted, self.get_runner().get_state()
        )
        if self.get_runner().is_waiting_toplevel_command():
            # register in history and count
            if text_to_be_submitted in self._command_history:
                self._command_history.PopItem(text_to_be_submitted)
            self.addHistory(text_to_be_submitted)

            # meaning command selection is not in process
            self._command_history_current_index = None

            self.update_tty_mode()

            try:
                self.process_cmd_line(text_to_be_submitted)
                # remember the place where the output of this command started
                self.mark_set("command_io_start", "output_insert")
                self.mark_gravity("command_io_start", "left")
                # discard old io events
                self._applied_io_events = []
                self._queued_io_events = []
            except Exception:
                GetApp().report_exception()
                self._insert_prompt()

            GetApp().event_generate("ShellCommand", command_text=text_to_be_submitted)
        else:
            assert self.get_runner().is_running()
            self.get_runner().send_program_input(text_to_be_submitted)
            GetApp().event_generate("ShellInput", input_text=text_to_be_submitted)
            self._applied_io_events.append((text_to_be_submitted, "stdin"))

    def _arrow_up(self, event):
        if not self.get_runner().is_waiting_toplevel_command():
            self.bell()
            return None

        if not self._in_current_input_range("insert"):
            self.bell()
            return None

        insert_line = index2line(self.index("insert"))
        input_start_line = index2line(self.index("input_start"))
        if insert_line != input_start_line:
            # we're in the middle of a multiline command
            self.bell()
            return None

        if self._command_history.GetSize() == 0 or self._command_history_current_index == 0:
            # can't take previous command
            self.bell()
            return "break"

        if self._command_history_current_index is None:
            self._command_history_current_index = self._command_history.GetSize() - 1
        else:
            self._command_history_current_index -= 1

        cmd = self._command_history[self._command_history_current_index]
        if cmd[-1] == "\n":
            cmd = cmd[:-1]  # remove the submission linebreak
        self._propose_command(cmd)
        return "break"

    def _arrow_down(self, event):
        if not self.get_runner().is_waiting_toplevel_command():
            self.bell()
            return None

        if not self._in_current_input_range("insert"):
            self.bell()
            return None

        insert_line = index2line(self.index("insert"))
        last_line = index2line(self.index("end-1c"))
        if insert_line != last_line:
            # we're in the middle of a multiline command
            self.bell()
            return None

        if (
            self._command_history.GetSize() == 0
            or self._command_history_current_index is None
            or self._command_history_current_index >= self._command_history.GetSize() - 1
        ):
            # can't take next command
            self._command_history_current_index = self._command_history.GetSize()
            self._propose_command("")
            self.bell()
            return "break"

        if self._command_history_current_index is None:
            self._command_history_current_index = self._command_history.GetSize() - 1
        else:
            self._command_history_current_index += 1

        self._propose_command(
            self._command_history[self._command_history_current_index].strip("\n")
        )
        return "break"

    def _propose_command(self, cmd_line):
        self.delete("input_start", "end")
        self.intercept_insert("input_start", cmd_line)
        self.see("insert")

    def _text_key_press(self, event):
        # Ctrl should underline values
        # TODO: this underline may confuse, when user is just copying on pasting
        # try to add this underline only when mouse is over the value

        # TODO: take theme into account
        """
        if event.keysym in ("Control_L", "Control_R", "Command"):  # TODO: check in Mac
            self.tag_configure("value", foreground="DarkBlue", underline=1)
        """

    def _text_key_release(self, event):
        # Remove value underlining
        # TODO: take theme into account
        """
        if event.keysym in ("Control_L", "Control_R", "Command"):  # TODO: check in Mac
            self.tag_configure("value", foreground="DarkBlue", underline=0)
        """

    def _clear_shell(self):
        end_index = self.index("output_end")
        self._clear_content(end_index)

    def compute_smart_home_destination_index(self):
        """Is used by EnhancedText"""

        if self._in_current_input_range("insert"):
            # on input line, go to just after prompt
            return "input_start"
        else:
            return super().compute_smart_home_destination_index()

    def _hyperlink_enter(self, event):
        self.config(cursor="hand2")

    def _hyperlink_leave(self, event):
        self.config(cursor="")

    def _handle_hyperlink(self, event):
        try:
            line = self.get("insert linestart", "insert lineend")
            matches = re.findall(r'File "([^"]+)", line (\d+)', line)
            if len(matches) == 1 and len(matches[0]) == 2:
                filename, lineno = matches[0]
                lineno = int(lineno)
                if os.path.exists(filename) and os.path.isfile(filename):
                    # TODO: better use events instead direct referencing
                    get_workbench().get_editor_notebook().show_file(
                        filename, lineno, set_focus=False
                    )
            else:
                r = self.tag_prevrange("io_hyperlink", "@%d,%d" % (event.x, event.y))
                if r and len(r) == 2:
                    url = self.get(r[0], r[1])
                    if SIMPLE_URL_SPLIT_REGEX.match(url):
                        webbrowser.open(url)

        except Exception:
            traceback.print_exc()

    def _show_user_exception(self, user_exception):

        for line, frame_id, *_ in user_exception["items"]:

            tags = ("io", "stderr")
            if frame_id is not None:
                frame_tag = "frame_%d" % frame_id

                def handle_frame_click(event, frame_id=frame_id):
                    self.get_runner().send_command(InlineCommand("get_frame_info", frame_id=frame_id))
                    return "break"

                # TODO: put first line with frame tag and rest without
                tags += (frame_tag,)
                self.tag_bind(frame_tag, "<ButtonRelease-1>", handle_frame_click, True)

            self._insert_text_directly(line, tags)

    def _discard_old_content(self):
        max_lines = max(utils.profile_get_int("shell.max_lines"), 1000)
        proposed_cut = self.index("end -%d lines linestart" % max_lines)
        if proposed_cut == "1.0":
            return

        # would this keep current block intact?
        next_prompt = self.tag_nextrange("prompt", proposed_cut, "end")
        if not next_prompt:
            pass  # TODO: disable stepping back

        self._clear_content(proposed_cut)

    def _clear_content(self, cut_idx):
        proposed_cut_float = float(cut_idx)
        for btn in list(self._squeeze_buttons):
            btn_pos = float(self.index(btn))
            if btn_pos < proposed_cut_float:
                self._squeeze_buttons.remove(btn)
                # looks like the widgets are not fully GC-d.
                # At least avoid leaking big chunks of texts
                btn.contained_text = None
                btn.destroy()

        self.direct_delete("0.1", cut_idx)

    def _invalidate_current_data(self):
        """
        Grayes out input & output displayed so far
        """
        end_index = self.index("output_end")

        self.tag_add("inactive", "1.0", end_index)
        self.tag_remove("value", "1.0", end_index)

        while len(self.active_object_tags) > 0:
            self.tag_remove(self.active_object_tags.pop(), "1.0", "end")

    def get_lines_above_viewport_bottom(self, tag_name, n):
        end_index = self.index("@%d,%d lineend" % (self.winfo_height(), self.winfo_height()))
        start_index = self.index(end_index + " -50 lines")

        result = ""
        while True:
            r = self.tag_nextrange(tag_name, start_index, end_index)
            if not r:
                break
            result += self.get(r[0], r[1])
            start_index = r[1]

        return result

    def update_tty_mode(self):
        self.tty_mode = utils.profile_get_int("shell.tty_mode",True)

    def set_syntax_options(self, syntax_options):
        super().set_syntax_options(syntax_options)
        self.update_margin_color()

    def update_margin_color(self):
        #如果tk版本大于8.6.6
        if strutils.compare_version(pyutils.get_tk_version_str(),("8.6.6")) > 0:
            self.tag_configure("io", lmargincolor=syntax.SyntaxThemeManager().get_syntax_options_for_tag("TEXT")["background"])

    def addHistory(self, command):
        """Add command to the command history."""
        # Reset the history position.
        # Insert this command into the history, unless it's a blank
        # line or the same as the last command.
        if command != '' \
        and (self._command_history.GetSize() == 0 or command != self._command_history[0]):
            self._command_history.PutItem(command)
            
    def CreatePopupMenu(self):
        TextCtrl.CreatePopupMenu(self)
        menu_item = tkmenu.MenuItem(NewId(),_("Clear shell"),None,None,None)
        self._popup_menu.add_separator()
        self._popup_menu.AppendMenuItem(menu_item,handler=self._clear_shell)
        item = tkmenu.MenuItem(NewId(),_("Stop/Restart backend"), None,self.stop_png,self.CanStopbackend)
        self._popup_menu.AppendMenuItem(item,handler=self.RestartBackend)
        self._popup_menu.InsertAfter(constants.ID_PASTE,NewId(),_("Paste Plus"),handler=self.PastePlus)
        
    def CanStopbackend(self):
        return True

    def _propose_command(self, cmd_line):
        self.delete("input_start", "end")
        self.intercept_insert("input_start", cmd_line)
        self.see("insert")

    def _clear_shell(self):
        '''
            清空shell窗口
        '''
        end_index = self.index("output_end")
        self.direct_delete("1.0", end_index)
            
    def RestartBackend(self):
        '''
            重启后端进程
        '''
        self.get_runner().restart_backend(clean=True,first=False)
        
    def PastePlus(self):
        '''
            粘贴并执行代码
        '''
        GetApp().MainFrame.CreateEditCommandHandler("<<Paste>>")()
        self.perform_return(None)

class BaseShell(ttk.Frame):
    def __init__(self, mater,):
        ttk.Frame.__init__(self,mater)
        self.vert_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, style=None)
        self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)
        self.text = self.GetShelltextClass()(
                self,
                font=self.GetFontName(),
                # foreground="white",
                # background="#666666",
                highlightthickness=0,
                # highlightcolor="LightBlue",
                borderwidth=0,
                yscrollcommand=self.vert_scrollbar.set,
                padx=4,
                insertwidth=2,
                height=10,
                undo=True,
            )
        self.text.grid(row=0, column=0, sticky=tk.NSEW)
        self.vert_scrollbar["command"] = self.text.yview
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        GetApp().bind("UpdateShell", self.UpdateShell, True )
        self._runner = self.GetRunner()
        self.after(1, self._start_runner)  # Show UI already before waiting for the backend to start

    def GetShelltextClass(self):
        return BaseShellText

    def GetFontName(self):
        return ''

    def UpdateShell(self,event):
        '''
            更新shell后端进程
        '''
        pass
        
    def GetRunner(self):
        return running.Runner(self)
        
    def _start_runner(self):
        try:
            GetApp().update_idletasks()  # allow UI to complete
            self._runner.start()
        except Exception:
            GetApp().report_exception("Error when initializing backend")
            
    def restart(self):
        self.text.restart()
   
    @property     
    def Runner(self):
        return self._runner
        
    def submit_magic_command(self, cmd_line):
        if isinstance(cmd_line, list):
            cmd_line = construct_cmd_line(cmd_line)

        if not cmd_line.endswith("\n"):
            cmd_line += "\n"

        self.text.submit_command(cmd_line, ("magic",))