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

    def IndentRegion(self,editor):
        editor.GetView().GetCtrl().indent_region()
    
    def DedentRegion(self,editor):
        editor.GetView().GetCtrl().dedent_region()

    def UpperCase(self,editor):
        ctrl = editor.GetView().GetCtrl()
        selected_text = ctrl.GetSelectionText()
        if not selected_text:
            return
        ctrl.do_replace(selected_text.upper())

    def LowerCase(self,editor):
        ctrl = editor.GetView().GetCtrl()
        selected_text = ctrl.GetSelectionText()
        if not selected_text:
            return
        ctrl.do_replace(selected_text.lower())
        

formatter = Formatter()
