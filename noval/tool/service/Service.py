#----------------------------------------------------------------------------
# Name:         Service.py
# Purpose:      Basic Reusable Service View for wx.lib.pydocview
#
# Author:       Morgan Hua
#
# Created:      11/4/04
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.lib.docview
import wx.lib.pydocview
import noval.util.sysutils as sysutilslib
import os
import noval.tool.images as images
import noval.util.utils as utils
import noval.tool.aui as aui
from noval.tool.consts import _,DEBUGGER_PAGE_COMMON_METHOD
import copy


FLOATING_MINIFRAME = -1


class ServiceView(wx.EvtHandler):
    """ Basic Service View.
    """
    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self, service):
        wx.EvtHandler.__init__(self)
        self._viewFrame = None
        self._service = service
        self._control = None
        self._embeddedWindow = None


    def Destroy(self):
        wx.EvtHandler.Destroy(self)


    def GetFrame(self):
        if self._viewFrame is not None:
            if not self.AuiManager.FindPane(self._viewFrame):
                paneInfo = self.AuiManager.GetPane(self._viewFrame.name)
                self.SetFrame(paneInfo)
            elif self._viewFrame.name != self._service.GetServiceName():
                for paneInfo in self.AuiManager._panes:
                    if paneInfo.name == self._service.GetServiceName():
                        self.SetFrame(paneInfo)
                        break
        return self._viewFrame

    def SetFrame(self, frame):
        self._viewFrame = frame


    def _CreateControl(self, parent, id):
        return None
        
    
    def GetControl(self):
        return self._control
        
    @property
    def AuiManager(self):
        return self._service.AuiManager

    def SetControl(self, control):
        self._control = control


    def OnCreate(self, doc, flags):
        config = wx.ConfigBase_Get()
        windowLoc = self._service.GetEmbeddedWindowLocation()
        if windowLoc == FLOATING_MINIFRAME:
            pos = config.ReadInt(self._service.GetServiceName() + "FrameXLoc", -1), config.ReadInt(self._service.GetServiceName() + "FrameYLoc", -1)
            # make sure frame is visible
            screenWidth = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
            screenHeight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
            if pos[0] < 0 or pos[0] >= screenWidth or pos[1] < 0 or pos[1] >= screenHeight:
                pos = wx.DefaultPosition

            size = wx.Size(config.ReadInt(self._service.GetServiceName() + "FrameXSize", -1), config.ReadInt(self._service.GetServiceName() + "FrameYSize", -1))
            title = _(self._service.GetServiceName())
            if wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI and wx.GetApp().GetAppName():
                title =  title + " - " + wx.GetApp().GetAppName()
            frame = wx.MiniFrame(wx.GetApp().GetTopWindow(), -1, title, pos = pos, size = size, style = wx.CLOSE_BOX|wx.CAPTION|wx.SYSTEM_MENU)
            wx.EVT_CLOSE(frame, self.OnCloseWindow)
        elif wx.GetApp().IsMDI():
            self._embeddedWindow = self._service._frame
        else:
            pos = config.ReadInt(self._service.GetServiceName() + "FrameXLoc", -1), config.ReadInt(self._service.GetServiceName() + "FrameYLoc", -1)
            # make sure frame is visible
            screenWidth = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
            screenHeight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
            if pos[0] < 0 or pos[0] >= screenWidth or pos[1] < 0 or pos[1] >= screenHeight:
                pos = wx.DefaultPosition

            size = wx.Size(config.ReadInt(self._service.GetServiceName() + "FrameXSize", -1), config.ReadInt(self._service.GetServiceName() + "FrameYSize", -1))
            title = _(self._service.GetServiceName())
            if wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI and wx.GetApp().GetAppName():
                title =  title + " - " + wx.GetApp().GetAppName()
            frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, pos = pos, size = size)
            frame.SetTitle(title)
            if config.ReadInt(self._service.GetServiceName() + "FrameMaximized", False):
                frame.Maximize(True)
            wx.EVT_CLOSE(frame, self.OnCloseWindow)
        
        windowLoc = self._service.GetEmbeddedWindowLocation()
        if self._embeddedWindow or windowLoc == FLOATING_MINIFRAME:
            if (self._service.GetEmbeddedWindowLocation() == wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM):
                direction = aui.AUI_DOCK_BOTTOM
                if self.AuiManager.GetAnyPane(direction) == None:
                    self._control = self._CreateControl(self._embeddedWindow, wx.NewId())
                    pane_info = self._service.CreatePane(direction)
                    frame = pane_info
                    self.SetFrame(frame)
                else:
                    # Factor this out.
                    self._control = self._CreateControl(self._embeddedWindow, wx.NewId())
                    if self._control != None:
                        target = self._service.GetTargetPane(direction)
                        pane_info = self._service.CreatePane(direction,target)
                        frame = pane_info
                        self.SetFrame(frame)
            else:
                # Factor this out.
                self._control = self._CreateControl(self._embeddedWindow, wx.NewId())
                pane_info = self._service.CreatePane(aui.AUI_DOCK_RIGHT)
                frame = pane_info
                self.SetFrame(frame)
        else:
            # Factor this out.
            self._control = self._CreateControl(frame, wx.NewId())
            sizer.Add(self._control, 1, wx.EXPAND, 0)
        self.Activate()
        return True
            
    @staticmethod
    def RemoveAllPages():
        panes = copy.copy(wx.GetApp().MainFrame._mgr.GetAllPanes())
        for pane in panes:
            window = pane.window
            if hasattr(window, DEBUGGER_PAGE_COMMON_METHOD):
                if not window.StopAndRemoveUI(None):
                    return False
        return True
        
    def OnCloseWindow(self, event):
        frame = self.GetFrame()
        config = wx.ConfigBase_Get()
        if frame and not self._embeddedWindow:
            if not frame.IsMaximized():
                config.WriteInt(self._service.GetServiceName() + "FrameXLoc", frame.GetPositionTuple()[0])
                config.WriteInt(self._service.GetServiceName() + "FrameYLoc", frame.GetPositionTuple()[1])
                config.WriteInt(self._service.GetServiceName() + "FrameXSize", frame.GetSizeTuple()[0])
                config.WriteInt(self._service.GetServiceName() + "FrameYSize", frame.GetSizeTuple()[1])
            config.WriteInt(self._service.GetServiceName() + "FrameMaximized", frame.IsMaximized())

        if not self._embeddedWindow:
            windowLoc = self._service.GetEmbeddedWindowLocation()
            if windowLoc == FLOATING_MINIFRAME:
                # don't destroy it, just hide it
                frame.Hide()
            else:
                # Call the original OnCloseWindow, could have subclassed SDIDocFrame and MDIDocFrame but this is easier since it will work for both SDI and MDI frames without subclassing both
                frame.OnCloseWindow(event)


    def Activate(self, activate = True):
        """ Dummy function for SDI mode """
        pass


    def Close(self, deleteWindow = True):
        """
        Closes the view by calling OnClose. If deleteWindow is true, this
        function should delete the window associated with the view.
        """
        if deleteWindow:
            self.Destroy()

        return True


    #----------------------------------------------------------------------------
    # Callback Methods
    #----------------------------------------------------------------------------

    def SetCallback(self, callback):
        """ Sets in the event table for a doubleclick to invoke the given callback.
            Additional calls to this method overwrites the previous entry and only the last set callback will be invoked.
        """
        wx.stc.EVT_STC_DOUBLECLICK(self.GetControl(), self.GetControl().GetId(), callback)


    #----------------------------------------------------------------------------
    # Display Methods
    #----------------------------------------------------------------------------

    def IsShown(self):
        if not self.GetFrame():
            return False
        return self.GetFrame().IsShown()


    def Hide(self):
        self.Show(False)


    def Show(self, show = True):
        if self.GetFrame():
            self.GetFrame().Show(show)
            self._service._frame._mgr.Update()

    def GetAuiNotebook(self):
        pane = self.GetFrame()
        print pane.IsNotebookPage(),pane.notebook_id
        if pane.IsNotebookPage():
            return self._service._frame._mgr.GetNotebookPaneId(pane.notebook_id)
        return None
        
    def GetDockDirection(self):
        windowLoc = self._service.GetEmbeddedWindowLocation()
        if windowLoc == wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM:
            return aui.AUI_DOCK_BOTTOM
        elif windowLoc == wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT:
            return aui.AUI_DOCK_RIGHT
        elif windowLoc == wx.lib.pydocview.EMBEDDED_WINDOW_LEFT:
            return aui.AUI_DOCK_LEFT

class TabbedServiceView(ServiceView):
    """ Service View for notebook.
    """

    
    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self, service):
        ServiceView.__init__(self, service)
        
    def Show(self, show = True):
        pane = self.GetFrame()
        dock_direction = self.GetDockDirection()
        if self.IsShown():
            pane.Show(False)
            self.AuiManager.ClosePane(pane)
        else:
            target_pane = self._service.GetTargetPane(dock_direction)
            pane.dock_direction_set(dock_direction)
            pane.dock_layer = 1
            pane.Show(True)
            self.AuiManager.AddPane(self.GetControl(), pane, target=target_pane)
        self.AuiManager.Update()
            
    def ShowFrame(self, show):
        if self.GetFrame():
            self.GetFrame().Show(show)

        
class BaseService(wx.lib.pydocview.DocService):

    def __init__(self):
        wx.lib.pydocview.DocService.__init__(self)

    @staticmethod
    def GetActiveView():
        if None == wx.GetApp().MainFrame:
            return None
        return wx.GetApp().MainFrame.GetActiveTextView()

class Service(BaseService):

    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    SHOW_WINDOW = wx.NewId()  # keep this line for each subclass, need unique ID for each Service

    def __init__(self, serviceName, embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_LEFT,icon_path=None):
        self._serviceName = serviceName
        self._embeddedWindowLocation = embeddedWindowLocation
        self._view = None
        self._frame = None
        self._icon_path = icon_path

    def GetEmbeddedWindowLocation(self):
        return self._embeddedWindowLocation

    def SetEmbeddedWindowLocation(self, embeddedWindowLocation):
        self._embeddedWindowLocation = embeddedWindowLocation

    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        self._frame = frame
        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))
        menuItemPos = self.GetMenuItemPos(viewMenu, viewMenu.FindItem(_("&Status Bar"))) + 1

        viewMenu.InsertCheckItem(menuItemPos, self.SHOW_WINDOW, self.GetMenuString(), self.GetMenuDescr())
        wx.EVT_MENU(frame, self.SHOW_WINDOW, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, self.SHOW_WINDOW, frame.ProcessUpdateUIEvent)
        return True

    def GetServiceName(self):
        """ String used to save out Service View configuration information """
        return self._serviceName

    def GetMenuString(self):
        """ Need to override this method to provide menu item for showing Service View """
        return _(self.GetServiceName())

    def GetMenuDescr(self):
        """ Need to override this method to provide menu item for showing Service View """
        return _("Show or hides the %s window") % self.GetMenuString()
    #----------------------------------------------------------------------------
    # Event Processing Methods
    #----------------------------------------------------------------------------

    def ProcessEvent(self, event):
        id = event.GetId()
        if id == self.SHOW_WINDOW:
            self.ToggleWindow(event)
            return True
        else:
            return False

    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == self.SHOW_WINDOW:
            event.Check(self._view != None and self._view.IsShown())
            event.Enable(True)
            return True
        else:
            return False

    #----------------------------------------------------------------------------
    # View Methods
    #----------------------------------------------------------------------------
    def _CreateView(self):
        """ This method needs to be overridden with corresponding ServiceView """
        return ServiceView(self)

    def GetView(self):
        # Window Menu Service Method
        return self._view

    def SetView(self, view):
        self._view = view

    def ShowWindow(self, show = True):
        if show:
            if self._view:
                if not self._view.IsShown():
                    self._view.Show()
            else:
                view = self._CreateView()
                self.SetView(view)
                view.OnCreate(None, flags = 0)
        else:
            if self._view:
                if self._view.IsShown():
                    self._view.Hide()
        self._frame._mgr.Update()

    def HideWindow(self):
        self.ShowWindow(False)

    def ToggleWindow(self, event):
        show = event.IsChecked()
        wx.ConfigBase_Get().WriteInt(self.GetServiceName()+"Shown", show)
        self.ShowWindow(show)

    def OnCloseFrame(self, event):
        if not self._view:
            return True

        if wx.GetApp().IsMDI():
            self._view.OnCloseWindow(event)
        # This is called when any SDI frame is closed, so need to check if message window is closing or some other window
        elif self._view == event.GetEventObject().GetView():
            self.SetView(None)
        return True
        
    def GetIcon(self):
        if self._icon_path is None:
            return None
        return images.load(self._icon_path)
        
    def GetTargetPane(self,dock_direction):
        nb_pane = self.AuiManager.GetNotebookPaneDirection(dock_direction)
        if nb_pane is None:
            #get any dock_direction pane as the target pane
            return self.AuiManager.GetAnyPane(dock_direction)
        nb = nb_pane.window
        if 0 == nb._tabs.GetPageCount():
            return None
        window = nb.GetPage(0)
        pane = self.AuiManager.GetPane(window)
        return pane
        
    def CreatePane(self,dock_direction,target=None,control = None,caption='',name='',icon=None,minSize=80):
        frameSize = self._frame.GetSize()   # TODO: GetClientWindow.GetSize is still returning 0,0 since the frame isn't fully constructed yet, so using full frame size
        defaultHSize = max(minSize, int(frameSize[0] / 6))
        defaultVSize = max(minSize, int(frameSize[1] / 7))
        
        if caption == '':
            caption = self.GetMenuString()
        if name == '':
            name = self.GetServiceName()
        if dock_direction == aui.AUI_DOCK_BOTTOM:
            if None == target:
                pane_info = aui.TabPaneFrame().Name(name).Caption(caption)\
                        .BestSize(wx.Size(-1,defaultVSize)).MinSize(wx.Size(-1,minSize))\
                        .Bottom().Layer(1).Position(1).MinimizeButton(True)
            else:
                pane_info = aui.TabPaneFrame().Name(name).Caption(caption).Bottom().\
                                    MinSize(wx.Size(-1,minSize)).MinimizeButton(True)
                                    
        elif dock_direction == aui.AUI_DOCK_RIGHT:
            pane_info = aui.TabPaneFrame().Name(name).Caption(caption)\
                            .BestSize(wx.Size(defaultHSize,-1)).MinSize(wx.Size(minSize,-1))\
                            .Right().MinimizeButton(True)
        elif dock_direction == aui.AUI_DOCK_LEFT:
            pane_info = aui.TabPaneFrame().Name(name).Caption(caption).Left().Layer(1)\
                    .BestSize(wx.Size(defaultHSize,-1)).MinSize(wx.Size(minSize,-1))\
                    .Position(1).MinimizeButton(True)
        
        view_control = self.GetView().GetControl()
        if view_control == None:
            view_control = control
        assert(view_control != None)
        if icon is None:
            icon = self.GetIcon()
        #shoud set pane icon before addpane
        if icon != None:
            pane_info.Icon(icon)
        self.AuiManager.AddPane(view_control, pane_info, target=target)
        return pane_info
        
    @property
    def AuiManager(self):
        return self._frame._mgr

    @classmethod
    def GetNoteBook(cls,dock_direction):
        nb_pane = wx.GetApp().MainFrame._mgr.GetNotebookPaneDirection(dock_direction)
        if nb_pane is None:
            return None
        nb = nb_pane.window
        return nb

    @classmethod
    def GetBottomTab(cls):
        nb = cls.GetNoteBook(aui.AUI_DOCK_BOTTOM)
        if nb is None:
            None
        return nb
        
    def SwitchtoTabPage(self):
        bottom_tab = self.GetBottomTab()
        if bottom_tab is None:
            return
        for i in range(bottom_tab.GetPageCount()):
            if bottom_tab.GetPage(i) == self.GetView()._control:
                bottom_tab.SetSelection(i)
                break