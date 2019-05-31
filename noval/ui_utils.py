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
import noval.util.strutils as strutils

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
        self.name_ctrl = ttk.Entry(self.main_frame, textvariable=self.name_var)
        self.name_ctrl.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_ctrl["state"] = tk.DISABLED
        
        self.check_var = tk.IntVar(value=False)
        check_box = ttk.Checkbutton(self.main_frame, text=_("Edit"),variable=self.check_var,command=self.onChecked)
        check_box.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AddokcancelButton()
        
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
    env = update_environment_with_overrides(os.environ)
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
    
def update_environment_with_overrides(overrides):
    env = overrides.copy()
    for key in env:
        if utils.is_py2():
            if isinstance(key,unicode):
                key = str(key)
                utils.get_logger().warn('enrironment key %s is unicode should convert to str',key)
                env[key] = overrides[key]
            if isinstance(overrides[key],unicode):
                utils.get_logger().warn('enrironment key %s value %s is unicode should convert to str',key,overrides[key])
                env[key] = str(overrides[key])
    return env

class FullScreenDialog(ui_base.CommonDialog):
    
    def __init__(self, parent):
        """Initialize the navigator window
        @param parent: parent window
        @param auiMgr: wx.aui.AuiManager
        @keyword icon: wx.Bitmap or None
        @keyword title: string (dialog title)

        """
        ui_base.CommonDialog.__init__(self,parent)
        self.title(_('FullScreen Display'))
        self._listBox = None
        self.transient(parent)
        # Setup
        self.__DoLayout()
        self.protocol("WM_DELETE_WINDOW", self.CloseDialog)

        #双击列表框,回车,Esc键关闭窗口
        self._listBox.bind("<Double-Button-1>", self.CloseDialog, True)
        self._listBox.bind("<Return>", self.CloseDialog, True)
        self._listBox.bind("<Escape>", self.CloseDialog)

    def __DoLayout(self):
        """Layout the dialog controls
        @param icon: wx.Bitmap or None
        @param title: string

        """
        self._listBox = tk.Listbox(self.main_frame,height=2)
        self._listBox.pack(fill="both",expand=1)

    def OnKeyUp(self, event):
        """Handles wx.EVT_KEY_UP"""
        key_code = event.GetKeyCode()
        # TODO: add setter method for setting the navigation key
        if key_code in self._close_keys:
            self.CloseDialog()
        else:
            event.Skip()

    def PopulateListControl(self):
        """Populates the L{AuiPaneNavigator} with the panes in the AuiMgr"""
        GetApp().MainFrame.SavePerspective(is_full_screen=True)
        GetApp().MainFrame.HideAll(is_full_screen=True)
        self._listBox.insert(0,_("Close Show FullScreen"))

    def OnItemDoubleClick(self, event):
        """Handles the wx.EVT_LISTBOX_DCLICK event"""
        self.CloseDialog()

    def CloseDialog(self,event=None):
        global _fullScreenDlg
        """Closes the L{AuiPaneNavigator} dialog"""
        GetApp().ToggleFullScreen()
        GetApp().MainFrame.LoadPerspective(is_full_screen=True)
        self.destroy()
        _fullScreenDlg = None

    def GetCloseKeys(self):
        """Get the list of keys that can dismiss the dialog
        @return: list of long (wx.WXK_*)

        """
        return self._close_keys

    def SetCloseKeys(self, keylist):
        """Set the keys that can be used to dismiss the L{AuiPaneNavigator}
        window.
        @param keylist: list of key codes

        """
        self._close_keys = keylist

    def Show(self):
        # Set focus on the list box to avoid having to click on it to change
        # the tab selection under GTK.
        self.PopulateListControl()
        self._listBox.focus_set()
        self._listBox.selection_set(0)
        self.CenterWindow()
        GetApp().ToggleFullScreen()
        
_fullScreenDlg = None
def GetFullscreenDialog():
    global _fullScreenDlg
    if _fullScreenDlg == None:
        _fullScreenDlg = FullScreenDialog(GetApp().MainFrame)
    
    return _fullScreenDlg
    
class BaseConfigurationPanel(ttk.Frame):
    
    def __init__(self,master,**kw):
        ttk.Frame.__init__(self,master,**kw)
        self._configuration_changed = False
        
    def OnOK(self,optionsDialog):
        if not self.Validate():
            return False
        return True
        
    def OnCancel(self,optionsDialog):
        if self._configuration_changed:
            return False
        return True
        
    def NotifyConfigurationChanged(self):
        self._configuration_changed = True
        
    def Validate(self):
        return True
        
def check_chardet_version():
    import chardet
    if strutils.compare_version(chardet.__version__,"3.0.4") <0:
        raise RuntimeError(_("chardet version is less then 3.0.4,please use python pip to upgrade it first!"))