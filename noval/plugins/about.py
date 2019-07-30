# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        about.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-05-10
# Copyright:   (c) wukan 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk
import noval.util.apputils as apputils
import noval.ui_base as ui_base
import noval.python.pyutils as pyutils
import webbrowser
import datetime
import platform
import noval.imageutils as imageutils
import noval.iface as iface
import noval.plugin as plugin
import noval.constants as constants

class AboutDialog(ui_base.CommonModaldialog):

    def __init__(self, parent):
        """
        Initializes the about dialog.
        """
        ui_base.CommonModaldialog.__init__(self, parent)
        title = _("About ") + GetApp().GetAppName()
        self.resizable(height=tk.FALSE, width=tk.FALSE)
        self.title(title)
        self.main_frame.grid_forget()
        self.main_frame.grid(sticky=tk.NSEW, ipadx=15, ipady=15)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        
        heading_font = tk.font.nametofont("TkHeadingFont").copy()
        heading_font.configure(size=19, weight="bold")
        heading_label = ttk.Label(
            self.main_frame, text=GetApp().GetAppName() + ' '  + apputils.get_app_version(), font=heading_font
        )
        heading_label.grid()
        
        self.logo = imageutils.load_image("","logo.png")
        ttk.Label(self.main_frame,image=self.logo).grid()

        url = "http://www.novalide.com"
        url_font = tk.font.nametofont("TkDefaultFont").copy()
        url_font.configure(underline=1)
        url_label = ttk.Label(
            self.main_frame, text=url, style="Url.TLabel", cursor="hand2", font=url_font
        )
        url_label.grid()
        url_label.bind("<Button-1>", lambda _: webbrowser.open(url))
        

        platform_label = ttk.Label(
            self.main_frame,
            justify=tk.CENTER,
            text="Python "
            + pyutils.get_python_version_string()
            + "Tk "
            + pyutils.get_tk_version_str()
            + '\nMAIL wekay102200@sohu.com\nQQ 273655394\nWX w89730387'
        )
        platform_label.grid(pady=20)

        credits_label = ttk.Label(
            self.main_frame,
            text="Based on the open source version →",
            style="Url.TLabel",
            cursor="hand2",
            font=url_font,
            justify="center",
        )
        credits_label.grid()
        credits_label.bind(
            "<Button-1>",
            lambda _: webbrowser.open(
                "https://gitee.com/wekay/NovalIDE"
            ),
        )
        
        
        license_font = tk.font.nametofont("TkDefaultFont").copy()
        license_font.configure(size=7)
        license_label = ttk.Label(
            self.main_frame,
            text="Copyright © 2018-"
            + str(datetime.datetime.now().year)
            + " wukan\nAll rights reserved",
            justify=tk.CENTER,
            font=license_font,
        )
        license_label.grid(pady=20)

        self.ok_button = ttk.Button(
            self.main_frame, text=_("&OK"), command=self._ok, default="active"
        )
        self.ok_button.grid(pady=(0, 15))
        self.ok_button.focus_set()
        self.ok_button.bind("<Return>", self._ok, True)
        self.FormatTkButtonText(self.ok_button)


class AboutLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().AddCommand(constants.ID_ABOUT,_("&Help"),_("&About"),self.OnAbout,image="about.png")

    def OnAbout(self):
        aboutdlg = AboutDialog(GetApp().GetTopWindow())
        aboutdlg.ShowModal()
        


