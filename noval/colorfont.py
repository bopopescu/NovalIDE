# -*- coding: utf-8 -*-
from noval import _
import tkinter as tk
from tkinter import ttk
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

class CodeSampleCtrl(CodeCtrl):
    
    def __init__(self, parent,**kw):
        CodeCtrl.__init__(self, parent,font="EditorFont",borderwidth=1,read_only=True,**kw)
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
        font_obj = tk_font.nametofont("EditorFont")
        
        lexerLabel = ttk.Label(self, text=_("Lexers:")).pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        select_lexer_nane = ''
        names = []
        for lexer in syntax.SyntaxThemeManager().Lexers:
            if lexer.IsVisible():
                names.append(lexer.GetShowName())
            if lexer.GetLangId() == lang.ID_LANG_TXT:
                select_lexer_nane = lexer.GetShowName()
      #  self._lexerCombo.SetSelection(select_index)
        row = ttk.Frame(self)
        self.lexerVal = tk.StringVar(value=select_lexer_nane)
        lexerCombo = ttk.Combobox(row, values=names, state="readonly",textvariable=self.lexerVal)
        lexerCombo.bind("<<ComboboxSelected>>",self.OnSelectLexer)
        lexerCombo.pack(side=tk.LEFT,fill="x",expand=1)
        defaultButton = ttk.Button(row, text=_("Restore Default(D)"),command=self.SetDefaultValue)
        defaultButton.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y/2))
        
        row = ttk.Frame(self)
        lframe = ttk.Frame(row)
        ttk.Label(lframe, text=_("Font(F):")).pack(fill="x")
        self.fontVal = tk.StringVar(value=font_obj['family'])
        fontCombo = ttk.Combobox(lframe, values=self._get_families_to_show(), state="readonly",textvariable=self.fontVal)
        fontCombo.pack(fill="x",expand=1)
        lframe.pack(side=tk.LEFT,fill="x",expand=1)
        fontCombo.bind("<<ComboboxSelected>>",self.OnSelectFont)
    #    self._fontCombo.SetSelection(0)
    
        rframe = ttk.Frame(row)
        ttk.Label(rframe, text=_("Size(S):")).pack(fill="x")
        
        choices = []
        min_size = 6
        max_size = 25
        for i in range(min_size,max_size):
            choices.append(str(i))
        self.sizeVar = tk.IntVar(value=font_obj['size'])
        #验证历史文件个数文本控件输入是否合法
        validate_cmd = self.register(self.validateSizeInput)
        self.sizeCombo = ttk.Combobox(rframe,validate = 'key', values=choices,textvariable=self.sizeVar,validatecommand = (validate_cmd, '%P'))
        self.sizeCombo.bind("<<ComboboxSelected>>",self.OnSelectSize)
        self.sizeCombo.pack(fill="x")
        rframe.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_CONTRL_PAD_X,0))
        
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
     #   self._sizeCombo.SetSelection(0)
        style_list = []
        row = ttk.Frame(self)
        ttk.Label(row, text=_("Code Sample(P):")).pack(side=tk.LEFT,fill="x",expand=1)
        ttk.Label(row, text=_("Themes:")).pack(side=tk.LEFT,fill="x")
        
        themes = list(syntax.SyntaxThemeManager()._syntax_themes.keys())
        self.themeVal = tk.StringVar()
        themCombo = ttk.Combobox(row,values = themes, state="readonly",textvariable=self.themeVal)
        themCombo.bind("<<ComboboxSelected>>",self.OnSelectTheme)
        themCombo.pack(side=tk.LEFT,fill="x")
        row.pack(padx=consts.DEFAUT_CONTRL_PAD_X,fill="x",pady=(0,consts.DEFAUT_CONTRL_PAD_Y/2))

        #默认文本控件高度超过面板高度了,这里指定一个小的高度,下面设置控件铺满面板
        self.code_sample_ctrl = CodeSampleCtrl(self,height=10)
        self.code_sample_ctrl.pack(fill="both",expand=1,padx=consts.DEFAUT_CONTRL_PAD_X)
                self.OnSelectLexer()

    def validateSizeInput(self,contents):
        if not contents.isdigit():
            self.sizeCombo.bell()
            return False
        return True

    def _get_families_to_show(self):
        # In Linux, families may contain duplicates (actually different fonts get same names)
        return sorted(set(filter(lambda name: name[0].isalpha(), tk_font.families())))
        
    def SetDefaultValue(self, event):
        theme_name = self._themCombo.GetString(self._themCombo.GetSelection())
        style_sheet_path = os.path.join(appdirs.GetAppDataDirLocation(),"styles")
        theme_style_sheet = os.path.join(style_sheet_path,theme_name + consts.THEME_FILE_EXT)
        lexer_manager = syntax.LexerManager()
        LexerStyleItem.SetThresHold(LexerStyleItem.LOAD_FROM_DEFAULT)
        lexer_manager.LoadThemeSheet(theme_style_sheet)
        self.code_sample_ctrl.UpdateStyles()
        self.GetLexerStyles()
        LexerStyleItem.SetDefaultThresHold()
        
    def OnSelectLexer(self, event=None):
        showname = self.lexerVal.get()
        lexer = syntax.SyntaxThemeManager().GetLangLexerFromShowname(showname)
        self.GetLexerStyles(lexer)
        
    def OnSelectFont(self,event):
        self.SetLexerStyle(consts.FACE_ATTR_NAME)
        
    def OnSelectSize(self,event):
        self.SetLexerStyle(consts.SIZE_ATTR_NAME)
        
    def OnSelectTheme(self, event):
        theme = self.themeVal.get()
        syntax.SyntaxThemeManager().ApplySyntaxTheme(theme)
        self.code_sample_ctrl.UpdateSyntaxTheme()
        
    def OnOK(self, optionsDialog):
        config = wx.ConfigBase_Get()
        theme = self._themCombo.GetString(self._themCombo.GetSelection())
        config.Write(THEME_KEY,theme)
        lex_manager = syntax.LexerManager()
        
        selection = self._lexerCombo.GetSelection()
        lexer = self._lexerCombo.GetClientData(selection)
        lexer_name = lexer.GetShowName()
        global_style = lex_manager.GetGlobalItemByName(consts.GLOBAL_STYLE_NAME)
        for style in lexer.StyleItems:
            key_name = getStyleKeyName(lexer_name,style.KeyName)
            if style.KeyName != consts.GLOBAL_STYLE_NAME:
                style_str = self.GetStyleSpecStr(style,global_style)
                if style_str == "":
                    config.DeleteEntry(key_name)
                    continue
            else:
                style_str = unicode(style)
            config.Write(key_name,style_str)
        txt_lexer = lex_manager.GetLexer(lang.ID_LANG_TXT)
        lexer_name = txt_lexer.GetShowName()
        key_name = getStyleKeyName(lexer_name,global_style.KeyName)
        config.Write(key_name,unicode(global_style))
        data_str = json.dumps({'font':global_style.Face,'size':int(global_style.Size)})
        config.Write(consts.PRIMARY_FONT_KEY, data_str)
        config.Write("TextEditorColor", global_style.Fore.replace("#",""))
        lex_manager.SetGlobalFont(global_style.Face,int(global_style.Size))
        
        openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if isinstance(openDoc,STCTextEditor.TextDocument):
                docView = openDoc.GetFirstView()
                lex_manager.UpdateAllStyles(docView.GetCtrl(),theme)
        return True
        
    def SetStyle(self,selection):
        style = self.lb.GetClientData(selection)
        self.fore_color_combo.SetColor(style.GetFore())
        self.back_color_combo.SetColor(style.GetBack())
        self._fontCombo.SetValue(style.GetFace())
        self._sizeCombo.SetValue(style.GetSize())
        self.bold_chkbox.SetValue(style.Bold)
        self.eol_chkbox.SetValue(style.Eol)
        self.underline_chkbox.SetValue(style.Underline)
        self.italic_chkbox.SetValue(style.Italic)
        
    def GetLexerStyles(self,lexer):
        self.code_sample_ctrl.ResetColorClass()
        self.code_sample_ctrl.SetLangLexer(lexer)
        self.code_sample_ctrl.set_content(lexer.GetSampleCode())