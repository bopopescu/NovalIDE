# -*- coding: utf-8 -*-
from noval.util.logger import *
from noval.util.apputils import *
from noval.util.appdirs import *
from noval import GetApp
    
def profile_get(key,default_value=""):
    if is_py2():
        basestring_ = basestring
    elif is_py3_plus():
        basestring_ = str
    if isinstance(default_value,basestring_):
        return GetApp().GetConfig().Read(key, default_value)
    else:
        try:
            return eval(GetApp().GetConfig().Read(key, ""))
        except:
            return default_value
    
def profile_get_int(key,default_value=-1):
    return GetApp().GetConfig().ReadInt(key, default_value)
    
def profile_set(key,value):
    if type(value) == int or type(value) == bool:
        GetApp().GetConfig().WriteInt(key,value)
    else:
        if isinstance(value, str) or (is_py2() and isinstance(value,unicode)):
            GetApp().GetConfig().Write(key,value)
        else:
            GetApp().GetConfig().Write(key,repr(value))

def update_statusbar(msg):
    GetApp().MainFrame.PushStatusText(msg)
    
def get_main_frame():
    return GetApp().MainFrame

def get_child_pids(ppid):
    child_ids = []
    for pid in psutil.pids():
        try:
            p = psutil.Process(pid)
            if p.ppid() == ppid:
                child_ids.append(p.pid)
        except:
            pass
    return child_ids
    
if is_windows():
    from noval.util.registry import *
elif is_linux():
    try:
        from ConfigParser import ConfigParser
    except:
        from configparser import ConfigParser
        
class Config(object):
    if is_windows():
        def __init__(self,app_name):
            self.app_name = app_name
            base_reg = Registry().Open('SOFTWARE')
            self.reg = self.EnsureOpenKey(base_reg,self.app_name)
                
        def EnsureOpenKey(self,parent_reg,key):
            #打开时必须设置注册表有写的权限,否则会提示权限不足
            reg = parent_reg.Open(key,access=KEY_ALL_ACCESS)
            if reg is None:
                reg = parent_reg.CreateKey(key)
            return reg
                
        def GetDestRegKey(self,key,ensure_open=True):
            '''
                按照/分割线分割多级key,如果是写入操作,则创建所有子健
                如果是读取操作,则不能创建子健,只能打开,如果打开失败,则返回None
                ensure_open:打开子健失败时是否创建子健
            '''
            if -1 == key.find("/"):
                return self.reg,key
            child_keys = key.split("/")
            last_key = child_keys.pop()
            loop_reg = self.reg
            for child in child_keys:
                if ensure_open:
                    child_reg = self.EnsureOpenKey(loop_reg,child)
                else:
                    child_reg = loop_reg.Open(child,access=KEY_ALL_ACCESS)
                    if child_reg is None:
                        return None,last_key
                loop_reg = child_reg
            return loop_reg,last_key
                
        def Read(self,key,default=""):
            dest_key_reg,last_key = self.GetDestRegKey(key,ensure_open=False)
            if dest_key_reg is None:
                return default
            try:
                return dest_key_reg.ReadEx(last_key)
            except:
                if is_py2():
                    assert(isinstance(default,basestring))
                elif is_py3_plus():
                    assert(isinstance(default,str))
                return default
            
        def ReadInt(self,key,default=-1):
            if not self.Exist(key):
                assert(isinstance(default,int))
                return default
            return int(self.Read(key))
            
        def Write(self,key,value):
            dest_key_reg,last_key = self.GetDestRegKey(key)
            try:
                val_type = REG_SZ
                if is_py3_plus() and type(value) == bytes:
                    val_type = REG_BINARY
                dest_key_reg.WriteValueEx(last_key,value,val_type=val_type)
            except Exception as e:
                get_logger().exception("write reg key %s fail" % key)
                
        def WriteInt(self,key,value):
            dest_key_reg,last_key = self.GetDestRegKey(key)
            dest_key_reg.WriteValueEx(last_key,value,val_type=REG_DWORD)
                
        def Exist(self,key):
            try:
                self.reg.ReadEx(key)
                return True
            except:
                return False
                
        def DeleteEntry(self,key_val):
            dest_key_reg,value = self.GetDestRegKey(key_val,ensure_open=False)
            if dest_key_reg is None:
                return
            try:
                dest_key_reg.DeleteValue(value)
            except:
                get_logger().debug("delete key_val %s fail" % key_val)
                
        def GetGroups(self,key_path,names):
            if not self.reg.Exist(key_path):
                return
            dest_key_reg,value = self.GetDestRegKey(key_path)
            for name in dest_key_reg.EnumChildKeyNames():
                names.append(name)
            
        def DeleteGroup(self,key_path):
            self.reg.DeleteKeys(key_path)
            
    else:
        def __init__(self,app_name):
            self.app_name = app_name
            self.cfg = ConfigParser()
            self.config_path = os.path.join(os.path.expanduser("~"),"." + self.app_name)
            try:
                self.cfg.read(self.config_path)
            except Exception as e:
                get_logger().warn('load ide config file error %s,will reaload it',str(e))
                self.Reload()
            
        def GetDestSection(self,key,ensure_open=True):
            '''
                按照/分割线分割多级key,如果是写入操作,则创建所有子健
                如果是读取操作,则不能创建子健,只能打开,如果打开失败,则返回None
                ensure_open:打开子健失败时是否创建子健
            '''
            if -1 == key.find("/"):
                return 'DEFAULT',key
            sections = key.split("/")
            last_key = sections.pop()
            for i in range(len(sections)):
                section = ("/").join(sections[0:i+1])
                if ensure_open:
                    #禁止写入空字段[]
                    if section and not self.cfg.has_section(section):
                        self.cfg.add_section(section)
                else:
                    if section and not self.cfg.has_section(section):
                        return None,last_key
            return ("/").join(sections),last_key
                
        def Read(self,key,default=""):
            section,last_key = self.GetDestSection(key,ensure_open=False)
            try:
                return self.cfg.get(section,last_key)
            except:
                if is_py2():
                    assert(isinstance(default,basestring))
                elif is_py3_plus():
                    assert(isinstance(default,str))
                return default
            
        def ReadInt(self,key,default=-1):
            try:
                return int(self.Read(key))
            except:
                return default
            
        def Write(self,key,value):
            section,last_key = self.GetDestSection(key)
            if isinstance(value, str) or (is_py2() and isinstance(value,unicode)):
                if is_py2():
                    value = str(value)
                self.cfg.set(section,last_key,value)
            else:
                self.cfg.set(section,last_key,repr(value))
            
        def WriteInt(self,key,value):
            section,last_key = self.GetDestSection(key)
            #将bool值转换为int
            if type(value) == bool:
                value = int(value)
            assert(type(value) == int)
            #python3 configparser不支持写入整形变量,必须先转换为字符串
            if is_py3_plus():
                value = str(value)
            self.cfg.set(section,last_key,value)
            
        def Save(self):
            with open(self.config_path,"w") as f:
                self.cfg.write(f)
                
        def DeleteEntry(self,key):
            section,last_key = self.GetDestSection(key)
            self.cfg.remove_option(section,last_key)
            self.Save()

        def GetGroups(self,key_path,names):
            for section in self.cfg.sections():
                if section.find(key_path) != -1:
                    names.append(key_path)
            
        def DeleteGroup(self,key_path):
            for section in self.cfg.sections():
                if section.find(key_path) != -1:
                    self.cfg.remove_section(section)
            self.Save()
            
        def Reload(self):
            '''
                如果配置文件加载错误,重新加载时删除原配置文件
            '''
            if os.path.exists(self.config_path):
                os.remove(self.config_path)
            self.cfg.read(self.config_path)

def call_after(func): 
    def _wrapper(*args, **kwargs): 
        return GetApp().after(100,func, *args, **kwargs) 
    return _wrapper 