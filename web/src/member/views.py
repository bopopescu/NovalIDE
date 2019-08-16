# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from member.models import Member,MemberData,DownloadData,PyPackage
from django.conf import settings
import logging
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
import ConfigParser
from util.utils import *
import sys

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
        'user_name':user_name,
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
            
@require_http_methods(['GET'])
def new_app_download(request):
    ip_addr = request.META['REMOTE_ADDR']
    language = request.REQUEST.get('lang')
    new_version  = request.REQUEST.get('new_version',None)
    os_name = request.REQUEST.get('os_name')
    member_id = request.REQUEST.get('member_id',None)
    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
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
            msg = "版本文件不存在"
        else:
            msg = "version file is not exist"
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
    response = StreamingHttpResponse(file_iterator(version_file_path))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Length'] = os.path.getsize(version_file_path)
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(version_file_name)
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
def get_packages(request):
    names = []
    name = request.REQUEST.get('name',None)
    for pkg in PyPackage.objects():
        if name is None or pkg.name.lower().find(name.lower()) != -1:
            names.append(pkg.name)
    return json_response(names=names)
   
@require_http_methods(['GET'])
def get_package_info(request):
    names = []
    name = request.REQUEST.get('name')
    pkg = PyPackage.objects(name=name).first()
    ret_data = dict(pkg.to_mongo())
    return json_response(**ret_data)
