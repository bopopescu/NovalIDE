# -*- coding: utf-8 -*-
from random import Random
from django.core.cache import cache
from redis_cache import get_redis_connection
from django.core.mail import send_mail
from web.settings import EMAIL_HOST_USER,ACTIVATE_CODE_TIMEOUT,MEMBERS_REDIS_CACHE
import json
from member.const import *
import os

def random_str(randomlength=8):
    str = ''
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str

def sendto_email(to_mail, send_type=sendtype_default,**kwargs):
    if send_type == sendtype_verificationcode:
        code = random_str(4)
    else:
        code = random_str(15)
    kwargs['send_type'] = send_type
    conn = get_redis_connection(MEMBERS_REDIS_CACHE)
    key = activate_code_key%code
    conn.set(key,json.dumps(kwargs))
    conn.expire(key, ACTIVATE_CODE_TIMEOUT)
    if send_type == sendtype_default:
        email_title = "诺娃IDE在线注册激活"
        email_body = "如果你确认要激活你的账户，请尽快点击该链接激活:http://www.novalide.com/member/activate/{}".format(code)

        os.system('/opt/web/sendmail.py -t "%s" -s "%s" -to %s'%(email_title,email_body,to_mail))
       # send_status = send_mail(email_title, email_body, 'kan.wu@genetalks.com', [to_mail])
        #if send_status:
         #   pass
    elif send_type == "forget":
        email_title = "碎碎猫在线密码重置链接"
        email_body = "重置您的密码请点击连接： http://www.suisuimao.com/reset/{}".format(code)

        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass

    elif send_type == sendtype_verificationcode:
        email_title = "诺娃IDE在线邮箱验证码"
        email_body = "请不要把验证码告诉他人，您的邮箱验证码为：{0}".format(code)
        os.system('/opt/web/sendmail.py -t "%s" -s "%s" -to %s'%(email_title,email_body,to_mail))
        #send_status = send_mail(email_title, email_body, EMAIL_HOST_USER, [to_mail])
        #if send_status:
         #   pass




