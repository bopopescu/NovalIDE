# -*- coding: utf-8 -*-
import noval.ui_base as ui_base
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk,messagebox
import noval.consts as consts
import noval.auth.validation as validation
from dummy.userdb import UserDataDb
import noval.util.urlutils as urlutils

class ForgetPasswordDialog(ui_base.CommonModaldialog):
    '''
        找回密码对话框
    '''
    def __init__(self,parent):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(_('Forget Password'))
        sizer_frame = ttk.Frame(self.main_frame)
        sizer_frame.pack(fill="both")
        sizer_frame.columnconfigure(1,weight=1)

        ttk.Label(sizer_frame,text=_('Email:')).grid(column=0, row=0, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.email_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.email_var)
        name_entry.grid(column=1, row=0,columnspan=2,sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))

        ttk.Label(sizer_frame,text=_('Verification Code:')).grid(column=0, row=1, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.code_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.code_var)
        name_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))

        ttk.Button(sizer_frame, text=_("Send Verification Code"), command=self.SendVerificationCode).grid(column=2, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        ttk.Label(sizer_frame,text=_('New Password:')).grid(column=0, row=2, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.password_var = tk.StringVar()
        #密码文本框
        password_entry = ttk.Entry(sizer_frame,textvariable=self.password_var,show='*')
        password_entry.grid(column=1,columnspan=2, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        ttk.Label(sizer_frame,text=_('Confirm New Password:')).grid(column=0, row=3, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.confirm_password_var = tk.StringVar()
        #密码文本框
        password_entry = ttk.Entry(sizer_frame,textvariable=self.confirm_password_var,show='*')
        password_entry.grid(column=1,columnspan=2, row=3, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        self.AddokcancelButton()
        self.ok_button.configure(text=_('Reset Password'),default="active")

    def SendVerificationCode(self):
        if not validation.check_email(self.email_var.get()):
            return
            
        api_addr = '%s/member/send_verification_code' % (UserDataDb.HOST_SERVER_ADDR)
        data = urlutils.RequestData(api_addr,method='post',arg = {'email':self.email_var.get()})
        if data and data['code'] == 0:
            messagebox.showinfo(GetApp().GetAppName(),_('Send verification code success'))
        else:
            messagebox.showerror(GetApp().GetAppName(),_('Send verification code fail'))
        

    def _ok(self,event=None):
        if not validation.check_code(self.code_var.get()):
            return
            
        if not validation.check_email(self.email_var.get()):
            return
            
        if not validation.check_password(self.password_var.get()):
            return
            
        if validation.check_password_diff(self.password_var.get(),self.confirm_password_var.get()):
            return
        messagebox.showinfo(GetApp().GetAppName(),_('Reset password success'))
        ui_base.CommonModaldialog._ok(self,event)
