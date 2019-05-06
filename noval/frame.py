# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        frame.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-16
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import GetApp,constants,_,NewId,consts
import os
import tkinter as tk
from tkinter import ttk
import noval.toolbar as toolbar
import noval.ui_common as ui_common
from noval.editor import notebook
import noval.plugin as plugin
import noval.plugin_joint as plugin_joint
import noval.util.utils as utils
import noval.statusbar as statusbar
        
class DocTabbedParentFrame(ttk.Frame):

    def __init__(self, parent,docManager, frame, id, title, direction):
        GetApp().frame = self
        ttk.Frame.__init__(self,parent)
        self.grid(row=1, column=0, sticky=direction)
        self.CreateToolBar()
        self._main_pw = ui_common.AutomaticPanedWindow(self, orient=tk.HORIZONTAL)
        #padx和pady为设置主框架的左右和上下边距,设置主框架水平垂直2个方向拉伸
        self._main_pw.grid(column=0, row=consts.DEFAULT_MAIN_FRAME_ROW, sticky=tk.NSEW, padx=0, pady=0)
        self.CreateDefaultStatusBar()
        self.columnconfigure(0, weight=1)
        #设置第二行,即主框架所在的行权重为1,即填充满
        self.rowconfigure(consts.DEFAULT_MAIN_FRAME_ROW, weight=1)
        self._views = {}

        self._west_pw = ui_common.AutomaticPanedWindow(
            self._main_pw,
            1,
            orient=tk.VERTICAL,
            preferred_size_in_pw=400,
        )
        self._center_pw = ui_common.AutomaticPanedWindow(self._main_pw, 2, orient=tk.VERTICAL)
        self._east_pw = ui_common.AutomaticPanedWindow(
            self._main_pw,
            3,
            orient=tk.VERTICAL,
            preferred_size_in_pw=400,
        )
        
        self._view_notebooks = {
            "nw": ui_common.AutomaticNotebook(
                self._west_pw,
                1,
                preferred_size_in_pw=utils.profile_get_int("layout.nw_nb_height",500),
            ),
            "w": ui_common.AutomaticNotebook(self._west_pw, 2),
            "sw": ui_common.AutomaticNotebook(
                self._west_pw,
                3,
                preferred_size_in_pw=utils.profile_get_int("layout.sw_nb_height",500),
            ),
            "s": ui_common.AutomaticNotebook(
                self._center_pw,
                3,
                preferred_size_in_pw=utils.profile_get_int("layout.s_nb_height",500),
            ),
            "ne": ui_common.AutomaticNotebook(
                self._east_pw,
                1,
                preferred_size_in_pw=utils.profile_get_int("layout.ne_nb_height",500),
            ),
            "e": ui_common.AutomaticNotebook(self._east_pw, 2),
            "se": ui_common.AutomaticNotebook(
                self._east_pw,
                3,
                preferred_size_in_pw=utils.profile_get_int("layout.se_nb_height",500),
            ),
        }
        self.CreateNotebook()
        self._current_document = None
        self._plugin_handlers = dict(menu=list(), ui=list())
    
    def CreateDefaultStatusBar(self):
        sep = ttk.Frame(self, height=1, borderwidth=1)
        sep.grid(column=0, row=consts.DEFAULT_STATUS_BAR_ROW-1, sticky=tk.EW, padx=0, pady=0)
        self.status_bar = statusbar.MultiStatusBar(self,height=16,borderwidth=1)
        self.status_bar.Show(self.status_bar.IsDefaultShown())
        #先创建状态栏文本控件,支撑状态栏高度
        self.status_bar.set_label(consts.STATUS_BAR_LABEL_COL, 'Col: ?', side=tk.RIGHT)
        self.status_bar.set_label(consts.STATUS_BAR_LABEL_LINE, 'Ln: ?', side=tk.RIGHT)
        #初始时将状态栏所有文本显示空
        self.status_bar.Reset()
       
    def CreateToolBar(self):
        self._toolbar = toolbar.ToolBar(self)
        self._toolbar.Show(self._toolbar.IsDefaultShown())
       
    def GetToolBar(self):
        return self._toolbar
        
    def GetStatusBar(self):
        return self.status_bar

    def AddToolbarButton(self,command_id,image,command_label,handler,accelerator,tester):
        self._toolbar.AddButton(command_id,image,command_label,handler,accelerator,tester)
                        
    def MaximizeEditorWindow(self,event):
        
        is_maximized = True
        for pane in self._mgr.GetAllPanes():
            if pane.name == consts.EDITOR_CONTENT_PANE_NAME or pane.name == consts.TOOLBAR_PANE_NAME or not pane.IsShown() or \
                    pane.IsNotebookPage() or isinstance(pane.window,aui.auibar.AuiToolBar):
                continue
            if not pane.IsMinimized():
                is_maximized = False
                break
        if not is_maximized:
            self._perspective = self._mgr.SavePerspective()
        all_panes = self._mgr.GetAllPanes()
        for pane in all_panes:
            if pane.name == consts.EDITOR_CONTENT_PANE_NAME or pane.IsMinimized() or pane.name == consts.TOOLBAR_PANE_NAME or \
                    pane.IsNotebookPage() or not pane.IsShown() or isinstance(pane.window,aui.auibar.AuiToolBar):
                continue
            self._mgr.MinimizePane(pane)
        
    def RestoreEditorWindow(self,event):
        if self._perspective is None:
            return
        self._mgr.LoadPerspective(self._perspective)
        
    def CreateNotebook(self):
        self._editor_notebook = notebook.EditorNotebook(self._center_pw)
        self._editor_notebook.position_key = 1  # type: ignore
        self._center_pw.insert("auto", self._editor_notebook)
        
    def GetNotebook(self):
        return self._editor_notebook

    def AddNotebookPage(self, panel, title,filename):
        """
        Adds a document page to the notebook.
        """
        template = panel.GetView().GetDocument().GetDocumentTemplate()
        img = template.GetIcon()
        self._editor_notebook.add(panel, text=title,image=img,compound=tk.LEFT)
       # windowMenuService = wx.GetApp().GetService(wx.lib.pydocview.WindowMenuService)
        #if windowMenuService:
         #   windowMenuService.BuildWindowMenu(wx.GetApp().GetTopWindow())  # build file menu list when we open a file

    def SetNotebookPageTitle(self, panel, title):
        self._editor_notebook.update_editor_title(panel,title)
        panel.SetFocus()
        
    def GetNotebookPageTitle(self,panel):
        return self._editor_notebook.tab(panel)['text']

    def ActivateNotebookPage(self,child_frame):
        self._editor_notebook.select(child_frame)
        child_frame.GetView().SetFocus()

    def InitPlugins(self):
        # Setup Plugins after locale as they may have resource that need to be loaded.
        plgmgr = plugin.PluginManager()
        GetApp().SetPluginManager(plgmgr)
        main_window_addon = plugin_joint.MainWindowAddOn(plgmgr)
        main_window_addon.Init(self)
        
        common_plugin_loader = plugin_joint.CommonPluginLoader(plgmgr)
        common_plugin_loader.Load()
        #self._plugin_handlers['menu'].extend(addons.GetEventHandlers())
        #self._plugin_handlers['ui'].extend(addons.GetEventHandlers(ui_evt=True))
        #self.InitPluginMenus()

    def InitPluginMenus(self):
        for menu_item_command in self._plugin_handlers['menu']:
            wx.EVT_MENU(self, menu_item_command[0], menu_item_command[1])
            
        for menu_update_item_command in self._plugin_handlers['ui']:
            wx.EVT_UPDATE_UI(self, menu_update_item_command[0], menu_update_item_command[1])
            
    def RemoveNotebookPage(self,panel):
        self._editor_notebook.close_editor(panel)
        
    def CloseDoc(self):
        editor = self._editor_notebook.get_current_editor()
        if editor is None:
            return
        doc = editor.GetView().GetDocument()
        doc.DeleteAllViews()
        
    def CloseAllDocs(self):
        self._editor_notebook.CloseAllWithoutDoc(closeall=True)

    def CloseWindows(self):
        return True

    def _InitCommands(self):
        
        GetApp().AddCommand(constants.ID_VIEW_TOOLBAR,main_menu_name=_("&View"),command_label=_("&Toolbar"),\
                            handler=self.OnViewToolBar,kind = consts.CHECK_MENU_ITEM_KIND,variable=self._toolbar.visibility_flag)
        GetApp().AddCommand(constants.ID_VIEW_STATUSBAR,main_menu_name=_("&View"),command_label=_("&Status Bar"),\
                            handler=self.OnViewStatusBar,kind = consts.CHECK_MENU_ITEM_KIND,variable=self.status_bar.visibility_flag)

        # TODO: do these commands have to be in EditorNotebook ??
        # Create a module level function install_editor_notebook ??
        # Maybe add them separately, when notebook has been installed ??
        ##tk已经默认绑定常见文本编辑快捷键,这里不需要再次绑定,否则会执行2次
        GetApp().AddCommand(constants.ID_UNDO,_("&Edit"),_("&Undo"),self.CreateEditCommandHandler("<<Undo>>"),image="toolbar/undo.png",default_tester=True,default_command=True,skip_sequence_binding=True)
        GetApp().AddCommand(constants.ID_REDO,_("&Edit"),_("&Redo"),self.CreateEditCommandHandler("<<Redo>>"),image="toolbar/redo.png",add_separator=True,default_tester=True,default_command=True,skip_sequence_binding=True)
        GetApp().AddCommand(constants.ID_CUT,_("&Edit"),_("&Cut"),self.CreateEditCommandHandler("<<Cut>>"),image="toolbar/cut.png",include_in_toolbar=True,default_tester=True,default_command=True,skip_sequence_binding=True)
        GetApp().AddCommand(constants.ID_COPY,_("&Edit"),_("&Copy"),self.CreateEditCommandHandler("<<Copy>>"),image="toolbar/copy.png",include_in_toolbar=True,default_tester=True,default_command=True,skip_sequence_binding=True)
        GetApp().AddCommand(constants.ID_PASTE,_("&Edit"),_("&Paste"),self.CreateEditCommandHandler("<<Paste>>"),image="toolbar/paste.png",include_in_toolbar=True,default_tester=True,default_command=True,skip_sequence_binding=True)
        #文本默认绑定了ctrl+d事件,需要解除并从新绑定快捷键事件
        GetApp().AddCommand(constants.ID_CLEAR,_("&Edit"),_("&Delete"),handler=lambda:self.OnDelete(),image="delete.png",\
                            default_tester=True,default_command=True,extra_sequences=["<<CtrlDInText>>"])
        GetApp().AddCommand(constants.ID_SELECTALL,_("&Edit"),_("Select A&ll"),self.SelectAll,add_separator=True,default_tester=True,default_command=True,skip_sequence_binding=True)

        undo_menu_item = GetApp().Menubar.GetEditMenu().FindMenuItem(constants.ID_UNDO)
        self.AddToolbarButton(constants.ID_UNDO,undo_menu_item.image,undo_menu_item.label,\
                                            self.CreateEditCommandHandler("<<Undo>>"),undo_menu_item.accelerator,tester=lambda:GetApp().UpdateUI(constants.ID_UNDO))
                                            
        redo_menu_item = GetApp().Menubar.GetEditMenu().FindMenuItem(constants.ID_REDO)
        self.AddToolbarButton(constants.ID_REDO,redo_menu_item.image,redo_menu_item.label,\
                                            self.CreateEditCommandHandler("<<Redo>>"),redo_menu_item.accelerator,tester=lambda:GetApp().UpdateUI(constants.ID_REDO))
                                            

        self.GetNotebook()._InitCommands()
        #在此处初始化插件
        self.InitPlugins()
        self.GetProjectView()._InitCommands()
                                            

    def CreateEditCommandHandler(self,virtual_event_sequence):
        def handler(event=None):
            widget = GetApp().focus_get()
            #如果是工具栏的编辑按钮,则切换到当前视图下面的控件
            if isinstance(widget,ttk.Button):
                current_active_view = GetApp().GetDocumentManager().GetCurrentView()
                widget = current_active_view.GetCtrl()
            if widget:
                return widget.event_generate(virtual_event_sequence)
            return None
            
        return handler

    def SelectAll(event=None):
        # Tk 8.6 has <<SelectAll>> virtual event, but 8.5 doesn't
        widget = GetApp().focus_get()
        if isinstance(widget, tk.Text):
            widget.tag_remove("sel", "1.0", "end")
            widget.tag_add("sel", "1.0", "end")
        elif isinstance(widget, (ttk.Entry, tk.Entry)):
            widget.select_range(0, tk.END)
            
    def OnDelete(self):
        self.GetNotebook().get_current_editor().GetView().GetCtrl().OnDelete()
            
    def AddView(self,view_name,cls,label,default_location,default_position_key=None,create=True,\
                visible_by_default=False,image_file=None):
        """Adds item to "View" menu for showing/hiding given view. 
        Args:
            view_class: Class or constructor for view. Should be callable with single
                argument (the master of the view)
            label: Label of the view tab
            location: Location descriptor. Can be "nw", "sw", "s", "se", "ne"
        Returns: None        
        """        
        is_visibile = utils.profile_get_int(consts.FRAME_VIEW_VISIBLE_KEY % view_name,visible_by_default)
        visibility_flag = tk.BooleanVar(value=bool(is_visibile))
        image = None
        if image_file is not None:
            image = GetApp().GetImage(image_file)
        self._views[view_name] = {
            "class": cls,
            "label": label,
            "location": default_location,
            "position_key": default_position_key,
            "visibility_flag": visibility_flag,
            'image':image
        }

        # handler
        def toggle_view_visibility():
            visibility_flag_ = self._views[view_name]['visibility_flag']
            if visibility_flag_.get():
                self.ShowView(view_name)
            else:
                self.ShowView(view_name,False,hidden=True)
        GetApp().InsertCommand(consts.ID_VIEW_STATUSBAR,view_name,main_menu_name=_("&View"),command_label=label,handler=toggle_view_visibility,\
                        kind = consts.CHECK_MENU_ITEM_KIND,variable=visibility_flag)
        if create:
            self.ShowView(view_name,hidden = not is_visibile)

    def ShowView(self, view_name, set_focus=True,hidden=False,toogle_visibility_flag = False,generate_event=True):
        """View must be already registered.
        
        Args:
            view_id: View class name 
            without package name (eg. 'ShellView') """

        # NB! Don't forget that view.home_widget is added to notebook, not view directly
        # get or create
        view = self.GetView(view_name)
        notebook = view.home_widget.master  # type: ignore
        
        if not hidden:
            if hasattr(view, "before_show") and view.before_show() == False:  # type: ignore
                return False
            kw = {'text':self._views[view_name]["label"]}
            if self._views[view_name]["image"] is not None:
                kw.update({'image':self._views[view_name]["image"],'compound':tk.LEFT})
            if view.hidden:  # type: ignore
                notebook.insert(
                    "auto",
                    view.home_widget,  # type: ignore
                    **kw
                )
                view.hidden = False  # type: ignore

            # switch to the tab
            notebook.select(view.home_widget)  # type: ignore
            # add focus
            if set_focus:
                view.focus_set()
            #设置视图复选菜单选中
            if toogle_visibility_flag:
                self._views[view_name]['visibility_flag'].set(True)
        else:
            if not view.hidden:
                notebook.forget(view.home_widget)
               # self.set_option("view." + view_id + ".visible", False)
              #  self.event_generate("HideView", view=view, view_id=view_id)
                view.hidden = True
                #设置视图复选菜单取消选中
                if toogle_visibility_flag:
                    self._views[view_name]['visibility_flag'].set(False)
        if generate_event:
            GetApp().event_generate("ShowView", view=view, view_name=view_name,show=not hidden)
        return view
        
    def GetView(self, view_name):
        if "instance" not in self._views[view_name]:
            class_ = self._views[view_name]["class"]
            location = self._views[view_name]["location"]
            master = self._view_notebooks[location]
            home_widget = ttk.Frame(master)
            # create the view
            view = class_(
                home_widget
            )  # View's master is workbench to allow making it maximized
            #设置视图在notebook中的位置顺序,如果放置在最后则设置为None
            view.position_key = self._views[view_name]["position_key"]
            self._views[view_name]["instance"] = view

            # create the view home_widget to be added into notebook
            view.home_widget = home_widget
            view.home_widget.columnconfigure(0, weight=1)
            view.home_widget.rowconfigure(0, weight=1)
          ###  view.home_widget.maximizable_widget = view  # type: ignore
            #关闭窗口事件,同时修改菜单选中状态
            view.home_widget.close = lambda: self.ShowView(view_name,False,hidden=True,toogle_visibility_flag=True)  # type: ignore
            if hasattr(view, "position_key"):
                view.home_widget.position_key = view.position_key  # type: ignore

            # initially the view will be in it's home_widget
            view.grid(row=0, column=0, sticky=tk.NSEW, in_=view.home_widget)
            view.hidden = True

        return self._views[view_name]["instance"]
        
    def SaveLayout(self):
        ##TODO 测试此处代码BUG,测试完成后要删除
        try:
            utils.profile_set(self._toolbar.GetToolbarKey(), self._toolbar.IsShown())
            utils.profile_set(self.status_bar.GetStatusbarKey(), self.status_bar.IsShown())
            for view_name in self._views:
                visibility_flag = self._views[view_name]['visibility_flag']
                utils.profile_set(consts.FRAME_VIEW_VISIBLE_KEY % view_name,visibility_flag.get())
        except:
            print (self._toolbar.GetToolbarKey(), self._toolbar.IsShown())
            print (self.status_bar.GetStatusbarKey(), self.status_bar.IsShown())
            for view_name in self._views:
                visibility_flag = self._views[view_name]['visibility_flag']
                print (view_name,visibility_flag.get(),"===================")
                utils.profile_set(consts.FRAME_VIEW_VISIBLE_KEY % view_name,visibility_flag.get())
                print (k)
            
    def IsViewShown(self,view_name):
        visibility_flag = self._views[view_name]['visibility_flag']
        return visibility_flag.get()
        
    def OnViewToolBar(self):
        """
        Toggles whether the ToolBar is visible.
        """
        self.GetToolBar().Show(not self._toolbar.IsShown())

    def OnViewStatusBar(self):
        """
        Toggles whether the StatusBar is visible.
        """
        self.GetStatusBar().Show(not self.GetStatusBar().IsShown())
        
    def UpdateToolbar(self):
        if not hasattr(self, "_toolbar"):
            return
        self._toolbar.Update()
        
    def GetProjectView(self,show=False,generate_event=True):
        #只有在软件启动时才需要发送事件,以便加载项目
        frame_view = self.GetView(consts.PROJECT_VIEW_NAME)
        if show:
            self.ShowView(consts.PROJECT_VIEW_NAME,toogle_visibility_flag=True,generate_event=generate_event)
        return frame_view
        
    def GetSearchresultsView(self,show=True):
        return self.GetCommonView(consts.SEARCH_RESULTS_VIEW_NAME,show)
        
    def GetCommonView(self,view_name,show=True):
        frame_view = self.GetView(view_name)
        if show:
            self.ShowView(view_name,toogle_visibility_flag=True)
        return frame_view
        
    def GetOutlineView(self,show=False):
        return self.GetCommonView(consts.OUTLINE_VIEW_NAME,show)
        
    def GetCurrentView(self):
        editor = self.GetNotebook().get_current_editor()
        if editor is None:
            return None
        return editor.GetView()
        
    @utils.call_after
    def PushStatusText(self,msg,label=""):
        self.GetStatusBar().PushStatusText(msg,label)
        
 
    