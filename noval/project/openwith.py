# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        openwith.py
# Purpose:     文件打开方式对话框
#
# Author:      Administrator
#
# Created:     2020-03-13
# Copyright:   (c) Administrator 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from noval import GetApp,_
import noval.ui_base as ui_base
import os
from tkinter import ttk
import noval.util.strutils as strutils
import tkinter as tk
import noval.util.utils as utils
from noval.ttkwidgets.treeviewframe import TreeViewFrame
from noval.editor import text as texteditor
import noval.consts as consts

class EditorSelectionDlg(ui_base.CommonModaldialog):
    
    OPEN_WITH_PATH = 1
    OPEN_WITH_NAME = 2
    OPEN_WITH_EXTENSION = 3
    def __init__(self,parent,item_file,project_document):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(_("Editor Selection"))
        self._item_file = item_file
        self._file_path = item_file.filePath
        self._open_with_mode = self.OPEN_WITH_PATH
        self._is_changed = False
        ttk.Label(self.main_frame,text=_("Choose an editor you want to open") \
                                   + " '%s':" % os.path.basename(self._file_path)).pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,\
                                                            pady=consts.DEFAUT_CONTRL_PAD_Y)
        tree_view = TreeViewFrame(self.main_frame,treeview_class=ttk.Treeview,)
        self.tree = tree_view.tree
        tree_view.pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.tree.bind("<Double-Button-1>", self._ok, "+")
        self.templates = self.GetTemplates()
        document_template_name = utils.profile_get(project_document.GetFileKey(self._item_file,"Open"),"")
        filename = os.path.basename(self._file_path)
        if not document_template_name:
            document_template_name = utils.profile_get("Open/filenames/%s" % filename,"")
            if not document_template_name:
                document_template_name = utils.profile_get("Open/extensions/%s" % strutils.get_file_extension(filename),"")
                if document_template_name:
                    self._open_with_mode = self.OPEN_WITH_EXTENSION
            else:
                self._open_with_mode = self.OPEN_WITH_NAME
                
        self._document_template_name = document_template_name
        for i,temp in enumerate(self.templates):
            show_name = temp.GetViewName()
            if 0 == i:
                show_name += (" (" + _("Default") + ")")
            item = self.tree.insert("","end",text=show_name ,image=temp.GetIcon())
            if document_template_name == temp.GetDocumentName():
                self.tree.selection_set(item)
        if document_template_name == "":
            self._document_template_name = self.templates[0].GetDocumentName()
            self.tree.selection_set(self.tree.get_children()[0])
         
        self.val = tk.IntVar(value=self._open_with_mode)   
        ttk.Radiobutton(self.main_frame,value=self.OPEN_WITH_NAME,variable=self.val,text=_("Use this editor for all files named") + " '%s'" % os.path.basename(self._file_path))\
                .pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        ext = strutils.get_file_extension(os.path.basename(self._file_path))
        if ext != "":
            ttk.Radiobutton(self.main_frame,value=self.OPEN_WITH_EXTENSION,variable=self.val,text=_("Use it for all files with extension") + " '.%s'" % ext)\
                .pack(fill="x",padx=consts.DEFAUT_CONTRL_PAD_X)
        self.AddokcancelButton()
        
    def GetTemplates(self):
        templates = []
        default_template = GetApp().GetDocumentManager().FindTemplateForPath(self._file_path)
        #默认模板不可见,使用文本模板
        if not default_template.IsVisible():
            default_template = GetApp().GetDocumentManager().FindTemplateForPath("test.txt")
        for temp in GetApp().GetDocumentManager().GetTemplates():
            want = False
            if temp.IsVisible() and temp.GetViewName() and temp != default_template:
                want = True
            elif not temp.IsVisible() and temp.GetDocumentType() != texteditor.TextDocument:
                want = True
            if want:
                templates.append(temp)
        templates.insert(0,default_template)
        return templates
        
    @property
    def Openwith(self):
        return self._open_with_mode
        
    def _ok(self,event=None):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(GetApp().GetAppName(),_("Please choose one editor"),main=self)
            return
        self.selected_template = self.templates[self.tree.get_children().index(selection[0])]
        self._is_changed = False if self._open_with_mode == self.val.get() else True
        if not self._is_changed:
            self._is_changed =  False if self._document_template_name == self.selected_template.GetDocumentName() else True
        self._open_with_mode = self.val.get()
        ui_base.CommonModaldialog._ok(self,event)
 