# -*- coding: utf-8 -*-
from noval import _,NewId,GetApp
import json
import logging
import os
import re
import subprocess
import sys
import tkinter as tk
import webbrowser
from distutils.version import LooseVersion, StrictVersion
from logging import exception
from os import makedirs
from tkinter import messagebox, ttk,filedialog
from tkinter.messagebox import showerror
import noval.ui_base as ui_base
import noval.iface as iface
import noval.plugin as plugin
import noval.constants as constants
import noval.util.utils as utils
import noval.misc as misc
import noval.ui_utils as ui_utils
import noval.ui_common as ui_common
import noval.consts as consts
from dummy.userdb import UserDataDb
import noval.util.fileutils as fileutils
import noval.util.strutils as strutils
import site
import noval.python.interpreter.interpretermanager as interpretermanager
import intellisence
import pkg_resources
import noval.python.pyutils as pyutils
import noval.util.downutils as downutils
import shutil
import noval.python.parser.utils as parserutils
import noval.python.interpreter.pythonpackages as pythonpackages
import noval.plugins.update as updateutils
import noval.editor.text as texteditor
import noval.util.urlutils as urlutils
import noval.preference as preference
import inspect
import noval.auth.register as register

#找回pip工具的url地址
PIP_INSTALLER_URL = "https://bootstrap.pypa.io/get-pip.py"

def GetAllPackages(find_name=None):
    '''
        获取所有pypi包名称列表
    '''
    #包列表信息存储在用户数据目录下的pypi_packages.txt文件中
    cache_path = utils.get_cache_path()
    package_data_path = os.path.join(cache_path,"pypi_packages.txt")
    if not os.path.exists(package_data_path):
        return []
    names = []
    with open(package_data_path) as f:
        for line in f:
            normal_name = line.strip()
            if find_name is None or normal_name.lower().find(find_name) != -1:
                names.append(normal_name)
    return names
    
def GetAllPlugins(find_name=None,message=None,plugin_dlg=None,aync=False):
    '''
        异步或同步请求获取所有插件名称列表
    '''
    def end(data):
        if message:
            message['msg'] = _("There is total %d plugins on Server")%len(data['names'])
            if plugin_dlg:
                plugin_dlg.label_var.set(message['msg'])
        
    def error(data):
        if message:
            message['msg'] = _("can't fetch plugin from Server")
            if plugin_dlg:
                plugin_dlg.label_var.set(message['msg'])
        
    api_addr = '%s/member/get_plugins' % (UserDataDb.HOST_SERVER_ADDR)
    if aync:
        urlutils.fetch_url_future(api_addr,method='get',arg={'name':find_name},callback=end,error_callback=error)
    else:
        data = utils.RequestData(api_addr,method='get',arg={'name':find_name})
        if data:
            return data['names']
        return []
        
def GetPluginInstallpath():
    #调式模式时默认安装到应用程序目录(系统目录)
    #正常时默认安装到用户目录
    if GetApp().GetDebug():
        #系统目录(软件安装目录)
        value = utils.get_sys_plugin_path()
    else:
        #用户数据目录
        value = utils.get_user_plugin_path()
    plugin_install_path = utils.profile_get("PluginInstallPath",value)
    return plugin_install_path

class PipDialog(ui_base.CommonModaldialog):
    def __init__(self, master,package_count,message=None):
        self._state = "idle"  # possible values: "listing", "fetching", "idle"
        self._process = None
        self._active_distributions = {}
        #当前选中的包的信息
        self.current_package_data = {}
        self.package_count = package_count
        ui_base.CommonModaldialog.__init__(self,master)

        main_frame = ttk.Frame(self)
        main_frame.grid(sticky=tk.NSEW, ipadx=15, ipady=15)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.title(self._get_title())
        if package_count > 0:
           total_package_msg =  _("There is total %d packages on PyPI")%self.package_count
        else:
            total_package_msg = message
        self._create_widgets(main_frame,_("Installed Packages:"),_("Find package from PyPI"),total_package_msg,_("input the package name to search..."))

        self.search_box.focus_set()

        self.bind("<Escape>", self._cancel, True)
#        self._show_instructions()

        self._start_update_list()
        
    def CreateBottomLabel(self,parent,label_text):
        pass

    def _create_widgets(self,parent,install_label_text,button_text,label_text,tip_text):

        header_frame = ttk.Frame(parent)
        header_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(15, 0))
        header_frame.columnconfigure(0, weight=1)
        header_frame.rowconfigure(1, weight=1)

        name_font = tk.font.nametofont("TkDefaultFont").copy()
        name_font.configure(size=16)
        self.search_box = ttk.Entry(header_frame)
        misc.create_tooltip(self.search_box,tip_text)
        self.search_box.grid(row=1, column=0, sticky="nsew")
        self.search_box.bind("<Return>", self._on_search, False)

        self.search_button = ttk.Button(
            header_frame, text=button_text, command=self._on_search, width=25
        )
        self.search_button.grid(row=1, column=1, sticky="nse", padx=(10, 0))

        main_pw = tk.PanedWindow(
            parent,
            orient=tk.HORIZONTAL,
            background=misc.lookup_style_option("TPanedWindow", "background"),
            sashwidth=15,
        )
        main_pw.grid(row=2, column=0, sticky="nsew", padx=15, pady=(15,consts.DEFAUT_CONTRL_PAD_Y))
        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)
        self.CreateBottomLabel(parent,label_text)
        
        listframe = ttk.Frame(main_pw, relief="flat", borderwidth=1)
        listframe.rowconfigure(1, weight=1)
        listframe.columnconfigure(1, weight=1)
        #显示安装包标签
        self.installled_var = tk.StringVar(value=install_label_text)
        self.install_label_text = install_label_text
        installled_label = ttk.Label(listframe, textvariable=self.installled_var)
        installled_label.grid(row=0, column=0, sticky="w")
        self.listbox = ui_utils.ThemedListbox(
            listframe,
            activestyle="dotbox",
            width=20,
            height=20,
            selectborderwidth=0,
            relief="flat",
            # highlightthickness=4,
            # highlightbackground="red",
            # highlightcolor="green",
            borderwidth=0,
        )
        self.listbox.insert("end", " <INSTALL>")
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select, True)
        self.listbox.grid(row=1, column=0, sticky="nsew")
        list_scrollbar = ui_common.AutoScrollbar(
            listframe, orient=tk.VERTICAL, style=None
        )
        list_scrollbar.grid(row=1, column=1, sticky="ns")
        list_scrollbar["command"] = self.listbox.yview
        self.listbox["yscrollcommand"] = list_scrollbar.set

        info_frame = ttk.Frame(main_pw)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(1, weight=1)

        main_pw.add(listframe)
        main_pw.add(info_frame)

        self.name_label = ttk.Label(info_frame, text="", font=name_font)
        self.name_label.grid(row=0, column=0, sticky="w", padx=5)

        #用文本控件显示包详细信息,并且设置为只读
        info_text_frame = ui_base.TextviewFrame(
            info_frame,
            read_only=True,
            horizontal_scrollbar=False,
            background=misc.lookup_style_option("TFrame", "background"),
            vertical_scrollbar_class=ui_common.AutoScrollbar,
            vertical_scrollbar_style=None,
            horizontal_scrollbar_style=None,
            width=70,
            height=10,
            text_class = texteditor.TextCtrl
        )
        info_text_frame.configure(borderwidth=0)
        info_text_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=(0, 10))
        self.info_text = info_text_frame.text
        link_color = misc.lookup_style_option("Url.TLabel", "foreground", "red")
        self.info_text.tag_configure("url", foreground=link_color, underline=True)
        self.info_text.tag_bind("url", "<ButtonRelease-1>", self._handle_url_click)
        self.info_text.tag_bind("url", "<Enter>", lambda e: self.info_text.config(cursor="hand2"))
        self.info_text.tag_bind("url", "<Leave>", lambda e: self.info_text.config(cursor=""))
        self.info_text.tag_configure("install_reqs", foreground=link_color, underline=True)
        self.info_text.tag_bind(
            "install_reqs", "<ButtonRelease-1>", self._handle_install_requirements_click
        )
        self.info_text.tag_bind(
            "install_reqs", "<Enter>", lambda e: self.info_text.config(cursor="hand2")
        )
        self.info_text.tag_bind(
            "install_reqs", "<Leave>", lambda e: self.info_text.config(cursor="")
        )
        self.info_text.tag_configure("install_file", foreground=link_color, underline=True)
        self.info_text.tag_bind(
            "install_file", "<ButtonRelease-1>", self._handle_install_file_click
        )
        self.info_text.tag_bind(
            "install_file", "<Enter>", lambda e: self.info_text.config(cursor="hand2")
        )
        self.info_text.tag_bind(
            "install_file", "<Leave>", lambda e: self.info_text.config(cursor="")
        )

        default_font = tk.font.nametofont("TkDefaultFont")
        self.info_text.configure(font=default_font, wrap="word")

        bold_font = default_font.copy()
        # need to explicitly copy size, because Tk 8.6 on certain Ubuntus use bigger font in copies
        bold_font.configure(weight="bold", size=default_font.cget("size"))
        self.info_text.tag_configure("caption", font=bold_font)
        self.info_text.tag_configure("bold", font=bold_font)

        self.command_frame = ttk.Frame(info_frame)
        self.command_frame.grid(row=2, column=0, sticky="w")

        self.install_button = ttk.Button(
            self.command_frame, text=_(" Upgrade "), command=self._on_click_install
        )

        self.install_button.grid(row=0, column=0, sticky="w", padx=0)

        self.uninstall_button = ttk.Button(
            self.command_frame,
            text=_("Uninstall"),
            command=lambda: self._perform_action("uninstall"),
        )

        self.uninstall_button.grid(row=0, column=1, sticky="w", padx=(5, 0))
        self.create_advance_buttons()
        self.close_button = ttk.Button(info_frame, text=_("Close"), command=self._cancel)
        self.close_button.grid(row=2, column=3, sticky="e")
        
    def create_advance_buttons(self):
        '''
            创建其它按钮
        '''

    def _on_click_install(self):
        self._perform_action("install")

    def _set_state(self, state, force_normal_cursor=False):
        self._state = state
        widgets = [
            self.listbox,
            # self.search_box, # looks funny when disabled
            self.search_button,
            self.install_button,
            self.uninstall_button,
        ]

        if state == "idle":
            self.config(cursor="")
            for widget in widgets:
                widget["state"] = tk.NORMAL
        else:
            if force_normal_cursor:
                self.config(cursor="")
            else:
                self.config(cursor=ui_utils.get_busy_cursor())

            for widget in widgets:
                widget["state"] = tk.DISABLED

    def _get_state(self):
        return self._state

    def _handle_outdated_or_missing_pip(self, error):
        raise NotImplementedError()

    def _install_pip(self):
        self._clear()
        self.info_text.direct_insert("end", _("Installing pip\n\n"), ("caption",))
        self.info_text.direct_insert(
            "end",
            _(
                "pip, a required module for managing packages is missing or too old.\n\n"
                + "Downloading pip installer (about 1.5 MB), please wait ...\n"
            ),
        )
        self.update()
        self.update_idletasks()

        installer_filename, _ = urlretrieve(PIP_INSTALLER_URL)

        self.info_text.direct_insert("end", _("Installing pip, please wait ...\n"))
        self.update()
        self.update_idletasks()

        proc, _ = self._create_python_process([installer_filename], stderr=subprocess.PIPE)
        out, err = proc.communicate()
        os.remove(installer_filename)

        if err != "":
            raise RuntimeError("Error while installing pip:\n" + err)

        self.info_text.direct_insert("end", out + "\n")
        self.update()
        self.update_idletasks()

        # update list
        self._start_update_list()

    def _provide_pip_install_instructions(self, error):
        self._clear()
        self.info_text.direct_insert("end", error)
        self.info_text.direct_insert(
            "end", _("You seem to have problems with pip\n\n"), ("caption",)
        )
        self.info_text.direct_insert(
            "end",
            _(
                "pip, a required module for managing packages is missing or too old for Noval.\n\n"
                + "If your system package manager doesn't provide recent pip (9.0.0 or later), "
                + "then you can install newest version by downloading "
            ),
        )
        self.info_text.direct_insert("end", PIP_INSTALLER_URL, ("url",))
        self.info_text.direct_insert(
            "end",
            _(" and running it with ")
            + self._get_interpreter().Name
            + _(" (probably needs admin privileges).\n\n"),
        )

        self.info_text.direct_insert("end", self._instructions_for_command_line_install())
        self._set_state("disabled", True)

    def _instructions_for_command_line_install(self):
        return _(
            "Alternatively, if you have an older pip installed, then you can install packages "
            + "on the command line (Tools → Open terminator...)"
        )

    def _start_update_list(self, name_to_show=None,refresh=False):
        self.installled_var.set(self.install_label_text)
        
    def ShowNameList(self,names):
        self.listbox.delete(1, "end")
        for name in sorted(names):
            self.listbox.insert("end", " " + name)
            
    def _update_list(self, name_to_show):
        self.ShowNameList(self._active_distributions.keys())
        if name_to_show is None:
            self._show_instructions()
        else:
            self._start_show_package_info(name_to_show)

    def _on_listbox_select(self, event):
        self.listbox.focus_set()
        selection = self.listbox.curselection()
        if len(selection) == 1:
            self.listbox.activate(selection[0])
            if selection[0] == 0:  # special first item
                self._show_instructions()
            else:
                self._start_show_package_info(self.listbox.get(selection[0]).strip())
                
    def search_by_name(self,name):
        return []

    def _on_search(self, event=None):
        if self._get_state() != "idle":
            # Search box is not made inactive for busy-states
            return

        #搜索名称为空时显示已经安装的包列表
        if self.search_box.get().strip() == "":
            self._start_update_list()
            return
            
        #模糊搜索关键字
        search_name = self.search_box.get().strip()
        names = self.search_by_name(search_name)
        #列表框显示搜索结果
        self.ShowNameList(names)
        if not names:
            self._clear()
            self.NotFoundPackage(search_name)
            return
        #显示第一个包名
        self._start_show_package_info(names[0])

    def _clear(self):
        self.current_package_data = {}
        self.name_label.grid_remove()
        self.command_frame.grid_remove()
        self.info_text.direct_delete("1.0", "end")
        
    def _show_instructions(self):
        '''
            显示<INSTALL>提示信息
        '''
        
    def start_fetching_package_info(self,name):
        '''
            从pypi服务器上查询pypi包信息
        '''
        _start_fetching_package_info(name, None, self._show_package_info)

    def _start_show_package_info(self, name):
        self.current_package_data = {}
        # Fetch info from PyPI
        self._set_state("fetching")
        # Follwing fetches info about latest version.
        # This is OK even when we're looking an installed older version
        # because new version may have more relevant and complete info.
        self.info_text.direct_delete("1.0", "end")
        self.name_label["text"] = ""
        self.name_label.grid()
        self.command_frame.grid()
        #包是否已在本地安装,先显示安装信息
        active_dist = self._get_active_dist(name)
        if active_dist is not None:
            #获取包的安装信息
            dist_version = active_dist["version"]
            self.current_package_data['name'] = active_dist["project_name"]
            self.current_package_data['version'] = dist_version
            #已安装包
            self.name_label["text"] = active_dist["project_name"]
            self.info_text.direct_insert("end", _("Installed version: "), ("caption",))
            self.info_text.direct_insert("end", active_dist["version"] + "\n")
            self.info_text.direct_insert("end", _("Installed to: "), ("caption",))
            dist_location = active_dist["location"]
            if not os.path.exists(dist_location):
                self.info_text.direct_insert(
                    "end", _('path is not exist...')
                )
            else:
                self.info_text.direct_insert(
                    "end", strutils.normpath_with_actual_case(dist_location), ("url",)
                )
            self.info_text.direct_insert("end", "\n\n")
            self._select_list_item(name)
        else:
            #未安装包
            self._select_list_item(0)
            
        #从服务器上查询包信息,其次显示包信息,如果能查询到则覆盖包的安装信息
        self.start_fetching_package_info(name)

        # update gui
        if self._is_read_only_package(name):
            self.install_button.grid_remove()
            self.uninstall_button.grid_remove()
        else:
            self.install_button.grid(row=0, column=0)

            if active_dist is not None:
                # existing package in target directory
                self.install_button["text"] = _("Upgrade")
                #比较包的安装版本号和最新版本号,如果小于最新版本则可以更新
                if not parserutils.CompareCommonVersion(self.current_package_data['version'],dist_version):
                    self.install_button["state"] = "disabled"
                else:
                    self.install_button["state"] = "enable"
                self.uninstall_button.grid(row=0, column=1)
            else:
                # new package
                self.install_button["text"] = _("Install")
                self.uninstall_button.grid_remove()
                
    def NotFoundPackage(self,name):
        pass
        
    def write(self,s, tag=None,index="end"):
        if tag is None:
            tags = ()
        else:
            tags = (tag,)
        self.info_text.direct_insert(index, s, tags)
        
    def write_att(self,caption, value, value_tag=None):
        self.write(caption + ": ", "caption")
        self.write(value, value_tag)
        self.write("\n")

    def _get_latest_stable_version(self,version_strings):
        '''
            获取pypi包的最新稳定版本号
        '''
        versions = []
        for s in version_strings:
            if s.replace(".", "").isnumeric():  # Assuming stable versions have only dots and numbers
                versions.append(
                    LooseVersion(s)
                )  # LooseVersion __str__ doesn't change the version string

        if len(versions) == 0:
            return None

        return str(sorted(versions)[-1])

    def _show_package_info(self, name, data, error_code=None):
        self._set_state("idle")
        #从服务器上查询到数据才能覆盖初始的安装信息
        if data:
            self.current_package_data = data
        #如果未找到则设定为404错误
        else:
            error_code = 404


        if error_code is not None:
            if error_code == 404:
                self.NotFoundPackage(name)
            else:
                write(
                    _("Could not find the package info from PyPI. Error code: ") + str(error_code)
                )

            return
        info = data
        self.name_label["text"] = info["name"]  # search name could have been a bit different
        latest_stable_version = self._get_latest_stable_version(data["releases"])
        if latest_stable_version is not None:
            self.write_att(_("Latest stable version"), latest_stable_version)
        else:
            self.write_att(_("Latest version"), data["version"])
        self.write_att(_("Summary"), info["summary"])
        self.write_att(_("Author"), info["author"])
        self.write_att(_("Homepage"), info["homepage"], "url")
        if info.get("bugtrack_url", None):
            self.write_att(_("Bugtracker"), info["bugtrack_url"], "url")
        if info.get("docs_url", None):
            self.write_att(_("Documentation"), info["docs_url"], "url")
        if info.get("package_url", None):
            self.write_att(_("PyPI page"), info["package_url"], "url")
        if info.get("requires_dist", None):
            # Available only when release is created by a binary wheel
            # https://github.com/pypa/pypi-legacy/issues/622#issuecomment-305829257
            self.write_att(_("Requires"), ", ".join(info["requires_dist"]))

        if self._get_active_version(name) != latest_stable_version or not self._get_active_version(
            name
        ):
            self.install_button["state"] = "normal"
        else:
            self.install_button["state"] = "disabled"

    def _is_read_only_package(self, name):
        dist = self._get_active_dist(name)
        if dist is None:
            return False
        else:
            target_dir = self._get_target_directory()
            if not os.path.exists(dist["location"]) or target_dir is None:
                return True
            return False

    def _normalize_name(self, name):
        # looks like (in some cases?) pip list gives the name as it was used during install
        # ie. the list may contain lowercase entry, when actual metadata has uppercase name
        # Example: when you "pip install cx-freeze", then "pip list"
        # really returns "cx-freeze" although correct name is "cx_Freeze"

        # https://www.python.org/dev/peps/pep-0503/#id4
        return re.sub(r"[-_.]+", "-", name).lower().strip()

    def _select_list_item(self, name_or_index):
        if isinstance(name_or_index, int):
            index = name_or_index
        else:
            normalized_items = list(map(self._normalize_name, self.listbox.get(0, "end")))
            try:
                index = normalized_items.index(self._normalize_name(name_or_index))
            except Exception:
                exception(_("Can't find package name from the list: ") + name_or_index)
                return

        old_state = self.listbox["state"]
        try:
            self.listbox["state"] = "normal"
            self.listbox.select_clear(0, "end")
            self.listbox.select_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)
        finally:
            self.listbox["state"] = old_state
            
    def _perform_install(self,package_data):
        '''
            安装
        '''
        self._start_update_list(package_data['name'],refresh=True)
        
    def _perform_uninstall(self,package_data):
        '''
            卸载
        '''
        self._show_instructions()
        #卸载后重新加载并刷新包列表
        self._start_update_list(None,refresh=True)
        
    def _perform_advanced(self,package_data):
        '''
            其它操作
        '''
        self._start_update_list(package_data['name'])

    def _perform_action(self, action):
        assert self._get_state() == "idle"
        assert self.current_package_data
        data = self.current_package_data
        name = self.current_package_data["name"]
        if action == "install":
            if not self._confirm_install(self.current_package_data):
                return
            self._perform_install(self.current_package_data)

        elif action == "uninstall":
            self._perform_uninstall(self.current_package_data)
        else:
            raise RuntimeError("Unknown action")
            
    def _handle_install_file_click(self, event):
        if self._get_state() != "idle":
            return

        filename = filedialog.askopenfilename(
            master=self,
            filetypes=[("Package", ".whl .zip .tar.gz"), ("all files", ".*")],
          #  initialdir=get_workbench().get_local_cwd,
        )
        if filename:  # Note that missing filename may be "" or () depending on tkinter version
            self._install_local_file(filename, False)

    def _handle_install_requirements_click(self, event):
        if self._get_state() != "idle":
            return

        filename = filedialog.askopenfilename(
            master=self,
            filetypes=[("requirements", ".txt"), ("all files", ".*")],
           # initialdir=get_workbench().get_local_cwd,
        )
        if filename:  # Note that missing filename may be "" or () depending on tkinter version
            self._install_local_file(filename, True)

    def _handle_target_directory_click(self, event):
        if self._get_target_directory():
            open_path_in_system_file_manager(self._get_target_directory())

    def _install_local_file(self, filename, is_requirements_file):
        self._start_update_list(None)

    def _handle_url_click(self, event):
        '''
            点击链接操作
        '''
        url = _extract_click_text(self.info_text, event, "url")
        if url is not None:
            #如果是http地址则打开web链接
            if url.startswith("http:") or url.startswith("https:"):
                webbrowser.open(url)
            else:
                #否则打开文件或文件夹
                fileutils.safe_open_file_directory(url)

    def _get_active_version(self, name):
        dist = self._get_active_dist(name)
        if dist is None:
            return None
        else:
            return dist["version"]

    def _get_active_dist(self, name):
        normname = self._normalize_name(name)
        for key in self._active_distributions:

            if self._normalize_name(key) == normname:
                return self._active_distributions[key]

        return None

    def _should_install_to_site_packages(self):
        raise NotImplementedError()

    def _use_user_install(self):
        #虚拟解释器必须安装到到site-package目录下,不能使用user参数安装
        #非虚拟解释器将使用user参数安装
        return not self._should_install_to_site_packages()

    def _get_target_directory(self):
        if self._use_user_install():
            assert hasattr(site, "getusersitepackages")
            os.makedirs(site.getusersitepackages(), exist_ok=True)
            return strutils.normpath_with_actual_case(site.getusersitepackages())
        else:
            for d in sys.path:
                if ("site-packages" in d or "dist-packages" in d) and path_startswith(
                    d, sys.prefix
                ):
                    return strutils.normpath_with_actual_case(d)
            return None

    def _get_title(self):
        return _("Manage packages")

    def _confirm_install(self, package_data):
        return True

    def _read_only(self):
        if self._should_install_to_site_packages():
            return False
        else:
            # readonly if not in a virtual environment
            # and user site packages is disabled
            return not site.ENABLE_USER_SITE
            
    def _targets_virtual_environment(self):
        # https://stackoverflow.com/a/42580137/261181
        return (
            hasattr(sys, "base_prefix")
            and sys.base_prefix != sys.prefix
            or hasattr(sys, "real_prefix")
            and getattr(sys, "real_prefix") != sys.prefix
        )

class PluginsPipDialog(PipDialog):
    MESSAGE = {'msg':''}
    def __init__(self, master,package_count):
        self._install_plugins = {}
        self._uninstall_plugins = set()
        PipDialog.__init__(self, master,package_count,self.MESSAGE['msg'])
        #插件配置是否改变,如果改变关闭对话框时提示用户需要重启软件才能生效
        self._plugin_configuration_changed = False

    def _is_read_only_package(self, name):
        return False

    def _show_instructions(self):
        '''
            显示插件<INSTALL>提示信息
        '''
        self._clear()

        self.info_text.direct_insert("end", _("Install from Server\n"), ("caption",))
        self.info_text.direct_insert(
            "end",
            _("If you don't know where to get the plugin from, ")
            + _("then most likely you'll want to search the plugin Package Index. ")
            + _("Start by entering the name of the plugin in the search box above and pressing ENTER.\n\n"),
        )

        self.info_text.direct_insert("end", _("Install from local file\n"), ("caption",))
        self.info_text.direct_insert("end", _("Click "))
        self.info_text.direct_insert("end", _("here"), ("install_file",))
        self.info_text.direct_insert(
            "end",
            _(
                " to locate and install the plugin file (usually with .egg extension).\n\n"
            ),
        )

        self.info_text.direct_insert("end", _("Upgrade or uninstall\n"), ("caption",))
        self.info_text.direct_insert(
            "end", _("Start by selecting the plugin from the left.\n\n")
        )
        #显示插件安装目录
        if self._get_target_directory():
            self.info_text.direct_insert("end", _("Target:  "), ("caption",))
            self.info_text.direct_insert("end", _("User directory or System directory\n"), ("caption",))

            self.info_text.direct_insert(
                "end",
                _("This dialog lists all available plugins,")
                + _(" but allows upgrading and uninstalling only plugins from "),
            )
            #插件有2个安装目录
            target_directorys = self._get_target_directory()
            #第一个是用户目录
            self.info_text.direct_insert("end",target_directorys[0], ("url"))
            #2个目录之间以逗号分隔
            self.info_text.direct_insert("end", ", ")
            #第二个是软件安装目录
            self.info_text.direct_insert("end",target_directorys[1], ("url"))
            self.info_text.direct_insert(
                "end",
                _(". New plugin will be also installed into the user directory default.")
                + _(" if you want to install to other location,Please go to Tools->Options...->Misc->Plugin"),
            )

        self._select_list_item(0)
        
    def CreateBottomLabel(self,parent,label_text):
        row = ttk.Frame(parent)
        row.grid(row=3, column=0, sticky="nsew", padx=15, pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.label_var = tk.StringVar(value=label_text)
        ttk.Label(row, textvariable=self.label_var).pack(fill="x",side=tk.LEFT)
        self.img = GetApp().GetImage("python/plugins.png")
        btn = ttk.Button(row,image=self.img,state=tk.NORMAL,style="Toolbutton",command=self.ShowAllPlugins)
        btn.pack(side=tk.LEFT)
        misc.create_tooltip(btn, _("View all plugins"))
        
    def ShowAllPlugins(self):
        '''
            查看所有插件
        '''
        names = GetAllPlugins()
        self.installled_var.set(_("All Plugins:"))
        self.ShowNameList(names)
        #显示第一个包名
        if names:
            self._start_show_package_info(names[0])
        
    def ShowAvailablePlugins(self,names):
        self.installled_var.set(_("Available Plugins:"))
        self.ShowNameList(names)
        #显示第一个包名
        self._start_show_package_info(names[0])
    
    def NotFoundPackage(self,name):
        self.write(_("Could not find the plugin from Server.\n"))
        if not self._get_active_version(name):
            # new package
            self.write(_("\nPlease check your spelling!") + _("\nYou need to enter "))
            self.write(_("exact plugin name"), "bold")
            self.write("!")
        
    def search_by_name(self,name):
        names = []
        lower_name = name.lower()
        names = GetAllPlugins(lower_name)
        self.installled_var.set(_("Searched Plugins:"))
        return names
        
    def _handle_install_file_click(self, event):
        if self._get_state() != "idle":
            return

        filename = filedialog.askopenfilename(
            master=self,
            filetypes=[("Plugin", ".egg"), ("all files", ".*")],
            #initialdir=get_workbench().get_local_cwd,
        )
        if filename:  # Note that missing filename may be "" or () depending on tkinter version
            self._install_local_file(filename, False)

    def _get_latest_stable_version(self,version_strings):
        '''
            获取插件的最新稳定版本号
        '''
        versions = []
        #插件版本号列表存储的是字典数据和pypi包的版本号列表不一样
        for s in version_strings:
            versions.append(
                LooseVersion(s['version'])
            )  # LooseVersion __str__ doesn't change the version string

        if len(versions) == 0:
            return None

        return str(sorted(versions)[-1])

    def start_fetching_package_info(self,name):
        '''
            从novalide服务器上查询插件信息
        '''
        _start_fetching_plugin_info(name, None, self._show_package_info)

    def _start_update_list(self, name_to_show=None,refresh=False):
        '''
            获取所有已安装插件,在插件对话框初始化时显示
        '''
        assert self._get_state() in [None, "idle"]
        PipDialog._start_update_list(self,name_to_show)
        pdata = GetApp().GetPluginManager().GetPluginData()
        self._active_distributions = {
            plugin.GetName(): {
                "project_name": plugin.GetName(),
                "key": plugin.GetName(),
                "location": plugin.GetDist().location,
                "version": plugin.GetVersion(),
                'enabled':plugin.IsEnabled()
            }
            for plugin in pdata  if plugin.GetName() not in self._uninstall_plugins# pylint: disable=not-an-iterable
        }
        #手动安装的插件
        self._active_distributions.update(self._install_plugins)
        self._update_list(name_to_show)

    def _conflicts_with_application_version(self, plugin_data):
        '''
            检查插件要求的软件版本是否小于等于当前版本,如果不是则需要提示用户更新软件版本
        '''
        app_version = utils.get_app_version()
        if not plugin_data['app_version']:
            return False
        #检查插件要求的软件版本是否大于当前版本,如果是则提示用户是否更新软件
        if parserutils.CompareCommonVersion(plugin_data['app_version'],app_version):
            ret = messagebox.askyesno(GetApp().GetAppName(),_("Plugin '%s' requires application version at least '%s',Do you want to update your application?")%(plugin_data['name'],plugin_data['app_version']),parent=self)
            if ret == False:
                return True
            #更新软件,如果用户执行更新安装,则程序会退出,不会执行下面的语句
            updateutils.CheckAppUpdate()
        #再检查一次
        return parserutils.CompareCommonVersion(plugin_data['app_version'],app_version)

    def _should_install_to_site_packages(self):
        return self._targets_virtual_environment()
        
    def GetInstallPluginPath(self,plugin_name):
        '''
            先检查插件是否安装,如果已安装则安装到插件安装的目录
            否则获取插件安装目录,有2种目录供选择,一种是用户数据目录,一种是软件安装目录
        '''
        dist = GetApp().GetPluginManager().GetPluginDistro(plugin_name)
        #如果插件未安装则选择2种插件目录中的一种
        if not dist:
            plugin_path = GetPluginInstallpath()
        else:
            plugin_path = os.path.dirname(dist.location)
        utils.get_logger().info("plugin %s install path is %s",plugin_name,plugin_path)
        #确保插件目录存在
        parserutils.MakeDirs(plugin_path)
        return plugin_path
        
    def GetEggPyVersion(self,egg_name):
        '''
            从egg文件名称中提取python版本号
        '''
        i = egg_name.find("py")
        trim_name = egg_name[i:]
        return trim_name.replace("py","").replace(".egg","")
        
    def InstallEgg(self,name,egg_path,version,local=False):
        
        def copy_or_move_egg(src_path,dest_path):
            #将下载的插件文件移至插件目录下
            try:
                #如果是本地安装egg插件,则使用拷贝方式
                if local:
                    shutil.copy(src_path,dest_path)
                #如果是从服务器安装egg插件,则使用剪切方式
                else:
                    shutil.move(src_path,dest_path)
            except Exception as e:
                messagebox.showerror(_("Error"),str(e))
                return False
            
        plugin_path = self.GetInstallPluginPath(name)
        if utils.is_windows():
            copy_or_move_egg(egg_path,plugin_path)
        #linux系统下有可能是python3.x解释器,只能加载python3.x的插件,故需要将插件的python版本改成3.x的
        else:
            #如果python3不是3.6版本则需要更改egg文件名,改之后的插件也是可以加载的
            if utils.is_py3_plus():
                if sys.version_info.minor != 6:
                    egg_file_name = os.path.basename(egg_path)
                    egg_py_version = self.GetEggPyVersion(egg_file_name)
                    #将egg文件名的py版本号替换成sys版本号
                    new_egg_name = egg_file_name.replace("py%s"%egg_py_version,"3.%d"%sys.version_info.minor)
                    #新的egg文件名
                    dest_egg_path = os.path.join(plugin_path,new_egg_name)
                    copy_or_move_egg(egg_path,dest_egg_path)
                #如果是3.6版本则不用更改egg文件名,直接拷贝即可
                else:
                    copy_or_move_egg(egg_path,plugin_path)
            
        #执行插件的安装操作,需要在插件里面执行
        GetApp().GetPluginManager().LoadPluginByName(name)
        #必须重新加载后才能启用插件
        if utils.profile_get_int("ENABLE_INSTALL_PLUGIN", True):
            GetApp().GetPluginManager().EnablePlugin(name)
        #将插件安装信息通知到界面
        self._install_plugins[name] = {
            "project_name": name,
            "key": name,
            "location": os.path.join(plugin_path,os.path.basename(egg_path)),
            "version": version,
            'enabled':True
        }
        self.install_button['state'] = tk.DISABLED
        self._plugin_configuration_changed = True
        return True

    def _perform_install(self,package_data):
        '''
            安装插件
        '''
        def after_download(egg_path):
            '''
                插件下载后回调函数
            '''
            if self.InstallEgg(name,egg_path,package_data['version']):
                PipDialog._perform_install(self,package_data)
                messagebox.showinfo(GetApp().GetAppName(),_("Install plugin '%s' success") % name)
            else:
                messagebox.showerror(GetApp().GetAppName(),_("Install plugin '%s' fail") % name)
            
        name = package_data["name"]
        lang = GetApp().locale.GetLanguageCanonicalName()
        app_version = utils.get_app_version()
        download_url = '%s/member/download_plugin' % (UserDataDb.HOST_SERVER_ADDR)
        payload = dict(new_version = package_data['version'],app_version = app_version,\
                    lang = lang,os_name=sys.platform,plugin_id=package_data['id'])
        #下载插件文件
        downutils.download_file(download_url,call_back=after_download,**payload)
        
    def GetInstallEggPath(self,name):
        """Get the path of the plugin
        @return: string
        """
        return self._active_distributions[name]['location']
        
    def _perform_uninstall(self,package_data):
        '''
            卸载插件
        '''
        plist = utils.profile_get('UNINSTALL_PLUGINS',[])
        plist.append(self.GetInstallEggPath(package_data['name']))
        utils.profile_set('UNINSTALL_PLUGINS', plist)
        self._plugin_configuration_changed = True
        self.uninstall_button['state'] = tk.DISABLED
        #通知界面删除卸载包
        self._uninstall_plugins.add(package_data['name'])
        PipDialog._perform_uninstall(self,package_data)
        #执行插件的卸载操作,需要在插件里面执行
        GetApp().GetPluginManager().UnloadPluginByName(package_data['name'])
        messagebox.showinfo(GetApp().GetAppName(),_("Uninstall success"))
        
    def _perform_enable_action(self,package_data):
        '''
            这里执行启动和禁止插件操作
        '''
        self._plugin_configuration_changed = True
        enable_label_text = _("Enabled")
        disable_label_text = _("Disabled")
        #找到state标签的位置
        state_index = self.info_text.search(_("State")+":","1.0",stopindex=tk.END)
        line,col = self.info_text.get_line_col(state_index)
        col += len(_("State"))
        col += 2
        if self.enabled_button["text"] == enable_label_text:
            self.enabled_button["text"] = disable_label_text
            #启用插件
            GetApp().GetPluginManager().EnablePlugin(package_data['name'],enable=True)
            #执行插件的一些启用操作
            GetApp().GetPluginManager().EnablePluginByName(package_data['name'])
            #更改插件的状态显示
            col += len(disable_label_text)
            del_len = len(disable_label_text)
            #删除旧状态
            index = "%d.%d"%(line,col)
            self.info_text.direct_delete("%d.%d-%dc"%(line,col,del_len),index)
            #插入新的状态
            self.write(enable_label_text,index=index)
        else:
            self.enabled_button["text"] = enable_label_text
            #禁止插件
            GetApp().GetPluginManager().EnablePlugin(package_data['name'],enable=False)
            #执行插件的一些禁止操作
            GetApp().GetPluginManager().DisablePluginByName(package_data['name'])
            #更改插件的状态显示
            col += len(enable_label_text)
            del_len = len(enable_label_text)
            index = "%d.%d"%(line,col)
            self.info_text.direct_delete("%d.%d-%dc"%(line,col,del_len),index)
            self.write(disable_label_text,index=index)

    def _confirm_install(self, package_data):
        '''
            确认是否安装插件
        '''
        #插件是否需要登录
        if package_data.get('login_required',False) and not GetApp().is_login:
            messagebox.showinfo(GetApp().GetAppName(),_('You need register an account and login if you want to install plugin "%s"')%package_data['name'])
            register.RegisterDialog(self).ShowModal()
            #用户未登录成功
            if not GetApp().is_login:
                return False
        try:
            plugin_path = self.GetInstallPluginPath(package_data['name'])
        except Exception as e:
            messagebox.showerror(_("Error"),str(e))
            return False
        dest_egg_path =  os.path.join(plugin_path,package_data['path'])
        #是否替换现有插件文件
        if os.path.exists(dest_egg_path):
            ret = messagebox.askyesno(_("Move File"),_("Plugin file is already exist,Do you want to overwrite it?"),parent=self)
            if ret == False:
                return False
            #删除已经存在的插件文件
            try:
                os.remove(dest_egg_path)
            except:
                messagebox.showerror(GetApp().GetAppName(),_("Remove faile:%s fail") % dest_egg_path)
                return False
        #检查插件是否免费或者是否付费,如果需要付费而未付款则不允许安装
        #本地安装的插件不用检查插件是否需要付费
        if not package_data.get('local',False) and not ui_utils.check_plugin_free_or_payed(package_data):
            return False
        #检查软件的版本是否是插件要求的最低版本
        return not self._conflicts_with_application_version(package_data)

    def _get_target_directory(self):
        '''
            获取插件安装目录
        '''
        return [utils.get_user_plugin_path(),utils.get_sys_plugin_path()]

    def _create_widgets(self, parent,install_label_text,button_text,label_text,tip_text):
        bg = "#ffff99"
        banner = tk.Label(parent, background=bg)
        banner.grid(row=0, column=0, sticky="nsew")

        banner_msg = (
            _("This dialog is for managing Noval plug-ins and their dependencies.\n")
            + _("If you want to install packages for your own programs please install PipManager plugin and then choose 'Tools → Manage packages...'\n")
        )
        banner_msg += (
            "\n"
            + _("NB! You need to restart Noval after installing / upgrading / uninstalling a plug-in.")
        )

        banner_text = tk.Label(banner, text=banner_msg, background=bg, justify="left")
        banner_text.grid(pady=10, padx=10)
        PipDialog._create_widgets(self, parent,_("Installed Plugins:"),_("Find plugin from Server"),label_text,_("input the plugin name to search..."))

    def _get_title(self):
        return _("NovalIDE plug-ins")
        
    def create_advance_buttons(self):
        self.enabled_button = ttk.Button(
            self.command_frame,
            text=_("Enabled"),
            command=lambda: self._perform_enable_action(self.current_package_data)
        )
        self.enabled_button.grid(row=0, column=2, sticky="w", padx=(5, 0))
        
    def _cancel(self,event=None):
        '''
            关闭对话框时检查插件配置是否更改,如果更提示用户需要重启软件
        '''
        if self._plugin_configuration_changed:
            messagebox.showwarning(_("Plugin Configuration Changed"),_("You must restart NovalIDE before your changes will take full affect."),parent=self)
        PipDialog._cancel(self,event)
        
    def _install_local_file(self, filename, is_requirements_file):
        '''
            从本地安装插件
            filename:本地插件路径
        '''
        pi_path = os.path.dirname(filename)
        file_plugin_manager = plugin.PluginManager(pi_path=pi_path)
        plugin_data = file_plugin_manager.FindPluginByegg(filename)
        if plugin_data is None:
            messagebox.showerror(GetApp().GetAppName(),_("invalid plugin"),parent=self)
            return
        plugin_name = plugin_data.GetName()
        #设置为本地安装插件
        if not self._confirm_install({'local':True,'name':plugin_name,'path':os.path.basename(filename),'app_version':plugin_data.Instance.GetMinVersion()}):
            return
            
        #必须要删除插件实例化对象
        instance = plugin_data.GetInstance()
        module = inspect.getmodule(instance)
        #调用egg.activate()会报如下警告,是因为本地egg文件和插件目录下的egg文件重复加载了,不影响程序正常运行
        #安装插件后重启软件即可
        #UserWarning: Module xxxxx was already imported from xxxxxx\__init__.py, but c:\users\administrator\appdata\roaming\novalidedebug\plugins\xxxxx.egg is being added to sys.path
        self.InstallEgg(plugin_name,filename,plugin_data.GetVersion(),local=True)
        self._start_update_list(plugin_name)
        messagebox.showinfo(GetApp().GetAppName(),_("Install plugin '%s' success") % plugin_name)
        
    def _show_package_info(self, name, data, error_code=None):
        PipDialog._show_package_info(self,name,data,error_code)
        plugin_name = data['name'] if data else name
        #未安装的插件不显示启用按钮
        if plugin_name in self._active_distributions:
            enabled = self._active_distributions[plugin_name]['enabled']
            #加载安装插件的状态信息
            self.write_att(_("State"), _('Enabled') if enabled else _("Disabled"))
            if enabled:
                self.enabled_button["text"] = _("Disabled")
            else:
                self.enabled_button["text"] = _('Enabled')
            self.enabled_button.grid(row=0, column=2)
        else:
            self.enabled_button.grid_remove()
        if data and error_code is None:
            self.write_att(_("Installs"), str(data['down_amount']))
        #调试版本时显示插件是否免费
        if GetApp().GetDebug() and data and error_code is None:
            if data['free']:
                self.write_att(_("Free"), _("Yes"))
            else:
                self.write_att(_("Free"), _("No"))
                self.write_att(_("Price"), str(data['price']))
                
        if not GetApp().GetDebug():
            #是否禁止卸载插件,调试模式时总是允许卸载插件
            if data.get('disable_uninstall',False):
                self.uninstall_button['state'] = tk.DISABLED
                self.enabled_button['state'] = tk.DISABLED
            else:
                self.uninstall_button['state'] = tk.NORMAL
                self.enabled_button['state'] = tk.NORMAL
            
        #是否禁止安装插件
        if data.get('disabled',False):
            self.install_button['state'] = tk.DISABLED
        else:
            self.install_button['state'] = tk.NORMAL
            
class PyPiPipDialog(PipDialog):
    
    #搜索包显示的最多结果数
    MAX_RESULTS_COUNT = 100
    def __init__(self, master,package_count,message):
        #message表示正在获取pypi包过程的信息
        PipDialog.__init__(self, master,package_count,message['msg'])
 
    def _show_instructions(self):
        '''
            显示pypi<INSTALL>提示信息
        '''
        if self._get_state() == "disabled":
            return
        self._clear()
        if self._read_only():
            self.info_text.direct_insert("end", "Browse the packages\n", ("caption",))
            self.info_text.direct_insert(
                "end",
                _(
                    "With current interpreter you can only browse the packages here.\n"
                    + "Use 'Tools → Plugin Manager' for installing, upgrading or uninstalling.\n\n"
                ),
            )

            if self._get_target_directory():
                self.info_text.direct_insert("end", _("Packages' directory\n"), ("caption",))
                self.info_text.direct_insert(
                    "end", self._get_target_directory(), ("target_directory")
                )
        else:
            self.info_text.direct_insert("end", _("Install from PyPI\n"), ("caption",))
            self.info_text.direct_insert(
                "end",
                _("If you don't know where to get the package from, ")
                + _("then most likely you'll want to search the Python Package Index. ")
                + _("Start by entering the name of the package in the search box above and pressing ENTER.\n\n"),
            )

            self.info_text.direct_insert("end", _("Install from requirements file\n"), ("caption",))
            self.info_text.direct_insert("end", _("Click "))
            self.info_text.direct_insert("end", _("here"), ("install_reqs",))
            self.info_text.direct_insert(
                "end",
                _(" to locate requirements.txt file and install the packages specified in it.\n\n"),
            )

            self.info_text.direct_insert("end", _("Install from local file\n"), ("caption",))
            self.info_text.direct_insert("end", _("Click "))
            self.info_text.direct_insert("end", _("here"), ("install_file",))
            self.info_text.direct_insert(
                "end",
                _(
                    " to locate and install the package file (usually with .whl, .tar.gz or .zip extension).\n\n"
                ),
            )

            self.info_text.direct_insert("end", _("Upgrade or uninstall\n"), ("caption",))
            self.info_text.direct_insert(
                "end", _("Start by selecting the package from the left.\n\n")
            )
            #显示pip包安装目录,在解释器的site-packages目录下
            if self._get_target_directory():
                self.info_text.direct_insert("end", _("Target:  "), ("caption",))
                if self._should_install_to_site_packages():
                    self.info_text.direct_insert("end", _("virtual environment\n"), ("caption",))
                else:
                    self.info_text.direct_insert("end", _("user site-packages\n"), ("caption",))

                self.info_text.direct_insert(
                    "end",
                    _("This dialog lists all available packages,")
                    + _(" but allows upgrading and uninstalling only packages from "),
                )
                self.info_text.direct_insert("end", self._get_target_directory(), ("url"))
                self.info_text.direct_insert(
                    "end",
                    _(". New packages will be also installed into this directory.")
                    + _(" Other locations must be managed by alternative means."),
                )

        self._select_list_item(0)
        
    def CreateBottomLabel(self,parent,label_text):
        row = ttk.Frame(parent)
        choices,index = interpretermanager.InterpreterManager().GetChoices()
        self.interprterChoice = ttk.Combobox(row,values = choices,state="readonly")
        if index != -1:
            self.interprterChoice.current(index)
        ttk.Label(row, text= _("Interpreter:")).pack(fill="x",side=tk.LEFT)
        self.interprterChoice.pack(side=tk.LEFT)
        self.interprterChoice.bind("<<ComboboxSelected>>",self.update_packages_list)
        #图片对象必须保持住
        self.img = GetApp().GetImage("refresh.png")
        btn = ttk.Button(row, image=self.img,state=tk.NORMAL,style="Toolbutton",command=self.RefreshPackages)
        btn.pack(fill="x",side=tk.LEFT,padx=consts.DEFAUT_HALF_CONTRL_PAD_X)
        misc.create_tooltip(btn, _("refresh"))
        row.grid(row=3,column=0,sticky=tk.NSEW,padx=15)
        self.label_var = tk.StringVar(value=label_text)
        ttk.Label(parent, textvariable=self.label_var).grid(row=4, column=0, sticky="nsew", padx=15, pady=consts.DEFAUT_CONTRL_PAD_Y)
        
    def RefreshPackages(self):
        self._start_update_list(None,refresh=True)
        
    def NotFoundPackage(self,name):
        self.write(_("Could not find the package from PyPI."))
        if not self._get_active_version(name):
            # new package
            self.write(_("\nPlease check your spelling!") + _("\nYou need to enter "))
            self.write(_("exact package name"), "bold")
            self.write("!")
        
    def search_by_name(self,name):
        names = []
        lower_name = name.lower()
        names = GetAllPackages(lower_name)
        self.installled_var.set(_("Searched Packages:"))
        #结果数不能显示太多,如果超过最大数将削减至最多数
        if self.MAX_RESULTS_COUNT < len(names):
            messagebox.showwarning(_("Warning"),_("The resuls count is tool much!trim to %d")%self.MAX_RESULTS_COUNT,parent=self)
            names = names[0:self.MAX_RESULTS_COUNT]
        return names
        
    def update_packages_list(self,event):
        self._set_state('idle')
        self._start_update_list()

    def _start_update_list(self, name_to_show=None,refresh=False):
        '''
            获取解释器所有已安装pypi包,在pypi对话框初始化时显示
        '''
        assert self._get_state() in [None, "idle"]
        PipDialog._start_update_list(self,name_to_show)
        interpreter = self._get_interpreter()
        if interpreter is None:
            return
        #内建解释器直接执行
        if interpreter.IsBuiltIn:
            pkg_resources._initialize_master_working_set()
            self._active_distributions = {
                dist.key: {
                    "project_name": dist.project_name,
                    "key": dist.key,
                    "location": dist.location,
                    "version": dist.version,
                }
                for dist in pkg_resources.working_set  # pylint: disable=not-an-iterable
            }
        else:
            #获取解释器存储数据的路径
            interpreter_data_path = intellisence.IntellisenceManager().GetInterpreterDatabasePath(interpreter)
            #保证路径存在而且路径已存在时不抛出异常
            os.makedirs(interpreter_data_path,exist_ok=True)
            packages_file = os.path.join(interpreter_data_path,"packages.txt")
            #重新加载解释器已安装包
            if refresh:
                try:
                    os.remove(packages_file)
                except:
                    pass
            if not os.path.exists(packages_file):
                temp_data_path  = pkg_resources.resource_filename("pipmanager",'')
                run_pkg_path = os.path.join(temp_data_path,"run_pkg.py")
                if os.path.exists(interpreter.Path) and os.path.exists(run_pkg_path):
                    #生成每个解释器的安装包列表
                    p = pyutils.create_python_interpreter_process(interpreter,run_pkg_path + " " + packages_file)
                    p.wait()
            if not os.path.exists(packages_file):
                self.ShowNameList([])
                self._clear()
                utils.get_logger().error("could not get interpreter %s packages",interpreter.Name)
                self._active_distributions = {}
            else:
                with open(packages_file) as f:
                    #从包文件列表中加载所有包信息
                    self._active_distributions = json.load(f)
        self._update_list(name_to_show)
        #解释器缺失pip工具
        if not interpreter.IsBuiltIn and interpreter.GetPipPath() is None:
            self._handle_outdated_or_missing_pip(_("NB!\n"))
            utils.get_logger().error("interpreter %s miss pp tool",interpreter.Name)

    def _conflicts_with_thonny_version(self, req_strings):
        import pkg_resources

        try:
            conflicts = []
            for req_string in req_strings:
                req = pkg_resources.Requirement.parse(req_string)
                if req.project_name == "thonny" and thonny.get_version() not in req:
                    conflicts.append(req_string)

            return conflicts
        except Exception:
            logging.exception("Problem computing conflicts")
            return None

    def _get_interpreter(self):
        if len(interpretermanager.InterpreterManager().interpreters) == 0:
            return None
        return interpretermanager.InterpreterManager().interpreters[self.interprterChoice.current()]

    def _should_install_to_site_packages(self):
        '''
            虚拟解释器的包必须安装到site_packages目录下
        '''
        return self._targets_virtual_environment()
        
    def _use_user_install(self):
        '''
            内建解释器以及虚拟解释器不能使用user参数安装包
        '''
        if self._get_interpreter() is None or self._get_interpreter().IsBuiltIn:
            return False
        return not self._should_install_to_site_packages()
        
    def _read_only(self):
        if self._should_install_to_site_packages():
            return False
        else:
            #如果是内建解释器,则不能安装任何包,是只读状态
            if self._get_interpreter() is None or self._get_interpreter().IsBuiltIn:
                return True
            return False

    def _targets_virtual_environment(self):
        # https://stackoverflow.com/a/42580137/261181
        #获取当前解释器是否虚拟解释器
        current_interpreter = self._get_interpreter()
        if current_interpreter is None:
            return False
        return current_interpreter.IsVirtual()
        
    def GetInstallArgs(self,file_or_packagename,is_requirements_file=False):
        args = []
        #不加user参数代表进行全局安装,安装后全局可用,如果是信任的安装包可用使用该命令进行安装
        if self._use_user_install():
            #利用--user参数即pip install --user package_name
            #代表仅该用户的安装,安装后仅该用户可用.处于安全考虑,尽量使用该命令进行安装
            #这样会将Python程序包安装到$HOME/.local路径下,其中包含三个字文件夹:bin,lib和share
            args.append("--user")
            
        if is_requirements_file:
            args.append("-r")
        args.append(file_or_packagename)
        return " ".join(args)

    def _install_local_file(self, filename, is_requirements_file):
        '''
            从本地安装包
            filename:本地包路径或者requirements文件路径
            is_requirements_file：表示是否通过requirements文本文件安装
        '''
        install_args = self.GetInstallArgs(filename,is_requirements_file)
        dlg = pythonpackages.InstallPackagesDialog(self,self._get_interpreter(),install_args=install_args,autorun=True)
        status = dlg.ShowModal()
        if status == constants.ID_CANCEL:
            return
        package_name = None
        self._start_update_list(package_name)

    def _perform_install(self,package_data):
        '''
            安装包
        '''
        name = package_data['name']
        install_args = self.GetInstallArgs(name)
        dlg = pythonpackages.InstallPackagesDialog(self,self._get_interpreter(),pkg_name=name,install_args=install_args,autorun=True)
        status = dlg.ShowModal()
        if status == constants.ID_CANCEL:
            return
        PipDialog._perform_install(self,package_data)
        
    def _perform_uninstall(self,package_data):
        '''
            卸载包
        '''
        name = package_data['name']
        #pip和setuptools是用来管理其它包的如果卸载会影响安装卸载包
        if name in ["pip", "setuptools"] and not messagebox.askyesno(
                _("Really uninstall?"),
                _("Package '{}' is required for installing and uninstalling other packages.\n\n").format(
                    name
                )
                + _("Are you sure you want to uninstall it?"),
                parent=self,
            ):
            return
        dlg = pythonpackages.UninstallPackagesDialog(self,self._get_interpreter(),pkg_name=name,uninstall_args=name,autorun=True)
        status = dlg.ShowModal()
        PipDialog._perform_uninstall(self,package_data)

    def _confirm_install(self, package_data):
        return True
        name = package_data["info"]["name"]
        reqs = package_data["info"].get("requires_dist", None)

        other_version_text = (
            "NB! There may be another version available "
            + "which is compatible with current Thonny version. "
            + "Click on '...' button to choose the version to install."
        )

        if name.lower().startswith("thonny-") and not reqs:
            showerror(
                "Thonny plugin without requirements",
                "Looks like you are trying to install an outdated Thonny\n"
                + "plug-in (it doesn't specify required Thonny version).\n\n"
                + "If you still want it, then please install it from the command line."
                + "\n\n"
                + other_version_text,
                parent=get_workbench(),
            )
            return False
        elif reqs:
            conflicts = self._conflicts_with_thonny_version(reqs)
            if conflicts:
                showerror(
                    "Unsuitable requirements",
                    "This package requires different Thonny version:\n\n  "
                    + "\n  ".join(conflicts)
                    + "\n\nIf you still want it, then please install it from the command line."
                    + "\n\n"
                    + other_version_text,
                    parent=get_workbench(),
                )
                return False

        return True

    def _get_target_directory(self):
        if self._get_interpreter() is None or not os.path.exists(self._get_interpreter().Path):
            return None
        if self._use_user_install():
            #获取解释器的site-packages路径
            site_packages_path = self._get_interpreter().GetUserLibPath()
            if not site_packages_path:
                site_packages_path = self._get_interpreter().GetPythonLibPath()
            os.makedirs(site_packages_path, exist_ok=True)
            return strutils.normpath_with_actual_case(site_packages_path)
        else:
            return self._get_interpreter().GetPythonLibPath()

    def _handle_outdated_or_missing_pip(self, error):
        return self._provide_pip_install_instructions(error)
        
    def _perform_advanced(self,package_data):
        '''
            其它操作
        '''
        details = _ask_installation_details(
            self, data, _get_latest_stable_version(list(data["releases"].keys()))
        )
        if details is None:  # Cancel
            return

        version, package_data, upgrade_deps = details
        if not self._confirm_install(package_data):
            return

        args = install_args
        if upgrade_deps:
            args.append("--upgrade")
        args.append(name + "==" + version)
        PipDialog._perform_advanced(self,package_data)


def _ask_installation_details(master, data, selected_version):
    dlg = DetailsDialog(master, data, selected_version)
    ui_utils.show_dialog(dlg, master)
    return dlg.result


def _start_fetching_package_info(name, version_str, completion_handler):
    '''
        从服务器上获取包信息,实际是从pypi上抓取的
    '''
    # Fetch info from novalide server
    api_addr = '%s/member/get_package' % (UserDataDb.HOST_SERVER_ADDR)
    def poll_fetch_complete():
        data = utils.RequestData(api_addr,method='get',arg={'name':name})
        if data is not None:
            #去掉非数据字段
            data.pop('message')
            data.pop('code')
        if data:
            completion_handler(name, data)
        else:
            #未能从服务器上找到包
            completion_handler(name, {},error_code=404)
    #这里最好不要异步获取,否则在频繁点击左侧列表项时会因为多线程导致界面信息混乱
    poll_fetch_complete()
    

def _start_fetching_plugin_info(name, version_str, completion_handler):
    '''
        从服务器上获取插件信息
    '''
    # Fetch info from novalide server
    api_addr = '%s/member/get_plugin' % (UserDataDb.HOST_SERVER_ADDR)
    def poll_fetch_complete():
        data = utils.RequestData(api_addr,method='get',arg={'name':name})
        if data is not None:
            #去掉非数据字段
            data.pop('message')
            data.pop('code')
        if data:
            completion_handler(name, data)
        else:
            #未能从服务器上找到插件
            completion_handler(name, {},error_code=404)

    #这里最好不要异步获取,否则在频繁点击左侧列表项时会因为多线程导致界面信息混乱
    poll_fetch_complete()


def _extract_click_text(widget, event, tag):
    # http://stackoverflow.com/a/33957256/261181
    try:
        index = widget.index("@%s,%s" % (event.x, event.y))
        tag_indices = list(widget.tag_ranges(tag))
        for start, end in zip(tag_indices[0::2], tag_indices[1::2]):
            # check if the tag matches the mouse click index
            if widget.compare(start, "<=", index) and widget.compare(index, "<", end):
                return widget.get(start, end)
    except Exception:
        logging.exception("extracting click text")

    return None
    
class PluginOptionPanel(ui_utils.CommonOptionPanel):
    """
    """
    def __init__(self, parent):
        ui_utils.CommonOptionPanel.__init__(self, parent)
        
        sbox = ttk.LabelFrame(self.panel, text=_("Default plugin directory:"))
        value = self.GetPluginInstallpath()
        self.default_plugin_dirvar = tk.IntVar(value=value)
        ttk.Radiobutton(sbox,text=_('User directory'),variable=self.default_plugin_dirvar,value=0).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        ttk.Radiobutton(sbox,text=_('System directory'),variable=self.default_plugin_dirvar,value=1).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        sbox.pack(fill=tk.X)
        self._enablePluginCheckVar = tk.IntVar(value=utils.profile_get_int("ENABLE_INSTALL_PLUGIN", True))
        enablePluginCheckBox = ttk.Checkbutton(self.panel,text=_("Enable plugin after install it"),variable=self._enablePluginCheckVar)
        enablePluginCheckBox.pack(fill=tk.X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        self._enablecheckFileExtensionVar = tk.IntVar(value=utils.profile_get_int("CHECK_FILE_EXTENSION_PLUGIN", True))
        enablecheckFileExtensionCheckBox = ttk.Checkbutton(self.panel,text=_("Search plugin market When open unsupported file extension"),variable=self._enablecheckFileExtensionVar)
        enablecheckFileExtensionCheckBox.pack(fill=tk.X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))

    def OnOK(self, optionsDialog):
        plugin_install_path = ''
        if self.default_plugin_dirvar.get() == 0:
            plugin_install_path = utils.get_user_plugin_path()
        elif self.default_plugin_dirvar.get() == 1:
            plugin_install_path = utils.get_sys_plugin_path()
        utils.profile_set("PluginInstallPath", plugin_install_path)
        utils.profile_set("ENABLE_INSTALL_PLUGIN", self._enablePluginCheckVar.get())
        utils.profile_set("CHECK_FILE_EXTENSION_PLUGIN", self._enablecheckFileExtensionVar.get())
        return True
        
    def GetPluginInstallpath(self):
        plugin_install_path = GetPluginInstallpath()
        if plugin_install_path == utils.get_sys_plugin_path():
            return 1
        return 0

class PluginManagerGUI(plugin.Plugin):
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        self.parent = parent
        utils.get_logger().info("load default plugin gui plugin")
        # Add Menu
        menuBar = GetApp().Menubar
        tools_menu = menuBar.GetToolsMenu()
        mitem = tools_menu.InsertBefore(constants.ID_PREFERENCES,constants.ID_PLUGIN,_("Plugin Manager"), 
                                  ("Plugin Manager GUI"),handler=self.ShowPluginManagerDlg,img=GetApp().GetImage("plugin.png"))
        PluginsPipDialog.MESSAGE = {'msg':_("fetching plugin from server...")}
        self.plugin_dlg = None
        preference.PreferenceManager().AddOptionsPanelClass("Misc","Plugin",PluginOptionPanel)
        self.GetPlugins()
        
        GetApp().bind("ShowInstallPluginsDlg",self.ShowInstallPluginsDlg,True)
        
    def ShowPluginManagerDlg(self,plugin_names =[]):
        self.plugin_dlg = PluginsPipDialog(self.parent,package_count=0)
        if plugin_names:
            self.plugin_dlg.ShowAvailablePlugins(plugin_names)
        self.plugin_dlg.ShowModal()
        self.plugin_dlg = None
        
    def ShowInstallPluginsDlg(self,event):
        plugin_names = event.get('plugin_names')
        self.ShowPluginManagerDlg(plugin_names)
        
    def GetPlugins(self):
        GetAllPlugins(None,PluginsPipDialog.MESSAGE,self.plugin_dlg,aync=True)
   #     t = threading.Thread(target=GetAllPlugins,args=(None,self.message))
        #daemon表示后台线程,即程序不用等待子线程才退出
    #    t.daemon = True
     #   t.start()