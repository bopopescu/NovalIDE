import sys
import os
import pickle
import config,fileparser,utils
import types
import datetime

def generate_builtin_data(dest_path,database_version):
    def make_python2_builtin_types(builtin_type,recursive=True):
        childs = []
        for name in dir(builtin_type):
            try:
                builtin_attr_intance = getattr(builtin_type,name)
            except:
                continue
            builtin_attr_type = type(builtin_attr_intance)
            if builtin_attr_type == types.TypeType:
                if not recursive:
                    continue
                builtin_attr_childs = make_python2_builtin_types(builtin_attr_intance,False)
                node = dict(name = name,is_builtin=True,type = config.NODE_CLASSDEF_TYPE,childs=builtin_attr_childs,doc=builtin_attr_intance.__doc__)
                childs.append(node)
            elif builtin_attr_type == types.BuiltinFunctionType or builtin_attr_type == types.BuiltinMethodType \
                        or str(builtin_attr_type).find("method_descriptor") != -1:
                node = dict(name = name,is_builtin=True,type = config.NODE_FUNCDEF_TYPE,doc=builtin_attr_intance.__doc__)
                childs.append(node)
            else:
                node = dict(name = name,is_builtin=True,type = config.NODE_CLASS_PROPERTY)
                childs.append(node)
        return childs

    def make_python3_builtin_types(builtin_type,recursive=True):
        childs = []
        for name in dir(builtin_type):
            try:
                builtin_attr_intance = getattr(builtin_type,name)
            except:
                continue
            builtin_attr_type = type(builtin_attr_intance)
            if builtin_attr_type == type(type):
                if not recursive:
                    continue
                builtin_attr_childs = make_python3_builtin_types(builtin_attr_intance,False)
                node = dict(name = name,is_builtin=True,type = config.NODE_CLASSDEF_TYPE,childs=builtin_attr_childs,doc=builtin_attr_intance.__doc__)
                childs.append(node)
            elif builtin_attr_type == types.BuiltinFunctionType or builtin_attr_type == types.BuiltinMethodType \
                        or str(builtin_attr_type).find("method_descriptor") != -1:
                node = dict(name = name,is_builtin=True,type = config.NODE_FUNCDEF_TYPE,doc=builtin_attr_intance.__doc__)
                childs.append(node)
            else:
                node = dict(name = name,is_builtin=True,type = config.NODE_CLASS_PROPERTY)
                childs.append(node)
        return childs

    def make_builtin_types(builtin_type):
        if utils.IsPython2():
            return make_python2_builtin_types(builtin_type)
        else:
            return make_python3_builtin_types(builtin_type)
        
    utils.MakeDirs(dest_path)
    if not utils.NeedRenewDatabase(dest_path,database_version):
        return
    for built_module in sys.builtin_module_names:
        module_instance = __import__(built_module)
        childs = make_builtin_types(module_instance)
        with open(dest_path + "/" + built_module + config.MEMBERLIST_FILE_EXTENSION, 'w') as f:
            for node in childs:
                f.write(node['name'])
                f.write('\n')
        module_dict = fileparser.make_module_dict(built_module,'',True,childs,doc=module_instance.__doc__)
        with open(dest_path + "/" + built_module + config.MEMBERS_FILE_EXTENSION, 'wb') as j:
            # Pickle dictionary using protocol 0.
            pickle.dump(module_dict, j,protocol=0)
    utils.SaveDatabaseVersion(dest_path,database_version)

if __name__ == "__main__":
    out_path = sys.argv[1]
    new_database_version = sys.argv[2]
    generate_builtin_data(out_path,new_database_version)
