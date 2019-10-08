# -*- coding: utf-8 -*-
import nodeast
import scope
import pickle
import config
from noval.python.parser.utils import CmpMember,py_sorted
import os

class ModuleLoader(object):
    CHILD_KEY = "childs"
    NAME_KEY = "name"
    TYPE_KEY = "type"
    LINE_KEY = "line"
    COL_KEY = "col"
    PATH_KEY = "path"
    MEMBERS_KEY = "members"
    MEMBER_LIST_KEY = "member_list"
    FULL_NAME_KEY = "full_name"
    BUILTIN_KEY = "is_builtin"
    def __init__(self,name,members_file,member_list_file,mananger):
        self._name = name
        self._members_file = members_file
        self._member_list_file = member_list_file
        self._manager = mananger
        self._path = None
        self._is_builtin = False
        self._data = None
        self._doc = None
    @property
    def Name(self):
        return self._name

    def LoadMembers(self):
        if self._data is None:
            with open(self._members_file,'rb') as f:
                self._data = pickle.load(f)
                self._is_builtin = self._data.get(self._is_builtin,False)
                self._path = self._data.get(self.PATH_KEY)
                self._doc = self._data.get('doc',None)
        return self._data

    def GetDoc(self):
        self.LoadMembers()
        return self._doc

    def LoadMembeList(self):
        member_list = []
        with open(self._member_list_file) as f:
           # for line in f.readlines():
            #    member_list.append(line.strip())
            return(map(lambda s:s.strip(),f.readlines()))
        return member_list

    def GetMemberList(self):
        return self.LoadMembeList()
        #return py_sorted(member_list,CmpMember)

    def GetMembersWithName(self,name):
        strip_name = name.strip()
        if strip_name == "":
            names = []
        else:
            names = strip_name.split(".")
        return self.GetMembers(names)

    def GetMembers(self,names):
        if len(names) == 0:
            return self.GetMemberList()
        data = self.LoadMembers()
        member = self.GetMember(data[self.CHILD_KEY],names)
        member_list = []
        if member is not None:
            if member[self.TYPE_KEY] == config.NODE_MODULE_TYPE:
                child_module = self._manager.GetModule(member[self.FULL_NAME_KEY])
                member_list = child_module.GetMemberList()
            else:
                if self.CHILD_KEY in member:
                    for child in member[self.CHILD_KEY]:
                        member_list.append(child[self.NAME_KEY])
                ##get members in parent inherited classes
                if member[self.TYPE_KEY] == config.NODE_CLASSDEF_TYPE:
                    member_list.extend(self.GetBaseMembers(member,names))                    
        return member_list

    def GetBaseMembers(self,member,names):
        base_members = []
        bases = member.get('bases',[])
        for base in bases:
            base_members.extend(self.GetMembers(names[0:(len(names) -1)] + [base]))
        return base_members

    def FindChildDefinitionInBases(self,bases,names):
        for base in bases:
            for child in self._data[self.CHILD_KEY]:
                if child[self.NAME_KEY] == base:
                    return self.FindChildDefinition(child[self.CHILD_KEY],names)
        return []
        
    def GetMember(self,childs,names):
        for child in childs:
            if child[self.NAME_KEY] == (names[0].strip()):
                if len(names) == 1:
                    return child
                else:
                    if child[self.TYPE_KEY] != config.NODE_MODULE_TYPE:
                        return self.GetMember(child[self.CHILD_KEY],names[1:])
                    else:
                        child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
                        data = child_module.LoadMembers()
                        return self.GetMember(data[self.CHILD_KEY],names[1:])
        return None

    def FindDefinitionWithName(self,name):
        strip_name = name.strip()
        if strip_name == "":
            names = []
        else:
            names = strip_name.split(".")
        return self.FindDefinition(names)

    def FindDefinition(self,names):
        data = self.LoadMembers()
        if self._is_builtin:
            return []
        if len(names) == 0:
            return [self.MakeModuleScope(),]
        child_definition =  self.FindChildDefinition(data[self.CHILD_KEY],names)
        if child_definition is None:
            return self.FindInRefModule(data.get('refs',[]),names)
        return child_definition

    def FindInRefModule(self,refs,names):
        for ref in refs:
            ref_module_name = ref['module']
            ref_module = self._manager.GetModule(ref_module_name)
            if ref_module is None:
                continue
            for ref_name in ref['names']:
                if ref_name['name'] == '*' or ref_name['name'] == names[0]:
                    member_definition = ref_module.FindDefinition(names)
                    if member_definition is not None:
                        return member_definition
        return None

    def MakeModuleScope(self):
        module = nodeast.Module(self._name,self._path,self._doc)
        module_scope = scope.ModuleScope(module,-1)
        return module_scope

    def MakeDefinitionScope(self,child):
        if child.get(self.TYPE_KEY) == config.NODE_MODULE_TYPE:
            child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
            #某些测试模块,软件跳过分析,可能不存在,不宜作为错误处理
            if child_module is None:
                print ('module %s path %s is not exist'%(child[self.FULL_NAME_KEY],child[self.PATH_KEY]))
                return []
            child_module._path = child[self.PATH_KEY]
            child_module.GetDoc()
            return [child_module.MakeModuleScope()]
            
        if 'module_path' in child:
            module = nodeast.Module("",child['module_path'],"")
            module_scope = scope.ModuleScope(module,-1)
        else:
            module_scope = self.MakeModuleScope()
            #有些导入模块由于智能提示数据库先后生成的问题未完全分析成功,需要找出这些模块,并将其放至unfinish.txt文件列表中,等待下次生成数据库的时候再次强制分析
            if child[self.TYPE_KEY] == config.NODE_IMPORT_TYPE and child.get(self.LINE_KEY,-1) == -1:
                module_name = child[self.NAME_KEY]
                module_members_file = os.path.join(os.path.dirname(self._members_file),module_name + config.MEMBERS_FILE_EXTENSION)
                if os.path.exists(module_members_file):
                    print ('import module name %s in module %s members file %s exist,but code line is -1' % (module_name,self._path,module_members_file))
                    self._manager.AddUnfinishModuleFile(self._path)
                    
        self.MakeChildScope(child,module_scope.Module)
        module_scope.MakeModuleScopes()
        return module_scope.ChildScopes
        
    def MakeChildScope(self,child,parent):
        name = child[self.NAME_KEY]
        line_no = child.get(self.LINE_KEY,-1)
        col = child.get(self.COL_KEY,-1)
        doc = child.get('doc',None)
        is_builtin = child.get('is_builtin',False)
        if child[self.TYPE_KEY] == config.NODE_FUNCDEF_TYPE:
            datas = child.get('args',[])
            args = []
            for arg_data in datas:
                arg = nodeast.ArgNode(name=arg_data.get('name'),line=arg_data.get('line'),\
                        col=arg_data.get('col'),is_default=arg_data.get('is_default'),\
                        is_var=arg_data.get('is_var',False),is_kw=arg_data.get('is_kw',False),parent=None)
                args.append(arg)
            node = nodeast.FuncDef(name,line_no,col,parent,doc,is_method=child.get('is_method',False),\
                    is_class_method=child.get('is_class_method',False),args=args,is_built_in=is_builtin)
        elif child[self.TYPE_KEY] == config.NODE_CLASSDEF_TYPE:
            bases = child.get('bases',[])
            for i,base in enumerate(bases):
                bases[i] = parent.Name + "." + base
            #print (bases)
            node = nodeast.ClassDef(name,line_no,col,parent,doc,bases=bases,is_built_in=is_builtin)
            for class_child in child.get(self.CHILD_KEY,[]):
                self.MakeChildScope(class_child,node)
        elif child[self.TYPE_KEY] == config.NODE_CLASS_PROPERTY:
            node = nodeast.PropertyDef(name,line_no,col,config.ASSIGN_TYPE_UNKNOWN,"",parent,is_built_in=is_builtin)
        elif child[self.TYPE_KEY] == config.NODE_ASSIGN_TYPE:
            node = nodeast.AssignDef(name,line_no,col,child['value'],child['value_type'],parent,is_built_in=is_builtin)
        elif child[self.TYPE_KEY] == config.NODE_IMPORT_TYPE:
            node = nodeast.ImportNode(name,line_no,col,parent,is_built_in=is_builtin)
        else:
            node = nodeast.UnknownNode(line_no,col,parent)
                
    def FindChildDefinition(self,childs,names):
        for child in childs:
            if child[self.NAME_KEY] == (names[0].strip()):
                if len(names) == 1:
                    return self.MakeDefinitionScope(child)
                else:
                    if child[self.TYPE_KEY] != config.NODE_MODULE_TYPE:
                        child_definition = self.FindChildDefinition(child.get(self.CHILD_KEY,[]),names[1:])
                        if child_definition is None and child[self.TYPE_KEY] == config.NODE_CLASSDEF_TYPE:
                            bases = child.get('bases',[])
                            #search member definition in parent inherited classes
                            child_definition = self.FindChildDefinitionInBases(bases,names[1:])
                        return child_definition
                    else:
                        child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
                        data = child_module.LoadMembers()
                        return child_module.FindChildDefinition(data[self.CHILD_KEY],names[1:])
        return []
