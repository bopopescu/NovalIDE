import wx
from noval.tool.consts import SPACE,HALF_SPACE,_

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
