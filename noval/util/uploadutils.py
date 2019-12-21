# -*- coding: utf-8 -*-
from noval import GetApp,_
from tkinter import messagebox
import os
import noval.ui_base as ui_base
from dummy.userdb import UserDataDb
import requests
import noval.util.appdirs as appdirs
import noval.python.parser.utils as dirutils
import threading

class UploadProgressDialog(ui_base.GenericProgressDialog):
    '''
        上传进度显示对话框
    '''
    
    def __init__(self,parent,file_sie,file_name):
        welcome_msg = _("Please wait a minute for Uploading")
        ui_base.GenericProgressDialog.__init__(self,parent,_("Uploading %s") % file_name,info=welcome_msg,maximum = file_sie)

class FileUploader(object):
    '''
        上传文件公用类
    '''
    def __init__(self, filename, chunksize=1 << 13,call_back=None):
        self._file_name = filename
        self.chunksize = chunksize
        self._file_size = os.path.getsize(filename)
        self.readsofar = 0
        self._call_back = call_back
        #是否正在上传文件,用来表示是否显示进度条对话框
        self._is_uploading = False
        #进度条对话框
        self.progress_dlg = None
    
    def StartUpload(self):
        
        def UploadCallBack():
            self.DestoryDialog()
            if self._call_back is not None and not self.IsCanceled():
                GetApp().MainFrame.after(300,self._call_back,download_file_path)

        self._is_uploading = True
        #1秒后才显示进度条对话框,如果在此时间内下载文件已经完成,则不会显示下载进度条对话框
        GetApp().MainFrame.after(1000,self.ShowUploadProgressDialog)
            
    def DestoryDialog(self):
        '''
            上传完成后关闭进度条
        '''
        if self.progress_dlg is None:
            return
        self.progress_dlg.keep_going = False
        self.progress_dlg.destroy()
        
    def __iter__(self):
        try:
            with open(self._file_name, 'rb') as file:
                while True:
                    data = file.read(self.chunksize)
                    if not data or self.IsCanceled():
                        break
                    self.readsofar += len(data)
                    if self.progress_dlg is not None:
                        self.progress_dlg.SetValue(self.readsofar)
                    yield data
        except Exception as e:
            messagebox.showerror("",_("Upload fail:%s") % e)
            #错误回调函数
            if err_callback:
                err_callback()
            
        assert(self.readsofar == self._file_size)
        self._is_uploading = False
        #下载完成调用回调函数
        self._call_back()

    def __len__(self):
        return self._file_size
        
        
    def IsCanceled(self):
        if self.progress_dlg is None:
            return False
        return self.progress_dlg.is_cancel
        
    def ShowUploadProgressDialog(self):
        #如果上传操作已经完成,则不会显示上传进度条对话框
        if self._is_uploading:
            upload_progress_dlg = UploadProgressDialog(GetApp().GetTopWindow(),int(self._file_size),self._file_name)
            self.progress_dlg = upload_progress_dlg
            upload_progress_dlg.ShowModal()

    def UploadFile(self,callback,err_callback=None):
        t = threading.Thread(target=self.DownloadFileContent,args=(download_file_path,self._req,callback,err_callback))
        t.start()
        
    def DownloadFileContent(self,download_file_path,req,callback,err_callback=None):
        f = open(download_file_path, "wb")
        try:
            ammount = 0
            #分块下载
            for chunk in req.iter_content(chunk_size=512):
                if chunk:
                    if self.IsCanceled():
                        break
                    f.write(chunk)
                    ammount += len(chunk)
                    if self.progress_dlg is not None:
                        self.progress_dlg.SetValue(ammount)
        except Exception as e:
            messagebox.showerror("",_("Download fail:%s") % e)
            #错误回调函数
            if err_callback:
                err_callback()
            f.close()
            return
        f.close()
        self._is_dowloading = False
        #下载完成调用回调函数
        callback()
        
class IterableToFileAdapter(object):
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.length = len(iterable)

    def read(self, size=-1): # TBD: add buffer for `len(data) > size` case
        return next(self.iterator, b'')

    def __len__(self):
        return self.length
        

def upload_file_progress(url,filename,**payload):
    '''
        下载文件公用函数
        download_url:下载地址
        call_back:下载完成后回调函数
        payload:url参数
    '''
    it = FileUploader(filename, 100)
    r = requests.post(url, data=IterableToFileAdapter(it))
