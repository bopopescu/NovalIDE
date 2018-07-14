import wx
import wx.lib.docview
import os
import noval.tool.Singleton as Singleton
import noval.util.sysutils as sysutilslib
import noval.util.strutils as strutils
import sys
import syntax
import noval.tool.images as images

class LexerFactory(object):
    """description of class"""

    __metaclass__ = Singleton.SingletonNew
    
    def CreateLexers(self):
        lexer_path = os.path.join(sysutilslib.mainModuleDir,"noval","tool","syntax","lexer")
        sys.path.append(lexer_path)
        for fname in os.listdir(lexer_path):
            if not fname.endswith(".py"):
                continue
            modname = strutils.GetFilenameWithoutExt(fname)
            module = __import__(modname)
            if not hasattr(module,"SyntaxLexer"):
                continue
            cls_lexer = getattr(module,"SyntaxLexer")
            lexer_instance = cls_lexer()
            lexer_instance.Register()

    def CreateLexerTemplates(self,docManager):
        self.CreateLexers()
        for lexer in syntax.LexerManager().Lexers:
            templateIcon = lexer.GetDocIcon()
            if templateIcon is None:
                templateIcon = images.getBlankIcon()
            docTemplate = wx.lib.docview.DocTemplate(docManager,
                    lexer.GetDescription(),
                    lexer.GetExtStr(),
                    os.getcwd(),
                    "." + lexer.GetDefaultExt(),
                    lexer.GetDocTypeName(),
                    lexer.GetViewTypeName(),
                    lexer.GetDocTypeClass(),
                    lexer.GetViewTypeClass(),
                    icon = templateIcon)
            docManager.AssociateTemplate(docTemplate)