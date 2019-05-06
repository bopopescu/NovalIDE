# -*- coding: utf-8 -*-
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk
from noval.util import hiscache
import noval.consts as consts
from noval.util import utils
import noval.python.parser.utils as parserutils
import noval.util.fileutils as fileutils
import os
import noval.ui_base as ui_base

class FileHistory(hiscache.CycleCache):
    '''
        历史文件列表是一个循环列表,新文件会覆盖最后一个文件
    '''
    
    def __init__(self, maxFiles, idBase):
        hiscache.CycleCache.__init__(self,size=maxFiles,trim=hiscache.CycleCache.TRIM_LAST,add=hiscache.CycleCache.ADD_FIRST)
        self._menu = None
        self._id_base = idBase
        
    def GetMaxFiles(self):
        return self._size
        
    def AddFileToHistory(self, file_path):
        #检查文件路径是否在历史文件列表中,如果存在则删除
        if self.CheckFileExists(file_path):
            self._list.remove(file_path)
        self.PutItem(file_path)
        #按照文件顺序重新构建历史文件列表菜单
        self.RebuildFilesMenu()
        
    def RemoveFileFromHistory(self, i):
        #从历史文件列表中删除文件
        del self._list[i]
        #从新构建历史文件菜单
        self.RebuildFilesMenu()
        
    def Load(self,config):
        index = 1
        paths = []
        while True:
            key = "%s/file%d" % (consts.RECENT_FILES_KEY,index)
            path = config.Read(key)
            if path:
                paths.append(path)
                index += 1
            else:
                break
        #务必按照倒序加载文件列表
        for path in paths[::-1]:
            self.PutItem(path)

    def Save(self,config):
        for i,item in enumerate(self._list):
            config.Write("%s/file%d" % (consts.RECENT_FILES_KEY,i+1),item)
            
        if utils.is_linux():
            config.Save()
        
    def UseMenu(self,menu):
        self._menu = menu
        
    def AddFilesToMenu(self):
        assert(self._menu is not None)
        assert(len(self._list) <= self._size)
        if len(self._list) > 0:
            self._menu.add_separator()
        for i,item in enumerate(self._list):
            label = "%d %s" % (i+1,item)
            def load(n=i):
                self.OpenFile(n)
            GetApp().AddCommand(self._id_base+i,_("&File"),label,handler=load)
            
    def RebuildFilesMenu(self):
        first_file_index = self._menu.GetMenuIndex(self._id_base)
        if first_file_index != -1:
            #先要删除原先的所有历史菜单项
            self._menu.delete(first_file_index-1)
        #重新生成历史菜单项
        self.AddFilesToMenu()
        
    def OpenFile(self,n):
        GetApp().OpenMRUFile(n)
        
    def CheckFileExists(self,path):
        for item in self._list:
            if parserutils.ComparePath(item,path):
                return True
        return False
        
    def GetHistoryFile(self,i):
        assert(i >=0 and i < len(self._list))
        return self._list[i]

class EncodingDeclareDialog(ui_base.CommonModaldialog):
    def __init__(self,parent):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(_("Declare Encoding"))
        self.name_var = tk.StringVar(value="# -*- coding: utf-8 -*-")
        self.name_ctrl = ttk.Entry(self, textvariable=self.name_var)
        self.name_ctrl.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_ctrl["state"] = tk.DISABLED
        
        self.check_var = tk.IntVar(value=False)
        check_box = ttk.Checkbutton(self, text=_("Edit"),variable=self.check_var,command=self.onChecked)
        check_box.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        space_label = ttk.Label(bottom_frame,text="")
        space_label.grid(column=0, row=0, sticky=tk.EW, padx=(consts.DEFAUT_CONTRL_PAD_X, consts.DEFAUT_CONTRL_PAD_X), pady=consts.DEFAUT_CONTRL_PAD_Y)
        self.ok_button = ttk.Button(bottom_frame, text=_("&OK"), command=self._ok,default=tk.ACTIVE)
        self.ok_button.grid(column=1, row=0, sticky=tk.EW, padx=(0, consts.DEFAUT_CONTRL_PAD_X), pady=consts.DEFAUT_CONTRL_PAD_Y)
        self.cancel_button = ttk.Button(bottom_frame, text=_("Cancel"), command=self._cancel)
        self.cancel_button.grid(column=2, row=0, sticky=tk.EW, padx=(0, consts.DEFAUT_CONTRL_PAD_X), pady=consts.DEFAUT_CONTRL_PAD_Y)
        bottom_frame.columnconfigure(0, weight=1)
        
    def onChecked(self):
        if self.check_var.get():
            self.name_ctrl["state"] = tk.NORMAL
        else:
            self.name_ctrl["state"] = tk.DISABLED
def get_augmented_system_path(extra_dirs):
    path_items = os.environ.get("PATH", "").split(os.pathsep)
    
    for d in reversed(extra_dirs):
        if d not in path_items:
            path_items.insert(0, d)
    
    return os.pathsep.join(path_items)
    

def update_system_path(env, value):
    # in Windows, env keys are not case sensitive
    # this is important if env is a dict (not os.environ)
    if utils.is_windows():
        found = False
        for key in env:
            if key.upper() == "PATH":
                found = True
                env[key] = value
        
        if not found:
            env["PATH"] = value
    else:
        env["PATH"] = value

def get_environment_with_overrides(overrides):
    env = os.environ.copy()
    for key in overrides:
        if overrides[key] is None and key in env:
            del env[key]
        else:
            assert isinstance(overrides[key], str)
            if key.upper() == "PATH":
                update_system_path(env, overrides[key])
            else:
                env[key] = overrides[key]
    return env