# -*- coding: utf-8 -*-
from noval import GetApp,_
import os
import tkinter as tk
from tkinter.messagebox import showerror
import noval.iface as iface
import noval.plugin as plugin
import noval.consts as consts
from tkinter import ttk
from code import InteractiveInterpreter
import sys
from noval.editor.code import CodeCtrl
import noval.syntax.lang as lang
import noval.syntax.syntax as syntax
import noval.util.strutils as strutils
import noval.util.utils as utils
import noval.python.pyutils as pyutils
from noval.util import hiscache
import re
import noval.editor.text as texteditor
import tkinter.font as tk_font
import six.moves.builtins as builtins

#执行解释器退出方法时,提示的信息
EXIT_PROMPT_ERROR_MSG = 'Click on the close button to leave the application.'

def execfile(filePath):
    with open(filePath,encoding="utf-8") as f:
        exec(f.read())

class PythonText(CodeCtrl):
    def __init__(self, master=None, cnf={}, **kw):
        if "indent_with_tabs" not in kw:
            kw["indent_with_tabs"] = False
            
        CodeCtrl.__init__(self,master=master, cnf=cnf, **kw)
        self._should_tag_current_line = False
        
    def GetLangLexer(self):
        if self._lang_lexer is None:
            self._lang_lexer = syntax.SyntaxThemeManager().GetLexer(lang.ID_LANG_PYTHON)
        return self._lang_lexer
        
    def _reload_theme_options(self,force=False):
        texteditor.TextCtrl._reload_theme_options(self,force)
        
    def CanPaste(self):
        return True
        
    def GetColorClass(self):
        '''
            shell窗口的python着色类和普通python文本的着色类稍微有点差别
        '''
        lexer = self.GetLangLexer()
        return lexer.GetShellColorClass()
    
    def perform_return1111(self, event):
        # copied from idlelib.EditorWindow (Python 3.4.2)
        # slightly modified
        # pylint: disable=lost-exception

        text = event.widget
        assert text is self

        try:
            # delete selection
            first, last = text.get_selection_indices()
            if first and last:
                text.delete(first, last)
                text.mark_set("insert", first)

            # Strip whitespace after insert point
            # (ie. don't carry whitespace from the right of the cursor over to the new line)
            while text.get("insert") in [" ", "\t"]:
                text.delete("insert")

            left_part = text.get("insert linestart", "insert")
            # locate first non-white character
            i = 0
            n = len(left_part)
            while i < n and left_part[i] in " \t":
                i = i + 1

            # is it only whitespace?
            if i == n:
                # start the new line with the same whitespace
                text.insert("insert", "\n" + left_part)
                return "break"

            # Turned out the left part contains visible chars
            # Remember the indent
            indent = left_part[:i]

            # Strip whitespace before insert point
            # (ie. after inserting the linebreak this line doesn't have trailing whitespace)
            while text.get("insert-1c", "insert") in [" ", "\t"]:
                text.delete("insert-1c", "insert")

            # start new line
            text.insert("insert", "\n")

            # adjust indentation for continuations and block
            # open/close first need to find the last stmt
            lno = tktextext.index2line(text.index("insert"))
            y = roughparse.RoughParser(text.indent_width, text.tabwidth)

            for context in roughparse.NUM_CONTEXT_LINES:
                startat = max(lno - context, 1)
                startatindex = repr(startat) + ".0"
                rawtext = text.get(startatindex, "insert")
                y.set_str(rawtext)
                bod = y.find_good_parse_start(
                    False, roughparse._build_char_in_string_func(startatindex)
                )
                if bod is not None or startat == 1:
                    break
            y.set_lo(bod or 0)

            c = y.get_continuation_type()
            if c != roughparse.C_NONE:
                # The current stmt hasn't ended yet.
                if c == roughparse.C_STRING_FIRST_LINE:
                    # after the first line of a string; do not indent at all
                    pass
                elif c == roughparse.C_STRING_NEXT_LINES:
                    # inside a string which started before this line;
                    # just mimic the current indent
                    text.insert("insert", indent)
                elif c == roughparse.C_BRACKET:
                    # line up with the first (if any) element of the
                    # last open bracket structure; else indent one
                    # level beyond the indent of the line with the
                    # last open bracket
                    text._reindent_to(y.compute_bracket_indent())
                elif c == roughparse.C_BACKSLASH:
                    # if more than one line in this stmt already, just
                    # mimic the current indent; else if initial line
                    # has a start on an assignment stmt, indent to
                    # beyond leftmost =; else to beyond first chunk of
                    # non-whitespace on initial line
                    if y.get_num_lines_in_stmt() > 1:
                        text.insert("insert", indent)
                    else:
                        text._reindent_to(y.compute_backslash_indent())
                else:
                    assert 0, "bogus continuation type %r" % (c,)
                return "break"

            # This line starts a brand new stmt; indent relative to
            # indentation of initial line of closest preceding
            # interesting stmt.
            indent = y.get_base_indent_string()
            text.insert("insert", indent)
            if y.is_block_opener():
                text.perform_smart_tab(event)
            elif indent and y.is_block_closer():
                text.perform_smart_backspace(event)
            return "break"
        finally:
            text.see("insert")
            text.event_generate("<<NewLine>>")
            return "break"
            

class ShellText(PythonText):
    def __init__(self, master, cnf={}, **kw):

        PythonText.__init__(self,master, cnf, **kw)
        self.bindtags(self.bindtags() + ("ShellText",))
        PythonInteractiveInterpreter.InitPrompt()
        self._before_io = True
        self._command_history = (
            []
        )  # actually not really history, because each command occurs only once
        self._command_history_current_index = None
        prompt_font = tk.font.nametofont("BoldEditorFont")
        vert_spacing = 10
        io_indent = 16
        code_indent = prompt_font.measure(sys.ps1)

        self.tag_configure("command", lmargin1=code_indent, lmargin2=code_indent)
        self.tag_configure(
            "io",
            lmargin1=io_indent,
            lmargin2=io_indent,
            rmargin=io_indent,
            font="IOFont",
        )
        
        self.tag_configure(
            "prompt",
            font="PyShellBoldEditorFont",
        )
        #如果tk版本大于8.6.6
        if strutils.compare_version(pyutils.get_tk_version_str(),("8.6.6")) > 0:
            self.tag_configure(
                "io", lmargincolor=syntax.SyntaxThemeManager().get_syntax_options_for_tag("TEXT")["background"]
            )

        self.tag_bind("hyperlink", "<ButtonRelease-1>", self._handle_hyperlink)
        self.tag_bind("hyperlink", "<Enter>", self._hyperlink_enter)
        self.tag_bind("hyperlink", "<Leave>", self._hyperlink_leave)
        self.tag_raise("hyperlink")

        self.tag_configure("vertically_spaced", spacing1=vert_spacing)
        
        # Underline on font looks better than underline on tag
        io_hyperlink_font = tk.font.nametofont("IOFont").copy()
      #  io_hyperlink_font.configure(underline=get_syntax_options_for_tag("hyperlink").get("underline", True))
        self.tag_configure("io_hyperlink", 
                           underline=False,
                           font=io_hyperlink_font)
        self.tag_raise("io_hyperlink", "hyperlink")

        self.tag_configure("suppressed_io", elide=True)

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

        self._last_welcome_text = None
     #   self.bind("<<Return>>",self.perform_return)

  #      get_workbench().bind("InputRequest", self._handle_input_request, True)
   #     get_workbench().bind("ProgramOutput", self._handle_program_output, True)
    #    get_workbench().bind("ToplevelResponse", self._handle_toplevel_response, True)
     #   get_workbench().bind(
      #      "DebuggerResponse", self._handle_fancy_debugger_progress, True
       # )

    #    self._init_menu()

    def _init_menu(self):
        self._menu = tk.Menu(self, tearoff=False, **get_style_configuration("Menu"))
        clear_seq = get_workbench().get_option(
            "shortcuts.clear_shell", _CLEAR_SHELL_DEFAULT_SEQ
        )
        self._menu.add_command(
            label="Clear shell",
            command=self._clear_shell,
            accelerator=sequence_to_accelerator(clear_seq),
        )

    def submit_command(self, cmd_line, tags):
        assert get_runner().is_waiting_toplevel_command()
        self.delete("input_start", "end")
        self.insert("input_start", cmd_line, tags)
        self.see("end")
        self.mark_set("insert", "end")
        self._try_submit_input()

    def _handle_input_request(self, msg):
        self.focus_set()
        self.mark_set("insert", "end")
        self.tag_remove("sel", "1.0", tk.END)
        self._try_submit_input()  # try to use leftovers from previous request
        self.see("end")

    def _handle_program_output(self, msg):
        # mark first line of io
        if self._before_io:
            self._insert_text_directly(
                msg.data[0], ("io", msg.stream_name, "vertically_spaced")
            )
            self._before_io = False
            self._insert_text_directly(msg.data[1:], ("io", msg.stream_name))
        else:
            self._insert_text_directly(msg.data, ("io", msg.stream_name))

        self.mark_set("output_end", self.index("end-1c"))
        self.see("end")

    def _handle_toplevel_response(self, msg):
        self._before_io = True
        if msg.get("error"):
            self._insert_text_directly(msg["error"] + "\n", ("toplevel", "stderr"))
        if "user_exception" in msg:
            self._show_user_exception(msg["user_exception"])

        welcome_text = msg.get("welcome_text")
        if welcome_text and welcome_text != self._last_welcome_text:
            self._insert_text_directly(welcome_text, ("comment",))
            self._last_welcome_text = welcome_text

        if "value_info" in msg:
            num_stripped_question_marks = getattr(msg, "num_stripped_question_marks", 0)
            if num_stripped_question_marks > 0:
                # show the value in object inspector
                get_workbench().event_generate(
                    "ObjectSelect", object_id=msg["value_info"].id
                )
            else:
                # show the value in shell
                value_repr = shorten_repr(msg["value_info"].repr, 10000)
                if value_repr != "None":
                    if get_workbench().in_heap_mode():
                        value_repr = memory.format_object_id(msg["value_info"].id)
                    object_tag = "object_" + str(msg["value_info"].id)
                    self._insert_text_directly(
                        value_repr + "\n", ("toplevel", "value", object_tag)
                    )
                    if running_on_mac_os():
                        sequence = "<Command-Button-1>"
                    else:
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
        self._update_visible_io(None)
        self._insert_prompt()
        self._try_submit_input()  # Trying to submit leftover code (eg. second magic command)
        self.see("end")

    def _handle_fancy_debugger_progress(self, msg):
        if msg.in_present or msg.io_symbol_count is None:
            self._update_visible_io(None)
        else:
            self._update_visible_io(msg.io_symbol_count)

    def _update_visible_io(self, num_visible_chars):
        self.tag_remove("suppressed_io", "1.0", "end")
        if num_visible_chars is not None:
            start_index = self.index("command_io_start+" + str(num_visible_chars) + "c")
            self.tag_add("suppressed_io", start_index, "end")

        self.see("end")

    def _insert_prompt(self,prompt=None):
        if prompt is None:
            prompt = sys.ps1
        # if previous output didn't put a newline, then do it now
        if not self.index("output_insert").endswith(".0"):
            self._insert_text_directly("\n", ("io",))

        prompt_tags = ("toplevel", "prompt")

        # if previous line has value or io then add little space
        prev_line = self.index("output_insert - 1 lines")
        prev_line_tags = self.tag_names(prev_line)
        if "io" in prev_line_tags or "value" in prev_line_tags:
            prompt_tags += ("vertically_spaced",)
            # self.tag_add("last_result_line", prev_line)

        self._insert_text_directly(prompt, prompt_tags)
        self.edit_reset()

    def restart(self):
        self._insert_text_directly(
            "\n========================= RESTART =========================\n",
            ("magic",),
        )

    def intercept_insert(self, index, txt, tags=()):
        # pylint: disable=arguments-differ
        if self._editing_allowed() and self._in_current_input_range(index):
            # self._print_marks("before insert")
            # I want all marks to stay in place
            self.mark_gravity("input_start", tk.LEFT)
            self.mark_gravity("output_insert", tk.LEFT)
            tags = tags + ("io", "stdin")

            PythonText.intercept_insert(self, index, txt, tags)
            if self._before_io:
                # tag first char of io differently
                self.tag_add("vertically_spaced", index)
                self._before_io = False

         #   self._try_submit_input()

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
            GetApp().bell()

    def perform_return(self, event):
    
        # if we are fixing the middle of the input string and pressing ENTER
        # then we expect the whole line to be submitted not linebreak to be inserted
        # (at least that's how IDLE works)
        self.mark_set("insert", "end")  # move cursor to the end
        # Do the return without auto indent
        ###PythonText.perform_return(self, event)
       # self.insert("insert", "\n")
        return "break"

    def on_secondary_click(self, event=None):
        texteditor.TextCtrl.CreatePopupMenu(self)
        self._popup_menu.tk_popup(event.x_root, event.y_root)

    def _in_current_input_range(self, index):
        try:
            return self.compare(index, ">=", "input_start")
        except Exception:
            return False

    def _insert_text_directly(self, txt, tags=()):
        if "\a" in txt:
            get_workbench().bell()
            # TODO: elide bell character

        def _insert(txt, tags):
            if txt != "":
                self.direct_insert("output_insert", txt, tags)

        # I want the insertion to go before marks
        # self._print_marks("before output")
        self.mark_gravity("input_start", tk.RIGHT)
        self.mark_gravity("output_insert", tk.RIGHT)
        tags = tuple(tags)

        if "stderr" in tags or "error" in tags:
            # show lines pointing to source lines as hyperlinks
            for line in txt.splitlines(True):
                parts = re.split(r"(File .* line \d+.*)$", line, maxsplit=1)
                if len(parts) == 3 and "<pyshell" not in line:
                    _insert(parts[0], tags)
                    _insert(parts[1], tags + ("hyperlink", "io_hyperlink",))
                    _insert(parts[2], tags)
                else:
                    _insert(line, tags)
        else:
            _insert(txt, tags)

        # self._print_marks("after output")
        # output_insert mark will move automatically because of its gravity
        
    def get_submit_text(self):
        
        input_text = self.get("input_start", "insert")
        tail = self.get("insert", "end")

        # user may have pasted more text than necessary for this request
        submittable_text = self._extract_submittable_input(input_text, tail)
        
        # leftover text will be kept in widget, waiting for next request.
        start_index = self.index("input_start")
        end_index = self.index("input_start+{0}c".format(len(submittable_text)))

        # apply correct tags (if it's leftover then it doesn't have them yet)

        self.tag_add("io", start_index, end_index)
        self.tag_add("stdin", start_index, end_index)

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
                
        return submittable_text

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
        i = 0
        while True:
            if i >= len(input_text):
                return input_text
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
        if (
            parser.get_continuation_type() != roughparse.C_NONE
            or parser.is_block_opener()
        ):
            return False

        # Multiline compound statements need to end with empty line to be considered
        # complete.
        lines = source.splitlines()
        # strip starting empty and comment lines
        while len(lines) > 0 and (
            lines[0].strip().startswith("#") or lines[0].strip() == ""
        ):
            lines.pop(0)

        compound_keywords = [
            "if",
            "while",
            "for",
            "with",
            "try",
            "def",
            "class",
            "async",
            "await",
        ]
        if len(lines) > 0:
            first_word = lines[0].strip().split()[0]
            if first_word in compound_keywords and not source.replace(" ", "").replace(
                "\t", ""
            ).endswith("\n\n"):
                # last line is not empty
                return False

        return True

    def _submit_input(self, text_to_be_submitted):
        logging.debug(
            "SHELL: submitting %r in state %s",
            text_to_be_submitted,
            get_runner().get_state(),
        )
        if get_runner().is_waiting_toplevel_command():
            # register in history and count
            if text_to_be_submitted in self._command_history:
                self._command_history.remove(text_to_be_submitted)
            self._command_history.append(text_to_be_submitted)
            self._command_history_current_index = (
                None
            )  # meaning command selection is not in process

            cmd_line = text_to_be_submitted.strip()
            try:
                if cmd_line.startswith("%"):
                    parts = cmd_line.split(" ", maxsplit=1)
                    if len(parts) == 2:
                        args_str = parts[1].strip()
                    else:
                        args_str = ""
                    argv = parse_cmd_line(cmd_line[1:])
                    command_name = argv[0]
                    get_workbench().event_generate(
                        "MagicCommand", cmd_line=text_to_be_submitted
                    )
                    get_runner().send_command(
                        ToplevelCommand(
                            command_name,
                            args=argv[1:],
                            args_str=args_str,
                            cmd_line=cmd_line,
                        )
                    )
                elif cmd_line.startswith("!"):
                    argv = parse_cmd_line(cmd_line[1:])
                    get_workbench().event_generate(
                        "SystemCommand", cmd_line=text_to_be_submitted
                    )
                    get_runner().send_command(
                        ToplevelCommand(
                            "execute_system_command", argv=argv, cmd_line=cmd_line
                        )
                    )
                else:
                    get_runner().send_command(
                        ToplevelCommand("execute_source", source=text_to_be_submitted)
                    )

                # remember the place where the output of this command started
                self.mark_set("command_io_start", "output_insert")
                self.mark_gravity("command_io_start", "left")
            except Exception:
                get_workbench().report_exception()
                self._insert_prompt()

            get_workbench().event_generate(
                "ShellCommand", command_text=text_to_be_submitted
            )
        else:
            assert get_runner().is_running()
            get_runner().send_program_input(text_to_be_submitted)
            get_workbench().event_generate(
                "ShellInput", input_text=text_to_be_submitted
            )

    def _arrow_up(self, event):
        if not self._in_current_input_range("insert"):
            return None

        insert_line = index2line(self.index("insert"))
        input_start_line = index2line(self.index("input_start"))
        if insert_line != input_start_line:
            # we're in the middle of a multiline command
            return None

        if len(self._command_history) == 0 or self._command_history_current_index == 0:
            # can't take previous command
            return "break"

        if self._command_history_current_index is None:
            self._command_history_current_index = len(self._command_history) - 1
        else:
            self._command_history_current_index -= 1

        cmd = self._command_history[self._command_history_current_index]
        if cmd[-1] == "\n":
            cmd = cmd[:-1]  # remove the submission linebreak
        self._propose_command(cmd)
        return "break"

    def _arrow_down(self, event):
        if not self._in_current_input_range("insert"):
            return None

        insert_line = index2line(self.index("insert"))
        last_line = index2line(self.index("end-1c"))
        if insert_line != last_line:
            # we're in the middle of a multiline command
            return None

        if (
            len(self._command_history) == 0
            or self._command_history_current_index == len(self._command_history) - 1
        ):
            # can't take next command
            return "break"

        if self._command_history_current_index is None:
            self._command_history_current_index = len(self._command_history) - 1
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
        self.direct_delete("1.0", end_index)

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
        except Exception:
            traceback.print_exc()

    def _show_user_exception(self, user_exception):

        for line, frame_id, _ in user_exception["items"]:

            tags = ("io", "stderr")
            if frame_id is not None:
                frame_tag = "frame_%d" % frame_id

                def handle_frame_click(event, frame_id=frame_id):
                    get_runner().send_command(
                        InlineCommand("get_frame_info", frame_id=frame_id)
                    )
                    return "break"

                # TODO: put first line with frame tag and rest without
                tags += (frame_tag,)
                self.tag_bind(frame_tag, "<ButtonRelease-1>", handle_frame_click, True)

            self._insert_text_directly(line, tags)

    def _invalidate_current_data(self):
        """
        Grayes out input & output displayed so far
        """
        end_index = self.index("output_end")

        self.tag_add("inactive", "1.0", end_index)
        self.tag_remove("value", "1.0", end_index)

        while len(self.active_object_tags) > 0:
            self.tag_remove(self.active_object_tags.pop(), "1.0", "end")


class PythonInteractiveInterpreter(InteractiveInterpreter):
    """Interpreter based on code.InteractiveInterpreter."""
    
    @staticmethod
    def InitPrompt():
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = '>>> '
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = '... '
    
    def __init__(self, locals=None, rawin=None, 
                 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                 showInterpIntro=True):
        """Create an interactive interpreter object."""
        InteractiveInterpreter.__init__(self, locals=locals)
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        if rawin:
            builtins.raw_input = rawin
        if showInterpIntro:
            copyright = 'Type "help", "copyright", "credits" or "license"'
            copyright += ' for more information.'
            #linux系统下sys.version包含换行符,需要去除掉
            self.introText = 'Python %s on %s%s%s' % \
                             (sys.version.replace(os.linesep,""), sys.platform, os.linesep, copyright)
        self.InitPrompt()
        self.more = 0
        # List of lists to support recursive push().
        self.commandBuffer = []
        self.startupScript = None
    
    def push(self, command, astMod=None):
        """Send command to the interpreter to be executed.
        
        Because this may be called recursively, we append a new list
        onto the commandBuffer list and then append commands into
        that.  If the passed in command is part of a multi-line
        command we keep appending the pieces to the last list in
        commandBuffer until we have a complete command. If not, we
        delete that last list."""
        
        # In case the command is unicode try encoding it
        if utils.is_py2():
            if type(command) == unicode:
                try:
                    command = command.encode(utils.get_default_encoding())
                except UnicodeEncodeError:
                    pass # otherwise leave it alone
                
        if not self.more:
            try: del self.commandBuffer[-1]
            except IndexError: pass
        if not self.more: self.commandBuffer.append([])
        self.commandBuffer[-1].append(command)
        source = '\n'.join(self.commandBuffer[-1])
        
        # If an ast code module is passed, pass it to runModule instead
        more=False
        if astMod != None:
            self.runModule(astMod)
            self.more=False
        else:
            more = self.more = self.runsource(source)
        return more
        
    def runsource(self, source,filename="<input>", symbol="single"):
        """Compile and run source code in the interpreter."""
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   self.stdin, self.stdout, self.stderr
        more = InteractiveInterpreter.runsource(self, source,filename,symbol)
        # this was a cute idea, but didn't work...
        #more = self.runcode(compile(source,'',
        #               ('exec' if self.useExecMode else 'single')))
        
        
        # If sys.std* is still what we set it to, then restore it.
        # But, if the executed source changed sys.std*, assume it was
        # meant to be changed and leave it. Power to the people.
        if sys.stdin == self.stdin:
            sys.stdin = stdin
        else:
            self.stdin = sys.stdin
        if sys.stdout == self.stdout:
            sys.stdout = stdout
        else:
            self.stdout = sys.stdout
        if sys.stderr == self.stderr:
            sys.stderr = stderr
        else:
            self.stderr = sys.stderr
        return more
        
    def runModule(self, mod):
        """Compile and run an ast module in the interpreter."""
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   self.stdin, self.stdout, self.stderr
        self.runcode(compile(mod,'','single'))
        # If sys.std* is still what we set it to, then restore it.
        # But, if the executed source changed sys.std*, assume it was
        # meant to be changed and leave it. Power to the people.
        if sys.stdin == self.stdin:
            sys.stdin = stdin
        else:
            self.stdin = sys.stdin
        if sys.stdout == self.stdout:
            sys.stdout = stdout
        else:
            self.stdout = sys.stdout
        if sys.stderr == self.stderr:
            sys.stderr = stderr
        else:
            self.stderr = sys.stderr
        return False
    
    def getAutoCompleteKeys(self):
        """Return list of auto-completion keycodes."""
        return [ord('.')]

    def getAutoCompleteList(self, command='', *args, **kwds):
        """Return list of auto-completion options for a command.
        
        The list of options will be based on the locals namespace."""
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   self.stdin, self.stdout, self.stderr
        l = introspect.getAutoCompleteList(command, self.locals,
                                           *args, **kwds)
        sys.stdin, sys.stdout, sys.stderr = stdin, stdout, stderr
        return l

    def getCallTip(self, command='', *args, **kwds):
        """Return call tip text for a command.
        
        Call tip information will be based on the locals namespace."""
        return introspect.getCallTip(command, self.locals, *args, **kwds)
        

class PseudoFile:

    def __init__(self):
        """Create a file-like object."""
        pass

    def readline(self):
        pass

    def write(self, s):
        pass

    def writelines(self, l):
        map(self.write, l)

    def flush(self):
        pass

    def isatty(self):
        pass


class PseudoFileIn(PseudoFile):

    def __init__(self, readline, readlines=None):
        if callable(readline):
            self.readline = readline
        else:
            raise ValueError('readline must be callable')
        if callable(readlines):
            self.readlines = readlines

    def isatty(self):
        return 1
        
        
class PseudoFileOut(PseudoFile):

    def __init__(self, write):
        if callable(write):
            self.write = write
        else:
            raise ValueError('write must be callable')

    def isatty(self):
        return 1


class PseudoFileErr(PseudoFile):

    def __init__(self, write):
        if callable(write):
            self.write = write
        else:
            raise ValueError('write must be callable')

    def isatty(self):
        return 1

class PyShell(ttk.Frame):
    def __init__(self, mater,introText='', locals=None, InterpClass=PythonInteractiveInterpreter,startupScript=None, \
                 execStartupScript=True,*args, **kwds):
        ttk.Frame.__init__(self,mater)
        self.vert_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, style=None)
        self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)
        default_editor_family = GetApp().GetDefaultEditorFamily()
        #pyshell不能和文本编辑器使用同一字体,以免放大字体时pyshell也会放大字体
        self.fonts = [
            tk_font.Font(
                name="PyShellEditorFont", family=utils.profile_get(consts.EDITOR_FONT_FAMILY_KEY,default_editor_family)
            ),
            tk_font.Font(
                name="PyShellBoldEditorFont",
                family=utils.profile_get(consts.EDITOR_FONT_FAMILY_KEY,default_editor_family),
                weight="bold",
            ),
        ]
        
        self.text = ShellText(
                self,
                font="PyShellEditorFont",
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
        
        self.text.bind("<Up>", self._arrow_up, True)
        self.text.bind("<Down>", self._arrow_down, True)
       # self.text.bind("<KeyPress>", self._text_key_press, True)
        #self.text.bind("<KeyRelease>", self._text_key_release, True)
        #必须先解绑text控件绑定的回车键事件,重写该事件方法
        self.text.unbind("<Return>")
        self.text.bind("<Return>", self.perform_return, True)
        
        if locals is None:
            import __main__
            locals = __main__.__dict__

        # Grab these so they can be restored by self.redirect* methods.
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        
        # Create a replacement for stdin.
        self.reader = PseudoFileIn(self.readline, self.readlines)
        self.reader.input = ''
        self.reader.isreading = False
        
        self.interp = InterpClass(locals=locals,
                                  rawin=self.raw_input,
                                  stdin=self.reader,
                                  stdout=PseudoFileOut(self.writeOut),
                                  stderr=PseudoFileErr(self.writeErr),
                                  *args, **kwds)
            
        self.more = False
        
        self.history = hiscache.HistoryCache(100)
        self.historyIndex = -1

        # 显示Python解释器信息.
        self.showIntro(introText)
        #重写内建的解释器关闭,退出事件,不运行用户在解释器中执行退出,关闭方法
        self.setBuiltinKeywords()
        self.text._insert_prompt()
        #python3没有execfile函数,自己实现一个
        if utils.is_py3():
            import builtins
            builtins.execfile = execfile
        
    def _arrow_up(self,event):
        #if self.historyIndex < 0:
         #   self.text.bell()
            #返回break禁止默认键盘事件
          #  
        self.OnHistoryReplace(step=+1)
        return "break"
        
    def _arrow_down(self,event):
        self.OnHistoryReplace(step=-1)
        return "break"
        
    def perform_return(self,event):
        self.text.perform_return(event)
        command = self.text.get_submit_text().strip()
        self.push(command)
        return "break"
        
    def setBuiltinKeywords(self):
        #重定向系统模块的退出方法到一个字符串
        builtins.close = builtins.exit = builtins.quit = EXIT_PROMPT_ERROR_MSG
        os._exit = sys.exit = EXIT_PROMPT_ERROR_MSG
        
    def push(self, command, silent = False):
        try:
            if not silent:
                self.write(os.linesep)
        
            #DNM
          #  if USE_MAGIC:
           #     command=magic(command)
             
            self.waiting = True
            self.lastUpdate=None
            self.more = self.interp.push(command)
            self.lastUpdate=None
            self.waiting = False
            if not self.more:
                self.addHistory(command.rstrip())
            if not silent:
                self.prompt()
        except SystemExit as x:
            self.write(str(x))
            self.run("")
            #sys.exit
        except Exception as x:
            self.write(str(x))
            
    def run(self, command, prompt=True, verbose=True):
        """Execute command as if it was typed in directly.
        >>> shell.run('print "this"')
        >>> print "this"
        this
        >>>
        """
        # Go to the very bottom of the text.
     #   endpos = self.GetTextLength()
      #  self.SetCurrentPos(endpos)
        command = command.rstrip()
        if prompt: self.prompt()
        if verbose: self.write(command)
        self.push(command)

    def runsource(self,source,filename="<editor selection>", symbol="exec"):
        self.write('\n')
        self.interp.runsource(source.strip(),filename,symbol)
        self.prompt()
            
    def prompt(self):
        """Display proper prompt for the context: ps1, ps2 or ps3.

        If this is a continuation line, autoindent as necessary."""
        isreading = self.reader.isreading
        skip = False
        if isreading:
            prompt = str(sys.ps3)
        elif self.more:
            prompt = str(sys.ps2)
        else:
            prompt = str(sys.ps1)
        pos = self.text.GetCurrentColumn()
        if pos > 0:
            if isreading:
                skip = True
            else:
                self.write(os.linesep)
        if not self.more:
            self.promptPosStart = self.text.GetCurrentPos()
        if not skip:
            self.text._insert_prompt(prompt)
           # self.write(prompt)
        if not self.more:
            self.promptPosEnd = self.text.GetCurrentPos()
            # Keep the undo feature from undoing previous responses.
         ##   self.EmptyUndoBuffer()
        
        if self.more:
            line_num=self.GetCurrentLine()
            currentLine=self.GetLine(line_num)
            previousLine=self.GetLine(line_num-1)[len(prompt):]
            pstrip=previousLine.strip()
            lstrip=previousLine.lstrip()
            
            # Get the first alnum word:
            first_word=[]
            for i in pstrip:
                if i.isalnum():
                    first_word.append(i)
                else:
                    break
            first_word = ''.join(first_word)
            
            if pstrip == '':
                # because it is all whitespace!
                indent=previousLine.strip('\n').strip('\r')
            else:
                indent=previousLine[:(len(previousLine)-len(lstrip))]
                if pstrip[-1]==':' and \
                    first_word in ['if','else','elif','for','while',
                                   'def','class','try','except','finally']:
                    indent+=' '*4
            
            self.write(indent)
        self.text.see("end")
            

    def addHistory(self, command):
        """Add command to the command history."""
        # Reset the history position.
        self.historyIndex = -1
        # Insert this command into the history, unless it's a blank
        # line or the same as the last command.
        if command != '' \
        and (self.history.GetSize() == 0 or command != self.history[0]):
            self.history.PutItem(command)

    def readline(self):
        """Replacement for stdin.readline()."""
        input = ''
        reader = self.reader
        reader.isreading = True
        self.prompt()
        try:
            while not reader.input:
                wx.YieldIfNeeded()
            input = reader.input
        finally:
            reader.input = ''
            reader.isreading = False
        input = str(input)  # In case of Unicode.
        return input

    def readlines(self):
        """Replacement for stdin.readlines()."""
        lines = []
        while lines[-1:] != ['\n']:
            lines.append(self.readline())
        return lines

    def raw_input(self, prompt=''):
        """Return string based on user input."""
        if prompt:
            self.write(prompt)
        return self.readline()
        
    def writeOut(self, text):
        """Replacement for stdout."""
        self.write(text)

    def writeErr(self, text):
        """Replacement for stderr."""
        tags = ("io", "stderr")
        self.write(text,tags)
        
    def showIntro(self, text=''):
        """Display introductory text in the shell."""
        if text:
            self.write(text)
        try:
            if self.interp.introText:
                if text and not text.endswith(os.linesep):
                    self.write(os.linesep)
                self.write(self.interp.introText,tags=('magic',))
        except AttributeError:
            pass

    def write(self, text,tags=()):
        """Display text in the shell.

        Replace line endings with OS-specific endings."""
        text = self.fixLineEndings(text)
        self.AddText(text,tags)
    
    def fixLineEndings(self, text):
        """Return text with line endings replaced by OS-specific endings."""
        lines = text.split('\r\n')
        for l in range(len(lines)):
            chunks = lines[l].split('\r')
            for c in range(len(chunks)):
                chunks[c] = os.linesep.join(chunks[c].split('\n'))
            lines[l] = os.linesep.join(chunks)
        text = os.linesep.join(lines)
        return text
        
    def AddText(self,text,tags=()):
        self.text._insert_text_directly(text,tags)
        
    def clearCommand(self):
        """Delete the current, unexecuted command."""
        startpos = self.promptPosEnd
        endpos = self.GetTextLength()
        self.SetSelection(startpos, endpos)
        self.ReplaceSelection('')
        self.more = False

    def OnHistoryReplace(self, step):
        """Replace with the previous/next command from the history buffer."""
        self.clearCommand()
        self.replaceFromHistory(step)

    def replaceFromHistory(self, step):
        """Replace selection with command from the history buffer."""
        ps2 = str(sys.ps2)
        self.ReplaceSelection('')
        newindex = self.historyIndex + step
        if -1 <= newindex <= len(self.history):
            self.historyIndex = newindex
        if 0 <= newindex <= len(self.history)-1:
            command = self.history[self.historyIndex]
            command = command.replace('\n', os.linesep + ps2)
            self.ReplaceSelection(command)
        else:
            self.text.bell()

class PyshellViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(consts.PYTHON_INTERPRETER_VIEW_NAME,PyShell, _("Python Interpreter"), "s",\
                            image_file="python/interpreter.ico",default_position_key=1)


