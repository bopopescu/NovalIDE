# -*- coding: utf-8 -*-
from noval import _,GetApp
import tkinter as tk
from tkinter import ttk,messagebox
from noval.syntax import syntax
import copy
import noval.util.strutils as strutils
import os
import noval.util.appdirs as appdirs
import noval.consts as consts
import noval.syntax.lang as lang
import json
import noval.editor.text as texteditor
from noval.editor.code import CodeCtrl
from tkinter import font as tk_font
import noval.ui_utils as ui_utils
import noval.ttkwidgets.textframe as textframe
import noval.util.utils as utils

class CodeSampleCtrl(CodeCtrl):
    
    def __init__(self, parent,**kw):
        CodeCtrl.__init__(self, parent,font="EditorFont",read_only=True,height=10,**kw)
        self._lexer = None
        
    def on_secondary_click(self, event=None):
        texteditor.TextCtrl.CreatePopupMenu(self)
        self._popup_menu.tk_popup(event.x_root, event.y_root)

    def ResetColorClass(self):
        if hasattr(self, "syntax_colorer"):
            del self.syntax_colorer

class ColorFontOptionsPanel(ui_utils.BaseConfigurationPanel):
    """description of class"""
    
    def __init__(self, parent):
        ui_utils.BaseConfigurationPanel.__init__(self,parent)
        #默认值
        self._default_settings = {
            'size':GetApp()._guard_font_size(consts.DEFAULT_FONT_SIZE),
            'font':GetApp().GetDefaultEditorFamily(),
            'syntax_theme':consts.DEFAULT_SYNTAX_THEME
        }
        #存储值
        self._saved_settings = {}
        font_obj = self.GetEditorFont()
        lexerLabel = ttk.Label(self, text=_("Lexers:")).pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        select_lexer_nane = ''
        names = []
        for lexer in syntax.SyntaxThemeManager().Lexers:
            if lexer.IsVisible():
                names.append(lexer.GetShowName())
            if lexer.GetLangId() == lang.ID_LANG_TXT:
                select_lexer_nane = lexer.GetShowName()
        row = ttk.Frame(self)
        self.lexerVal = tk.StringVar(value=select_lexer_nane)
        lexerCombo = ttk.Combobox(row, values=names, state="readonly",textvariable=self.lexerVal)
        lexerCombo.bind("<<ComboboxSelected>>",self.OnSelectLexer)
        lexerCombo.pack(side=tk.LEFT,fill="x",expand=1)
        defaultButton = ttk.Button(row, text=_("Restore Default(D)"),command=self.SetDefaultValue)
        defaultButton.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_HALF_CONTRL_PAD_Y))
        
        row = ttk.Frame(self)
        lframe = ttk.Frame(row)
        ttk.Label(lframe, text=_("Font(F):")).pack(fill="x")
        self.fontVal = tk.StringVar(value=font_obj['family'])
        self._saved_settings['font'] = self.fontVal.get()
        fontCombo = ttk.Combobox(lframe, values=self._get_families_to_show(), state="readonly",textvariable=self.fontVal)
        fontCombo.pack(fill="x",expand=1)
        lframe.pack(side=tk.LEFT,fill="x",expand=1)
        fontCombo.bind("<<ComboboxSelected>>",self.OnSelectFont)
    
        rframe = ttk.Frame(row)
        ttk.Label(rframe, text=_("Size(S):")).pack(fill="x")
        
        choices = []
        min_size = 6
        max_size = 25
        for i in range(min_size,max_size):
            choices.append(str(i))
        self.sizeVar = tk.IntVar(value=font_obj['size'])
        self._saved_settings['size'] = self.sizeVar.get()
        #验证历史文件个数文本控件输入是否合法
        validate_cmd = self.register(self.validateSizeInput)
        self.sizeCombo = ttk.Combobox(rframe,validate = 'key', values=choices,textvariable=self.sizeVar,validatecommand = (validate_cmd, '%P'))
        self.sizeCombo.bind("<<ComboboxSelected>>",self.OnSelectSize)
        self.sizeCombo.pack(fill="x")
        rframe.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
        style_list = []
        row = ttk.Frame(self)
        ttk.Label(row, text=_("Code Sample(P):")).pack(side=tk.LEFT,fill="x",expand=1)
        ttk.Label(row, text=_("Syntax Themes:")).pack(side=tk.LEFT,fill="x")
        
        themes = list(syntax.SyntaxThemeManager()._syntax_themes.keys())
        self.themeVal = tk.StringVar(value=utils.profile_get(consts.SYNTAX_THEME_KEY,consts.DEFAULT_SYNTAX_THEME))
        self._saved_settings['syntax_theme'] = self.themeVal.get()
        themCombo = ttk.Combobox(row,values = themes, state="readonly",textvariable=self.themeVal)
        themCombo.bind("<<ComboboxSelected>>",self.OnSelectTheme)
        themCombo.pack(side=tk.LEFT,fill="x")
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_HALF_CONTRL_PAD_Y))

        #默认文本控件高度超过面板高度了,这里指定一个小的高度,下面设置控件铺满面板
        text_frame = textframe.TextFrame(self,borderwidth=1,relief="solid",text_class=CodeSampleCtrl,undo=False)
        self.code_sample_ctrl = text_frame.text
        text_frame.pack(fill="both",expand=1,padx=consts.DEFAUT_CONTRL_PAD_X)
        self.OnSelectLexer()

    def validateSizeInput(self,contents):
        if not contents.isdigit():
            self.sizeCombo.bell()
            return False
        return True

    def _get_families_to_show(self):
        # In Linux, families may contain duplicates (actually different fonts get same names)
        return sorted(set(filter(lambda name: name[0].isalpha(), tk_font.families())))
        
    def SetDefaultValue(self):
        font = self.GetEditorFont()
        self.fontVal.set(self._default_settings.get('font'))
        self.sizeVar.set(self._default_settings.get('size'))
        self.themeVal.set(self._default_settings.get('syntax_theme'))
        self.OnSelectFont()
        self.OnSelectSize()
        self.OnSelectTheme()
        self.NotifyConfigurationChanged()

    def OnSelectLexer(self, event=None):
        showname = self.lexerVal.get()
        lexer = syntax.SyntaxThemeManager().GetLangLexerFromShowname(showname)
        self.GetLexerStyles(lexer)
        
    def OnSelectFont(self,event=None):
        font = self.GetEditorFont()
        font['family'] = self.fontVal.get()
        self.NotifyConfigurationChanged()
        
    def OnSelectSize(self,event=None):
        font = self.GetEditorFont()
        font['size'] = self.sizeVar.get()
        self.NotifyConfigurationChanged()

    def GetEditorFont(self):
        font = tk_font.nametofont("EditorFont")
        return font
        
    def OnSelectTheme(self, event=None):
        theme = self.themeVal.get()
        syntax.SyntaxThemeManager().ApplySyntaxTheme(theme)
        self.code_sample_ctrl.UpdateSyntaxTheme()
        self.NotifyConfigurationChanged()
        
    def OnOK(self, optionsDialog):
        theme = self.themeVal.get()
        utils.profile_set(consts.SYNTAX_THEME_KEY,theme)
        utils.profile_set(consts.EDITOR_FONT_SIZE_KEY,self.sizeVar.get())
        utils.profile_set(consts.EDITOR_FONT_FAMILY_KEY,self.fontVal.get())
        #更新文本视图的字体和主题颜色
        self.UpdateCodetextView(theme)
        return True
        
    def GetLexerStyles(self,lexer):
        self.code_sample_ctrl.ResetColorClass()
        self.code_sample_ctrl.SetLangLexer(lexer)
        self.code_sample_ctrl.set_content(lexer.GetSampleCode())
        
    def OnCancel(self, optionsDialog):
        '''
            取消时恢复存储的值
        '''
        if self._configuration_changed:
            ret = messagebox.askyesno(_("Save configuration"),_("fonts and colors configuration has already been modified outside,Do you want to save?"),parent=self)
            if ret == True:
                self.OnOK(optionsDialog)
                return True
                
        font = self.GetEditorFont()
        font['family'] = self._saved_settings['font']
        font['size'] = self._saved_settings['size']
        syntax.SyntaxThemeManager().ApplySyntaxTheme(self._saved_settings.get('syntax_theme'))
        self.code_sample_ctrl.UpdateSyntaxTheme()
        return True

    def UpdateCodetextView(self,theme):
        for editor in GetApp().MainFrame.GetNotebook().winfo_children():
            if isinstance(editor.GetView(),texteditor.TextView):
                #更新语法主题
                if self._saved_settings['syntax_theme'] != theme:
                    editor.GetView().GetCtrl().UpdateSyntaxTheme()
                #更新字体
                editor.GetView().UpdateFont(self.sizeVar.get(),self.fontVal.get())