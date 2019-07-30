# -*- coding: utf-8 -*-
import os.path
import tempfile
import webbrowser
import platform
import subprocess
from noval import GetApp,_
import noval.iface as iface
import noval.plugin as plugin
import noval.constants as constants
import noval.util.utils as utils

def print_current_script():
    editor = _get_current_editor()
    assert editor is not None

    template_fn = os.path.join(os.path.dirname(__file__), "template.html")
    kwargs = {}
    if utils.is_py3_plus():
        kwargs = dict(encoding="utf-8")

    with open(template_fn,**kwargs) as f:
        template_html = f.read()


    script_html = _export_text_as_html(editor.GetView().GetCtrl())
    title_html = escape_html(os.path.basename(editor.GetView().GetDocument().GetFilename()))
    full_html = template_html.replace("%title%", title_html).replace("%script%", script_html)

    temp_handle, temp_fn = tempfile.mkstemp(suffix=".html", prefix="novalide_")
    with os.fdopen(temp_handle, "w", **kwargs) as f:
        f.write(full_html)

    if platform.system() == "Darwin":
        subprocess.Popen(["open", temp_fn])
    else:
        webbrowser.open(temp_fn)


def can_print_current_script():
    if not GetApp().UpdateUI(constants.ID_PRINT):
        return False
    active_view = GetApp().GetDocumentManager().GetCurrentView()
    if hasattr(active_view,"GetLangId"):
        return True
    return False

def _export_text_as_html(text):
    last_line = int(float(text.index("end-1c")))
    result = ""
    for i in range(1, last_line + 1):
        result += "<code>" + _export_line_as_html(text, i) + "</code>\n"
    return result


def _export_line_as_html(text, lineno):
    s = text.get("%d.0" % lineno, "%d.0 lineend" % lineno).strip("\r\n")

    parts = []
    for i in range(len(s)):
        tag_names = text.tag_names("%d.%d" % (lineno, i))
        if not parts or parts[-1][1] != tag_names:
            parts.append([s[i], tag_names])
        else:
            parts[-1][0] += s[i]

    # print(lineno, parts)
    result = ""
    for s, tags in parts:
        if tags:
            result += "<span class='%s'>%s</span>" % (" ".join(tags), escape_html(s))
        else:
            result += escape_html(s)

    return result


def escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _get_current_editor():
    return GetApp().MainFrame.GetNotebook().get_current_editor()

class FilePrinterPluginLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        menuBar = GetApp().Menubar
        file_menu = menuBar.GetFileMenu()
        menu_item = GetApp().InsertCommand(constants.ID_EXIT,constants.ID_PRINT,_("&File"),_("Print..."),handler=print_current_script,tester=can_print_current_script,pos="before",image="toolbar/print.png")
        GetApp().MainFrame.GetToolBar().AddButton(constants.ID_PRINT,menu_item.image,_("Print"),handler=print_current_script,tester=menu_item.tester,pos=4,accelerator=menu_item.accelerator)
        #使用默认tester函数,必须添加到默认id列表中
        GetApp().AppendDefaultCommand(constants.ID_PRINT)