# -*- coding: utf-8 -*-
from noval import GetApp,_
import tkinter as tk
from tkinter import ttk,messagebox
from noval.util import hiscache
import noval.consts as consts
from noval.util import utils
import noval.python.parser.utils as parserutils
import noval.util.fileutils as fileutils
import os
import noval.ui_base as ui_base
import noval.util.strutils as strutils
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.constants as constants

class FileHistory(hiscache.CycleCache):
    '''
        历史文件列表是一个循环列表,如果超过限制文件个数,会删除最后一个文件
,新添加文件放在头部
    '''
    
    def __init__(self, maxFiles, idBase):
        '''
            maxFiles表示最大允许的历史文件列表个数,从注册表或配置文件中读取
        '''
        #hiscache.CycleCache.TRIM_LAST表示超过限制文件个数后,删除最后一个文件
        hiscache.CycleCache.__init__(self,size=maxFiles,trim=hiscache.CycleCache.TRIM_LAST,add=hiscache.CycleCache.ADD_FIRST)
        self._menu = None
        self._id_base = idBase
        
    def GetMaxFiles(self):
        return self._size
        
    def AddFileToHistory(self, file_path):
        #检查文件路径是否在历史文件列表中,如果存在则删除
        if self.CheckFileExists(file_path):
            self._list.remove(file_path)
        self.PutPath(file_path)
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
            self.PutPath(path)
            
    def PutPath(self,path):
        if self.GetCurrentSize() >= self._size:
            utils.get_logger().debug('history file list size %d is greater then max list size %d,will trim the last file item',self.GetCurrentSize(),self._size)
        #这里超过文件限制,会删除最后一个文件
        self.PutItem(path)

    def Save(self,config):
        for i,item in enumerate(self._list):
            config.Write("%s/file%d" % (consts.RECENT_FILES_KEY,i+1),item)
            
        if utils.is_linux():
            config.Save()
        
    def UseMenu(self,menu):
        self._menu = menu
        
    def AddFilesToMenu(self):
        if 0 == len(self._list):
            return
        assert(self._menu is not None)
        assert(len(self._list) <= self._size)
        self._menu.add_separator()
        #以第一个文件(一般为新添加的文件)作为参考目录
        ref_dir = os.path.dirname(self._list[0])
        for i,item in enumerate(self._list):
            #如果历史文件目录为参考目录,则显示短文件名
            if os.path.dirname(item) == ref_dir:
                label = "%d %s" % (i+1,os.path.basename(item))
            #否则显示长文件名
            else:
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
        #隐藏窗体标题栏
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
        #全屏时是否隐藏菜单栏
        if utils.profile_get_int("HideMenubarFullScreen", False):
            GetApp().ShowMenubar()
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
        

class EnvironmentVariableDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_("Key: ")).pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        self.key_var = tk.StringVar()
        key_ctrl = ttk.Entry(row,textvariable=self.key_var)
        key_ctrl.pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        row.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        row = ttk.Frame(self.main_frame)
        ttk.Label(row, text=_("Value:")).pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        self.value_var = tk.StringVar()
        value_ctrl = ttk.Entry(row,textvariable=self.value_var)
        value_ctrl.pack(side=tk.LEFT,padx=(0,consts.DEFAUT_CONTRL_PAD_X),fill="x")
        row.pack(padx=(consts.DEFAUT_CONTRL_PAD_X,0),fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.AddokcancelButton()
        

class BaseEnvironmentUI(ttk.Frame):
    """description of class"""
    
    def __init__(self,master):
        ttk.Frame.__init__(self,master)
        self.InitUI()

    def InitUI(self):
        ttk.Label(self, text=_("Set user defined environment variable:")).pack(fill="x")
        columns = ['Key','Value']
        
        row = ttk.Frame(self)
        self.listview = treeviewframe.TreeViewFrame(row,columns=columns,show="headings")
        for column in columns:
            self.listview.tree.heading(column, text=_(column))
        self.listview.tree.bind("<<TreeviewSelect>>", self.UpdateUI, True)
        self.listview.pack(side=tk.LEFT,fill="both",expand=1)
        right_frame = ttk.Frame(row)
        self.new_btn = ttk.Button(right_frame, text=_("New.."),command=self.NewVariable)
        self.new_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.edit_btn = ttk.Button(right_frame, text=_("Edit"),command=self.EditVariable)
        self.edit_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        self.remove_btn = ttk.Button(right_frame,text=_("Remove..."),command=self.RemoveVariable)
        
        self.remove_btn.pack(padx=consts.DEFAUT_HALF_CONTRL_PAD_X,pady=(consts.DEFAUT_HALF_CONTRL_PAD_Y))
        right_frame.pack(side=tk.LEFT,fill="y")
        row.pack(fill="both",expand=1)
        
    def UpdateUI(self,event=None):
        selections = self.listview.tree.selection()
        if not selections:
            self.remove_btn["state"] = tk.DISABLED
            self.edit_btn["state"] = tk.DISABLED
        else:
            self.remove_btn["state"] = "normal"
            self.edit_btn["state"] = "normal"

    def RemoveVariable(self):
        selections = self.listview.tree.selection()
        if not selections:
            return
        self.RemoveRowVariable(selections)
        self.UpdateUI(None)
        
    def RemoveRowVariable(self,selections):
        for item in selections:
            self.listview.tree.delete(item)
        
    def GetVariableRow(self,key):
        count = self.dvlc.GetStore().GetCount()
        for i in range(count):
            if self.dvlc.GetTextValue(i,0) == key:
                return i
        return -1
        
    def AddVariable(self,key,value):
        #检查变量是否存在
        if self.CheckAndRemoveKeyitem(key):
            self.listview.tree.insert("","end",values=(key,value))
        
    def NewVariable(self):
        dlg = EnvironmentVariableDialog(self,_("New Environment Variable"))
        status = dlg.ShowModal()
        key = dlg.key_var.get().strip()
        value = dlg.value_var.get().strip()
        if status == constants.ID_OK and key and value:
            self.AddVariable(key,value)
        self.UpdateUI()
        
    def EditVariable(self):
        selections = self.listview.tree.selection()
        if not selections:
            return
        item = selections[0]
        dlg = EnvironmentVariableDialog(self,_("Edit Environment Variable"))
        old_key = self.listview.tree.item(item)['values'][0]
        dlg.key_var.set(old_key)
        dlg.value_var.set(self.listview.tree.item(item)['values'][1])
        status = dlg.ShowModal()
        key = dlg.key_var.get().strip()
        value = dlg.value_var.get().strip()
        if status == constants.ID_OK and key and value:
            self.listview.tree.set(item, column=0, value=key)
            self.listview.tree.set(item, column=1, value=value)
        self.UpdateUI()
        
    def CheckAndRemoveKeyitem(self,key):
        item = self.CheckKeyItem(key)
        if item:
            ret = messagebox.askyesno(_("Warning"),_("Key name has already exist in environment variable,Do you wann't to overwrite it?"),parent=self)
            if ret == True:
                self.RemoveRowVariable([item])
            else:
                return False
        return True
    
    def CheckKeyItem(self,key):
        for child in self.listview.tree.get_children():
            if self.listview.tree.item(child)['values'][0] == key:
                return child
        return None
        
    def GetEnviron(self):
        dct = {}
        for item in self.listview.tree.get_children():
            value = self.listview.tree.item(item)['values']
            #存储值会把数字字符串自动转换成整形,这里需要转换成字符串类型
            dct[value[0]] = str(value[1])
        return dct
        

class ThemedListbox(tk.Listbox):
    def __init__(self, master=None, cnf={}, **kw):
        tk.Listbox.__init__(self,master=master, cnf=cnf, **kw)

        self._ui_theme_change_binding = self.bind(
            "<<ThemeChanged>>", self._reload_theme_options, True
        )
        self._reload_theme_options()

    def _reload_theme_options(self, event=None):
        style = ttk.Style()

        states = []
        if self["state"] == "disabled":
            states.append("disabled")

        # Following crashes when a combobox is focused
        # if self.focus_get() == self:
        #    states.append("focus")
        opts = {}
        for key in [
            "background",
            "foreground",
            "highlightthickness",
            "highlightcolor",
            "highlightbackground",
        ]:
            value = style.lookup(self.get_style_name(), key, states)
            if value:
                opts[key] = value

        self.configure(opts)

    def get_style_name(self):
        return "Listbox"

    def destroy(self):
        self.unbind("<<ThemeChanged>>", self._ui_theme_change_binding)
        tk.Listbox.destroy(self)
        
def no_implemented_yet(func): 
    def _wrapper(*args, **kwargs): 
        messagebox.showwarning(GetApp().GetAppName(),_("This function does not implemented yet!"))
    return _wrapper 
    

def get_default_eol():
    '''
        返回操作系统默认的行尾模式
    '''
    if utils.is_windows():
        return consts.EOL_CRLF
    elif utils.is_linux():
        return consts.EOL_LF
    return consts.EOL_CR

class CommonOptionPanel(BaseConfigurationPanel):
    def __init__(self,master):
        BaseConfigurationPanel.__init__(self,master)
        self.panel = ttk.Frame(self)
        self.panel.pack(fill="both",expand=1,padx=consts.DEFAUT_CONTRL_PAD_X,pady=consts.DEFAUT_CONTRL_PAD_Y)
        

def get_busy_cursor():
    if utils.is_windows():
        return "wait"
    elif utils.is_linux():
        return "watch"
    else:
        return "spinning"

class CommonAccountDialog(ui_base.CommonModaldialog):
    '''
        公用账号密码登录对话框
    '''
    def __init__(self,parent,title,label,ok_text=''):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
        sizer_frame = ttk.Frame(self.main_frame)
        sizer_frame.pack(fill="both")
        ttk.Label(sizer_frame,text=label).grid(column=0, row=0, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2)

        ttk.Label(sizer_frame,text=_('Username:')).grid(column=0, row=1, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.name_var)
        name_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        ttk.Label(sizer_frame,text=_('Password:')).grid(column=0, row=2, sticky="nsew",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.password_var = tk.StringVar()
        #密码文本框
        password_entry = ttk.Entry(sizer_frame,textvariable=self.password_var,show='*')
        password_entry.grid(column=1, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        self.AddokcancelButton()
        if ok_text:
            self.ok_button.configure(text=ok_text,default="active")

def capture_tclerror(func):
    '''
        捕获多线程操作时界面关闭仍向界面写数据的tk异常
    '''
    def _wrapper(*args, **kwargs):
        try:
            func(*args,**kwargs)
        except tk.TclError as e:
            print('warning:tkinter object is not accessable when run function %s'%func.__name__)
    return _wrapper