#----------------------------------------------------------------------------
# Name:         MarkerService.py
# Purpose:      Adding and removing line markers in text for easy searching
#
# Author:       Morgan Hua
#
# Created:      10/6/03
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.stc
import wx.lib.docview
import wx.lib.pydocview
import os
import noval.util.sysutils as sysutilslib
import noval.tool.consts as consts
import noval.util.constants as constants
_ = constants._


class MarkerService(wx.lib.pydocview.DocService):
    def __init__(self):
        pass

    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        if document and document.GetFirstView().GetType() != consts.TEXT_VIEW:
            return
        if not document and wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return

        editMenu = menuBar.GetMenu(menuBar.FindMenu(_("&Edit")))
        editMenu.AppendSeparator()
        bookMenu = wx.Menu()
        item = wx.MenuItem(bookMenu,constants.ID_TOGGLE_MARKER, _("Toggle &Bookmark\tCtrl+M"), _("Toggles a bookmark at text line"))
        tooglebk_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "tooglebk.png")
        item.SetBitmap(wx.BitmapFromImage(wx.Image(tooglebk_image_path,wx.BITMAP_TYPE_ANY)))
        bookMenu.AppendItem(item)
        wx.EVT_MENU(frame, constants.ID_TOGGLE_MARKER, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_TOGGLE_MARKER, frame.ProcessUpdateUIEvent)
        item = wx.MenuItem(bookMenu,constants.ID_DELALL_MARKER, _("Clear Bookmarks"), _("Removes all jump bookmarks from selected file"))
        clearbk_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "clearbk.png")
        item.SetBitmap(wx.BitmapFromImage(wx.Image(clearbk_image_path,wx.BITMAP_TYPE_ANY)))
        bookMenu.AppendItem(item)
        wx.EVT_MENU(frame, constants.ID_DELALL_MARKER, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_DELALL_MARKER, frame.ProcessUpdateUIEvent)
        item = wx.MenuItem(bookMenu,constants.ID_NEXT_MARKER, _("Bookmark Next\tF4"), _("Moves to next bookmark in selected file"))
        nextbk_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "nextbk.png")
        item.SetBitmap(wx.BitmapFromImage(wx.Image(nextbk_image_path,wx.BITMAP_TYPE_ANY)))
        bookMenu.AppendItem(item)
        wx.EVT_MENU(frame, constants.ID_NEXT_MARKER, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_NEXT_MARKER, frame.ProcessUpdateUIEvent)
        item = wx.MenuItem(bookMenu,constants.ID_PREV_MARKER, _("Bookmark Previous\tShift+F4"), _("Moves to previous bookmark in selected file"))
        prevbk_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "prevbk.png")
        item.SetBitmap(wx.BitmapFromImage(wx.Image(prevbk_image_path,wx.BITMAP_TYPE_ANY)))
        bookMenu.AppendItem(item)
        wx.EVT_MENU(frame, constants.ID_PREV_MARKER, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, constants.ID_PREV_MARKER, frame.ProcessUpdateUIEvent)

        editMenu.AppendMenu(constants.ID_BOOKMARKER, _("&BookMark"), bookMenu)
        wx.EVT_UPDATE_UI(frame, constants.ID_BOOKMARKER, frame.ProcessUpdateUIEvent)


    def ProcessEvent(self, event):
        id = event.GetId()
        if id == constants.ID_TOGGLE_MARKER:
            wx.GetApp().GetDocumentManager().GetCurrentView().MarkerToggle()
            return True
        elif id == constants.ID_DELALL_MARKER:
            wx.GetApp().GetDocumentManager().GetCurrentView().MarkerDeleteAll()
            return True
        elif id == constants.ID_NEXT_MARKER:
            wx.GetApp().GetDocumentManager().GetCurrentView().MarkerNext()
            return True
        elif id == constants.ID_PREV_MARKER:
            wx.GetApp().GetDocumentManager().GetCurrentView().MarkerPrevious()
            return True
        else:
            return False


    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == constants.ID_TOGGLE_MARKER:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            event.Enable(hasattr(view, "MarkerToggle"))
            return True
        elif id == constants.ID_DELALL_MARKER:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            event.Enable(hasattr(view, "MarkerDeleteAll") and view.GetMarkerCount())
            return True
        elif id == constants.ID_NEXT_MARKER:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            event.Enable(hasattr(view, "MarkerNext") and view.GetMarkerCount())
            return True
        elif id == constants.ID_PREV_MARKER:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            event.Enable(hasattr(view, "MarkerPrevious") and view.GetMarkerCount())
            return True
        elif (id == constants.ID_BOOKMARKER):
            event.Enable(False)
            return True
        else:
            return False

