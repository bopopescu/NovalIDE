from noval import _,GetApp
import os
import noval.ui_utils as ui_utils
from tkinter import ttk,messagebox
import noval.menu as tkmenu
import noval.consts as consts
import tkinter as tk
import noval.util.utils as utils
from noval.binds import *
import noval.constants as constants
import json
'''
    菜单快捷键绑定处理
'''

KEYS = ['', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '+', '/', ',',
        '.', '[', ']', '{', '}', '>', '<', ':', '|', 'Left', 'Right', 'Down',
        'Up', 'Home', 'End', 'Enter', 'Tab', 'Space', '"', "'"]
KEYS.extend(["F" + str(x) for x in range(1, 13)]) # Add function keys

if utils.is_windows():
    KEYS.remove('Tab')

MODIFIERS = ['', 'Alt', 'Shift','Ctrl']
MODIFIERS2 = MODIFIERS[0:-1]
MODIFIERS.sort()
MODIFIERS2.sort()

class KeybindOptionPanel(ui_utils.BaseConfigurationPanel):
    """description of class"""
    def __init__(self, parent):
        ui_utils.BaseConfigurationPanel.__init__(self, parent)
        ttk.Label(self, text=_("Menu:")).pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        menubar = GetApp().Menubar
        menus = menubar.Menus
        values = []
        self.menus = {}
        for menu in menus:
            self.ScanMenu(menu[1],menu[2],values)
            
        top = ttk.Frame(self)
        left = ttk.Frame(top)
        self.menu_combo = ttk.Combobox(left,values=values,state="readonly")
        self.menu_combo.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",expand=1)
        self.menu_combo.bind("<<ComboboxSelected>>",self.SelectMenu)
        #在操作Combox时会使listbox选中项消失
        #exportselection需设置为False,可以保证选中项不消失
        self.menu_listbox = ui_utils.ThemedListbox(left,activestyle="dotbox",
            width=40,
            height=20,
            selectborderwidth=0,
            relief="flat",
        #     highlightthickness=4,
         #    highlightbackground="red",
          #   highlightcolor="green",
            borderwidth=0,
            exportselection=False,
            takefocus=True)
        self.menu_listbox.pack(padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),fill="x",expand=1)
        left.pack(fill="x",side=tk.LEFT,expand=1,anchor=tk.N)
        self.menu_listbox.bind('<<ListboxSelect>>', self.SelectMenuItem)
        
        right = ttk.Frame(top)
        ttk.Label(right, text=_("Modifier 1:")).pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y*2,0))
        self.modifier1 = tk.StringVar()
        modifier1_combo = ttk.Combobox(right,textvariable=self.modifier1,values=MODIFIERS)
        modifier1_combo.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        ttk.Label(right, text=_("Modifier 2:")).pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.modifier2 = tk.StringVar()
        modifier2_combo = ttk.Combobox(right,textvariable=self.modifier2,values=MODIFIERS2)
        modifier2_combo.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        ttk.Label(right, text=_("Key:")).pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.key = tk.StringVar()
        key_combo = ttk.Combobox(right,textvariable=self.key,values=KEYS)
        key_combo.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        
        ttk.Label(right, text=_("Binding:")).pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.binding = tk.StringVar()
        ttk.Label(right, textvariable=self.binding).pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x")
        right.pack(fill="x",anchor=tk.N,pady=consts.DEFAUT_CONTRL_PAD_Y)
        
        top.pack(fill="x")
        
        bottom = ttk.Frame(self)
        self.restore_button = ttk.Button(bottom,text=_("Restore Default"),command=self.RestoreDefault)
        self.restore_button.pack(padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),side=tk.LEFT)
        self.apply_button = ttk.Button(bottom,text=_("Apply"),command=self.Apply)
        self.apply_button.pack(padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0),anchor=tk.E)
        bottom.pack(fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y,expand=1)
        
        reopen_label = ttk.Label(
            self,
            text=_("NB! Restart NovalIDE after change keybinding options!"),
            font="BoldTkDefaultFont",
        )
        reopen_label.pack(fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y,padx=consts.DEFAUT_CONTRL_PAD_X)
        self.menu_combo.current(0)
        self.UpdateMenu(0)
        
    def RestoreDefault(self):
        menus = GetApp().Menubar.Menus
        for menu in menus:
            self.RestoreDefaultMenu(menu[2])
        if not self.menu_listbox.curselection():
            return
        self.UpdateMenuItem()
                
    def RestoreDefaultMenu(self,menu):
        item_count = menu.GetItemCount()
        for i in range(item_count):
            item = menu.GetItemByIndex(i)
            if item.id in DEFAULT_KEY_BINDS:
                if item.accelerator != DEFAULT_KEY_BINDS.get(item.id):
                    item.accelerator = DEFAULT_KEY_BINDS.get(item.id)
                    self.NotifyConfigurationChanged()
            else:
                if item.accelerator is not None:
                    item.accelerator = None
                    self.NotifyConfigurationChanged()
            
        if menu.SubMenus == []:
            return
        for submenu in menu.SubMenus:
            self.RestoreDefaultMenu(submenu[1])
        
    def Apply(self):
        if not self.menu_listbox.curselection():
            return
        index = self.menu_combo.current()
        menu = self.menus[index]
        menu_item = menu.FindMenuItemByname(self.GetStringSelection())
        accelerator = None
        if self.key.get() and not self.modifier1.get() and not self.modifier2.get():
            accelerator = self.key.get()
        elif self.modifier1.get() and not self.modifier2.get() and self.key.get():
            accelerator = self.modifier1.get() + "+" + self.key.get()
        elif self.modifier1.get() and self.modifier2.get() and self.key.get():
            accelerator = self.modifier1.get() + "+" + self.modifier2.get() + "+" + self.key.get()
        else:
            messagebox.showerror(_("Error"),_("Invalid key binding"))
            return
        if menu_item.accelerator != accelerator:
            if self.CheckMenusKeybindsConflict(menu_item.id,accelerator):
                return
            menu_item.accelerator = accelerator
            self.NotifyConfigurationChanged()
            
    def SaveKeybindings(self):
        menus = GetApp().Menubar.Menus
        keybinds = {}
        item_ids = dir(constants)
        items = {}
        for item_id in item_ids:
            id_value = getattr(constants,item_id)
            if type(id_value) == int:
                items[id_value] = item_id
        for menu in menus:
            self.SaveKeybinding(menu[2],keybinds,items)
            
        keybind_setting_path = os.path.join(utils.get_cache_path(),tkmenu.KeyBinder.KEY_BINDING_FILE)
        with open(keybind_setting_path,"w") as f:
            json.dump(keybinds,f)
            
    def SaveKeybinding(self,menu,keybinds,items):
        item_count = menu.GetItemCount()
        for i in range(item_count):
            item = menu.GetItemByIndex(i)
            if item.accelerator is not None:
                id_name = items.get(item.id)
                keybinds[id_name] = item.accelerator
        if menu.SubMenus == []:
            return
        for submenu in menu.SubMenus:
            self.SaveKeybinding(submenu[1],keybinds,items)
        
            
    def CheckMenusKeybindsConflict(self,mid,accelerator):
        menus = GetApp().Menubar.Menus
        for menu in menus:
            try:
                self.CheckKeybindsConflict(mid,accelerator,menu[2])
            except RuntimeError as e:
                messagebox.showerror(_("Error"),str(e))
                return True
        return False
        
    def CheckKeybindsConflict(self,mid,accelerator,menu):
        '''
            检查快捷键冲突
        '''
        item_count = menu.GetItemCount()
        for i in range(item_count):
            item = menu.GetItemByIndex(i)
            if item.id != mid and item.accelerator == accelerator:
                raise RuntimeError("accelerator %s is conflicted...." % accelerator)
            
        if menu.SubMenus == []:
            return
        for submenu in menu.SubMenus:
            self.CheckKeybindsConflict(mid,accelerator,submenu[1])
        
    def ScanMenu(self,label,menu,values):
        index = len(values)
        values.append(label)
        self.menus[index] = menu
        if menu.SubMenus == []:
            return
        for submenu in menu.SubMenus:
            menu_id = submenu[0]
            menu_item = menu.FindMenuItem(menu_id)
            self.ScanMenu(menu_item.label,submenu[1],values)
        
    def SelectMenu(self,event):
        index = self.menu_combo.current()
        if index == -1:
            self.UpdateButtons()
            return
        self.UpdateMenu(index)
        
    def UpdateMenu(self,index):
        self.ClearKeys()
        self.menu_listbox.delete(0,"end")
        file_history = GetApp().GetDocumentManager().GetFileHistory()
        id_base = file_history.IdBase
        menu = self.menus[index]
        item_count = menu.GetItemCount()
        for i in range(item_count):
            item = menu.GetItemByIndex(i)
            if item.id == -1:
                continue
            elif item.id >= id_base and item.id <= id_base + consts.MAX_MRU_FILE_LIMIT:
                continue
            elif menu.GetMenu(item.id) is not None:
                continue
            self.menu_listbox.insert(i,item.label)
        self.UpdateButtons()
            
    def SelectMenuItem(self,event):
        self.UpdateButtons()
        if not self.menu_listbox.curselection():
            return
        self.UpdateMenuItem()
        
    def UpdateMenuItem(self):
        index = self.menu_combo.current()
        menu = self.menus[index]
        menu_item = menu.FindMenuItemByname(self.GetStringSelection())
        accelerator = menu_item.accelerator
        if accelerator is not None:
            keys = accelerator.split("+")
            key_count = len(keys) 
            if key_count == 1:
                self.modifier1.set("")
                self.modifier2.set("")
                self.key.set(keys[0])
            elif key_count == 2:
                self.modifier2.set("")
                self.modifier1.set(keys[0])
                self.key.set(keys[1])
            elif key_count == 3:
                self.modifier1.set(keys[0])
                self.modifier2.set(keys[1])
                self.key.set(keys[2])
            self.binding.set(accelerator)
        else:
            self.ClearKeys()
        
    def ClearKeys(self):
        self.modifier1.set("")
        self.modifier2.set("")
        self.key.set("")
        self.binding.set('')

    def GetStringSelection(self):
        return self.menu_listbox.get(self.menu_listbox.curselection()[0])
        
    def UpdateButtons(self):
        if not self.menu_listbox.curselection():
            self.restore_button['state'] = tk.DISABLED
            self.apply_button['state'] = tk.DISABLED
        else:
            self.restore_button['state'] = tk.NORMAL
            self.apply_button['state'] = tk.NORMAL
            
        
    def OnOK(self,optionsDialog):
        try:
            if self._configuration_changed:
                self.SaveKeybindings()
        except Exception as e:
            messagebox.showerror(_("Error"),"Save keybinding settings fail:%s"%str(e))
            return False
        return True
        
    def OnCancel(self,optionsDialog):
        if self._configuration_changed:
            ret = messagebox.askyesno(_("Save keybinding"),_("Keybinding configuration has already been modified outside,Do you want to save?"),parent=self)
            if ret == True:
                self.OnOK(optionsDialog)
                return True
        return True