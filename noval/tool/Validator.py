import wx
import string
from consts import _

class NumValidator(wx.PyValidator):
    ''' Validates data as it is entered into the text controls. '''

    #----------------------------------------------------------------------
    def __init__(self,item_name,min_num,max_num):
        wx.PyValidator.__init__(self)
        self._min = min_num
        self._max = max_num
        self._item_name = item_name
        self.Bind(wx.EVT_CHAR, self.OnChar)

    #----------------------------------------------------------------------
    def Clone(self):
        '''Required Validator method'''
        return NumValidator(self._item_name,self._min,self._max)

    #----------------------------------------------------------------------
    def Validate(self, win):
        ctrl = self.GetWindow()
        text = ctrl.GetValue().strip()
        is_valid = False
        if not text.isdigit():
            wx.MessageBox(_("%s must be digit!") % self._item_name, style = wx.OK|wx.ICON_WARNING)
        elif int(text) < self._min:
            wx.MessageBox(_("%s must not be less than %d") % (self._item_name,self._min), style = wx.OK|wx.ICON_WARNING)
        elif int(text) > self._max:
            wx.MessageBox(_("%s must not be greater than %d") % (self._item_name,self._max), style = wx.OK|wx.ICON_WARNING)
        else:
            is_valid = True
            if not is_valid:
                ctrl.SetFocus()
        return True if is_valid else False

    #----------------------------------------------------------------------
    def TransferToWindow(self):
        return True

    #----------------------------------------------------------------------
    def TransferFromWindow(self):
        return True

    #----------------------------------------------------------------------
    def OnChar(self, event):
        keycode = int(event.GetKeyCode())
        if keycode < 256:
            key = chr(keycode)
            if key in string.digits or keycode == 8:
                event.Skip()
                return
        #if is not digit,bell it
        if not wx.Validator_IsSilent():
            wx.Bell()
        

