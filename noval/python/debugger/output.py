# -*- coding: utf-8 -*-
from noval import GetApp,_
from tkinter import messagebox
from noval.project.output import *

class DebugOutputctrl(CommonOutputctrl):
    def __init__(self, parent,is_debug=False,**kwargs):
        CommonOutputctrl.__init__(self, parent,**kwargs)
        self._is_debug = is_debug

    def OnDoubleClick(self, event):
        # Looking for a stack trace line.
        line, col = self.GetCurrentLineColumn()
        lineText = self.GetLineText(line)
        #python程序崩溃有3种错误方式
        #1:主程序报错
        #2:线程报错
        #3:语法错误
        
        #这是线程错误格式
        #Thread 0x00001704 (most recent call first):
        #  File "D:\env\project\Noval\noval\launcher.py", line 33 in run
        
        #这是主程序报错格式
        #Traceback (most recent call last):
        # File "D:\env\project\Noval\noval\ui_base.py", line 572, in _dispatch_tk_operation
        
        #这是语法错误格式
        #File "D:\env\project\Noval\tests\test_utils.py", line 15
        
        fileBegin = lineText.find("File \"")
        fileEnd = lineText.find("\", line ")
        #主程序错误
        lineEnd = lineText.find(", in ")
        #线程错误
        lineEnd2 = lineText.find(" in ")
        if lineText == "\n" or  fileBegin == -1 or fileEnd == -1:
            # Check the line before the one that was clicked on
            lineNumber = self.GetCurrentLine()
            if(lineNumber == 0):
                return
            lineText = self.GetLineText(lineNumber - 1)
            fileBegin = lineText.find("File \"")
            fileEnd = lineText.find("\", line ")
            lineEnd = lineText.find(", in ")
            lineEnd2 = lineText.find(" in ")
            if lineText == "\n" or  fileBegin == -1 or fileEnd == -1:
                return

        filename = lineText[fileBegin + 6:fileEnd]
        if filename == "<string>" :
            return
        if -1 == lineEnd:
            if -1 == lineEnd2:
                lineNum = int(lineText[fileEnd + 8:])
            else:
               lineNum = int(lineText[fileEnd + 8:lineEnd2]) 
        else:
            lineNum = int(lineText[fileEnd + 8:lineEnd])
        if filename and not os.path.exists(filename):
            messagebox.showerror( _("File Error"),_("The file '%s' doesn't exist and couldn't be opened!") % filename,parent=self.master)
            return
        GetApp().GotoView(filename,lineNum,load_outline=False)
        #last activiate debug view
        self.ActivateView()

class DebugOutputView(CommononOutputview):
    def __init__(self, master,is_debug=False):
        CommononOutputview.__init__(self, master)

    def GetOuputctrlClass(self):
        return DebugOutputctrl