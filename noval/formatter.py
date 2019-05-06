import noval.syntax.lang as lang

class Formatter(object):
    """description of class"""
    

    def IsFormatterEnable(self,editor):
        if editor is None:
            return False
        return editor.GetView().GetLangId() != lang.ID_LANG_TXT

    def CommentRegion(self,editor):
        editor.GetView().comment_region()
    
    def UncommentRegion(self,editor):
        editor.GetView().uncomment_region()



formatter = Formatter()
