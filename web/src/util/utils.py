# -*- coding: utf-8 -*-
import calendar
import datetime
from django.http import HttpResponse
import json
import os
import sys
from bson import ObjectId
from mongoengine.queryset import QuerySet
from django.conf import settings
import logging
from errors import *
from django.core.cache import get_cache
from django.contrib.sessions.backends.cache import KEY_PREFIX
import member.const as const 

logger = logging.getLogger('logsite')


def get_milliseconds_from_datetime(d):
    """
    将datetime对象转换成UNIX时间戳，单位为毫秒。
    此方法不会四舍五入，会采取直接截取的方式去掉小数点之后的数据
    参考用例：
    get_milliseconds_from_datetime('2013-10-01 10:10:10.888')
    get_milliseconds_from_datetime('2013-10-01 10:10:10')
    get_milliseconds_from_datetime(datetime.datetime.utcnow())

    支持带时区的datetime
    返回给客户端：CST的时间戳
    """
    temp = None
    if isinstance(d, basestring):
        # 可以带毫秒, 也可以不带
        if d.find('.') > -1:
            temp = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S.%f')
        else:
            temp = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')

    elif isinstance(d, datetime.datetime):
        return calendar.timegm(d.timetuple()) * 1000 + (d.microsecond / 1000)
    else:
        return d
    
    return calendar.timegm(temp.utctimetuple()) * 1000 + (temp.microsecond / 1000)

def json_response(code=OK, message='',host=None, **kwargs):
    """生成JSON格式的HTTP响应结果。
    
    :param code: int，结果码，0为成功，其余为失败。0-9999用于公共错误，业务错误使用10000或以上。
    :param message: str，结果消息，成功时为空，失败时为出错原因。亦可自定义数据结构。
    :param **kwargs: 任意数量的业务数据项
    
    :returns: str, JSON字符串
    """
    if not message:
        message = GetCodeMessage(code)
    d = {
        "code": code,
        "message": message
    }

    d.update(kwargs)

    d = bson_type_to_builtin(d)
    if settings.UNITTEST:
        s = json.dumps(d, ensure_ascii=False, indent=4)
    else:
        s = json.dumps(d, ensure_ascii=False)

    if settings.DEBUG:
        logger.info("[Server Response]:\n%s\n\n\n\n\n"%s)
    #else:
     #   logger.info("[Server Response Length]:%d" % len(s) )

    h = HttpResponse(s, content_type='application/json; charset=utf-8')
    return h

def bson_type_to_builtin(data):
    """将变量内的BSON和MongoEngine的类型转换成Python内置内型。
    :param data: mixed
    :returns: mixed
    """
    if isinstance(data, (list, tuple)):
        return [bson_type_to_builtin(v) for v in data]
    elif isinstance(data, dict):
        d = {}
        for k, v in data.items():
            if v is not None:
                if isinstance(k, ObjectId):
                    k = str(k)
                if k == '_id':
                    k = 'id'
                d[k] = bson_type_to_builtin(v)
        return d
    elif isinstance(data, datetime.datetime):
        return get_milliseconds_from_datetime(data)
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, QuerySet):
        return [bson_type_to_builtin(v) for v in data]
    elif isinstance(data,unicode):
        return str(data)
    else:
        return data
        

def MakeDirs(dirname):
    dirname = os.path.abspath(dirname)
    dirname = dirname.replace("\\","/")
    dirnames = dirname.split("/")
    destdir = ""
    destdir = os.path.join(dirnames[0] + "/",dirnames[1])
    
    if not os.path.exists(destdir):
        os.mkdir(destdir)
        
    for name in dirnames[2:]:
        destdir=os.path.join(destdir,name)
        if not os.path.exists(destdir):
            os.mkdir(destdir)
    
def CalcVersionValue(ver_str="0.0.0"):
    """Calculates a version value from the provided dot-formated string

    1) SPECIFICATION: Version value calculation AA.BBB.CCC
         - major values: < 1     (i.e 0.0.85 = 0.850)
         - minor values: 1 - 999 (i.e 0.1.85 = 1.850)
         - micro values: >= 1000 (i.e 1.1.85 = 1001.850)

    @keyword ver_str: Version string to calculate value of

    """
    ver_str = ''.join([char for char in ver_str
                       if char.isdigit() or char == '.'])
    ver_lvl = ver_str.split(u".")
    if len(ver_lvl) < 3:
        return 0

    major = int(ver_lvl[0]) * 1000
    minor = int(ver_lvl[1])
    if len(ver_lvl[2]) <= 2:
        ver_lvl[2] += u'0'
    micro = float(ver_lvl[2]) / 1000
    return float(major) + float(minor) + micro
    
def CompareAppVersion(new_version,old_version):
    if CalcVersionValue(new_version) <= CalcVersionValue(old_version):
        return 0
    return 1
    
def get_session_or_token(request):
    '''
        获取缓存中的sesson token存储的用户数据
    '''
    token = request.REQUEST.get('token',None)
    if token is not None:
        cache = get_cache(settings.SESSION_REDIS_CACHE)
        cache_key = KEY_PREFIX + token
        session_data = cache.get(cache_key)
        if session_data is None:
            return {
                const.IS_LOGINED_KEY:False,
                const.MEMBER_ID_KEY:None
            }
        return session_data
    return request.session
    

def member_logout(request):
    '''
        删除缓存中的sesson token存储的用户数据
    '''
    token = request.REQUEST.get('token',None)
    if token is not None:
        cache = get_cache(settings.SESSION_REDIS_CACHE)
        cache_key = KEY_PREFIX + token
        cache.delete(cache_key)
        

def is_member_logined(request):
    '''
        通过token检测用户是否已经登录,如果已经登录则自动登录
    '''
    session = get_session_or_token(request)
    is_logined = session.get(const.IS_LOGINED_KEY)
    return is_logined

def member_login(request, member):
    '''
        用户登录成功后在缓存中保存session token
    '''
    request.session[const.IS_LOGINED_KEY] = True
    request.session[const.MEMBER_ID_KEY] = member.id
    request.session.save()
    #设置登录时间
    member.login_at = datetime.datetime.utcnow()
    member.save()
    #us = UserSession(member_id=str(member.id), session_id=request.session.session_key)
    #us.save()