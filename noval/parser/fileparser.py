#coding:utf-8
import ast
import os
import config
import nodeast
import sys
import utils
import pickle
import codeparser

#below tow codes will cause redirect output problem when use py2exe to transfer into windows exe
#reload(sys)
#sys.setdefaultencoding("utf-8")



def is_package_dir(dir_name):
    package_file = "__init__.py"
    if os.path.exists(os.path.join(dir_name,package_file)):
        return True
    return False

def get_package_childs(module_path):
    module_dir = os.path.dirname(module_path)
    file_name = os.path.basename(module_path)
    assert(file_name == "__init__.py")
    childs = []
    for file_name in os.listdir(module_dir):
        file_path_name = os.path.join(module_dir,file_name)
        if os.path.isfile(file_path_name) and not file_name.endswith(".py"):
            continue
        if file_name == "__init__.py":
            continue
            
        if os.path.isdir(file_path_name) and not is_package_dir(file_path_name) :
            continue
        if os.path.isfile(file_path_name):
            module_name = '.'.join(os.path.basename(file_name).split('.')[0:-1])
            full_module_name,_ = utils.get_relative_name(file_path_name)
        else:
            module_name = file_name
            file_path_name = os.path.join(file_path_name,"__init__.py")
            full_module_name,_ = utils.get_relative_name(file_path_name)
        d = dict(name=module_name,full_name=full_module_name,path=file_path_name,type=config.NODE_MODULE_TYPE)
        childs.append(d)        
    return childs

def fix_ref_module_name(module_dir,ref_module_name):
    ref_module_path = os.path.join(module_dir,ref_module_name + ".py")
    ref_module_package_path = os.path.join(module_dir,ref_module_name)
    ref_module_package_file_path = os.path.join(ref_module_package_path,"__init__.py")
    if os.path.exists(ref_module_path):
        return utils.get_relative_name(ref_module_path)[0]
    elif os.path.exists(ref_module_package_file_path):
        return utils.get_relative_name(ref_module_package_file_path)[0]
    #elif ref_module_name in sys.modules:
     #   return sys.modules[ref_module_name].__name__
    else:
        return ref_module_name

def fix_refs(module_dir,refs):
    for ref in refs:
        ref_module_name = fix_ref_module_name(module_dir,ref['module'])
        ref['module'] = ref_module_name

def dump(module_path,output_name,dest_path,is_package):
    doc = None
    if utils.IsPython3():
        f = open(module_path,encoding="utf-8")
    else:
        f = open(module_path)
    with f:
        content = f.read()
        try:
            node = ast.parse(content,module_path)
            doc = codeparser.get_node_doc(node)
            childs,refs = walk(node)
        except Exception as e:
            print(e)
            return
        module_name = os.path.basename(module_path).split(".")[0]
        if is_package:
            module_childs = get_package_childs(module_path)
            childs.extend(module_childs)
        else:
            for module_key in sys.modules.keys():
                starts_with_module_name = output_name + "."
                if module_key.startswith(starts_with_module_name):
                    module_instance = sys.modules[module_key]
                    d = dict(name=module_key.replace(starts_with_module_name,""),full_name=module_instance.__name__,\
                            path=module_instance.__file__.rstrip("c"),type=config.NODE_MODULE_TYPE)
                    childs.append(d)
                    break
                    
        module_dict = make_module_dict(module_name,module_path,False,childs,doc,refs)
        fix_refs(os.path.dirname(module_path),refs)
        dest_file_name = os.path.join(dest_path,output_name )
        with open(dest_file_name + ".$members", 'wb') as o1:
            # Pickle dictionary using protocol 0.
            pickle.dump(module_dict, o1,protocol=0)
        with open(dest_file_name + ".$memberlist", 'w') as o2:
            name_sets = set()
            for data in childs:
                name = data['name']
                if name in name_sets:
                    continue
                o2.write(name)
                o2.write('\n')
                name_sets.add(name)
            for ref in refs:
                for name in ref['names']:
                    o2.write( ref['module'] + "/" + name['name'])
                    o2.write('\n')

def make_module_dict(name,path,is_builtin,childs,doc,refs=[]):
    if is_builtin:
        module_data = dict(name=name,is_builtin=True,doc=doc,childs=childs)
    else:
          module_data = dict(name=name,path=path,childs=childs,doc=doc,refs=refs)
    return module_data

def walk_method_element(node):
    childs = []
    for element in node.body:
        if isinstance(element,ast.Assign):
            targets = element.targets
            line_no = element.lineno
            col = element.col_offset
            for target in targets:
                if type(target) == ast.Attribute:
                    if type(target.value) == ast.Name and target.value.id == "self":
                        name = target.attr
                        data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                        childs.append(data)
    return childs

def make_element_data(element,parent,childs,refs):
    if isinstance(element,ast.FunctionDef):
        def_name = element.name
        line_no = element.lineno
        col = element.col_offset
        args = []
        is_class_method = False
        for deco in element.decorator_list:
            line_no += 1
            if type(deco) == ast.Name:
                if deco.id == codeparser.CLASS_METHOD_NAME or deco.id == codeparser.STATIC_METHOD_NAME:
                    is_class_method = True
                    break
        is_method = False
        default_arg_num = len(element.args.defaults)
        arg_num = len(element.args.args)
        for i,arg in enumerate(element.args.args):
            is_default = False
            #the last serveral argments are default arg if default argment number is not 0
            if i >= arg_num - default_arg_num:
                is_default = True
            if utils.IsPython2():
                if type(arg) == ast.Name:
                    if arg.id == 'self':
                        is_method = True
                    arg = dict(name=arg.id,is_default=is_default,line=arg.lineno,col=arg.col_offset)
                    args.append(arg)
            elif utils.IsPython3():
                if type(arg) == ast.arg:
                    if arg.arg == 'self':
                        is_method = True
                    arg = dict(name=arg.arg,is_default=is_default,line=arg.lineno,col=arg.col_offset)
                    args.append(arg)
        #var arg
        if element.args.vararg is not None:
            if utils.IsPython3():
                args.append(dict(name=element.args.vararg.arg,is_var=True,line=line_no,col=col))
            elif utils.IsPython2():
                args.append(dict(name=element.args.vararg,is_var=True,line=line_no,col=col))
        #keyword arg
        if element.args.kwarg is not None:
            if utils.IsPython3():
                args.append(dict(name=element.args.kwarg.arg,is_kw=True,line=line_no,col=col))
            elif utils.IsPython2():
                args.append(dict(name=element.args.kwarg,is_kw=True,line=line_no,col=col))
        doc = codeparser.get_node_doc(element)
        data = dict(name=def_name,line=line_no,col=col,type=config.NODE_FUNCDEF_TYPE,\
                    is_method=is_method,is_class_method=is_class_method,args=args,doc=doc)
        childs.append(data)
        ##parse self method,parent is class definition
        if is_method and isinstance(parent,ast.ClassDef):
            childs.extend(walk_method_element(element))
    elif isinstance(element,ast.ClassDef):
        class_name = element.name
        line_no = element.lineno
        col = element.col_offset
        base_names = codeparser.GetBases(element)
        doc = codeparser.get_node_doc(element)
        cls_childs,_ = walk(element)
        data = dict(name=class_name,line=line_no,col=col,type=config.NODE_CLASSDEF_TYPE,\
                        bases=base_names,childs=cls_childs,doc=doc)
        childs.append(data)
    elif isinstance(element,ast.Assign):
        targets = element.targets
        line_no = element.lineno
        col = element.col_offset
        for target in targets:
            if type(target) == ast.Tuple:
                elts = target.elts
                for elt in elts:
                    name = elt.id
                    data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                    childs.append(data)
            elif type(target) == ast.Name:
                name = target.id
                data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                childs.append(data)
    elif isinstance(element,ast.ImportFrom):
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
        names = []
        for name in element.names:
            d = {'name':name.name}
            if name.asname is not None:
                d.update({'asname':name.asname})
            names.append(d)
        data = dict(module=module_name,names=names)
        refs.append(data)
    elif isinstance(element,ast.If):
        for body in element.body:
            make_element_data(body,parent,childs,refs)
        for orelse in element.orelse:
            make_element_data(orelse,parent,childs,refs)
    
def walk(node):
    childs = []
    refs = []
    for element in node.body:
        make_element_data(element,node,childs,refs)
    return childs,refs
        
if __name__ == "__main__":
    
  ###  print get_package_childs(r"C:\Python27\Lib\site-packages\aliyunsdkcore\auth\__init__.py")
    module = parse(r"D:\env\Noval\noval\parser\fileparser.py")
   ## module = parse(r"D:\env\Noval\noval\test\run_test_input.py")
    ##print module
    dump(r"C:\Users\wk\AppData\Local\Programs\Python\Python36-32\Lib\collections\abc.py","collections","./",False)
    import pickle
    with open(r"D:\env\Noval\noval\parser\collections.$members",'rb') as f:
        datas = pickle.load(f)
   ### print datas['name'],datas['path'],datas['is_builtin']
    import json
    print (json.dumps(datas,indent=4))
    
