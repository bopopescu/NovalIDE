#-------------------------------------------------------------------------------
# Name:        findctrl.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-03-14
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
import wx
import BaseCtrl
import service.FindService as FindService
from noval.tool.consts import _

class FindTextCtrl(BaseCtrl.ScintillaCtrl):

    def __init__(self, parent, id=-1,style=wx.NO_FULL_REPAINT_ON_RESIZE):
        BaseCtrl.ScintillaCtrl.__init__(self, parent, id, style=style)
        
    def DoFindText(self,findString,flags,forceFindNext = False, forceFindPrevious = False):
        startLoc, endLoc = self.GetSelection()
        wholeWord = flags & wx.FR_WHOLEWORD > 0
        matchCase = flags & wx.FR_MATCHCASE > 0
        regExp = flags & FindService.FindService.FR_REGEXP > 0
        down = flags & wx.FR_DOWN > 0
        wrap = flags & FindService.FindService.FR_WRAP > 0
        
        if forceFindPrevious:   # this is from function keys, not dialog box
            down = False
            wrap = False        # user would want to know they're at the end of file
        elif forceFindNext:
            down = True
            wrap = False        # user would want to know they're at the end of file
            
        minpos = self.GetSelectionStart()
        maxpos = self.GetSelectionEnd()
        if minpos != maxpos:
            if down:
                minpos += 1
            else:
                maxpos = minpos - 1
        if down:
            maxpos = self.GetLength()
        else:
            minpos = 0
        flags =  wx.stc.STC_FIND_MATCHCASE if matchCase else 0
        flags |= wx.stc.STC_FIND_WHOLEWORD if wholeWord else 0
        flags |= wx.stc.STC_FIND_REGEXP if regExp else 0
         #Swap the start and end positions which Scintilla uses to flag backward searches
        if not down:
            tmp_min = minpos
            minpos = maxpos
            maxpos= tmp_min

        return True if self.FindAndSelect(findString,minpos,maxpos,flags) != -1 else False
        
    def FindAndSelect(self,findString,minpos,maxpos,flags):
        index = self.FindText(minpos,maxpos,findString,flags)
        if -1 != index:
            start = index
            end = index + len(findString.encode('utf-8'))
            self.SetSelection(start,end)
            self.EnsureVisibleEnforcePolicy(self.LineFromPosition(end))  # show bottom then scroll up to top
            self.EnsureVisibleEnforcePolicy(self.LineFromPosition(start)) # do this after ensuring bottom is visible
            wx.GetApp().GetTopWindow().PushStatusText(_("Found \"%s\".") % findString)
        return index

    def TextNotFound(self,findString,flags,forceFindNext = False, forceFindPrevious = False):
        wx.MessageBox(_("Have been reached the end of document,Can't find \"%s\".") % findString, _("Find Text"),
                          wx.OK | wx.ICON_INFORMATION)     
        down = flags & wx.FR_DOWN > 0
        wrap = flags & FindService.FindService.FR_WRAP > 0
        if forceFindPrevious: 
            down = False
            wrap = False 
        elif forceFindNext:
            down = True
            wrap = False
        if wrap & down:
            self.SetSelectionStart(0)
            self.SetSelectionEnd(0)
        elif wrap & (not down):
            doc_length = self.GetLength()
            self.SetSelectionStart(doc_length)
            self.SetSelectionEnd(doc_length)