import wx
import os
import noval.tool.Singleton as Singleton
import lang
import re
from style import *
import noval.util.appdirs as appdirs
import json
import noval.tool.consts as consts
import noval.util.strutils as strutils

RE_ESS_COMMENT = re.compile("\/\*[^*]*\*+([^/][^*]*\*+)*\/")
RE_HEX_STR = re.compile("#[0-9a-fA-F]{3,6}")
RE_ESS_SCALAR = re.compile("\%\([a-zA-Z0-9]+\)")


class LexerManager(object):
    """Class Object for managing loaded syntax data. The manager
    is only created once as a singleton and shared amongst all
    editor windows

    """
    __metaclass__ = Singleton.SingletonNew
    
    THEMES = dict()         # Static cache for loaded theme set(s)
    
    FONT_PRIMARY   = u"primary"
    FONT_SECONDARY = u"secondary"
    FONT_SIZE      = u"size"
    FONT_SIZE2     = u"size2"
    FONT_SIZE3     = u"size3"
    
    def __init__(self, config=None):
        """Initialize a syntax manager. If the optional
        value config is set the mapping of extensions to
        lexers will be loaded from a config file.
        @keyword config: path of config file to load file extension config from

        """

##        self._extreg = ExtensionRegister()
##        self._config = config
##        self._loaded = dict()
##
##        # Syntax mode extensions
##        self._extensions = dict()   # loaded extensions "py" : PythonMode()
##
##        self.InitConfig()
        self.fonts = self.GetFontDictionary()
        self.syntax_set = []
        self.lexers = []
        self.style_set = ""
        theme_name = wx.ConfigBase_Get().Read(consts.THEME_KEY, consts.DEFAULT_THEME_NAME)
        if theme_name:
            style_sheet_path = os.path.join(appdirs.GetAppDataDirLocation(),"styles")
            theme_style_sheet = os.path.join(style_sheet_path,theme_name + consts.THEME_FILE_EXT)
            self.LoadThemeSheet(theme_style_sheet)

    def Register(self,lang_lexer):
        
        for lexer in self.lexers:
            if lang_lexer == lexer:
                return False
        self.lexers.append(lang_lexer)
        return True
        

    def UnRegister(self,lang_lexer):
        if -1 == self.lexers.index(lang_lexer):
            return False
        self.lexers.remove(lang_lexer)
        return True
            

    def _ExtToMod(self, ext):
        """Gets the name of the module that is is associated
        with the given extension or None in the event that there
        is no association or that the association is plain text.
        @param ext: extension string to lookup module for

        """
        ftype = self._extreg.FileTypeFromExt(ext)
        lexdat = synglob.LANG_MAP.get(ftype)
        mod = None
        if lexdat:
            mod = lexdat[MODULE]
        return mod

    def GetLangId(self, ext):
        """Gets the language Id that is associated with the file
        extension.
        @param ext: extension to get lang id for

        """
        ftype = self._extreg.FileTypeFromExt(ext)
        return synglob.LANG_MAP[ftype][LANG_ID]

    def InitConfig(self):
        """Initialize the SyntaxMgr's configuration state"""
        if self._config:
            self._extreg.LoadFromConfig(self._config)
        else:
            self._extreg.LoadDefault()

        if self._config:
            self.LoadExtensions(self._config)

    def IsModLoaded(self, modname):
        """Checks if a module has already been loaded
        @param modname: name of module to lookup

        """
        if modname in self._loaded:
            return True
        else:
            return False

    def LoadModule(self, modname):
        """Dynamically loads a module by name. The loading is only
        done if the modules data set is not already being managed
        @param modname: name of syntax module to load

        """
        if modname == None:
            return False
        if not self.IsModLoaded(modname):
            try:
                self._loaded[modname] = __import__(modname, globals(), 
                                                   locals(), [''])
            except ImportError, msg:
                return False
        return True

    def SaveState(self):
        """Saves the current configuration state of the manager to
        disk for use in other sessions.
        @return: whether save was successful or not

        """
        if not self._config or not os.path.exists(self._config):
            return False
        path = os.path.join(self._config, self._extreg.config)
        try:
            file_h = open(path, "wb")
            file_h.write(str(self._extreg))
            file_h.close()
        except IOError:
            return False
        return True

    def GetSyntaxData(self, ext):
        """Fetches the language data based on a file extension string. The file
        extension is used to look up the default lexer actions from the EXT_REG
        dictionary.
        @see: L{synglob}
        @param ext: a string representing the file extension
        @return: SyntaxData object

        """
        # The Return Value
        lexer = self.GetLexer(self.GetLangIdFromExt(ext))
        syn_data = lexer.StyleItems
        return syn_data

    def LoadExtensions(self, path):
        """Load all extensions found at the extension path
        @param path: path to look for extension on

        """
        for fname in os.listdir(path):
            if fname.endswith(u".edxml"):
                fpath = os.path.join(path, fname)
                modeh = synxml.LoadHandler(fpath)

                if modeh.IsOk():
                    sdata = SynExtensionDelegate(modeh)
                    self._extensions[sdata.GetXmlObject().GetLanguage()] = sdata
                else:
                    pass
                    #TODO: report error

    def SetConfigDir(self, path):
        """Set the path to locate config information at. The SyntaxMgr will
        look for file type associations in a file called synmap and will load
        syntax extensions from .edxml files found at this path.
        @param path: string

        """
        self._config = path


    def GetLexer(self,lang_id):
        for lexer in self.lexers:
            if lexer.LangId == lang_id:
                return lexer
        return self.GetLexer(lang.ID_LANG_TXT)
        
    def GetLangIdFromExt(self,ext):
        for lexer in self.lexers:
            if lexer.ContainExt(ext):
                return lexer.LangId
        return lang.ID_LANG_TXT
        
    def GetLangIdFromDescription(self,desc):
        return lang.GetIdFromDescription(desc)
        
    @property
    def Lexers(self):
        return self.lexers

    def LoadThemeSheet(self, theme_style_sheet, force=False):
        """Loads a custom style sheet and returns True on success
        @param style_sheet: path to style sheet to load
        @keyword force: Force re-parse of style sheet, default is to use cached
                        data when available
        @return: whether style sheet was loaded or not

        """
        if isinstance(theme_style_sheet, basestring) and os.path.exists(theme_style_sheet) and \
           ((force or theme_style_sheet not in LexerManager.THEMES) or \
             theme_style_sheet != self.style_set):
            #try:
            with open(theme_style_sheet) as reader:
                style_data = self.ParseStyleData(reader.read())
                ret_val = self.SetStyles(theme_style_sheet, style_data)
                return ret_val
            #except Exception, msg:
             #   self.LOG("[ed_style][err] Failed to parse style data for %s:" % style_sheet)
              #  return False
        elif theme_style_sheet not in LexerManager.THEMES:
            self.LOG("[ed_style][warn] Style sheet %s does not exists" % style_sheet)
            # Reset to default style
            if Profile_Get('SYNTHEME') != 'default':
                Profile_Set('SYNTHEME', 'default')
                self.SetStyles('default', DEF_STYLE_DICT)
            return False
        else:
            return True
            

    def ParseStyleData(self, style_data):
        """Parses a string style definitions read from an Editra Style Sheet.
        @param style_data: style sheet data string
        @return: dictionary of StyleItems constructed from the style sheet data.

        """
        # Remove all comments
        style_data = RE_ESS_COMMENT.sub(u'', style_data)

        # Compact data into a contiguous string
        style_data = style_data.replace(u"\r\n", u"").replace(u"\n", u"")
        style_data = style_data.replace(u"\t", u"")
#        style_data = style_data.replace(u" ", u"") # support old style

        ## Build style data tree
        # Tree Level 1 split tag from data
        style_tree = [style.split(u"{") for style in style_data.split(u'}')]
        if len(style_tree) and len(style_tree[-1]) and not style_tree[-1][0]:
            style_tree.pop()

        # Tree Level 2 Build small trees of tag and style attributes
        # Tree Level 3 Branch tree into TAG => Attr => Value String
        ttree = list(style_tree)
        for branch in ttree:
            # Check for level 1 syntax errors
            if len(branch) != 2:
                self.LOG("[ed_style][err] There was an error parsing "
                         "the syntax data from " + self.style_set)
                self.LOG("[ed_style][err] Missing a { or } in Def: " + repr(branch[0]))
                ttree.remove(branch)
                continue

            tmp2 = [leaf.strip().split(u":")
                    for leaf in branch[1].strip().split(u";")]
            if len(tmp2) and not tmp2[-1][0]:
                tmp2.pop()
            branch[1] = tmp2
        style_tree = ttree

        # Check for L2/L3 Syntax errors and build a clean dictionary
        # of Tags => Valid Attributes
        style_dict = dict()
        for branch in style_tree:
            value = list()
            tag = branch[0].replace(u" ", u"")
            for leaf in branch[1]:
                # Remove any remaining whitespace
                leaf = [part.strip() for part in leaf]
                if len(leaf) != 2:
                    self.LOG("[ed_style][err] Missing a : or ; in the "
                             "declaration of %s" % tag)
                elif leaf[0] not in STY_ATTRIBUTES:
                    self.LOG(("[ed_style][warn] Unknown style attribute: %s"
                             ", In declaration of %s") % (leaf[0], tag))
                else:
                    value.append(leaf)

            # Skip all leafless branches
            if len(value) != 0:
                style_dict[tag] = value

        # Validate leaf values and format into style string
        rdict = dict()
        for style_def in style_dict:
            if not style_def[0][0].isalpha():
                self.LOG("[ed_style][err] The style def %s is not a "
                         "valid name" % style_def[0])
            else:
                style_str = u""
                # Check each definition and validate its items
                for attrib in style_dict[style_def]:
                    values = [ val for val in attrib[1].split()
                               if val != u"" ]

                    v1ok = v2ok = False
                    # Check that colors are a hex string
                    n_values = len(values)
                    if n_values and \
                       attrib[0] in "fore back" and RE_HEX_STR.match(values[0]):
                        v1ok = True
                    elif n_values and attrib[0] == "size":
                        if RE_ESS_SCALAR.match(values[0]) or values[0].isdigit():
                            v1ok = True
                        else:
                            self.LOG("[ed_style][warn] Bad value in %s"
                                     " the value %s is invalid." % \
                                     (attrib[0], values[0]))
                    elif n_values and attrib[0] == "face":
                        # Font names may have spaces in them so join the
                        # name of the font into one item.
                        if n_values > 1 and values[1] not in STY_EX_ATTRIBUTES:
                            tmp = list()
                            for val in list(values):
                                if val not in STY_EX_ATTRIBUTES:
                                    tmp.append(val)
                                    values.remove(val)
                                else:
                                    break
                            values = [u' '.join(tmp),] + values
                        v1ok = True
                    elif n_values and attrib[0] == "modifiers":
                        v1ok = True

                    # Check extra attributes
                    if len(values) > 1:
                        for value in values[1:]:
                            if value not in STY_EX_ATTRIBUTES:
                                self.LOG("[ed_style][warn] Unknown extra " + \
                                         "attribute '" + values[1] + \
                                         "' in attribute: " + attrib[0])
                                break
                            else:
                                v2ok = True

                    if v1ok and v2ok:
                        value = u",".join(values)
                    elif v1ok:
                        value = values[0]
                    else:
                        continue

                    style_str = u",".join([style_str,
                                           u":".join([attrib[0], value])])

                # Build up the StyleItem Dictionary
                if style_str != u"":
                    new_item = StyleItem()
                    value = style_str.strip(u",")
                    if isinstance(value, basestring):
                        new_item.SetAttrFromStr(value)
                    rdict[style_def] = new_item

        return rdict
        

    def SetStyles(self, name, style_dict, nomerge=False):
        """Sets the managers style data and returns True on success.
        @param name: name to store dictionary in cache under
        @param style_dict: dictionary of style items to use as managers style
                           set.
        @keyword nomerge: merge against default set or not

        """
        if nomerge:
            self.style_set = name
            StyleMgr.STYLES[name] = self.PackStyleSet(style_dict)
            return True

        # Merge the given style set with the default set to fill in any
        # unset attributes/tags
        if isinstance(style_dict, dict):
            # Check for bad data
            for style in style_dict.values():
                if not isinstance(style, StyleItem):
                    self.LOG("[ed_style][err] Invalid data in style dictionary")
                    self.style_set = 'default'
                    return False

            self.style_set = name
            defaultd = DEF_STYLE_DICT
            dstyle = style_dict.get('default_style', None)
            if dstyle is None:
                self.LOG("[ed_style][warn] default_style is undefined")
                style_dict['default_style'] = defaultd['default_style'].Clone()

            # Set any undefined styles to match the default_style
            for tag in defaultd:
                if tag not in style_dict:
                    if tag in ('select_style',):
                        style_dict[tag] = NullStyleItem()
                    else:
                        ###style_dict[tag] = style_dict['default_style'].Clone()
                        style_dict[tag] = NullStyleItem()

            ###LexerManager.THEMES[name] = self.PackStyleSet(style_dict)
            LexerManager.THEMES[name] = style_dict
            return True
        else:
            self.LOG("[ed_style][err] SetStyles expects a " \
                     "dictionary of StyleItems")
            return False
            
    def PackStyleSet(self, style_set):
        """Checks the difference of each item in the style set as
        compared to the default_style tag and packs any unset value
        in the item to be equal to the default style.
        @param style_set: style set to pack
        @return: style_set with all unset attributes set to match default style

        """
        if isinstance(style_set, dict) and 'default_style' in style_set:
            default = style_set['default_style']
            for tag in style_set:
                if style_set[tag].IsNull():
                    continue
                if not style_set[tag].Face:
                    style_set[tag].SetFace(default.Face)
                if not style_set[tag].Fore:
                    style_set[tag].SetFore(default.Fore)
                if not style_set[tag].Back:
                    style_set[tag].SetBack(default.Back)
                if not style_set[tag].Size:
                    style_set[tag].SetSize(default.Size)

            # Now need to pack in undefined styles that are part of
            # the standard set.
            for tag in DEF_STYLE_DICT.keys():
                if tag not in style_set:
                    if tag == 'select_style':
                        style_set[tag] = NullStyleItem()
                    else:
                        style_set[tag] = default.Clone()
        else:
            pass
        return style_set
        
    @classmethod
    def GetStyleSheet(cls,sheet_name=None):
        """Finds the current style sheet and returns its path. The
        lookup is done by first looking in the users config directory
        and if it is not found there it looks for one on the system
        level and if that fails it returns None.
        @param sheet_name: style sheet to look for
        @return: full path to style sheet

        """
        if sheet_name:
            style_name = sheet_name
        else:
            style_name = wx.ConfigBase_Get().Read('SYNTHEME', 'Default')
        style = style_name + consts.THEME_FILE_EXT
        style = style.lower()
        # Get Correct Filename if it exists
        for sheet in cls.GetResourceFiles():
            if sheet.lower() == style:
                style = sheet
                break

        user_data_path = os.path.join(appdirs.getAppDataFolder(),"styles",style)
        sys_data_path = os.path.join(appdirs.GetAppDataDirLocation(),"styles", style)
        if os.path.exists(user_data_path):
            return user_data_path
        elif os.path.exists(sys_data_path):
            return sys_data_path
        else:
            return None
            
    @classmethod
    def GetResourceFiles(cls):
        res_files = []
        style_sheet_path = os.path.join(appdirs.GetAppDataDirLocation(),"styles")
        for name in os.listdir(style_sheet_path):
            if name.endswith(consts.THEME_FILE_EXT):
                res_files.append(name)
        return res_files
        
    @classmethod
    def GetThemes(cls):
        theme_name = wx.ConfigBase_Get().Read(consts.THEME_KEY, consts.DEFAULT_THEME_NAME)
        theme_index = -1
        theme_names = []
        style_sheet_path = os.path.join(appdirs.GetAppDataDirLocation(),"styles")
        for i,file_path in enumerate(os.listdir(style_sheet_path)):
            if file_path.endswith(consts.THEME_FILE_EXT):
                name = strutils.GetFilenameWithoutExt(file_path)
                if name.lower() == theme_name.lower():
                    theme_index = i
                theme_names.append(name)
        return theme_names,theme_index
        
    def GetStyleSet(self):
        """Returns the current set of styles or the default set if
        there is no current set.
        @return: current style set dictionary

        """
        return LexerManager.THEMES.get(self.style_set, DEF_STYLE_DICT)
        
    def HasNamedStyle(self, name):
        """Checks if a style has been set/loaded or not
        @param name: tag name of style to look for
        @return: whether item is in style set or not

        """
        return name in self.GetStyleSet()
        
    def GetStyleByName(self, name):
        """Gets and returns a style string using its name for the search
        @param name: tag name of style to get
        @return: style item in string form

        """
        if self.HasNamedStyle(name):
            style = self.GetItemByName(name)
            stystr = style.GetStyleSpecStr()
            return stystr
        else:
            return u""
            
    def GetGlobalItemByName(self, key_name):
        lexer = self.GetLexer(lang.ID_LANG_TXT)
        for global_style in lexer.StyleItems:
            if global_style.KeyName == key_name:
                return global_style
        return None
        
    def GetGlobalStyleByName(self, key_name):
        global_style = self.GetGlobalItemByName(key_name)
        if global_style is None:
            return ""
        return global_style.GetStyleSpec()
        
    def GetItemByKeyName(self,key_name):
        config = wx.ConfigBase_Get()
        style_data = config.Read(key_name,"")
        if not style_data:
            return None
        item = StyleItem()
        item.SetAttrFromStr(style_data)
        return item
            
    def GetItemByName(self, name):
        """Gets and returns a style item using its name for the search
        @param name: tag name of style item to get
        @return: style item (may be empty/null style item)

        """
        scheme = self.GetStyleSet()
        if name in scheme:
            item = scheme[name]
            # Set font value if need be
            ival = unicode(item)
            if u"%" in ival:
                val = ival % self.fonts
                item = StyleItem()
                item.SetAttrFromStr(val)
            return item
        else:
            return StyleItem()
            
    def GetFontDictionary(self, default=True):
        """Does a system lookup to build a default set of fonts using
        ten point fonts as the standard size.
        @keyword default: return the default dictionary of fonts, else return
                          the current running dictionary of fonts if it exists.
        @return: font dictionary (primary, secondary) + (size, size2)

        """
        if hasattr(self, 'fonts') and not default:
            return self.fonts

        font = wx.ConfigBase_Get().Read(consts.PRIMARY_FONT_KEY, '')
        if font != '':
            font_data = json.loads(font)
            mfont =  wx.Font(font_data['size'],wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL,faceName=font_data['font'])
        else:
            mfont = self.GetDefaultFont()
            data_str = json.dumps({'font':mfont.GetFaceName(),'size':mfont.GetPointSize()})
            wx.ConfigBase_Get().Write(consts.PRIMARY_FONT_KEY, data_str)
        primary = mfont.GetFaceName()

        font = wx.ConfigBase_Get().Read(consts.SECONDARY_FONT_KEY, '')
        if font != '':
            font_data = json.loads(font)
            font = wx.Font(font_data['size'],wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL,faceName=font_data['font'])
        else:
            if wx.Platform == '__WXMSW__':
                font = wx.Font(consts.DEFAULT_FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL,\
                                faceName = consts.DEFAULT_FONT_NAME)
            else:
                font = wx.Font(consts.DEFAULT_FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL)
            data_str = json.dumps({'font':font.GetFaceName(),'size':font.GetPointSize()})
            wx.ConfigBase_Get().Write(consts.SECONDARY_FONT_KEY, data_str)
        secondary = font.GetFaceName()
        faces = {
                  self.FONT_PRIMARY   : primary,
                  self.FONT_SECONDARY : secondary,
                  self.FONT_SIZE  : mfont.GetPointSize(),
                  self.FONT_SIZE2 : font.GetPointSize(),
                  self.FONT_SIZE3 : mfont.GetPointSize() - 2
                 }
        return faces

    def UpdateAllStyles(self, text_ctrl,spec_style=None):
        """Refreshes all the styles and attributes of the control
        @param spec_style: style scheme name
        @postcondition: style scheme is set to specified style

        """
        if spec_style and (spec_style != self.style_set):
            self.LoadThemeSheet(self.GetStyleSheet(spec_style), force=True)
        text_ctrl.SetSyntax(self.GetSyntaxParams())
        
    def GetSyntaxParams(self):
        """Get the set of syntax parameters
        @return: list

        """
        return self.syntax_set
        
    def GetShowNameList(self):
        name_list = []
        for lexer in self.lexers:
            if lexer.IsVisible():
                name_list.append(lexer.GetShowName())
        return name_list
    
    @property
    def Theme(self):
        return self.style_set
        
    @Theme.setter
    def Theme(self,name):
        self.style_set = name
        
    def GetFontAndColorFromConfig(self):
        config = wx.ConfigBase_Get()
        fontData = config.Read(consts.PRIMARY_FONT_KEY, "")
        if fontData:
            font_data = json.loads(fontData)
            font =  wx.Font(font_data['size'],wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL,faceName=font_data['font'])
        else:
           font = self.GetDefaultFont() 
        color = self.GetDefaultColor()
        colorData = config.Read("TextEditorColor", "")
        if colorData:
            red = int("0x" + colorData[0:2], 16)
            green = int("0x" + colorData[2:4], 16)
            blue = int("0x" + colorData[4:6], 16)
            color = wx.Colour(red, green, blue)
        return font, color
        
    def GetDefaultFont(self):
        if wx.Platform == '__WXMSW__':
            font = wx.Font(consts.DEFAULT_FONT_SIZE, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_NORMAL,faceName = consts.DEFAULT_FONT_NAME)
        else:
            font = wx.Font(consts.DEFAULT_FONT_SIZE, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_NORMAL)
        return font
        
    def GetDefaultColor(self):
        """ Subclasses should override this """
        return wx.BLACK
        
    def SetGlobalFont(self,fontface="", size=-1):
        """Sets one of the fonts in the global font set by tag
        and sets it to the named font. Returns true on success.
        @param fonttag: font type identifier key
        @param fontface: face name to set global font to

        """
        if hasattr(self, 'fonts'):
            global_style = self.GetGlobalItemByName(consts.GLOBAL_STYLE_NAME)
            if fontface != "":
                self.fonts[self.FONT_PRIMARY] = fontface
                global_style.SetFace(fontface)
            if size > 0:
                self.fonts[self.FONT_SIZE] = size
                global_style.SetSize(str(size))
            return True
        else:
            return False
            
    def SetGlobalFontColor(self,back="", fore=""):
        """Sets one of the fonts in the global font set by tag
        and sets it to the named font. Returns true on success.
        @param fonttag: font type identifier key
        @param fontface: face name to set global font to

        """

        global_style = self.GetGlobalItemByName(consts.GLOBAL_STYLE_NAME)
        if back != "":
            global_style.SetBack(back)
        if fore != "":
            global_style.SetFore(fore)
        
def NullStyleItem():
    """Create a null style item
    @return: empty style item that cannot be merged

    """
    item = StyleItem()
    item.null = True
    return item
        

DEF_STYLE_DICT = \
        {'brace_good' : StyleItem("#FFFFFF", "#0000FF", ex=["bold",]),
         'brace_bad'  : StyleItem(back="#FF0000", ex=["bold",]),
         'calltip'    : StyleItem("#404040", "#FFFFB8"),
         'caret_line' : StyleItem(back="#D8F8FF"),
         'ctrl_char'  : StyleItem(),
         'line_num'   : StyleItem(back="#C0C0C0", face="%(secondary)s", \
                                  size="%(size3)d"),
         'array_style': StyleItem("#EE8B02",
                                  face="%(secondary)s",
                                  ex=["bold",]),
         'btick_style': StyleItem("#8959F6", size="%(size)d", ex=["bold",]),
         'default_style': StyleItem("#000000", "#F6F6F6", \
                                    "%(primary)s", "%(size)d"),
         'char_style' : StyleItem("#FF3AFF"),
         'class_style' : StyleItem("#2E8B57", ex=["bold",]),
         'class2_style' : StyleItem("#2E8B57", ex=["bold",]),
         'comment_style' : StyleItem("#838383"),
         'decor_style' : StyleItem("#BA0EEA", face="%(secondary)s",
                                   ex=["italic",]),
         'directive_style' : StyleItem("#0000FF", face="%(secondary)s",
                                       ex=["bold",]),
         'dockey_style' : StyleItem("#0000FF"),
         'edge_style'   : StyleItem(), # inherit from default
         'error_style' : StyleItem("#DD0101", face="%(secondary)s",
                                    ex=["bold",]),
         'foldmargin_style' : StyleItem(back="#D1D1D1"),
         'funct_style' : StyleItem("#008B8B", ex=["italic",]),
         'global_style' : StyleItem("#007F7F", face="%(secondary)s",
                                    ex=["bold",]),
         'guide_style' : StyleItem("#838383"),
         'here_style' : StyleItem("#CA61CA", face="%(secondary)s",
                                  ex=["bold",]),
         'ideol_style' : StyleItem("#E0C0E0", face="%(secondary)s"),
         'keyword_style' : StyleItem("#A52B2B", ex=["bold",]),
         'keyword2_style' : StyleItem("#2E8B57", ex=["bold",]),
         'keyword3_style' : StyleItem("#008B8B", ex=["bold",]),
         'keyword4_style' : StyleItem("#9D2424"),
         'marker_style' : StyleItem("#FFFFFF", "#000000"),
         'number_style' : StyleItem("#DD0101"),
         'number2_style' : StyleItem("#DD0101", ex=["bold",]),
         'operator_style' : StyleItem("#000000", face="%(primary)s",
                                      ex=["bold",]),
         'pre_style' : StyleItem("#AB39F2", ex=["bold",]),
         'pre2_style' : StyleItem("#AB39F2", "#FFFFFF", ex=["bold",]),
         'regex_style' : StyleItem("#008B8B"),
         'scalar_style' : StyleItem("#AB37F2", face="%(secondary)s",
                                    ex=["bold",]),
         'scalar2_style' : StyleItem("#AB37F2", face="%(secondary)s"),
         'select_style' : NullStyleItem(), # Use system default colour
         'string_style' : StyleItem("#FF3AFF", ex=["bold",]),
         'stringeol_style' : StyleItem("#000000", "#EEC0EE",
                                       "%(secondary)s", ex=["bold", "eol"]),
         'unknown_style' : StyleItem("#FFFFFF", "#DD0101", ex=["bold", "eol"]),
         'userkw_style' : StyleItem()
         }
         
