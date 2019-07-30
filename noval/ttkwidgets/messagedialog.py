import noval.ui_base as ui_base
import noval.editor.text as texteditor
import noval.ttkwidgets.textframe as textframe

class ScrolledMessageDialog(ui_base.CommonModaldialog):
    """description of class"""

    def __init__(self, parent,title,content):
        """
        Initializes the feedback dialog.
        """
        ui_base.CommonModaldialog.__init__(self, parent)
        self.title(title)
        text_frame = textframe.TextFrame(self.main_frame,read_only=True,borderwidth=1,relief="solid",text_class=texteditor.TextCtrl)
        text_frame.text.set_content(content)
        text_frame.pack(fill="both",expand=1)

