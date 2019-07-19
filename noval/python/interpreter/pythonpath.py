from noval import _
import tkinter as tk
from tkinter import ttk,messagebox
import noval.python.parser.utils as parserutils
import noval.python.interpreter.pythonpathmixin as pythonpathmixin
import noval.util.utils as utils

class PythonPathPanel(ttk.Frame,pythonpathmixin.PythonpathMixin):
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        self.InitUI()
        self._interpreter = None
        
    def AppendSysPath(self,interpreter):
        self._interpreter = interpreter
        self.treeview._clear_tree()
        if self._interpreter is not None:
            root_item = self.treeview.tree.insert("","end",text=_("Path List"),image=self.LibraryIcon)
            path_list = interpreter.SysPathList + interpreter.PythonPathList
            for path in path_list:
                if path.strip() == "":
                    continue
                #process path contains chinese character
                if utils.is_py2():
                    path = self.ConvertPath(path)
                self.treeview.tree.insert(root_item,"end",text=path,image=self.LibraryIcon)
            self.treeview.tree.item(root_item, open=True)
        self.UpdateUI()
        
    def RemovePath(self):
        if self._interpreter is None:
            return
        selections = self.treeview.tree.selection()
        if not selections:
            return
        if selections[0] == self.treeview.tree.get_children()[0]:
            return
        path = self.treeview.tree.item(selections[0],"text")
        if parserutils.PathsContainPath(self._interpreter.SysPathList,path):
            messagebox.showerror(_("Error"),_("The Python System Path could not be removed"),parent=self)
            return
        pythonpathmixin.PythonpathMixin.RemovePath(self)
        
    def CheckPythonPathList(self):
        python_path_list = self.GetPythonPathFromPathList()
        is_pythonpath_changed = self.IsPythonPathChanged(python_path_list)
        if is_pythonpath_changed:
            self._interpreter.PythonPathList = python_path_list
        return is_pythonpath_changed
        
    def IsPythonPathChanged(self,python_path_list):
        if self._interpreter is None:
            return False
        if len(python_path_list) != len(self._interpreter.PythonPathList):
            return True
        for pythonpath in python_path_list:
            if not parserutils.PathsContainPath(self._interpreter.PythonPathList,pythonpath):
                return True
        return False
        
    def CheckPythonPath(self):
        return self.IsPythonPathChanged(self.GetPythonPathFromPathList())
        
    def GetPythonPathFromPathList(self):
        if self._interpreter is None:
            return []
        path_list = self.GetPathList()
        python_path_list = []
        for path in path_list:
            #process path contains chinese character
            if utils.is_py2():
                new_path = self.ConvertPath(path)
            elif utils.is_py3_plus():
                new_path = path
            if not parserutils.PathsContainPath(self._interpreter.SysPathList,new_path):
                python_path_list.append(new_path)
        return python_path_list
        
    def UpdateUI(self):
        if self._interpreter is None:
            self.add_path_btn["state"] = tk.DISABLED
            self.add_file_btn["state"] = tk.DISABLED
            self.remove_path_btn["state"] = tk.DISABLED
        else:
            self.add_path_btn["state"] = "normal"
            self.add_file_btn["state"] = "normal"
            self.remove_path_btn["state"] = "normal"
            
    def destroy(self):
        if self.menu is not None:
            self.menu.destroy()
        self.button_menu.destroy()
        ttk.Frame.destroy(self)