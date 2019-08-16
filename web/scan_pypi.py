# -*- coding: utf-8 -*-
from mongoengine import *
from datetime import datetime
import requests
try:
    #python2用法
    from HTMLParser import HTMLParser
except ImportError:
    #python3用法
    from html.parser import HTMLParser
import logging
import sys
# 连接数据库
connect('pypi') # 连接本地pypi数据库
# 如需验证和指定主机名
# connect('blog', host='192.168.3.1', username='root', password='1234')

UPDATE_COUNT = 0
#必须先初始化日志配置,否则根日志将无法打印出来
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
# 定义分类文档
class PyPackage(Document):
    name = StringField(max_length=100, required=True)
    author = StringField(max_length=500, required=True,default='')
    author_mail = StringField(max_length=200, required=True,default='')
    homepage = StringField(max_length=400)
    version = StringField(max_length=100, required=True)
    releases = ListField()
    pypi_url = StringField(max_length=400, required=True)
    summary = StringField(required=True,default='')
    updated_at = DateTimeField(requred=True,default=datetime.utcnow)

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
        logger.error('open %s error:%s' ,addr,e)
    return None

def generate_package_info(name):
    global UPDATE_COUNT
    is_exist = PyPackage.objects(name=name).first()
    if is_exist:
        logger.info("package name %s has already exist",name)
        return
    api_addr = "https://pypi.org//pypi/%s/json" % name
    data = RequestData(api_addr,to_json=True)
    if data is None:
        logger.error("could not get pypi packge %s info",name)
        return
  #  print json.dumps(data,indent=4)
    releases = data['releases'].keys()
    releases.sort()
    data = data['info']

   # print json.dumps(data,indent=4)
    author = data['author']
    if author is None:
        author = ''
    author_mail = data['author_email']
    pypi_url = data['package_url']
    project_urls = data['project_urls']
    if project_urls is None:
        homepage = data['home_page']
    else:
        homepage = project_urls.get('Homepage','')
    name = data['name']
    summary = data['summary']
    version = data['version']
    save_data = {
        'name':name,
        'version':version,
        'author':author[0:400],
        'author_mail':author_mail,
        'homepage':homepage,
        'releases':releases,
        'pypi_url':pypi_url,
        'summary':summary
    }
    logger.info("insert package name %s success",name)
    PyPackage(**save_data).save()
    UPDATE_COUNT += 1
    

class PyPiHtmlParser(HTMLParser):  
    a_text = False  
      
    def handle_starttag(self,tag,attr):  
        if tag == 'a':  
            self.a_text = True  
              
    def handle_endtag(self,tag):  
        if tag == 'a':  
            self.a_text = False  
              
    def handle_data(self,data):  
        if self.a_text:  
            api_addr = "https://pypi.org//pypi/%s/json" % data
            generate_package_info(data)
            
def scan_pypi():
    pip_source = "https://pypi.org/simple"
    contents = RequestData(pip_source,to_json=False)
    html_parser = PyPiHtmlParser()  
    html_parser.feed(contents)  
    html_parser.close()  

if __name__ == "__main__":
    scan_pypi()
    logger.info("total update %d packages",UPDATE_COUNT)