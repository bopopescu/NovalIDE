# -*- coding: utf-8 -*-
import sys
sys.path.append("/opt/web/src/member")
sys.path.append("/opt/web/src/web")
sys.path.append("/opt/web/src")
import settings
import models
from mongoengine import *
from datetime import datetime
import requests
import copy
try:
    #python2用法
    from HTMLParser import HTMLParser
except ImportError:
    #python3用法
    from html.parser import HTMLParser
import logging
import logging.config
import json
import argparse

# register mongodb connections.
for k, v in settings.MONGODBS.items():
    conn_params = copy.deepcopy(v)
    name = conn_params.pop('name')
    register_connection(k, name, **conn_params)

#连接数据库
#connect('pypi') # 连接本地pypi数据库
# 如需验证和指定主机名
# connect('blog', host='192.168.3.1', username='root', password='1234')

UPDATE_COUNT = 0
#从配置文件中加载日志对象
logging.config.fileConfig("/opt/web/pypi/logger.conf")
#获取root日志
logger = logging.getLogger()

#必须先初始化日志配置,否则根日志将无法打印出来
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
    


ONLY_NEW = False
ONLY_UPDATE = False
    
def check_package_updated(name,version):
    if ONLY_NEW:
        return False
    package = models.PyPIPackage.objects(name=name).first()
    if package.version != version:
        return True
    return False

def generate_package_info(name):
    global UPDATE_COUNT
    is_exist = models.PyPIPackage.objects(name=name).first()
    if not ONLY_NEW or not is_exist:
        #从pypi从获取包信息
        api_addr = "https://pypi.org//pypi/%s/json" % name
        data = RequestData(api_addr,to_json=True)
        if data is None:
            #logger.error("could not get pypi packge %s info",name)
            return
     #   print json.dumps(data,indent=4)
        #先获取版本号列表,不属于包信息
        releases = data['releases'].keys()
        releases.sort()
        #包信息
        data = data['info']
        #包最新版本号
        version = data['version']
    else:
        logger.debug("package name %s has already exist....",name)
        return
    #是否是更新数据库里面的包信息还是新建包信息
    is_updated = False
    #包存在
    if is_exist:
        #检查包版本号是否有更新
        if not check_package_updated(name,version):
            logger.debug("package name %s has already exist,and no update",name)
            return
        else:
            is_updated = True

   # print json.dumps(data,indent=4)
    author = data['author']
    if author is None:
        author = ''
    author = author[0:150]
    author_mail = data['author_email']
    if author_mail is None:
        author_mail = ''
    author_mail = author_mail[0:300]
    package_url = data['package_url']
    project_urls = data['project_urls']
    if project_urls is None:
        homepage = data['home_page']
    else:
        homepage = project_urls.get('Homepage','')
    name = data['name']
    summary = data['summary']
    docs_url = data.get("docs_url", '')
    bugtrack_url = data.get("bugtrack_url", '')
    requires_dist = data.get("requires_dist", [])
    data = {
        'name':name,
        'lower_name':name.lower(),
        'version':version,
        'author':author,
        'author_mail':author_mail,
        'homepage':homepage,
        'releases':releases,
        'package_url':package_url,
        'summary':summary,
        'bugtrack_url':bugtrack_url,
        'docs_url':docs_url,
        'requires_dist':requires_dist
    }
    #这是新包
    if not is_exist and not ONLY_UPDATE:
        models.PyPIPackage(**data).save()
        logger.info("insert package %s success",name)
    #更新已有包
    elif is_exist and is_updated and not ONLY_NEW:
        pkgs = models.PyPIPackage.objects(name=name)
        #包名称必须是唯一的
        assert(pkgs.count() == 1)
        pkg = pkgs.first()
        pkg.version = version
        pkg.author = author
        pkg.author_mail = author_mail
        pkg.homepage = homepage
        pkg.releases = releases
        pkg.package_url = package_url
        pkg.docs_url = docs_url
        pkg.bugtrack_url = bugtrack_url
        pkg.requires_dist = requires_dist
        pkg.summary = summary
        pkg.updated_at = datetime.utcnow()
        pkg.save()
        logger.info("update package %s success",name)
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
    parser = argparse.ArgumentParser()
    #只更新包不插入新包更新频率少一点
    parser.add_argument("--update", action='store_true', dest="only_update",help='',default=False)
    #只插入新包不更新包,这个频率多一点每天都做
    parser.add_argument("--new", action='store_true', dest="only_new",help='',default=False)
    args = parser.parse_args()
    ONLY_UPDATE = args.only_update
    ONLY_NEW = args.only_new
    scan_pypi()
    logger.info("total update %d packages",UPDATE_COUNT)
