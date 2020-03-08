# -*- coding: utf-8 -*-
from noval import GetApp,_
import hashlib
import os,sys
from tkinter import messagebox
import re

def get_str_md5(content):
    '''
        将字符串用MD5加密
    '''
    m0 = hashlib.md5()
    m0.update(content.encode('utf-8'))
    return m0.hexdigest()

def check_username(username):
    if username.strip() == "":
        messagebox.showinfo(GetApp().GetAppName(),_('username could not empty'))
        return False
    return True
    
def check_password(password):
    if password.strip() == "":
        messagebox.showinfo(GetApp().GetAppName(),_('password could not empty'))
        return False
    return True
    
def check_code(code):
    if code.strip() == "":
        messagebox.showinfo(GetApp().GetAppName(),_('verification code could not empty'))
        return False
    return True
    
def check_email(email):
    if email.strip() == "":
        messagebox.showinfo(GetApp().GetAppName(),_('email could not empty'))
        return False
    ex_email = re.compile(r'^([\w]+\.*)([\w]+)\@[\w]+\.\w{3}(\.\w{2}|)$')
    result = ex_email.match(email)
    if result:
        return True
    else:
        messagebox.showinfo(GetApp().GetAppName(),_('invalid email addr'))
        return False

def check_password_diff(new_password,old_password):
    if new_password == old_password:
        return False
    messagebox.showinfo(GetApp().GetAppName(),_('password is not match'))
    return True