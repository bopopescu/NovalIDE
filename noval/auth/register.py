# -*- coding: utf-8 -*-
import noval.ui_base as ui_base
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk,messagebox
import noval.consts as consts
import noval.ttkwidgets.linklabel as linklabel
import noval.auth.login as login
import noval.auth.validation as validation
from dummy.userdb import UserDataDb
import noval.util.urlutils as urlutils
import noval.util.md5 as md5_util

class RegisterDialog(ui_base.CommonModaldialog):
    '''
        注册对话框
    '''
    def __init__(self,parent):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(_('Register'))
        sizer_frame = ttk.Frame(self.main_frame)
        sizer_frame.pack(fill="both")
        sizer_frame.columnconfigure(1,weight=1)

        ttk.Label(sizer_frame,text=_('Username:')).grid(column=0, row=0, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.name_var)
        name_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))

        ttk.Label(sizer_frame,text=_('Email:')).grid(column=0, row=1, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.email_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.email_var)
        name_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))

        ttk.Label(sizer_frame,text=_('Phone:')).grid(column=0, row=2, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.phone_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.phone_var)
        name_entry.grid(column=1, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))

        ttk.Label(sizer_frame,text=_('Password:')).grid(column=0, row=3, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.password_var = tk.StringVar()
        #密码文本框
        password_entry = ttk.Entry(sizer_frame,textvariable=self.password_var,show='*')
        password_entry.grid(column=1, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        ttk.Label(sizer_frame,text=_('Confirm Password:')).grid(column=0, row=4, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.confirm_password_var = tk.StringVar()
        #密码文本框
        password_entry = ttk.Entry(sizer_frame,textvariable=self.confirm_password_var,show='*')
        password_entry.grid(column=1, row=4, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        self.AppendokcancelButton()
        
    def _ok(self,event=None):
        if not validation.check_username(self.name_var.get()):
            return
            
        if not validation.check_email(self.email_var.get()):
            return
            
        if not validation.check_password(self.password_var.get()):
            return
            
        if validation.check_password_diff(self.password_var.get(),self.confirm_password_var.get()):
            return
            
        api_addr = '%s/member/register' % (UserDataDb.HOST_SERVER_ADDR)
        #将原始裸密码用MD5加密,在服务端还要MD5再加密一次
        password = md5_util.get_str_md5(self.password_var.get())
        member_id = UserDataDb().GetUserId()
        data = urlutils.RequestData(api_addr,method='post',arg = {'username':self.name_var.get(),\
                'member_id':member_id,'password':password,'email':self.email_var.get(),'phone':self.phone_var.get()})
        if data and data['code'] == 0:
            messagebox.showinfo(GetApp().GetAppName(),_("An activate mail have been send to your mail addr,please check your mail and activate your \naccount,if you don't receive the email,please register again later or contact the author!"))
        elif data:
            messagebox.showerror(GetApp().GetAppName(),_('Register fail:%s')%data['message'])
        else:
            messagebox.showerror(GetApp().GetAppName(),_('could not connect to server'))
        
    def Login(self,event):
        self._cancel()
        login.LoginDialog(GetApp().MainFrame).ShowModal()

    def AppendokcancelButton(self):
        bottom_frame = ttk.Frame(self.main_frame)
        link_label = linklabel.LinkLabel(bottom_frame,text=_('Login'),underline=False,normal_color='DeepPink',hover_color='DeepPink',clicked_color='red')
        link_label.bind("<Button-1>", self.Login)
        link_label.grid(column=0, row=0, sticky=tk.EW, padx=(consts.DEFAUT_CONTRL_PAD_X, consts.DEFAUT_CONTRL_PAD_X), pady=consts.DEFAUT_CONTRL_PAD_Y)
        self.ok_button = ttk.Button(bottom_frame, text=_("&Register"), command=self._ok,default=tk.ACTIVE,takefocus=1)
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
        bottom_frame.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))