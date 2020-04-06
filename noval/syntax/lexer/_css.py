# -- coding: utf-8 --
#-------------------------------------------------------------------------------
# Name:        _xml.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-17
# Copyright:   (c) wukan 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

#-----------------------------------------------------------------------------#
from noval import _
from noval.syntax import syndata,lang
from noval.syntax.pat import *
import noval.util.appdirs as appdirs
import os
import noval.editor.code as codeeditor
import noval.imageutils as imageutils
#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#
# CSS1 Keywords (Identifiers)
CSS1_KEYWORDS = ['font-family', 'font-style', 'font-variant', 'font-weight', 'font-size', 'font', 'color', 'background-color', \
                 'background-image', 'background-repeat', 'background-position', 'background', 'word-spacing', 'letter-spacing', \
                 'text-decoration', 'vertical-align', 'text-transform', 'text-align', 'text-indent', 'line-height', 'margin-top', \
                 'margin-right', 'margin-left', 'margin', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left', \
                 'padding', 'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width', 'border-width', \
                 'border-color', 'border-style', 'border-top', 'border-right', 'border-bottom', 'border-left', 'border', 'width', \
                 'height', 'float', 'clear', 'display', 'white-space', 'list-style-type', 'list-style-image', 'list-style-position', \
                 'list-style', 'margin-bottom', 'text-decoration', 'min-width', 'min-height', 'background-attachment']

# CSS Psuedo Classes
CSS_PSUEDO_CLASS = ['link', 'active', 'visited', 'indeterminate', 'default', 'first-child', 'focus', 'hover', 'lang', 'left', 'right', \
                    'first', 'empty', 'enabled', 'disabled', 'checked', 'not', 'root', 'target', 'only-child', 'last-child', 'nth-child', \
                    'nth-last-child', 'first-of-type', 'last-of-type', 'nth-of-type', 'nth-last-of-type', 'only-of-type', 'valid', \
                    'invalid', 'required', 'optional']

# CSS2 Keywords (Identifiers)
# This is meant for css2 specific keywords, but in order to get a better
# coloring effect this will contain special css properties as well.
CSS2_KEYWORDS = ['ActiveBorder', 'ActiveCaption', 'AppWorkspace', 'Background', 'ButtonFace', 'ButtonHighlight', 'ButtonShadow', 'ButtonText', \
                 'CaptionText', 'GrayText', 'Highlight', 'HighlightText', 'InactiveBorder', 'InactiveCaption', 'InactiveCaptionText', \
                 'InfoBackground', 'InfoText', 'Menu', 'MenuText', 'Scrollbar', 'ThreeDDarkShadow', 'ThreeDFace', 'ThreeDHighlight', \
                 'ThreeDLightShadow', 'ThreeDShadow', 'Window', 'WindowFrame', 'WindowText', 'above', 'absolute', 'all', 'always', 'aqua', \
                 'armenian', 'ascent', 'auto', 'avoid', 'azimuth', 'baseline', 'baseline', 'bbox', 'behind', 'below', 'bidi-override', 'black', \
                 'blink', 'block', 'blue', 'bold', 'bolder', 'both', 'bottom', 'capitalize', 'center', 'center', 'centerline', 'child', 'circle', \
                 'clear', 'clip', 'code', 'collapse', 'color', 'compact', 'content', 'continuous', 'crop', 'cross', 'crosshair', 'cursive', \
                 'cursor', 'dashed', 'default', 'descent', 'digits', 'disc', 'dotted', 'double', 'during', 'elevation', 'embed', 'fantasy', \
                 'faster', 'female', 'fixed', 'fixed', 'float', 'fuchsia', 'georgian', 'gray', 'green', 'groove', 'hebrew', 'height', \
                 'help', 'hidden', 'hide', 'higher', 'icon', 'inherit', 'inline', 'inset', 'inside', 'inside', 'invert', 'italic', 'justify', \
                 'landscape', 'larger', 'leftwards', 'level', 'lighter', 'lime', 'lowercase', 'ltr', 'male', 'marks', 'maroon', 'mathline', \
                 'medium', 'menu', 'middle', 'mix', 'monospace', 'move', 'narrower', 'navy', 'non', 'none', 'normal', 'nowrap', 'oblique', \
                 'olive', 'once', 'orphans', 'outset', 'outside', 'overflow', 'overline', 'pointer', 'portrait', 'position', 'pre', 'purple', \
                 'quotes', 'red', 'relative', 'richness', 'ridge', 'rightwards', 'rtl', 'scroll', 'scroll', 'separate', 'show', 'silent', \
                 'silver', 'size', 'slope', 'slower', 'smaller', 'solid', 'square', 'src', 'static', 'stemh', 'stemv', 'stress', 'sub', \
                 'super', 'teal', 'thick', 'thin', 'top', 'topline', 'underline', 'uppercase', 'visibility', 'visible', 'volume', 'wait', \
                 'wider', 'widows', 'width', 'widths', 'yellow', 'z-index', 'outline', 'left']

# CSS3 Keywords
CSS3_KEYWORDS = ['border-radius', 'border-top-left-radius', 'border-top-right-radius', 'border-bottom-left-radius', \
                 'border-bottom-right-radius', 'border-image', 'border-image-outset', 'border-image-repeat', 'border-image-source', \
                 'border-image-slice', 'border-image-width', 'break-after', 'break-before', 'break-inside', 'columns', 'column-count', \
                 'column-fill', 'column-gap', 'column-rule', 'column-rule-color', 'column-rule-style', 'column-rule-width', 'column-span', \
                 'column-width', '@keframes', 'animation', 'animation-delay', 'animation-direction', 'animation-duration', \
                 'animation-fill-mode', 'animation-iteration-count', 'animation-name', 'animation-play-state', 'animation-timing-function', \
                 'transition', 'transition-delay', 'transition-duration', 'transition-timing-function', 'transition-property', \
                 'backface-visibility', 'perspective', 'perspective-origin', 'transform', 'transform-origin', 'transform-style', \
                 'background-clip', 'background-origin', 'background-size', 'overflow-x', 'overflow-y', 'overflow-style', 'marquee-direction', \
                 'marquee-play-count', 'marquee-speed', 'marquee-style', 'box-shadow', 'box-decoration-break', 'opacity']

PSEUDO_ELEMENTS = ['first-letter', 'first-line', 'before', 'after', 'selection']

def make_pat(kw_list):
    kw = get_keyword_pat(kw_list)
    builtin = get_builtin_pat(CSS_PSUEDO_CLASS+PSEUDO_ELEMENTS)
    #匹配块注释
    cregx = stringprefix + r"/\*((?!(\*/)).)*(\*/)?"
    comment = matches_any("comment", [cregx])
    number = get_number_pat()
    selector = matches_any("selector", [r"(?<=\.)[\w|-]+"])
    css_keyword = matches_any("css_keyword", [r"(?<=@)[\w|-]+"])
    return selector + "|" + css_keyword + "|" +  kw + "|" + builtin + "|" + comment  + "|" + number + "|" + matches_any("SYNC", [r"\n"])

prog = get_prog(make_pat(CSS1_KEYWORDS+CSS2_KEYWORDS+CSS3_KEYWORDS))

#-----------------------------------------------------------------------------#

class SyntaxColorer(syndata.BaseSyntaxcolorer):
    def __init__(self, text):
        syndata.BaseSyntaxcolorer.__init__(self,text)
        self.prog = prog
        self._config_tags()

    def _config_tags(self):
        self.tagdefs.update({
        "stdin",
        'stderr',
        })
        
    def AddTag(self,head,match_start,match_end,key,value,chars):
        if key == "selector":
            key = "stderr"
        elif key == "css_keyword":
            key = "definition"
        syndata.BaseSyntaxcolorer.AddTag(self,head,match_start,match_end,key,value,chars)
 
        
class SyntaxLexer(syndata.BaseLexer):
    """SyntaxData object for Python"""             
    def __init__(self):
        lang_id = lang.RegisterNewLangId("ID_LANG_CSS")
        syndata.BaseLexer.__init__(self,lang_id)
        
    def GetDescription(self):
        return _('StyleSheet')
        
    def GetExt(self):
        return "css"

    def GetDefaultCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'/*', u'*/']

    def GetShowName(self):
        return "Cascading Style Sheet"
        
    def GetDefaultExt(self):
        return "css"
        
    def GetDocTypeName(self):
        return "StyleSheet Document"
        
    def GetViewTypeName(self):
        return _("StyleSheet Editor")
        
    def GetDocTypeClass(self):
        return codeeditor.CodeDocument
        
    def GetViewTypeClass(self):
        return codeeditor.CodeView
        
    def GetDocIcon(self):
        return imageutils.load_image("","file/css.png")
        
    def GetSampleCode(self):
        sample_file_path = os.path.join(appdirs.get_app_data_location(),"sample","css.sample")
        return self.GetSampleCodeFromFile(sample_file_path)
        
    def GetColorClass(self):
        return SyntaxColorer
