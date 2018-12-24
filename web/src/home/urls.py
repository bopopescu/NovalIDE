#coding:utf-8
"""
与页面相关的url
"""

from django.conf.urls import patterns, url

urlpatterns = patterns('home.views',
    url(r'^$', "index_html"),
    url(r'^(?P<filename>[\w.\/]+)$', 'render_html'),
)
