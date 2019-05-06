from watchdog.observers import Observer  
from watchdog.events import FileSystemEventHandler
import os
from noval.util.singleton import *
import noval.util.utils as utils

@Singleton
class FileAlarmWatcher():
    path_watchers = {}
    def AddFileDoc(self,doc):
        file_path = os.path.dirname(doc.GetFilename())
        if file_path not in self.path_watchers:
            path_watcher = PathWatcher(file_path)
            self.path_watchers[file_path] = path_watcher
        else:
            path_watcher = self.path_watchers[file_path]
        path_watcher.AddFile(doc)

    def RemoveFileDoc(self,doc):
        file_name_path = doc.GetFilename()
        file_path = os.path.dirname(file_name_path)
        assert file_path in self.path_watchers
        path_watcher = self.path_watchers[file_path]
        path_watcher.RemoveFile(doc)

        if 0 == path_watcher.GetFileCount():
            path_watcher.Stop()
            self.path_watchers.pop(file_path)

    def RemoveFile(self,file_name_path):
        file_path = os.path.dirname(file_name_path)
        assert file_path in self.path_watchers
        path_watcher = self.path_watchers[file_path]
        path_watcher.RemoveFilePath(file_name_path)
        if 0 == path_watcher.GetFileCount():
            path_watcher.Stop()
            self.path_watchers.pop(file_path)

    def StopWatchFile(self,doc):
        file_name_path = doc.GetFilename()
        file_path = os.path.dirname(file_name_path)
        if file_path not in self.path_watchers:
            return
        path_watcher = self.path_watchers[file_path]
        path_watcher.Stop()

    def StartWatchFile(self,doc):
        file_name_path = doc.GetFilename()
        file_path = os.path.dirname(file_name_path)
        if file_path not in self.path_watchers:
            self.AddFileDoc(doc)
        else:
            path_watcher = self.path_watchers[file_path]
            path_watcher.AddFile(doc)
            path_watcher.Start()

    def IsFileWatched(self,filePath):
        dir_path = os.path.dirname(filePath)
        if dir_path in self.path_watchers:
            path_watcher = self.path_watchers[dir_path]
            return path_watcher.IsFileWatched(filePath)
        return False
        
    def IsDocFileWatched(self,doc):
        return self.IsFileWatched(doc.GetFilename())

class PathWatcher(object):

    def __init__(self,path):
        self.file_docs = {}
        self._path = path
        self.event_handler = FileEventHandler(self)
        self._is_watched = False
        self.Start()

    def Stop(self):
        try:
            #TODO:the watchdog package bug,to fix
            self.observer.stop()
            self.observer.join(5)
        except Exception as e:
            utils.get_logger().error('stop file watcher error %s',e)
        self._is_watched = False

    def Start(self):
        if self._is_watched:
            self.Stop()
        self.observer = Observer()  
        self.observer.schedule(self.event_handler, path=self._path, recursive=False)
        self.observer.start()
        self._is_watched = True
        
    def AddFile(self,doc):
        file_name_path = doc.GetFilename()
        ##lower_file_path = file_path.lower()
        if file_name_path not in self.file_docs:
            self.file_docs[file_name_path] = doc

    def RemoveFile(self,doc):
        file_name_path = doc.GetFilename()
        assert file_name_path in self.file_docs
        self.file_docs.pop(file_name_path)

    def RemoveFilePath(self,file_name_path):
        assert file_name_path in self.file_docs
        self.file_docs.pop(file_name_path)

    def GetFileCount(self):
        return len(self.file_docs)

    @property
    def Path(self):
        return self._path

    def FileAlarm(self,file_path,event_alarm_type):

        if file_path in self.file_docs:
            file_doc = self.file_docs[file_path]
            file_doc.GetFirstView().Alarm(event_alarm_type)
            
    def IsFileWatched(self,filePath):
        if filePath in self.file_docs:
            return True
        return False
  
class FileEventHandler(FileSystemEventHandler):

    FILE_DELETED_EVENT = 1
    FILE_MOVED_EVENT = 2
    FILE_MODIFY_EVENT = 3

    def __init__(self,path_watcher):
        self._path_watcher = path_watcher
        
    def on_modified(self, event):
        self._path_watcher.FileAlarm(event.src_path,self.FILE_MODIFY_EVENT)
    def on_moved(self,event):
        if os.path.exists(event.src_path):
            return
        self._path_watcher.FileAlarm(event.src_path,self.FILE_MOVED_EVENT)
    def on_deleted(self,event):
        self._path_watcher.FileAlarm(event.src_path,self.FILE_DELETED_EVENT)
