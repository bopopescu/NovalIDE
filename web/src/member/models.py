# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from django.db import models
import datetime

# Create your models here.
from mongoengine import Document,StringField,EmailField,ObjectIdField,DateTimeField,BooleanField,ListField,IntField,FloatField

class Member(Document):
    user_name = StringField(max_length=100)
    password = StringField(max_length=32)
    password_salt = StringField(max_length=8)
    email = EmailField(max_length=100)
    phone = StringField(max_length=11)
    sn = StringField(max_length=100)
    os_bit  = StringField(max_length=50)
    os_name = StringField(max_length=200)
    app_version = StringField(max_length=30)
    created_at = DateTimeField(requred=True,default=datetime.datetime.utcnow)
    
    meta = {
        'db_alias':'members'
    }


class MemberData(Document):
    user_id = ObjectIdField(required=True)
    start_time = DateTimeField()
    end_time = DateTimeField()
    app_version = StringField(max_length=20)
    
    created_at = DateTimeField(requred=True,default=datetime.datetime.utcnow)
    meta = {
        'db_alias':'members'
    }

class DownloadData(Document):
    user_id = ObjectIdField()
    app_version = StringField(max_length=100)
    is_update = BooleanField(default=False)
    os_name = StringField(max_length=20)
    ip_addr = StringField()
    
    meta = {
        'db_alias':'members',
        #允许子类继承,必须设置该字段
        'allow_inheritance':True,
    }
    
    download_at = DateTimeField(requred=True,default=datetime.datetime.utcnow)
    
class PluginDownloadData(DownloadData):
    '''
        插件下载数据
    '''
    #member_id和基类的user_id意思一样,但是由于user_id作为唯一建必须保证不能为空,所以不能用user_id
    member_id = ObjectIdField()
    plugin_id = ObjectIdField(required=True,unique_with=('member_id','plugin_version'))
    plugin_version = StringField(required=True,max_length=100)
    meta = {
        'db_alias':'plugins',
        'indexes': ['member_id','plugin_id']
    }

# 定义分类文档
class PyPackage(Document):
    #包名
    name = StringField(max_length=100, required=True,unique=True)
    #包的小写名称
    #lower_name不能设置唯一建,有的包名称不一样但是小写是一样的
    lower_name = StringField(max_length=100, required=True)
    #包作者
    author = StringField(max_length=200, required=True,default='')
    #作者邮箱
    author_mail = StringField(max_length=400, required=True,default='')
    #包的网址
    homepage = StringField(max_length=400)
    #包最新版本
    version = StringField(max_length=100, required=True)
    #包历史版本号列表
    releases = ListField()
    #包描述说明
    summary = StringField(required=True,default='')
    meta = {
        'db_alias':'pypi',
        #允许子类继承,必须设置该字段
        'allow_inheritance':True,
        'indexes': ['name','lower_name']
    }
    #包的创建时间
    created_at = DateTimeField(requred=True,default=datetime.datetime.utcnow)
    #包的更新时间
    updated_at = DateTimeField(requred=True,default=datetime.datetime.utcnow)
    
class PyPIPackage(PyPackage):
    bugtrack_url = StringField(max_length=400, required=False)
    docs_url = StringField(max_length=400, required=False)
    package_url = StringField(max_length=400, required=False)
    requires_dist = ListField()
    
class PluginPackage(PyPackage):
    #发布插件的用户
    member_id = ObjectIdField(required=True)
    #插件是否免费
    free = BooleanField(default=True)
    #插件的价格,一次付费永久有效
    price = FloatField()
    #查看次数
    view_amount = IntField(default=0)
    #下载次数
    down_amount = IntField(default=0)
    #插件最新版本的路径
    path = StringField(max_length=400, required=True)
    #插件要求的程序最低版本,默认是从1.1.8版本开始支持插件
    app_version = StringField(max_length=100,default="1.1.8")
    #插件信息存储在plugins数据库中
    meta = {
        'db_alias':'plugins',
    }
    
class FileExtensionPluginPackage(PluginPackage):
    file_extensions = ListField(required=True)
    
class Payments(Document):
    '''
        付款记录
    '''
    member_id = ObjectIdField(required=True)
    plugin_id = ObjectIdField(required=True,unique_with=('member_id',))
    plugin_version = StringField(required=True,max_length=100)
    created_at = DateTimeField(requred=True,default=datetime.datetime.utcnow)
    meta = {
        'db_alias':'plugins'
    }
    