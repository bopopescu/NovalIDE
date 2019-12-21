from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from pkg_resources import resource_filename
import shutil
import noval.project.variables as variablesutils
import os
import noval.util.strutils as strutils
from tkinter import messagebox

class ShellEditorPlugin(plugin.Plugin):
    """plugin description here..."""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing ShellEditor plugin")
        GetApp().bind(constants.FILE_OPENING_EVT,self.OpeningFile,True)
        GetApp().bind(constants.FILE_SAVEING_EVT,self.SaveingFile,True)
        
    def OpeningFile(self,event):
        self.CheckFileLines(event)
        
    def CheckFileLines(self,event):
        msg = event.get('msg')
        doc = msg.get('doc')
        data = msg.get('data')
        filename = doc.GetFilename()
        if strutils.get_file_extension(filename) == "sh":
            if data.find('\r\n') != -1:
                ret = messagebox.askyesno(GetApp().GetAppName(),_("The shell srcipt \"%s\" contains windows line break,it will not run ok on linux,Do you want to convert \"\\r\\n\" to \"\\n\"")%filename)
                if ret == True:
                    msg['data'] = data.replace("\r\n","\n")
                    
    def SaveingFile(self,event):
        self.CheckFileLines(event)
        
    def CopyShellscript(self):
        path = resource_filename(__name__,'')
        shell_scipt_path = os.path.join(path,"_sh.py")
        lexer_path = self.GetInstallLexerPath()
        utils.get_logger().info('shell script path is %s,lexer path is %s',shell_scipt_path,lexer_path)
        shutil.copy(shell_scipt_path,lexer_path)
        
    def RemoveShellscript(self):
        lexer_path = self.GetInstallLexerPath()
        shell_scipt_path = os.path.join(lexer_path,"_sh.py")
        try:
            os.remove(shell_scipt_path)
            utils.get_logger().info('remove ShellEditor lexer script path %s success',shell_scipt_path)
        except:
            utils.get_logger().error('remove ShellEditor lexer script path %s success',shell_scipt_path)
    
    def GetInstallLexerPath(self):
        project_variable_manager = variablesutils.GetProjectVariableManager()
        d = project_variable_manager.GetGlobalVariables()
        install_path = d["InstallPath"]
        lexer_path = os.path.join(install_path,"noval","syntax","lexer")
        return lexer_path

    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of novalide that
        the plugin is compatible with. By default it will return the current
        version of novalide.
        @return: version str
        """
        return "1.2.0"

    def InstallHook(self):
        """Override in subclasses to allow the plugin to be loaded
        dynamically.
        @return: None

        """
        self.CopyShellscript()

    def UninstallHook(self):
        self.RemoveShellscript()

    def EnableHook(self):
        self.CopyShellscript()
        
    def DisableHook(self):
        self.RemoveShellscript()
        
    def GetFree(self):
        return True
        
    def GetPrice(self):
        pass
    
    def GetFileExtension(self):
        return '.sh'
    