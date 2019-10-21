# -*- coding: utf-8 -*-
"""web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import patterns, include, url
from django.contrib import admin
import member.views
from django.conf import settings

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    #获取用户信息
    url(r'^member/getuser', member.views.get_member),
    #创建用户
    url(r'^member/createuser', member.views.register_member),
    #纪录用户使用数据
    url(r'^member/share_data', member.views.share_member_data),
    #获取软件版本信息
    url(r'^member/get_update', member.views.get_update_info),
    #下载软件
    url(r'^member/download_app', member.views.download_app),
    url(r'^member/login', member.views.login),
    url(r'^member/get_mail', member.views.get_mail),
    #获取所有pypi包
    url(r'^member/get_pypi_packages', member.views.get_pypi_packages),
    url(r'^member/get_pypi_package_count', member.views.get_pypi_package_count),
    #获取包信息
    url(r'^member/get_package', member.views.get_package_info),
    #获取所有插件
    url(r'^member/get_plugins', member.views.get_plugin_packages),
    #获取插件信息
    url(r'^member/get_plugin', member.views.get_plugin_info),
    #发布并上传插件
    url(r'^member/publish', member.views.publish_plugin),
    #下载插件
    url(r'^member/download_plugin', member.views.download_plugin),
    url(r'^member/get_payment', member.views.get_member_payment),
    url(r'^member/payment', member.views.payment),
    #检查客户端软件是否需要强制更新
    url(r'^member/check_force_update', member.views.check_force_update),
    #set static media file path url pattern,should start with /media
    #静态资源
    url(r"^media/(?P<path>.*)$", "django.views.static.serve", {"document_root": settings.MEDIA_ROOT,}),
    url(r'^', include('home.urls')),
]
