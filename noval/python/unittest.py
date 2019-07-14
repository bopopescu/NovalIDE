import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from noval import _,GetApp
import os
import noval.python.parser.config as parserconfig
import noval.python.parser.nodeast as nodeast
import noval.ui_base as ui_base
import noval.consts as consts
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.ttkwidgets.checkboxtreeview as checkboxtreeview
import noval.imageutils as imageutils
import tkinter.font as tk_font
from noval.util import utils
import noval.python.pyeditor as pyeditor
import noval.core as core

UNITTEST_TEMPLATE_HEADER = '''\
#This file was originally generated by NovalIDE's unitest wizard
import unittest
'''

UNITTEST_TMPLATE_FOOTER = '''
if __name__ == "__main__":
    unittest.main()
'''

UNITTEST_CLASS_HEADER ='''
class Test{ClassName}(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
'''

UNITTEST_FUNC_HEADER ='''
    def test{FuncName}(self):
        pass
'''
        
class UnitTestDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,view):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(_("UnitTest"))
        self.checked_items = []
        
        self.img = imageutils.load_image("","unittest_wizard.png")
        welcome_label_font = tk_font.Font(
            name="UniteTestDlgFont",
            family=utils.profile_get(consts.EDITOR_FONT_FAMILY_KEY,GetApp().GetDefaultEditorFamily()),
            weight="bold",
            size=14,
        ),
        
        sizer_frame = ttk.Frame(self.main_frame)
        label_ctrl = ttk.Label(sizer_frame,text=_("NovalIDE UnitTest Wizard"),font=welcome_label_font)
        label_ctrl.pack(side=tk.LEFT,fill="x",expand=1)
        
        img_ctrl = ttk.Label(sizer_frame,image=self.img,compound=tk.RIGHT)
        img_ctrl.pack(side=tk.LEFT)
        
        sizer_frame.pack(fill="x")
        
        self.treeview = treeviewframe.TreeViewFrame(self.main_frame,treeview_class=checkboxtreeview.CheckboxTreeview)
        self.treeview.pack(expand=1,fill=tk.BOTH,pady=(consts.DEFAUT_CONTRL_PAD_Y, 0))
        self.tree = self.treeview.tree
        self.AddokcancelButton()
        self._cur_view = view

    def CreateUnitTestFrame(self):
        module_scope = self._cur_view.ModuleScope
        if module_scope is None:
            messagebox.showerror(_("Error"),self._cur_view.ModuleAnalyzer.SyntaxError)
            self.withdraw()
            self.destroy()
            return False
        self.root = self.tree.insert("","end",text=module_scope.Module.Name)
        self.TranverseItem(module_scope.Module,self.root)
        self.tree.CheckItem(self.root, True)
        return True

    def TranverseItem(self,node,parent):
        for child in node.Childs:
            if child.Type == parserconfig.NODE_FUNCDEF_TYPE:
                if child.IsConstructor:
                    continue
                item = self.tree.insert(parent,"end",text=child.Name,values=child.Type)
            elif child.Type == parserconfig.NODE_CLASSDEF_TYPE:
                item = self.tree.insert(parent, "end",text=child.Name,values=child.Type)
                self.TranverseItem(child,item)
        self.tree.item(parent, open=True)

    def _ok(self,event=None):
        for template in GetApp().GetDocumentManager().GetTemplates():
            if template.GetDocumentType() == pyeditor.PythonDocument:
                newDoc = template.CreateDocument("", flags = core.DOC_NEW)
                if newDoc:
                    newDoc.SetDocumentName(template.GetDocumentName())
                    newDoc.SetDocumentTemplate(template)
                    newDoc.OnNewDocument()
                    doc_view = newDoc.GetFirstView()
                    doc_view.AddText(UNITTEST_TEMPLATE_HEADER)
                    doc_view.AddText("import %s\n" % self._cur_view.ModuleScope.Module.Name)
                    doc_view.AddText(self.CreateUnitTestTemplate())
                    doc_view.AddText(UNITTEST_TMPLATE_FOOTER)
                    break
        ui_base.CommonModaldialog._ok(self,event)

    def CreateUnitTestFromClass(self,node_name,is_name=False):
        if is_name:
            name = node_name
        else:
            name = self.tree.item(node_name,"text")
        return UNITTEST_CLASS_HEADER.format(ClassName=name)
        

    def CreateUnitTestFromFunction(self,node):
        name = self.tree.item(node,"text")
        return UNITTEST_FUNC_HEADER.format(FuncName=name)

    def CreateUnitTestTemplate(self):
        global_func_nodes = []
        template_text = ''
        childs = self.tree.get_children(self.root)
        for item in childs:
            if not self.tree.IsItemChecked(item):
                continue
            node_type = self.tree.item(item)["values"][0]
            if node_type == parserconfig.NODE_CLASSDEF_TYPE:
                template_text += self.CreateUnitTestFromClass(item)
            elif node_type == parserconfig.NODE_FUNCDEF_TYPE:
                global_func_nodes.append(item)
                
            item_childs = self.tree.get_children(item)
            if len(item_childs) > 0:
                for cihld_item in item_childs:
                    if not self.tree.IsItemChecked(cihld_item):
                        continue
                    child_node_type = self.tree.item(cihld_item)["values"][0]
                    if child_node_type == parserconfig.NODE_FUNCDEF_TYPE:
                        template_text += self.CreateUnitTestFromFunction(cihld_item)

        if global_func_nodes != []:
            template_text += self.CreateUnitTestFromClass("GlobalFunction",True)
            for func_node in global_func_nodes:
                template_text += self.CreateUnitTestFromFunction(func_node)

        template_text += "\n"
        return template_text
        
