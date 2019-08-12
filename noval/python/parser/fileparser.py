#coding:utf-8
import ast
import os
import config
import nodeast
import sys
import utils
import pickle
import codeparser

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

def make_module_dict(name,path,is_builtin,childs,doc,refs=[]):
    if is_builtin:
        module_data = dict(name=name,is_builtin=True,doc=doc,childs=childs,type=config.NODE_MODULE_TYPE)
    else:
        module_data = dict(name=name,path=path,childs=childs,doc=doc,refs=refs,type=config.NODE_MODULE_TYPE)
    return module_data

class FiledumpParser(codeparser.CodebaseParser):

    def __init__(self,module_path,output_path,force_update=False):
        codeparser.CodebaseParser.__init__(self,deep=False)
        self.top_module_name,self.is_package = utils.get_relative_name(module_path)
        self.output = output_path
        self.force_update = force_update
        self.module_path = module_path

    def ParsefileContent(self,filepath,content,encoding=None):
        node = codeparser.CodebaseParser.ParsefileContent(self,filepath,content,encoding)
        doc = self.get_node_doc(node)
        module_d = make_module_dict(os.path.basename(filepath).split('.')[0],filepath,False,[],doc)
        self.WalkBody(node.body,module_d)
        return module_d

    def AddNodeData(self,name,lineno,col,node_type,parent,**kwargs):
        if node_type in [config.NODE_CLASS_PROPERTY,config.NODE_FUNCDEF_TYPE,config.NODE_ARG_TYPE,config.NODE_CLASSDEF_TYPE,config.NODE_FROMIMPORT_TYPE,config.NODE_ASSIGN_TYPE]:
            data = dict(name=name,line=lineno,col=col,type=node_type,**kwargs)
            #fromimport不能作为儿子
            if parent is None or node_type == config.NODE_FROMIMPORT_TYPE:
                return data
            if 'childs' in parent:
                parent['childs'].append(data)
            else:
                parent['childs'] = [data]
            return data

    def GetParentType(self,parent):
        return parent['type']

    def Dump(self):
        if self.top_module_name == "":
            return
        dest_file_name = os.path.join(self.output,self.top_module_name)
        self.member_file_path = dest_file_name + ".$members"
        if os.path.exists(self.member_file_path) and not self.force_update:
            #print (self.module_path,'has been already analyzed')
            return

        doc = None
        try:
            module_d = self.Parsefile(self.module_path)
        except:
            print ('parse file %s error' %self.module_path)
            return
        #如果是包,则将文件夹下的所有python模块作为其儿子
        if self.is_package:
            module_childs = get_package_childs(self.module_path)
            module_d['childs'].extend(module_childs)
        else:
            #处理sys modules中的模块,如果类似os.path这样的模块,这样需要添加到os模块的儿子中
            for module_key in sys.modules.keys():
                sys_module_name = self.top_module_name + "."
                if module_key.startswith(sys_module_name):
                    module_instance = sys.modules[module_key]
                    d = dict(name=module_key.replace(sys_module_name,""),full_name=module_instance.__name__,\
                            path=module_instance.__file__.rstrip("c"),type=config.NODE_MODULE_TYPE)
                    module_d['childs'].append(d)
                    break
        with open(self.member_file_path, 'wb') as o1:
            # Pickle dictionary using protocol 0.
            pickle.dump(module_d, o1,protocol=0)
        childs = module_d['childs']
        with open(dest_file_name + ".$memberlist", 'w') as o2:
            name_sets = set()
            for data in childs:
                name = data['name']
                if name in name_sets:
                    continue
                o2.write(name)
                o2.write('\n')
                name_sets.add(name)
           # for ref in refs:
            #    for name in ref['names']:
             #       o2.write( ref['module'] + "/" + name['name'])
              #      o2.write('\n')
    
