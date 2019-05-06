import ast
from noval.python.parser import nodeast
import os
from noval.python.parser import config
from noval.python.parser import utils
import sys
import traceback

CLASS_METHOD_NAME = "classmethod"
STATIC_METHOD_NAME = "staticmethod"

def get_node_doc(node):

    body = node.body
    if len(body) > 0:
        element = body[0]
        if isinstance(element,ast.Expr) and isinstance(element.value,ast.Str):
            return element.value.s
    return None

def GetAssignValueType(node):
    value = ""
    if type(node.value) == ast.Call:
        if type(node.value.func) == ast.Name:
            value = node.value.func.id
        elif type(node.value.func) == ast.Attribute:
            value = get_attribute_name(node.value.func)
        value_type = config.ASSIGN_TYPE_OBJECT
        #if value is None:
         #   value_type = config.ASSIGN_TYPE_UNKNOWN
    else:
        value_type = GetAstType(node.value)
        if type(node.value) == ast.Name:
            value = node.value.id
    return value_type,value
    
def GetBases(node):
    base_names = []
    for base in node.bases:
        if type(base) == ast.Name:
            base_names.append(base.id)
        elif type(base) == ast.Attribute:
            base_name = get_attribute_name(base)
            base_names.append(base_name)
    return base_names
    
def GetAstType(ast_type):
    if isinstance(ast_type,ast.Num):
        return config.ASSIGN_TYPE_INT
    elif isinstance(ast_type,ast.Str):
        return config.ASSIGN_TYPE_STR
    elif isinstance(ast_type,ast.List):
        return config.ASSIGN_TYPE_LIST
    elif isinstance(ast_type,ast.Tuple):
        return config.ASSIGN_TYPE_TUPLE
    elif isinstance(ast_type,ast.Dict):
        return config.ASSIGN_TYPE_DICT
    elif isinstance(ast_type,ast.Name):
        return config.ASSIGN_TYPE_OBJECT
    else:
        return config.ASSIGN_TYPE_UNKNOWN
        

def get_attribute_name(node):
    value = node.value
    names = [node.attr]
    while type(value) == ast.Attribute:
        names.append(value.attr)
        value = value.value
    if type(value) == ast.Name:
        names.append(value.id)
    else:
        return None
    return '.'.join(names[::-1])

class CodeParser(object):
    """description of class"""

    def __init__(self,code_file_path,is_debug=False):
        self._code_file_path = code_file_path
        self._syntax_error_msg = ""
        self._is_debug = is_debug
        
    @property
    def CodeFilePath(self):
        return self._code_file_path
    
    def Parse(self):
        try:
            with open(self._code_file_path) as f:
                content = f.read()
                node = ast.parse(content,self._code_file_path)
                doc = get_node_doc(node)
                module = nodeast.Module(os.path.basename(self._code_file_path).split('.')[0],self._code_file_path,doc)
                deep_walk(node,module)
                #add a builtin import node to all file to make search builtin types convenient,which is hidden in outline view
                nodeast.BuiltinImportNode(module)
                return module
        except Exception as e:
            print (e)
            return None

    def ParseContent(self,content,text_encoding):
        try:
            node = ast.parse(content.encode(text_encoding),self._code_file_path.encode("utf-8"))
            doc = get_node_doc(node)
            module = nodeast.Module(os.path.basename(self._code_file_path).split('.')[0],self._code_file_path,doc)
            self.DeepWalk(node,module)
            #add a builtin import node to all file to make search builtin types convenient,which is hidden in outline view
            nodeast.BuiltinImportNode(module)
            return module
        except Exception as e:
            if self._is_debug:
                tp,val,tb = sys.exc_info()
                traceback.print_exception(tp, val, tb)
                
            try:
                self._syntax_error_msg = unicode(e)
            except:
                self._syntax_error_msg = str(e)
            return None
            
    @property
    def SyntaxError(self):
        return self._syntax_error_msg
            
    def DeepWalk(self,node,parent,retain_new=True):
        for element in node.body:
            self.MakeElementNode(element,parent,retain_new)
            
    def MakeElementNode(self,element,parent,retain_new):
        if isinstance(element,ast.FunctionDef):
            self.WalkFuncElement(element,parent)
        elif isinstance(element,ast.ClassDef):
            self.WalkClassElement(element,parent)
        elif isinstance(element,ast.Assign):
            self.WalkAssignElement(element,parent,retain_new)
        elif isinstance(element,ast.Import):
            self.WalkImportElement(element,parent)
        elif isinstance(element,ast.ImportFrom):
            self.WalkFromImportElement(element,parent)
        elif isinstance(element,ast.If):
            self.WalkIfElement(element,parent)
        else:
            nodeast.UnknownNode(element.lineno,element.col_offset,parent)
            
    def WalkFuncElement(self,element,parent):
        def_name = element.name
        line_no = element.lineno
        col = element.col_offset
        args = []
        is_property_def = False
        is_class_method = False
        for deco in element.decorator_list:
            line_no += 1
            if type(deco) == ast.Name:
                if deco.id == "property":
                    nodeast.PropertyDef(def_name,line_no,col,"",config.ASSIGN_TYPE_UNKNOWN,parent)
                    is_property_def = True
                    break
                elif deco.id == CLASS_METHOD_NAME or deco.id == STATIC_METHOD_NAME:
                    is_class_method = True
                    break
        if is_property_def:
            return
        is_method = False
        default_arg_num = len(element.args.defaults)
        arg_num = len(element.args.args)
        for i,arg in enumerate(element.args.args):
            is_default = False
            #the last serveral argments are default arg if default argment number is not 0
            if i >= arg_num - default_arg_num:
                is_default = True
            if type(arg) == ast.Name:
                if arg.id == 'self' and parent.Type == config.NODE_CLASSDEF_TYPE:
                    is_method = True
                arg_node = nodeast.ArgNode(arg.id,arg.lineno,arg.col_offset,is_default=is_default,parent=None)
                args.append(arg_node)
        if element.args.vararg is not None:
            arg_node = nodeast.ArgNode(element.args.vararg,line_no,col,is_var=True,parent=None)
            args.append(arg_node)
        if element.args.kwarg is not None:
            arg_node = nodeast.ArgNode(element.args.kwarg,line_no,col,is_kw=True,parent=None)
            args.append(arg_node)
        doc = get_node_doc(element)
        func_def = nodeast.FuncDef(def_name,line_no,col,parent,doc,is_method=is_method,\
                            is_class_method=is_class_method,args=args)
        self.DeepWalk(element,func_def)
        
    def WalkClassElement(self,element,parent):
        
        class_name = element.name
        base_names = GetBases(element)
        line_no = element.lineno
        col = element.col_offset
        doc = get_node_doc(element)
        class_def = nodeast.ClassDef(class_name,line_no,col,parent,doc,bases=base_names)
        self.DeepWalk(element,class_def)
        
    def WalkAssignElement(self,element,parent,retain_new):
        targets = element.targets
        line_no = element.lineno
        col = element.col_offset
        for target in targets:
            if type(target) == ast.Tuple:
                pass
           #     elts = target.elts
            #    for elt in elts:
             #       name = elt.value
              #      print name
                #    data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                 #   childs.append(data)
               #     nodeast.PropertyDef(name,line_no,col,config.PROPERTY_TYPE_NONE,parent)
            elif type(target) == ast.Name:
                name = target.id
                if parent.HasChild(name):
                    if retain_new:
                        parent.RemoveChild(name)
                    else:
                        continue
                value_type,value = GetAssignValueType(element)
                nodeast.AssignDef(name,line_no,col,value,value_type,parent)
            elif type(target) == ast.Attribute:
                if type(target.value) == ast.Name and target.value.id == "self" and parent.Type == config.NODE_FUNCDEF_TYPE and \
                        parent.IsMethod:
                    name = target.attr
                    if parent.Parent.HasChild(name):
                        if parent.Name == "__init__":
                            parent.Parent.RemoveChild(name)
                        else:
                            continue
                    value_type,value = GetAssignValueType(element)
                    nodeast.PropertyDef(name,line_no,col,value,value_type,parent)
                    

    def WalkImportElement(self,element,parent):
        for name in element.names:
            nodeast.ImportNode(name.name,element.lineno,element.col_offset,parent,name.asname)

    def WalkFromImportElement(self,element,parent):
        module_name = element.module
        if utils.IsNoneOrEmpty(module_name):
            if element.level == 1:
                module_name = "."
            elif element.level == 2:
                module_name = ".."
        else:
            if element.level == 1:
                module_name = "." + module_name
            elif element.level == 2:
                module_name = ".." + module_name
        from_import_node = nodeast.FromImportNode(module_name,element.lineno,element.col_offset,parent)
        for name in element.names:
            nodeast.ImportNode(name.name,element.lineno,element.col_offset,from_import_node,name.asname)
            
    def WalkIfElement(self,element,parent):
        #parse if __name__ == "__main__" function
        if isinstance(element.test,ast.Compare) and isinstance(element.test.left,ast.Name) and element.test.left.id == "__name__" \
                and len(element.test.ops) > 0 and isinstance(element.test.ops[0],ast.Eq) \
                and len(element.test.comparators) > 0 and isinstance(element.test.comparators[0],ast.Str) \
                and element.test.comparators[0].s == nodeast.MainFunctionNode.MAIN_FUNCTION_NAME:
            nodeast.MainFunctionNode(element.lineno,element.col_offset,parent)
        for body in element.body:
            self.MakeElementNode(body,parent,True)
        for orelse in element.orelse:
            self.MakeElementNode(orelse,parent,False)
