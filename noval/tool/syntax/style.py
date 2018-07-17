import wx
import syntax

STY_ATTRIBUTES = (u"face", u"fore", u"back", u"size", u"modifiers")
STY_EX_ATTRIBUTES  = (u"eol", u"bold", u"italic", u"underline")

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
        elif not add and ex_attr in self._exattr:
            self._exattr.remove(ex_attr)
        else:
            pass
        

class LexerStyleItem(StyleItem):
    
    def __init__(self,style_id,key_name,style_name,global_style_name,fore=u"", back=u"", face=u"", size=u"", ex=None):
        super(LexerStyleItem,self).__init__(fore,back,face,size)
        self._style_id  = style_id
        self._style_name = style_name
        self._key_name = key_name
        self._global_style_name = global_style_name

        
    @property
    def StyleId(self):
        return self._style_id
        
    @property
    def StyleName(self):
        return self._style_name
        
    @property
    def GlobalStyleName(self):
        return self._global_style_name
        
    @property
    def KeyName(self):
        return self._key_name
        
    def GetStyleSpec(self):
        style_item = syntax.LexerManager().GetItemByName(self._global_style_name)
        if not self.Back:
            self.SetBack(style_item.Back)
        if not self.Fore:
            self.SetFore(style_item.Fore)
        if not self.Face:
            self.SetFace(style_item.Face)
        if not self.Size:
            self.SetSize(style_item.Size)
        style_spec_str = syntax.LexerManager().GetStyleByName(self._global_style_name)
        return style_spec_str
        
    
