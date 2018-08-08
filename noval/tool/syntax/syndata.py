import syntax
import lang
import wx.stc as stc
import style
import zlib

class BaseLexer(object):
    """Syntax data container object base class"""
    
    SYNTAX_ITEMS = []
    def __init__(self, langid = lang.ID_LANG_TXT):
        object.__init__(self)

        # Attributes
        self._langid = langid
        self._lexer = stc.STC_LEX_NULL
        self._features = dict()
        lang_data = lang.LANG_MAP.get(self._langid)
        self.exts = lang_data[1].split()
        self.style_items = []
        self.GetStyleItems(self.SYNTAX_ITEMS)

    @property
    def CommentPattern(self):
        return self.GetCommentPattern()

    @property
    def Keywords(self):
        return self.GetKeywords()

    @property
    def LangId(self):
        return self.GetLangId()

    @property
    def Lexer(self):
        return self.GetLexer()

    @property
    def Properties(self):
        return self.GetProperties()

    @property
    def SyntaxSpec(self):
        return self.GetSyntaxSpec()

    #---- Interface Methods ----#

    def GetCommentPattern(self):
        """Get the comment pattern
        @return: list of strings ['/*', '*/']

        """
        return list()

    def GetKeywords(self):
        """Get the Keyword List(s)
        @return: list of tuples [(1, ['kw1', kw2']),]

        """
        return list()

    def GetLangId(self):
        """Get the language id
        @return: int

        """
        return self._langid

    def GetLexer(self):
        """Get the lexer id
        @return: wx.stc.STC_LEX_

        """
        return self._lexer

    def GetProperties(self):
        """Get the Properties List
        @return: list of tuples [('fold', '1'),]

        """
        return list()

    def GetSyntaxSpec(self):
        """Get the the syntax specification list
        @return: list of tuples [(int, 'style_tag'),]
        @note: required override for subclasses

        """
        raise NotImplementedError

    #---- End Interface Methods ----#

    def GetFeature(self, name):
        """Get a registered features callable
        @param name: feature name
        @return: callable or None

        """
        return self._features.get(name, None)

    def RegisterFeature(self, name, funct):
        """Register an extension feature with the factory
        @param name: feature name
        @param funct: callable

        """
        assert isinstance(funct, collections.Callable), "funct must be callable object"
        self._features[name] = funct

    def SetLexer(self, lex):
        """Set the lexer object for this data object"""
        self._lexer = lex

    def SetLangId(self, lid):
        """Set the language identifier
        @param lid: int

        """
        self._langid = lid
        
    def Register(self):
        syntax.LexerManager().Register(self)

    def UnRegister(self):
        syntax.LexerManager().UnRegister(self)
        
    def GetDescription(self):
        return lang.GetDescriptionFromId(self.LangId)
        
    def GetShowName(self):
        return ""
        
    def GetDefaultExt(self):
        return ""
        
    def GetDocTypeName(self):
        return ""
        
    def GetViewTypeName(self):
        return ""
        
    def GetDocTypeClass(self):
        return None
        
    def GetViewTypeClass(self):
        return None
        
    def GetDocIcon(self):
        return None
        
    def GetSampleCode(self):
        return ''
        
    def GetCommentTemplate(self):
        return None
        
    @property
    def Exts(self):
        return self.exts
        
    @property
    def StyleItems(self):
        return self.style_items
        
    def GetExtStr(self):
        strext = "*." + self.Exts[0]
        for ext in self.Exts[1:]:
            strext += ";"
            strext += "*."
            strext +=  ext
        return strext
        
    def ContainExt(self,ext):
        ext = ext.replace(".","")
        for ext_name in self.Exts:
            if ext.lower() == ext_name:
                return True
        return False

    def GetStyleItems(self,syntax_items):
        for style_id,key_name,style_name,global_style_name in syntax_items:
            lexer_style_item = style.LexerStyleItem(style_id,key_name,style_name,global_style_name)
            lexer_style_item.LangId = self.LangId
            self.style_items.append(lexer_style_item)
            
    def GetSampleCodeFromFile(self,sample_file_path,is_zip_compress = True):
        if not is_zip_compress:
            with open(sample_file_path) as f:
                return f.read()
        else:
            content = ''
            with open(sample_file_path, 'rb') as f:
                decompress = zlib.decompressobj()
                data = f.read(1024)
                while data:
                    content += decompress.decompress(data)
                    data = f.read(1024)
                content += decompress.flush()
            return content
        
    def IsVisible(self):
        return True
        