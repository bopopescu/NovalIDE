import noval.syntax.syntax as syntax
import zlib

class BaseLexer(object):
    """Syntax data container object base class"""
    
    SYNTAX_ITEMS = []
    def __init__(self, langid):
        object.__init__(self)
        # Attributes
        self._langid = langid
        self.exts = []
        self.style_items = []

    @property
    def CommentPattern(self):
        return self.GetCommentPattern()

    @property
    def Keywords(self):
        return self.GetKeywords()

    @property
    def LangId(self):
        return self.GetLangId()

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

    def SetLangId(self, lid):
        """Set the language identifier
        @param lid: int

        """
        self._langid = lid
        
    def Register(self):
        syntax.SyntaxThemeManager().Register(self)

    def UnRegister(self):
        syntax.SyntaxThemeManager().UnRegister(self)
        
    def GetDescription(self):
        return ""
        
    def GetShowName(self):
        return ""
        
    def GetDefaultExt(self):
        return ""
        
    def GetExt(self):
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
        
    def IsCommentTemplateEnable(self):
        return self.GetCommentTemplate() is not None
        
    @property
    def StyleItems(self):
        return self.style_items
        
    def GetExtStr(self):
        if len(self.Exts) == 0:
            return ""
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
        
    @property
    def Exts(self):
        if 0 == len(self.exts):
            self.exts = self.GetExt().split()
        return self.exts


class BaseSyntaxcolorer:
    def __init__(self,text):
        self.text = text
        self._update_scheduled = False
        self._dirty_ranges = set()
        self._use_coloring = False

    def schedule_update(self, event, use_coloring=True):
        self._use_coloring = use_coloring

        