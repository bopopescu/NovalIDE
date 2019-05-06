import os
import noval.util.singleton as singleton
import noval.util.utils as utils
import noval.util.strutils as strutils
import sys
from noval.syntax import syntax
import noval.imageutils as imageutils
import noval.core as core

@singleton.Singleton
class LexerFactory(object):
    """description of class"""
    
    def CreateLexers(self,lang=""):
        if lang == "":
            lexer_path = os.path.join(utils.get_app_path(),"noval","syntax","lexer")
        else:
            lexer_path = os.path.join(utils.get_app_path(),"noval",lang,"syntax","lexer")
        sys.path.append(lexer_path)
        try:
            for fname in os.listdir(lexer_path):
                if not fname.endswith(".py"):
                    continue
                modname = strutils.get_filename_without_ext(fname)
                module = __import__(modname)
                if not hasattr(module,"SyntaxLexer"):
                    continue
                cls_lexer = getattr(module,"SyntaxLexer")
                lexer_instance = cls_lexer()
                lexer_instance.Register()
        except Exception as e:
            utils.get_logger().exception("")
            utils.get_logger().error("load lexer error:%s",e)

    def CreateLexerTemplates(self,docManager,lang=""):
        self.CreateLexers(lang)
        
    def LoadLexerTemplates(self,docManager):
        for lexer in syntax.SyntaxThemeManager().Lexers:
            utils.get_logger().info("load lexer id:%d description %s ",lexer.LangId,lexer.GetDescription())
            templateIcon = lexer.GetDocIcon()
            if templateIcon is None:
                templateIcon = imageutils.getBlankIcon()
            docTemplate = core.DocTemplate(docManager,
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
