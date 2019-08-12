import noval.syntax.lang as lang
import noval.util.utils as utils
import noval.constants as constants

class Formatter(object):
    """description of class"""

    def __init__(self,editor):
        self.editor = editor

    def CommentRegion(self):
        self.editor.GetView().comment_region()
    
    def UncommentRegion(self):
        self.editor.GetView().uncomment_region()

    def IndentRegion(self):
        self.editor.GetView().GetCtrl().indent_region()
    
    def DedentRegion(self):
        self.editor.GetView().GetCtrl().dedent_region()

    def UpperCase(self):
        ctrl = self.editor.GetView().GetCtrl()
        selected_text = ctrl.GetSelectionText()
        if not selected_text:
            return
        ctrl.do_replace(selected_text.upper())

    def LowerCase(self):
        ctrl = self.editor.GetView().GetCtrl()
        selected_text = ctrl.GetSelectionText()
        if not selected_text:
            return
        ctrl.do_replace(selected_text.lower())

    def FirstUppercase(self):
        ctrl = self.editor.GetView().GetCtrl()
        selected_text = ctrl.GetSelectionText()
        if not selected_text:
            return
        lower_text = selected_text.lower()
        convert_text = lower_text[0].upper() + lower_text[1:]
        ctrl.do_replace(convert_text)

    def EditLineEvent(self,command_id,line=-1):
        ctrl = self.editor.GetView().GetCtrl()
        if line == -1:
            line = ctrl.GetCurrentLine()
        line_start = "%d.0" % line
        #line_end = "%d.end" % line
        line_end = "%d.0" % (line+1)
        if command_id == constants.ID_CUT_LINE or command_id == constants.ID_COPY_LINE or command_id == constants.ID_CLONE_LINE:
            line_text = ctrl.GetLineText(line)
            utils.CopyToClipboard(line_text)
        if command_id == constants.ID_CUT_LINE or command_id == constants.ID_DELETE_LINE:
            ctrl.delete(line_start, line_end)
        elif command_id == constants.ID_CLONE_LINE:
            ctrl.insert(line_end,line_text+"\n")
