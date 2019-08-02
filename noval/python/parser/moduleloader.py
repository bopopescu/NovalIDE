import nodeast
import scope

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
            for line in f.readlines():
                if -1 == line.find("/"):
                    member_list.append(line.strip())
                else:
                    names = line.strip().split("/")
                    module_name = names[0]
                    ref_name = names[1]
                    if ref_name != "*":
                        member_list.append(ref_name)
                    else:
                        ref_module = self._manager.GetModule(module_name)
                        if ref_module is None:
                            continue
                        else:
                            member_list.extend(ref_module.GetMemberList())
            ##return map(lambda s:s.strip(),f.readlines())
        return member_list

    def GetMemberList(self):
        member_list = self.LoadMembeList()
        member_list.sort(CmpMember)
        return member_list

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
                if member.has_key(self.CHILD_KEY):
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
        return None
        
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
            return None
        if len(names) == 0:
            return self.MakeModuleScope()
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
            child_module._path = child[self.PATH_KEY]
            child_module.GetDoc()
            return child_module.MakeModuleScope()
        module_scope = self.MakeModuleScope()
        self.MakeChildScope(child,module_scope.Module)
        module_scope.MakeModuleScopes()
        return module_scope.ChildScopes[0]
        
    def MakeChildScope(self,child,parent):
        name = child[self.NAME_KEY]
        line_no = child.get(self.LINE_KEY,-1)
        col = child.get(self.COL_KEY,-1)
        doc = child.get('doc',None)
        if child[self.TYPE_KEY] == config.NODE_FUNCDEF_TYPE:
            datas = child.get('args',[])
            args = []
            for arg_data in datas:
                arg = nodeast.ArgNode(name=arg_data.get('name'),line=arg_data.get('line'),\
                        col=arg_data.get('col'),is_default=arg_data.get('is_default'),\
                        is_var=arg_data.get('is_var',False),is_kw=arg_data.get('is_kw',False),parent=None)
                args.append(arg)
            node = nodeast.FuncDef(name,line_no,col,parent,doc,is_method=child.get('is_method',False),\
                    is_class_method=child.get('is_class_method',False),args=args)
        elif child[self.TYPE_KEY] == config.NODE_CLASSDEF_TYPE:
            bases = child.get('bases',[])
            for i,base in enumerate(bases):
                bases[i] = parent.Name + "." + base
            #print (bases)
            node = nodeast.ClassDef(name,line_no,col,parent,doc,bases=bases)
            for class_child in child.get(self.CHILD_KEY,[]):
                self.MakeChildScope(class_child,node)
        elif child[self.TYPE_KEY] == config.NODE_OBJECT_PROPERTY or \
                child[self.TYPE_KEY] == config.NODE_CLASS_PROPERTY:
            node = nodeast.PropertyDef(name,line_no,col,config.ASSIGN_TYPE_UNKNOWN,"",parent)
        elif child[self.TYPE_KEY] == config.NODE_UNKNOWN_TYPE:
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
        return None
