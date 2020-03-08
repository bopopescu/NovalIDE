from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from tkinter import messagebox

class AutoCompletionPlugin(plugin.Plugin):
    """plugin description here..."""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing AutoCompletion plugin")

        GetApp().bind(constants.AUTO_COMPLETION_BACKSPACE_EVT, self.AutoBackSpace,True)
        GetApp().bind(constants.AUTO_COMPLETION_INPUT_EVT, self.AutoInput,True)
                

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """
        return "1.2.1"

    def InstallHook(self):
        """Override in subclasses to allow the plugin to be loaded
        dynamically.
        @return: None

        """
        messagebox.showinfo(GetApp().GetAppName(),_("To use this, go to Tools->Options...->Text panel after install this plugin"))

    def UninstallHook(self):
        pass

    def EnableHook(self):
        pass
        
    def DisableHook(self):
        pass
        
    def GetFree(self):
        return True
        
    def GetPrice(self):
        pass
    
    def AutoInput(self,event):
        current_view = event.get('view')
        char = event.get('char')
        context,hint = current_view.GetAutoCompleteHint()
        ctrl = current_view.GetCtrl()
        completions,replaceLen = current_view.GetAutoCompleteKeywordList(context,hint,ctrl.GetCurrentLine())
        ctrl.AutoCompShow(replaceLen, completions,auto_insert=False)
        hint += char
        if ctrl.autocompleter is not None:
            ctrl.autocompleter.ShowHintCompletions(hint)
        
    def AutoBackSpace(self,event):
        current_view = event.get('view')
        context,hint = current_view.GetAutoCompleteHint()
        if context:
            ctrl = current_view.GetCtrl()
            completions,replaceLen = current_view.GetAutoCompleteKeywordList(context,hint,ctrl.GetCurrentLine())
            #退格时不能自动插入文本,否则会导致匹配列表为1时无法退格
            ctrl.AutoCompShow(replaceLen, completions,auto_insert=False)
            if ctrl.autocompleter is not None:
                ctrl.autocompleter.ShowHintCompletions(hint)
        
