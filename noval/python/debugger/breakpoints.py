# -*- coding: utf-8 -*-
from noval import GetApp,_,NewId
import os
import noval.constants as constants
import noval.ui_base as ui_base
import noval.iface as iface
import noval.plugin as plugin
import tkinter as tk
from tkinter import ttk
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.imageutils as imageutils
import noval.consts as consts
import noval.menu as tkmenu
import noval.util.utils as utils
import noval.ttkwidgets.checklistbox as checklistbox

class BreakpointExceptionDialog(ui_base.CommonModaldialog):
    EXCEPTIONS = ['ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException', 'BufferError', \
        'BytesWarning', 'DeprecationWarning', 'EOFError', 'EnvironmentError', 'Exception', \
         'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError', 'ImportError', \
         'ImportWarning', 'IndentationError', 'IndexError', 'KeyError', 'KeyboardInterrupt', \
         'LookupError', 'MemoryError', 'NameError', 'NotImplementedError', 'OSError', 'OverflowError', \
         'PendingDeprecationWarning', 'ReferenceError', 'RuntimeError', 'RuntimeWarning', 'StandardError', \
         'StopIteration', 'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'TypeError', \
         'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError',\
          'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning', 'WindowsError', 'ZeroDivisionError']
 
    def __init__(self,parent):
        self.filters = []
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(_("Add Python Exception Breakpoint"))
        
        ttk.Label(self.main_frame,text=_("Break when exception is:")).pack(fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y)
        check_listbox_view = treeviewframe.TreeViewFrame(self.main_frame,treeview_class=checklistbox.CheckListbox,borderwidth=1,relief="solid",height=10)
        self.listbox = check_listbox_view.tree
        check_listbox_view.pack(fill="both",expand=1)
        
        frame = ttk.Frame(self.main_frame)
        ttk.Button(frame,text=_("UnSelect All"),command=self.UnSelectAll).pack(side=tk.RIGHT,fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        ttk.Button(frame,text=_("Select All"),command=self.SelectAll).pack(side=tk.RIGHT,fill="x")
        frame.pack(fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y)
        ttk.Label(self.main_frame,text= _("User defined exceptions:")).pack(fill="x")
        self.user_exception = tk.StringVar()
        ttk.Entry(self.main_frame, text="",textvariable=self.user_exception).pack(fill="x",expand=1)
        frame = ttk.Frame(self.main_frame)
        ttk.Button(frame,text=_("Add Exception"),command=self.AddException).pack(fill="x",side=tk.RIGHT,padx=consts.DEFAUT_CONTRL_PAD_X)
        frame.pack(fill="x",pady=consts.DEFAUT_CONTRL_PAD_Y)
        self.AddokcancelButton()
        self.InitExceptions()
        self.exceptions = []
        
    def _ok(self,event=None):
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                exception = self.listbox.GetString(i)
                self.exceptions.append(exception)
        ui_base.CommonModaldialog._ok(self,event)
        
    def InitExceptions(self):
        descr = ''
        for exception in self.EXCEPTIONS:
            self.listbox.Append(exception)
            
    def SelectAll(self):
        for i in range(self.listbox.GetCount()):
            if not self.listbox.IsChecked(i):
                self.listbox.Check(i,True)
        
    def UnSelectAll(self):
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                self.listbox.Check(i,False)
            
    def AddException(self):
        other_exception = self.user_exception.get().strip()
        if other_exception == "":
            return
        self.listbox.Append(other_exception)
        
class BreakpointsUI(treeviewframe.TreeViewFrame):
    FILE_NAME_COLUMN_WIDTH = 150
    FILE_LINE_COLUMN_WIDTH = 50
    clearBPID = NewId()
    syncLineID = NewId()
    def __init__(self, parent):
        columns = ["File","Line","Path"]
        treeviewframe.TreeViewFrame.__init__(self, parent,columns=columns,show="headings",displaycolumns=(0,1,2))
        self.currentItem = None
        for column in columns:
            self.tree.heading(column, text=_(column))
        self.tree.column('0',width=100,anchor='w')
        self.tree.column('1',width=60,anchor='w')


        self.breakpoint_bmp = imageutils.load_image("","python/debugger/breakpoint.png")
        self.tree.bind("<3>", self.OnListRightClick, True)
        self.tree.bind("<Double-Button-1>", self.OnDoubleClick, "+")
        self.currentItem = None
        self._masterBPDict = {}
        self.PopulateBPList()

    def PopulateBPList(self):
        breakpoints = utils.profile_get("MasterBreakpointDict",[])
        for dct in breakpoints:
            self.tree.insert("","end",image=self.breakpoint_bmp,values=(dct['filename'],dct['lineno'],dct['path']))
            self.AddBreakpoint(dct['path'],dct['lineno'])
            
    def OnDoubleClick(self, event):
        if not self.tree.selection():
            return
        self.currentItem = self.tree.selection()[0]
        self.SyncBPLine()

    def OnListRightClick(self, event):
        if not self.tree.selection():
            return
        self.currentItem = self.tree.selection()[0]
        menu = tkmenu.PopupMenu()
        item = tkmenu.MenuItem(self.clearBPID, _("Clear Breakpoint"),None,None,None)
        menu.AppendMenuItem(item,handler=self.ClearBreakPoint)
        item = tkmenu.MenuItem(self.syncLineID, _("Goto Source Line"),None,None,None)
        menu.AppendMenuItem(item,handler=self.SyncBPLine)
        item = tkmenu.MenuItem( constants.ID_CLEAR_ALL_BREAKPOINTS, _("&Clear All Breakpoints"),None,None,None)
        menu.AppendMenuItem(item,handler=self.ClearAllBreakPoints)
        menu.tk_popup(event.x_root, event.y_root)

    def SyncBPLine(self):
        if self.currentItem != None:
            values = self.tree.item(self.currentItem,"values")
            fileName = values[2]
            lineNumber = values[1]
            GetApp().GotoView(fileName,int(lineNumber))

    def ClearBreakPoint(self):
        if self.currentItem != None:
            self.DeleteBreakPoint(self.currentItem)
            
    def DeleteBreakPoint(self,item,notify=True):
        values = self.tree.item(item,"values")
        fileName = values[2]
        lineNumber = values[1]
        doc = GetApp().GetDocumentManager().GetDocument(fileName)
        #如果断点所在的文件打开了,同时要删除文件中的断点标记
        if doc:
            doc.GetFirstView().DeleteBpMark(int(lineNumber),notify=notify)
        #否则直接删除节点即可
        else:
            self.tree.delete(item)
            self.RemoveBreakpoint(fileName,lineNumber,notify)

    def ListItemSelected(self, event):
        self.currentItem = event.m_itemIndex

    def ListItemDeselected(self, event):
        self.currentItem = -1

    def ToogleBreakpoint(self,lineno,filename,delete=False,notify=True):
        if not delete:
            self.tree.insert("","end",image=self.breakpoint_bmp,values=(os.path.basename(filename),lineno,filename))
            self.AddBreakpoint(filename,lineno)
            #通知断点服务器增加断点
            if GetApp().GetDebugger()._debugger_ui:
                GetApp().GetDebugger()._debugger_ui.NotifyDebuggersOfBreakpointChange()
        else:
            for child in self.tree.get_children():
                values = self.tree.item(child,"values")
                if values[1] == lineno and values[2] == filename:
                    self.tree.delete(child)
                    self.RemoveBreakpoint(filename,lineno,notify)
                    break
                   
    def ClearAllBreakPoints(self):
        for child in self.tree.get_children():
            #删除所有断点时,不要反复通知断点服务器删除断点,断点删除后统一一次性通知
            self.DeleteBreakPoint(child,notify=False)
        if GetApp().GetDebugger()._debugger_ui is not None:
            GetApp().GetDebugger()._debugger_ui.NotifyDebuggersOfBreakpointChange()
            
    def SaveBreakpoints(self):
        breakpoints = []
        for child in self.tree.get_children():
            values = self.tree.item(child,"values")
            dct = {
                "filename":values[0],
                "lineno":values[1],
                "path":values[2],
            }
            breakpoints.append(dct)
        utils.profile_set("MasterBreakpointDict", breakpoints)
        
    def GetMasterBreakpointDict(self):
        return self._masterBPDict
        
    def AddBreakpoint(self,filename,lineno):
        '''
            通知断点服务器添加断点
        '''
        lineno = int(lineno)
        if not filename in self._masterBPDict:
            self._masterBPDict[filename] = [lineno]
        else:
            self._masterBPDict[filename] += [lineno]
            
    def RemoveBreakpoint(self,filename,lineno,notify=True):
        '''
            通知断点服务器删除断点
        '''
        lineno = int(lineno)
        if not filename in self._masterBPDict:
            utils.get_logger().error("In ClearBreak: no filename %s",filename)
            return
        else:
            if lineno in self._masterBPDict[filename]:
                self._masterBPDict[filename].remove(lineno)
                if self._masterBPDict[filename] == []:
                    del self._masterBPDict[filename]
            #删除断点后通知断点服务器删除断点
            if notify and GetApp().GetDebugger()._debugger_ui:
                GetApp().GetDebugger()._debugger_ui.NotifyDebuggersOfBreakpointChange()
            else:
                utils.get_logger().error("In ClearBreak: no filename %s line %d",filename,lineno)
                
    def SetExceptionBreakPoint(self):
        exception_dlg = BreakpointExceptionDialog(GetApp().GetTopWindow())
        if exception_dlg.ShowModal() == constants.ID_OK:
            GetApp().GetDebugger().SetExceptions(exception_dlg.exceptions)
       
class BreakpointsViewLoader(plugin.Plugin):
    plugin.Implements(iface.CommonPluginI)
    def Load(self):
        GetApp().MainFrame.AddView(consts.BREAKPOINTS_TAB_NAME,BreakpointsUI, _("Break Points"), "se",image_file="python/debugger/breakpoints.png")
        