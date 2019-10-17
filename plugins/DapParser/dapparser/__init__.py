from noval import _,GetApp,NewId
import os
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
from pkg_resources import resource_filename
import shutil
import noval.project.variables as variablesutils

class DapParserPlugin(plugin.Plugin):
    """Simple Programmer's Calculator"""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing DapParser plugin.............")
        
    def CopyDapscript(self):
        path = resource_filename(__name__,'')
        dap_scipt_path = os.path.join(path,"_dap.py")
        lexer_path = self.GetInstallPythonLexerPath()
        utils.get_logger().info('DapParser script path is %s,lexer path is %s',dap_scipt_path,lexer_path)
        shutil.copy(dap_scipt_path,lexer_path)
        
    def RemoveDapscript(self):
        lexer_path = self.GetInstallPythonLexerPath()
        dap_scipt_path = os.path.join(lexer_path,"_dap.py")
        try:
            os.remove(dap_scipt_path)
            utils.get_logger().info('remove DapParser lexer script path %s success',dap_scipt_path)
        except:
            utils.get_logger().error('remove DapParser lexer script path %s success',dap_scipt_path)
    
    def GetInstallPythonLexerPath(self):
        project_variable_manager = variablesutils.GetProjectVariableManager()
        d = project_variable_manager.GetGlobalVariables()
        install_path = d["InstallPath"]
        lexer_path = os.path.join(install_path,"noval","python","syntax","lexer")
        return lexer_path
        
    def InstallHook(self):
        '''
        '''
        self.CopyDapscript()
        
    def UninstallHook(self):
        ''''''
        self.RemoveDapscript()

    def EnableHook(self):
        ''''''
        self.CopyDapscript()
        
    def DisableHook(self):
        ''''''
        self.RemoveDapscript()
        
    def GetMinVersion(self):
        ''''''