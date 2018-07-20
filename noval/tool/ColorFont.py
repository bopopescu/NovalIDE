import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ ,THEME_KEY,DEFAULT_THEME_NAME
import wx.stc as stc
import wx.combo
from noval.tool.syntax import syntax
import copy
import noval.util.strutils as strutils
import os
import noval.util.appdirs as appdirs
import STCTextEditor
import consts

class CodeSampleCtrl(stc.StyledTextCtrl):
    
    def __init__(self, parent, ID,pos=wx.DefaultPosition, size=(1000,800),style=0):
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)
        self._lexer = None
        
    def SetLangLexer(self,lexer):
        lexer_id = lexer.Lexer
        self._lexer = lexer
        # Check for special cases
        # TODO: add fetch method to check if container lexer requires extra
        #       style bytes beyond the default 5.
        if lexer_id in [ wx.stc.STC_LEX_HTML, wx.stc.STC_LEX_XML]:
            self.SetStyleBits(7)
        elif lexer_id == wx.stc.STC_LEX_NULL:
            self.SetStyleBits(5)
            self.SetLexer(lexer_id)
            self.ClearDocumentStyle()
            self.UpdateBaseStyles()
            return True
        else:
            self.SetStyleBits(5)

        # Set Lexer
        self.SetLexer(lexer_id)
        # Set Keywords
        self.SetKeyWords(lexer.Keywords)
        # Set Lexer/Syntax Specifications
        self.SetSyntax(lexer.StyleItems)
        
    def UpdateStyles(self):
        self.SetSyntax(self._lexer.StyleItems)
        
    def SetKeyWords(self, kw_lst):
        """Sets the keywords from a list of keyword sets
        @param kw_lst: [ (KWLVL, "KEWORDS"), (KWLVL2, "KEYWORDS2"), ect...]

        """
        # Parse Keyword Settings List simply ignoring bad values and badly
        # formed lists
        kwlist = ""
        for keyw in kw_lst:
            if len(keyw) != 2:
                continue
            else:
                if not isinstance(keyw[0], int) or \
                   not isinstance(keyw[1], basestring):
                    continue
                else:
                    kwlist += keyw[1]
                    super(CodeSampleCtrl, self).SetKeyWords(keyw[0], keyw[1])

        # Can't have ? in scintilla autocomp list unless specifying an image
        # TODO: this should be handled by the autocomp service
        if '?' in kwlist:
            kwlist.replace('?', '')

        kwlist = kwlist.split()         # Split into a list of words
        kwlist = list(set(kwlist))      # Remove duplicates from the list
        kwlist.sort()                   # Sort into alphabetical order
        
    def HideLineNumber(self):
        self.SetMarginWidth(1, 0)
        
    def SetSyntax(self, synlst):
        """Sets the Syntax Style Specs from a list of specifications
        @param synlst: [(STYLE_ID, "STYLE_TYPE"), (STYLE_ID2, "STYLE_TYPE2)]

        """
        # Parses Syntax Specifications list, ignoring all bad values
        self.UpdateBaseStyles()
        for syn in synlst:
            self.StyleSetSpec(syn.StyleId, syn.GetStyleSpec())
        self.Refresh()
        return True
        
    def StyleDefault(self):
        """Clears the editor styles to default
        @postcondition: style is reset to default

        """
        self.StyleClearAll()
        self.SetCaretForeground(wx.BLACK)
        self.Colourise(0, -1)
        
    def UpdateBaseStyles(self):
        """Updates the base styles of editor to the current settings
        @postcondition: base style info is updated

        """
        self.StyleDefault()
        self.SetMargins(4, 0)
        
        lex_manager = syntax.LexerManager()

        # Global default styles for all languages
        self.StyleSetSpec(0, lex_manager.GetStyleByName('default_style'))
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, lex_manager.GetStyleByName('default_style'))
        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR, lex_manager.GetStyleByName('ctrl_char'))
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT, lex_manager.GetStyleByName('brace_good'))
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD, lex_manager.GetStyleByName('brace_bad'))

        sback = lex_manager.GetItemByName('select_style')
        if not sback.IsNull() and len(sback.Back):
            sback = sback.Back
            sback = strutils.HexToRGB(sback)
            sback = wx.Colour(*sback)
        else:
            sback = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)

        # If selection colour is dark make the foreground white
        # else use the default settings.
        if sum(sback.Get()) < 384:
            self.SetSelForeground(True, wx.WHITE)
        else:
            self.SetSelForeground(True, wx.BLACK)
        self.SetSelBackground(True, sback)
        
        default_fore = self.GetDefaultForeColour()

        self.SetCaretForeground(default_fore)
        self.SetCaretLineBack(lex_manager.GetItemByName('caret_line').Back)
        self.Colourise(0, -1)
        
    def GetDefaultForeColour(self, as_hex=False):
        """Gets the foreground color of the default style and returns
        a Colour object. Otherwise returns Black if the default
        style is not found.
        @keyword as_hex: return a hex string or colour object
        @return: wx.Colour of default style foreground or hex value

        """
        fore = syntax.LexerManager().GetItemByName('default_style').Fore
        if not fore:
            fore = u"#000000"

        if not as_hex:
            rgb = strutils.HexToRGB(fore[1:])
            fore = wx.Colour(red=rgb[0], green=rgb[1], blue=rgb[2])
        return fore

class ColorComboBox(wx.combo.OwnerDrawnComboBox):
    
    def __init__(self, parent,colors, choices = [] , style=wx.CB_READONLY,size=(-1,-1)):
        wx.combo.OwnerDrawnComboBox.__init__(self,parent,choices = choices,style=style,size=size)
        self.Colors = colors

    # Overridden from OwnerDrawnComboBox, called to draw each
    # item in the list
    def OnDrawItem(self, dc, rect, item, flags):
        if item == wx.NOT_FOUND:
            # painting the control, but there is no valid item selected yet
            return

        r = wx.Rect(*rect)  # make a copy
        r.Deflate(3, 5)

        penStyle = wx.SOLID
        if item % 11 == 1:
            penStyle = wx.TRANSPARENT
        elif item % 11 == 2:
            penStyle = wx.DOT
        elif item == 3:
            penStyle = wx.LONG_DASH
        elif item == 4:
            penStyle = wx.SHORT_DASH
        elif item == 5:
            penStyle = wx.DOT_DASH
        elif item == 6:
            penStyle = wx.BDIAGONAL_HATCH
        elif item == 7:
            penStyle = wx.CROSSDIAG_HATCH
        elif item == 8:
            penStyle = wx.FDIAGONAL_HATCH
        elif item == 9:
            penStyle = wx.CROSS_HATCH
        elif item == 10:
            penStyle = wx.HORIZONTAL_HATCH
        elif item == 11:
            penStyle = wx.VERTICAL_HATCH
            
        print self.GetString(item),self.Colors[self.GetString(item)]
            
        pen = wx.Pen(dc.GetTextForeground(), 3, penStyle)
        dc.SetPen(pen)
        
        brush = wx.Brush(self.Colors[self.GetString(item)])
        dc.SetBrush(brush)

        if flags & wx.combo.ODCB_PAINTING_CONTROL:
            # for painting the control itself
            dc.DrawRectangle(r.x + 3,(r.y + 4) + ( (r.height/2) - dc.GetCharHeight() )/2,50,self.OnMeasureItem(item))
            dc.DrawText(self.GetString( item ),
                        r.x + 55,
                        (r.y + 4) + ( (r.height/2) - dc.GetCharHeight() )/2
                        )
        else:
            # for painting the items in the popup
            dc.DrawRectangle(r.x + 3,(r.y + 0) + ( (r.height/2) - dc.GetCharHeight() )/2,50,self.OnMeasureItem(item))
            dc.DrawText(self.GetString( item ),
                        r.x + 55,
                        (r.y + 0) + ( (r.height/2) - dc.GetCharHeight() )/2
                        )
           ### dc.DrawLine( r.x+5, r.y+((r.height/4)*3)+1, r.x+r.width - 5, r.y+((r.height/4)*3)+1 )

           
    # Overridden from OwnerDrawnComboBox, called for drawing the
    # background area of each item.
    def OnDrawBackground(self, dc, rect, item, flags):
        # If the item is selected, or its item # iseven, or we are painting the
        # combo control itself, then use the default rendering.
        if (item & 1 == 0 or flags & (wx.combo.ODCB_PAINTING_CONTROL |
                                      wx.combo.ODCB_PAINTING_SELECTED)):
            wx.combo.OwnerDrawnComboBox.OnDrawBackground(self, dc, rect, item, flags)
            return

        # Otherwise, draw every other background with different colour.
        bgCol = wx.Colour(240,240,250)
        dc.SetBrush(wx.Brush(bgCol))
        dc.SetPen(wx.Pen(bgCol))
        dc.DrawRectangleRect(rect);

    # Overridden from OwnerDrawnComboBox, should return the height
    # needed to display an item in the popup, or -1 for default
    def OnMeasureItem(self, item):
        # Simply demonstrate the ability to have variable-height items
        return 24

    # Overridden from OwnerDrawnComboBox.  Callback for item width, or
    # -1 for default/undetermined
    def OnMeasureItemWidth(self, item):
        return -1; # default - will be measured from text width
        
    def SetColor(self,clr):
        sel = self.GetSelColor(clr)
        if sel != wx.NOT_FOUND:
            self.SetSelection(sel)
            return
        if not self.Colors.has_key(_('Custom')):
            self.Append(_('Custom'))
        rgb = strutils.HexToRGB(clr)
        color = wx.Colour(red=rgb[0], green=rgb[1], blue=rgb[2])
        self.Colors[_('Custom')] = color
        self.SetSelection(self.GetCount() - 1)
        
    def GetSelColor(self,clr):
        sel = wx.NOT_FOUND
        for i in range(self.GetCount()):
            clr_name = self.GetString(i)
            if clr.lower() == strutils.RGBToHex(self.Colors[clr_name]):
                sel = i
        return sel

class ColorFontOptionsPanel(wx.Panel):
    """description of class"""
    
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
         
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lexerLabel = wx.StaticText(self, -1, _("Lexers:"))
        
        line_sizer.Add(lexerLabel, 0, wx.ALL,0)
        main_sizer.Add(line_sizer, 0, wx.TOP|wx.LEFT|wx.EXPAND,SPACE)

        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._lexerCombo = wx.ComboBox(self, -1,choices=[], style = wx.CB_READONLY)
        for lexer in syntax.LexerManager().Lexers:
            if lexer.IsVisible():
                self._lexerCombo.Append(lexer.GetShowName(),lexer)
        self._lexerCombo.Bind(wx.EVT_COMBOBOX, self.OnSelectLexer) 

        line_sizer.Add(self._lexerCombo, 1, wx.ALL|wx.EXPAND, 0)
        self._lexerCombo.SetSelection(0)
        defaultButton = wx.Button(self, -1, _("Restore Default(D)"))
        wx.EVT_BUTTON(self, defaultButton.GetId(), self.SetDefaultValue)
        line_sizer.Add(defaultButton, 0, wx.LEFT, SPACE)
        
        main_sizer.Add(line_sizer, 0, wx.LEFT|wx.EXPAND,SPACE)
        
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        font_sizer = wx.BoxSizer(wx.VERTICAL)
        font_sizer.Add(wx.StaticText(self, -1, _("Font(F):")), 0, wx.ALL)
        e = wx.FontEnumerator()
        e.EnumerateFacenames()
        choices = e.GetFacenames()
        choices.sort()
        self._fontCombo = wx.ComboBox(self, -1,choices=choices, style = wx.CB_READONLY)
        self._fontCombo.SetSelection(0)
        font_sizer.Add(self._fontCombo, 1, wx.ALL|wx.EXPAND, 0)
        
        size_sizer = wx.BoxSizer(wx.VERTICAL)
        size_sizer.Add(wx.StaticText(self, -1, _("Size(S):")),0,wx.ALL|wx.EXPAND, 0)
        
        choices = []
        for i in range(6,25):
            choices.append(str(i))
        self._sizeCombo = wx.ComboBox(self, -1,choices=choices, style = wx.CB_DROPDOWN)
        self._sizeCombo.SetSelection(0)
        size_sizer.Add(self._sizeCombo, 1, wx.LEFT|wx.EXPAND, 0)
        
        line_sizer.Add(font_sizer, 1, wx.EXPAND,0)
        line_sizer.Add(size_sizer, 1, wx.LEFT|wx.EXPAND,SPACE)
        
        main_sizer.Add(line_sizer, 1, wx.TOP|wx.LEFT|wx.EXPAND,SPACE)
        
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        style_list = []
        
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(wx.StaticText(self, -1, _("Display Element(E):")), 0, wx.ALL,0)
        self.lb = wx.ListBox(self, -1, choices = style_list, size=(250,200),style = wx.LB_SINGLE)
        wx.EVT_LISTBOX(self,self.lb.GetId(), self.SelectStyle)
        left_sizer.Add(self.lb, 0, wx.TOP,SPACE)
        
        left_sizer.Add(wx.StaticText(self, -1, _("Background Color(B):")), 0, wx.TOP,SPACE)
        
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        colors = [_('Default'),_('Blue'),_('Red'),_('Black'),_('Green'),_('Yellow'),_('White'),_('Reddish Orange'),\
                  _('Aubergine'),_('Violet'),_('Indigo'),_('Yellow Green'),_('Silver'),_('Orange')]
        back_colors = dict()
        back_colors[_('Default')] = wx.Colour(0xFF,  0xFF, 0xFF)
        back_colors[_('Blue')] = wx.Colour(0x00,  0x00, 0xFF)
        back_colors[_('Red')] = wx.Colour(0xFF,  0x00, 0x00)
        back_colors[_('Black')] = wx.Colour(0x00,  0x00, 0x00)
        back_colors[_('Green')] = wx.Colour(0x00,  0xFF, 0x00)
        back_colors[_('Yellow')] = wx.Colour(0xFF,  0xFF, 0x00)
        back_colors[_('White')] = wx.Colour(0xFF,  0xFF, 0xFF)
        back_colors[_('Reddish Orange')] = wx.Colour(0xFF, 0x45,0x00)
        back_colors[_('Aubergine')] = wx.Colour(0xFF, 0x00, 0xFF)
        back_colors[_('Violet')] = wx.Colour(0xEE, 0x82, 0xEE)
        back_colors[_('Indigo')] = wx.Colour(0x4B, 0x00, 0x82)
        back_colors[_('Yellow Green')] = wx.Colour(0xAD,0xFF,0x2F)
        back_colors[_('Silver')] = wx.Colour(0xC0, 0xC0, 0xC0)
        back_colors[_('Orange')] = wx.Colour( 0xFF, 0xA5,0x00)
        self.back_color_combo = ColorComboBox(self,back_colors,choices = colors,size=(150,defaultButton.GetSize().GetHeight()))
        self.back_color_combo.SetSelection(0)
        line_sizer.Add(self.back_color_combo, 0, wx.ALL,0)
        self.fore_color_button = wx.Button(self, -1, _("Custom(C)..."))
        line_sizer.Add(self.fore_color_button, 0, wx.LEFT,SPACE)
        wx.EVT_BUTTON(self, self.fore_color_button.GetId(), self.ShowCustomColorDialog)
        left_sizer.Add(line_sizer, 0, wx.ALL,0)
        
        left_sizer.Add(wx.StaticText(self, -1, _("Foreground Color(F):")), 0, wx.TOP,SPACE)
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        fore_colors = copy.deepcopy(back_colors)
        fore_colors[_('Default')] = wx.Colour(0x00,  0x00, 0x00)
        self.fore_color_combo = ColorComboBox(self,fore_colors,choices = colors,size=(150,defaultButton.GetSize().GetHeight()))
        self.fore_color_combo.SetSelection(0)
        line_sizer.Add(self.fore_color_combo, 0, wx.ALL,0)
        self.back_color_button = wx.Button(self, -1, _("Custom(C)..."))
        wx.EVT_BUTTON(self, self.back_color_button.GetId(), self.ShowCustomColorDialog)
        line_sizer.Add(self.back_color_button, 0, wx.LEFT,SPACE)
        left_sizer.Add(line_sizer, 0, wx.ALL,0)
        
        sbox = wx.StaticBox(self, -1, _("Text Option"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        self.bold_chkbox = wx.CheckBox(self, label = _("Bold"))
        sboxSizer.Add(self.bold_chkbox , flag=wx.LEFT, border=HALF_SPACE)
        self.italic_chkbox = wx.CheckBox(self, label = _("Italic"))
        sboxSizer.Add(self.italic_chkbox,flag=wx.LEFT|wx.TOP, border=HALF_SPACE)
        self.underline_chkbox = wx.CheckBox(self, label = _("Underline"))
        sboxSizer.Add(self.underline_chkbox,flag=wx.LEFT|wx.TOP, border=HALF_SPACE)
        left_sizer.Add(sboxSizer, flag=wx.EXPAND|wx.RIGHT|wx.TOP , border=SPACE) 
        bottom_sizer.Add(left_sizer, 0, wx.TOP|wx.EXPAND,0)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        line_sizer.Add(wx.StaticText(self, -1, _("Code Sample(P):"),size=(200,-1)), 1, flag=wx.LEFT|wx.EXPAND,border=0)
        line_sizer.Add(wx.StaticText(self, -1, _("Themes:")), 0, wx.LEFT|wx.RIGHT,border=SPACE)
        themes,theme_index = syntax.LexerManager.GetThemes()
        self._themCombo = wx.ComboBox(self, -1,choices = themes, style = wx.CB_READONLY)
        self._themCombo.Bind(wx.EVT_COMBOBOX, self.OnSelectTheme) 
        if theme_index != -1:
            self._themCombo.SetSelection(theme_index)
        line_sizer.Add(self._themCombo,0, wx.ALL,0)
        right_sizer.Add(line_sizer,0,wx.ALL,0)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.code_sample_ctrl = CodeSampleCtrl(self,-1,size=(200,400))
        self.code_sample_ctrl.HideLineNumber()
        lineSizer.Add(self.code_sample_ctrl, 1, flag =wx.EXPAND|wx.RIGHT,border=0)
        right_sizer.Add(lineSizer, 1, flag=wx.EXPAND|wx.TOP,border=HALF_SPACE)
        bottom_sizer.Add(right_sizer, 0, wx.LEFT|wx.EXPAND,SPACE)
        
        main_sizer.Add(bottom_sizer, 0, wx.TOP|wx.LEFT|wx.EXPAND|wx.BOTTOM,SPACE)
        
        self.SetSizer(main_sizer)
        self.Fit()
        self.GetLexerStyles(self._lexerCombo.GetSelection())
        
    def SetDefaultValue(self, event):
        pass

    def ShowCustomColorDialog(self, event):
        dlg = wx.ColourDialog(self)
        # Ensure the full colour dialog is displayed, 
        # not the abbreviated version.
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            # If the user selected OK, then the dialog's wx.ColourData will
            # contain valid information. Fetch the data ...
            data = dlg.GetColourData()
            # ... then do something with it. The actual colour data will be
            # returned as a three-tuple (r, g, b) in this particular case.
            self.log.WriteText('You selected: %s\n' % str(data.GetColour().Get()))
        # Once the dialog is destroyed, Mr. wx.ColourData is no longer your
        # friend. Don't use it again!
        dlg.Destroy()
        
    def OnSelectLexer(self, event):
        selection = event.GetSelection()
        self.GetLexerStyles(selection)
        
    def OnSelectTheme(self, event):
        theme_name = event.GetString()
        style_sheet_path = os.path.join(appdirs.GetAppDataDirLocation(),"styles")
        theme_style_sheet = os.path.join(style_sheet_path,theme_name + consts.THEME_FILE_EXT)
        old_theme = syntax.LexerManager().Theme
        syntax.LexerManager().LoadThemeSheet(theme_style_sheet)
        self.code_sample_ctrl.UpdateStyles()
        syntax.LexerManager().Theme = old_theme
        
    def GetLexerStyles(self,selection):
        lexer = self._lexerCombo.GetClientData(selection)
        self.lb.Clear()
        for i,style in enumerate(lexer.StyleItems):
            self.lb.Insert(style.StyleName, i)
            self.lb.SetClientData(i, style)
        
        self.lb.SetSelection(0)
        self.code_sample_ctrl.SetText(lexer.GetSampleCode())
        self.code_sample_ctrl.SetLangLexer(lexer)
        self.SelectFontSize(0)
        
    def OnOK(self, optionsDialog):
        config = wx.ConfigBase_Get()
        theme = self._themCombo.GetString(self._themCombo.GetSelection())
        config.Write(THEME_KEY,theme)
        
        openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if isinstance(openDoc,STCTextEditor.TextDocument):
                docView = openDoc.GetFirstView()
                syntax.LexerManager().UpdateAllStyles(docView.GetCtrl(),theme)
        
    def SelectStyle(self,event):
        self.SelectFontSize(event.GetSelection())
        
    def SelectFontSize(self,selection):
        style = self.lb.GetClientData(selection)
        self.fore_color_combo.SetColor(style.Fore)
        self.back_color_combo.SetColor(style.Back)
        self._fontCombo.SetValue(style.Face)
        self._sizeCombo.SetValue(style.Size)
