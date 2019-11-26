# -*- coding: utf-8 -*-
import requests
from concurrent import futures
import atexit

#删除注册全局退出函数,否则会在程序退出时等待ThreadPoolExecutor异步线程执行完才退出,导致程序卡死
try:
    atexit.unregister(futures.thread._python_exit)
except:
    pass

def RequestData(addr,arg={},method='get',timeout = None,to_json=True):
    '''
    '''
    params = {}
    try:
        if timeout is not None:
            params['timeout'] = timeout
        req = None
        if method == 'get':
            params['params'] = arg
            req = requests.get(addr,**params)
        elif method == 'post':
            req = requests.post(addr,data = arg,**params)
        if not to_json:
            return req.text
        return req.json()
    except Exception as e:
        print('open %s error:%s'%(addr,e))
    return None
    
def upload_file(addr,file,arg={},timeout = None):
    '''
        上传文件
        addr:上传url地址
        file:上传本地文件路径
        arg:url参数
    '''
    params = {}
    files = {
      "file" : open(file, "rb")
    }
    try:
        req = requests.post(addr,data = arg,files=files,**params)
    except:
        print ('upload file %s error'%file)
        return None
    return req.json()

def fetch_url_future(addr,arg={},method='get',timeout=None,callback=None,error_callback=None):
    '''
        异步请求获取url数据
        callback:请求正确后回调函数
        error_callback:请求失败后回调函数
    '''
    def load_url():
        data = RequestData(addr,arg,method,timeout)
        if data:
            #去掉非数据字段
            data.pop('message')
            data.pop('code')
            callback(data)
        else:
            #如果error_callback为None,则使用callback
            if not error_callback:
                callback(None)
            else:
                error_callback(None)
    #异步请求
    executor = futures.ThreadPoolExecutor(max_workers=1)
    return executor.submit(load_url)
