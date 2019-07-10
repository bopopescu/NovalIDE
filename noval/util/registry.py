# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        registry.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-10
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
try:
    from _winreg import *
except ImportError:
    from winreg import *

class Registry(object):
    """description of class"""
    
    def __init__(self,hkey = HKEY_CURRENT_USER):
        self._hkey = hkey
        
    @property
    def RootKey(self):
        return self._hkey

    def Open(self,subkey,access=KEY_READ):
        #打开子健
        try:
            open_key = OpenKey(self.RootKey, subkey,0,access)
        except Exception as e:
            return None
        return Registry(open_key)
        
    def Exist(self,key):
        return self.Open(key) is not None
        
    def Read(self,value_name):
        #读取健的默认值
        return QueryValue(self.RootKey,value_name)
        
    def ReadEx(self,value_name):
        #读取健的值对应数据
        #返回(value,value_type)类型的值,只需取第一个即可
        return QueryValueEx(self.RootKey,value_name)[0]
        
    def EnumChildKey(self):
        child_key_count = QueryInfoKey(self.RootKey)[0]  
        for i in range(int(child_key_count)):  
            name = EnumKey(self.RootKey,i)
            child_key = self.Open(name)
            yield child_key
            
    def EnumChildKeyNames(self):
        #获取该键的所有键值,遍历枚举
        child_key_count = QueryInfoKey(self.RootKey)[0]  
        for i in range(int(child_key_count)):  
            name = EnumKey(self.RootKey,i)
            yield name
        
    def DeleteKey(self,key_name):
        #删除键
        DeleteKey(self.RootKey, key_name)
        
    def DeleteValue(self,value_name):
        #删除键值
        DeleteValue(self.RootKey, value_name)
        
    def CreateKey(self,key_name):
        #创建新的子键
        new_key = CreateKey(self.RootKey,key_name)
        return Registry(new_key)
        
    def WriteValue(self,key_name,value,val_type = REG_SZ):
        #创建子健并给键添加默认值
        SetValue(self.RootKey,key_name,val_type,value)

    def WriteValueEx(self,value_name,value,val_type = REG_SZ):
        #给键添加一个值
        SetValueEx(self.RootKey,value_name,0,val_type,value)
        
    def CreateKeys(self,key_str):
        #创建多级子健,以/字符分割
        keys = key_str.split("/")
        loop_key = None
        for key in keys:
            if loop_key is None:
                loop_key = self.CreateKey(key)
            else:
                loop_key = loop_key.CreateKey(key)
        return loop_key

    def DeleteKeys(self,key_str):
        key_path = key_str.replace("/","\\")
        registry = self.Open(key_path)
        if registry is None:
            return
        names = list(registry.EnumChildKeyNames())
        if 0 == len(names):
            self.DeleteKey(key_path)
        else:
            for name in names:
                self.DeleteKeys(key_str + "/" + name)
            self.DeleteKeys(key_str)
        
    def CloseKey(self):
        CloseKey(self.RootKey)
        
    def __enter__(self):
        #with语句进入
        return self
                        
    def __exit__(self, e_t, e_v, t_b):
        #with语句退出时关闭键
        self.CloseKey()
        