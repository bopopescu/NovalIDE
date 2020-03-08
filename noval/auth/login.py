# -*- coding: utf-8 -*-
import noval.ui_base as ui_base
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk,messagebox
import noval.consts as consts
import noval.ttkwidgets.linklabel as linklabel
import noval.auth.forget as forget
import noval.auth.validation as validation
from dummy.userdb import UserDataDb
import noval.util.urlutils as urlutils

class LoginDialog(ui_base.CommonModaldialog):
    '''
        登录主账号对话框
    '''
    def __init__(self,parent):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(_('Login'))
        sizer_frame = ttk.Frame(self.main_frame)
        sizer_frame.pack(fill="both")
        sizer_frame.columnconfigure(1,weight=1)
        ttk.Label(sizer_frame,text=_('Email:')).grid(column=0, row=0, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.email_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.email_var)
        name_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))

        ttk.Label(sizer_frame,text=_('Password:')).grid(column=0, row=1, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.password_var = tk.StringVar()
        #密码文本框
        password_entry = ttk.Entry(sizer_frame,textvariable=self.password_var,show='*')
        password_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        self.AppendokcancelButton()
            
    def AppendokcancelButton(self,):
        bottom_frame = ttk.Frame(self.main_frame)
        link_label = linklabel.LinkLabel(bottom_frame,text=_("Forget password"),underline=False,normal_color='DeepPink',hover_color='DeepPink',clicked_color='red')
        link_label.bind("<Button-1>", self.ForgetPassword)
        link_label.grid(column=0, row=0, sticky=tk.EW, padx=(consts.DEFAUT_CONTRL_PAD_X, consts.DEFAUT_CONTRL_PAD_X), pady=consts.DEFAUT_CONTRL_PAD_Y)
        self.ok_button = ttk.Button(bottom_frame, text=_("&Login"), command=self._ok,default=tk.ACTIVE,takefocus=1)
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
        
    def ForgetPassword(self,event):
        forget.ForgetPasswordDialog(self).ShowModal()
        
    def _ok(self,event=None):
        if not validation.check_email(self.email_var.get()):
            return
            
        if not validation.check_password(self.password_var.get()):
            return
        api_addr = '%s/member/login' % (UserDataDb.HOST_SERVER_ADDR)
        #将原始裸密码用MD5加密,在服务端还要MD5再加密一次
        password = validation.get_str_md5(self.password_var.get())
        data = urlutils.RequestData(api_addr,method='get',arg = {'password':password,'email':self.email_var.get()})
        if data and data['code'] == 0:
            messagebox.showinfo(GetApp().GetAppName(),_('Login success'))
            UserDataDb().UpdateUserInfo(**data)
            GetApp().is_login = True
            #登录成功后更新菜单注册标签为注销
            GetApp().UpdateLoginState()
            ui_base.CommonModaldialog._ok(self,event)
        elif data:
            messagebox.showerror(GetApp().GetAppName(),_('Login fail:%s')%data['message'])
        else:
            messagebox.showerror(GetApp().GetAppName(),_('could not connect to server'))

def auto_login():
    '''
        用本地数据库保存的token自动登录
    '''
    token = UserDataDb().GetToken()
    if not token:
        return False
    api_addr = '%s/member/login' % (UserDataDb.HOST_SERVER_ADDR)
    data = urlutils.RequestData(api_addr,method='get',arg = {'token':token})
    if data and data['code'] == 0:
        return True
    return False
    
def logout():
    '''
        注销用户
    '''
    token = UserDataDb().GetToken()
    if not token:
        return
    api_addr = '%s/member/logout' % (UserDataDb.HOST_SERVER_ADDR)
    data = urlutils.RequestData(api_addr,method='post',arg = {'token':token})