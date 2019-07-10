# -*- coding: utf-8 -*-
from noval import GetApp,_,Locale
from tkinter import messagebox
import os
import noval.util.apputils as sysutilslib
import xml.etree.ElementTree as ET
import noval.generalopt as generalopt
from bz2 import BZ2File
import noval.util.fileutils as fileutils
import noval.syntax.syntax as syntax
import noval.util.appdirs as appdirs
import copy
import uuid
import tarfile
import tempfile
import noval.ui_base as ui_base
import noval.consts as consts
import noval.util.utils as utils
import noval.util.compat as compat

class NewFileDialog(ui_base.SingleChoiceDialog):
    def __init__(self,parent,title,folderPath):
        self.file_templates = []
        self.LoadFileTemplates()
        names = self.GetTemplateNames()
        ui_base.SingleChoiceDialog.__init__(self,parent,title,_("Select a new document template:"),names)
        current_project_document = GetApp().MainFrame.GetProjectView(generate_event=False).GetCurrentProject()
        project_path = os.path.dirname(current_project_document.GetFilename())
        self.dest_path = project_path
        if folderPath != "":
            self.dest_path = os.path.join(self.dest_path,folderPath)
        if sysutilslib.is_windows():
            self.dest_path = self.dest_path.replace("/",os.sep)

    def GetTemplateNames(self):
        names = []
        for file_template in self.file_templates:
            if syntax.SyntaxThemeManager().IsExtSupported(file_template['Ext']):
                names.append(file_template['Name'])
        return names

    def GetTemplate(self,name):
        for file_template in self.file_templates:
            if name == file_template['Name']:
                return file_template
        return None

    def _ok(self,event=None):            
        index = self.listbox.curselection()[0]
        if index == -1:
            wx.MessageBox(_("You don't select any item"))
            return
        self.selection = self.GetStringSelection()
        file_template = self.GetTemplate(self.selection)
        default_name = file_template.get('DefaultName',None)
        if default_name is None:
            default_name = "Untitle" + file_template.get('Ext')
        content = file_template['Content'].strip()
        content_zip_path = fileutils.opj(os.path.join(sysutilslib.mainModuleDir,content))
        if not os.path.exists(content_zip_path):
            content_zip_path = fileutils.opj(os.path.join(appdirs.get_user_data_path(),content))
        name,ext = os.path.splitext(default_name)
        i = 1
        while True:
            file_name = "%s%d%s" % (name,i,ext)
            self.file_path = os.path.join(self.dest_path,file_name)
            if not os.path.exists(self.file_path):
                break
            i += 1
        try:
            with open(self.file_path,"w") as fp:
                try:
                    with BZ2File(content_zip_path,"r") as f:
                        for i,line in enumerate(f):
                            if i == 0:
                                continue
                            if utils.is_py3_plus():
                                line = compat.ensure_string(line)
                            fp.write(line.strip('\0').strip('\r').strip('\n'))
                            fp.write('\n')
                except Exception as e:
                    messagebox.showerror(GetApp().GetAppName(),_("Load File Template Content Error.%s") % e)
                    utils.get_logger().exception('')
                    return
        except Exception as e:
            messagebox.showerror(GetApp().GetAppName(),_("New File Error.%s") % e)
            return
        ui_base.SingleChoiceDialog._ok(self)
        
    def GetFileTypeTemplate(self,node):
        file_type = {}
        for item in node.getchildren():
            if item.tag == "Icon":
                try:
                    small_path = item.get('Small',"")
                    if os.path.isabs(small_path):
                        small_icon_path = small_path
                    else:
                        small_icon_path = os.path.join(sysutilslib.mainModuleDir,small_path)
                    file_type['SmallIconPath'] = small_icon_path
                    if not os.path.exists(small_icon_path):
                        small_icon_path = os.path.join(sysutilslib.mainModuleDir,"noval/tool/bmp_source/template/default-small.bmp")
                    small_icon = wx.Image(small_icon_path, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
                    index = self.small_iconList.AddWithColourMask(small_icon,COMMON_MASK_COLOR)
                    large_path = item.get('Large',"")
                    if os.path.isabs(large_path):
                        large_icon_path = large_path
                    else:
                        large_icon_path = os.path.join(sysutilslib.mainModuleDir,large_path)
                    file_type['LargeIconPath'] = large_icon_path
                    if not os.path.exists(large_icon_path):
                        large_icon_path = os.path.join(sysutilslib.mainModuleDir,"noval/tool/bmp_source/template/default.bmp")
                    large_icon = wx.Image(large_icon_path, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
                    index = self.large_iconList.AddWithColourMask(large_icon,COMMON_MASK_COLOR)
                    file_type['ImageIndex'] = index
                except Exception as e:
                    #print e
                    continue
            else:
                file_type[item.tag] = item.text
        return file_type
        
    def LoadFileTemplates(self):
        user_template_path = os.path.join(appdirs.get_user_data_path(),consts.USER_CACHE_DIR,consts.TEMPLATE_FILE_NAME)
        sys_template_path = os.path.join(appdirs.get_app_path(), consts.TEMPLATE_FILE_NAME)
        if os.path.exists(user_template_path):
            file_template_path = user_template_path
        elif os.path.exists(sys_template_path):
            file_template_path = sys_template_path
        else:
            return
        self.LoadFromFileTemplate(file_template_path)
        #if load template fail,load template from default path
        if 0 == len(self.file_templates):
           self.LoadFromFileTemplate(sys_template_path)
            
    def LoadFromFileTemplate(self,file_template_path):
        try:
            tree = ET.parse(file_template_path)
            doc = tree.getroot()
        except Exception as e:
            messagebox.showerror(GetApp().GetAppName(),_("Load Template File Error.%s") % e)
            return
        langId = utils.profile_get_int(consts.LANGUANGE_ID_KEY,-1)
        if langId != -1:
            lang = Locale(langId).GetLanguageCanonicalName()
        else:
            lang = "en_US"
        self.LoadLangTemplate(doc,lang)
        #如果未找到该语言对应的模板,默认加载英语模板
        if 0 == len(self.file_templates):
            self.LoadLangTemplate(doc,"en_US")

    def LoadLangTemplate(self,doc,lang):
        for element in doc.getchildren():
            if element.tag == lang:
                for node in element.getchildren():
                    value_type = node.get('value')
                    for child in node.getchildren():
                        file_type = self.GetFileTypeTemplate(child)
                        file_type.update({
                            'Category':value_type
                        })
                        self.file_templates.append(file_type)
                    