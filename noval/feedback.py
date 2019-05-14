# -*- coding: utf-8 -*-
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk
import noval.iface as iface
import noval.plugin as plugin
import noval.constants as constants
import noval.util.utils as utils
import noval.util.mailutils as mailutils
from dummy.userdb import UserDataDb
import noval.ui_base as ui_base
import noval.editor.text as texteditor
import noval.consts as consts

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
        self._feedback_category_combo = ttk.Combobox(row, values=category_list,state = "readonly")
        self._feedback_category_combo.current(0)
        self._feedback_category_combo.pack(side=tk.LEFT,fill="x",expand=1)
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y)
        
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_("Title:")).pack(side=tk.LEFT,fill="x")
        self._title_txtctrl = ttk.Entry(row)
        self._title_txtctrl.pack(side=tk.LEFT,fill="x",expand=1)
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
        ttk.Label(self.main_frame, text=_("Content:")).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        self.content_ctrl = texteditor.TextCtrl(self.main_frame)
        self.content_ctrl.pack(fill="both",expand=1,padx=consts.DEFAUT_CONTRL_PAD_X,)
        self.AddokcancelButton()
        self.ok_button.configure(text=_("&Send"),default="active")
        
    def OnSend(self,event):
        
        content = self.content_ctrl.GetValue().strip()
        if content == "":
            wx.MessageBox(_("Content could not be empty!"),style=wx.OK|wx.ICON_ERROR)
            return
        result = UserDataDb.get_db().GetUserInfo()
        content =  CONTENT_TEMPLATE % (result[5],result[3],result[1],utils.GetAppVersion(),self.content_ctrl.GetValue().strip())
        subject = u"%s【%s】" % (self._title_txtctrl.GetValue().strip(),self._feedback_category_combo.GetValue())
        if Mail.send_mail(subject,content):
            wx.MessageBox(_("Send mail success,Thanks for your feedback!"))
            self.EndModal(wx.ID_OK)

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
    