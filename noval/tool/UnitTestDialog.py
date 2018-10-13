import wx
import os
import noval.parser.config as parserconfig
import wx.lib.agw.customtreectrl as CT
import noval.parser.nodeast as nodeast
import PythonEditor
import noval.util.sysutils as sysutilslib
_ = wx.GetTranslation

SPACE = 10
HALF_SPACE = 5

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
        
class UnitTestDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,view,size=(500,500)):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=size)
        self.checked_items = []

        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        flagSizer = wx.BoxSizer(wx.HORIZONTAL)
        st_text = wx.StaticText(self,label = _("NovalIDE UnitTest Wizard"))
        st_text.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
        flagSizer.Add(st_text, 1,flag=wx.LEFT|wx.EXPAND,border = SPACE)  
        icon = wx.StaticBitmap(self,bitmap = wx.Bitmap(os.path.join(sysutilslib.mainModuleDir, \
                            "noval", "tool", "bmp_source", "unittest_wizard.png")))  
        flagSizer.Add(icon,0,flag=wx.ALL,border = 0)
        contentSizer.Add(flagSizer,0,flag=wx.EXPAND|wx.TOP,border = HALF_SPACE)
        
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        modulebmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "module.png")
        modulebmp = wx.Bitmap(modulebmp_path, wx.BITMAP_TYPE_PNG)
        self.ModuleIdx = il.Add(modulebmp)

        funcbmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "func.png")
        funcbmp = wx.Bitmap(funcbmp_path, wx.BITMAP_TYPE_PNG)
        self.FuncIdx = il.Add(funcbmp)

        classbmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "class.png")
        classbmp = wx.Bitmap(classbmp_path, wx.BITMAP_TYPE_PNG)
        self.ClassIdx = il.Add(classbmp)

        #lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._treeCtrl = CT.CustomTreeCtrl(self, style = wx.BORDER_THEME,agwStyle = wx.TR_DEFAULT_STYLE)
        self._treeCtrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX))
        self._treeCtrl.SetImageList(il)
        contentSizer.Add(self._treeCtrl, 1, wx.EXPAND|wx.BOTTOM,SPACE)

        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        self.SetSizer(contentSizer) 
        
        self._cur_view = view
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.checked_item)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnClose)

    def checked_item(self, event):
        if self._treeCtrl.IsItemChecked(event.GetItem()):
            self.check_child_item(event.GetItem(),True)
            self.check_parent_item(event.GetItem())
        else:
            self.check_child_item(event.GetItem(),False)

    def check_child_item(self,item,checked=True):
        childs = self.get_childs(item)
        for child in self.get_childs(item):
            self._treeCtrl.CheckItem(child, checked)
            #if self._treeCtrl.HasChildren(child):
             #   self.check_child_item(child,checked)

    def check_parent_item(self,item):
        parent_item = self._treeCtrl.GetItemParent(item)
        while parent_item:
            self._treeCtrl.CheckItem2(parent_item, True,True)
            parent_item = self._treeCtrl.GetItemParent(parent_item)

    def get_childs(self, item_obj):
        item_list = []
        (item, cookie) = self._treeCtrl.GetFirstChild(item_obj)
        while item:
            item_list.append(item)
            (item, cookie) = self._treeCtrl.GetNextChild(item_obj, cookie)
        return item_list

    def CreateUnitTestFrame(self):
        module_scope = self._cur_view.ModuleScope
        if module_scope is None:
            wx.MessageBox(self._cur_view.ParseError,style=wx.OK|wx.ICON_ERROR)
            return False
        self.root = self._treeCtrl.AddRoot(module_scope.Module.Name,ct_type=1)
        self._treeCtrl.SetItemImage(self.root,self.ModuleIdx,wx.TreeItemIcon_Normal)
        self.TranverseItem(module_scope.Module,self.root)
        self._treeCtrl.CheckItem(self.root, True)
        return True

    def TranverseItem(self,node,parent):
        for child in node.Childs:
            if child.Type == parserconfig.NODE_FUNCDEF_TYPE:
                if child.IsConstructor:
                    continue
                item_image_index = self.FuncIdx
                item = self._treeCtrl.AppendItem(parent, child.Name,ct_type=1)
                self._treeCtrl.SetItemImage(item,item_image_index,wx.TreeItemIcon_Normal)
                self._treeCtrl.SetPyData(item,child)
            elif child.Type == parserconfig.NODE_CLASSDEF_TYPE:
                item_image_index = self.ClassIdx
                item = self._treeCtrl.AppendItem(parent, child.Name,ct_type=1)
                self._treeCtrl.SetItemImage(item,item_image_index,wx.TreeItemIcon_Normal)
                self._treeCtrl.SetPyData(item,child)
                self.TranverseItem(child,item)
        self._treeCtrl.Expand(parent)

    def OnClose(self,event):
        for template in wx.GetApp().GetDocumentManager().GetTemplates():
            if template.GetDocumentType() == PythonEditor.PythonDocument:
                newDoc = template.CreateDocument("", flags = wx.lib.docview.DOC_NEW)
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
        self.Destroy()

    def CreateUnitTestFromClass(self,node):
        return UNITTEST_CLASS_HEADER.format(ClassName=node.Name)
        

    def CreateUnitTestFromFunction(self,node):
        return UNITTEST_FUNC_HEADER.format(FuncName=node.Name)

    def CreateUnitTestTemplate(self):
        global_func_nodes = []
        template_text = ''
        (item, cookie) = self._treeCtrl.GetFirstChild(self.root)
        while item:
            if not self._treeCtrl.IsItemChecked(item):
                (item, cookie) = self._treeCtrl.GetNextChild(self.root, cookie)
                continue
            node = self._treeCtrl.GetPyData(item)
            if node.Type == parserconfig.NODE_CLASSDEF_TYPE:
                template_text += self.CreateUnitTestFromClass(node)
            elif node.Type == parserconfig.NODE_FUNCDEF_TYPE:
                global_func_nodes.append(node)
                
            if self._treeCtrl.HasChildren(item):
                (child, child_cookie) = self._treeCtrl.GetFirstChild(item)
                while child:
                    if not self._treeCtrl.IsItemChecked(child):
                        (child, child_cookie) = self._treeCtrl.GetNextChild(item, child_cookie)
                        continue
                    child_node = self._treeCtrl.GetPyData(child)
                    if child_node.Type == parserconfig.NODE_FUNCDEF_TYPE:
                        template_text += self.CreateUnitTestFromFunction(child_node)
                    (child, child_cookie) = self._treeCtrl.GetNextChild(item, child_cookie)
            (item, cookie) = self._treeCtrl.GetNextChild(self.root, cookie)

        if global_func_nodes != []:
            global_function_node = nodeast.ClassDef("GlobalFunction",-1,-1,None,None)
            template_text += self.CreateUnitTestFromClass(global_function_node)
            for func_node in global_func_nodes:
                template_text += self.CreateUnitTestFromFunction(func_node)

        template_text += "\n"
        return template_text
        
