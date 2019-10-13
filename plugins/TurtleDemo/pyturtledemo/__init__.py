# -*- coding: utf-8 -*-
from noval import _,GetApp,NewId
import noval.iface as iface
import noval.plugin as plugin
import noval.util.utils as utils
import noval.constants as constants
import subprocess
import noval.python.pyutils as pyutils

class TurtleDemoPlugin(plugin.Plugin):
    """Simple Programmer's Calculator"""
    plugin.Implements(iface.MainWindowI)
    ID_TURTLE_DEMO = NewId()
    def PlugIt(self, parent):
        """Hook the calculator into the menu and bind the event"""
        utils.get_logger().info("Installing TurtleDemo plugin")
        if utils.is_py3_plus():
            GetApp().InsertCommand(constants.ID_ABOUT,self.ID_TURTLE_DEMO,_("&Help"),_("Turtle Demo"),handler=self.open_turtle_demo,pos="before")

    def open_turtle_demo(self):
        interpreter = GetApp().GetCurrentInterpreter()
        if interpreter is None:
            return "break"
     #   cmd = [interpreter.Path,
      #         '-c',
       #        'from turtledemo.__main__ import main; main()']
       #utils.get_logger().info("run demo command is %s------------",' '.join(cmd))
        cmd = "%s -c \"from turtledemo.__main__ import main; main()\""%(interpreter.Path)
        args = "-c \"from turtledemo.__main__ import main; main()\""
        pyutils.create_python_interpreter_process(interpreter,args)
##        utils.get_logger().info("run demo command is %s------------",cmd)
##        #隐藏命令行黑框
##        if utils.is_windows():
##            startupinfo = subprocess.STARTUPINFO()
##            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
##            startupinfo.wShowWindow = subprocess.SW_HIDE
##        else:
##            startupinfo = None
##        p = subprocess.Popen(cmd, shell=False,startupinfo=startupinfo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        #p.wait()
        #utils.get_logger().info("command ret code is %d,stdout is %s,stderr is %s+++++++++++++",p.returncode,p.stdout.read(),p.stderr.read())
        return "break"