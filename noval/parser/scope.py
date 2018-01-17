import fileparser
import config
from utils import CmpMember
import intellisence
import nodeast

class Scope(object):
    def __init__(self,line_start,line_end,parent=None):
        self._line_start = line_start
        self._line_end = line_end
        self._parent = parent
        self._child_scopes = []
        if self._parent != None:
            self.Parent.AppendChildScope(self)
    @property
    def Parent(self):
        return self._parent       
    @property
    def LineStart(self):
        return self._line_start
    @property
    def LineEnd(self):
        return self._line_end
    @LineEnd.setter
    def LineEnd(self,line):
        self._line_end = line
    @property
    def ChildScopes(self):
        return self._child_scopes
        
    def HasNoChild(self):
        return 0 == len(self._child_scopes)
        
    def AppendChildScope(self,scope):
        self._child_scopes.append(scope)
    
    def IslocateInScope(self,line):
        if self.LineStart <= line and self.LineEnd >= line:
            return True
        return False
        
    def RouteChildScopes(self):
        self.ChildScopes.sort(key=lambda c :c.LineStart)
        last_scope = None
        for child_scope in self.ChildScopes:
            if child_scope.Node.Type == config.NODE_FUNCDEF_TYPE:
                child_scope.RouteChildScopes()
            elif child_scope.Node.Type == config.NODE_CLASSDEF_TYPE:
                child_scope.RouteChildScopes()
            if last_scope is not None:
                last_scope.LineEnd = child_scope.LineStart -1
                last_scope.Parent.LineEnd = last_scope.LineEnd
            last_scope = child_scope
        if last_scope is not None:    
            last_scope.Parent.LineEnd = last_scope.LineEnd
            
    def FindScope(self,line):
        for child_scope in self.ChildScopes:
            if child_scope.IslocateInScope(line):
                if self.IsRoutetoEnd(child_scope):
                    return child_scope
                else:
                    return child_scope.FindScope(line)
                    
    def FindScopeInChildScopes(self,name):
        for child_scope in self.ChildScopes:
            if child_scope.EqualName(name):
                return child_scope
        return None
        
    def IsRoutetoEnd(self,scope):
        for child_scope in scope.ChildScopes:
            if not child_scope.HasNoChild():
                return False
        return True        
        
    def FindScopeInScope(self,name):
        found_scope = None
        parent = self
        while parent is not None:
            found_scope = parent.FindScopeInChildScopes(name)
            if found_scope != None:
                break
            parent = parent.Parent
        return found_scope
        
    def FindDefinition(self,name):
        names = name.split('.')
        if names[0] == 'self':
            return self.FindScopeInScope(names[1])
        else:
            find_scope = None
            i = len(names)
            find_name = ""
            while True:
                if i <= 0:
                    break
                find_name = ".".join(names[0:i])
                find_scope = self.FindScopeInScope(find_name)
                if find_scope is not None:
                    break
                i -= 1
            return find_scope
        
    def FindDefinitionScope(self,name):
        names = name.split('.')
        if names[0] == 'self':
            if len(names) == 1:
                return self.Parent
            else:
                return self.FindScopeInScope(names[1])
        else:
            return self.FindScopeInScope(names[0])
            
class ModuleScope(Scope):
        def __init__(self,module,line_count):
            super(ModuleScope,self).__init__(0,line_count)
            self._module = module
        @property
        def Module(self):
            return self._module
        
        def MakeModuleScopes(self):
            self.MakeScopes(self.Module,self)
            
        def MakeScopes(self,node,parent_scope):
            for child in node.Childs:
                if child.Type == config.NODE_FUNCDEF_TYPE:
                    func_def_scope = FuncDefScope(child,parent_scope,self)
                    self.MakeScopes(child,func_def_scope)
                elif child.Type == config.NODE_CLASSDEF_TYPE:
                    class_def_scope = ClassDefScope(child,parent_scope,self)
                    self.MakeScopes(child,class_def_scope)
                elif child.Type == config.NODE_OBJECT_PROPERTY or\
                            child.Type == config.NODE_ASSIGN_TYPE:
                    NameScope(child,parent_scope,self)
                elif child.Type == config.NODE_IMPORT_TYPE:
                    ImportScope(child,parent_scope,self)
                elif child.Type == config.NODE_FROMIMPORT_TYPE:
                    from_import_scope = FromImportScope(child,parent_scope,self)
                    self.MakeScopes(child,from_import_scope)
                elif child.Type == config.NODE_UNKNOWN_TYPE:
                    UnknownScope(child,parent_scope,self)
                    
        def __str__(self):
            print 'module name is',self.Module.Name,'path is',self.Module.Path
            for child_scope in self.ChildScopes:
                print 'module child:', child_scope
            return self.Module.Name
            
        def FindScope(self,line):
            find_scope = Scope.FindScope(self,line)
            if find_scope == None:
                return self
            return find_scope
                                  
class NodeScope(Scope):
        def __init__(self,node,parent,root):
            super(NodeScope,self).__init__(node.Line,node.Line,parent)
            self._node= node
            self._root = root
        @property
        def Node(self):
            return self._node
        
        def EqualName(self,name):
            return self.Node.Name == name
            
        def GetMemberList(self,sort=True):
            return self.Node.GetMemberList(sort)

        @property
        def Root(self):
            return self._root        
            
class FuncDefScope(NodeScope):
        def __init__(self,func_def_node,parent,root):
            super(FuncDefScope,self).__init__(func_def_node,parent,root)
            
        def __str__(self):
            print 'type is func scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            for child in self.ChildScopes:
                print 'func scope child:', child
            return self.Node.Name

class ClassDefScope(NodeScope):
        INIT_METHOD_NAME = "__init__"
        def __init__(self,class_def_node,parent,root):
            super(ClassDefScope,self).__init__(class_def_node,parent,root)
            
        def __str__(self):
            print 'type is class scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            for child in self.ChildScopes:
                print 'class scope child:', child
            return self.Node.Name
            
        def FindScopeInChildScopes(self,name):
            found_child_scope = Scope.FindScopeInChildScopes(self,name)
            if None == found_child_scope:
                for base in self.Node.Bases:
                    base_scope = self.Parent.FindDefinitionScope(base)
                    if base_scope is not None:
                        if base_scope.Node.Type == config.NODE_IMPORT_TYPE:
                            base_child_scope = intellisence.IntellisenceManager().find_name_definition(base + "."+ name)
                            if base_child_scope != None:
                                return base_child_scope
                        else:
                            base_child_scope = base_scope.FindScopeInChildScopes(name)
                            if base_child_scope != None:
                                return base_child_scope
            return found_child_scope
            
        def UniqueInitMember(self,member_list):
            while member_list.count(self.INIT_METHOD_NAME) > 1:
                member_list.remove(self.INIT_METHOD_NAME)
            
        def GetMemberList(self,sort=True):
            member_list = NodeScope.GetMemberList(self,False)
            for base in self.Node.Bases:
                base_scope = self.Parent.FindDefinitionScope(base)
                if base_scope is not None:
                    if base_scope.Node.Type == config.NODE_IMPORT_TYPE:
                        base_scope = intellisence.IntellisenceManager().find_name_definition(base)
                    if base_scope is not None:
                        member_list.extend(base_scope.GetMemberList(False))
            self.UniqueInitMember(member_list)
            if sort:
                member_list.sort(CmpMember)
            return member_list

 
class NameScope(NodeScope):
        def __init__(self,name_property_node,parent,root):
            super(NameScope,self).__init__(name_property_node,parent,root)
            
        def __str__(self):
            print 'type is name scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name
            
class UnknownScope(NodeScope):
        def __init__(self,unknown_type_node,parent,root):
            super(UnknownScope,self).__init__(unknown_type_node,parent,root)
            
        def __str__(self):
            print 'type is unknown scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name

class ImportScope(NodeScope):
        def __init__(self,import_node,parent,root):
            super(ImportScope,self).__init__(import_node,parent,root)
            
        def __str__(self):
            print 'type is import scope, import name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name
            
class FromImportScope(NodeScope):
        def __init__(self,from_import_node,parent,root):
            super(FromImportScope,self).__init__(from_import_node,parent,root)
            
        def __str__(self):
            print 'type is from import scope, from name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name
            
        def EqualName(self,name):
            for child_scope in self.ChildScopes:
                if child_scope.EqualName(name):
                    return True
            return False
    
if __name__ == "__main__":
    module = fileparser.parse(r"D:\env\Noval\noval\test\ast_test_file.py")
    module_scope = ModuleScope(module,100)
    module_scope.MakeModuleScopes()
    module_scope.RouteChildScopes()
    print module_scope
