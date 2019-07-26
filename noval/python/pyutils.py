# -*- coding: utf-8 -*-
from noval import GetApp,_
from tkinter import messagebox
import sys
import os
import noval.consts as consts
import noval.ui_utils as ui_utils
import noval.ttkwidgets.treeviewframe as treeviewframe
import noval.ui_base as ui_base
import noval.syntax.syntax as syntax
import noval.syntax.lang as lang
import noval.imageutils as imageutils
import noval.util.strutils as strutils
import noval.util.fileutils as fileutils
from noval.project.basebrowser import ProjectTreeCtrl

def get_tk_version_str():
    tkVer = GetApp().call('info', 'patchlevel')
    return tkVer
    
def get_python_version_string():
    version_info = sys.version_info
    result = ".".join(map(str, version_info[:3]))
    if version_info[3] != "final":
        result += "-" + version_info[3]
    result += " (" + ("64" if sys.maxsize > 2 ** 32 else "32") + " bit)\n"
    return result
    
def update_pythonpath_env(env,pythonpath):
    if type(pythonpath) == list:
        pathstr = os.pathsep.join(pythonpath)
    else:
        pathstr = pythonpath
    env[consts.PYTHON_PATH_NAME] = env[consts.PYTHON_PATH_NAME] + os.pathsep + pathstr
    return env

def get_override_runparameter(run_parameter):
    interpreter = run_parameter.Interpreter
    environment = run_parameter.Environment
    environ = interpreter.Environ.GetEnviron()
    if consts.PYTHON_PATH_NAME in environ and environment is not None:
        environ = update_pythonpath_env(environ,environment.get(consts.PYTHON_PATH_NAME,''))
    environ = ui_utils.update_environment_with_overrides(environ)

    interpreter_specific_keys = [
        "TCL_LIBRARY",
        "TK_LIBRARY",
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "PYTHONHOME",
        "PYTHONNOUSERSITE",
        "PYTHONUSERBASE",
    ]
    if len(environ) > 0:
        if environment is None:
            environment = environ
        else:
            environment.update(environ)

    #软件安装路径下面的tk版本和解释器自带的tk版本会混淆,故必须去除系统环境变量中类似TCL_LIBRARY,TK_LIBRARY的变量
    #如果不去除会出现如下类似错误:
    #version conflict for package "Tcl": have 8.5.15, need exactly 8.6.6
    #TODO:必须去除的变量为TCL_LIBRARY,TK_LIBRARY,其它变量是否必须去除待定
    for key in interpreter_specific_keys:
        if key in os.environ:
            del environment[key]
        #in windows and if is python3 interpreter ,shoud add 'SYSTEMROOT' Environment Variable
        #othersise it will raise progblem below when add a Environment Variable
        #Fatal Python error: failed to get random numbers to initialize Python
       # if sysutilslib.isWindows() and interpreter.IsV3():
        #    SYSTEMROOT_KEY = 'SYSTEMROOT'
         #   if not environment.has_key(SYSTEMROOT_KEY):
          #      environment[SYSTEMROOT_KEY] = os.environ[SYSTEMROOT_KEY]
    #add python path to env
    if len(interpreter.PythonPathList) > 0:
        environment = update_pythonpath_env(environment,interpreter.PythonPathList)
    if run_parameter.Environment == environment:
        return run_parameter
    else:
        save_interpreter = run_parameter.Interpreter
        run_parameter.Interpreter = None
        cp_run_parameter = copy.deepcopy(run_parameter)
        cp_run_parameter.Environment = environment
        run_parameter.Interpreter = save_interpreter
        return cp_run_parameter

class ProjectFolderPathDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title,project_model):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
        self._current_project = project_model
        rootPath = project_model.homeDir
        self.treeview = treeviewframe.TreeViewFrame(self.main_frame,treeview_class=ProjectTreeCtrl)
        self.treeview.tree["show"] = ("tree",)
        self.treeview.pack(fill="both",expand=1)
        self.folder_bmp = imageutils.load_image("","packagefolder_obj.gif")
        root_item = self.treeview.tree.insert("","end",text=os.path.basename(rootPath),image=self.folder_bmp,values=(rootPath,))
        self.ListDirItem(root_item,rootPath)
        self.treeview.tree.item(root_item,open=True)
        self.treeview.tree.selection_set(root_item)
        self.AddokcancelButton()

    def ListDirItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isdir(file_path) and not fileutils.is_path_hidden(file_path):
                item = self.treeview.tree.insert(parent_item,"end",text=f,image=self.folder_bmp,values=(file_path,))
                self.ListDirItem(item,file_path)

    def _ok(self):
        path = fileutils.getRelativePath(self.treeview.tree.GetPyData(self.treeview.tree.GetSingleSelectItem()),self._current_project.homeDir)
        self.selected_path = path
        ui_base.CommonModaldialog._ok(self)

class SelectModuleFileDialog(ui_base.CommonModaldialog):
    def __init__(self,parent,title,project_model,is_startup=False,filters=[]):
        ui_base.CommonModaldialog.__init__(self,parent)
        self.title(title)
        self.module_file = None
        if filters == []:
            filters = syntax.SyntaxThemeManager().GetLexer(lang.ID_LANG_PYTHON).Exts
        self.filters = filters
        self.is_startup = is_startup
        self._current_project = project_model
        rootPath = project_model.homeDir        
        self.treeview = treeviewframe.TreeViewFrame(self.main_frame,treeview_class=ProjectTreeCtrl)
        self.treeview.tree["show"] = ("tree",)
        self.treeview.pack(fill="both",expand=1)
        
        self.folder_bmp = imageutils.load_image("","packagefolder_obj.gif")
        self.python_file_bmp = imageutils.load_image("","file/python_module.png")
        
        self.zip_file_bmp = imageutils.load_image("","project/zip.png")
        root_item = self.treeview.tree.insert("","end",text=os.path.basename(rootPath),image=self.folder_bmp)
        self.ListDirItem(root_item,rootPath)
        self.treeview.tree.item(root_item,open=True)
        self.AddokcancelButton()

    def ListDirItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isfile(file_path) and self.IsFileFiltered(file_path):
                pj_file = self._current_project.FindFile(file_path)
                if pj_file:
                    if fileutils.is_python_file(file_path):
                        item = self.treeview.tree.insert(parent_item,"end",text=f,image=self.python_file_bmp,values=(file_path,))
                    else:
                        item = self.treeview.tree.insert(parent_item,"end",text=f,image=self.zip_file_bmp,values=(file_path,))
                    #self._treeCtrl.SetPyData(item,pj_file)
                    if pj_file.IsStartup and self.is_startup:
                        self.treeview.tree.SetItemBold(item)
            elif os.path.isdir(file_path) and not fileutils.is_path_hidden(file_path):
                item = self.treeview.tree.insert(parent_item,"end",text=f,image=self.folder_bmp)
                self.ListDirItem(item,file_path)

    def _ok(self):
        pj_file = self.treeview.tree.GetPyData(self.treeview.tree.GetSingleSelectItem())
        if pj_file is None:
            messagebox.showinfo(GetApp().GetAppName(),_("Please select a file"))
            return
        self.module_file = pj_file
        ui_base.CommonModaldialog._ok(self)
        
    def IsFileFiltered(self,file_path):
        file_ext = strutils.get_file_extension(file_path)
        return file_ext in self.filters
