# -*- coding: utf-8 -*-
import requests

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
