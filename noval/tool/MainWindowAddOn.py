import noval.util.plugin as plugin
import noval.util.iface as iface

class MainWindowAddOn(plugin.Plugin):
    """Plugin that Extends the L{MainWindowI}"""
    observers = plugin.ExtensionPoint(iface.MainWindowI)
    def Init(self, window):
        """Call all observers once to initialize
        @param window: window that observers become children of

        """
        for observer in self.observers:
            try:
                observer.PlugIt(window)
            except Exception, msg:
                utils.GetLogger().error("MainWindowAddOn.Init plugin %s: %s" , observer.__class__,msg)

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
            except Exception, msg:
                util.Log("[ed_main][err] MainWindowAddOn.GetEventHandlers: %s" % str(msg))
                continue

            if items is not None:
                handlers.extend(items)

        return handlers
