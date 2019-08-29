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
        self.raise_parse_error = False

    def ParsefileContent(self,filepath,content,encoding=None):
        node = codeparser.CodebaseParser.ParsefileContent(self,filepath,content,encoding)
        doc = self.get_node_doc(node)
        module_d = make_module_dict(os.path.basename(filepath).split('.')[0],filepath,False,[],doc)
        self.WalkBody(node.body,module_d)
        return module_d

    def AddNodeData(self,name,lineno,col,node_type,parent,**kwargs):
        if node_type in [config.NODE_CLASS_PROPERTY,config.NODE_FUNCDEF_TYPE,config.NODE_ARG_TYPE,config.NODE_CLASSDEF_TYPE,config.NODE_IMPORT_TYPE,config.NODE_ASSIGN_TYPE,config.NODE_FROMIMPORT_TYPE]:
            #导入模块作为儿子特殊处理
            if node_type == config.NODE_IMPORT_TYPE:
                #是否是from xx import yyy
                is_parent_from = self.GetParentType(parent) == config.NODE_FROMIMPORT_TYPE
                if is_parent_from:
                    module = parent['name']
                else:
                    module = name
                #查找导入模块的智能数据库文件
                module_members_file,is_builtin = self.FindModuleMembersFile(module)
                if module_members_file is not None:
                    with open(module_members_file,'rb') as f:
                        data = pickle.load(f)
                        childs = []
                        module_path = data.get('path',module)
                        #如果是from xx import yyy导入该模块的所有儿子到当前模块作为儿子
                        if is_parent_from:
                            for child in data['childs']:
                                #导入模块的所有成员
                                if name == "*":
                                    childs.append(child)
                                #导入某一个成员
                                else:
                                    if name == child['name']:
                                        childs.append(child)
                            if childs == []:
                                pass
                                #print ('child %s is not find in module %s members file %s' % (name,module,module_members_file))
                                #assert(False)
                            
                            for child_data in childs:
                                #导入其它模块的成员到当前模块时parent必须为当前模块,root的值既是
                                extra_args = {'module_path':module_path,'is_builtin':is_builtin}
                                #如果是赋值类型的成员,获取其值以及值类型
                                if child_data['type'] == config.NODE_ASSIGN_TYPE:
                                    extra_args.update({'value':child_data['value'],'value_type':child_data['value_type']})
                                self.AddNodeData(child_data['name'],child_data.get('line',-1),child_data.get('col',-1),child_data['type'],kwargs.get('root'),**extra_args)
                            kwargs.pop('root')
                        #仅仅是import则只把导入模块作为当前模块的儿子,设置line和col为0,即转到模块文件时默认定位到第一行
                        else:
                            lineno = 0
                            col = 0
                            kwargs.update({'module_path':module_path,'is_builtin':is_builtin})
                else:
                    #有可能导入模块的智能数据库文件还没有生成,标记col和line为-1,加入到unfinish列表,以便下次重新分析并生成数据库文件
                    lineno = -1
                    col = -1
                    #print ("module %s members files is not exist"%module)
                
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
        self.member_file_path = dest_file_name + config.MEMBERS_FILE_EXTENSION
        if os.path.exists(self.member_file_path) and not self.force_update:
            #print (self.module_path,'has been already analyzed')
            return

        doc = None
        try:
            module_d = self.Parsefile(self.module_path)
        except Exception as e:
            print ('parse file %s error' %self.module_path)
            if self.raise_parse_error:
                tp,val,tb = sys.exc_info()
                import traceback
                traceback.print_exception(tp, val, tb)
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
        with open(dest_file_name + config.MEMBERLIST_FILE_EXTENSION, 'w') as o2:
            name_sets = set()
            for data in childs:
                name = data['name']
                if name in name_sets:
                    continue
                o2.write(name)
                o2.write('\n')
                name_sets.add(name)
    
    def FindModuleMembersFile(self,module_name):
        if not module_name:
            return None,False
        #查找当前目录下是否存在模块的智能数据库文件
        members_file_name = module_name + config.MEMBERS_FILE_EXTENSION
        cur_members_file = os.path.join(self.output,members_file_name)
        if not os.path.exists(cur_members_file):
            #再查找是否是内建模块智能数据库文件
            builtin_data_dir = os.path.dirname(os.path.dirname(self.output))
            py_ver = "2" if utils.IsPython2() else "3"
            builtin_members_file = os.path.join(builtin_data_dir,"builtins",py_ver,members_file_name)
            if os.path.exists(builtin_members_file):
                return builtin_members_file,True
            return None,False
        return cur_members_file,False