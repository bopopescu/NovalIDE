#coding:utf-8
from noval import GetApp,_
import noval.iface as iface
import noval.plugin as plugin
import noval.ttkwidgets.linklabel as linklabel
import tkinter as tk
import noval.util.fileutils as fileutils
import datetime
from dummy.userdb import UserDataDb
import noval.util.urlutils as urlutils
import noval.util.utils as utils
import threading

class Feed:
    def __init__(self,text,url=None,call_back=None,start_time=None,end_time=None):
        self.msg = text
        self.url = url
        self.cack_back = call_back
        self.start_time = start_time
        self.end_time = end_time

FEEDS = []

def add_feed(feed):
    global FEEDS
    FEEDS.append(feed)

class AdvLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        toolbar = GetApp().MainFrame.GetToolBar()
        group_frame = toolbar.CreateNewSlave()
        self.link_var = tk.StringVar()
        self.link_label = linklabel.LinkLabel(group_frame,textvariable=self.link_var,normal_color='DeepPink',hover_color='DeepPink',clicked_color='red')
        self.link_label.bind("<Button-1>", self.OpenLink)
        self.link_label.pack(fill="x",side=tk.RIGHT)
        self.index = 0
        self.current_index = 0
        self.elapse = 0
        add_feed(Feed("双十一狂欢,点击参与!!","http://www.baidu.com"))
        add_feed(Feed("过年狂打折!!","http://www.novalide.com/"))
        #self.LoadFeedsSync()
        self.link_label.after(100,self.LoadFeedsSync)
      #  self.LoadFeeds()
        
    def ShowAdv(self):
        api_addr = '%s/member/show_adv' % (UserDataDb.HOST_SERVER_ADDR)
        data = urlutils.RequestData(api_addr,arg = {'app_version':utils.get_app_version()})
        if not data:
            return False
        self.elapse = data['elapse']
        return data['show_adv']

    def GetServerFeeds(self):
        global FEEDS
        api_addr = '%s/member/get_feeds' % (UserDataDb.HOST_SERVER_ADDR)
        data = urlutils.RequestData(api_addr,arg = {'app_version':utils.get_app_version()})
        print (data,"++++++++++++++++++++++")
        if not data:
            return []
        feeds = data['feeds']
        for d in feeds:
            FEEDS.append(Feed(text=d.get('msg'),url=get.get('url'),start_time=d.get('start_time',None),\
                 end_time=d.get('end_time',None)))
    
    def OpenLink(self,event):
        feed = FEEDS[self.current_index]
        if feed.url:
            fileutils.startfile(feed.url)
        elif feed.call_back:
            feed.call_back()
        
    def LoadFeedsSync(self):
        t = threading.Thread(target=self.LoadFeeds)
        t.start()
        
    def LoadFeeds(self):
        global FEEDS
        if not self.ShowAdv():
            return
        self.GetServerFeeds()
        if len(FEEDS) == 0:
            return
        if len(FEEDS) == 1:
            feed = FEEDS[self.index]
            self.link_var.set(feed.msg)
        else:
            self.start_time = datetime.datetime.now()
            self.link_label.after(5000,self.LoadFeed)
            
    def LoadFeed(self):
        global FEEDS
        self.end_time = datetime.datetime.now()
        time_delta = self.end_time - self.start_time
        if 0 == len(FEEDS) or time_delta.seconds > self.elapse*3600:
            self.link_var.set("")
            return
        if self.index >= len(FEEDS):
            self.index = 0
        self.current_index = self.index
        feed = FEEDS[self.index]
        self.index += 1
        self.link_var.set(feed.msg)
        if not self.IsFeedAvailable(feed):
            FEEDS.remove(feed)
        self.link_label.after(5000,self.LoadFeed)
        
    def IsFeedAvailable(self,feed):
        if feed.start_time and feed.end_time is None:
            return True
        now_time = datetime.datetime.now()
        if feed.start_time is not None:
            start_time = datetime.datetime.strptime(feed.start_time)
            if now_time < start_time:
                return False
        if feed.end_time is not None:
            end_time = datetime.datetime.strptime(feed.end_time)
            if now_time > end_time:
                return False
        return True