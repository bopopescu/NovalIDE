# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from member.models import *
from django.conf import settings
import logging
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
import ConfigParser
from util.utils import *
from util.errors import *
import sys
import pymongo

logger = logging.getLogger('logsite')

reload(sys)
sys.setdefaultencoding('utf-8')

# Create your views here.

@csrf_exempt
@require_http_methods(['POST'])
def register_member(request):
    sn = request.REQUEST.get('sn')
    os_bit  = request.REQUEST.get('os_bit')
    os_name  = request.REQUEST.get('os_name')
    user_name =  request.REQUEST.get('user_name')
    kwargs = {
        'sn':sn,
        'os_bit':os_bit,
        'os_name':os_name,
        'user_name':user_name,
        'app_version':request.REQUEST.get('app_version')
    }
    member = Member(**kwargs).save()
    return json_response(member_id = member.id)

@require_http_methods(['GET'])
def get_member(request):
    sn = request.REQUEST.get('sn')
    member = Member.objects(sn=sn).first()
    if member is None:
        return json_response(code=-1,msg='user is not exist')
    return json_response(member_id = member.id)

@csrf_exempt
@require_http_methods(['POST'])
def share_member_data(request):
    member_id = request.REQUEST.get('member_id')
    if member_id in ['5aef0fb461f7b14f0ca52310','5af1334861f7b159b6df646a','5af137aa61f7b159b6df646c']:
        return json_response()
    start_time = request.REQUEST.get('start_time')
    end_time = request.REQUEST.get('end_time')
    app_version  = request.REQUEST.get('app_version')
    kwargs = {
        'user_id':member_id,
        'start_time':start_time,
        'end_time':end_time,
        'app_version':app_version
    }
    MemberData(**kwargs).save()
    return json_response()
    
@require_http_methods(['GET'])
def get_update_info(request):
    app_version  = request.REQUEST.get('app_version')
    language = request.REQUEST.get('lang')
    version_dir = os.path.dirname(settings.BASE_DIR)
    version_txt_file = os.path.join(version_dir,"version","version.txt")
    is_zh = True if language.strip().lower().find("cn") != -1 else False
    if not os.path.exists(version_txt_file):
        if is_zh:
            msg = u"无法获取版本号"
        else:
            msg = "could not get application version"
        return json_response(code=2,message=msg)
    with open(version_txt_file) as f:
        version = f.read().strip()
        if not CompareAppVersion(version,app_version):
            if is_zh:
                msg = u"当前已是最新版本"
            else:
                msg = "this is the lastest version"
            return json_response(code=0,message=msg)
        else:
            if is_zh:
                msg = u"有最新版本'%s'可用,你需要下载更新吗?" % version
            else:
                msg = "this lastest version '%s' is available,do you want to download and update it?" % version
            return json_response(code=1,message=msg,new_version=version)

def download_file(request,file_path):
    '''
        下载文件公用函数
    '''
    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
    
    response = StreamingHttpResponse(file_iterator(file_path))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Length'] = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_name)
    return response
                            
@require_http_methods(['GET'])
def download_app(request):
    '''
        下载软件
    '''
    ip_addr = request.META['REMOTE_ADDR']
    language = request.REQUEST.get('lang')
    new_version  = request.REQUEST.get('new_version',None)
    os_name = request.REQUEST.get('os_name')
    member_id = request.REQUEST.get('member_id',None)
    if new_version is not None:
        if os_name.lower().find('win32') != -1:
            version_file_name = "NovalIDE_Setup_%s.exe" % new_version
        else:
            version_file_name = "NovalIDE-%s.tar.gz" % new_version
    else:
        if os_name.lower().find('win32') != -1:
            version_file_name = "NovalIDE_Setup.exe"
        else:
            version_file_name = "NovalIDE.tar.gz"
    version_dir = os.path.dirname(settings.BASE_DIR)
    version_file_path = os.path.join(version_dir,"version",version_file_name)
    is_zh = True if language.strip().lower().find("cn") != -1 else False
    if not os.path.exists(version_file_path):
        if is_zh:
            msg = "程序文件不存在"
        else:
            msg = "application file is not exist"
        return json_response(code=1,message=msg)
        
    kwargs = {
        'os_name':os_name,
        'ip_addr':ip_addr
    }
    if new_version is not None:
        kwargs.update({'is_update':True,'app_version':new_version})
    if member_id is not None:
        kwargs.update({'user_id':member_id})
    DownloadData(**kwargs).save()
    response = download_file(request,version_file_path)
    return response
    
@require_http_methods(['GET'])
def download_plugin(request):
    '''
        下载插件
    '''
    ip_addr = request.META['REMOTE_ADDR']
    language = request.REQUEST.get('lang')
    app_version  = request.REQUEST.get('app_version',None)
    new_version  = request.REQUEST.get('new_version',None)
    os_name = request.REQUEST.get('os_name')
    member_id = request.REQUEST.get('member_id',None)
    plugin_id = request.REQUEST.get('plugin_id',None)
    plugin_pkg = PluginPackage.objects(id=plugin_id).first()
    egg_name = None
    if new_version is not None:
        for release in plugin_pkg.releases:
            if release['version'] == new_version:
                egg_name = release['filename']
    else:
        egg_name = plugin_pkg.path
        new_version = plugin_pkg.version
        
    if not egg_name:
        return json_response(code=PLUGIN_VERSION_NOT_FOUND,message=GetCodeMessage(PLUGIN_VERSION_NOT_FOUND).format(version=new_version,name=plugin_pkg.name))
    version_dir = os.path.dirname(settings.BASE_DIR)
    plugin_base_path = os.path.join(version_dir,"version")
    egg_file_path = os.path.join(plugin_base_path,plugin_pkg.name,egg_name)
    is_zh = True if language.strip().lower().find("cn") != -1 else False
    if not os.path.exists(egg_file_path):
        if is_zh:
            msg = "插件文件不存在"
        else:
            msg = "plugin file is not exist"
        logger.error("plugin %s file %s is not exist",plugin_id,egg_file_path)
        return json_response(code=PLUGIN_EGG_FILE_NOT_FOUND,message=msg)
    kwargs = {
        'os_name':os_name,
        'ip_addr':ip_addr,
        'plugin_id':plugin_id,
        'app_version':app_version,
        'plugin_version':new_version
    }
    if new_version is not None:
        kwargs.update({'is_update':True})
    if member_id is not None:
        kwargs.update({'member_id':member_id})
    try:
        PluginDownloadData(**kwargs).save()
        #更新插件下载次数
        down_amount = plugin_pkg.down_amount + 1
        plugin_pkg.update(**{'set__down_amount':down_amount})
    except pymongo.errors.DuplicateKeyError:
        pass
    response = download_file(request,egg_file_path)
    return response
    
@require_http_methods(['GET'])
def login(request):
    code = request.REQUEST.get('code')
    print code
    return json_response(auth_code=code)
    
@require_http_methods(['GET'])
def get_mail(request):
    is_load_private_key  = int(request.REQUEST.get('is_load_private_key',True))
    cfg = ConfigParser.ConfigParser()
    home_path = os.path.expanduser("~")
    mail_config_path = os.path.join(home_path,".mailcfg")
    cfg.read(mail_config_path)
    mail_provider = 'mail'
    sender = cfg.get(mail_provider,"sender")
    smtpserver = cfg.get(mail_provider,"smtp")
    user = cfg.get(mail_provider,"user")
    password = cfg.get(mail_provider,"passwd")
    port = cfg.get(mail_provider,"port")
    if is_load_private_key:
        with open(os.path.join(home_path,".ssh/id_rsa")) as f:
            private_key  = f.read()
        return json_response(sender = sender,user=user,password=password,smtpserver=smtpserver,port=port,private_key=private_key)
    else:
        return json_response(sender = sender,user=user,password=password,smtpserver=smtpserver,port=port)

@require_http_methods(['GET'])
def get_pypi_packages(request):
    names = []
    name = request.REQUEST.get('name',None)
    for pkg in PyPIPackage.objects():
        if name is None or pkg.lower_name.find(name.lower()) != -1:
            names.append(pkg.name)
    return json_response(names=names)
    

@require_http_methods(['GET'])
def get_pypi_package_count(request):
    return json_response(count=PyPIPackage.objects().count())
   
@require_http_methods(['GET'])
def get_package_info(request):
    names = []
    name = request.REQUEST.get('name')
    pkg = PyPIPackage.objects(lower_name=name.lower()).first()
    if not pkg:
        ret_data = {}
    else:
        ret_data = dict(pkg.to_mongo())
    return json_response(**ret_data)
    
@require_http_methods(['GET'])
def get_plugin_info(request):
    names = []
    name = request.REQUEST.get('name')
    plugin_pkg = PluginPackage.objects(lower_name=name.lower()).first()
    if not plugin_pkg:
        ret_data = {}
    else:
        #更新插件查看次数
        view_amount = plugin_pkg.view_amount + 1
        plugin_pkg.update(**{'set__view_amount':view_amount})
        ret_data = dict(plugin_pkg.to_mongo())
    return json_response(**ret_data)

@require_http_methods(['GET'])
def get_plugin_packages(request):
    names = []
    name = request.REQUEST.get('name',None)
    for pkg in PluginPackage.objects():
        if name is None or pkg.lower_name.find(name.lower()) != -1:
            names.append(pkg.name)
    return json_response(names=names)
    
@require_http_methods(['POST'])
def publish_plugin(request):
    '''
       发布并上传插件
    '''
    def upload_file(file_path):
        '''
           上传文件到服务器本地路径
        '''
        #获取上传文件流
        egg_file = request.FILES.get("file", None)
        with open(file_path, 'wb+') as f:
            #分块写入文件
            for chunk in egg_file.chunks():
                f.write(chunk)        
    names = []
    name = request.REQUEST.get('name')
    lower_name = name.lower()
    plugin_pkgs = PluginPackage.objects(lower_name=lower_name)
    #插件版本文件存在时是否强制替换
    force_update = int(request.REQUEST.get('force_update'))
    version = request.REQUEST.get('version')
    author = request.REQUEST.get('author')
    author_mail = request.REQUEST.get('author_mail')
    homepage = request.REQUEST.get('homepage')
    summary = request.REQUEST.get('summary')
    egg_name =  request.REQUEST.get('egg_name')
    member_id = request.REQUEST.get('member_id')
    version_dir = os.path.dirname(settings.BASE_DIR)
    free = bool(request.REQUEST.get('free'))
    price = request.REQUEST.get('price')
    app_version = request.REQUEST.get('app_version')
    plugin_base_path = os.path.join(version_dir,"version")
    egg_path = os.path.join(plugin_base_path,name) 
    if not os.path.exists(egg_path):
        os.makedirs(egg_path)
    egg_file_path = os.path.join(egg_path,egg_name)
    if plugin_pkgs.count() == 0:
        #新插件先上传文件,成功后再写入插件信息
        upload_file(egg_file_path)
        #插件新插件
        data = {
            'name':name,
            'lower_name':name.lower(),
            'version':version,
            'author':author,
            'author_mail':author_mail,
            'homepage':homepage,
            'releases':[{'version':version,'filename':egg_name}],
            'summary':summary,
            #存储egg名称即可
            'path':egg_name,
            'member_id':member_id,
            'free':free,
            'price':price,
            'app_version':app_version
        }
        logger.info("insert plugin name %s success",name)
        #保存插件信息
        PluginPackage(**data).save()
    else:
        #更新已有插件信息
        assert(plugin_pkgs.count() == 1)
        plugin_pkg = plugin_pkgs.first()
        #是否是新版本,是新版本则添加到历史版本列表当中
        if version != plugin_pkg.version:
            plugin_pkg.version = version
            plugin_pkg.releases.append({'version':version,'filename':egg_name})
        #替换用户是否强制替换版本文件
        elif not force_update:
            return json_response(code=PLUGIN_EGG_FILE_EXISTS)
        #上传插件文件
        upload_file(egg_file_path)
        plugin_pkg.author = author
        plugin_pkg.author_mail = author_mail
        plugin_pkg.homepage = homepage
        plugin_pkg.summary = summary
        plugin_pkg.free = free
        plugin_pkg.app_version = app_version
        plugin_pkg.price = price
        plugin_pkg.updated_at = datetime.datetime.utcnow()
        #更新插件信息
        plugin_pkg.save()
    return json_response()
        
@require_http_methods(['GET'])
def check_force_update(request):
    app_version = request.REQUEST.get('app_version')
    ret_data = {'force_update':False}
    return json_response(**ret_data)
    
@require_http_methods(['GET'])
def get_member_payment(request):
    '''
        查询用户是否付款
    '''
    member_id = request.REQUEST.get('member_id',None)
    plugin_id = request.REQUEST.get('plugin_id',None)
    payment = Payments.objects(member_id=member_id,plugin_id=plugin_id).first()
    plugin_pkg = PluginPackage.objects(id=plugin_id).first()
    if not plugin_pkg:
        logger.error("plugin id %s is not exist",plugin_id)
    data = {}
    if not payment:
        data['payed'] = False
        price = plugin_pkg.price
        if price:
            data['price'] = price
        else:
            logger.error('plugin id %s set charged,but no set price',plugin_id)
    else:
        data['payed'] = True
    return json_response(**data)

@require_http_methods(['POST'])
def payment(request):
    '''
        存储用户付款记录
    '''
    plugin_version = request.REQUEST.get('plugin_version',None)
    member_id = request.REQUEST.get('member_id')
    plugin_id = request.REQUEST.get('plugin_id')
    Payments(member_id=member_id,plugin_id=plugin_id,plugin_version=plugin_version).Save()
    return json_response()
    
