# -*- coding: utf-8 -*-
from noval import GetApp,_
import os
import tkinter as tk
from tkinter.messagebox import showerror
import noval.iface as iface
import noval.plugin as plugin
import noval.consts as consts
from tkinter import ttk
import sys
from noval.editor.code import CodeCtrl
import noval.syntax.lang as lang
import noval.syntax.syntax as syntax
import noval.util.strutils as strutils
import noval.util.utils as utils
import noval.python.pyutils as pyutils
import re
import noval.editor.text as texteditor
import tkinter.font as tk_font
import noval.python.plugins.pyshell.running_py as running
from noval.util.command import *
from noval.shell import *
import noval.roughparse as roughparse
import traceback

runner = None
def get_runner():
    return runner

class PythonText(BaseShellText):
    def __init__(self, master=None, cnf={}, **kw):
        if "indent_with_tabs" not in kw:
            kw["indent_with_tabs"] = False
            
        BaseShellText.__init__(self,master=master, cnf=cnf, **kw)
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
    
    def perform_return(self, event):
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
        running.PythonInteractiveInterpreter.InitPrompt()
        prompt_font = tk.font.nametofont("BoldEditorFont")
        code_indent = prompt_font.measure(sys.ps1)
        self.tag_configure(
            "prompt",
            font="PyShellBoldEditorFont",
        )
        
        self.tag_bind("io_hyperlink", "<ButtonRelease-1>", self._handle_hyperlink)
        self.tag_bind("io_hyperlink", "<Enter>", self._hyperlink_enter)
        self.tag_bind("io_hyperlink", "<Leave>", self._hyperlink_leave)
        
        GetApp().bind("InputRequest", self._handle_input_request, True)
        GetApp().bind("ProgramOutput", self._handle_program_output, True)
        GetApp().bind("ToplevelResponse", self._handle_toplevel_response, True)
        GetApp().bind("DebuggerResponse", self._handle_fancy_debugger_progress, True )

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

    def perform_return(self, event):
        if get_runner().is_running():
            # if we are fixing the middle of the input string and pressing ENTER
            # then we expect the whole line to be submitted not linebreak to be inserted
            # (at least that's how IDLE works)
            self.mark_set("insert", "end")  # move cursor to the end
            # Do the return without auto indent
            CodeCtrl.perform_return(self, event)
            self._try_submit_input()

        elif get_runner().is_waiting_toplevel_command():
            # Same with editin middle of command, but only if it's a single line command
            whole_input = self.get("input_start", "end-1c")  # asking the whole input
            if "\n" not in whole_input and self._code_is_ready_for_submission(whole_input):
                self.mark_set("insert", "end")  # move cursor to the end
                # Do the return without auto indent
                CodeCtrl.perform_return(self, event)
            else:
                # Don't want auto indent when code is ready for submission
                source = self.get("input_start", "insert")
                tail = self.get("insert", "end")

                if self._code_is_ready_for_submission(source + "\n", tail):
                    # No auto-indent
                    CodeCtrl.perform_return(self, event)
                else:
                    # Allow auto-indent
                    PythonText.perform_return(self, event)

            self._try_submit_input()

        return "break"
        
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

    def process_cmd_line(self,text_to_be_submitted):
        cmd_line = text_to_be_submitted.strip()
        if cmd_line.startswith("%"):
            parts = cmd_line.split(" ", maxsplit=1)
            if len(parts) == 2:
                args_str = parts[1].strip()
            else:
                args_str = ""
            argv = strutils.parse_cmd_line(cmd_line[1:],posix=True)
            command_name = argv[0]
            cmd_args = argv[1:]
        
            if len(cmd_args) >= 2 and cmd_args[0] == "-c":
                # move source argument to source attribute
                source = cmd_args[1]
                cmd_args = [cmd_args[0]] + cmd_args[2:]
                if source == EDITOR_CONTENT_TOKEN:
                    source = (
                        get_workbench().get_editor_notebook().get_current_editor_content()
                    )
            else:
                source = None
        
            GetApp().event_generate("MagicCommand", cmd_line=text_to_be_submitted)
            self.get_runner().send_command(
                ToplevelCommand(
                    command_name,
                    args=cmd_args,
                    args_str=args_str,
                    cmd_line=cmd_line,
                    tty_mode=self.tty_mode,
                    source=source,
                )
            )
        elif cmd_line.startswith("!"):
            argv = strutils.parse_cmd_line(cmd_line[1:])
            GetApp().event_generate("SystemCommand", cmd_line=text_to_be_submitted)
            self.get_runner().send_command(
                ToplevelCommand(
                    "execute_system_command",
                    argv=argv,
                    cmd_line=cmd_line,
                    tty_mode=self.tty_mode,
                    source = None
                )
            )
        else:
            self.get_runner().send_command(
                ToplevelCommand(
                    "execute_source", source=text_to_be_submitted, tty_mode=self.tty_mode
                )
            )

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
                    GetApp().GotoView(filename,lineno,load_outline=False)
        except Exception:
            traceback.print_exc()
            
    def get_runner(self):
        return get_runner()

    def CanStopbackend(self):
        return not (utils.profile_get("run.backend_name","SameAsFrontend") == "SameAsFrontend" or get_runner().get_backend_proxy() is None)

class PyShell(BaseShell):
    def __init__(self, mater):
        global runner
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
        BaseShell.__init__(self,mater)
        self._add_main_backends()
        runner = self._runner
        
    def UpdateShell(self,event):
        current_interpreter = GetApp().GetCurrentInterpreter()
        backend = None
        if current_interpreter.IsBuiltIn:
            backend = "SameAsFrontend"
        else:
            backend = "CustomCPython"
        utils.profile_set("run.backend_name",backend)
        self._runner.restart_backend(clean=True,first=False)

    def _start_runner(self):
        try:
            GetApp().update_idletasks()  # allow UI to complete
            self._runner.start()
        except Exception:
            GetApp().report_exception("Error when initializing backend")
            

    def GetShelltextClass(self):
        return ShellText

    def GetFontName(self):
        return 'PyShellEditorFont'

    def GetRunner(self):
        return running.PythonRunner(self)
    
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

    def _add_main_backends(self):
        #self.set_default("run.backend_name", "SameAsFrontend")
        #self.set_default("CustomInterpreter.used_paths", [])
        #self.set_default("CustomInterpreter.path", "")
        GetApp().add_backend(
            "SameAsFrontend",
            running.BuiltinCPythonProxy,
            _("The same interpreter which runs Thonny (default)"),
            "1",
        )
        GetApp().add_backend(
            "CustomCPython",
            running.CustomCPythonProxy,
            _("Alternative Python 3 interpreter or virtual environment"),
            "2",
        )

class PyshellViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(consts.PYTHON_INTERPRETER_VIEW_NAME,PyShell, _("Shell"), "s",\
                            image_file="python/interpreter.ico",default_position_key=1)


