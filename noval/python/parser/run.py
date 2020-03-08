from __future__ import print_function
import sys
import os
import pickle
import config,fileparser,utils
import json
import types
import time
import functools
import multiprocessing
import datetime
import importlib
import glob
import faulthandler
import logging

logger = logging.getLogger("novalide.intellisense.run")
        
def SaveLastUpdateTime(database_location):
    with open(os.path.join(database_location,config.UPDATE_FILE),"w") as f:
        datetime_str = datetime.datetime.strftime(datetime.datetime.now(), config.ISO_8601_DATETIME_FORMAT)
        f.write(datetime_str)

def get_python_version():
    #less then python 2.7 version
    if isinstance(sys.version_info,tuple) and sys.version_info[0] == 2:
        version = str(sys.version_info[0]) + "." +  str(sys.version_info[1]) 
        #if sys.verion[0] == 2 and sys.version_info[2] > 0:
        if sys.version_info[2] > 0:
            version += "."
            version += str(sys.version_info[2])
    #python 2.7 or python3 version,which python3 version type is tuple,python2.7 version type is not tuple
    else:
        if sys.version_info.releaselevel.find('final') != -1:
            version = str(sys.version_info.major) + "." +  str(sys.version_info.minor) + "."  + str(sys.version_info.micro)
        elif sys.version_info.releaselevel.find('beta') != -1:
            version = str(sys.version_info.major) + "." +  str(sys.version_info.minor) + "."  + str(sys.version_info.micro) + \
                        "b" + str(sys.version_info.serial)
        elif sys.version_info.releaselevel.find('candidate') != -1:
            version = str(sys.version_info.major) + "." +  str(sys.version_info.minor) + "."  + str(sys.version_info.micro) + \
                    "rc" +  str(sys.version_info.serial)
        elif sys.version_info.releaselevel.find('alpha') != -1:
            version = str(sys.version_info.major) + "." +  str(sys.version_info.minor) + "."  + str(sys.version_info.micro) + \
                "a" + str(sys.version_info.serial)
        else:
            print (sys.version_info.releaselevel)
    return version
     
def generate_intelligent_data_by_pool(out_path,new_database_version):
    version = get_python_version()
    dest_path = os.path.join(out_path,version)
    utils.MakeDirs(dest_path)
    need_renew_database = utils.NeedRenewDatabase(dest_path,new_database_version)
    sys_path_list = sys.path
    max_pool_count = 5
    for i,path in enumerate(sys_path_list):
        sys_path_list[i] = os.path.abspath(path)
    pool = multiprocessing.Pool(processes=min(max_pool_count,len(sys_path_list)))
    future_list = []
    for path in sys_path_list:
        logger.info('start parse path %s data',path)
        pool.apply_async(scan_sys_path,(path,dest_path,need_renew_database))
    pool.close()
    pool.join()
    process_sys_modules(dest_path)
    if need_renew_database:
        utils.SaveDatabaseVersion(dest_path,new_database_version)
    update_intelliense_database(dest_path)
    SaveLastUpdateTime(dest_path)
    
def get_unfinished_modules(outpath):
    unfinished_file_name = "unfinish.txt"
    unfinished_file_path = os.path.join(outpath,unfinished_file_name)
    if not os.path.exists(unfinished_file_path):
        return []
    module_paths = []
    try:
        with open(unfinished_file_path) as f:
            module_paths = f.read().split()
        os.remove(unfinished_file_path)
    except:
        pass
    return module_paths
     
def scan_sys_path(src_path,dest_path,need_renew_database):

    def is_path_ignored(path):
        for ignore_path in ignore_path_list:
            if path.startswith(ignore_path):
                return True
        return False
    ignore_path_list = []
    unfinished_module_paths = get_unfinished_modules(os.path.dirname(dest_path))
    for root,path,files in os.walk(src_path):
        if is_path_ignored(root):
            continue
        if root != src_path and is_test_dir(root):
            ignore_path_list.append(root)
          ##  print ('path',root,'is a test dir')
            continue
        elif root != src_path and not fileparser.is_package_dir(root):
            ignore_path_list.append(root)
           ### print ('path',root,'is not a package dir')
            continue
        for afile in files:
            fullpath = os.path.join(root,afile)
            ext = os.path.splitext(fullpath)[1].lower()
            if not ext in ['.py','.pyw']:
                continue
            is_file_unfinished =  fullpath in unfinished_module_paths
            file_need_renew_database = need_renew_database or is_file_unfinished
            file_parser = fileparser.FiledumpParser(fullpath,dest_path,force_update=file_need_renew_database)
            file_parser.Dump()
           
def is_test_dir(dir_path):
    dir_name = os.path.basename(dir_path)
    if dir_name.lower() == "test" or dir_name.lower() == "tests":
        return True
    else:
        return False


def process_sys_modules(dest_path):
    for name in list(sys.modules.keys()):
        module_members_file = os.path.join(dest_path,name+ config.MEMBERS_FILE_EXTENSION)
        if os.path.exists(module_members_file):
            ###print 'sys module',name,'has been already analyzed'
            continue
        if not hasattr(sys.modules[name],'__file__'):
            continue
        fullpath = sys.modules[name].__file__.rstrip("c")
        if not fullpath.endswith(".py"):
            continue

        file_parser = fileparser.FiledumpParser(fullpath,dest_path)
        file_parser.Dump()
        

def generate_intelligent_data(out_path,new_database_version):
    version = get_python_version()
    dest_path = os.path.join(out_path,version)
    utils.MakeDirs(dest_path)
    need_renew_database = NeedRenewDatabase(dest_path,new_database_version)
    sys_path_list = sys.path
    for i,path in enumerate(sys_path_list):
        sys_path_list[i] = os.path.abspath(path)
    for path in sys_path_list:
        logger.info('start parse path %s data',path)
        scan_sys_path(path,dest_path,need_renew_database)
    process_sys_modules(dest_path)
    if need_renew_database:
        SaveDatabaseVersion(dest_path,new_database_version)
        
def update_intelliense_database(dest_path):
    
    def delete_file(filepath):
        try:
            os.remove(filepath)
        except:
            pass
    delete_file_count = 0
    for filepath in glob.glob(os.path.join(dest_path,"*" + config.MEMBERS_FILE_EXTENSION)):
        filename = os.path.basename(filepath)
        module_name = '.'.join(filename.split(".")[0:-1])
        try:
            spec = importlib.util.find_spec(module_name)
            logger.debug('module %s file %s spec is %s',module_name,filepath,spec)
        except ImportError as msg:
            if msg.name is not None and module_name.find(msg.name) != -1:
                logger.info("module %s not found,delete intelliense file %s",module_name,filepath)
                delete_file(filepath)
                delete_file(os.path.join(dest_path,module_name + config.MEMBERLIST_FILE_EXTENSION))
                delete_file_count += 1
            else:
                logger.info("find module %s error:%s",module_name,msg)
            continue
        except Exception as e:
            continue
        if spec is None:
            logger.info("module %s not found,delete intelliense file %s",module_name,filepath)
            delete_file(filepath)
            delete_file(os.path.join(dest_path,module_name + config.MEMBERLIST_FILE_EXTENSION))
            delete_file_count += 1
            continue
    logger.info('delete total %d intelliense files',delete_file_count)
    
if __name__ == "__main__":
    logger.propagate = False
    logFormatter = logging.Formatter("%(levelname)s: %(message)s")
    start_time = time.time()
    out_path = sys.argv[1]
    new_database_version = sys.argv[2]
    debug = int(sys.argv[3])
    utils.MakeDirs(out_path)
    file_handler = logging.FileHandler(
        os.path.join(out_path, "backend.log"), encoding="UTF-8", mode="w"
    )
    file_handler.setFormatter(logFormatter)
    logger.addHandler(file_handler)
    if debug:
        file_handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
    fault_out = open(os.path.join(out_path, "backend_faults.log"), mode="w")
    faulthandler.enable(fault_out)
    
    
    #generate_intelligent_data(out_path,new_database_version)
    generate_intelligent_data_by_pool(out_path,new_database_version)
    end_time = time.time()
    elapse = end_time - start_time
    logger.info('elapse time:%.2fs',elapse)
    logger.info('end............')