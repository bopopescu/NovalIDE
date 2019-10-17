# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        ui_base.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-11
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk,TclError
import noval.util.utils as utils
import noval.constants as constants
from tkinter import font as tkfont
import noval.consts as consts
from noval.python.parser.utils import py_cmp,py_sorted
import noval.imageutils as imageutils
import noval.ttkwidgets.listboxframe as listboxframe

class ClosableNotebook(ttk.Notebook):
    def __init__(self, master, style="ButtonNotebook.TNotebook", **kw):
        ttk.Notebook.__init__(self,master, style=style, **kw)
        self._popup_index = None
        self.pressed_index = None

        #标签页点击关闭按钮事件
        self.bind("<ButtonPress-1>", self._letf_btn_press, True)
        self.bind("<ButtonRelease-1>", self._left_btn_release, True)

        # self._check_update_style()

    def _letf_btn_press(self, event):
        try:
            elem = self.identify(event.x, event.y)
            index = self.index("@%d,%d" % (event.x, event.y))

            if "closebutton" in elem:
                self.state(["pressed"])
                self.pressed_index = index
        except Exception:
            # may fail, if clicked outside of tab
            return

    def _left_btn_release(self, event):
        if not self.instate(["pressed"]):
            return

        try:
            elem = self.identify(event.x, event.y)
            index = self.index("@%d,%d" % (event.x, event.y))
        except Exception:
            # may fail, when mouse is dragged
            return
        else:
            if "closebutton" in elem and self.pressed_index == index:
                self.close_tab(index)

            self.state(["!pressed"])
        finally:
            self.pressed_index = None

    def GetPageCount(self):
        return len(self.tabs())
        
    def _close_tab_from_menu(self):
        self.close_tab(self._popup_index)

    def _close_other_tabs(self):
        self.close_tabs(self._popup_index)

    def close_tabs(self, except_index=None):
        for tab_index in reversed(range(len(self.winfo_children()))):
            if except_index is not None and tab_index == except_index:
                continue
            else:
                self.close_tab(tab_index)

    def close_tab(self, index):
        '''
            点击标签页关闭窗口事件,如果子类窗口实现了close方法,则调用子窗口关闭标签事件
        '''
        child = self.get_child_by_index(index)
        if hasattr(child, "close"):
            child.close()
        else:
            self.forget(index)
            child.destroy()
            
    def close_child(self,child):
        assert(self.has_child(child))
        self.forget(child)
        child.destroy()
        
    def has_child(self,child):
        childs = self.winfo_children()
        return child in childs

    def get_child_by_index(self, index):
        tab_id = self.tabs()[index]
        if tab_id:
            return self.nametowidget(tab_id)
        else:
            return None

    def get_current_child(self):
        child_id = self.select()
        if child_id:
            return self.nametowidget(child_id)
        else:
            return None

    def focus_set(self):
        editor = self.get_current_child()
        if editor:
            editor.focus_set()
        else:
            ttk.Notebook.focus_set(self)

    def _check_update_style(self):
        style = ttk.Style()
        if "closebutton" in style.element_names():
            # It's done already
            return

        # respect if required images have been defined already
        if "img_close" not in self.image_names():
            img_dir = os.path.join(os.path.dirname(__file__), "res")
            ClosableNotebook._close_img = tk.PhotoImage(
                "img_tab_close", file=os.path.join(img_dir, "tab_close.gif")
            )
            ClosableNotebook._close_active_img = tk.PhotoImage(
                "img_tab_close_active",
                file=os.path.join(img_dir, "tab_close_active.gif"),
            )

        style.element_create(
            "closebutton",
            "image",
            "img_tab_close",
            ("active", "pressed", "!disabled", "img_tab_close_active"),
            ("active", "!disabled", "img_tab_close_active"),
            border=8,
            sticky="",
        )

        style.layout(
            "ButtonNotebook.TNotebook.Tab",
            [
                (
                    "Notebook.tab",
                    {
                        "sticky": "nswe",
                        "children": [
                            (
                                "Notebook.padding",
                                {
                                    "side": "top",
                                    "sticky": "nswe",
                                    "children": [
                                        (
                                            "Notebook.focus",
                                            {
                                                "side": "top",
                                                "sticky": "nswe",
                                                "children": [
                                                    (
                                                        "Notebook.label",
                                                        {"side": "left", "sticky": ""},
                                                    ),
                                                    (
                                                        "Notebook.closebutton",
                                                        {"side": "left", "sticky": ""},
                                                    ),
                                                ],
                                            },
                                        )
                                    ],
                                },
                            )
                        ],
                    },
                )
            ],
        )
        

def get_text_font(text):
    font = text["font"]
    if isinstance(font, str):
        return tkfont.nametofont(font)
    else:
        return font

class TextviewFrame(ttk.Frame):
    "Decorates text with scrollbars, line numbers and print margin"

    def __init__(
        self,
        master,
        line_numbers=False,
        line_length_margin=0,
        first_line_number=1,
        text_class=tk.Text,
        horizontal_scrollbar=True,
        vertical_scrollbar=True,
        vertical_scrollbar_class=ttk.Scrollbar,
        horizontal_scrollbar_class=ttk.Scrollbar,
        vertical_scrollbar_style=None,
        horizontal_scrollbar_style=None,
        borderwidth=0,
        relief="sunken",
        gutter_background="#e0e0e0",
        gutter_foreground="#999999",
        **text_options
    ):
        '''
            line_numbers:是否显示行号
            line_length_margin:为0表示不显示边界线,否则显示边界线
        '''
        ttk.Frame.__init__(self, master=master, borderwidth=borderwidth, relief=relief)

        final_text_options = {
            "borderwidth": 0,
            "insertwidth": 2,
            "spacing1": 0,
            "spacing3": 0,
            "highlightthickness": 0,
            "inactiveselectbackground": "gray",
            "padx": 5,
            "pady": 5,
        }
        final_text_options.update(text_options)
        self.text = text_class(self, **final_text_options)
        self.text.grid(row=0, column=2, sticky=tk.NSEW)
        self.bp_margin = tk.Text(
            self,
            width=2,
            padx=0,
            pady=5,
            highlightthickness=0,
            bd=0,
            takefocus=False,
            font=self.text["font"],
            background="#e0e0e0",
            foreground=gutter_foreground,
            selectbackground=gutter_background,
            selectforeground=gutter_foreground,
            cursor="arrow",
            state="disabled",
            undo=False,
            wrap="none",
        )
        self.bp_margin.grid(row=0, column=0, sticky=tk.NSEW)
        self.bp_bmp = imageutils.load_image("","python/debugger/breakmark.png")
        self._gutter = tk.Text(
            self,
            width=5,
            padx=0,
            pady=5,
            highlightthickness=0,
            bd=0,
            takefocus=False,
            font=self.text["font"],
            background="#e0e0e0",
            foreground=gutter_foreground,
            selectbackground=gutter_background,
            selectforeground=gutter_foreground,
            cursor="arrow",
            state="disabled",
            undo=False,
            wrap="none",
        )
        self._gutter.bind("<ButtonRelease-1>", self.on_gutter_click)
        self._gutter.bind("<Button-1>", self.on_gutter_click)
        self._gutter.bind("<Button1-Motion>", self.on_gutter_motion)
        self._gutter["yscrollcommand"] = self._gutter_scroll

        # need tags for justifying and rmargin
        self._gutter.tag_configure("content", justify="right", rmargin=3)

        # gutter will be gridded later
        assert first_line_number is not None
        self._first_line_number = first_line_number
        self.set_gutter_visibility(line_numbers)

        if vertical_scrollbar:
            self._vbar = vertical_scrollbar_class(
                self, orient=tk.VERTICAL, style=vertical_scrollbar_style
            )
            self._vbar.grid(row=0, column=3, sticky=tk.NSEW)
            self._vbar["command"] = self._vertical_scroll
            self.text["yscrollcommand"] = self._vertical_scrollbar_update

        if horizontal_scrollbar:
            self._hbar = horizontal_scrollbar_class(
                self, orient=tk.HORIZONTAL, style=horizontal_scrollbar_style
            )
            self._hbar.grid(row=1, column=0, sticky=tk.NSEW, columnspan=3)
            self._hbar["command"] = self._horizontal_scroll
            self.text["xscrollcommand"] = self._horizontal_scrollbar_update

        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        self._recommended_line_length = line_length_margin
        margin_line_color = ttk.Style().lookup(
            "Gutter", "background", default="LightGray"
        )
        #垂直的代码边界线
        self._margin_line = tk.Canvas(
            self.text,
            borderwidth=0,
            width=1,
            height=2000,
            highlightthickness=0,
            background=margin_line_color,
        )
        self.update_margin_line()

        self.text.bind("<<TextChange>>", self._text_changed, True)
        self.text.bind("<<CursorMove>>", self._cursor_moved, True)

        self._ui_theme_change_binding = self.bind(
            "<<ThemeChanged>>", self._reload_theme_options, True
        )
        self._reload_theme_options()

        # TODO: add context menu?

    def focus_set(self):
        self.text.focus_set()

    def set_gutter_visibility(self, value):
        if value and not self._gutter.winfo_ismapped():
            self._gutter.grid(row=0, column=1, sticky=tk.NSEW)
        elif not value and self._gutter.winfo_ismapped():
            self._gutter.grid_forget()

        # insert first line number (NB! Without trailing linebreak. See update_gutter)
        self._gutter.config(state="normal")
        self.bp_margin.config(state="normal")
        self._gutter.delete("1.0", "end")
        self.bp_margin.delete("1.0", "end")
        for content, tags in self.compute_gutter_line(self._first_line_number):
            self._gutter.insert("end", content, ("content",) + tags)
            self.bp_margin.insert("end", '', ("content",) + tags)
        self._gutter.config(state="disabled")
        self.bp_margin.config(state="disabled")

        self.update_gutter()

    def set_line_length_margin(self, value):
        self._recommended_line_length = value
        self.update_margin_line()

    def _text_changed(self, event):
        "# TODO: make more efficient"
        self.update_gutter()
        self.update_margin_line()

    def _cursor_moved(self, event):
        self._update_gutter_active_line()

    def _vertical_scrollbar_update(self, *args):
        self._vbar.set(*args)
        self._gutter.yview(tk.MOVETO, args[0])
        self.bp_margin.yview(tk.MOVETO, args[0])

    def _gutter_scroll(self, *args):
        # FIXME: this doesn't work properly
        # Can't scroll to bottom when line numbers are not visible
        # and can't type normally at the bottom, when line numbers are visible
        return
        # self._vbar.set(*args)
        # self.text.yview(tk.MOVETO, args[0])

    def _horizontal_scrollbar_update(self, *args):
        self._hbar.set(*args)
        self.update_margin_line()

    def _vertical_scroll(self, *args):
        self.text.yview(*args)
        self._gutter.yview(*args)
        self.bp_margin.yview(*args)

    def _horizontal_scroll(self, *args):
        self.text.xview(*args)
        self.update_margin_line()

    def update_gutter(self, clean=True):
        # TODO: make it more efficient
        # by default clean only if line counts in gutter and text differ

        if clean:
            self._gutter.config(state="normal")
            self.bp_margin.config(state="normal")
            self._gutter.delete("1.0", "end")
            self.bp_margin.delete("1.0", "end")
            # need to add first item separately, because Text can't report 0 rows
            for content, tags in self.compute_gutter_line(self._first_line_number):
                self._gutter.insert("end-1c", content, tags + ("content",))
                self.bp_margin.insert("end", '', ("content",) + tags)

            self._gutter.config(state="disabled")
            self.bp_margin.config(state="disabled")

        text_line_count = int(self.text.index("end").split(".")[0])
        gutter_line_count = int(self._gutter.index("end").split(".")[0])

        if text_line_count != gutter_line_count:
            self._gutter.config(state="normal")
            self.bp_margin.config(state="normal")

            # NB! Text acts weird with last symbol
            # (don't really understand whether it automatically keeps a newline there or not)
            # Following seems to ensure both Text-s have same height
            if text_line_count > gutter_line_count:
                delta = text_line_count - gutter_line_count
                start = gutter_line_count + self._first_line_number - 1
                for i in range(start, start + delta):
                    self._gutter.insert("end-1c", "\n", ("content",))
                    self.bp_margin.insert("end-1c", "\n", ("content",))
                    for content, tags in self.compute_gutter_line(i):
                        self._gutter.insert("end-1c", content, ("content",) + tags)
                        self.bp_margin.insert("end-1c","",("content",) + tags)
            else:
                self._gutter.delete(line2index(text_line_count) + "-1c", "end-1c")
                self.bp_margin.delete(line2index(text_line_count) + "-1c", "end-1c")

            self._gutter.config(state="disabled")
            self.bp_margin.config(state="disabled")

        # synchronize gutter scroll position with text
        # https://mail.python.org/pipermail/tkinter-discuss/2010-March/002197.html
        first, _ = self.text.yview()
        self._gutter.yview_moveto(first)
        self.bp_margin.yview_moveto(first)
        self._update_gutter_active_line()

    def _update_gutter_active_line(self):
        self._gutter.tag_remove("active", "1.0", "end")
        insert = self.text.index("insert")
        self._gutter.tag_add("active", insert + " linestart", insert + " lineend")

    def compute_gutter_line(self, lineno):
        yield str(lineno), ("line_number",)

    def update_margin_line(self):
        if self._recommended_line_length == 0:
            self._margin_line.place_forget()
        else:
            try:
                self.text.update_idletasks()
                # How far left has text been scrolled
                first_visible_idx = self.text.index("@0,0")
                first_visible_col = int(first_visible_idx.split(".")[1])
                bbox = self.text.bbox(first_visible_idx)
                first_visible_col_x = bbox[0]

                margin_line_visible_col = (
                    self._recommended_line_length - first_visible_col
                )
                delta = first_visible_col_x
            except Exception:
                # fall back to ignoring scroll position
                margin_line_visible_col = self._recommended_line_length
                delta = 0

            if margin_line_visible_col > -1:
                x = (
                    get_text_font(self.text).measure(
                        (margin_line_visible_col - 1) * "M"
                    )
                    + delta
                    + self.text["padx"]
                )
            else:
                x = -10

            # print(first_visible_col, first_visible_col_x)

            self._margin_line.place(y=-10, x=x)

    def on_gutter_click(self, event=None):
        try:
            linepos = self._gutter.index("@%s,%s" % (event.x, event.y)).split(".")[0]
            self.text.mark_set("insert", "%s.0" % linepos)
            self._gutter.mark_set("gutter_selection_start", "%s.0" % linepos)
            if (
                event.type == "4"
            ):  # In Python 3.6 you can use tk.EventType.ButtonPress instead of "4"
                self.text.tag_remove("sel", "1.0", "end")
        except tk.TclError:
            exception("on_gutter_click")
            
    def on_gutter_motion(self, event=None):
        try:
            linepos = int(
                self._gutter.index("@%s,%s" % (event.x, event.y)).split(".")[0]
            )
            gutter_selection_start = int(
                self._gutter.index("gutter_selection_start").split(".")[0]
            )
            self.text.select_lines(
                min(gutter_selection_start, linepos),
                max(gutter_selection_start - 1, linepos - 1),
            )
            self.text.mark_set("insert", "%s.0" % linepos)
        except tk.TclError:
            exception("on_gutter_motion")

    def _reload_theme_options(self, event=None):

        style = ttk.Style()
        background = style.lookup("GUTTER", "background")
        if background:
            self._gutter.configure(background=background, selectbackground=background)
            self.bp_margin.configure(background=background, selectbackground=background)
            self._margin_line.configure(background=background)

        foreground = style.lookup("GUTTER", "foreground")
        if foreground:
            self._gutter.configure(foreground=foreground, selectforeground=foreground)

    def destroy(self):
        self.unbind("<<ThemeChanged>>", self._ui_theme_change_binding)
        ttk.Frame.destroy(self)
        

class TweakableText(tk.Text):
    """Allows intercepting Text commands at Tcl-level"""
    #read_only表示控件是否只读,只能查看数据不能写入数据
    def __init__(self, master=None, cnf={}, read_only=False, **kw):
        tk.Text.__init__(self,master=master, cnf=cnf, **kw)

        self._read_only = read_only
        self._suppress_events = False

        self._original_widget_name = self._w + "_orig"
        self.tk.call("rename", self._w, self._original_widget_name)
        self.tk.createcommand(self._w, self._dispatch_tk_operation)
        self._tk_proxies = {}

        self._original_insert = self._register_tk_proxy_function(
            "insert", self.intercept_insert
        )
        self._original_delete = self._register_tk_proxy_function(
            "delete", self.intercept_delete
        )
        self._original_mark = self._register_tk_proxy_function(
            "mark", self.intercept_mark
        )

    def _register_tk_proxy_function(self, operation, function):
        self._tk_proxies[operation] = function
        setattr(self, operation, function)

        def original_function(*args):
            self.tk.call((self._original_widget_name, operation) + args)

        return original_function

    def _dispatch_tk_operation(self, operation, *args):
        f = self._tk_proxies.get(operation)
        try:
            if f:
                return f(*args)
            else:
                return self.tk.call((self._original_widget_name, operation) + args)

        except TclError as e:
            # Some Tk internal actions (eg. paste and cut) can cause this error
            if (
                str(e).lower()
                == '''text doesn't contain any characters tagged with "sel"'''
                and operation in ["delete", "index", "get"]
                and args in [("sel.first", "sel.last"), ("sel.first",),("sel.last",)]
            ):

                pass
            else:
                utils.get_logger().exception(
                    "[_dispatch_tk_operation] operation: "
                    + operation
                    + ", args:"
                    + repr(args)
                )
                # traceback.print_exc()

            return ""  # Taken from idlelib.WidgetRedirector

    def set_read_only(self, value):
        self._read_only = value

    def is_read_only(self):
        return self._read_only

    def set_content(self, chars):
        self.direct_delete("1.0", tk.END)
        self.direct_insert("1.0", chars)

    def set_insertwidth(self, new_width):
        """Change cursor width
        
        NB! Need to be careful with setting text["insertwidth"]!
        My first straightforward solution caused unexplainable
        infinite loop of insertions and deletions in the text
        (Repro: insert a line and a word, select that word and then do Ctrl-Z).
        
        This solution seems safe but be careful!
        """
        if self._suppress_events:
            return

        if self["insertwidth"] != new_width:
            old_suppress = self._suppress_events
            try:
                self._suppress_events = True
                self.config(insertwidth=new_width)
            finally:
                self._suppress_events = old_suppress

    def intercept_mark(self, *args):
        self.direct_mark(*args)

    def intercept_insert(self, index, chars, tags=None, **kw):
###        assert isinstance(chars, str)
        if (
            chars >= "\uf704" and chars <= "\uf70d"
        ):  # Function keys F1..F10 in Mac cause these
            pass
        elif self.is_read_only():
            self.bell()
        else:
            self.direct_insert(index, chars, tags, **kw)

    def intercept_delete(self, index1, index2=None, **kw):
        if index1 == "sel.first" and index2 == "sel.last" and not self.has_selection():
            return

        if self.is_read_only():
            self.bell()
        elif self._is_erroneous_delete(index1, index2):
            pass
        else:
            self.direct_delete(index1, index2, **kw)

    def _is_erroneous_delete(self, index1, index2):
        """Paste can cause deletes where index1 is sel.start but text has no selection. This would cause errors"""
        return index1.startswith("sel.") and not self.has_selection()

    def direct_mark(self, *args):
        self._original_mark(*args)

        if args[:2] == ("set", "insert") and not self._suppress_events:
            self.event_generate("<<CursorMove>>")

    def index_sel_first(self):
        # Tk will give error without this check
        if self.tag_ranges("sel"):
            return self.index("sel.first")
        else:
            return None

    def index_sel_last(self):
        if self.tag_ranges("sel"):
            return self.index("sel.last")
        else:
            return None

    def has_selection(self):
        return len(self.tag_ranges("sel")) > 0

    def get_selection_indices(self):
        # If a selection is defined in the text widget, return (start,
        # end) as Tkinter text indices, otherwise return (None, None)
        if self.has_selection():
            return self.index("sel.first"), self.index("sel.last")
        else:
            return None, None

    def direct_insert(self, index, chars, tags=None, **kw):
        self._original_insert(index, chars, tags, **kw)
        if not self._suppress_events:
            self.event_generate("<<TextChange>>")

    def direct_delete(self, index1, index2=None, **kw):
        self._original_delete(index1, index2, **kw)
        if not self._suppress_events:
            self.event_generate("<<TextChange>>")
            

class SafeScrollbar(ttk.Scrollbar):
    def __init__(self, master=None, **kw):
        ttk.Scrollbar.__init__(self,master=master, **kw)

    def set(self, first, last):
        try:
            ttk.Scrollbar.set(self, first, last)
        except Exception:
            pass
            
class OutlineView(ttk.Frame):
    #不排序
    SORT_BY_NONE = 0
    #以行号排序
    SORT_BY_LINE = 1
    #以名称排序
    SORT_BY_NAME = 2
    #以类型排序
    SORT_BY_TYPE = 3

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self._init_widgets()
        self.menu = None

        self._tab_changed_binding = (GetApp().MainFrame.GetNotebook().bind("<<NotebookTabChanged>>", self._update_frame_contents, True))
        self.tree.bind("<3>", self.on_secondary_click, True)
        self._sortOrder = utils.profile_get_int("OutlineSort", self.SORT_BY_NONE)
        #当前在大纲中显示的文本视图
        self._callback_view = None
        #哪些视图类型允许在大纲中显示
        self._validViewTypes = []
        
    def GetCallbackView(self):
        return self._callback_view
        
    def SetCallbackView(self,view):
        self._callback_view = view

    def destroy(self):
        try:
            # Not sure if editor notebook is still living
            get_workbench().get_editor_notebook().unbind(
                "<<NotebookTabChanged>>", self._tab_changed_binding
            )
        except Exception:
            pass
        self.vert_scrollbar["command"] = None
        ttk.Frame.destroy(self)

    def _init_widgets(self):
        # init and place scrollbar
        self.vert_scrollbar = SafeScrollbar(self, orient=tk.VERTICAL)
        self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        # init and place tree
        self.tree = ttk.Treeview(self, yscrollcommand=self.vert_scrollbar.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.vert_scrollbar["command"] = self.tree.yview

        # set single-cell frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # init tree events
        self.tree.bind("<<TreeviewSelect>>", self._on_select, True)

        # configure the only tree column
        self.tree.column("#0", anchor=tk.W, stretch=True)
        # self.tree.heading('#0', text='Item (type @ line)', anchor=tk.W)
        self.tree["show"] = ("tree",)

    def _update_frame_contents(self, event=None):
        self._clear_tree()

    # clears the tree by deleting all items
    def _clear_tree(self):
        for child_id in self.tree.get_children():
            self.tree.delete(child_id)
            
    def on_secondary_click(self, event):
        if self.menu is None:
            self.menu = GetApp().Menubar.GetViewMenu().GetMenu(constants.ID_OUTLINE_SORT)
            self.menu["postcommand"] = lambda: self.menu._update_menu()
            
        node_id = self.tree.identify_row(event.y)
        if node_id:
            self.tree.selection_set(node_id)
            self.tree.focus(node_id)
        self.menu.tk_popup(event.x_root, event.y_root)
        
    def SortNode(self,node):
        # update tree
        children = self.tree.get_children(node)
        ids_sorted_by = py_sorted(children, cmp_func=self.OnCompareItems)
        #根节点排序特殊,需要删除原先的根节点再插入
        if node is None:
            for node in ids_sorted_by:
                text = self.tree.item(node,"text")
                new_node = self.tree.insert(
                    "", "end", text=text, values=self.tree.item(node)["values"], image=self.tree.item(node)['image']
                )
                #恢复根节点所有子节点
                childs = self.tree.get_children(node)
                self.tree.set_children(new_node, *childs)
                #删除原来的根节点
                self.tree.delete(node)
        else:
            self.tree.set_children(node, *ids_sorted_by)
        
    def OnCompareItems(self, item1, item2):
        #按行号排序
        if self._sortOrder == self.SORT_BY_LINE:
            line_1 = self.tree.item(item1)["values"][0]
            line_2 = self.tree.item(item2)["values"][0]
            return py_cmp(line_1, line_2)  # sort A-Z
        #按名称排序
        elif self._sortOrder == self.SORT_BY_NAME:
            return py_cmp(self.tree.item(item1,"text").lower(), self.tree.item(item2,"text").lower()) # sort Z-A
        #按类型排序
        elif self._sortOrder == self.SORT_BY_TYPE:
            type_1 = self.tree.item(item1)["values"][2]
            type_2 = self.tree.item(item2)["values"][2]
            return py_cmp(type_1, type_2)
        #未排序
        else:
            return -1
            return (self.tree.item(item1)["values"][0] > self.tree.item(item2)["values"][0]) # unsorted

    def Sort(self,sortOrder,node=None):
        if self._sortOrder == sortOrder:
            return
        self._sortOrder = sortOrder
        childs = self.tree.get_children(node)
        for child in childs:
            self.SortNode(child)
            self.Sort(sortOrder,child)
        self.SortNode(node)
        
    def AddViewTypeForBackgroundHandler(self, viewType):
        self._validViewTypes.append(viewType)

    def GetViewTypesForBackgroundHandler(self):
        return self._validViewTypes

    def RemoveViewTypeForBackgroundHandler(self, viewType):
        self._validViewTypes.remove(viewType)
        
    def IsValidViewType(self,currView):
        for viewType in self._validViewTypes:
            if isinstance(currView, viewType):
                return True
        return False

class DockFrame(ttk.Frame):
    def __init__(self, row,master=None,show=True,**kw):
        ttk.Frame.__init__(self, master, **kw)
        self._row = row
        self._is_show = show
        #复现菜单关联变量,通过这个变量控制复选菜单是否选中
        self.visibility_flag = tk.BooleanVar(value=bool(self._is_show))
        
    def Hide(self):
        self.grid_forget()
        self._is_show = False
        self.visibility_flag.set(False)
        
    def Show(self,show=True):
        if show:
            #设置状态栏和工具栏水平方向拉伸
            self.grid(column=0, row=self._row, sticky=tk.EW, padx=0, pady=0)
            self._is_show = True
            self.visibility_flag.set(True)
        else:
            self.Hide()
            
        
    def IsShown(self):
        return self._is_show
        
    @property
    def Row(self):
        return self._row
        
    @Row.setter
    def Row(self,row):
        self._row = row

class CommonDialog(tk.Toplevel):
    def __init__(self, master,**kwargs):
        tk.Toplevel.__init__(self, master,**kwargs)
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
    def CenterWindow(self):
        # looks like it doesn't take window border into account
        self.update_idletasks()

        if getattr(self.master, "initializing", False):
            # can't get reliable positions when main window is not in mainloop yet
            left = (self.winfo_screenwidth() - 600) // 2
            top = (self.winfo_screenheight() - 400) // 2
        else:
            if self.master is None:
                left = self.winfo_screenwidth() - win.winfo_width() // 2
                top = self.winfo_screenheight() - win.winfo_height() // 2
            else:
                left = (
                    self.master.winfo_rootx()
                    + self.master.winfo_width() // 2
                    - self.winfo_width() // 2
                )
                top = (
                    self.master.winfo_rooty()
                    + self.master.winfo_height() // 2
                    - self.winfo_height() // 2
                )

        self.geometry("+%d+%d" % (left, top))
        
    def FormatTkButtonText(self,btn):
        '''
            如果按钮文字包含&符号,去掉该符号不显示
        '''
        text = btn.configure()['text'][4]
        if text.find('&') != -1:
            btn.configure(text=text.replace("&",""))

class CommonModaldialog(CommonDialog):
    def __init__(self, master,**kwargs):
        CommonDialog.__init__(self, master,**kwargs)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.status = -1

    def ShowModal(self,center=True):
        if self.master is None:
            self.master = tk._default_root or GetApp()
        assert(self.master is not None)
        focused_widget = self.master.focus_get()
        if utils.is_linux() and focused_widget is not None:
            #在linux系统点击工具栏新建按钮后,提示信息会一直存在不会消失,手动隐藏提示信息
            focused_widget.event_generate("<Leave>")
        #隐藏最小化按钮
        self.transient(self.master)
        self.grab_set()
        self.lift()
        self.focus_set()
        if center:
            self.CenterWindow()
        self.master.wait_window(self)
        self.grab_release()
        self.master.lift()
        self.master.focus_force()
        if focused_widget is not None:
            try:
                focused_widget.focus_set()
            except tk.TclError:
                pass
            
        return self.status

    def _ok(self, event=None):
        if str(self.ok_button['state']) == tk.DISABLED:
            return
        self.status = constants.ID_OK
        self.destroy()
        
    def _cancel(self, event=None):
        self.status = constants.ID_CANCEL
        self.destroy()
        
    def AddokcancelButton(self,side=None):
        bottom_frame = ttk.Frame(self.main_frame)
        if side is None:
            bottom_frame.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        else:
            bottom_frame.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),side=side,expand=1)
        self.AppendokcancelButton(bottom_frame)
        
    def AppendokcancelButton(self,bottom_frame):
        space_label = ttk.Label(bottom_frame,text="")
        space_label.grid(column=0, row=0, sticky=tk.EW, padx=(consts.DEFAUT_CONTRL_PAD_X, consts.DEFAUT_CONTRL_PAD_X), pady=consts.DEFAUT_CONTRL_PAD_Y)
        self.ok_button = ttk.Button(bottom_frame, text=_("&OK"), command=self._ok,default=tk.ACTIVE,takefocus=1)
        self.ok_button.grid(column=1, row=0, sticky=tk.EW, padx=(0, consts.DEFAUT_CONTRL_PAD_X), pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.cancel_button = ttk.Button(bottom_frame, text=_("Cancel"), command=self._cancel)
        self.cancel_button.grid(column=2, row=0, sticky=tk.EW, padx=(0, consts.DEFAUT_CONTRL_PAD_X), pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.FormatTkButtonText(self.ok_button)
        self.FormatTkButtonText(self.cancel_button)
        bottom_frame.columnconfigure(0, weight=1)
        self.ok_button.focus_set()
        #设置回车键关闭对话框
        self.ok_button.bind("<Return>", self._ok, True)
        self.cancel_button.bind("<Return>", self._cancel, True)

class SingleChoiceDialog(CommonModaldialog):
    def __init__(self, master,title,label,choices = [],selection=-1,show_scrollbar=False):
        CommonModaldialog.__init__(self, master, takefocus=1)
        self.title(title)
        #禁止对话框改变大小
        self.resizable(height=tk.FALSE, width=tk.FALSE)
        label_ctrl = ttk.Label(self.main_frame,text=label)
        label_ctrl.pack(expand=1, fill="x",padx = consts.DEFAUT_CONTRL_PAD_X,pady = consts.DEFAUT_CONTRL_PAD_Y)
        
        v = tk.StringVar()
        #设置listbox的高度最小为5个文本,最多为10个的大小
        #如果数量过得时可以设置滚动条,默认不显示滚动条
      #  self.listbox = tk.Listbox(self.main_frame,listvariable=v,height=max(min(len(choices),10),5))
        listview = listboxframe.ListboxFrame(self.main_frame,show_scrollbar=show_scrollbar,listvariable=v,height=max(min(len(choices),10),5))
        self.listbox = listview.listbox
        #listbox双击事件,设置双击等价于点击ok按钮
        self.listbox.bind('<Double-Button-1>',self._ok)
        v.set(tuple(choices))
        if selection == -1:
            selection = 0
        self.listbox.selection_set(selection)
        listview.pack(expand=1, fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        
        separator = ttk.Separator (self.main_frame, orient = tk.HORIZONTAL)
        separator.pack(expand=1, fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady = (consts.DEFAUT_CONTRL_PAD_Y,0))
        
        self.AddokcancelButton()
        self.status = -1

    def _ok(self, event=None):
        self.selection = self.GetStringSelection()
        CommonModaldialog._ok(self,event)
        
    def GetStringSelection(self):
        return self.listbox.get(self.listbox.curselection()[0])

def GetSingleChoiceIndex(parent,title,label,strings,default_selection):
    dlg = SingleChoiceDialog(parent ,title,label,strings,default_selection) 
    if dlg.ShowModal() == constants.ID_OK:  
        name = dlg.selection
        index = strings.index(name)
        return index
    return -1
        
def GetNewDocumentChoiceIndex(parent,strings,default_selection):
    return GetSingleChoiceIndex(parent,_("New Document"),_("Select a document type:"),strings,default_selection)

class GenericProgressDialog(CommonModaldialog):
    
    def __init__(self,master,title,maximum=100,mode="determinate",length=400,info=""):
        CommonModaldialog.__init__(self, master, takefocus=1)
        self.title(title)
        self.label_var = tk.StringVar(value=info)
        self.label_ctrl = ttk.Label(self.main_frame,textvariable=self.label_var,width=30)
        self.label_ctrl.pack(fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X, consts.DEFAUT_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.cur_val = tk.IntVar(value=0)
        if mode == "determinate":
            self.mpb = ttk.Progressbar(self.main_frame, orient="horizontal", length=length, mode=mode,variable=self.cur_val,maximum=maximum)
        else:
            self.mpb = ttk.Progressbar(self.main_frame, mode=mode, length=length)
        self.mpb.pack(fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X, consts.DEFAUT_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        
        self.cancel_button = ttk.Button(
            self.main_frame, text=_("Cancel"), command=self.Cancel
        )
        self.cancel_button.pack(side=tk.RIGHT,fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,consts.DEFAUT_CONTRL_PAD_X), pady=(consts.DEFAUT_CONTRL_PAD_Y, consts.DEFAUT_CONTRL_PAD_Y))
        self.keep_going = True
        self.is_cancel = False
        self.protocol("WM_DELETE_WINDOW", self.Cancel)
    
    def SetRange(self,value):
        self.mpb["maximum"] = value
        
    def Cancel(self):
        self.keep_going = False
        self.is_cancel = True
        self.cancel_button['state'] = tk.DISABLED
        
    def SetValue(self,val):
        assert(type(val) == int)
        self.cur_val.set(val)
        
    def SetInfo(self,info):
        self.label_var.set(info)
        
    def GetMaximum(self):
        return self.mpb["maximum"]
        

class SplashScreen(CommonDialog):
    def __init__(self, master,image_path,stay=1):
        self.stay = stay
        CommonDialog.__init__(self, master,background="white")
        #隐藏对话框标题栏
        self.overrideredirect(True)
        #窗口置顶
        self.wm_attributes('-topmost',1)
        self.img = imageutils.load_image("",image_path)
        self.geometry("{}x{}".format(self.img.width(), self.img.height()))
        label = tk.Label(self.main_frame, image=self.img,compound='center',bg="white")
        #label = tk.Label(self, image=self.img,compound='center')
        label.pack(fill="both")

    def Show(self):
        self.CenterWindow()
        
    def Close(self):
        assert(isinstance(self.stay,int))
        if self.stay > 0:
            GetApp().after(self.stay*1000,self.destroy)
        else:
            self.destroy()
       
    def destroy(self):
        #最大化并显示隐藏的主窗口,同时关闭启动窗口
        tk.Toplevel.destroy(self)
        GetApp().MaxmizeWindow()
        GetApp().update()
        GetApp().RaiseWindow()
        GetApp().attributes("-alpha", 100)