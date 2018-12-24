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
    url(r'^member/getuser', member.views.get_member),
    url(r'^member/createuser', member.views.register_member),
    url(r'^member/share_data', member.views.share_member_data),
    url(r'^member/get_update', member.views.get_update_info),
    url(r'^member/download_app', member.views.new_app_download),
    url(r'^member/login', member.views.login),
    url(r'^member/get_mail', member.views.get_mail),
    #set static media file path url pattern,should start with /media
    url(r"^media/(?P<path>.*)$", "django.views.static.serve", {"document_root": settings.MEDIA_ROOT,}),
    url(r'^', include('home.urls')),
]
