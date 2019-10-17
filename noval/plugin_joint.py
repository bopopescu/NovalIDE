# -*- coding: utf-8 -*-
import noval.plugin as plugin
import noval.iface as iface
import noval.util.utils as utils
import time

class MainWindowAddOn(plugin.Plugin):
    """Plugin that Extends the L{MainWindowI}"""
    observers = plugin.ExtensionPoint(iface.MainWindowI)
    def Init(self, window):
        """Call all observers once to initialize
        @param window: window that observers become children of

        """
        for observer in self.observers:
            try:
                #计算插件初始化时间
                start = time.clock()
                observer.PlugIt(window)
                end = time.clock()
                elapse = end - start
                utils.get_logger().info("init plugin %s elapse time %.3f seconds" % (observer.__class__.__name__,end-start))
            except Exception as e:
                utils.get_logger().exception("MainWindowAddOn.Init plugin %s: %s" , observer.__class__,e)

    def GetEventHandlers(self, ui_evt=False):
        """Get Event handlers and Id's from all observers
        @keyword ui_evt: Get Update Ui handlers (default get menu handlers)
        @return: list [(ID_FOO, foo.OnFoo), (ID_BAR, bar.OnBar)]

        """
        handlers = list()
        for observer in self.observers:
            try:
                items = None
                if ui_evt:
                    if hasattr(observer, 'GetUIHandlers'):
                        items = observer.GetUIHandlers()
                        assert isinstance(items, list), "Must be a list()!"
                else:
                    if hasattr(observer, 'GetMenuHandlers'):
                        items = observer.GetMenuHandlers()
                        assert isinstance(items, list), "Must be a list()!"
            except Exception as e:
                util.Log("[ed_main][err] MainWindowAddOn.GetEventHandlers: %s" % str(e))
                continue

            if items is not None:
                handlers.extend(items)

        return handlers
        
class CommonPluginLoader(plugin.Plugin):
    observers = plugin.ExtensionPoint(iface.CommonPluginI)
    def Load(self):
        for observer in self.observers:
            observer.Load()

        
