# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import datetime

# Create your models here.
from mongoengine import Document,StringField,EmailField,ObjectIdField,DateTimeField,BooleanField

class Member(Document):
    user_name = StringField(max_length=100)
    password = StringField(max_length=32)
    password_salt = StringField(max_length=8)
    email = EmailField(max_length=100)
    phone = StringField(max_length=11)
    sn = StringField(max_length=100)
    os_bit  = StringField(max_length=50)
    os_name = StringField(max_length=200)
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
    app_version = StringField(max_length=20)
    is_update = BooleanField(default=False)
    os_name = StringField(max_length=20)
    ip_addr = StringField()
    
    meta = {
        'db_alias':'members'
    }
    
    download_at = DateTimeField(requred=True,default=datetime.datetime.utcnow)