# -*- coding: utf-8 -*-
import wx
from noval.tool.consts import _,SPACE,HALF_SPACE
import noval.util.iface as iface
import noval.util.plugin as plugin
import noval.util.constants as constants
import noval.util.utils as utils
import Mail
from noval.dummy.userdb import UserDataDb

CONTENT_TEMPLATE = '''
Operating system:%s
OS Bit:%s
MemberId:%s
App Version:%s
Description of the problem:%s
'''

class FeedbackDialog(wx.Dialog):

    def __init__(self, parent):
        """
        Initializes the feedback dialog.
        """
        wx.Dialog.__init__(self, parent, -1, _("Feedback Bug|Suggestion"), style = wx.DEFAULT_DIALOG_STYLE)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Please choose the feedback category:")), 0, \
                          wx.ALIGN_CENTER|wx.LEFT, SPACE)
        category_list = [_('Bug'),_('Suggestion')]
        self._feedback_category_combo = wx.ComboBox(self, -1,choices=category_list,value=category_list[0], \
                                           size=(200,-1),style = wx.CB_READONLY)
        lineSizer.Add(self._feedback_category_combo,1, wx.EXPAND|wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0, wx.RIGHT|wx.TOP|wx.EXPAND, SPACE)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Title:")), 0, wx.ALIGN_CENTER|wx.LEFT, SPACE)
        self._title_txtctrl = wx.TextCtrl(self, -1, "",size=(100,-1))
        lineSizer.Add(self._title_txtctrl,1, wx.EXPAND|wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0, wx.RIGHT|wx.TOP|wx.EXPAND, SPACE)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Content:")), 0, wx.ALIGN_CENTER|wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0, wx.RIGHT|wx.TOP|wx.EXPAND, SPACE)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.content_ctrl = wx.TextCtrl(self, -1, "", style = wx.TE_MULTILINE,size=(-1,250))
        lineSizer.Add(self.content_ctrl, 1, wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0, wx.RIGHT|wx.TOP|wx.EXPAND, SPACE)
        
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_btn = wx.Button(self, wx.ID_OK, _("&Send"))
        #set ok button default focused
        self.ok_btn.SetDefault()
        wx.EVT_BUTTON(self.ok_btn, -1, self.OnSend)
        bsizer.Add(self.ok_btn, 0,flag=wx.RIGHT, border=SPACE) 
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.Add(cancel_btn, 0,0, border=SPACE) 
        
        box_sizer.Add(bsizer, 0, flag=wx.ALL|wx.ALIGN_RIGHT,border=SPACE)
        
        self.SetSizer(box_sizer)
        self.Fit()
        
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
        utils.GetLogger().info("load default feedback plugin")

        # Add Menu
        menuBar = parent.GetMenuBar()
        help_menu = menuBar.GetHelpMenu()
        
        mitem = help_menu.InsertBefore(constants.ID_ABOUT,constants.ID_FEEDBACK, _("Feedback"), 
                                  ("Feedback bug or suggestion to author"))

    def GetMenuHandlers(self):
        """Register the calculators menu event handler with the 
        top level window and the app.

        """
        return [(constants.ID_FEEDBACK, self.ShowFeedback)]
        
    def ShowFeedback(self,event):
        feedback_dlg = FeedbackDialog(self.parent)
        feedback_dlg.CenterOnParent()
        feedback_dlg.ShowModal()
        feedback_dlg.Destroy()
    