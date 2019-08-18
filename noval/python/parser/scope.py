# -*- coding: utf-8 -*-
import fileparser, config,nodeast
from utils import CmpMember
import intellisence
import noval.util.utils as logger_utils

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
        if isinstance(scope,list):
            self._child_scopes.extend(scope)
        else:
            self._child_scopes.append(scope)
    
    def IslocateInScope(self,line):
        if self.LineStart <= line and self.LineEnd >= line:
            return True
        return False
        
    def RouteChildScopes(self):
        self.ChildScopes.sort(key=lambda c :c.LineStart)
        last_scope = None
        for child_scope in self.ChildScopes:
            ##exclude child scopes which is import from other modules
            if child_scope.Root.Module.Path != self.Root.Module.Path:
                continue
            if child_scope.Node.Type == config.NODE_FUNCDEF_TYPE:
                child_scope.RouteChildScopes()
            elif child_scope.Node.Type == config.NODE_CLASSDEF_TYPE:
                child_scope.RouteChildScopes()
            if last_scope is not None:
                if child_scope.LineStart > last_scope.LineEnd:
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
        child_scopes = []
        for child_scope in self.ChildScopes:
            if child_scope.EqualName(name):
                child_scopes.append(child_scope)
        return child_scopes
        
    def IsRoutetoEnd(self,scope):
        for child_scope in scope.ChildScopes:
            if not child_scope.HasNoChild():
                return False
        return True        
        
    def FindScopeInScope(self,name):
        found_scopes = []
        parent = self
        while parent is not None:
            child_scopes = parent.FindScopeInChildScopes(name)
            if child_scopes:
                found_scopes.extend(child_scopes)
            parent = parent.Parent
        return found_scopes

    def FindTopScope(self,names):
        find_scopes= []
        i = len(names)
        find_name = ""
        while True:
            if i <= 0:
                break
            find_name = ".".join(names[0:i])
            scopes = self.FindScopeInScope(find_name)
            if scopes:
                find_scopes.extend(scopes)
            i -= 1
        return find_scopes
        
    def FindScopes(self,names):
        scopes = self.FindTopScope(names)
        #search for __builtin__ member at last
        if not scopes and len(names) == 1:
            #get builtin module name from module scope,which python2 is __builtin__ and python3 is builtins
            scopes = self.FindTopScope([self.Root._builtin_module_name] + names)
        return scopes

    def GetDefinitions(self,name):
        if not name.strip():
            return []

        is_self = False
        is_cls = False
        names = name.split('.')
        #如果类的成员方法,则搜索名称不包含self
        if names[0] == 'self' and len(names) > 1 and self.IsMethodScope():
            names = names[1:]
            is_self = True
        #如果类的静态方法,则搜索名称不包含cls
        elif names[0] == 'cls' and len(names) > 1 and self.IsClassMethodScope():
            names = names[1:]
            is_cls = True

        find_scopes = self.FindScopes(names)
        if not find_scopes:
            return []
        definitions = []
        for find_scope in find_scopes:
            if is_self:
                members = find_scope.GetMember(name[5:])
            elif is_cls:
                members = find_scope.GetMember(name[4:])
            else:
                members = find_scope.GetMember(name)
            for member in members:
                #可能有重复的定义,只取一个
                if member not in definitions:
                    definitions.append(member)
        return definitions
        
    def FindNameScopes(self,name):
        names = name.split('.')
        #when like self. or cls., route to parent class scope
        if (names[0] == 'self' and self.IsMethodScope())  or (names[0] == 'cls' and self.IsClassMethodScope()):
            if len(names) == 1:
                return [self.Parent]
            else:
                return self.FindScopes(names[1:])
        else:
            return self.FindScopes(names)

    def IsMethodScope(self):
        return False

    def IsClassMethodScope(self):
        return False

    def MakeBeautyDoc(self,alltext):
        """Returns the formatted calltip string for the document.
        """
        if alltext is None:
            return None
        # split the text into natural paragraphs (a blank line separated)
        paratext = alltext.split("\n\n")
       
        # add text by paragraph until text limit or all paragraphs
        textlimit = 800
        if len(paratext[0]) < textlimit:
            numpara = len(paratext)
            calltiptext = paratext[0]
            ii = 1
            while ii < numpara and \
                  (len(calltiptext) + len(paratext[ii])) < textlimit:
                calltiptext = calltiptext + "\n\n" + paratext[ii]
                ii = ii + 1

            # if not all texts are added, add "[...]"
            if ii < numpara:
                calltiptext = calltiptext + "\n[...]"
        # present the function signature only (first newline)
        else:
            calltiptext = alltext.split("\n")[0]

##        if type(calltiptext) != types.UnicodeType:
##            # Ensure it is unicode
##            try:
##                stcbuff = self.GetBuffer()
##                encoding = stcbuff.GetEncoding()
##                calltiptext = calltiptext.decode(encoding)
##            except Exception, msg:
##                dbg("%s" % msg)

        return calltiptext
            
class ModuleScope(Scope):
    MAX_CHILD_SCOPE  = 100
    def __init__(self,module,line_count):
        super(ModuleScope,self).__init__(0,line_count)
        self._module = module
        self._builtin_module_name = "__builtin__"
    @property
    def Module(self):
        return self._module
    
    def MakeModuleScopes(self):
        self.MakeScopes(self.Module,self)

    def MakeImportScope(self,from_import_scope,parent_scope):
        from_import_name = from_import_scope.Node.Name
        member_names = []
        for child_scope in from_import_scope.ChildScopes:
            #get all import members
            if child_scope.Node.Name == "*":
                member_names.extend(intellisence.IntellisenceManager().GetModuleMembers(from_import_name,""))
                break
            #get one import member
            else:
                member_names.append(child_scope.Node.Name)
        #TODO:must reduce the child scope number,will elapse short time to finish
        #TODO:these code will expend a lot of time to finisih,should optimise later 
        for member_name in member_names[0:self.MAX_CHILD_SCOPE]:
            member_scope = intellisence.IntellisenceManager().GetModuleMember(from_import_name,member_name)
            if member_scope is not None:
                parent_scope.AppendChildScope(member_scope)
        
    def MakeScopes(self,node,parent_scope):
        for child in node.Childs:
            if child.Type == config.NODE_FUNCDEF_TYPE:
                func_def_scope = FuncDefScope(child,parent_scope,self)
                for arg in child.Args:
                    ArgScope(arg,func_def_scope,self)
                self.MakeScopes(child,func_def_scope)
            elif child.Type == config.NODE_CLASSDEF_TYPE:
                class_def_scope = ClassDefScope(child,parent_scope,self)
                self.MakeScopes(child,class_def_scope)
            elif child.Type == config.NODE_OBJECT_PROPERTY or\
                        child.Type == config.NODE_ASSIGN_TYPE:
                NameScope(child,parent_scope,self)
            elif child.Type == config.NODE_IMPORT_TYPE:
                ImportScope(child,parent_scope,self)
                #from xx import x
                if child.Parent.Type == config.NODE_FROMIMPORT_TYPE:
                    self.MakeImportScope(parent_scope,parent_scope.Parent)    
            elif child.Type == config.NODE_BUILTIN_IMPORT_TYPE:
                ImportScope(child,parent_scope,self)
                #get currenet interpreter builtin module name
                self._builtin_module_name = child.Name
            elif child.Type == config.NODE_FROMIMPORT_TYPE:
                from_import_scope = FromImportScope(child,parent_scope,self)
                self.MakeScopes(child,from_import_scope)
            elif child.Type == config.NODE_MAIN_FUNCTION_TYPE:
                MainFunctionScope(child,parent_scope,self)
            elif child.Type == config.NODE_UNKNOWN_TYPE:
                UnknownScope(child,parent_scope,self)
                
    def __str__(self):
        #print 'module name is',self.Module.Name,'path is',self.Module.Path
        #for child_scope in self.ChildScopes:
         #   print 'module child:', child_scope
        return self.Module.Name
        
    def FindScope(self,line):
        find_scope = Scope.FindScope(self,line)
        if find_scope == None:
            return self
        return find_scope

    def GetMemberList(self):
        return intellisence.IntellisenceManager().GetModuleMembers(self.Module.Name,"")

    @property
    def Root(self):
        return self

    def EqualName(self,name):
        return self.Module.Name == name

    def GetMembers(self):
        return self.Module.GetMemberList()

    def GetDoc(self):
        return self.MakeBeautyDoc(self.Module.Doc)
                                  
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
        
    def GetMemberList(self):
        return self.Node.GetMemberList()
        
    def __eq__(self, other):
        if other is None:
            return False
        return self.Node.Name == other.Node.Name and self.Node.Line == other.Node.Line and self.Node.Col == other.Node.Col
  
    @property
    def Root(self):
        return self._root

    def GetMember(self,name):
        return [self]

    def MakeFixName(self,name):
        #muse only replace once
        fix_name = name.replace(self.Node.Name,"",1)
        if fix_name.startswith("."):
            fix_name = fix_name[1:]
        return fix_name

    def GetDoc(self):
        return self.MakeBeautyDoc(self.Node.Doc)
        
    def GetArgTip(self):
        return ''

class ArgScope(NodeScope):
    def __init__(self,arg_node,parent,root):
        super(ArgScope,self).__init__(arg_node,parent,root)
    
    def GetArgName(self):
        if self.Node.IsKeyWord:
            return "**" + self.Node.Name
        elif self.Node.IsVar:
            return "*" + self.Node.Name
        elif self.Node.IsDefault:
            return self.Node.Name
        else:
            return self.Node.Name

class FuncDefScope(NodeScope):
    def __init__(self,func_def_node,parent,root):
        super(FuncDefScope,self).__init__(func_def_node,parent,root)
        
    def __str__(self):
        #print 'type is func scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
        #for child in self.ChildScopes:
         #   print 'func scope child:', child
        return self.Node.Name

    def MakeFixName(self,name):
        if self.Node.IsMethod:
            name = name.replace("self.","",1)
        fix_name = name.replace(self.Node.Name,"",1)
        if fix_name.startswith("."):
            fix_name = fix_name[1:]
        return fix_name

    def GetMember(self,name):
        fix_name = self.MakeFixName(name)
        if fix_name == "":
            return [self]
        return []

    def IsMethodScope(self):
        return self.Node.IsMethod

    def IsClassMethodScope(self):
        return self.Node.IsClassMethod

    def GetMemberList(self):
        return []
        
    def GetArgTip(self):
        info = ''
        arg_names = []
        for child_scope in self.ChildScopes:
            if child_scope.Node.Type == config.NODE_ARG_TYPE:
                arg_names.append(child_scope.GetArgName())
        if len(arg_names) > 0:
                info = "("
                info += ','.join(arg_names)
                info += ")"
        return info

class ClassDefScope(NodeScope):
    INIT_METHOD_NAME = "__init__"
    def __init__(self,class_def_node,parent,root):
        super(ClassDefScope,self).__init__(class_def_node,parent,root)
        
    def __str__(self):
        #print 'type is class scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
        #for child in self.ChildScopes:
         #   print 'class scope child:', child
        return self.Node.Name
        
    def FindScopeInChildScopes(self,name):
        #先在在类的儿子中去查找
        found_scopes = Scope.FindScopeInChildScopes(self,name)
        #再在类的基类的儿子中去查找
        if not found_scopes:
            for base in self.Node.Bases:
                base_scopes = self.Parent.FindNameScopes(base)
                if base_scopes:
                    return self.FindBasescopes(base_scopes,base,name)
        return found_scopes

    def FindBasescopes(self,base_scopes,base,name):
        find_scopes = []
        for base_scope in base_scopes:
            if base_scope.Node.Type == config.NODE_IMPORT_TYPE:
                child_scopes = base_scope.GetMember(base + "."+ name)
                find_scopes.extend(child_scopes)
            else:
                child_scopes = base_scope.FindScopeInChildScopes(name)
                find_scopes.extend(child_scopes)
        return find_scopes
        
    def UniqueInitMember(self,member_list):
        while member_list.count(self.INIT_METHOD_NAME) > 1:
            member_list.remove(self.INIT_METHOD_NAME)
        
    def GetMemberList(self):
        member_list = NodeScope.GetMemberList(self)
        for base in self.Node.Bases:
            base_scopes = self.Parent.FindNameScopes(base)
            for base_scope in base_scopes:
                if base_scope.Node.Type == config.NODE_IMPORT_TYPE:
                    member_list.extend(base_scope.GetImportMemberList(base))
                else:
                    member_list.extend(base_scope.GetMemberList())
        self.UniqueInitMember(member_list)
        return member_list

    def GetClassMembers(self,sort=True):
        return self.Node.GetClassMembers(sort)

    def GetClassMemberList(self,sort=True):
        member_list = self.GetClassMembers(False)
        for base in self.Node.Bases:
            base_scope = self.Parent.FindDefinitionScope(base)
            if base_scope is not None:
                if base_scope.Node.Type == config.NODE_IMPORT_TYPE or\
                    base_scope.Node.Type == config.NODE_BUILTIN_IMPORT_TYPE:
                    member_list.extend(base_scope.GetImportMemberList(base))
                else:
                    member_list.extend(base_scope.GetClassMembers(False))
        self.UniqueInitMember(member_list)
        if sort:
            member_list.sort(CmpMember)
        return member_list

    def GetMember(self,name):
        fix_name = self.MakeFixName(name)
        if fix_name == "":
            return [self]
        return self.FindScopeInChildScopes(fix_name)
    #class arg tip is the arg tip of class __init__ method
    def GetArgTip(self):
        for child_scope in self.ChildScopes:
            if child_scope.Node.Type == config.NODE_FUNCDEF_TYPE and child_scope.Node.IsConstructor:
                return child_scope.GetArgTip()
        return ''
 
class NameScope(NodeScope):
    def __init__(self,name_property_node,parent,root):
        super(NameScope,self).__init__(name_property_node,parent,root)
        
    def __str__(self):
        #print 'type is name scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
        return self.Node.Name

    def GetMemberList(self):
        member_list = []
        if self.Node.ValueType == config.ASSIGN_TYPE_OBJECT:
            found_scope = self.FindDefinitionScope(self.Node.Value)
            if found_scope is not None:
                if found_scope.Node.Type == config.NODE_IMPORT_TYPE:
                    member_list = found_scope.GetImportMemberList(self.Node.Value)
                else:
                    member_list = found_scope.GetMemberList()
        else:
            member_list = intellisence.IntellisenceManager().GetTypeObjectMembers(self.Node.ValueType)
        return member_list

    def GetMember(self,name):
        fix_name = self.MakeFixName(name)
        if fix_name == "":
            return [self]
        if self.Node.Value is None:
            return []
        found_scopes = self.FindNameScopes(self.Node.Value)
        members = []
        if found_scopes:
            for found_scope in found_scopes:
                if found_scope.Node.Type == config.NODE_IMPORT_TYPE:
                    members.extend(found_scope.GetMember(self.Node.Value + "." + fix_name))
                else:
                    members.extend(found_scope.GetMember(fix_name))
        return []
            
class UnknownScope(NodeScope):
    def __init__(self,unknown_type_node,parent,root):
        super(UnknownScope,self).__init__(unknown_type_node,parent,root)
        
    def __str__(self):
        #print 'type is unknown scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
        return self.Node.Name

class ImportScope(NodeScope):
    def __init__(self,import_node,parent,root):
        super(ImportScope,self).__init__(import_node,parent,root)
        
    def __str__(self):
        #print 'type is import scope, import name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
        return self.Node.Name

    def EqualName(self,name):
        if self.Node.AsName is not None:
            return self.Node.AsName == name
        else:
            return NodeScope.EqualName(self,name)

    def MakeFixName(self,name):
        #should only replace the first find name 
        if self.Node.AsName is not None:
            fix_name = name.replace(self.Node.AsName,"",1)
        else:
            fix_name = name.replace(self.Node.Name,"",1)
        if fix_name.startswith("."):
            fix_name = fix_name[1:]
        return fix_name

    def GetImportMemberList(self,name):
        fix_name = self.MakeFixName(name)
        member_list = intellisence.IntellisenceManager().GetModuleMembers(self.Node.Name,fix_name)
        return member_list

    def GetMember(self,name):
        fix_name = self.MakeFixName(name)
        if fix_name == "":
            return [self]
        return intellisence.IntellisenceManager().GetModuleMember(self.Node.Name,fix_name)

    def GetDoc(self):
        doc = intellisence.IntellisenceManager().GetModuleDoc(self.Node.Name)
        return self.MakeBeautyDoc(doc)
        
    def GetImportMemberArgTip(self,name):
        fix_name = self.MakeFixName(name)
        if fix_name == "":
            return ''
        return intellisence.IntellisenceManager().GetModuleMemberArgmentTip(self.Node.Name,fix_name)
            
class FromImportScope(NodeScope):
    def __init__(self,from_import_node,parent,root):
        super(FromImportScope,self).__init__(from_import_node,parent,root)
        
    def __str__(self):
        #print 'type is from import scope, from name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
        return self.Node.Name
        
    def EqualName(self,name):
        for child_scope in self.ChildScopes:
            if child_scope.EqualName(name):
                return True
        return False
            
class MainFunctionScope(NodeScope):
    def __init__(self,main_function_node,parent,root):
        super(MainFunctionScope,self).__init__(main_function_node,parent,root)

