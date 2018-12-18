import wx
from noval.tool.consts import SPACE,HALF_SPACE,_
import os
import noval.tool.images as images
import noval.util.constants as constants

class BreakpointExceptionDialog(wx.Dialog):
    EXCEPTIONS = ['ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException', 'BufferError', \
        'BytesWarning', 'DeprecationWarning', 'EOFError', 'EnvironmentError', 'Exception', \
         'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError', 'ImportError', \
         'ImportWarning', 'IndentationError', 'IndexError', 'KeyError', 'KeyboardInterrupt', \
         'LookupError', 'MemoryError', 'NameError', 'NotImplementedError', 'OSError', 'OverflowError', \
         'PendingDeprecationWarning', 'ReferenceError', 'RuntimeError', 'RuntimeWarning', 'StandardError', \
         'StopIteration', 'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'TypeError', \
         'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError',\
          'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning', 'WindowsError', 'ZeroDivisionError']
 
    def __init__(self,parent,dlg_id,title):
        self.filters = []
        wx.Dialog.__init__(self,parent,dlg_id,title)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        
        boxsizer.Add(wx.StaticText(self, -1, _("Break when exception is:"), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.ALL,border=SPACE)
        
        self.listbox = wx.CheckListBox(self,-1,size=(400,300),choices=[])
        boxsizer.Add(self.listbox,0,flag = wx.EXPAND|wx.BOTTOM|wx.RIGHT,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.select_all_btn = wx.Button(self, -1, _("Select All"))
        wx.EVT_BUTTON(self.select_all_btn, -1, self.SelectAll)
        lineSizer.Add(self.select_all_btn, 0,flag=wx.LEFT, border=SPACE)
        
        self.unselect_all_btn = wx.Button(self, -1, _("UnSelect All"))
        wx.EVT_BUTTON(self.unselect_all_btn, -1, self.UnSelectAll)
        lineSizer.Add(self.unselect_all_btn, 0,flag=wx.LEFT, border=SPACE)
        boxsizer.Add(lineSizer,0,flag = wx.RIGHT|wx.ALIGN_RIGHT,border = SPACE) 


        boxsizer.Add(wx.StaticText(self, -1, _("User defined exceptions:"), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.BOTTOM|wx.RIGHT|wx.TOP,border=SPACE)
                        
        self.other_exception_ctrl = wx.TextCtrl(self, -1, "", size=(-1,-1))
        boxsizer.Add(self.other_exception_ctrl, 0, flag=wx.BOTTOM|wx.RIGHT|wx.EXPAND,border=SPACE)

        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_exception_btn = wx.Button(self, -1, _("Add Exception"))
        wx.EVT_BUTTON(self.add_exception_btn, -1, self.AddException)
        lineSizer.Add(self.add_exception_btn, 0,flag=wx.LEFT, border=SPACE)
        boxsizer.Add(lineSizer,0,flag = wx.RIGHT|wx.ALIGN_RIGHT|wx.BOTTOM,border = SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM|wx.TOP,HALF_SPACE)
        self.SetSizer(boxsizer)
        self.Fit()
        self.InitExceptions()
        self.exceptions = []
        
    def OnOKClick(self,event):
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                exception = self.listbox.GetString(i)
                self.exceptions.append(exception)
        self.EndModal(wx.ID_OK)
        
    def InitExceptions(self):
        descr = ''
        for exception in self.EXCEPTIONS:
            self.listbox.Append(exception)
            
    def SelectAll(self,event):
        for i in range(self.listbox.GetCount()):
            if not self.listbox.IsChecked(i):
                self.listbox.Check(i,True)
        
    def UnSelectAll(self,event):
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                self.listbox.Check(i,False)
            
    def AddException(self,event):
        other_exception = self.other_exception_ctrl.GetValue().strip()
        if other_exception == "":
            return
        self.listbox.Append(other_exception)
        
class BreakpointsUI(wx.Panel):
    FILE_NAME_COLUMN_WIDTH = 150
    FILE_LINE_COLUMN_WIDTH = 50
    def __init__(self, parent, id, ui,degugger_service):
        wx.Panel.__init__(self, parent, id)
        self._ui = ui
        self._degugger_service = degugger_service
        self.currentItem = None
        self.clearBPID = wx.NewId()
        self.Bind(wx.EVT_MENU, self.ClearBreakPoint, id=self.clearBPID)
        self.syncLineID = wx.NewId()
        self.Bind(wx.EVT_MENU, self.SyncBPLine, id=self.syncLineID)
        sizer = wx.BoxSizer(wx.VERTICAL)
        p1 = self
        self._bpListCtrl = wx.ListCtrl(p1, -1, pos=wx.DefaultPosition, size=(1000,1000), style=wx.LC_REPORT)
        il = wx.ImageList(16, 16)
        breakpoint_bmp = images.load("debugger/breakpoint.png")
        self.BreakpointIndex = il.Add(breakpoint_bmp)
        self._bpListCtrl.AssignImageList(il, wx.IMAGE_LIST_SMALL)
        
        sizer.Add(self._bpListCtrl, 1, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 1)
        self._bpListCtrl.InsertColumn(0, _("File"))
        self._bpListCtrl.InsertColumn(1, _("Line"))
        self._bpListCtrl.InsertColumn(2, _("Path"))
        self._bpListCtrl.SetColumnWidth(0, self.FILE_NAME_COLUMN_WIDTH)
        self._bpListCtrl.SetColumnWidth(1, self.FILE_LINE_COLUMN_WIDTH)
        self._bpListCtrl.SetColumnWidth(2, 450)
        self._bpListCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnListRightClick)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.ListItemSelected, self._bpListCtrl)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.ListItemDeselected, self._bpListCtrl)

        def OnLeftDoubleClick(event):
            self.SyncBPLine(event)

        wx.EVT_LEFT_DCLICK(self._bpListCtrl, OnLeftDoubleClick)

        self.PopulateBPList()

        p1.SetSizer(sizer)
        sizer.Fit(p1)
        p1.Layout()

    def PopulateBPList(self):
        list = self._bpListCtrl
        list.DeleteAllItems()

        bps = self._degugger_service.GetMasterBreakpointDict()
        index = 0
        for fileName in bps.keys():
            shortFile = os.path.basename(fileName)
            lines = bps[fileName]
            if lines:
                for line in lines:
                    list.InsertImageStringItem( index,shortFile ,self.BreakpointIndex)
                    list.SetStringItem(index, 1, str(line))
                    list.SetStringItem(index, 2, fileName)

    def OnListRightClick(self, event):
        menu = wx.Menu()
        item = wx.MenuItem(menu, self.clearBPID, _("Clear Breakpoint"))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.syncLineID, _("Goto Source Line"))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, constants.ID_CLEAR_ALL_BREAKPOINTS, _("&Clear All Breakpoints"))
        menu.AppendItem(item)
        self.PopupMenu(menu, event.GetPosition())
        menu.Destroy()

    def SyncBPLine(self, event):
        if self.currentItem != -1:
            list = self._bpListCtrl
            fileName = list.GetItem(self.currentItem, 2).GetText()
            lineNumber = list.GetItem(self.currentItem, 1).GetText()
            self._ui.SynchCurrentLine( fileName, int(lineNumber) , noArrow=True)

    def ClearBreakPoint(self, event):
        if self.currentItem >= 0:
            list = self._bpListCtrl
            fileName = list.GetItem(self.currentItem, 2).GetText()
            lineNumber = list.GetItem(self.currentItem, 1).GetText()
            self._degugger_service.OnToggleBreakpoint(None, line=int(lineNumber) -1, fileName=fileName )

    def ListItemSelected(self, event):
        self.currentItem = event.m_itemIndex

    def ListItemDeselected(self, event):
        self.currentItem = -1
