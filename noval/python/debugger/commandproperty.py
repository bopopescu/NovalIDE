# -*- coding: utf-8 -*-
from noval import GetApp,_
import os
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import noval.ui_base as ui_base
import noval.consts as consts
import noval.python.project.viewer as projectviewer
import noval.util.utils as utils
import noval.misc as misc
import noval.util.fileutils as fileutils
from noval.python.parser.utils import py_cmp,py_sorted
from noval.syntax import syntax

class CommandPropertiesDialog(ui_base.CommonModaldialog):
    def __init__(self, parent, title, currentProj, okButtonName="&OK", debugging=False,is_last_config=False):
        self._is_last_config = is_last_config
        self._currentProj = currentProj
        self._projectNameList, self._projectDocumentList, selectedIndex = self.GetProjectList()
        if not self._projectNameList:
            messagebox.showerror(_("To run or debug you must have an open runnable file or project containing runnable files. Use File->Open to open the file you wish to run or debug."), _("Nothing to Run"))
            raise Exception("Nothing to Run or Debug.")

        ui_base.CommonModaldialog.__init__(self, parent)
        self.title(title)
        self.main_frame.columnconfigure(1, weight=1)

        ttk.Label(self.main_frame, text=_("PYTHONPATH:")).grid(row=4,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text=_("Project:")).grid(row=0,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text=_("File:")).grid(row=1,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text=_("Arguments:")).grid(row=2,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        ttk.Label(self.main_frame, text=_("Start in:")).grid(row=3,column=0,sticky=tk.NSEW,padx=(consts.DEFAUT_CONTRL_PAD_X,0),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        
        postpendStaticText = _("Postpend content root path")
        self._projectNameVar = tk.StringVar()
        self._projList = ttk.Combobox(self.main_frame, values=self._projectNameList,textvariable=self._projectNameVar)
        self._projList['state'] = 'readonly'
        self._projList.grid(row=0,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2,padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        self._projList.bind("<<ComboboxSelected>>",self.EvtListBox)

        self._fileList = ttk.Combobox(self.main_frame)
        self._fileList['state'] = 'readonly'
        self._fileList.grid(row=1,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2,padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        self._fileList.bind("<<ComboboxSelected>>",self.OnFileSelected)
  
        self._lastArguments = utils.profile_get(self.GetKey("LastRunArguments"))
        self._lastArgumentsVar = tk.StringVar(value=self._lastArguments)
        row = ttk.Frame(self.main_frame)
        self._argsEntry = ttk.Combobox(row,values=[],textvariable=self._lastArgumentsVar)
        self._argsEntry.pack(side=tk.LEFT,fill="x",expand=1)
             
        self._useArgCheckBoxVar = tk.IntVar(value=1)
        useArgCheckBox = ttk.Checkbutton(row, text= _("Use"),command=self.CheckUseArgument,variable=self._useArgCheckBoxVar)
        useArgCheckBox.pack(side=tk.LEFT,fill="x",padx=(consts.DEFAUT_HALF_CONTRL_PAD_X,0))
        
        row.grid(row=2,column=1,sticky=tk.NSEW,columnspan=2,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_HALF_CONTRL_PAD_X))

        self._lastStartIn = utils.profile_get(self.GetKey("LastRunStartIn"),os.getcwd())
        self._lastStartInVar = tk.StringVar(value=self._lastStartIn)
        startEntry = ttk.Entry(self.main_frame, textvariable=self._lastStartInVar)
        startEntry.grid(row=3,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_HALF_CONTRL_PAD_X))

        self._findDir = ttk.Button(self.main_frame,text=_("Browse..."),command=self.OnFindDirClick)
        self._findDir.grid(row=3,column=2,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
    
        if 'PYTHONPATH' in os.environ:
            startval = os.environ['PYTHONPATH']
        else:
            startval = ""
        self._lastPythonPath = utils.profile_get(self.GetKey("LastPythonPath"), startval)
        self._lastPythonPathVar = tk.StringVar(value=self._lastPythonPath)
        pythonPathEntry = ttk.Entry(self.main_frame, textvariable=self._lastPythonPathVar)
        pythonPathEntry.grid(row=4,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2,padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        misc.create_tooltip(pythonPathEntry,_('multiple path is seperated by %s') % os.pathsep)

        last_row = 4
        if self._currentProj is not None:
            last_row += 1
            self._postpendCheckBoxVar = tk.IntVar(value=1)
            self._postpendCheckBox = ttk.Checkbutton(self.main_frame, text=postpendStaticText,variable=self._postpendCheckBoxVar)
            self._postpendCheckBox.grid(row=last_row,column=1,sticky=tk.NSEW,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=2)
        # Set up selections based on last values used.
        self._fileNameList = None
        self._selectedFileIndex = -1
        lastProject = utils.profile_get(self.GetKey("LastRunProject"))
        lastFile = utils.profile_get(self.GetKey("LastRunFile"))
        #点击上一次配置按钮时,如果有保存上次运行的配置,则不显示对话框,否则要显示
        self._mustShow = not lastFile

        if lastProject in self._projectNameList:
            selectedIndex = self._projectNameList.index(lastProject)
        elif selectedIndex < 0:
            selectedIndex = 0
        self._projList.current(selectedIndex)
        self._selectedProjectIndex = selectedIndex
        self._selectedProjectDocument = self._projectDocumentList[selectedIndex]
        self.PopulateFileList(self._selectedProjectDocument, lastFile)
        
        if not self._is_last_config:
            self.SetEntryParams()
        last_row += 1
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.grid(row=last_row,column=0,pady=(consts.DEFAUT_CONTRL_PAD_Y,0),columnspan=3)
        self.AppendokcancelButton(bottom_frame)
        self.ok_button.configure(text=okButtonName,default="active")
        self.FormatTkButtonText(self.ok_button)

    def MustShowDialog(self):
        return self._mustShow

    def GetKey(self, lastPart):
        if self._currentProj:
            return self._currentProj.GetKey(lastPart)
        return lastPart
        
    def GetProjectFileKey(self, filepath,lastPart):
        if not self._currentProj:
            return self.GetKey(lastPart)
        if self._currentProj.GetFilename() == consts.NOT_IN_ANY_PROJECT:
            return self._currentProj.GetUnProjectFileKey(filepath,lastPart)
        else:
            pj_file = self._currentProj.GetModel().FindFile(filepath)
            if pj_file is None:
                return self.GetKey(lastPart)
            return self._currentProj.GetFileKey(pj_file,lastPart)
            
    def SetEntryParams(self):
        self._lastArgumentsVar.set("")
        if self._selectedFileIndex >= 0 and len(self._fileNameList) > self._selectedFileIndex:
            selected_filename = self._fileNameList[self._selectedFileIndex]
        else:
            selected_filename = ""
        argments = utils.profile_get(self.GetProjectFileKey(selected_filename,"RunArguments"),"")
        self._lastArgumentsVar.set(argments)
        self._lastPythonPathVar.set(utils.profile_get(self.GetProjectFileKey(selected_filename,"PythonPath"),""))
        startin = utils.profile_get(self.GetProjectFileKey(selected_filename,"RunStartIn"),"")
        self._lastStartInVar.set(startin)
        saved_arguments = utils.profile_get(self.GetProjectFileKey(selected_filename,"FileSavedArguments"),[])
        if saved_arguments:
            self._argsEntry['values'] = saved_arguments
        self._useArgCheckBoxVar.set(utils.profile_get_int(self.GetProjectFileKey(selected_filename,"UseArgument"),True))
        self.CheckUseArgument()
        
        if hasattr(self, "_postpendCheckBox"):
            if self._projectNameVar.get() == consts.NOT_IN_ANY_PROJECT:
                self._postpendCheckBox['state'] = tk.DISABLED
            else:
                self._postpendCheckBox['state'] = tk.NORMAL
                checked = bool(utils.profile_get_int(self.GetKey("PythonPathPostpend"), True))
                self._postpendCheckBoxVar.set(checked)
        
    def _ok(self,event=None):
        startIn = self._lastStartInVar.get().strip()
        if self._selectedFileIndex >= 0 and len(self._fileNameList) > self._selectedFileIndex:
            fileToRun = self._fileNameList[self._selectedFileIndex]
        else:
            fileToRun = ""
        if not fileToRun:
            messagebox.showinfo(GetApp().GetAppName(),_("You must select a file to proceed. Note that not all projects have files that can be run or debugged."))
            return
        isPython = fileutils.is_python_file(fileToRun)
        if isPython and not os.path.exists(startIn) and startIn != '':
            messagebox.showinfo(GetApp().GetAppName(),_("Starting directory does not exist. Please change this value."))
            return
        # Don't update the arguments or starting directory unless we're runing python.
        if isPython:
            utils.profile_set(self.GetProjectFileKey(fileToRun,"RunStartIn"), startIn)
            utils.profile_set(self.GetProjectFileKey(fileToRun,"PythonPath"),self._lastPythonPathVar.get().strip())
            utils.profile_set(self.GetProjectFileKey(fileToRun,"UseArgument"), self._useArgCheckBoxVar.get())
            #when use argument is checked,save argument
            if self._useArgCheckBoxVar.get():
                utils.profile_set(self.GetProjectFileKey(fileToRun,"RunArguments"), self._lastArgumentsVar.get())
                arguments = set()
                values = self._argsEntry['values']
                if not values:
                    values = []
                values = list(values)
                values.append(self._lastArgumentsVar.get())
                arguments = set(values)
                utils.profile_set(self.GetProjectFileKey(fileToRun,"FileSavedArguments"),list(arguments))
            if hasattr(self, "_postpendCheckBox"):
                utils.profile_set(self.GetKey("PythonPathPostpend"), self._postpendCheckBoxVar.get())
                
        ui_base.CommonModaldialog._ok(self,event=None)

    def GetSettings(self):
        projectDocument = self._selectedProjectDocument
        if self._selectedFileIndex >= 0 and len(self._fileNameList) > self._selectedFileIndex:
            fileToRun = self._fileNameList[self._selectedFileIndex]
        else:
            fileToRun = ""
        filename = utils.profile_get(self.GetKey("LastRunFile"),fileToRun)
        args = self._lastArgumentsVar.get()
        startIn = self._lastStartInVar.get().strip()
        isPython = fileutils.is_python_file(filename)
        env = {}
        if hasattr(self, "_postpendCheckBox"):
            postpend = self._postpendCheckBoxVar.get()
        else:
            postpend = False
        if postpend:
            env[consts.PYTHON_PATH_NAME] = str(self._lastPythonPathVar.get()) + os.pathsep + os.path.join(os.getcwd(), "3rdparty", "pywin32")
        else:
            #should avoid environment contain unicode string,such as u'xxx'
            env[consts.PYTHON_PATH_NAME] = str(self._lastPythonPathVar.get())

        return projectDocument, filename, args, startIn, isPython, env

    def OnFileSelected(self, event):
        self._selectedFileIndex = self._fileList.current()
        self.SetEntryParams()

    def OnFindDirClick(self):
        path = filedialog.askdirectory(title=_("Choose a starting directory:"))
        if not path:
            return
        self._lastStartInVar.set(fileutils.opj(path))
        
    def CheckUseArgument(self):
        use_arg = self._useArgCheckBoxVar.get()
        if use_arg:
            self._argsEntry['state'] = tk.NORMAL 
        else:
            self._argsEntry['state'] = tk.DISABLED

    def EvtListBox(self, event):
        if self._projectNameVar.get():
            index = self._projectNameList.index(self._projectNameVar.get())
            self._selectedProjectDocument = self._projectDocumentList[index]
            self._currentProj = self._selectedProjectDocument
            self._selectedProjectIndex = index
            self.PopulateFileList(self._selectedProjectDocument)
            self.SetEntryParams()

    def FilterFileList(self, file_list):
        files = filter(lambda f:fileutils.is_python_file(f), file_list)
        return list(files)

    def PopulateFileList(self, project, shortNameToSelect=None):
        project_startup_file = project.GetStartupFile()
        if project_startup_file is None:
            pj_files = project.GetFiles()[:]
        else:
            pj_files = [project_startup_file.filePath]
        self._fileNameList = self.FilterFileList(pj_files)
        if not self._fileNameList:
            self._fileList['values'] = []
            return
        py_sorted(self._fileNameList, cmp_func=lambda a, b: py_cmp(os.path.basename(a).lower(), os.path.basename(b).lower()))
        strings = list(map(lambda file: os.path.basename(file), self._fileNameList))
        for index in range(0, len(self._fileNameList)):
            if shortNameToSelect == self._fileNameList[index]:
                self._selectedFileIndex = index
                break

        self._fileList['values'] = (strings)
        if self._selectedFileIndex not in range(0, len(strings)):
            # Pick first bpel file if there is one.
            for index in range(0, len(strings)):
                if strings[index].endswith('.bpel'):
                    self._selectedFileIndex = index
                    break
        # Still no selected file, use first file.      
        if self._selectedFileIndex not in range(0, len(strings)):
            self._selectedFileIndex = 0
        self._fileList.current(self._selectedFileIndex)

    def GetProjectList(self):
        docList = []
        nameList = []
        found = False
        index = -1
        count = 0
        for document in GetApp().GetDocumentManager().GetDocuments():
            if document.GetDocumentTemplate().GetDocumentType() == self._currentProj.__class__:
                docList.append(document)
                nameList.append(os.path.basename(document.GetFilename()))
                if document == self._currentProj:
                    found = True
                    index = count
                count += 1
        #Check for open files not in any of these projects and add them to a default project
        def AlreadyInProject(fileName):
            for projectDocument in docList:
                if projectDocument.IsFileInProject(fileName):
                    return True
            return False

        unprojectedFiles = []
        python_document_type = syntax.SyntaxThemeManager().GetLexer(GetApp().GetDefaultLangId()).GetDocTypeClass()
        for document in GetApp().GetDocumentManager().GetDocuments():
            if type(document) == python_document_type:
                if not AlreadyInProject(document.GetFilename()):
                    unprojectedFiles.append(document.GetFilename())
        #不存在于当前项目的文件,全部归入'Not in Any Project',并且虚拟一个项目文档
        if unprojectedFiles:
            unprojProj = self._currentProj.__class__.GetUnProjectDocument()
            unprojProj.AddFiles(unprojectedFiles)
            docList.append(unprojProj)
            nameList.append(consts.NOT_IN_ANY_PROJECT)
            if self._currentProj is None:
                self._currentProj = unprojProj
                index = count
        return nameList, docList, index
