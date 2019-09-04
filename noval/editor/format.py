# -*- coding: utf-8 -*-
from noval import _
import noval.syntax.lang as lang
import noval.util.utils as utils
import noval.constants as constants
import noval.consts as consts
import noval.ui_base as ui_base
import tkinter as tk
from tkinter import ttk
import noval.imageutils as imageutils
import noval.ui_utils as ui_utils

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
            

    def tabify_region(self):
        text_ctrl = self.editor.GetView().GetCtrl()
        text_ctrl.tabify_region()

    def untabify_region(self):
        text_ctrl = self.editor.GetView().GetCtrl()
        text_ctrl.untabify_region()
        
    def do_rstrip(self):
        '''
            清除行尾的空白字符
        '''
        text_ctrl = self.editor.GetView().GetCtrl()
        head, tail, _, _ = text_ctrl._get_region()
        start_line = text_ctrl.get_line_col(head)[0]
        end_line = text_ctrl.get_line_col(tail)[0]
        for cur in range(start_line, end_line):
            txt = text_ctrl.get('%i.0' % cur, '%i.end-1c' % cur)
            raw = len(txt)
            cut = len(txt.rstrip())
            # Since text.delete() marks file as changed, even if not,
            # only call it when needed to actually delete something.
            if cut < raw:
                text_ctrl.delete('%i.%i' % (cur, cut), '%i.end' % cur)

    def do_eol(self,command_id):
        '''
            修改行尾模式
        '''
        eol_mode = -1
        if command_id == constants.ID_EOL_MAC:
            eol_mode = consts.EOL_CR
        elif command_id == constants.ID_EOL_UNIX:
            eol_mode = consts.EOL_LF
        elif command_id == constants.ID_EOL_WIN:
            eol_mode = consts.EOL_CRLF
        newlines = consts.EOL_DIC[eol_mode]
            
        text_ctrl = self.editor.GetView().GetCtrl()
        if eol_mode != text_ctrl.GetEol():
            text_ctrl.SetEol(eol_mode)
            text_ctrl.edit_modified(True)

class EOLFormatDlg(ui_base.CommonModaldialog):
    EOL_CHARS = consts.EOL_DIC.values()
    EOL_ITEMS = [consts.EOL_CR, consts.EOL_LF, consts.EOL_CRLF]
    EOL_CHOICES = ["Old Machintosh (\\r)", "Unix (\\n)",
                   "Windows (\\r\\n)"]    
    def __init__(self, master,view):
        ui_base.CommonModaldialog.__init__(self, master, takefocus=1)
        self.title(_("Format EOL?"))
        self.resizable(height=tk.FALSE, width=tk.FALSE)
        self.text_view = view        
        msg = _("Mixed EOL characters detected.\n\n"
                "Would you like to format them to all be the same?")

        self.img = imageutils.load_image("","doc_props.png")
        top = ttk.Frame(self.main_frame)
        left = ttk.Frame(top)
        tk.Label(left, image=self.img,compound="top").pack(fill="x")
        left.pack(side=tk.LEFT,fill=tk.X,padx=consts.DEFAUT_CONTRL_PAD_X)
        right = ttk.Frame(top)
        ttk.Label(right,text=msg).pack(fill="x")
        values = [_(value) for value in self.EOL_CHOICES]
        self.combo = ttk.Combobox(right,values=values)
        self.combo.pack(fill="x")
        default_eol = ui_utils.get_default_eol()
        self.combo.current(self.EOL_ITEMS.index(default_eol))
        self.combo.state(['readonly'])
        right.pack(side=tk.LEFT,fill=tk.X,padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=consts.DEFAUT_CONTRL_PAD_Y)
        top.pack(fill="x")
        self.AddokcancelButton()
        
    def _ok(self,event=None):
        self.eol = self.EOL_ITEMS[self.combo.current()]
        ui_base.CommonModaldialog._ok(self)