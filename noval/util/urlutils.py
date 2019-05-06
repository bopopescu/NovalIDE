import requests
import noval.util.utils as utils

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
        utils.get_logger().error('open %s error:%s' ,addr,e)
    return None
    
def open_url(url_path):
    oass