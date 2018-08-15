import wx
import syntax
import noval.tool.consts as consts
import lang

STY_ATTRIBUTES = (consts.FACE_ATTR_NAME, consts.FORE_ATTR_NAME, consts.BACK_ATTR_NAME, consts.SIZE_ATTR_NAME, u"modifiers")
STY_EX_ATTRIBUTES  = (consts.EOL_ATTR_NAME, consts.BOLD_ATTR_NAME, consts.ITALIC_ATTR_NAME, consts.UNDERLINE_ATTR_NAME)

STYLE_KEY = "/NOV_Styles"

def getStyleKeyName(lang,keyName):
    return "%s/%s/%s" % (STYLE_KEY, lang.replace("/", '|'), keyName)

class StyleItem(object):
    """description of class"""
    
    def __init__(self,fore=u"", back=u"", face=u"", size=u"", ex=None):
        super(StyleItem, self).__init__()
        self.size = size
        self.back = back
        self.fore = fore
        self.face = face
        self.bold = False
        self.italic = False
        self.eol = False
        self.underline = False
        self.null = False
        if ex is None:
            ex = list()
        self._exattr = ex
        
    def IsNull(self):
        """Return whether the item is null or not
        @return: bool

        """
        return self.null
        
    @property
    def Size(self):
        return self.size
        
    @property
    def Back(self):
        return self.back
        
    @property
    def Fore(self):
        return self.fore
        
    @property
    def Face(self):
        return self.face
        
    @property
    def Bold(self):
        return self.bold
        
    @property
    def Italic(self):
        return self.italic
        
    @property
    def Underline(self):
        return self.underline
        
    @property
    def Eol(self):
        return self.eol
        
    def __str__(self):
        """Convert StyleItem to string"""
        uni = unicode(self)
        return uni.encode('utf-8')

    def __unicode__(self):
        """Converts StyleItem to Unicode
        @note: This return string is in a format that can be accepted by
               Scintilla. No spaces may be in the string after the ':'.
        @return: Unicode representation of the StyleItem

        """
        style_str = list()
        if self.Fore:
            style_str.append(u"fore:%s" % self.Fore)
        if self.Back:
            style_str.append(u"back:%s" % self.Back)
        if self.Face:
            style_str.append(u"face:%s" % self.Face)
        if self.Size:
            style_str.append(u"size:%s" % unicode(self.Size))
        if len(self._exattr):
            style_str.append(u"modifiers:" +  u','.join(self._exattr))

        style_str = u",".join(style_str)
        return style_str.rstrip(u",")
        
    def Clone(self):
        """Make and return a copy of this object"""
        nitem = StyleItem(self.Fore, self.Back,
                          self.Face, self.Size,
                          None)
        if self.null:
            nitem.Nullify()
        return nitem
        
    def SetBack(self, back, ex=wx.EmptyString):
        """Sets the Background Value
        @param back: hex color string, or None to clear attribute
        @keyword ex: extra attribute (i.e bold, italic, underline)

        """
        self.null = False
        if back is None:
            back = u''
        self.back = back
        if ex and ex not in self._exattr:
            self._exattr.append(ex)

    def SetFace(self, face, ex=wx.EmptyString):
        """Sets the Face Value
        @param face: font name string, or None to clear attribute
        @keyword ex: extra attribute (i.e bold, italic, underline)

        """
        self.null = False
        if face is None:
            face = u''
        self.face = face
        if ex and ex not in self._exattr:
            self._exattr.append(ex)

    def SetFore(self, fore, ex=wx.EmptyString):
        """Sets the Foreground Value
        @param fore: hex color string, or None to clear attribute
        @keyword ex: extra attribute (i.e bold, italic, underline)

        """
        self.null = False
        if fore is None:
            fore = u''
        self.fore = fore
        if ex and ex not in self._exattr:
            self._exattr.append(ex)

    def SetSize(self, size, ex=wx.EmptyString):
        """Sets the Font Size Value
        @param size: font point size, or None to clear attribute
        @keyword ex: extra attribute (i.e bold, italic, underline)

        """
        self.null = False
        if size is None:
            size = u''
        self.size = unicode(size)
        if ex and ex not in self._exattr:
            self._exattr.append(ex)
            
    #---- Set Functions ----#
    def SetAttrFromStr(self, style_str):
        """Takes style string and sets the objects attributes
        by parsing the string for the values. Only sets or
        overwrites values does not zero out previously set values.
        Returning True if value(s) are set or false otherwise.
        @param style_str: style information string (i.e fore:#888444)

        """
        self.null = False
        last_set = wx.EmptyString
        for atom in style_str.split(u','):
            attrib = atom.split(u':')
            if len(attrib) == 2 and attrib[0] in STY_ATTRIBUTES:
                last_set = attrib[0]
                if last_set == u"modifiers":
                    self.SetExAttr(attrib[1])
                else:
                    setattr(self, attrib[0], attrib[1])
            else:
                for attr in attrib:
                    if attr in STY_EX_ATTRIBUTES:
                        self.SetExAttr(attr)

        return last_set != wx.EmptyString
        
    def SetExAttr(self, ex_attr, add=True):
        """Adds an extra text attribute to a StyleItem. Currently
        (bold, eol, italic, underline) are supported. If the optional
        add value is set to False the attribute will be removed from
        the StyleItem.
        @param ex_attr: extra style attribute (bold, eol, italic, underline)
        @keyword add: Add a style (True) or remove a style (False)

        """
        # Get currently set attributes
        self.null = False
        if ex_attr not in STY_EX_ATTRIBUTES:
            return

        if add and ex_attr not in self._exattr:
            self._exattr.append(ex_attr)
            setattr(self,ex_attr,True)
        elif not add and ex_attr in self._exattr:
            self._exattr.remove(ex_attr)
            setattr(self,ex_attr,False)
        else:
            pass
            
    def GetStyleSpecStr(self):
        style_str = list()
        lexer_manager = syntax.LexerManager()
        global_style = lexer_manager.GetGlobalItemByName(consts.GLOBAL_STYLE_NAME)
        if self.Fore:
            style_str.append(u"fore:%s" % self.Fore)
        else:
            style_str.append(u"fore:%s" % global_style.Fore)
        if self.Back:
            style_str.append(u"back:%s" % self.Back)
        else:
            style_str.append(u"back:%s" % global_style.Back)
        if self.Face:
            style_str.append(u"face:%s" % self.Face)
        else:
            style_str.append(u"face:%s" % global_style.Face)
        if self.Size:
            style_str.append(u"size:%s" % unicode(self.Size))
        else:
            style_str.append(u"size:%s" % unicode(global_style.Size))
        if len(self._exattr):
            style_str.append(u"modifiers:" +  u','.join(self._exattr))
        stystr = u",".join(style_str)
        return stystr.replace("modifiers:", "")
        
    def GetBack(self):
        if self.Back:
            return self.Back
        return syntax.LexerManager().GetGlobalItemByName(consts.GLOBAL_STYLE_NAME).Back
        
    def GetFore(self):
        if self.Fore:
            return self.Fore
        return syntax.LexerManager().GetGlobalItemByName(consts.GLOBAL_STYLE_NAME).Fore
        
    def GetSize(self):
        if self.Size:
            return self.Size
        return syntax.LexerManager().GetGlobalItemByName(consts.GLOBAL_STYLE_NAME).Size
        
    def GetFace(self):
        if self.Face:
            return self.Face
        return syntax.LexerManager().GetGlobalItemByName(consts.GLOBAL_STYLE_NAME).Face

class LexerStyleItem(StyleItem):
    
    LOAD_FROM_ATTRIBUTE = 1
    LOAD_FROM_DEFAULT =  2
    LOAD_FROM_CONFIG = 3
    
    LOAD_STYLE_THRESHOLD = LOAD_FROM_CONFIG
    
    def __init__(self,style_id,key_name,style_name,global_style_name,fore=u"", back=u"", face=u"", size=u"", ex=None):
        super(LexerStyleItem,self).__init__(fore,back,face,size)
        self._style_id  = style_id
        self._style_name = style_name
        self._key_name = key_name
        self._global_style_name = global_style_name
        self._lang_id = lang.ID_LANG_TXT

    @classmethod
    def SetThresHold(cls,val):
        cls.LOAD_STYLE_THRESHOLD = val
        
    @classmethod
    def GetThresHold(cls):
        return cls.LOAD_STYLE_THRESHOLD
        
    @classmethod
    def SetDefaultThresHold(cls):
       cls.LOAD_STYLE_THRESHOLD = cls.LOAD_FROM_CONFIG
               
    @property
    def StyleId(self):
        return self._style_id
        
    @property
    def StyleName(self):
        return self._style_name
        
    @property
    def LangId(self):
        return self._lang_id
        
    @LangId.setter
    def LangId(self,lang_id):
        self._lang_id = lang_id
        
    @property
    def GlobalStyleName(self):
        return self._global_style_name
        
    @property
    def KeyName(self):
        return self._key_name
        
    def GetStyleSpec(self):
        lexer_manager = syntax.LexerManager()
        global_style = lexer_manager.GetGlobalItemByName(consts.GLOBAL_STYLE_NAME)
        #load from attr directly
        if self.LOAD_STYLE_THRESHOLD == self.LOAD_FROM_ATTRIBUTE:
            #should update back color to global back color if is not equal
            return self.GetStyleSpecStr()
        
        #load from config
        if self.LOAD_STYLE_THRESHOLD == self.LOAD_FROM_CONFIG:
            lexer_name = lexer_manager.GetLexer(self.LangId).GetShowName()
            key_name = getStyleKeyName(lexer_name,self._key_name)
            style_item = lexer_manager.GetItemByKeyName(key_name)
            #if could not get style from config,then get default style
            if style_item is None:
                style_item = lexer_manager.GetItemByName(self._global_style_name)
        else:
            #load default
            style_item = lexer_manager.GetItemByName(self._global_style_name)
        if self.Back != style_item.Back:
            self.SetBack(style_item.Back)
        if self.Fore != style_item.Fore:
            self.SetFore(style_item.Fore)
        if self.Face != style_item.Face:
            self.SetFace(style_item.Face)
        if self.Size != style_item.Size:
            self.SetSize(style_item.Size)
        for attr in style_item._exattr:
            self.SetExAttr(attr)
        #should update back color to global back color if is not equal
        style_spec_str = self.GetStyleSpecStr()
        return style_spec_str
        
    
