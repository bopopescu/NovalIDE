import os
import sys
import time
import sched
import threading
import noval.parser.utils as parserutils
import noval.util.strutils as strutils
import noval.parser.fileparser as fileparser
import datetime
import cPickle
import noval.util.sysutils as sysutilslib
from noval.util.logger import app_debugLogger
import noval.tool.interpreter.manager as interpretermanager
from noval.tool import Singleton

schedule = sched.scheduler ( time.time, time.sleep )

class ProjectWatcher(threading.Thread):
    
    INTERVAL_TIME_SECOND = 3
    UPDATE_FILE = 'update.time'
    
    def __init__(self,project_service):
        threading.Thread.__init__(self)
        self._view = project_service.GetView()
        self._is_parsing = False
        self._stop = False
        self.schd = schedule.enter(self.INTERVAL_TIME_SECOND,0,self.watch_project,())
        self.last_update_time = -1

    def run(self):
        schedule.run()
        
    def watch_project(self):
        doc = self._view.GetDocument()
        if doc != None:
            self.parse_project(doc)
        if not self._stop:
            self.schd = schedule.enter(self.INTERVAL_TIME_SECOND,0,self.watch_project,())
            
    def get_last_update(self,intellisence_data_path):
        update_file_path = os.path.join(intellisence_data_path,self.UPDATE_FILE)
        if not os.path.exists(update_file_path):
            return 0
        else:
            return self.load_last_update(intellisence_data_path)

    def load_last_update(self,intellisence_data_path):
        time_stamp = 0
        update_file_path = os.path.join(intellisence_data_path,self.UPDATE_FILE)
        with open(update_file_path) as f:
            date_list = cPickle.load(f)
            time_stamp = date_list[0]
        return time_stamp
                
    def update_last_time(self,intellisence_data_path):
        update_datetime = datetime.datetime.now()
        time_stamp = time.mktime(update_datetime.timetuple())
        tm = [time_stamp]
        update_file_path = os.path.join(intellisence_data_path,self.UPDATE_FILE)
        with open(update_file_path,"w") as f:
            cPickle.dump(tm,f)

    def parse_project(self,doc):
        assert (doc != None)
        project = doc.GetModel()
        interpreter_path = project.Interpreter.Path
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByPath(interpreter_path)
        if interpreter is None:
            return
        project_location = os.path.dirname(doc.GetFilename())
        path_list = [project_location]
        metadata_path = os.path.join(project_location,".metadata")
        intellisence_data_path = os.path.join(metadata_path,str(interpreter.Id))
        self.last_update_time = self.get_last_update(intellisence_data_path)
        if not os.path.exists(intellisence_data_path):
            parserutils.MakeDirs(intellisence_data_path)
            #hidden intellisence data path on windows and linux
            if sysutilslib.isWindows():
                import win32api
                import win32con
                win32api.SetFileAttributes(metadata_path, win32con.FILE_ATTRIBUTE_HIDDEN)
        
        update_file_count = 0
        for filepath in project.filePaths:
            if self._stop:
                break
            file_dir = os.path.dirname(filepath)
            is_package_dir = fileparser.is_package_dir(file_dir)
            if is_package_dir or parserutils.PathsContainPath(path_list,file_dir):
                ext = strutils.GetFileExt(filepath)
                if ext in ['py','pyw']:
                    mk_time = os.path.getmtime(filepath)
                    relative_module_name,is_package = parserutils.get_relative_name(filepath,path_list)
                    if mk_time > self.last_update_time or not os.path.exists(os.path.join(intellisence_data_path,relative_module_name + ".$members")):
                        app_debugLogger.debug('update file %s ,relative module name is %s',\
                                    filepath,parserutils.get_relative_name(filepath,path_list)[0])
                        fileparser.dump(filepath,relative_module_name,intellisence_data_path,is_package)
                        update_file_count += 1
            else:
                app_debugLogger.debug('%s is not valid parse dir',file_dir)
        app_debugLogger.debug('total update %d files',update_file_count)
        if update_file_count > 0:
            self.update_last_time(intellisence_data_path)
                
    def stop(self):
        self._stop = True
        self.join()
        #schedule.cancel(self.schd)

class ProjectDataLoader:
    __metaclass__ = Singleton.SingletonNew
    def __init__(self):
        self.module_dicts = {}
        self.import_list = []
        
    def LoadMetadataPath(self,meta_data_path):
        self.module_dicts.clear()
        name_sets = set()
        for filepath in glob.glob(os.path.join(meta_data_path,"*.$members")):
            filename = os.path.basename(filepath)
            module_name = '.'.join(filename.split(".")[0:-1])
            name_sets.add(module_name)
        for name in name_sets:
            d = dict(members=os.path.join(data_path,name +".$members"),\
                     member_list=os.path.join(data_path,name +".$memberlist"))
            self.module_dicts[name] = d
            
    def LoadProjectMetaData(self,project):
        interpreter_path = project.Interpreter.Path
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByPath(interpreter_path)
        if interpreter is None:
            return
        project_location = project.homeDir
        metadata_path = os.path.join(project_location,".metadata")
        intellisence_data_path = os.path.join(metadata_path,str(interpreter.Id))
        self.LoadMetadataPath(intellisence_data_path)

    def LoadImportList(self):
        for key in self.module_dicts.keys():
            if key.find(".") == -1:
                self.import_list.append(key)
        #self.import_list.sort(CmpMember)
        
    @property
    def ImportList(self):
        return self.import_list
    