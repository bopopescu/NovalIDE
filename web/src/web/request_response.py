#coding:utf-8

import sys
import traceback
import uuid
import json
import re

from django.conf import settings
from django.http import HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import render, render_to_response
###from utils.response import json_response
###import utils.string
import logging

from django.contrib.sessions.models import Session

logger = logging.getLogger('site')

class RequestResponse(object):
    def process_request(self, request):
        if settings.DEBUG:
            print '\n\n--process_request called'
            if 'HTTP_COOKIE' in request.META:
                print '--cookies', request.META['HTTP_COOKIE'].replace("sessionid=", "session:")
                # for s in Session.objects.all():
                #     print s
            for x in request.REQUEST:
                print '--path:', request.path
                ###print '--args:', x, 'value:', request.REQUEST.get(x)
        
        logger.info("%s -- %s: --- %s" % (request.path, request.META.get('HTTP_COOKIE'), request.REQUEST))
        #请求是否需要登录
        url_prefix = request.path

        if settings.DEBUG:
            #给客户端调试辅助
            debug_name = request.REQUEST.get('debug_name')
                
        return None

    def process_response(self, request, response):
        if response.status_code in (500, 404) and \
                isinstance(response, (HttpResponseServerError, HttpResponseNotFound)):
            if self._should_hold_exception(request):
                response.content = json.dumps(self._process_exception_response(request, response.content, response.status_code))
            
        if settings.DEBUG:
            print '--process_response called'
            print '--status code:', response.status_code
            print '--returns:'
            ###print utils.string.truncate(response.content, 100)

        return response

    def process_exception(self, request, exception):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error("\n%s\n%s  %s\n%s\n" % (request.path, str(exc_type), str(exc_value), traceback.extract_tb(exc_traceback)))

        if self._should_hold_exception(request):
            return json_response(code=SYSTEM_ERROR,
                                 message=u"服务器正在努力中...",
                                 exception_type=str(exc_type),
                                 exception_value=str(exc_value),
                                 exception_location=traceback.extract_tb(exc_traceback))
        
        filename = '404.html'
        return render_to_response(filename)

    
    def _process_exception_response(self, request, content, status_code):
        d = {}
        
        if status_code == 500:
            text = content.replace("\n", "").replace("&#39;", "")
            start = "<th>Exception Type:</th>      <td>"
            end = "</td>    </tr>    <tr>      <th>Exception Value:</th> "
            exception_type = re.search(re.escape(start)+"(.*?)"+re.escape(end), text)
         	
            start = "Exception Value:</th>      <td><pre>"
            end = "</pre></td>    </tr>    <tr>      <th>Exception Location:</th>"
            exception_value = re.search(re.escape(start)+"(.*?)"+re.escape(end), text)
         	
            start = "Exception Location:</th>      <td>"
            end = "</td>    </tr>    <tr>      <th>Python Executable:</th>"
            exception_location = re.search(re.escape(start)+"(.*?)"+re.escape(end), text)
                
            d.update({'code': SYSTEM_ERROR, 
                      'message': u"发生系统错误", 
                      'exception_type': exception_type.group(1), 
                      'exception_value': exception_value.group(1), 
                      'exception_location': exception_location.group(1)})
            
        elif status_code == 404:
            d.update({'code': SYSTEM_ERROR,
            	     'message': u"发生请求路径错误",
            	     'exception_type': 'Exception.HttpResponseNotFound',
            	     'exception_value': 'Page not found(404)',
            	     'exception_location': request.path})
    	return d
        
    def _should_hold_exception(self, request):
        Accept = request.META.get('HTTP_ACCEPT', 'text/html')

        is_json = ('application/json' in Accept.lower())
        is_obvious = int(request.REQUEST.get('json', 0)) == 1
        is_client = len(request.META.get('X-TIANTIAN-VERSION', '')) > 0
        
        return is_json or is_obvious or is_client
