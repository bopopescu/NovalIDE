# -*- coding: utf-8 -*-
from noval import GetApp,_
import tkinter as tk
import os
from tkinter import ttk,messagebox
import noval.iface as iface
import noval.plugin as plugin
import noval.constants as constants
import noval.util.utils as utils
import noval.util.mailutils as mailutils
from dummy.userdb import UserDataDb
import noval.ui_base as ui_base
import noval.editor.text as texteditor
import noval.consts as consts
import noval.ttkwidgets.textframe as textframe
import noval.python.parser.utils as parserutils
from mss import mss
import noval.python.pyutils as pyutils
from PIL import Image
import noval.util.compat as compat

CONTENT_TEMPLATE = '''
Operating system:%s
OS Bit:%s
MemberId:%s
App Version:%s
Python Version:%s
Tk Version:%s
isPro:%d
Description of the problem:%s
'''

class FeedbackDialog(ui_base.CommonModaldialog):

    def __init__(self, parent):
        """
        Initializes the feedback dialog.
        """
        ui_base.CommonModaldialog.__init__(self, parent)
        self.title(_("Feedback Bug|Suggestion"))
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_("Please choose the feedback category:")).pack(side=tk.LEFT,fill="x")
        category_list = [_('Bug'),_('Suggestion')]
        self._feedback_category_var = tk.StringVar()
        feedback_category_combo = ttk.Combobox(row, values=category_list,state = "readonly",textvariable=self._feedback_category_var)
        feedback_category_combo.current(0)
        feedback_category_combo.pack(side=tk.LEFT,fill="x",expand=1)
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y)
        
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_("Title:")).pack(side=tk.LEFT,fill="x")
        self._title_var = tk.StringVar()
        title_txtctrl = ttk.Entry(row,textvariable=self._title_var)
        title_txtctrl.pack(side=tk.LEFT,fill="x",expand=1)
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
        ttk.Label(self.main_frame, text=_("Content:")).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        text_frame = textframe.TextFrame(self.main_frame,borderwidth=1,relief="solid",text_class=texteditor.TextCtrl)
        self.content_ctrl = text_frame.text
        text_frame.pack(fill="both",expand=1,padx=consts.DEFAUT_CONTRL_PAD_X,)
        self.AddokcancelButton()
        self.ok_button.configure(text=_("&Send"),default="active")
        
    def screenshot(self):
        """Take a screenshot, crop and save"""
        screenshot_path = os.path.join(utils.get_user_data_path(),"screenshots")
        if not os.path.exists(screenshot_path):
            parserutils.MakeDirs(screenshot_path)
        box = {
            "top": GetApp().winfo_y(),
            "left": GetApp().winfo_x(),
            "width": GetApp().winfo_width(),
            "height": GetApp().winfo_height()
        }
        screenshot = mss().grab(box)
        screenshot = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        screenshot_image_path = "{0}/{1}.png".format(screenshot_path,ttk.Style(GetApp()).theme_use())
        screenshot.save(screenshot_image_path)
        return screenshot_image_path
        
    def _ok(self):
        content = self.content_ctrl.GetValue().strip()
        if content == "":
            messagebox.showerror(GetApp().GetAppName(),_("Content could not be empty!"))
            return
        screenshot_image_path = self.screenshot()
        result = UserDataDb().GetUserInfo()
        os_system = result[5]
        if utils.is_py3():
            os_system = compat.ensure_string(result[5])
        content =  CONTENT_TEMPLATE % (os_system,result[3],result[1],utils.get_app_version(),pyutils.get_python_version_string().strip(),\
                                pyutils.get_tk_version_str(),0,self.content_ctrl.GetValue().strip())
        subject = u"%s【%s】" % (self._title_var.get().strip(),self._feedback_category_var.get())
        if mailutils.send_mail(subject,content,attach_files=[screenshot_image_path]):
            messagebox.showinfo(GetApp().GetAppName(),_("Send mail success,Thanks for your feedback!"))
            ui_base.CommonModaldialog._ok(self)

class FeedBack(plugin.Plugin):
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        self.parent = parent
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("load default feedback plugin")

        # Add Menu
        menuBar = GetApp().Menubar
        help_menu = menuBar.GetHelpMenu()
        
        mitem = help_menu.InsertBefore(constants.ID_ABOUT,constants.ID_FEEDBACK, _("Feedback"), 
                                  ("Feedback bug or suggestion to author"),handler=self.ShowFeedback)
        
    def ShowFeedback(self):
        feedback_dlg = FeedbackDialog(self.parent)
        feedback_dlg.ShowModal()
    