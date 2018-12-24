# -*- coding: utf-8 -*-
from django.shortcuts import render,render_to_response
from member.models import DownloadData

DEFAULT_DOWNLAOD_COUNT = 0


def index_html(request):
    """首页,依据 http_user_agent 选择渲染的页面, mobile or pc
    """
    req_dic = request.GET
    filename = "index.html"
    http_user_agent = request.META.get("HTTP_USER_AGENT", "")
#    is_mobile = True if -1 != http_user_agent.lower().find("mobile") else False
 #   if is_mobile:
  #      filename = "mobile.html"
    download_count = DEFAULT_DOWNLAOD_COUNT + DownloadData.objects.count()
    return render_to_response(filename, {"req": req_dic,'download_count':download_count})
    

def render_html(request, filename):
    """通用的渲染页面函数
    """
    req_dic = request.GET
    if "." not in filename:
        filename = "%s.html" % filename

    return render_to_response(filename, {"req": req_dic})
