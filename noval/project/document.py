# -*- coding: utf-8 -*-
from noval import GetApp,_
from tkinter import messagebox
import os
import noval.core as core
import noval.filewatcher as filewatcher
import noval.project.command as projectcommand
from noval.util import utils
import noval.project.basemodel as projectlib
import noval.util.fileutils as fileutils
import noval.consts as consts
import six

PROJECT_KEY = "/NOV_Projects"

class ProjectDocument(core.Document):
    
    UNPROJECT_MODEL_ID = "8F470CCF-A44F-11E8-88DC-005056C00008"
    #项目生成的二进制文件不能添加到项目中去
    BIN_FILE_EXTS = []
    
    @classmethod
    def GetUnProjectDocument(cls):
        unproj_model = cls.GetProjectModel()
        unproj_model.Id = ProjectDocument.UNPROJECT_MODEL_ID
        unprojProj = cls(model=unproj_model)
        unprojProj.SetFilename(consts.NOT_IN_ANY_PROJECT)
        unprojProj.SetDebugger(GetApp().GetDebugger())
        return unprojProj
        
    @classmethod
    def GetUnProjectFileKey(cls,file_path,lastPart):
        unprojProj = cls.GetUnProjectDocument()
        unprojProj.AddFile(file_path)
        return unprojProj.GetFileKey(file_path,lastPart)


    def __init__(self, model=None):
        core.Document.__init__(self)
        if model:
            self.SetModel(model)
        else:
            self.SetModel(self.GetProjectModel())  # initial model used by "File | New... | Project"
        self._stageProjectFile = False
        self._run_parameter = None
        self.document_watcher = filewatcher.FileAlarmWatcher()
        self._commandProcessor = projectcommand.CommandProcessor()
        self._debugger = None

    def PromptToSaveFiles(self):
        def save_docs():
            for modify_doc in modify_docs:
                modify_doc.Save()
            
        filesModified = False
        modify_docs = []
        docs = GetApp().GetDocumentManager().GetDocuments()
        for doc in docs:
              if doc.IsModified() and (self == GetApp().MainFrame.GetProjectView(show=False,generate_event=False).FindProjectFromMapping(doc) or\
                                     self.GetModel().FindFile(doc.GetFilename())):
                filesModified = True
                modify_docs.append(doc)
        if filesModified:
            if utils.profile_get_int("PromptSaveProjectFile", True):
                yesNoMsg = messagebox.askyesno(_("Run Project"),
                          _("Files have been modified.\nWould you like to save all files before running?")
                          )
                if yesNoMsg == True:
                    save_docs()
            else:
                save_docs()

    def GetDebugger(self):
        return self._debugger

    def SetDebugger(self,debugger):
        self._debugger = debugger

    @staticmethod
    def GetProjectModel():
        return projectlib.Project()

    def GetRunconfigClass(self):
        raise NotImplementedError('you must implement this in derived class')

    def GetRunConfiguration(self,start_up_file):
        file_key = self.GetFileKey(start_up_file)
        run_configuration_name = utils.ProfileGet(file_key + "/RunConfigurationName","")
        return run_configuration_name
    
    def __copy__(self):
        model = copy.copy(self.GetModel())        
        clone =  ProjectDocument(model)
        clone.SetFilename(self.GetFilename())
        return clone

    def GetFirstView(self):
        """ Bug: workaround.  If user tries to open an already open project with main menu "File | Open...", docview.DocManager.OnFileOpen() silently returns None if project is already open.
            And to the user, it appears as if nothing has happened.  The user expects to see the open project.
            This forces the project view to show the correct project.
        """
        view = core.Document.GetFirstView(self)
        view.SetProject(self.GetFilename())  # ensure project is displayed in view
        return view

    def GetModel(self):
        return self._projectModel

    def GetPath(self):
        return os.path.dirname(self.GetFilename())

    def SetModel(self, model):
        self._projectModel = model
        
    def GetKey(self,lastPart=None):
        if not lastPart:
            return "%s/{%s}" % (PROJECT_KEY, self.GetModel().Id)
        return "%s/{%s}/%s" % (PROJECT_KEY, self.GetModel().Id, lastPart)
        
    def GetFileKey(self,pj_file,lastPart=None):
        filename = pj_file
        if isinstance(pj_file,six.string_types[0]):
            pj_file = self.GetModel().FindFile(pj_file)
        #文件已经不存在与项目中,返回项目的key路径
        if pj_file is None:
            utils.get_logger().error('file %s is not in project'%filename)
            return "%s/{%s}" % (PROJECT_KEY, self.GetModel().Id)
            
        if pj_file.logicalFolder is None:
            key_path = os.path.basename(pj_file.filePath)
        else:
            key_path = os.path.join(pj_file.logicalFolder,os.path.basename(pj_file.filePath))
        key_path = fileutils.opj(key_path)
        if lastPart is None:
           return "%s/{%s}/%s" % (PROJECT_KEY, self.GetModel().Id, key_path.replace(os.sep, '|')) 
        return "%s/{%s}/%s/%s" % (PROJECT_KEY, self.GetModel().Id, key_path.replace(os.sep, '|'),lastPart)

    def OnCreate(self, path, flags):
        view = GetApp().MainFrame.GetProjectView().GetView()
        # All project documents share the same view.
        self.AddView(view)
        return view

    def LoadObject(self, fileObject):
        self.SetModel(projectlib.load(fileObject))
      #  self.GetModel().SetDocCallback(GetDocCallback)
        return True


    def SaveObject(self, fileObject):
        projectlib.save(fileObject, self.GetModel())
##        try:
##            projectlib.save(fileObject, self.GetModel())
##        except Exception as e:
##            wx.MessageBox(_("Project %s Save Failed") % self.GetModel().Name,_("Save Project"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
##            return False
        return True

    def OnOpenDocument(self, filePath):
        view = GetApp().MainFrame.GetProjectView(show=True,generate_event=False).GetView()
        if not os.path.exists(filePath):
            GetApp().CloseSplash()
            msgTitle = GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            messagebox.showwarning(msgTitle,_("Could not find '%s'.") % filePath,parent = GetApp().GetTopWindow())
            #TODO:this may cause problem ,should watch some time to check error or not
            if self in self.GetDocumentManager().GetDocuments():
                self.Destroy()
            return True  # if we return False, the Project View is destroyed, Service windows shouldn't be destroyed

        GetApp().GetTopWindow().PushStatusText(_("Loading project \"%s\".")%filePath)
        fileObject = open(filePath, 'r')
        try:
            self.LoadObject(fileObject)
        except Exception as e:
            utils.get_logger().exception('')
            GetApp().CloseSplash()
            msgTitle = GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            messagebox.showerror(msgTitle,_("Could not open '%s'.  %s") % (fileutils.get_filename_from_path(filePath), e))
            #TODO:this may cause problem ,should watch some time to check effection
            if self in self.GetDocumentManager().GetDocuments():
                self.Destroy()
            GetApp().GetTopWindow().PushStatusText(_("Load project \"%s\" fail.")%filePath)
            fileObject.close()
            return True  # if we return False, the Project View is destroyed, Service windows shouldn't be destroyed

        project_obj = self.GetModel()
        project_document_template_class = utils.GetClassFromDynamicImportModule(project_obj._runinfo.DocumentTemplate) 
        if project_document_template_class != self.GetDocumentTemplate().__class__:
            utils.get_logger().warn('default project document template %s is not same to the template %s assigned in project file,will reload project again',self.GetDocumentTemplate().__class__,project_obj._runinfo.DocumentTemplate)
            #先删除原有的文档
            if self in self.GetDocumentManager().GetDocuments():
                self.Destroy()
            fileObject.close()
            #用新模板创建文档
            GetApp().GetDocumentManager().CreateTemplateDocument(project_document_template_class.CreateProjectTemplate(),filePath, core.DOC_SILENT|core.DOC_OPEN_ONCE)
            #必须返回True
            return True
        #to make compatible to old version,which old project instance has no id attr
        if project_obj.id == '':
            project_obj.id = str(uuid.uuid1()).upper()
            self.Modify(True)
        else:
            self.Modify(False)
        self.SetFilename(filePath, True)
        view.AddProjectToView(self)
        self.SetDocumentModificationDate()
        self.UpdateAllViews()
        self._savedYet = True
        view.Activate()
        self.document_watcher.AddFileDoc(self)
        GetApp().GetTopWindow().PushStatusText(_("Load project \"%s\" success.")%filePath)
        return True

    def OnSaveDocument(self, filename):
        self.document_watcher.StopWatchFile(self)
        suc = core.Document.OnSaveDocument(self,filename)
        self.document_watcher.StartWatchFile(self)
        return suc

    def AddFile(self, filePath, folderPath=None, type=None, name=None):
        if type:
            types = [type]
        else:
            types = None
        if name:
            names = [name]
        else:
            names = None
            
        return self.AddFiles([filePath], folderPath, types, names)


    def AddFiles(self, filePaths=None, folderPath=None, types=None, names=None, files=None):
        # Filter out files that are not already in the project
        if filePaths:
            newFilePaths = []
            oldFilePaths = []
            for filePath in filePaths:
                if self.GetModel().FindFile(filePath):
                    oldFilePaths.append(filePath)
                else:
                    newFilePaths.append(filePath)
    
            for i, filePath in enumerate(newFilePaths):
                if types:
                    type = types[i]
                else:
                    type = None
                    
                if names:
                    name = names[i]
                else:
                    name = None
                    
                if not folderPath:
                    folder = None
                else:
                    folder = folderPath
                self.GetModel().AddFile(filePath, folder, type, name)
        elif files:
            newFilePaths = []
            oldFilePaths = []
            for file in files:
                if self.GetModel().FindFile(file.filePath):
                    oldFilePaths.append(file.filePath)
                else:
                    newFilePaths.append(file.filePath)
                    self.GetModel().AddFile(file=file)
        else:
            return False
                
        self.UpdateAllViews(hint = (consts.PROJECT_ADD_COMMAND_NAME, self, newFilePaths, oldFilePaths))
        if len(newFilePaths):
            self.Modify(True)
            return True
        else:
            return False
            
    def AddProgressFiles(self,progress_ui,que,filePaths=None, folderPath=None, types=None, names=None,range_value = 0):
        # Filter out files that are not already in the project
        if filePaths:
            newFilePaths = []
            oldFilePaths = []
            for filePath in filePaths:
                if self.GetModel().FindFile(filePath):
                    oldFilePaths.append(filePath)
                    range_value += 1
                    wx.CallAfter(Publisher.sendMessage, ImportFiles.NOVAL_MSG_UI_IMPORT_FILES_PROGRESS, \
                             value=range_value,is_cancel=self.GetFirstView().IsStopImport)
                else:
                    newFilePaths.append(filePath)
    

            for i, filePath in enumerate(newFilePaths):
                if types:
                    type = types[i]
                else:
                    type = None
                    
                if names:
                    name = names[i]
                else:
                    name = None
                    
                if not folderPath:
                    folder = None
                else:
                    folder = folderPath
                self.GetModel().AddFile(filePath, folder, type, name)
        else:
            return False

        self.UpdateAllViews(hint = (consts.PROJECT_ADD_PROGRESS_COMMAND_NAME, self, newFilePaths,range_value,progress_ui,que))
        if len(newFilePaths):
            self.Modify(True)
            return True
        else:
            return False


    def RemoveFile(self, filePath):
        return self.RemoveFiles([filePath])


    def RemoveFiles(self, filePaths=None, files=None):
        removedFiles = []
        
        if files:
            filePaths = []
            for file in files:
                filePaths.append(file.filePath)
                  
        for filePath in filePaths:
            file = self.GetModel().FindFile(filePath)
            if file:
                self.GetModel().RemoveFile(file)
                removedFiles.append(file.filePath)
                                        
        self.UpdateAllViews(hint = ("remove", self, removedFiles))
        if len(removedFiles):
            self.Modify(True)
            return True
        else:
            return False


    def RenameFile(self, oldFilePath, newFilePath, isProject = False):
        try:
            if oldFilePath == newFilePath:
                return False
            openDoc = None
            # projects don't have to exist yet, so not required to rename old file,
            # but files must exist, so we'll try to rename and allow exceptions to occur if can't.
            if not isProject or (isProject and os.path.exists(oldFilePath)):
                openDoc = self.GetFirstView().GetOpenDocument(oldFilePath)
                if openDoc:
                    openDoc.FileWatcher.StopWatchFile(openDoc)
                os.rename(oldFilePath, newFilePath)
            if isProject:
                documents = self.GetDocumentManager().GetDocuments()
                for document in documents:
                    if os.path.normcase(document.GetFilename()) == os.path.normcase(oldFilePath):  # If the renamed document is open, update it
                        document.SetFilename(newFilePath)
                        document.SetTitle(wx.lib.docview.FileNameFromPath(newFilePath))
                        document.UpdateAllViews(hint = ("rename", self, oldFilePath, newFilePath))
            else:
                self.UpdateFilePath(oldFilePath, newFilePath)
                if openDoc:
                    openDoc.SetFilename(newFilePath, notifyViews = True)
                    openDoc.UpdateAllViews(hint = ("rename", self, oldFilePath, newFilePath))
                    openDoc.FileWatcher.StartWatchFile(openDoc)
                    ###openDoc.GetFirstView().DoLoadOutlineCallback(True)

            return True
        except OSError as e:
            msgTitle = _("Rename File Error")
            messagebox.showerror(msgTitle,_("Could not rename file '%s'.  '%s'") % (fileutils.get_filename_from_path(oldFilePath), e),
                          parent=GetApp().GetTopWindow())
            return False


    def MoveFile(self, file, newFolderPath):
        return self.MoveFiles([file], newFolderPath)


    def MoveFiles(self, files, newFolderPath):
        filePaths = []
        newFilePaths = []
        move_files = []
        isArray = isinstance(newFolderPath, type([]))
        for i in range(len(files)):
            if isArray:
                files[i].logicalFolder = newFolderPath[i]
            else:
                files[i].logicalFolder = newFolderPath
            oldFilePath = files[i].filePath
            filename = os.path.basename(oldFilePath)
            if isArray:
                destFolderPath = newFolderPath[i]
            else:
                destFolderPath = newFolderPath
            newFilePath = os.path.join(self.GetModel().homeDir,\
                                destFolderPath,filename)
            #this is the same file,which will ignore
            if parserutils.ComparePath(oldFilePath,newFilePath):
                continue
            if os.path.exists(newFilePath):
                ret = wx.MessageBox(_("Dest file is already exist,Do you want to overwrite it?"),_("Move File"),\
                                  wx.YES_NO|wx.ICON_QUESTION,self.GetFirstView()._GetParentFrame())
                if ret == wx.NO:
                    continue        
            try:
                shutil.move(oldFilePath,newFilePath)
            except Exception as e:
                wx.MessageBox(str(e),style = wx.OK|wx.ICON_ERROR)
                return False
            filePaths.append(oldFilePath)
            newFilePaths.append(newFilePath)
            move_files.append(files[i])

        self.UpdateAllViews(hint = ("remove", self, filePaths))
        for k in range(len(move_files)):
            move_files[k].filePath = newFilePaths[k]
        self.UpdateAllViews(hint = ("add", self, newFilePaths, []))
        self.Modify(True)
        return True


    def UpdateFilePath(self, oldFilePath, newFilePath):
        file = self.GetModel().FindFile(oldFilePath)
        self.RemoveFile(oldFilePath)
        if file:
            self.AddFile(newFilePath, file.logicalFolder, file.type, file.name)
        else:
            self.AddFile(newFilePath)


    def RemoveInvalidPaths(self):
        """Makes sure all paths project knows about are valid and point to existing files. Removes and returns list of invalid paths."""

        invalidFileRefs = []
        
        fileRefs = self.GetFileRefs()
        
        for fileRef in fileRefs:
            if not os.path.exists(fileRef.filePath):
                invalidFileRefs.append(fileRef)

        for fileRef in invalidFileRefs:
            fileRefs.remove(fileRef)

        return [fileRef.filePath for fileRef in invalidFileRefs]


    def SetStageProjectFile(self):
        self._stageProjectFile = True


    def ArchiveProject(self, zipdest):
        """Zips stagedir, creates a zipfile that has as name the projectname, in zipdest. Returns path to zipfile."""
        if os.path.exists(zipdest):
            raise AssertionError("Cannot archive project, %s already exists" % zipdest)

        filePaths = self.GetModel().filePaths
        newfilePaths = []
        for filepath in filePaths:
            #去除空文件夹下生成的虚拟文件
            if filepath.find(consts.DUMMY_NODE_TEXT) == -1:
                newfilePaths.append(filepath)  
        #指定basedir则打包到压缩包的文件路径为相对路径,否则打包到压缩包的文件路径为绝对路径
        fileutils.zip(zipdest, basedir=self.GetPath(),files=newfilePaths)
        return zipdest


    def StageProject(self, tmpdir, targetDataSourceMapping={}):
        """ Copies all files this project knows about into staging location. Files that live outside of the project dir are copied into the root of the stage dir, and their recorded file path is updated. Files that live inside of the project dir keep their relative path. Generates .dpl file into staging dir. Returns path to staging dir."""

        projname = self.GetProjectName()
        stagedir = os.path.join(tmpdir, projname)
        fileutils.remove(stagedir)
        os.makedirs(stagedir)        

        # remove invalid files from project
        self.RemoveInvalidPaths()        

        # required so relative paths are written correctly when .dpl file is
        # generated below.
        self.SetFilename(os.path.join(stagedir,
                                      os.path.basename(self.GetFilename())))
        projectdir = self.GetModel().homeDir

        # Validate paths before actually copying, and populate a dict
        # with src->dest so copying is easy.
        # (fileDict: ProjectFile instance -> dest path (string))
        fileDict = self._ValidateFilePaths(projectdir, stagedir)
        
        # copy files to staging dir
        self._StageFiles(fileDict)

        # set target data source for schemas
        self._SetSchemaTargetDataSource(fileDict, targetDataSourceMapping)

        # it is unfortunate we require this. it would be nice if filepaths
        # were only in the project
        self._FixWsdlAgFiles(stagedir)
            
        # generate .dpl file
        dplfilename = projname + deploymentlib.DEPLOYMENT_EXTENSION
        dplfilepath = os.path.join(stagedir, dplfilename)
        self.GenerateDeployment(dplfilepath)

        if self._stageProjectFile:
            # save project so we get the .agp file. not required for deployment
            # but convenient if user wants to open the deployment in the IDE
            agpfilename = projname + PROJECT_EXTENSION
            agpfilepath = os.path.join(stagedir, agpfilename)

            # if this project has deployment data sources configured, remove
            # them. changing the project is fine, since this is a clone of
            # the project the IDE has.
            self.GetModel().GetAppInfo().ResetDeploymentDataSources()
            
            f = None
            try:
                f = open(agpfilepath, "w")
                
                # setting homeDir correctly is required for the "figuring out
                # relative paths" logic when saving the project
                self.GetModel().homeDir = stagedir
                
                projectlib.save(f, self.GetModel(), productionDeployment=True)
            finally:
                try:
                    f.close()
                except: pass

        return stagedir
        
    def _StageFiles(self, fileDict):
        """Copy files to staging directory, update filePath attr of project's ProjectFile instances."""

        # fileDict: ProjectFile instance -> dest path (string)
        
        for fileRef, fileDest in fileDict.items():
            fileutils.copyFile(fileRef.filePath, fileDest)
            fileRef.filePath = fileDest

    def _ValidateFilePaths(self, projectdir, stagedir):
        """If paths validate, returns a dict mapping ProjectFile to destination path. Destination path is the path the file needs to be copied to for staging. If paths don't validate, throws an IOError.
           With our current slightly simplistic staging algorithm, staging will not work iff the project has files outside of the projectdir with names (filename without path) that:
             -  match filenames of files living at the root of the project.
             -  are same as those of any other file that lives outside of the projectdir.
          
           We have this limitation because we move any file that lives outside of the project dir into the root of the stagedir (== copied project dir). We could make this smarter by either giving files unique names if we detect a collistion, or by creating some directory structure instead of putting all files from outside of the projectdir into the root of the stagedir (== copied projectdir)."""

        # ProjectFile instance -> dest path (string)
        rtn = {}
        
        projectRootFiles = sets.Set()   # live at project root
        foreignFiles = sets.Set()       # live outside of project

        fileRefsToDeploy = self.GetFileRefs()

        for fileRef in fileRefsToDeploy:
            relPath = fileutils.getRelativePath(fileRef.filePath, projectdir)
            filename = os.path.basename(fileRef.filePath)            
            if not relPath: # file lives outside of project dir...

                # do we have another file with the same name already?
                if filename in foreignFiles:
                    raise IOError("More than one file with name \"%s\" lives outside of the project. These files need to have unique names" % filename)
                foreignFiles.add(filename)       
                fileDest = os.path.join(stagedir, filename)
            else:
                # file lives somewhere within the project dir
                fileDest = os.path.join(stagedir, relPath)
                if not os.path.dirname(relPath):
                    projectRootFiles.add(filename)
                
            rtn[fileRef] = fileDest

        # make sure we won't collide with a file that lives at root of
        # projectdir when moving files into project
        for filename in foreignFiles:
            if filename in projectRootFiles:
                raise IOError("File outside of project, \"%s\", cannot have same name as file at project root" % filename)
        return rtn
    
                            
    def RenameFolder(self, oldFolderLogicPath, newFolderLogicPath):
        try:
            oldFolderPath = os.path.join(self.GetModel().homeDir,oldFolderLogicPath)
            newFolderPath = os.path.join(self.GetModel().homeDir,newFolderLogicPath)
            os.rename(oldFolderPath, newFolderPath)
        except Exception as e:
            messagebox.showerror(_("Rename Folder Error"),_("Could not rename folder '%s'.  '%s'") % (fileutils.get_filename_from_path(oldFolderPath), e),parent= GetApp().GetTopWindow())
            return False
        rename_files = []
        for file in self.GetModel()._files:
            if file.logicalFolder == oldFolderLogicPath:
                file.logicalFolder = newFolderLogicPath
                oldFilePath = file.filePath
                file_name = os.path.basename(oldFilePath)
                newFilePath = os.path.join(newFolderPath,file_name)
                rename_files.append((oldFilePath,newFilePath))
        for rename_file in rename_files:
            oldFilePath, newFilePath = rename_file
            self.UpdateFilePath(oldFilePath, newFilePath)
            openDoc = self.GetFirstView().GetOpenDocument(oldFilePath)
            if openDoc:
                openDoc.SetFilename(newFilePath, notifyViews = True)
                openDoc.UpdateAllViews(hint = ("rename", self, oldFilePath, newFilePath))
                openDoc.FileWatcher.RemoveFile(oldFilePath)
                openDoc.FileWatcher.StartWatchFile(openDoc)
        self.UpdateAllViews(hint = ("rename folder", self, oldFolderLogicPath, newFolderLogicPath))
        self.Modify(True)
        return True

    def GetSchemas(self):
        """Returns list of schema models (activegrid.model.schema.schema) for all schemas in this project."""
        
        rtn = []
        resourceFactory = self._GetResourceFactory()
        for projectFile in self.GetModel().projectFiles:
            if (projectFile.type == basedocmgr.FILE_TYPE_SCHEMA):
                schema = resourceFactory.getModel(projectFile)
                if (schema != None):
                    rtn.append(schema)

        return rtn
        
    def GetFiles(self):
        return self.GetModel().filePaths

    def GetStartupFile(self):
        return self.GetModel().StartupFile

    def GetandSetProjectStartupfile(self):
        startup_file = self.GetStartupFile()
        if startup_file is None:
            messagebox.showerror(GetApp().GetAppName(),_("Your project needs a Python script marked as startup file to perform this action"))
            #show the property dialog to remind user to set the startup file
            GetApp().MainFrame.GetProjectView(generate_event=False).OnProjectProperties(item_name="Debug/Run")
            return None
        return startup_file

    def GetFileRefs(self):
        return self.GetModel().findAllRefs()


    def SetFileRefs(self, fileRefs):
        return self.GetModel().setRefs(fileRefs)    


    def IsFileInProject(self, filename):
        return self.GetModel().FindFile(filename)
        

    def GetAppInfo(self):
        return self.GetModel().GetAppInfo()


    def GetAppDocMgr(self):
        return self.GetModel()
        

    def GetProjectName(self):
        return os.path.splitext(os.path.basename(self.GetFilename()))[0]


    def GetDeploymentFilepath(self, pre17=False):
        if (pre17):
            name = self.GetProjectName() + PRE_17_TMP_DPL_NAME
        else:
            name = self.GetProjectName() + _17_TMP_DPL_NAME
        return os.path.join(self.GetModel().homeDir, name)
    

    def _GetResourceFactory(self, preview=False, deployFilepath=None):
        return IDEResourceFactory(
            openDocs=wx.GetApp().GetDocumentManager().GetDocuments(),
            dataSourceService=wx.GetApp().GetService(DataModelEditor.DataSourceService),
            projectDir=os.path.dirname(self.GetFilename()),
            preview=preview,
            deployFilepath=deployFilepath)

    def GenerateDeployment(self, deployFilepath=None, preview=False):
        
        if ACTIVEGRID_BASE_IDE:
            return

        if not deployFilepath:
            deployFilepath = self.GetDeploymentFilepath()

        d = DeploymentGeneration.DeploymentGenerator(
            self.GetModel(), self._GetResourceFactory(preview,
                                                      deployFilepath))
                
        dpl = d.getDeployment(deployFilepath)

        if preview:
            dpl.initialize()  # used in preview only

        # REVIEW 07-Apr-06 stoens@activegrid.com -- Check if there's a
        # tmp dpl file with pre 17 name, if so, delete it, so user doesn't end
        # up with unused file in project dir. We should probably remove this
        # check after 1.7 goes out.
        fileutils.remove(self.GetDeploymentFilepath(pre17=True))

        deploymentlib.saveThroughCache(dpl.fileName, dpl)
        return deployFilepath
        

    def GetCommandProcessor(self):
        """
        Returns the command processor associated with this document.
        """
        return self._commandProcessor


    def SetCommandProcessor(self, processor):
        """
        Sets the command processor to be used for this document. The document
        will then be responsible for its deletion. Normally you should not
        call this; override OnCreateCommandProcessor instead.
        """
        self._commandProcessor = processor

    def GetRunconfigClass(self):
        '''
            获取项目的运行配置类,是项目文件的_runinfo下面的RunConfig值
        '''
        run_config_name = self.GetModel()._runinfo.RunConfig
        if not run_config_name:
            raise RuntimeError(_("We don't know how to run the program"))
        return utils.GetClassFromDynamicImportModule(run_config_name)

        
