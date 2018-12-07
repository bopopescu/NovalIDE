#----------------------------------------------------------------------------
# Name:         ProjectEditor.py
# Purpose:      IDE-style Project Editor for wx.lib.pydocview
#
# Author:       wukan
#
# Created:      8/15/03
# CVS-ID:       $Id$
# Copyright:    (c) 2003-2006 Genetalks, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.lib.docview
import wx.lib.pydocview
import wx.lib.buttons
import noval.tool.service.Service as Service
import copy
import os
import os.path
import sets
import sys
import time
import types
import noval.util.appdirs as appdirs
import noval.util.strutils as strutils
import noval.util.fileutils as fileutils
import noval.util.logger as logger
import noval.tool.UICommon as UICommon
import Wizard
import noval.tool.service.SVNService as SVNService
import project as projectlib
import noval.tool.service.ExtensionService as ExtensionService
import noval.tool.ResourceView as ResourceView
import noval.util.sysutils as sysutilslib
import ImportFiles
from noval.tool.consts import SPACE,HALF_SPACE,_,PROJECT_SHORT_EXTENSION,\
                    PROJECT_EXTENSION,ERROR_OK,NOT_IN_ANY_PROJECT,PYTHON_PATH_NAME
import threading
import shutil
import noval.util.WxThreadSafe as WxThreadSafe
import noval.parser.utils as parserutils
from wx.lib.pubsub import pub as Publisher
import ProjectUI
from noval.model import configuration
import uuid
import noval.tool.FileObserver as FileObserver
import cPickle
import NewFile
import noval.tool.images as images
import noval.tool.debugger.DebuggerService as DebuggerService
import datetime
from noval.util import utils
import Property
import noval.tool.project.RunConfiguration as RunConfiguration
from noval.util.exceptions import PromptErrorException
import noval.tool.aui as aui

from noval.tool.IDE import ACTIVEGRID_BASE_IDE
if not ACTIVEGRID_BASE_IDE:
    import activegrid.server.deployment as deploymentlib
    import ProcessModelEditor
    import DataModelEditor
    import DeploymentGeneration
    import WsdlAgEditor
    import WsdlAgModel
    APP_LAST_LANGUAGE = "LastLanguage"
    import activegrid.model.basedocmgr as basedocmgr
    import activegrid.model.basemodel as basemodel
    import activegrid.model.projectmodel as projectmodel
    import PropertyService
    from activegrid.server.toolsupport import GetTemplate
    import activegrid.util.xmlutils as xmlutils
    DataServiceExistenceException = DeploymentGeneration.DataServiceExistenceException
    import WebBrowserService

from noval.tool.service.SVNService import SVN_INSTALLED


if wx.Platform == '__WXMSW__':
    _WINDOWS = True
else:
    _WINDOWS = False
    
#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------

if not ACTIVEGRID_BASE_IDE:
    PRE_17_TMP_DPL_NAME = "RunTime_tmp" + deploymentlib.DEPLOYMENT_EXTENSION
    _17_TMP_DPL_NAME = ".tmp" + deploymentlib.DEPLOYMENT_EXTENSION

# wxBug: the wxTextCtrl and wxChoice controls on Mac do not correctly size
# themselves with sizers, so we need to add a right border to the sizer to
# get the control to shrink itself to fit in the sizer.
MAC_RIGHT_BORDER = 0
if wx.Platform == "__WXMAC__":
    MAC_RIGHT_BORDER = 5


PROJECT_KEY = "/NOV_Projects"
PROJECT_DIRECTORY_KEY = "NewProjectDirectory"

NEW_PROJECT_DIRECTORY_DEFAULT = appdirs.getSystemDir()
DF_COPY_FILENAME = wx.CustomDataFormat("copy_file_names")

#----------------------------------------------------------------------------
# Methods
#----------------------------------------------------------------------------

def AddProjectMapping(doc, projectDoc=None, hint=None):
    projectService = wx.GetApp().GetService(ProjectService)
    if projectService:
        if not projectDoc:
            if not hint:
                hint = doc.GetFilename()
            projectDocs = projectService.FindProjectByFile(hint)
            if projectDocs:
                projectDoc = projectDocs[0]
                
        projectService.AddProjectMapping(doc, projectDoc)
        if hasattr(doc, "GetModel"):
            projectService.AddProjectMapping(doc.GetModel(), projectDoc)


def getProjectKeyName(projectId, mode=None):
    if mode:
        return "%s/{%s}/%s" % (PROJECT_KEY, projectId, mode)
    else:
        return "%s/{%s}" % (PROJECT_KEY, projectId)


def GetDocCallback(filepath):
    """ Get the Document used by the IDE and the in-memory document model used by runtime engine """
    docMgr = wx.GetApp().GetDocumentManager()
    
    try:
        doc = docMgr.CreateDocument(filepath, docMgr.GetFlags()|wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE|wx.lib.docview.DOC_NO_VIEW)
        if doc:
            AddProjectMapping(doc)
        else:  # already open
            for d in docMgr.GetDocuments():
                if os.path.normcase(d.GetFilename()) == os.path.normcase(filepath):
                    doc = d
                    break
    except Exception,e:
        doc = None            
        logger.reportException(e, stacktrace=True)
            
    if doc and doc.GetDocumentTemplate().GetDocumentType() == WsdlAgEditor.WsdlAgDocument:
        # get referenced wsdl doc instead
        if doc.GetModel().filePath:
            if os.path.isabs(doc.GetModel().filePath):  # if absolute path, leave it alone
                filepath = doc.GetModel().filePath
            else:
                filepath = doc.GetAppDocMgr().fullPath(doc.GetModel().filePath)  # check relative to project homeDir
        
                if not os.path.isfile(filepath):
                    filepath = os.path.normpath(os.path.join(os.path.dirname(doc.GetFilename()), doc.GetModel().filePath))  # check relative to wsdlag file
                    
                    if not os.path.isfile(filepath):
                        filename = os.sep + os.path.basename(doc.GetModel().filePath)  # check to see if in project file
                        filePaths = findDocumentMgr(doc).filePaths
                        for fp in filePaths:
                            if fp.endswith(filename):
                                filepath = fp
                                break
        
            try:
                doc = docMgr.CreateDocument(filepath, docMgr.GetFlags()|wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE|wx.lib.docview.DOC_NO_VIEW)
            except Exception,e:
                doc = None
                logger.reportException(e, stacktrace=True)
                
            if doc: 
                AddProjectMapping(doc)
            else:  # already open
                for d in docMgr.GetDocuments():
                    if os.path.normcase(d.GetFilename()) == os.path.normcase(filepath):
                        doc = d
                        break
        else:
            doc = None

    if doc:
        docModel = doc.GetModel()
    else:
        docModel = None
        
    return doc, docModel


def findDocumentMgr(root):
    projectService = wx.GetApp().GetService(ProjectService)
    if projectService:
        projectDoc = projectService.FindProjectFromMapping(root)
        if projectDoc:
            return projectDoc.GetModel()
            
        projectDoc = projectService.GetCurrentProject()
        if not projectDoc:
            return None
            
        if isinstance(root, wx.lib.docview.Document):
            filepath = root.GetFilename()
        elif hasattr(root, "fileName") and root.fileName:
            filepath = root.fileName
        else:
            filepath = None
            
        if filepath:    
            if projectDoc.IsFileInProject(filepath):
                return projectDoc.GetModel()
                
            projects = []
            openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
            for openDoc in openDocs:
                if openDoc == projectDoc:
                    continue
                if(isinstance(openDoc, ProjectDocument)):
                    if openDoc.IsFileInProject(filepath):
                        projects.append(openDoc)
                        
            if projects:
                if len(projects) == 1:
                    return projects[0].GetModel()
                else:
                    choices = [os.path.basename(project.GetFilename()) for project in projects]
                    dlg = wx.SingleChoiceDialog(wx.GetApp().GetTopWindow(), _("'%s' found in more than one project.\nWhich project should be used for this operation?") % os.path.basename(filepath), _("Select Project"), choices, wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.OK|wx.CENTRE)
                    dlg.CenterOnParent()
                    projectDoc = None
                    if dlg.ShowModal() == wx.ID_OK:
                        i = dlg.GetSelection()
                        projectDoc = projects[i]
                    dlg.Destroy()
                    return projectDoc.GetModel()
        return projectDoc.GetModel()
    
    return None
    

if not ACTIVEGRID_BASE_IDE:
    basemodel.findGlobalDocumentMgr = findDocumentMgr


#----------------------------------------------------------------------------
# Classes
#----------------------------------------------------------------------------

if not ACTIVEGRID_BASE_IDE:
    class IDEResourceFactory(DeploymentGeneration.DeploymentResourceFactory):
        
        def __init__(self, openDocs, dataSourceService, projectDir,
                     preview=False, deployFilepath=None):

            self.openDocs = openDocs
            self.dataSourceService = dataSourceService
            self.projectDir = projectDir
            self.preview = preview
            self.deployFilepath = deployFilepath
            
            self.defaultFlagsNoView = (
                wx.GetApp().GetDocumentManager().GetFlags()|
                wx.lib.docview.DOC_SILENT|
                wx.lib.docview.DOC_OPEN_ONCE|
                wx.lib.docview.DOC_NO_VIEW)
            
        def getModel(self, projectFile):
            doc = wx.GetApp().GetDocumentManager().CreateDocument(
                projectFile.filePath, flags=self.defaultFlagsNoView)
            if (doc == None):  # already open
                doc = self._findOpenDoc(projectFile.filePath)
            else:
                AddProjectMapping(doc)
            if (doc != None):
                return doc.GetModel()

        def getDataSource(self, dataSourceName):
            # in preview mode, runtime needs the generated Deployment
            # to contain the requried data source. But runtime doesn't
            # actually need to communicate to db. So here is the logic to
            # make preview works if the required data soruce has not
            # yet been defined.            
            dataSource = self.dataSourceService.getDataSource(dataSourceName)
            if (dataSource != None):
                return dataSource
            elif not self.preview:
                raise DataServiceExistenceException(dataSourceName)
            else:
                # first to see if an existing dpl file is there, if so,
                # use the data source in dpl file
                if (self.deployFilepath != None):
                    tempDply = None
                    try:
                        tempDply = xmlutils.load(deployFilepath)
                    except:
                        pass
                    if (tempDply != None):
                        for tempDataSource in tempDply.dataSources:
                            if (tempDataSource.name == dataSourceName):
                                return tempDataSource

                # if unable to use dpl file, then create a dummy data source
                import activegrid.data.dataservice as dataservice
                return dataservice.DataSource(
                    name=dataSourceName, dbtype=dataservice.DB_TYPE_SQLITE)

        def initDocumentRef(self, projectFile, documentRef, dpl):
            doc = self._findOpenDoc(projectFile.filePath)
            if (doc and hasattr(doc, 'GetModel')):
                documentRef.document = doc.GetModel()
                if isinstance(documentRef, deploymentlib.XFormRef):
                    doc.GetModel().linkDeployment(dpl, dpl.loader)

        def _findOpenDoc(self, filePath):
            for openDoc in self.openDocs:
                if openDoc.GetFilename() == filePath:
                    return openDoc
            return None

        def getProjectDir(self):
            return self.projectDir


class ProjectDocument(wx.lib.docview.Document):
    
    UNPROJECT_MODEL_ID = "8F470CCF-A44F-11E8-88DC-005056C00008"
    #don't allow pyc and pyo file add to project
    BAN_FILE_EXTS = ['pyc','pyo']
    
    @staticmethod
    def GetUnProjectDocument():
        unproj_model = projectlib.PythonProject()
        unproj_model.Id = ProjectDocument.UNPROJECT_MODEL_ID
        unprojProj = ProjectDocument(model=unproj_model)
        unprojProj.SetFilename(NOT_IN_ANY_PROJECT)
        return unprojProj
        
    @staticmethod
    def GetUnProjectFileKey(file_path,lastPart):
        return "%s/{%s}/%s/%s" % (PROJECT_KEY, ProjectDocument.UNPROJECT_MODEL_ID, file_path.replace(os.sep, '|'),lastPart)


    def __init__(self, model=None):
        wx.lib.docview.Document.__init__(self)
        if model:
            self.SetModel(model)
        else:
            self.SetModel(projectlib.PythonProject())  # initial model used by "File | New... | Project"
        self.GetModel().SetDocCallback(GetDocCallback)

        self._stageProjectFile = False
        self._run_parameter = None
        self.document_watcher = FileObserver.FileAlarmWatcher()

    def GetRunConfiguration(self,start_up_file):
        file_key = self.GetFileKey(start_up_file)
        run_configuration_name = utils.ProfileGet(file_key + "/RunConfigurationName","")
        return run_configuration_name
        
    def GetRunParameter(self,start_up_file):
        #check the run configuration first,if exist,use run configuration
        run_configuration_name = self.GetRunConfiguration(start_up_file)
        if run_configuration_name:
            file_configuration = RunConfiguration.FileConfiguration(self,start_up_file)
            run_configuration = file_configuration.LoadConfiguration(run_configuration_name)
            try:
                return run_configuration.GetRunParameter()
            except PromptErrorException as e:
                wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR)
                return None
            
        config = wx.ConfigBase_Get()
        use_argument = config.ReadInt(self.GetFileKey(start_up_file,"UseArgument"),True)
        if use_argument:
            initialArgs = config.Read(self.GetFileKey(start_up_file,"RunArguments"),"")
        else:
            initialArgs = ''
        python_path = config.Read(self.GetFileKey(start_up_file,"PythonPath"),"")
        startIn = config.Read(self.GetFileKey(start_up_file,"RunStartIn"),"")
        if startIn == '':
            startIn = os.path.dirname(self.GetFilename())
        env = {}
        paths = set()
        path_post_end = config.ReadInt(self.GetKey("PythonPathPostpend"), True)
        if path_post_end:
            paths.add(str(os.path.dirname(self.GetFilename())))
        #should avoid environment contain unicode string,such as u'xxx'
        if len(python_path) > 0:
            paths.add(str(python_path))
        env[PYTHON_PATH_NAME] = os.pathsep.join(list(paths))
        return configuration.RunParameter(wx.GetApp().GetCurrentInterpreter(),start_up_file.filePath,initialArgs,env,startIn,project=self)

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
        view = wx.lib.docview.Document.GetFirstView(self)
        if view.GetMode() == ProjectView.PROJECT_VIEW:
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
        if pj_file.logicalFolder is None:
            key_path = os.path.basename(pj_file.filePath)
        else:
            key_path = os.path.join(pj_file.logicalFolder,os.path.basename(pj_file.filePath))
        key_path = fileutils.opj(key_path)
        if lastPart is None:
           return "%s/{%s}/%s" % (PROJECT_KEY, self.GetModel().Id, key_path.replace(os.sep, '|')) 
        return "%s/{%s}/%s/%s" % (PROJECT_KEY, self.GetModel().Id, key_path.replace(os.sep, '|'),lastPart)

    def OnCreate(self, path, flags):
        projectService = wx.GetApp().GetService(ProjectService)
        view = projectService.GetView()
        if view:  # view already exists, reuse
            # All project documents share the same view.
            self.AddView(view)

            if view.GetDocument():
                # All project documents need to share the same command processor,
                # to enable redo/undo of cross project document commands
                cmdProcessor = view.GetDocument().GetCommandProcessor()
                if cmdProcessor:
                    self.SetCommandProcessor(cmdProcessor)
        else:  # generate view
            view = self.GetDocumentTemplate().CreateView(self, flags)
            projectService.SetView(view)

        return view


    def LoadObject(self, fileObject):
        self.SetModel(projectlib.load(fileObject))
        self.GetModel().SetDocCallback(GetDocCallback)
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
        projectService = wx.GetApp().GetService(ProjectService)
        view = projectService.GetView()
        if view.GetMode() == ProjectView.RESOURCE_VIEW:
            view._physicalBtn.SetToggle(False)
            view._logicalBtn.SetToggle(True)
            view._projectChoice.Clear()
            view.SelectView()

        if not os.path.exists(filePath):
            wx.GetApp().CloseSplash()
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            wx.MessageBox(_("Could not find '%s'.") % filePath,
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP,
                          wx.GetApp().GetTopWindow())
                          
            #TODO:this may cause problem ,should watch some time to check error or not
            if self in self.GetDocumentManager().GetDocuments():
                self.Destroy()
            return True  # if we return False, the Project View is destroyed, Service windows shouldn't be destroyed

        fileObject = file(filePath, 'r')
        try:
            self.LoadObject(fileObject)
        except:
            wx.GetApp().CloseSplash()
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            wx.MessageBox(_("Could not open '%s'.  %s") % (wx.lib.docview.FileNameFromPath(filePath), sys.exc_value),
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP,
                          wx.GetApp().GetTopWindow())
            #TODO:this may cause problem ,should watch some time to check effection
            if self in self.GetDocumentManager().GetDocuments():
                self.Destroy()
            return True  # if we return False, the Project View is destroyed, Service windows shouldn't be destroyed

        project_obj = self.GetModel()
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
        return True

    def OnSaveDocument(self, filename):
        self.document_watcher.StopWatchFile(self)
        suc = wx.lib.docview.Document.OnSaveDocument(self,filename)
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
    
            projectService = wx.GetApp().GetService(ProjectService)
            for i, filePath in enumerate(newFilePaths):
                if types:
                    type = types[i]
                else:
                    type = None
                    
                if names:
                    name = names[i]
                else:
                    name = projectService.FindNameDefault(filePath)
                    
                if not folderPath:
                    folder = projectService.FindLogicalViewFolderDefault(filePath)
                else:
                    folder = folderPath
                    
                if strutils.GetFileExt(filePath) in self.BAN_FILE_EXTS:
                    continue
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

        self.AddNameSpaces(newFilePaths)
                
        self.UpdateAllViews(hint = ("add", self, newFilePaths, oldFilePaths))
        if len(newFilePaths):
            self.Modify(True)
            return True
        else:
            return False
            
    def AddProgressFiles(self,parent,filePaths=None, folderPath=None, types=None, names=None,range_value = 0):
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
    
            projectService = wx.GetApp().GetService(ProjectService)
            for i, filePath in enumerate(newFilePaths):
                if types:
                    type = types[i]
                else:
                    type = None
                    
                if names:
                    name = names[i]
                else:
                    name = projectService.FindNameDefault(filePath)
                    
                if not folderPath:
                    folder = projectService.FindLogicalViewFolderDefault(filePath)
                else:
                    folder = folderPath
                    
                if strutils.GetFileExt(filePath) in self.BAN_FILE_EXTS:
                    continue
                self.GetModel().AddFile(filePath, folder, type, name)
        else:
            return False

        self.AddNameSpaces(newFilePaths)
                
        self.UpdateAllViews(hint = ("progress_add", self, newFilePaths,range_value,parent))
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
                wx.CallAfter(self.UpdateFilePath,oldFilePath, newFilePath)
                if openDoc:
                    openDoc.SetFilename(newFilePath, notifyViews = True)
                    openDoc.UpdateAllViews(hint = ("rename", self, oldFilePath, newFilePath))
                    openDoc.FileWatcher.StartWatchFile(openDoc)
                    openDoc.GetFirstView().DoLoadOutlineCallback(True)

            return True
        except OSError, (code, message):
            msgTitle = _("Rename File Error")
            wx.MessageBox(_("Could not rename file '%s'.  '%s'") % (wx.lib.docview.FileNameFromPath(oldFilePath), message),
                          msgTitle,
                          wx.OK | wx.ICON_ERROR,
                          wx.GetApp().GetTopWindow())
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
        fileutils.zip(zipdest, files=self.GetModel().filePaths)
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

    def _FixWsdlAgFiles(self, stagedir):
        """For each wsdlag file in the stagedir: if referenced artifact (wsdl or code file) is a known product file (such as securityservice.wsdl), make sure patch to it is parameterized with special env var. We do not want to copy those files. For user artifacts, ensure the file lives in root of stagedir. This should be the case if it is part of project (since staging has run). If it is not at root of stagedir, copy it. Then update path in wsdlag."""
        files = os.listdir(stagedir)
        for f in files:
            if (f.endswith(WsdlAgEditor.WsdlAgDocument.WSDL_AG_EXT)):
                wsdlagpath = os.path.join(stagedir, f)
                fileObject = None
                modified = False
                try:
                    fileObject = open(wsdlagpath)
                    serviceref = WsdlAgEditor.load(fileObject)

                    # referenced wsdl
                    if (hasattr(serviceref, WsdlAgModel.WSDL_FILE_ATTR)):
                        modified = (modified |
                                    self._UpdateServiceRefPathAttr(
                                        stagedir, serviceref,
                                        WsdlAgModel.WSDL_FILE_ATTR))

                    # referenced code file
                    if (hasattr(serviceref, WsdlAgModel.LOCAL_SERVICE_ELEMENT)):
                        lse = getattr(serviceref,
                                      WsdlAgModel.LOCAL_SERVICE_ELEMENT)
                        if (hasattr(lse, WsdlAgModel.LOCAL_SERVICE_FILE_ATTR)):
                            modified = (modified |
                                        self._UpdateServiceRefPathAttr(
                                            stagedir, lse,
                                            WsdlAgModel.LOCAL_SERVICE_FILE_ATTR))

                    
                finally:
                    try:
                        fileObject.close()
                    except:
                        pass

                # no need to save the file if we did not change anything
                if not modified: continue

                # write the wsdlag file
                fileObject = open(wsdlagpath)
                try:
                    serviceref = WsdlAgEditor.save(fileObject, serviceref)
                finally:
                    try:
                        fileObject.close()
                    except:
                        pass
                    

    def _UpdateServiceRefPathAttr(self, stagedir, serviceref, attrName):
        """Returns True if serviceref path has been updated, False otherwise."""

        filePath = getattr(serviceref, attrName)

        if (filePath == None):
            return False

        filePath = filePath.strip()

        if (len(filePath) == 0):
            return False
            

        # if filePath starts with one of the AG systems vars, we don't
        # have to do anything
        if (fileutils.startsWithAgSystemVar(filePath)):
            return False

        # remove any known env var refs (we'll put them back a little below)
        # we remove them here so that paths that do not have env vars also
        # get parameterized correctly below
        filePath = fileutils.expandKnownAGVars(filePath)

        # make sure we have forward slashes. this is a workaround, which
        # would not be necessary if we only write paths with forward slashes
        # into our files
        filePath = filePath.replace("\\", "/")
        
        filePath = os.path.abspath(filePath)        

        if (not os.path.exists(filePath)):
            # Wrong place to validate that referenced file exists, so just
            # give up
            return False
            
        # If the referenced file is in stagedir already, there's nothing to do
        if (fileutils.hasAncestorDir(filePath, stagedir)):
            return False

        # The path points outside of stagedir.

        # Check if we already have the referenced wsdl file at root, should be
        # the case if the referenced wsdl is part of project.
        # Copy it if we don't have it, unless it lives in one of the known
        # product directories - in which case we parameterize the known path
        # with one of our AG system vars
        relPath = os.path.basename(filePath)
        stagePath = os.path.join(stagedir, relPath)

        if (not os.path.exists(stagePath)):
            pFilePath = fileutils.parameterizePathWithAGSystemVar(filePath)
            if pFilePath == filePath: # no parameterization happened, copy
                fileutils.copyFile(filePath, stagePath)
                setattr(serviceref, attrName, relPath)
            else:
                setattr(serviceref, attrName, pFilePath.replace("\\", "/"))
        else:
            setattr(serviceref, attrName, relPath)

        return True


    def _SetSchemaTargetDataSource(self, projectFiles, dsmapping):
        """Update schema's default data source, if necessary."""

        for projectFile in projectFiles:
            if (projectFile.type == basedocmgr.FILE_TYPE_SCHEMA):
                name = os.path.basename(projectFile.filePath)
                if (dsmapping.has_key(name)):
                    schema = xmlutils.load(projectFile.filePath)
                    defaultName = schema.getDefaultDataSourceName()
                    if (defaultName != dsmapping[name]):
                        schema.setDefaultDataSourceName(dsmapping[name])
                        xmlutils.save(projectFile.filePath, schema)
        
        
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
            wx.MessageBox(_("Could not rename folder '%s'.  '%s'") % (wx.lib.docview.FileNameFromPath(oldFolderPath), e),
                          _("Rename Folder Error"),
                          wx.OK | wx.ICON_ERROR,
                          wx.GetApp().GetTopWindow())
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
        
    def AddNameSpaces(self, filePaths):
        """ Add any new wsdl and schema namespaces to bpel files """
        """ Add any new schema namespaces to wsdl files """
        if ACTIVEGRID_BASE_IDE:
            return

        processRefs = self.GetAppDocMgr().findRefsByFileType(basedocmgr.FILE_TYPE_PROCESS) # bpel
        schemaRefs = self.GetAppDocMgr().findRefsByFileType(basedocmgr.FILE_TYPE_SCHEMA) # xsd
        serviceRefs = self.GetAppDocMgr().allServiceRefs  # wsdl
        
        # update bpel files
        if processRefs and (serviceRefs or schemaRefs):
            for processRef in processRefs:
                processDoc = processRef.ideDocument
                process = processDoc.GetModel()
                
                if processDoc and process:
                    modified = False
                    
                    # add wsdl namespaces to bpel file
                    for serviceRef in serviceRefs:
                        wsdl = serviceRef.document
                        if (wsdl
                        and (wsdl.fileName in filePaths
                        or serviceRef.filePath in filePaths)):
                            wsdlLongNS = wsdl.targetNamespace
                            wsdlShortNS = self.GetAppDocMgr().findShortNS(wsdlLongNS)
                            if not wsdlShortNS:
                                wsdlShortNS = xmlutils.genShortNS(process, wsdlLongNS)
                            xmlutils.addNSAttribute(process, wsdlShortNS, wsdlLongNS)
                            modified = True
                            
                    # add schema namespaces to bpel file
                    for schemaRef in schemaRefs:
                        schema = schemaRef.document
                        if schema and schema.fileName in filePaths:
                            schemaLongNS = schema.targetNamespace
                            schemaShortNS = self.GetAppDocMgr().findShortNS(schemaLongNS)
                            if not schemaShortNS:
                                schemaShortNS = xmlutils.genShortNS(process, schemaLongNS)
                            xmlutils.addNSAttribute(process, schemaShortNS, schemaLongNS)
                            modified = True
    
                    if modified:
                        processDoc.OnSaveDocument(processDoc.GetFilename())


        # update wsdl files
        if serviceRefs and schemaRefs:
            for serviceRef in serviceRefs:
                wsdl = serviceRef.document
                wsdlDoc = serviceRef.ideDocument
                
                if wsdl and wsdlDoc:
                    modified = False
                    
                    # add schema namespace to wsdl file
                    for schemaRef in schemaRefs:
                        schema = schemaRef.document
                        if schema and schema.fileName in filePaths:
                            schemaLongNS = schema.targetNamespace
                            schemaShortNS = self.GetAppDocMgr().findShortNS(schemaLongNS)
                            if not schemaShortNS:
                                schemaShortNS = xmlutils.genShortNS(wsdl, schemaLongNS)
                            xmlutils.addNSAttribute(wsdl, schemaShortNS, schemaLongNS)
                            modified = True
                            
                    if modified:
                        wsdlDoc.OnSaveDocument(wsdlDoc.GetFilename())


class NewProjectWizard(Wizard.BaseWizard):

    def __init__(self, parent):
        self._parent = parent
        self._fullProjectPath = None
        Wizard.BaseWizard.__init__(self, parent, _("New Project Wizard"))
        self._projectLocationPage = self.CreateProjectLocation(self)
        wx.wizard.EVT_WIZARD_PAGE_CHANGING(self, self.GetId(), self.OnWizPageChanging)
        self._project_configuration = None


    def CreateProjectLocation(self,wizard):
        page = Wizard.TitledWizardPage(wizard, _("Name and Location"))

        page.GetSizer().Add(wx.StaticText(page, -1, _("\nEnter the name and location for the project.\n")))
        self._fileValidation = UICommon.CreateDirectoryControl(page,fileExtension=PROJECT_SHORT_EXTENSION, appDirDefaultStartDir=True, fileLabel=_("Name:"), dirLabel=_("Location:"),useDirDialog=True)
        wizard.Layout()
        wizard.FitToPage(page)
        return page


    def RunWizard(self, existingTables = None, existingRelationships = None):
        status = Wizard.BaseWizard.RunWizard(self, self._projectLocationPage)
        if status:
            wx.ConfigBase_Get().Write(PROJECT_DIRECTORY_KEY, self._project_configuration.Location)
            docManager = wx.GetApp().GetTopWindow().GetDocumentManager()
            if os.path.exists(self._fullProjectPath):
                # What if the document is already open and we're overwriting it?
                documents = docManager.GetDocuments()
                for document in documents:
                    if os.path.normcase(document.GetFilename()) == os.path.normcase(self._fullProjectPath):  # If the renamed document is open, update it
                        document.DeleteAllViews()
                        break
                os.remove(self._fullProjectPath)

            for template in docManager.GetTemplates():
                if template.GetDocumentType() == ProjectDocument:
                    doc = template.CreateDocument(self._fullProjectPath, flags = wx.lib.docview.DOC_NEW)
                    #set project name
                    doc.GetModel().Name = self._project_configuration.Name
                    doc.GetModel().Id = str(uuid.uuid1()).upper()
                    doc.GetModel().SetInterpreter(self._project_configuration.Interpreter)
                    doc.OnSaveDocument(self._fullProjectPath)
                    projectService = wx.GetApp().GetService(ProjectService)
                    view = projectService.GetView()
                    if view.GetMode() == ProjectView.RESOURCE_VIEW:
                        view._physicalBtn.SetToggle(False)
                        view._logicalBtn.SetToggle(True)
                        view._projectChoice.Clear()
                        view.SelectView()
                    view.AddProjectToView(doc)
                    if self._project_configuration.PythonPathPattern == \
                                    configuration.ProjectSettings.PROJECT_SRC_PATH_ADD_TO_PYTHONPATH:
                            doc.GetCommandProcessor().Submit(ProjectAddFolderCommand(view, doc, \
                                    configuration.ProjectSettings.DEFAULT_PROJECT_SRC_PATH))
                    break

        self.Destroy()
        return status


    def OnWizPageChanging(self, event):
        if event.GetDirection():  # It's going forwards
            if event.GetPage() == self._projectLocationPage:
                ok,self._project_configuration = self._fileValidation(validClassName=True)
                if not ok:
                    event.Veto()
                    return
                #if project location path include project name
                if self._project_configuration.IsProjectDirCreated:
                    self._fullProjectPath = os.path.join(self._project_configuration.Location,self._project_configuration.Name,\
                                    UICommon.MakeNameEndInExtension(self._project_configuration.Name, PROJECT_EXTENSION))
                else:
                    self._fullProjectPath = os.path.join(self._project_configuration.Location,\
                                    UICommon.MakeNameEndInExtension(self._project_configuration.Name, PROJECT_EXTENSION))


    def OnShowCreatePages(self):
        self.Hide()
        import DataModelEditor
        requestedPos = self.GetPositionTuple()
        projectService = wx.GetApp().GetService(ProjectService)
        projectView = projectService.GetView()

        wiz = DataModelEditor.ImportExportWizard(projectView.GetFrame(), pos=requestedPos)
        if wiz.RunWizard(dontDestroy=True):
           self._schemaName.SetValue(wiz.GetSchemaFileName())
        wiz.Destroy()
        self.Show(True)


class ProjectTemplate(wx.lib.docview.DocTemplate):


    def CreateDocument(self, path, flags):
        if path:
            doc = wx.lib.docview.DocTemplate.CreateDocument(self, path, flags)
            if path:
                doc.GetModel()._projectDir = os.path.dirname(path)
            return doc
        else:
            wiz = NewProjectWizard(wx.GetApp().GetTopWindow())
            wiz.RunWizard()
            wiz.Destroy()
            return None  # never return the doc, otherwise docview will think it is a new file and rename it


class ProjectAddFilesCommand(wx.lib.docview.Command):


    def __init__(self, projectDoc, filePaths, folderPath=None, types=None, names=None):
        wx.lib.docview.Command.__init__(self, canUndo = True)
        self._projectDoc = projectDoc
        self._allFilePaths = filePaths
        self._folderPath = folderPath
        self._types = types
        self._names = names
        
        if not self._types:
            self._types = []
            projectService = wx.GetApp().GetService(ProjectService)
            for filePath in self._allFilePaths:
                self._types.append(projectService.FindFileTypeDefault(filePath))

        # list of files that will really be added
        self._newFiles = []
        for filePath in self._allFilePaths:
            if not projectDoc.GetModel().FindFile(filePath):
                self._newFiles.append(filePath)


    def GetName(self):
        if len(self._allFilePaths) == 1:
            return _("Add File %s") % os.path.basename(self._allFilePaths[0])
        else:
            return _("Add Files")


    def Do(self):
        return self._projectDoc.AddFiles(self._allFilePaths, self._folderPath, self._types, self._names)


    def Undo(self):
        return self._projectDoc.RemoveFiles(self._newFiles)
        
class ProjectAddProgressFilesCommand(wx.lib.docview.Command):


    def __init__(self, parent,projectDoc, filePaths, folderPath=None, types=None, names=None,range_value=0):
        wx.lib.docview.Command.__init__(self, canUndo = False)
        self._projectDoc = projectDoc
        self._allFilePaths = filePaths
        self._folderPath = folderPath
        self._types = types
        self._names = names
        self._parent = parent
        
        if not self._types:
            self._types = []
            projectService = wx.GetApp().GetService(ProjectService)
            for filePath in self._allFilePaths:
                self._types.append(projectService.FindFileTypeDefault(filePath))
        self._range_value = range_value

    def Do(self):
        return self._projectDoc.AddProgressFiles(self._parent,self._allFilePaths, self._folderPath, \
                    self._types, self._names,self._range_value)
        
    def Undo(self):
        return False


class ProjectRemoveFilesCommand(wx.lib.docview.Command):


    def __init__(self, projectDoc, files):
        wx.lib.docview.Command.__init__(self, canUndo = True)
        self._projectDoc = projectDoc
        self._files = files


    def GetName(self):
        if len(self._files) == 1:
            return _("Remove File %s") % os.path.basename(self._files[0].filePath)
        else:
            return _("Remove Files")


    def Do(self):
        return self._projectDoc.RemoveFiles(files=self._files)


    def Undo(self):
        return self._projectDoc.AddFiles(files=self._files)



class ProjectRenameFileCommand(wx.lib.docview.Command):


    def __init__(self, projectDoc, oldFilePath, newFilePath, isProject = False):
        wx.lib.docview.Command.__init__(self, canUndo = True)
        self._projectDoc = projectDoc
        self._oldFilePath = oldFilePath
        self._newFilePath = newFilePath
        self._isProject = isProject


    def GetName(self):
        return _("Rename File %s to %s") % (os.path.basename(self._oldFilePath), os.path.basename(self._newFilePath))


    def Do(self):
        return self._projectDoc.RenameFile(self._oldFilePath, self._newFilePath, self._isProject)


    def Undo(self):
        return self._projectDoc.RenameFile(self._newFilePath, self._oldFilePath, self._isProject)


class ProjectRenameFolderCommand(wx.lib.docview.Command):
    def __init__(self, doc, oldFolderPath, newFolderPath):
        wx.lib.docview.Command.__init__(self, canUndo = True)
        self._doc = doc
        self._oldFolderPath = oldFolderPath
        self._newFolderPath = newFolderPath


    def GetName(self):
        return _("Rename Folder %s to %s") % (os.path.basename(self._oldFolderPath), os.path.basename(self._newFolderPath))


    def Do(self):
        return self._doc.RenameFolder(self._oldFolderPath, self._newFolderPath)


    def Undo(self):
        return self._doc.RenameFolder(self._newFolderPath, self._oldFolderPath)
    

class ProjectAddFolderCommand(wx.lib.docview.Command):
    def __init__(self, view, doc, folderpath,is_package = False):
        wx.lib.docview.Command.__init__(self, canUndo = True)
        self._doc = doc
        self._view = view
        self._folderpath = folderpath
        self._is_package = is_package


    def GetName(self):
        return _("Add Folder %s") % (os.path.basename(self._folderpath))


    def Do(self):
        if self._view.GetDocument() != self._doc:
            return True
        status = self._view.AddFolder(self._folderpath,self._is_package)
        if status:
            self._view._treeCtrl.UnselectAll()
            item = self._view._treeCtrl.FindFolder(self._folderpath)
            self._view._treeCtrl.SelectItem(item)
        return status


    def Undo(self):
        if self._view.GetDocument() != self._doc:
            return True
        return self._view.DeleteFolder(self._folderpath)


class ProjectRemoveFolderCommand(wx.lib.docview.Command):
    def __init__(self, view, doc, folderpath,delete_folder_files = False):
        wx.lib.docview.Command.__init__(self, canUndo = True)
        self._doc = doc
        self._view = view
        self._folderpath = folderpath
        self._delete_folder_files = delete_folder_files

    def GetName(self):
        return _("Remove Folder %s") % (os.path.basename(self._folderpath))


    def Do(self):
        if self._view.GetDocument() != self._doc:
            return True
        return self._view.DeleteFolder(self._folderpath,self._delete_folder_files)


    def Undo(self):
        if self._view.GetDocument() != self._doc:
            return True
        status = self._view.AddFolder(self._folderpath)
        if status:
            self._view._treeCtrl.UnselectAll()
            item = self._view._treeCtrl.FindFolder(self._folderpath)
            self._view._treeCtrl.SelectItem(item)
        return status


class ProjectMoveFilesCommand(wx.lib.docview.Command):

    def __init__(self, doc, files, folderPath):
        wx.lib.docview.Command.__init__(self, canUndo = True)
        self._doc = doc
        self._files = files
        self._newFolderPath = folderPath
        
        self._oldFolderPaths = []
        for file in self._files:
            self._oldFolderPaths.append(file.logicalFolder)
            

    def GetName(self):
        if len(self._files) == 1:
            return _("Move File %s") % os.path.basename(self._files[0].filePath)
        else:    
            return _("Move Files")


    def Do(self):
        return self._doc.MoveFiles(self._files, self._newFolderPath)


    def Undo(self):
        return self._doc.MoveFiles(self._files, self._oldFolderPaths)            


class ProjectTreeCtrl(wx.TreeCtrl):

    #----------------------------------------------------------------------------
    # Overridden Methods
    #----------------------------------------------------------------------------

    def __init__(self, parent, id, style):
        wx.TreeCtrl.__init__(self, parent, id, style = style)

        templates = wx.GetApp().GetDocumentManager().GetTemplates()
        iconList = wx.ImageList(16, 16, initialCount = len(templates))
        self._iconIndexLookup = []
        for template in templates:
            icon = template.GetIcon()
            if icon:
                if icon.GetHeight() != 16 or icon.GetWidth() != 16:
                    icon.SetHeight(16)
                    icon.SetWidth(16)
                    if wx.GetApp().GetDebug():
                        print "Warning: icon for '%s' isn't 16x16, not crossplatform" % template._docTypeName
                iconIndex = iconList.AddIcon(icon)
                self._iconIndexLookup.append((template, iconIndex))

        icon = images.getBlankIcon()
        if icon.GetHeight() != 16 or icon.GetWidth() != 16:
            icon.SetHeight(16)
            icon.SetWidth(16)
            if wx.GetApp().GetDebug():
                print "Warning: getBlankIcon isn't 16x16, not crossplatform"
        self._blankIconIndex = iconList.AddIcon(icon)
        
        icon = getFolderClosedIcon()
        if icon.GetHeight() != 16 or icon.GetWidth() != 16:
            icon.SetHeight(16)
            icon.SetWidth(16)
            if wx.GetApp().GetDebug():
                print "Warning: getFolderIcon isn't 16x16, not crossplatform"
        self._folderClosedIconIndex = iconList.AddIcon(icon)

        icon = getFolderOpenIcon()
        if icon.GetHeight() != 16 or icon.GetWidth() != 16:
            icon.SetHeight(16)
            icon.SetWidth(16)
            if wx.GetApp().GetDebug():
                print "Warning: getFolderIcon isn't 16x16, not crossplatform"
        self._folderOpenIconIndex = iconList.AddIcon(icon)

        icon = getPackageFolderIcon()
        if icon.GetHeight() != 16 or icon.GetWidth() != 16:
            icon.SetHeight(16)
            icon.SetWidth(16)
            if wx.GetApp().GetDebug():
                print "Warning: getPackageFolderOIcon isn't 16x16, not crossplatform"
        self._packageFolderIndex = iconList.AddIcon(icon)

        self.AssignImageList(iconList)


    def OnCompareItems(self, item1, item2):
        item1IsFolder = (self.GetPyData(item1) == None)
        item2IsFolder = (self.GetPyData(item2) == None)
        if (item1IsFolder == item2IsFolder):  # if both are folders or both not
            return cmp(self.GetItemText(item1).lower(), self.GetItemText(item2).lower())
        elif item1IsFolder and not item2IsFolder: # folders sort above non-folders
            return -1
        elif not item1IsFolder and item2IsFolder: # folders sort above non-folders
            return 1
        

    def AppendFolder(self, parent, folderName):
        item = wx.TreeCtrl.AppendItem(self, parent, folderName)
        self.SetItemImage(item, self._folderClosedIconIndex, wx.TreeItemIcon_Normal)
        self.SetItemImage(item, self._folderOpenIconIndex, wx.TreeItemIcon_Expanded)
        self.SetPyData(item, None)
        return item
        
    def AppendPackageFolder(self, parent, folderName):
        item = wx.TreeCtrl.AppendItem(self, parent, folderName)
        self.SetItemImage(item, self._packageFolderIndex, wx.TreeItemIcon_Normal)
        self.SetPyData(item, None)
        return item
        
    def GetIconIndexFromName(self,filename):
        template = wx.GetApp().GetDocumentManager().FindTemplateForPath(filename)
        return self.GetTemplateIconIndex(template)
        
    def GetTemplateIconIndex(self,template):
        for t, iconIndex in self._iconIndexLookup:
            if t is template:
                return iconIndex
        return -1

    def AppendItem(self, parent, filename, file):
        item = wx.TreeCtrl.AppendItem(self, parent, filename)
        template = wx.GetApp().GetService(ProjectService).GetView().GetOpenDocumentTemplate(file)
        

        found = False
        if template is None:
            template = wx.GetApp().GetDocumentManager().FindTemplateForPath(filename)
        if template:
            iconIndex = self.GetTemplateIconIndex(template)
            if iconIndex != -1:
                self.SetItemImage(item, iconIndex, wx.TreeItemIcon_Normal)
                self.SetItemImage(item, iconIndex, wx.TreeItemIcon_Expanded)
                found = True

        if not found:
            self.SetItemImage(item, self._blankIconIndex, wx.TreeItemIcon_Normal)
            self.SetItemImage(item, self._blankIconIndex, wx.TreeItemIcon_Expanded)

        self.SetPyData(item, file)
        return item


    def AddFolder(self, folderPath,is_package = False):
        folderItems = []
        
        if folderPath != None:
            folderTree = folderPath.split('/')
            
            item = self.GetRootItem()
            for folderName in folderTree:
                found = False
                
                (child, cookie) = self.GetFirstChild(item)
                while child.IsOk():
                    file = self.GetPyData(child)
                    if file:
                        pass
                    else: # folder
                        if self.GetItemText(child) == folderName:
                            item = child
                            found = True
                            break
                    (child, cookie) = self.GetNextChild(item, cookie)
                    
                if not found:
                    if not is_package:
                        item = self.AppendFolder(item, folderName)
                    else:
                        item = self.AppendPackageFolder(item, folderName)
                    folderItems.append(item)

        return folderItems
        

    def FindItem(self, filePath, parentItem=None):
        if not parentItem:
            parentItem = self.GetRootItem()
            
        (child, cookie) = self.GetFirstChild(parentItem)
        while child.IsOk():
            file = self.GetPyData(child)
            if file:
                if file.filePath == filePath:
                    return child
            else: # folder
                result = self.FindItem(filePath, child)  # do recursive call
                if result:
                    return result
            (child, cookie) = self.GetNextChild(parentItem, cookie)
        
        return None


    def FindFolder(self, folderPath):
        if folderPath != None:
            folderTree = folderPath.split('/')
            
            item = self.GetRootItem()
            for folderName in folderTree:
                found = False
                
                (child, cookie) = self.GetFirstChild(item)
                while child.IsOk():
                    file = self.GetPyData(child)
                    if file:
                        pass
                    else: # folder
                        if self.GetItemText(child) == folderName:
                            item = child
                            found = True
                            break
                    (child, cookie) = self.GetNextChild(item, cookie)
                    
            if found:
                return item
                
        return None


    def FindClosestFolder(self, x, y):
        item, flags = self.HitTest((x,y))
        if item:
            file = self.GetPyData(item)
            if file:
                item = self.GetItemParent(item)
                return item
            return item
        return None
        

    def GetSingleSelectItem(self):
        items = self.GetSelections()
        if not items:
            return None
        return items[0]


class ProjectView(wx.lib.docview.View):
    PROJECT_VIEW  = "ProjectView"
    RESOURCE_VIEW = "ResourceView"
    
    COPY_FILE_TYPE = 1
    CUT_FILE_TYPE = 2
    
    PACKAGE_INIT_FILE = "__init__.py"

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self, service = None):
        wx.lib.docview.View.__init__(self)
        self._service = service  # not used, but kept to match other Services
        self._projectChoice = None
        self._logicalBtn = None
        self._physicalBtn = None
        self._treeCtrl = None
        self._editingSoDontKillFocus = False
        self._checkEditMenu = True
        self._loading = False  # flag to not to try to saving state of folders while it is loading
        max_documemt_num = 5
        self._documents = []
        self._document = None
        self._stop_importing = False
        self._bold_item = None

    def GetDocumentManager(self):  # Overshadow this since the superclass uses the view._viewDocument attribute directly, which the project editor doesn't use since it hosts multiple docs
        return wx.GetApp().GetDocumentManager()


    def Destroy(self):
        projectService = wx.GetApp().GetService(ProjectService)
        if projectService:
            projectService.SetView(None)
        wx.lib.docview.View.Destroy(self)
        
    @property
    def IsStopImport(self):
        return self._stop_importing

    @property
    def Documents(self):
        return self._documents
        
    def GetDocument(self):
        if not self._projectChoice or self.GetMode() == ProjectView.RESOURCE_VIEW:
            return None
        return self._document

    def GetFrame(self):
        if self._viewFrame is None:
            return None
            
        #the frame pane is not in manager panes,get the new pane info
        if not self._service._frame._mgr.FindPane(self._viewFrame):
            paneInfo = self._service._frame._mgr.GetPane(self._viewFrame.name)
            self.SetFrame(paneInfo)
                
        return self._viewFrame.window

    def SetDocument(self,document):
        self._document = document
        
    def Activate(self, activate = True):
        if not wx.GetApp().IsMDI():
            if activate and not self.IsShown():
                self.Show()

        if self.IsShown():
            wx.lib.docview.View.Activate(self, activate = activate)
            if activate and self._treeCtrl:
                self._treeCtrl.SetFocus()
                
    def GetControl(self):
        return None

    def OnCreate(self, doc, flags):
        config = wx.ConfigBase_Get()
        if wx.GetApp().IsMDI():
            self._embeddedWindow = self._service._frame
            frame = self._embeddedWindow
            #TODO: should disable resize event,it will prevent project view to change size
           ### wx.EVT_SIZE(frame, self.OnSize)
        else:
            self._embeddedWindow = None
            pos = config.ReadInt("ProjectFrameXLoc", -1), config.ReadInt("ProjectFrameYLoc", -1)
            # make sure frame is visible
            screenWidth = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
            screenHeight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
            if pos[0] < 0 or pos[0] >= screenWidth or pos[1] < 0 or pos[1] >= screenHeight:
                pos = wx.DefaultPosition

            size = wx.Size(config.ReadInt("ProjectFrameXSize", -1), config.ReadInt("ProjectFrameYSize", -1))

            title = _("Projects")
            if self.GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI and wx.GetApp().GetAppName():
                title =  title + " - " + wx.GetApp().GetAppName()

            frame = wx.GetApp().CreateDocumentFrame(self, doc, 0, title = title, pos = pos, size = size)
            if config.ReadInt("ProjectFrameMaximized", False):
                frame.Maximize(True)

        panel = wx.Panel(frame, -1)

        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)

        butSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._projectChoice = wx.combo.BitmapComboBox(panel, -1, "",choices=[], style=wx.CB_READONLY)
        panel.Bind(wx.EVT_COMBOBOX,self.OnProjectSelect,self._projectChoice)
        
        w, h = self._projectChoice.GetSize()

        self._logicalBtn = wx.lib.buttons.GenBitmapToggleButton(panel, -1, getLogicalModeOffBitmap(), size=(h,h))
        self._logicalBtn.SetBitmapSelected(getLogicalModeOnBitmap())
        self._logicalBtn.SetToolTipString(_("Project View"))
        panel.Bind(wx.EVT_BUTTON, self.OnSelectMode, self._logicalBtn)
        self._physicalBtn = wx.lib.buttons.GenBitmapToggleButton(panel, -1, getPhysicalModeOffBitmap(), size=(h,h))
        self._physicalBtn.SetBitmapSelected(getPhysicalModeOnBitmap())
        self._physicalBtn.SetToolTipString(_("Resource View"))
        self._physicalBtn.SetToggle(True)
        panel.Bind(wx.EVT_BUTTON, self.OnSelectMode, self._physicalBtn)
        
        butSizer.Add(self._projectChoice, 1, wx.EXPAND)
        butSizer.Add(self._logicalBtn, 0)
        butSizer.Add(self._physicalBtn, 0)
        self.panel_sizer.Add(butSizer, 0, wx.EXPAND)
        

        #Toolbar
        self._project_tb = tb = wx.ToolBar(panel,  -1, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT |wx.TB_NODIVIDER)
        tb.SetToolBitmapSize((16,16))
        self.panel_sizer.Add(tb, 0, wx.EXPAND|wx.TOP, 2)
        
        #Only one of the following buttons is needed.
        tb.AddSimpleTool(ProjectService.NEW_PROJECT_ID, images.load("project/new.png"), _('New Project'))
        ####wx.EVT_TOOL(panel, self._logicalID, self.OnSelectMode)
        
        tb.AddSimpleTool(ProjectService.OPEN_PROJECT_ID, images.load("project/open.png"), _('Open Project'))
        tb.AddSimpleTool(ProjectService.SAVE_PROJECT_ID, images.load("project/save.png"), _('Save Project'))
        tb.AddSimpleTool(ProjectService.ARCHIVE_PROJECT_ID, images.load("project/archive.png"), _('Archive Project'))
        
        tb.AddSeparator()
        tb.AddSimpleTool(ProjectService.IMPORT_FILES_ID, images.load("project/import.png"), _('Import Files...'))
        tb.AddSimpleTool(ProjectService.ADD_NEW_FILE_ID, images.load("project/new_file.png"), _('New File'))
        tb.AddSimpleTool(ProjectService.ADD_FOLDER_ID, images.load("project/folder.png"), _('New Folder'))
        tb.AddSimpleTool(ProjectService.ADD_PACKAGE_FOLDER_ID, images.load("project/package.png"), _('New Package Folder'))
        tb.AddSimpleTool(Property.FilePropertiesService.PROPERTIES_ID, images.load("project/properties.png"), _('Project/File Properties'))
        tb.Realize()
        
        self._resource_tb = tb2 = wx.ToolBar(panel,  -1, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT |wx.TB_NODIVIDER)
        tb2.SetToolBitmapSize((16,16))
        self.panel_sizer.Add(tb2, 0, wx.EXPAND|wx.TOP, 2)
        tb2.AddSimpleTool(ResourceView.ADD_FOLDER_ID, images.load("project/folder.png"), _('New Folder'))
        tb2.AddSimpleTool(ResourceView.REFRESH_PATH_ID, images.load("arrow_refresh.png"), _('Refresh Folder'))
        wx.EVT_TOOL(panel, ResourceView.ADD_FOLDER_ID, self.OnResourceViewToolClicked)
        wx.EVT_TOOL(panel, ResourceView.REFRESH_PATH_ID, self.OnResourceViewToolClicked)
        tb2.Realize()
        
        self.dirSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.dir_ctrl = ResourceView.ResourceTreeCtrl(panel, -1, style = wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_DEFAULT_STYLE | wx.TR_EXTENDED)
        self.dir_ctrl.AddRoot(_("Resources"))
        self.dirSizer.Add(self.dir_ctrl, 1, wx.EXPAND)
        
        self.treeSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._treeCtrl = ProjectTreeCtrl(panel, -1, style = wx.TR_HAS_BUTTONS | wx.TR_EDIT_LABELS | wx.TR_DEFAULT_STYLE | wx.TR_MULTIPLE | wx.TR_EXTENDED)
        rootItem = self.AddProjectRoot(_("Projects"))
        self.treeSizer.Add(self._treeCtrl, 1, wx.EXPAND)
        if self._embeddedWindow:
            self.panel_sizer.Add(self.dirSizer, 1, wx.EXPAND|wx.BOTTOM, HALF_SPACE)
            self.panel_sizer.Add(self.treeSizer, 1, wx.EXPAND|wx.BOTTOM, HALF_SPACE)
        else:
            self.panel_sizer.Add(self.treeSizer, 1, wx.EXPAND)
            self.panel_sizer.Add(self.dirSizer, 1, wx.EXPAND)
        panel.SetSizer(self.panel_sizer)
        
        self.Activate()
        pane_info = self._service.CreatePane(aui.AUI_DOCK_LEFT,control=panel)
        frame = pane_info
        self.SetFrame(frame)

        if wx.GetApp().IsMDI():
            wx.EVT_SET_FOCUS(self._treeCtrl, self.OnFocus)
            wx.EVT_KILL_FOCUS(self._treeCtrl, self.OnKillFocus)

        if self.GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            wx.EVT_TREE_ITEM_ACTIVATED(self._treeCtrl, self._treeCtrl.GetId(), self.OnOpenSelectionSDI)
        else:
            wx.EVT_TREE_ITEM_ACTIVATED(self._treeCtrl, self._treeCtrl.GetId(), self.OnOpenSelection)
        wx.EVT_TREE_BEGIN_LABEL_EDIT(self._treeCtrl, self._treeCtrl.GetId(), self.OnBeginLabelEdit)
        wx.EVT_TREE_END_LABEL_EDIT(self._treeCtrl, self._treeCtrl.GetId(), self.OnEndLabelEdit)
        wx.EVT_RIGHT_DOWN(self._treeCtrl, self.OnRightClick)
        wx.EVT_KEY_DOWN(self._treeCtrl, self.OnKeyPressed)
        wx.EVT_TREE_ITEM_COLLAPSED(self._treeCtrl, self._treeCtrl.GetId(), self.SaveFolderState)
        wx.EVT_TREE_ITEM_EXPANDED(self._treeCtrl, self._treeCtrl.GetId(), self.SaveFolderState)
        wx.EVT_TREE_BEGIN_DRAG(self._treeCtrl, self._treeCtrl.GetId(), self.OnBeginDrag)
        wx.EVT_TREE_END_DRAG(self._treeCtrl, self._treeCtrl.GetId(), self.OnEndDrag)
        ###wx.EVT_LEFT_DOWN(self._treeCtrl, self.OnLeftClick)

        # drag-and-drop support
        dt = ProjectFileDropTarget(self)
        self._treeCtrl.SetDropTarget(dt)
        self.SelectView()
        
        return True

    def OnChangeFilename(self):
        pass
        
    def StopImport(self,stop_importing=True):
        self._stop_importing = stop_importing

    def OnSelectMode(self, event):
        btn = event.GetEventObject()
        down = event.GetIsDown()
        if btn == self._logicalBtn:
            self._physicalBtn.SetToggle(not down)
        else:  # btn == self._physicalBtn:
            self._logicalBtn.SetToggle(not down)
        self.SelectView()
            
    def SelectView(self):    
        if self.GetMode() == ProjectView.RESOURCE_VIEW:
            ResourceView.ResourceView(self).LoadRoots()
            #only load file resource one,avoid load many times when switch toogle button
            if not ResourceView.ResourceView(self).IsLoad:
                ResourceView.ResourceView(self).LoadResource()
            self.panel_sizer.Hide(self.treeSizer)
            self._project_tb.Hide()
            self._resource_tb.Show()
            self.panel_sizer.Show(self.dirSizer)
        else:
            self.LoadDocuments()
            #self.LoadProject(self.GetDocument())
            self._resource_tb.Hide()
            self._project_tb.Show()
            self.panel_sizer.Show(self.treeSizer)
            self.panel_sizer.Hide(self.dirSizer)
        self.panel_sizer.Layout()

    def GetMode(self):
        if not self._physicalBtn.up:
            return ProjectView.RESOURCE_VIEW
        else:  # elif self._logicalBtn.GetValue():
            return ProjectView.PROJECT_VIEW


    def OnProjectSelect(self, event=None):
        selItem = self._projectChoice.GetSelection()
        if selItem == wx.NOT_FOUND:
            return
        if self.GetMode() == ProjectView.RESOURCE_VIEW:
            ResourceView.ResourceView(self).SelectIndex = selItem
            name = self._projectChoice.GetClientData(selItem)
            ResourceView.ResourceView(self).LoadRoot(name)
        else:
            document = self._projectChoice.GetClientData(selItem)
            self.SetDocument(document)
            self.LoadProject(self.GetDocument())
            if self.GetDocument():
                filename = self.GetDocument().GetFilename()
            else:
                filename = ''
            self._projectChoice.SetToolTipString(filename)


    def OnSize(self, event):
        event.Skip()
        wx.CallAfter(self.GetFrame().Layout)


    def OnBeginDrag(self, event):
        if self.GetMode() == ProjectView.RESOURCE_VIEW:
            return
            
        item = event.GetItem()
        if item.IsOk():
            self._draggingItems = []
            for item in self._treeCtrl.GetSelections():
                if self._IsItemFile(item):
                    self._draggingItems.append(item)
            if len(self._draggingItems):
                event.Allow()


    def OnEndDrag(self, event):
        item = event.GetItem()
        if item.IsOk():
            files = []
            for ditem in self._draggingItems:
                file = self._GetItemFile(ditem)
                if file not in files:
                    files.append(file)
                    
            folderPath = self._GetItemFolderPath(item)

            self.GetDocument().GetCommandProcessor().Submit(ProjectMoveFilesCommand(self.GetDocument(), files, folderPath))


    def WriteProjectConfig(self):
        if self.GetMode() == ProjectView.RESOURCE_VIEW:
            return
        frame = self.GetFrame()
        config = wx.ConfigBase_Get()
        if frame and not self._embeddedWindow:
            if not frame.IsMaximized():
                config.WriteInt("ProjectFrameXLoc", frame.GetPositionTuple()[0])
                config.WriteInt("ProjectFrameYLoc", frame.GetPositionTuple()[1])
                config.WriteInt("ProjectFrameXSize", frame.GetSizeTuple()[0])
                config.WriteInt("ProjectFrameYSize", frame.GetSizeTuple()[1])
            config.WriteInt("ProjectFrameMaximized", frame.IsMaximized())

        if config.ReadInt("ProjectSaveDocs", True):
            projectFileNames = []
            curProject = None

            if self._projectChoice:
                for i in range(self._projectChoice.GetCount()):
                    project = self._projectChoice.GetClientData(i)
                    if not project.OnSaveModified():
                        return
                    if project.GetDocumentSaved():  # Might be a new document and "No" selected to save it
                        projectFileNames.append(str(project.GetFilename()))
            config.Write("ProjectSavedDocs", projectFileNames.__repr__())

            document = None
            if self._projectChoice.GetCount():
                i = self._projectChoice.GetSelection()
                if i != wx.NOT_FOUND:
                    document = self._projectChoice.GetClientData(i)
            if document:
                config.Write("ProjectCurrent", document.GetFilename())
            else:
                config.DeleteEntry("ProjectCurrent")


    def OnClose(self, deleteWindow = True):
        if self.GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            self.WriteProjectConfig()
            
        project = self.GetDocument()
        if not project:
            return True
        if not project.Close():
            return True

        if not deleteWindow:
            self.RemoveCurrentDocumentUpdate()
        else:
            # need this to accelerate closing down app if treeCtrl has lots of items
            self._treeCtrl.Freeze()
            try:
                rootItem = self._treeCtrl.GetRootItem()
                self._treeCtrl.DeleteChildren(rootItem)
            finally:
                self._treeCtrl.Thaw()

        # We don't need to delete the window since it is a floater/embedded
        return True


    def _GetParentFrame(self):
        return wx.GetTopLevelParent(self.GetFrame())
        
    def AddProgressFiles(self,newFilePaths,range_value,projectDoc,parent):
        self._treeCtrl.Freeze()
        try:
            self._treeCtrl.UnselectAll()
            project = projectDoc.GetModel()
            projectDir = project.homeDir
            rootItem = self._treeCtrl.GetRootItem()
            # add new folders and new items
            addList = []                    
            for filePath in newFilePaths:
                file = project.FindFile(filePath)
                if file:
                    folderPath = file.logicalFolder
                    if folderPath:
                        if os.path.basename(filePath).lower() == self.PACKAGE_INIT_FILE:
                            self._treeCtrl.AddFolder(folderPath,True)
                        else:
                            self._treeCtrl.AddFolder(folderPath)
                        folder = self._treeCtrl.FindFolder(folderPath)
                    else:
                        folder = rootItem
                    if folderPath is None:
                        folderPath = ""
                    dest_path = os.path.join(projectDir,folderPath,os.path.basename(filePath))
                    if not parserutils.ComparePath(filePath,dest_path):
                        if os.path.exists(dest_path):
                            project.RemoveFile(file)
                            if ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_YES or\
                                        ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_NO:
                                prompt_dlg = ProjectUI.PromptMessageDialog(parent,-1,_("Project File Exists"),\
                                        _("The file %s is already exist in project ,Do You Want to overwrite it?") % filePath)
                                status = prompt_dlg.ShowModal()
                                ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID = status
                                prompt_dlg.Destroy()
                                if ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_NO:
                                    range_value += 1
                                    Publisher.sendMessage(ImportFiles.NOVAL_MSG_UI_IMPORT_FILES_PROGRESS,value=range_value,\
                                                    is_cancel=self._stop_importing)
                                    continue
                        dest_dir_path = os.path.dirname(dest_path)
                        if not os.path.exists(dest_dir_path):
                            parserutils.MakeDirs(dest_dir_path)
                            
                        if ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_YESTOALL or\
                            ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_YES:
                            shutil.copyfile(filePath,dest_path)
                        file.filePath = dest_path
                    if not self._treeCtrl.FindItem(file.filePath,folder):
                        item = self._treeCtrl.AppendItem(folder, os.path.basename(file.filePath), file)
                        addList.append(item)
                    self._treeCtrl.Expand(folder)
                range_value += 1
                #wx.CallAfter(Publisher.sendMessage, ImportFiles.NOVAL_MSG_UI_IMPORT_FILES_PROGRESS, \
                 #            value=range_value,is_cancel=self._stop_importing)
                Publisher.sendMessage(ImportFiles.NOVAL_MSG_UI_IMPORT_FILES_PROGRESS,value=range_value,is_cancel=self._stop_importing)

            # sort folders with new items
            parentList = []
            for item in addList:
                parentItem = self._treeCtrl.GetItemParent(item)
                if parentItem not in parentList:
                    parentList.append(parentItem)
            for parentItem in parentList:
                self._treeCtrl.SortChildren(parentItem)

        finally:
            self._treeCtrl.Thaw()

    def OnUpdate(self, sender = None, hint = None):
        if wx.lib.docview.View.OnUpdate(self, sender, hint):
            return
        
        if hint:
            if hint[0] == "add":
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                    
                self._treeCtrl.Freeze()

                try:
                    newFilePaths = hint[2]  # need to be added and selected, and sorted
                    oldFilePaths = hint[3]  # need to be selected
                    self._treeCtrl.UnselectAll()
                    
                    mode = self.GetMode()
                    
                    project = projectDoc.GetModel()
                    projectDir = project.homeDir
                    rootItem = self._treeCtrl.GetRootItem()
                        
                    # add new folders and new items
                    addList = []                    
                    for filePath in newFilePaths:
                        file = project.FindFile(filePath)
                        if file:
                            folderPath = file.logicalFolder
                            if folderPath:
                                if os.path.basename(filePath).lower() == self.PACKAGE_INIT_FILE:
                                    self._treeCtrl.AddFolder(folderPath,True)
                                else:
                                    self._treeCtrl.AddFolder(folderPath)
                                folder = self._treeCtrl.FindFolder(folderPath)
                            else:
                                folder = rootItem
                            if folderPath is None:
                                folderPath = ""
                            dest_path = os.path.join(projectDir,folderPath,os.path.basename(filePath))
                            if not parserutils.ComparePath(filePath,dest_path):
                                if os.path.exists(dest_path):
                                    #the dest file is already in the project
                                    if project.FindFile(dest_path):
                                        project.RemoveFile(file)
                                    if ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_YES or\
                                                ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_NO:
                                        prompt_dlg = ProjectUI.PromptMessageDialog(wx.GetApp().GetTopWindow(),-1,_("Project File Exists"),\
                                                _("The file %s is already exist in project ,Do You Want to overwrite it?") % filePath)
                                        status = prompt_dlg.ShowModal()
                                        ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID = status
                                        prompt_dlg.Destroy()
                                if ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_YESTOALL or\
                                    ProjectUI.PromptMessageDialog.DEFAULT_PROMPT_MESSAGE_ID == wx.ID_YES:
                                    try:
                                        shutil.copyfile(filePath,dest_path)
                                    except Exception as e:
                                        wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)
                                        return
                                file.filePath = dest_path
                            if not self._treeCtrl.FindItem(file.filePath,folder):
                                item = self._treeCtrl.AppendItem(folder, os.path.basename(file.filePath), file)
                                addList.append(item)
                            self._treeCtrl.Expand(folder)
                    # sort folders with new items
                    parentList = []
                    for item in addList:
                        parentItem = self._treeCtrl.GetItemParent(item)
                        if parentItem not in parentList:
                            parentList.append(parentItem)
                    for parentItem in parentList:
                        self._treeCtrl.SortChildren(parentItem)
    
                    # select all the items user wanted to add
                    lastItem = None
                    for filePath in (oldFilePaths + newFilePaths):
                        item = self._treeCtrl.FindItem(filePath)
                        if item:
                            self._treeCtrl.SelectItem(item)
                            lastItem = item
                            
                    if lastItem:        
                        self._treeCtrl.EnsureVisible(lastItem)

                finally:
                    self._treeCtrl.Thaw()
                return
                
            elif hint[0] == "progress_add":
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                newFilePaths = hint[2]  # need to be added and selected, and sorted
                range_value = hint[3]  # need to be selected
                parent = hint[4]
                self.AddProgressFiles(newFilePaths,range_value,projectDoc,parent)
                return

            elif hint[0] == "remove":
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                    
                self._treeCtrl.Freeze()

                try:
                    filePaths = hint[2]
                    self._treeCtrl.UnselectAll()
                    
                    for filePath in filePaths:
                        item = self._treeCtrl.FindItem(filePath)
                        if item:
                            self._treeCtrl.Delete(item)
    
                    self._treeCtrl.UnselectAll()  # wxBug: even though we unselected earlier, an item still gets selected after the delete
                
                finally:
                    self._treeCtrl.Thaw()
                return
                
            elif hint[0] == "rename":
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                    
                self._treeCtrl.Freeze()
                try:
                    item = self._treeCtrl.FindItem(hint[2])
                    self._treeCtrl.SetItemText(item, os.path.basename(hint[3]))
                    self._treeCtrl.EnsureVisible(item)
                finally:
                    self._treeCtrl.Thaw()
                return
                
            elif hint[0] == "rename folder":
                projectDoc = hint[1]
                if self.GetDocument() != projectDoc:  # project being updated isn't currently viewed project
                    return
                    
                self._treeCtrl.Freeze()
                try:
                    item = self._treeCtrl.FindFolder(hint[2])
                    if item:
                        self._treeCtrl.UnselectAll()
                        self._treeCtrl.SetItemText(item, os.path.basename(hint[3]))
                        self._treeCtrl.SortChildren(self._treeCtrl.GetItemParent(item))
                        self._treeCtrl.SelectItem(item)
                        self._treeCtrl.EnsureVisible(item)
                finally:
                    self._treeCtrl.Thaw()
                return
     

    def RemoveProjectUpdate(self, projectDoc):
        """ Called by service after deleting a project, need to remove from project choices """
        i = self._projectChoice.FindString(self._MakeProjectName(projectDoc))
        self._projectChoice.Delete(i)

        numProj = self._projectChoice.GetCount()
        if i >= numProj:
            i = numProj - 1
        if i >= 0:
            self._projectChoice.SetSelection(i)
        self._documents.remove(self._document)
        wx.GetApp().GetDocumentManager().CloseDocument(projectDoc, False)
        self._document = None
        self.OnProjectSelect()


    def RemoveCurrentDocumentUpdate(self, i=-1):
        """ Called by service after deleting a project, need to remove from project choices """
        i = self._projectChoice.GetSelection()
        assert(self._document == self._projectChoice.GetClientData(i))
        self._projectChoice.Delete(i)

        numProj = self._projectChoice.GetCount()
        if i >= numProj:
            i = numProj - 1
        if i >= 0:
            self._projectChoice.SetSelection(i)
        self._documents.remove(self._document)
        self._document = None
        self.OnProjectSelect()
 
    def CloseProject(self):
        projectDoc = self.GetDocument()
        if projectDoc:
            projectService = wx.GetApp().GetService(ProjectService)
            if projectService:
                openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
                #close all open documents of this project first
                for openDoc in openDocs[:]:  # need to make a copy, as each file closes we're off by one
                    if projectDoc == openDoc:  # close project last
                        continue
                        
                    if projectDoc == projectService.FindProjectFromMapping(openDoc):
                        self.GetDocumentManager().CloseDocument(openDoc, False)
                        
                        projectService.RemoveProjectMapping(openDoc)
                        if hasattr(openDoc, "GetModel"):
                            projectService.RemoveProjectMapping(openDoc.GetModel())
            #delete project regkey config
            wx.ConfigBase_Get().DeleteGroup(getProjectKeyName(projectDoc.GetModel().Id))
            projectDoc.document_watcher.RemoveFileDoc(projectDoc)
            if self.GetDocumentManager().CloseDocument(projectDoc, False):
                self.RemoveCurrentDocumentUpdate()
            if not self.GetDocument():
                self.AddProjectRoot(_("Projects"))
    def ProcessEvent(self, event):
        id = event.GetId()
        if id == ProjectService.CLOSE_PROJECT_ID:
            self.CloseProject()
            return True
        elif id == ProjectService.ADD_FILES_TO_PROJECT_ID:
            self.OnAddFileToProject(event)
            return True
        elif id == ProjectService.ADD_DIR_FILES_TO_PROJECT_ID:
            self.OnAddDirToProject(event)
            return True
        elif id == ProjectService.ADD_CURRENT_FILE_TO_PROJECT_ID:
            return False  # Implement this one in the service
        elif id == ProjectService.ADD_NEW_FILE_ID:
            self.OnAddNewFile(event)
            return True
        elif id == ProjectService.ADD_FOLDER_ID:
            self.OnAddFolder(event)
            return True
        elif id == ProjectService.ADD_PACKAGE_FOLDER_ID:
            self.OnAddPackageFolder(event)
            return True
        elif id == ProjectService.RENAME_ID:
            self.OnRename(event)
            return True
        elif id == wx.ID_CLEAR:
            self.DeleteFromProject(event)
            return True
        elif id == ProjectService.DELETE_PROJECT_ID:
            self.OnDeleteProject(event)
            return True
        elif id == wx.ID_CUT:
            self.OnCut(event)
            return True
        elif id == wx.ID_COPY:
            self.OnCopy(event)
            return True
        elif id == wx.ID_PASTE:
            self.OnPaste(event)
            return True
        elif (id == wx.ID_CLEAR
        or id == ProjectService.REMOVE_FROM_PROJECT):
            self.RemoveFromProject(event)
            return True
        elif id == wx.ID_SELECTALL:
            self.OnSelectAll(event)
            return True
        elif id == ProjectService.OPEN_SELECTION_ID:
            self.OnOpenSelection(event)
            return True
        elif id == Property.FilePropertiesService.PROPERTIES_ID:
            self.OnProperties(event)
            return True
        elif id == ProjectService.PROJECT_PROPERTIES_ID:
            self.OnProjectProperties()
            return True
        elif id == ProjectService.IMPORT_FILES_ID:
            self.ImportFilesToProject(event)
            return True
        elif id == ProjectService.OPEN_PROJECT_PATH_ID:
            self.OpenProjectPath(event)
            return True
        elif id == ProjectService.NEW_PROJECT_ID:
            self.NewProject(event)
            return True
        elif id == ProjectService.OPEN_PROJECT_ID:
            self.OpenProject(event)
            return True
        elif id == ProjectService.SAVE_PROJECT_ID:
            self.SaveProject(event)
            return True
        elif id == ProjectService.SET_PROJECT_STARTUP_FILE_ID:
            self.SetProjectStartupFile()
            return True
        elif id == ProjectService.START_RUN_ID:
            self.RunFile()
            return True
        elif id == ProjectService.START_DEBUG_ID:
            self.DebugRunFile()
            return True
        elif id == DebuggerService.DebuggerService.BREAK_INTO_DEBUGGER_ID:
            self.BreakintoDebugger()
            return True
        elif id == ProjectService.OPEN_FOLDER_PATH_ID:
            self.OpenFolderPath(event)
            return True
        elif id == ProjectService.OPEN_TERMINAL_PATH_ID:
            self.OpenPromptPath(event)
            return True
        elif id == ProjectService.COPY_PATH_ID:
            self.CopyPath(event)
            return True
        elif id == ProjectService.CLEAN_PROJECT_ID:
            self.CleanProject()
            return True
        elif id == ProjectService.ARCHIVE_PROJECT_ID:
            self.ArchiveProject()
            return True
        else:
            return False
            
    def OnResourceViewToolClicked(self, event):
        id = event.GetId()
        if id == ResourceView.REFRESH_PATH_ID or id == ResourceView.ADD_FOLDER_ID:
            return self.dir_ctrl.ProcessEvent(event)
            
    def SetProjectStartupFile(self):
        item = self._treeCtrl.GetSingleSelectItem()
        self.SetProjectStartupFileItem(item)
        
    def SetProjectStartupFileItem(self,item):
        if item == self._bold_item:
            return
        if self._bold_item is not None:
            self._treeCtrl.SetItemBold(self._bold_item ,False)
        pjfile = self._GetItemFile(item)
        self._treeCtrl.SetItemBold(item)
        self._bold_item = item
        self.GetDocument().GetModel().StartupFile = pjfile
        self.GetDocument().Modify(True)
        
    def RunFile(self):
        selected_file_path = self.GetSelectedFile()
        if selected_file_path is None and not fileutils.is_python_file(selected_file_path):
            return
        wx.GetApp().GetService(DebuggerService.DebuggerService).Run(selected_file_path)
        
    def DebugRunFile(self):
        selected_file_path = self.GetSelectedFile()
        if selected_file_path is None and not fileutils.is_python_file(selected_file_path):
            return
        wx.GetApp().GetService(DebuggerService.DebuggerService).RunWithoutDebug(selected_file_path)
        
    def BreakintoDebugger(self):
        selected_file_path = self.GetSelectedFile()
        if selected_file_path is None and not fileutils.is_python_file(selected_file_path):
            return
        wx.GetApp().GetService(DebuggerService.DebuggerService).BreakIntoDebugger(selected_file_path)
            
    def NewProject(self,event):
        docManager = wx.GetApp().GetDocumentManager()
        for template in docManager.GetTemplates():
            if template.GetDocumentType() == ProjectDocument:
                doc = template.CreateDocument("", flags = wx.lib.docview.DOC_NEW)
                break
                
    def OpenProject(self,event):
        descr = _("Project File") + "(*%s)|*%s" % (PROJECT_EXTENSION,PROJECT_EXTENSION)
        dlg = wx.FileDialog(self.GetFrame(),_("Open Project") ,
                       wildcard = descr,
                       style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        project_path = dlg.GetPath()
        dlg.Destroy()
        
        doc = self.GetDocumentManager().CreateDocument(project_path, wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
        if not doc:  # project already open
            self.SetProject(project_path)
        elif doc:
            AddProjectMapping(doc)
                
    def SaveProject(self,event):
        doc = self.GetDocument()
        if doc.IsModified():
            wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
            wx.GetApp().GetTopWindow().PushStatusText(_("Project is saving..."))
            if doc.OnSaveDocument(doc.GetFilename()):
                wx.GetApp().GetTopWindow().PushStatusText(_("Project save success."))
            else:
                wx.GetApp().GetTopWindow().PushStatusText(_("Project save failed."))
            wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            
    def CleanProject(self):
        doc = self.GetDocument()
        path = os.path.dirname(doc.GetFilename())
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        for root,path,files in os.walk(path):
            for filename in files:
                fullpath = os.path.join(root,filename)
                ext = strutils.GetFileExt(fullpath)
                if ext in ProjectDocument.BAN_FILE_EXTS:
                    wx.GetApp().GetTopWindow().PushStatusText(_("Cleaning \"%s\".") % fullpath)
                    try:
                        os.remove(fullpath)
                    except:
                        pass
        wx.GetApp().GetTopWindow().PushStatusText(_("Clean Completed."))
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        
    def ArchiveProject(self):
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        doc = self.GetDocument()
        path = os.path.dirname(doc.GetFilename())
        try:
            wx.GetApp().GetTopWindow().PushStatusText(_("Archiving..."))
            datetime_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
            zip_name = doc.GetModel().Name + "_" + datetime_str + ".zip"
            zip_path = doc.ArchiveProject(os.path.join(path,zip_name))
            wx.MessageBox(_("Success archived to %s") % zip_path,_("Archive Success"),style = wx.OK)
            wx.GetApp().GetTopWindow().PushStatusText(_("Success archived to %s") % zip_path)
        except Exception as e:
            msg = unicode(e)
            wx.MessageBox(msg,_("Archive Error"),style = wx.OK|wx.ICON_ERROR)
            wx.GetApp().GetTopWindow().PushStatusText(_("Archive Error"))
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
                
    def BuildFileMaps(self,file_list):
        d = {}
        for file_path in file_list:
            dir_path = os.path.dirname(file_path)
            if not d.has_key(dir_path):
                d[dir_path] = [file_path]
            else:
                d[dir_path].append(file_path)
        return d
        
    def StartCopyFilesToProject(self,parent,file_list,src_path,dest_path):
        self.copy_thread = threading.Thread(target = self.CopyFilesToProject,args=(parent,file_list,src_path,dest_path))
        self.copy_thread.start()
        
    def BuildFileList(self,file_list):
        '''put the package __init__.py to the first item'''
        package_initfile_path = None
        for file_path in file_list:
            if os.path.basename(file_path).lower() == self.PACKAGE_INIT_FILE:
                package_initfile_path = file_path
                file_list.remove(file_path)
                break
        if package_initfile_path is not None:
            file_list.insert(0,package_initfile_path)
        
    @WxThreadSafe.call_after
    def CopyFilesToProject(self,parent,file_list,src_path,dest_path):
        files_dict = self.BuildFileMaps(file_list)
        copy_file_count = 0
        for dir_path in files_dict:
            if self._stop_importing:
                break
            file_path_list = files_dict[dir_path]
            #should put package __init__.py to the first position of file list
            self.BuildFileList(file_path_list)
            folder_path = dir_path.replace(src_path,"").replace(os.sep,"/").lstrip("/").rstrip("/")
            paths = dest_path.split(os.sep)
            if len(paths) > 1:
                dest_folder_path =  "/".join(paths[1:]) 
                if folder_path != "":
                    dest_folder_path +=  "/" + folder_path
            else:
                dest_folder_path = folder_path
            self.GetDocument().GetCommandProcessor().Submit(\
                    ProjectAddProgressFilesCommand(parent,self.GetDocument(), file_path_list, folderPath=dest_folder_path,range_value = copy_file_count))
            copy_file_count += len(file_path_list)
                
    def OpenProjectPath(self,event):
        document = self.GetDocument()
        fileutils.open_file_directory(document.GetFilename())
        
    def OpenFolderPath(self,event):
        document = self.GetDocument()
        project_path = os.path.dirname(document.GetFilename())
        item = self._treeCtrl.GetSingleSelectItem()
        if self._IsItemFile(item):
            filePath = self._GetItemFilePath(item)
        else:
            filePath = fileutils.opj(os.path.join(project_path,self._GetItemFolderPath(item)))
        err_code,msg = fileutils.open_file_directory(filePath)
        if err_code != ERROR_OK:
            wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
        
    def OpenPromptPath(self,event):
        document = self.GetDocument()
        project_path = os.path.dirname(document.GetFilename())
        item = self._treeCtrl.GetSingleSelectItem()
        if self._IsItemFile(item):
            filePath = os.path.dirname(self._GetItemFilePath(item))
        else:
            filePath = fileutils.opj(os.path.join(project_path,self._GetItemFolderPath(item)))
        err_code,msg = fileutils.open_path_in_terminator(filePath)
        if err_code != ERROR_OK:
            wx.MessageBox(msg,style = wx.OK|wx.ICON_ERROR)
            
    def CopyPath(self,event):
        document = self.GetDocument()
        project_path = os.path.dirname(document.GetFilename())
        item = self._treeCtrl.GetSingleSelectItem()
        if self._IsItemFile(item):
            filePath = self._GetItemFilePath(item)
        else:
            filePath = fileutils.opj(os.path.join(project_path,self._GetItemFolderPath(item)))
        sysutilslib.CopyToClipboard(filePath)

    def ImportFilesToProject(self,event):
        items = self._treeCtrl.GetSelections()
        if items:
            item = items[0]
        else:
            item = self._treeCtrl.GetRootItem()
        folderPath = self._GetItemFolderPath(item)
        frame = ImportFiles.ImportFilesDialog(wx.GetApp().GetTopWindow(),-1,_("Import Files"),folderPath)
        frame.CenterOnParent()
        if frame.ShowModal() == wx.ID_OK:
            if not self._treeCtrl.IsExpanded(item):
                self._treeCtrl.Expand(item)
            #muse unsubscribe the registered msg,otherwise will sendmessage to the deleted dialog
            Publisher.unsubscribe(frame.UpdateImportProgress,ImportFiles.NOVAL_MSG_UI_IMPORT_FILES_PROGRESS)
        frame.Destroy()
        
    def ProcessUpdateUIEvent(self, event):
        # Hack: The edit menu is not being set for projects that are preloaded at startup, so make sure it is OK here
        if self._checkEditMenu:
            doc = self.GetDocument()
            if doc and not doc.GetCommandProcessor().GetEditMenu():
                doc.GetCommandProcessor().SetEditMenu(wx.GetApp().GetEditMenu(self._GetParentFrame()))
            self._checkEditMenu = False

        id = event.GetId()
        if id == wx.ID_CLOSE:
            # Too confusing, so disable closing from "File | Close" menu, must close from "Project | Close Current Project" menu
            if self.ProjectHasFocus() or self.FilesHasFocus():
                event.Enable(False)
                return True
            else:
                return False
        elif (id == ProjectService.ADD_FILES_TO_PROJECT_ID
        or id == ProjectService.ADD_DIR_FILES_TO_PROJECT_ID
        or id == ProjectService.CLOSE_PROJECT_ID
        or id == ProjectService.DELETE_PROJECT_ID
        or id == ProjectService.SAVE_PROJECT_ID
        or id == ProjectService.OPEN_PROJECT_PATH_ID
        or id == ProjectService.IMPORT_FILES_ID
        or id == ProjectService.CLEAN_PROJECT_ID
        or id == ProjectService.ARCHIVE_PROJECT_ID):
            event.Enable(self.GetDocument() != None)
            return True
        elif id == ProjectService.ADD_CURRENT_FILE_TO_PROJECT_ID:
            event.Enable(False)  # Implement this one in the service
            return True
        elif (id == ProjectService.ADD_FOLDER_ID
            or id == ProjectService.ADD_PACKAGE_FOLDER_ID
            or id == ProjectService.ADD_NEW_FILE_ID):
            event.Enable((self.GetDocument() != None) and (self.GetMode() == ProjectView.PROJECT_VIEW))
            return True
        elif (id == wx.ID_CUT
        or id == wx.ID_COPY
        or id == ProjectService.OPEN_SELECTION_ID):
            event.Enable(self._HasFilesSelected())
            return True
        elif (id == wx.ID_CLEAR
        or id == ProjectService.RENAME_ID):
            items = self._treeCtrl.GetSelections()
            if items:
                hasViewSelected = False
                for item in items:
                    if self._IsItemFile(item):
                        file = self._GetItemFile(item)
                        if file.type == 'xform':
                            hasViewSelected = True
                            break
                if hasViewSelected:
                    event.Enable(False)
                    return True

            event.Enable(self._HasFilesSelected() or (self.GetDocument() != None and self.GetMode() == ProjectView.PROJECT_VIEW and self._HasFoldersSelected()))
            return True
        elif id == wx.ID_PASTE:
            event.Enable(self.CanPaste())
            return True
        elif id == wx.ID_SELECTALL:
            event.Enable(self._HasFiles())
            return True
        elif (id == wx.ID_PREVIEW
        or id == wx.ID_PRINT):
            event.Enable(False)
            return True
        else:
            return False

    #----------------------------------------------------------------------------
    # Display Methods
    #----------------------------------------------------------------------------

    def IsShown(self):
        if not self.GetFrame():
            return False
        return self._viewFrame.IsShown()


    def Hide(self):
        self.Show(False)


    def Show(self, show = True):
        self._viewFrame.Show(show)
        self._service._frame._mgr.Update()
       # if wx.GetApp().IsMDI():
        #    mdiParentFrame = wx.GetApp().GetTopWindow()
        #    mdiParentFrame.ShowEmbeddedWindow(self.GetFrame(), show)


    #----------------------------------------------------------------------------
    # Methods for ProjectDocument and ProjectService to call
    #----------------------------------------------------------------------------

    def SetProject(self, projectPath):
        if self._service.IsLoadingProjects:
            utils.GetLogger().info("application is loading projects at startup ,do not load project document %s at this time",projectPath)
            return
        utils.GetLogger().info("load project document %s",projectPath)
        curSel = self._projectChoice.GetSelection()
        for i in range(self._projectChoice.GetCount()):
            document = self._projectChoice.GetClientData(i)
            if document.GetFilename() == projectPath:
                if curSel != i:  # don't reload if already loaded
                    self._projectChoice.SetSelection(i)
                    self.SetDocument(document)
                    self.LoadProject(document)
                    self._projectChoice.SetToolTipString(document.GetFilename())
                break
        

    def GetSelectedFile(self):
        for item in self._treeCtrl.GetSelections():
            filePath = self._GetItemFilePath(item)
            if filePath:
                return filePath
        return None


    def GetSelectedFiles(self):
        filePaths = []
        for item in self._treeCtrl.GetSelections():
            filePath = self._GetItemFilePath(item)
            if filePath and filePath not in filePaths:
                filePaths.append(filePath)
        return filePaths


    def GetSelectedPhysicalFolder(self):
        if self.GetMode() == ProjectView.PROJECT_VIEW:
            return None
        else:
            for item in self._treeCtrl.GetSelections():
                if not self._IsItemFile(item):
                    filePath = self._GetItemFolderPath(item)
                    if filePath:
                        return filePath
            return None


    def GetSelectedProject(self):
        document = self.GetDocument()
        if document:
            return document.GetFilename()
        else:
            return None
            
    def GetProjectSelection(self,document):
        for i in range(self._projectChoice.GetCount()):
            project = self._projectChoice.GetClientData(i)
            if document == project:
                return i
        return wx.NOT_FOUND

    def AddProjectToView(self, document):
        #check the project is already exist or not
        index = self.GetProjectSelection(document)
        #if proejct not exist,add the new document
        if index == wx.NOT_FOUND:
            index = self._projectChoice.Append(self._MakeProjectName(document),getProjectBitmap(), document)
            self._documents.append(document)
        self._projectChoice.SetSelection(index)
        self.OnProjectSelect()
        
    def LoadDocuments(self):
        self._projectChoice.Clear()
        for document in self._documents:
            i = self._projectChoice.Append(self._MakeProjectName(document),getProjectBitmap(), document)
            if document == self.GetDocument():
                self._projectChoice.SetSelection(i)
                
    def AddProjectRoot(self,document_or_name):
        self._treeCtrl.DeleteAllItems()
        if isinstance(document_or_name,basestring):
            name = document_or_name
            root_item = self._treeCtrl.AddRoot(name)
        else:
            document = document_or_name
            root_item = self._treeCtrl.AddRoot(document.GetModel().Name)
        project_icon_index = self._treeCtrl.GetIconIndexFromName("test%s" % PROJECT_EXTENSION)
        self._treeCtrl.SetItemImage(root_item,project_icon_index,wx.TreeItemIcon_Normal)
        return root_item

    def LoadProject(self, document):
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        self._treeCtrl.Freeze()

        try:
            rootItem = self.AddProjectRoot(document)
            #rootItem = self._treeCtrl.GetRootItem()
            #self._treeCtrl.DeleteChildren(rootItem)
            
            if document:
                mode = self.GetMode()
                docFilePath = document.GetFilename()
                
                if mode == ProjectView.PROJECT_VIEW:
                    folders = document.GetModel().logicalFolders
                else:
                    folders = document.GetModel().physicalFolders
                    
                folders.sort()
                folderItems = []
                for folderPath in folders:
                    destfolderPath = os.path.join(document.GetModel().homeDir,folderPath)
                    packageFilePath = os.path.join(destfolderPath,self.PACKAGE_INIT_FILE)
                    is_package = False
                    if os.path.exists(packageFilePath):
                        is_package = True
                    folderItems = folderItems + self._treeCtrl.AddFolder(folderPath,is_package)
                                            
                for file in document.GetModel()._files:
                    if mode == ProjectView.PROJECT_VIEW:
                        folder = file.logicalFolder
                    else:
                        folder = file.physicalFolder
                    if folder:
                        folderTree = folder.split('/')
                    
                        item = rootItem
                        for folderName in folderTree:
                            found = False
                            (child, cookie) = self._treeCtrl.GetFirstChild(item)
                            while child.IsOk():
                                if self._treeCtrl.GetItemText(child) == folderName:
                                    item = child 
                                    found = True
                                    break
                                (child, cookie) = self._treeCtrl.GetNextChild(item, cookie)
                                
                            if not found:
                                print "error folder '%s' not found for %s" % (folder, file.filePath)
                                break
                    else:
                        item = rootItem
                        
                    fileItem = self._treeCtrl.AppendItem(item, os.path.basename(file.filePath), file)
                    if file.IsStartup:
                        self._bold_item = fileItem
                        self._treeCtrl.SetItemBold(fileItem)
                        document.GetModel().StartupFile = file
                    
                self._treeCtrl.SortChildren(rootItem)
                for item in folderItems:
                    self._treeCtrl.SortChildren(item)
                    
                if utils.ProfileGetInt("LoadFolderState", True):
                    self.LoadFolderState()
    
                self._treeCtrl.SetFocus()
                (child, cookie) = self._treeCtrl.GetFirstChild(self._treeCtrl.GetRootItem())
                if child.IsOk():
                    self._treeCtrl.UnselectAll()
                    self._treeCtrl.SelectItem(child)
                    self._treeCtrl.ScrollTo(child)
                
                if self._embeddedWindow:
                    document.GetCommandProcessor().SetEditMenu(wx.GetApp().GetEditMenu(self._GetParentFrame()))

        finally:
            self._treeCtrl.Thaw()
            wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))


    def ProjectHasFocus(self):
        """ Does Project Choice have focus """
        return (wx.Window.FindFocus() == self._projectChoice)


    def FilesHasFocus(self):
        """ Does Project Tree have focus """
        winWithFocus = wx.Window.FindFocus()
        if not winWithFocus:
            return False
        while winWithFocus:
            if winWithFocus == self._treeCtrl:
                return True
            winWithFocus = winWithFocus.GetParent()
        return False


    def ClearFolderState(self):
        config = wx.ConfigBase_Get()
        config.DeleteGroup(getProjectKeyName(self.GetDocument().GetModel().Id))
        

    def SaveFolderState(self, event=None):
        """ Save the open/close state of folders """

        if self._loading:
            return
            
        folderList = []
        folderItemList = self._GetFolderItems(self._treeCtrl.GetRootItem())
        for item in folderItemList:
            if self._treeCtrl.IsExpanded(item):
                folderList.append(self._GetItemFolderPath(item))
        
        config = wx.ConfigBase_Get()
        config.Write(getProjectKeyName(self.GetDocument().GetModel().Id, self.GetMode()), repr(folderList))


    def LoadFolderState(self):
        """ Load the open/close state of folders. """
        self._loading = True
      
        config = wx.ConfigBase_Get()
        openFolderData = config.Read(getProjectKeyName(self.GetDocument().GetModel().Id, self.GetMode()), "")
        if openFolderData:
            folderList = eval(openFolderData)
                
            folderItemList = self._GetFolderItems(self._treeCtrl.GetRootItem())
            for item in folderItemList:
                folderPath = self._GetItemFolderPath(item)
                if folderPath in folderList:
                    self._treeCtrl.Expand(item)
                else:
                    self._treeCtrl.Collapse(item)

        else:
            projectService = wx.GetApp().GetService(ProjectService)
            
            folderItemList = self._GetFolderItems(self._treeCtrl.GetRootItem())
            for item in folderItemList:
                folderPath = self._GetItemFolderPath(item)
                if projectService.FindLogicalViewFolderCollapsedDefault(folderPath):  # get default initial state
                    self._treeCtrl.Collapse(item)
                else:
                    self._treeCtrl.Expand(item)
            
        self._loading = False


    #----------------------------------------------------------------------------
    # Control events
    #----------------------------------------------------------------------------

    def OnProperties(self, event):
        if self.ProjectHasFocus():
            self.OnProjectProperties()
        elif self.FilesHasFocus():
            items = self._treeCtrl.GetSelections()
            if not items:
                return
            item = items[0]
            filePropertiesService = wx.GetApp().GetService(Property.FilePropertiesService)
            filePropertiesService.ShowPropertiesDialog(self.GetDocument(),item)

    def OnProjectProperties(self, option_name=None):
        if self.GetDocument():
            filePropertiesService = wx.GetApp().GetService(Property.FilePropertiesService)
            filePropertiesService.ShowPropertiesDialog(self.GetDocument(),self._treeCtrl.GetRootItem(),option_name)
            
    def OnAddNewFile(self,event):
        items = self._treeCtrl.GetSelections()
        if items:
            item = items[0]
            folderPath = self._GetItemFolderPath(item)
        else:
            folderPath = ""
        frame = NewFile.NewFileDialog(self.GetFrame(),-1,_("New FileType"),folderPath)
        frame.CenterOnParent()
        if frame.ShowModal() == wx.ID_OK:
            if self.GetDocument().GetCommandProcessor().Submit(ProjectAddFilesCommand(self.GetDocument(), [frame.file_path], folderPath=folderPath)):
                self.OnOpenSelection(None)
        frame.Destroy()

    def OnAddFolder(self, event):
        if self.GetDocument():
            items = self._treeCtrl.GetSelections()
            if items:
                item = items[0]
                if self._IsItemFile(item):
                    item = self._treeCtrl.GetItemParent(item)
                    
                folderDir = self._GetItemFolderPath(item)
            else:
                folderDir = ""
                
            if folderDir:
                folderDir += "/"
            folderPath = "%sUntitled" % folderDir
            i = 1
            while self._treeCtrl.FindFolder(folderPath):
                i += 1
                folderPath = "%sUntitled%s" % (folderDir, i)
            projectdir = self.GetDocument().GetModel().homeDir
            destfolderPath = os.path.join(projectdir,folderPath)
            try:
                os.mkdir(destfolderPath)
            except Exception as e:
                wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)
                return
            self.GetDocument().GetCommandProcessor().Submit(ProjectAddFolderCommand(self, self.GetDocument(), folderPath))
            
            self._treeCtrl.UnselectAll()
            item = self._treeCtrl.FindFolder(folderPath)
            self._treeCtrl.SelectItem(item)
            self._treeCtrl.EnsureVisible(item)
            self.OnRename()

    def OnAddPackageFolder(self,event):
        if self.GetDocument():
            items = self._treeCtrl.GetSelections()
            if items:
                item = items[0]
                if self._IsItemFile(item):
                    item = self._treeCtrl.GetItemParent(item)
                    
                folderDir = self._GetItemFolderPath(item)
            else:
                folderDir = ""
                
            if folderDir:
                folderDir += "/"
            folderPath = "%sPackage" % folderDir
            i = 1
            while self._treeCtrl.FindFolder(folderPath):
                i += 1
                folderPath = "%sPackage%s" % (folderDir, i)
            projectdir = self.GetDocument().GetModel().homeDir
            destpackagePath = os.path.join(projectdir,folderPath)
            try:
                os.mkdir(destpackagePath)
            except Exception as e:
                wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)
                return
            self.GetDocument().GetCommandProcessor().Submit(ProjectAddFolderCommand(self, self.GetDocument(), folderPath,True))
            destpackageFile = os.path.join(destpackagePath,self.PACKAGE_INIT_FILE)
            with open(destpackageFile,"w") as f:
                self.GetDocument().GetCommandProcessor().Submit(ProjectAddFilesCommand(self.GetDocument(),[destpackageFile],folderPath))
            self._treeCtrl.UnselectAll()
            item = self._treeCtrl.FindFolder(folderPath)
            self._treeCtrl.SelectItem(item)
            self._treeCtrl.EnsureVisible(item)
            self.OnRename()

    def AddFolder(self, folderPath,is_package=False):
        self._treeCtrl.AddFolder(folderPath,is_package)
        return True

    def DeleteFolder(self, folderPath,delete_folder_files=True):
        if delete_folder_files:
            projectdir = self.GetDocument().GetModel().homeDir
            folder_local_path = os.path.join(projectdir,folderPath)
            if os.path.exists(folder_local_path):
                try:
                    fileutils.RemoveDir(folder_local_path)
                except Exception as e:
                    wx.MessageBox("Could not delete '%s'.  %s" % (os.path.basename(folder_local_path), e),
                                              _("Delete Folder"),
                                              wx.OK | wx.ICON_ERROR,
                                              self.GetFrame())
                    return
        item = self._treeCtrl.FindFolder(folderPath)
        self._treeCtrl.Freeze()
        self.DeleteFolderItems(item)
        self._treeCtrl.Delete(item)
        self._treeCtrl.Thaw()
        return True
        
    def DeleteFolderItems(self,folder_item):
        files = []
        items = self._GetChildItems(folder_item)
        for item in items:
            if self._treeCtrl.GetChildrenCount(item, False):
                self.DeleteFolderItems(item)
            else:
                file = self._GetItemFile(item)
                files.append(file)
        if files:
            self.GetDocument().GetCommandProcessor().Submit(ProjectRemoveFilesCommand(self.GetDocument(), files))

    def OnAddFileToProject(self, event):
        descr = strutils.GenFileFilters(ProjectDocument)
        dialog = wx.FileDialog(self.GetFrame(), _("Add Files"), wildcard=descr, style=wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)
        # dialog.CenterOnParent()  # wxBug: caused crash with wx.FileDialog
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        paths = dialog.GetPaths()
        dialog.Destroy()
        if len(paths):
            
            folderPath = None
            if self.GetMode() == ProjectView.PROJECT_VIEW:
                selections = self._treeCtrl.GetSelections()
                if selections:
                    item = selections[0]
                    if not self._IsItemFile(item):
                        folderPath = self._GetItemFolderPath(item)
                        
            self.GetDocument().GetCommandProcessor().Submit(ProjectAddFilesCommand(self.GetDocument(), paths, folderPath=folderPath))
        self.Activate()  # after add, should put focus on project editor


    def OnAddDirToProject(self, event):
        frame = wx.Dialog(wx.GetApp().GetTopWindow(), -1, _("Add Directory Files to Project"), size= (320,200))
        contentSizer = wx.BoxSizer(wx.VERTICAL)

        flexGridSizer = wx.FlexGridSizer(cols = 2, vgap=HALF_SPACE, hgap=HALF_SPACE)
        flexGridSizer.Add(wx.StaticText(frame, -1, _("Directory:")), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        dirCtrl = wx.TextCtrl(frame, -1, os.path.dirname(self.GetDocument().GetFilename()), size=(250,-1))
        dirCtrl.SetToolTipString(dirCtrl.GetValue())
        lineSizer.Add(dirCtrl, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        findDirButton = wx.Button(frame, -1, _("Browse..."))
        lineSizer.Add(findDirButton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, HALF_SPACE)
        flexGridSizer.Add(lineSizer, 1, wx.EXPAND)

        def OnBrowseButton(event):
            dlg = wx.DirDialog(frame, _("Choose a directory:"), style=wx.DD_DEFAULT_STYLE)
            dir = dirCtrl.GetValue()
            if len(dir):
                dlg.SetPath(dir)
            dlg.CenterOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                dirCtrl.SetValue(dlg.GetPath())
                dirCtrl.SetToolTipString(dirCtrl.GetValue())
                dirCtrl.SetInsertionPointEnd()
            dlg.Destroy()
        wx.EVT_BUTTON(findDirButton, -1, OnBrowseButton)

        visibleTemplates = []
        for template in self.GetDocumentManager()._templates:
            if template.IsVisible():
                visibleTemplates.append(template)

        choices = []
        descr = ''
        for template in visibleTemplates:
            if len(descr) > 0:
                descr = descr + _('|')
            descr = _(template.GetDescription()) + " (" + template.GetFileFilter() + ")"
            choices.append(descr)
        choices.insert(0, _("All Files") + "(*.*)")  # first item
        filterChoice = wx.Choice(frame, -1, size=(250, -1), choices=choices)
        filterChoice.SetSelection(0)
        filterChoice.SetToolTipString(_("Select file type filter."))
        flexGridSizer.Add(wx.StaticText(frame, -1, _("Files of type:")), 0, wx.ALIGN_CENTER_VERTICAL)
        flexGridSizer.Add(filterChoice, 1, wx.EXPAND)

        contentSizer.Add(flexGridSizer, 0, wx.ALL|wx.EXPAND, SPACE)

        subfolderCtrl = wx.CheckBox(frame, -1, _("Add files from subdirectories"))
        subfolderCtrl.SetValue(True)
        contentSizer.Add(subfolderCtrl, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, SPACE)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        findBtn = wx.Button(frame, wx.ID_OK, _("Add"))
        findBtn.SetDefault()
        buttonSizer.Add(findBtn, 0, wx.RIGHT, HALF_SPACE)
        buttonSizer.Add(wx.Button(frame, wx.ID_CANCEL), 0)
        contentSizer.Add(buttonSizer, 0, wx.ALL|wx.ALIGN_RIGHT, SPACE)

        frame.SetSizer(contentSizer)
        frame.Fit()

        frame.CenterOnParent()
        status = frame.ShowModal()

        passedCheck = False
        while status == wx.ID_OK and not passedCheck:
            if not os.path.exists(dirCtrl.GetValue()):
                dlg = wx.MessageDialog(frame,
                                       _("'%s' does not exist.") % dirCtrl.GetValue(),
                                       _("Find in Directory"),
                                       wx.OK | wx.ICON_EXCLAMATION
                                       )
                dlg.CenterOnParent()
                dlg.ShowModal()
                dlg.Destroy()

                status = frame.ShowModal()
            else:
                passedCheck = True

        frame.Destroy()

        if status == wx.ID_OK:
            wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))

            try:
                doc = self.GetDocument()
                searchSubfolders = subfolderCtrl.IsChecked()
                dirString = dirCtrl.GetValue()
    
                if os.path.isfile(dirString):
                    # If they pick a file explicitly, we won't prevent them from adding it even if it doesn't match the filter.
                    # We'll assume they know what they're doing.
                    paths = [dirString]
                else:
                    paths = []
    
                    index = filterChoice.GetSelection()
                    lastIndex = filterChoice.GetCount()-1
                    if index and index != lastIndex:  # if not All or Any
                        template = visibleTemplates[index-1]
    
                    # do search in files on disk
                    for root, dirs, files in os.walk(dirString):
                        if not searchSubfolders and root != dirString:
                            break
    
                        for name in files:
                            if index == 0:  # All
                                filename = os.path.join(root, name)
                                # if already in project, don't add it, otherwise undo will remove it from project even though it was already in it.
                                if not doc.IsFileInProject(filename):
                                    paths.append(filename)
                            else:  # use selected filter
                                if template.FileMatchesTemplate(name):
                                    filename = os.path.join(root, name)
                                    # if already in project, don't add it, otherwise undo will remove it from project even though it was already in it.
                                    if not doc.IsFileInProject(filename):
                                        paths.append(filename)
    
                folderPath = None
                if self.GetMode() == ProjectView.PROJECT_VIEW:
                    selections = self._treeCtrl.GetSelections()
                    if selections:
                        item = selections[0]
                        if not self._IsItemFile(item):
                            folderPath = self._GetItemFolderPath(item)

                doc.GetCommandProcessor().Submit(ProjectAddFilesCommand(doc, paths, folderPath=folderPath))
                self.Activate()  # after add, should put focus on project editor
                
            finally:
                wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))


    def DoAddFilesToProject(self, filePaths, folderPath):
        # method used by Drag-n-Drop to add files to current Project
        self.GetDocument().GetCommandProcessor().Submit(ProjectAddFilesCommand(self.GetDocument(), filePaths, folderPath))


    def OnFocus(self, event):
        self.GetDocumentManager().ActivateView(self)
        event.Skip()


    def OnKillFocus(self, event):
        # Get the top MDI window and "activate" it since it is already active from the perspective of the MDIParentFrame
        # wxBug: Would be preferable to call OnActivate, but have casting problem, so added Activate method to docview.DocMDIChildFrame
        if not self._editingSoDontKillFocus:  # wxBug: This didn't used to happen, but now when you start to edit an item in a wxTreeCtrl it puts out a KILL_FOCUS event, so we need to detect it
            topWindow = wx.GetApp().GetTopWindow()
            # wxBug: On Mac, this event can fire during shutdown, even after GetTopWindow()
            # is set to NULL. So make sure we have a TLW before getting the active child.
            if topWindow:
                childFrame = topWindow.GetActiveChild()
                if childFrame:
                    childFrame.Activate()
        event.Skip()


    def OnLeftClick(self, event):
        """ 
            wxBug: We also spurious drag events on a single click of on item that is already selected,
            so the solution was to consume the left click event.  But his broke the single click expand/collapse
            of a folder, so if it is a folder, we do an event.Skip() to allow the expand/collapse,
            otherwise we consume the event.
        """          
        # if folder let it collapse/expand
        if wx.Platform == '__WXMSW__':
            item, flags = self._treeCtrl.HitTest(event.GetPosition())
            if item.IsOk() and self._treeCtrl.GetChildrenCount(item, False):
                event.Skip()
        else:
            event.Skip()
            

    def GetPopupFileMenu(self):
        menu = wx.Menu()
        menu.Append(ProjectService.OPEN_SELECTION_ID, _("&Open"), _("Opens the selection"))
        menu.Enable(ProjectService.OPEN_SELECTION_ID, True)
        wx.EVT_MENU(self._GetParentFrame(), ProjectService.OPEN_SELECTION_ID, self.OnOpenSelection)
        
        menu.Append(ProjectService.OPEN_SELECTION_WITH_ID, _("&Open With..."), _("Opens the selection with specify editor"))
        menu.Enable(ProjectService.OPEN_SELECTION_WITH_ID, True)
        wx.EVT_MENU(self._GetParentFrame(), ProjectService.OPEN_SELECTION_WITH_ID, self.OnOpenSelectionWith)
        
        extService = wx.GetApp().GetService(ExtensionService.ExtensionService)
        if extService and extService.GetExtensions():
            firstItem = True
            for ext in extService.GetExtensions():
                if not ext.opOnSelectedFile:
                    continue
                if firstItem:
                    menu.AppendSeparator()
                    firstItem = False
                menu.Append(ext.id, ext.menuItemName)
                wx.EVT_MENU(self._GetParentFrame(), ext.id, extService.ProcessEvent)
                wx.EVT_UPDATE_UI(self._GetParentFrame(), ext.id, extService.ProcessUpdateUIEvent)
                
        itemIDs = [None]
        for item in self._treeCtrl.GetSelections():
            if self._IsItemProcessModelFile(item):
                itemIDs = [None, ProjectService.RUN_SELECTED_PM_ID, None]
                break
                
        itemIDs.extend([wx.ID_UNDO, wx.ID_REDO, None, wx.ID_CUT, wx.ID_COPY, wx.ID_PASTE,wx.ID_CLEAR,None, \
                         wx.ID_SELECTALL,ProjectService.RENAME_ID , ProjectService.REMOVE_FROM_PROJECT, None])
                         
        self.GetCommonItemsMenu(menu,itemIDs)
        tree_item = self._treeCtrl.GetSingleSelectItem()
        filePath = self._GetItemFilePath(tree_item)
        itemIDs = []
        if self._IsItemFile(tree_item) and fileutils.is_python_file(filePath):
            menuBar = wx.GetApp().GetTopWindow().GetMenuBar()
            menu_item = menuBar.FindItemById(DebuggerService.DebuggerService.START_RUN_ID)
            item = wx.MenuItem(menu,ProjectService.START_RUN_ID,_("&Run"), kind = wx.ITEM_NORMAL)
            item.SetBitmap(menu_item.GetBitmap())
            menu.AppendItem(item)
            wx.EVT_MENU(self._treeCtrl, ProjectService.START_RUN_ID, self.ProcessEvent)
            
            debug_menu = wx.Menu()
            menu.AppendMenu(wx.NewId(), _("Debug"), debug_menu)

            menu_item = menuBar.FindItemById(DebuggerService.DebuggerService.START_DEBUG_ID)
            item = wx.MenuItem(menu,ProjectService.START_DEBUG_ID,_("&Debug"), kind = wx.ITEM_NORMAL)
            item.SetBitmap(menu_item.GetBitmap())
            debug_menu.AppendItem(item)
            wx.EVT_MENU(self._treeCtrl, ProjectService.START_DEBUG_ID, self.ProcessEvent)
            
            item = wx.MenuItem(menu,DebuggerService.DebuggerService.BREAK_INTO_DEBUGGER_ID,_("&Break into Debugger"), kind = wx.ITEM_NORMAL)
            debug_menu.AppendItem(item)
            wx.EVT_MENU(self._treeCtrl, DebuggerService.DebuggerService.BREAK_INTO_DEBUGGER_ID, self.ProcessEvent)
            if tree_item != self._bold_item:
                menu.Append(ProjectService.SET_PROJECT_STARTUP_FILE_ID, _("Set as Startup File..."), _("Set the start script of project"))
                wx.EVT_MENU(self._treeCtrl, ProjectService.SET_PROJECT_STARTUP_FILE_ID, self.ProcessEvent)
                wx.EVT_UPDATE_UI(self._treeCtrl, ProjectService.SET_PROJECT_STARTUP_FILE_ID, self.ProcessUpdateUIEvent)
            itemIDs.append(None)
        itemIDs.append(Property.FilePropertiesService.PROPERTIES_ID)
        self.GetCommonItemsMenu(menu,itemIDs)
        menu.Append(ProjectService.OPEN_FOLDER_PATH_ID, _("Open Path in Explorer"))
        wx.EVT_MENU(self._treeCtrl, ProjectService.OPEN_FOLDER_PATH_ID, self.ProcessEvent)
        
        menu.Append(ProjectService.OPEN_TERMINAL_PATH_ID, _("Open Command Prompt here..."))
        wx.EVT_MENU(self._treeCtrl, ProjectService.OPEN_TERMINAL_PATH_ID, self.ProcessEvent)

        menu.Append(ProjectService.COPY_PATH_ID, _("Copy Full Path"))
        wx.EVT_MENU(self._treeCtrl, ProjectService.COPY_PATH_ID, self.ProcessEvent)
        
        return menu

    def GetPopupFolderMenu(self):
        menu = wx.Menu()
        itemIDs = [ProjectService.IMPORT_FILES_ID,ProjectService.ADD_FILES_TO_PROJECT_ID, \
                           ProjectService.ADD_DIR_FILES_TO_PROJECT_ID,ProjectService.ADD_NEW_FILE_ID,ProjectService.ADD_FOLDER_ID, ProjectService.ADD_PACKAGE_FOLDER_ID]
        itemIDs.extend([None,wx.ID_UNDO, wx.ID_REDO, None, wx.ID_CUT, wx.ID_COPY, wx.ID_PASTE, wx.ID_CLEAR,None, \
                            wx.ID_SELECTALL,ProjectService.RENAME_ID , ProjectService.REMOVE_FROM_PROJECT, None, Property.FilePropertiesService.PROPERTIES_ID])
        self.GetCommonItemsMenu(menu,itemIDs)
        
        menu.Append(ProjectService.OPEN_FOLDER_PATH_ID, _("Open Path in Explorer"))
        wx.EVT_MENU(self._treeCtrl, ProjectService.OPEN_FOLDER_PATH_ID, self.ProcessEvent)
        
        menu.Append(ProjectService.OPEN_TERMINAL_PATH_ID, _("Open Command Prompt here..."))
        wx.EVT_MENU(self._treeCtrl, ProjectService.OPEN_TERMINAL_PATH_ID, self.ProcessEvent)

        menu.Append(ProjectService.COPY_PATH_ID, _("Copy Full Path"))
        wx.EVT_MENU(self._treeCtrl, ProjectService.COPY_PATH_ID, self.ProcessEvent)
        return menu
        
    def GetSVNItemIds(self,itemIDs):
        if SVN_INSTALLED:
            itemIDs.extend([None, SVNService.SVNService.SVN_UPDATE_ID, SVNService.SVNService.SVN_CHECKIN_ID, SVNService.SVNService.SVN_REVERT_ID])

    def GetPopupProjectMenu(self):
        menu = wx.Menu()
        itemIDs = [ProjectService.NEW_PROJECT_ID,ProjectService.OPEN_PROJECT_ID,ProjectService.CLOSE_PROJECT_ID,ProjectService.SAVE_PROJECT_ID, ProjectService.DELETE_PROJECT_ID,\
                        ProjectService.CLEAN_PROJECT_ID,ProjectService.ARCHIVE_PROJECT_ID]
        itemIDs.extend([None,ProjectService.IMPORT_FILES_ID,ProjectService.ADD_FILES_TO_PROJECT_ID, \
                           ProjectService.ADD_DIR_FILES_TO_PROJECT_ID,None,ProjectService.ADD_NEW_FILE_ID,ProjectService.ADD_FOLDER_ID, ProjectService.ADD_PACKAGE_FOLDER_ID])
        itemIDs.extend([None, ProjectService.PROJECT_PROPERTIES_ID])
        itemIDs.append(ProjectService.RENAME_ID)
        itemIDs.append(ProjectService.OPEN_PROJECT_PATH_ID)
        self.GetCommonItemsMenu(menu,itemIDs)

        menu.Append(ProjectService.OPEN_TERMINAL_PATH_ID, _("Open Command Prompt here..."))
        wx.EVT_MENU(self._treeCtrl, ProjectService.OPEN_TERMINAL_PATH_ID, self.ProcessEvent)

        menu.Append(ProjectService.COPY_PATH_ID, _("Copy Full Path"))
        wx.EVT_MENU(self._treeCtrl, ProjectService.COPY_PATH_ID, self.ProcessEvent)

        return menu
        
    def GetCommonItemsMenu(self,menu,itemIDs):
        menuBar = self._GetParentFrame().GetMenuBar()
        svnIDs = [SVNService.SVNService.SVN_UPDATE_ID, SVNService.SVNService.SVN_CHECKIN_ID, SVNService.SVNService.SVN_REVERT_ID]
        globalIDs = [wx.ID_UNDO, wx.ID_REDO, wx.ID_CLOSE, wx.ID_SAVE, wx.ID_SAVEAS]
        for itemID in itemIDs:
            if not itemID:
                menu.AppendSeparator()
            else:
                if itemID == ProjectService.RUN_SELECTED_PM_ID and not ACTIVEGRID_BASE_IDE:
                    webBrowserService = wx.GetApp().GetService(WebBrowserService.WebBrowserService)
                    if webBrowserService:
                        if wx.Platform == '__WXMSW__':
                            menu.Append(ProjectService.RUN_SELECTED_PM_ID, _("Run Process"))
                            wx.EVT_MENU(self._GetParentFrame(), ProjectService.RUN_SELECTED_PM_ID, self.ProjectServiceProcessEvent)

                        if wx.Platform == '__WXMSW__':
                            menuLabel = _("Run Process in External Browser")
                        else:
                            menuLabel = _("Run Process")
                        menu.Append(ProjectService.RUN_SELECTED_PM_EXTERNAL_BROWSER_ID, menuLabel)
                        wx.EVT_MENU(self._GetParentFrame(), ProjectService.RUN_SELECTED_PM_EXTERNAL_BROWSER_ID, self.ProjectServiceProcessEvent)
                        
                        if wx.Platform == '__WXMSW__':
    
                            if wx.GetApp().GetUseTabbedMDI():
                                menuLabel = _("Run Process in new Tab")
                            else:
                                menuLabel = _("Run Process in new Window")
                            menu.Append(ProjectService.RUN_SELECTED_PM_INTERNAL_WINDOW_ID, menuLabel)
                            wx.EVT_MENU(self._GetParentFrame(), ProjectService.RUN_SELECTED_PM_INTERNAL_WINDOW_ID, self.ProjectServiceProcessEvent)
                        
                elif itemID == ProjectService.REMOVE_FROM_PROJECT:
                    menu.Append(ProjectService.REMOVE_FROM_PROJECT, _("Remove from Project"))
                    wx.EVT_MENU(self._GetParentFrame(), ProjectService.REMOVE_FROM_PROJECT, self.RemoveFromProject)
                    wx.EVT_UPDATE_UI(self._GetParentFrame(), ProjectService.REMOVE_FROM_PROJECT, self._GetParentFrame().ProcessUpdateUIEvent)
                else:
                    item = menuBar.FindItemById(itemID)
                    if item:
                        if SVN_INSTALLED:
                            svnService = wx.GetApp().GetService(SVNService.SVNService)
                            
                        if itemID in svnIDs:
                            if SVN_INSTALLED and svnService:
                                wx.EVT_MENU(self._GetParentFrame(), itemID, svnService.ProcessEvent)
                        elif itemID in globalIDs:
                            pass
                        else:
                            wx.EVT_MENU(self._treeCtrl, itemID, self.ProcessEvent)
                        menu_item = wx.MenuItem(menu,itemID,item.GetLabel())
                        bmp = item.GetBitmap()
                        if bmp:
                            menu_item.SetBitmap(bmp)
                        menu.AppendItem(menu_item)

    def OnRightClick(self, event):
        self.Activate()
        items = self._treeCtrl.GetSelections()
        if not self.GetSelectedProject() or 0 == len(items):
            return
        if self._HasFilesSelected():  # Files context
            menu = self.GetPopupFileMenu()
        else:  # Project context
            if items[0] == self._treeCtrl.GetRootItem():
                menu = self.GetPopupProjectMenu()
            else:
                menu = self.GetPopupFolderMenu()
        self._treeCtrl.PopupMenu(menu, wx.Point(event.GetX(), event.GetY()))
        menu.Destroy()

    def ProjectServiceProcessEvent(self, event):
        projectService = wx.GetApp().GetService(ProjectService)
        if projectService:
            projectService.ProcessEvent(event)


    def OnRename(self, event=None):
        items = self._treeCtrl.GetSelections()
        if not items:
            return
        item = items[0]
        if wx.Platform == "__WXGTK__":
            dlg = wx.TextEntryDialog(self.GetFrame(), _("Enter New Name"), _("Enter New Name"))
            dlg.CenterOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                text = dlg.GetValue()
                self.ChangeLabel(item, text)
        else:
            if items:
                self._treeCtrl.EditLabel(item)


    def OnBeginLabelEdit(self, event):
        self._editingSoDontKillFocus = True
        item = event.GetItem()
        if self._IsItemFile(item):
            file = self._GetItemFile(item)
            if file.type == 'xform':
                event.Veto()
        if (self.GetMode() == ProjectView.RESOURCE_VIEW) and not self._IsItemFile(item):
            event.Veto()


    def OnEndLabelEdit(self, event):
        self._editingSoDontKillFocus = False
        item = event.GetItem()
        newName = event.GetLabel()
        if item == self._treeCtrl.GetRootItem():
            if not newName:
                #wx.MessageBox(_("project name could not be empty"),style=wx.OK|wx.ICON_ERROR)
                event.Veto()
            else:
                self.GetDocument().GetModel().Name = newName
                self.GetDocument().Modify(True)
            return
        
        if not self.ChangeLabel(item, newName):
            event.Veto()
            

    def ChangeLabel(self, item, newName):
        if not newName:
            return False
        if self._IsItemFile(item):
            oldFilePath = self._GetItemFilePath(item)
            newFilePath = os.path.join(os.path.dirname(oldFilePath), newName)
            doc = self.GetDocument()
            if not doc.GetCommandProcessor().Submit(ProjectRenameFileCommand(doc, oldFilePath, newFilePath)):
                return False
            self._treeCtrl.SortChildren(self._treeCtrl.GetItemParent(item))
        else:
            oldFolderPath = self._GetItemFolderPath(item)
            newFolderPath = os.path.dirname(oldFolderPath)
            if newFolderPath:
                newFolderPath += "/"
            newFolderPath += newName
            if self._treeCtrl.FindFolder(newFolderPath):
                wx.MessageBox(_("Folder '%s' already exists.") % newName,
                            "Rename Folder",
                            wx.OK | wx.ICON_EXCLAMATION,
                            self.GetFrame())
                return False
            doc = self.GetDocument()
            if not doc.GetCommandProcessor().Submit(ProjectRenameFolderCommand(doc, oldFolderPath, newFolderPath)):
                return False
            self._treeCtrl.SortChildren(self._treeCtrl.GetItemParent(item))
            #should delete the folder item ,other it will have double folder item
            wx.CallAfter(self._treeCtrl.Delete,item)

        return True
        

    def CanPaste(self):
        # wxBug: Should be able to use IsSupported/IsSupportedFormat here
        #fileDataObject = wx.FileDataObject()
        #hasFilesInClipboard = wx.TheClipboard.IsSupportedFormat(wx.FileDataObject)
        hasFilesInClipboard = False
        if not wx.TheClipboard.IsOpened():
            if wx.TheClipboard.Open():
                fileDataObject = wx.CustomDataObject(DF_COPY_FILENAME)
                hasFilesInClipboard = wx.TheClipboard.GetData(fileDataObject)
                wx.TheClipboard.Close()
        return hasFilesInClipboard
        
    def CopyFileItem(self,actionType):
        
        fileDataObject = wx.CustomDataObject(DF_COPY_FILENAME)
        items = self._treeCtrl.GetSelections()
        file_items = []
        for item in items:
            filePath = self._GetItemFilePath(item)
            if filePath:
                d = {
                    'filePath':filePath,
                    'actionType':actionType
                }
                file_items.append(d)
        share_data = cPickle.dumps(file_items)
        fileDataObject.SetData(share_data)
        if fileDataObject.GetSize() > 0 and wx.TheClipboard.Open():
            wx.TheClipboard.SetData(fileDataObject)
            wx.TheClipboard.Close()


    def OnCut(self, event):
        self.CopyFileItem(self.CUT_FILE_TYPE)
        self.RemoveFromProject(event)


    def OnCopy(self, event):
        self.CopyFileItem(self.COPY_FILE_TYPE)
        
    def CopyToDest(self,src_path,file_name,dest_path,action_type):
        dest_file_path = os.path.join(dest_path,file_name)
        if not os.path.exists(dest_file_path):
            if action_type == self.COPY_FILE_TYPE:
                shutil.copy(src_path,dest_file_path)
            elif action_type == self.CUT_FILE_TYPE:
                shutil.move(src_path,dest_file_path)
            return dest_file_path
        src_dir_path = os.path.dirname(src_path)
        if not parserutils.ComparePath(src_dir_path,dest_path):
            if action_type == self.COPY_FILE_TYPE:
                ret = wx.MessageBox(_("Dest file is already exist,Do you want to overwrite it?"),_("Copy File"),\
                              wx.YES_NO|wx.ICON_QUESTION,self._GetParentFrame())
                if ret == wx.YES:
                    shutil.copy(src_path,dest_file_path)
            elif action_type == self.CUT_FILE_TYPE:
                ret = wx.MessageBox(_("Dest file is already exist,Do you want to overwrite it?"),_("Move File"),\
                              wx.YES_NO|wx.ICON_QUESTION,self._GetParentFrame())
                if ret == wx.YES:
                    shutil.move(src_path,dest_file_path)
            return dest_file_path
        if action_type == self.CUT_FILE_TYPE:
            return dest_file_path
        file_ext = strutils.GetFileExt(file_name)
        filename_without_ext = strutils.GetFilenameWithoutExt(file_name)
        if sysutilslib.isWindows():
            dest_file_name = _("%s - Copy.%s") % (filename_without_ext,file_ext)
            dest_file_path = os.path.join(dest_path,dest_file_name)
            if os.path.exists(dest_file_path):
                i = 2
                while os.path.exists(dest_file_path):
                    dest_file_name = _("%s - Copy (%d).%s") % (filename_without_ext,i,file_ext)
                    dest_file_path = os.path.join(dest_path,dest_file_name)
                    i += 1
        else:
            dest_file_name = _("%s (copy).%s") % (filename_without_ext,file_ext)
            dest_file_path = os.path.join(dest_path,dest_file_name)
            if os.path.exists(dest_file_path):
                i = 2
                while os.path.exists(dest_file_path):
                    if i == 2:
                        dest_file_name = _("%s (another copy).%s") % (filename_without_ext,file_ext)
                    elif i == 3:
                        dest_file_name = _("%s (%drd copy).%s") % (filename_without_ext,i,file_ext)
                    else:
                        dest_file_name = _("%s (%dth copy).%s") % (filename_without_ext,i,file_ext)
                    dest_file_path = os.path.join(dest_path,dest_file_name)
                    i += 1
        shutil.copy(src_path,dest_file_path)
        return dest_file_path

    def OnPaste(self, event):
        if wx.TheClipboard.Open():
            fileDataObject = wx.CustomDataObject(DF_COPY_FILENAME)
            if wx.TheClipboard.GetData(fileDataObject):
                folderPath = None
                dest_files = []
                if self.GetMode() == ProjectView.PROJECT_VIEW:
                    items = self._treeCtrl.GetSelections()
                    if items:
                        item = items[0]
                        if item:
                            folderPath = self._GetItemFolderPath(item)
                destFolderPath = os.path.join(self.GetDocument().GetModel().homeDir,folderPath)
                for src_file in cPickle.loads(fileDataObject.GetData()):
                    filepath =  src_file['filePath']
                    actionType = src_file['actionType']
                    filename = os.path.basename(filepath)
                    if not os.path.exists(filepath):
                        wx.MessageBox(_("The item '%s' does not exist in the project directory.It may have been moved,renamed or deleted.") % filename,style=wx.OK|wx.ICON_ERROR)
                        return
                    try:
                        if actionType == self.COPY_FILE_TYPE:
                            dest_file_path = self.CopyToDest(filepath,filename,destFolderPath,self.COPY_FILE_TYPE)
                            dest_files.append(dest_file_path)
                        elif actionType == self.CUT_FILE_TYPE:
                            dest_file_path = self.CopyToDest(filepath,filename,destFolderPath,self.CUT_FILE_TYPE)
                            dest_files.append(dest_file_path)
                        else:
                            assert(False)
                    except Exception as e:
                        wx.MessageBox(str(e),style=wx.OK|wx.ICON_ERROR)
                        return
                self.GetDocument().GetCommandProcessor().Submit(ProjectAddFilesCommand(self.GetDocument(), dest_files, folderPath))
            wx.TheClipboard.Close()


    def RemoveFromProject(self, event):
        items = self._treeCtrl.GetSelections()
        files = []
        for item in items:
            if not self._IsItemFile(item):
                folderPath = self._GetItemFolderPath(item)
                self.GetDocument().GetCommandProcessor().Submit(ProjectRemoveFolderCommand(self, self.GetDocument(), folderPath))
            else:
                file = self._GetItemFile(item)
                if file:
                    files.append(file)
        if files:
            self.GetDocument().GetCommandProcessor().Submit(ProjectRemoveFilesCommand(self.GetDocument(), files))
        
    def GetOpenDocument(self,filepath):
        openDocs = self.GetDocumentManager().GetDocuments()[:]  # need copy or docs shift when closed
        for d in openDocs:
            if parserutils.ComparePath(d.GetFilename(),filepath):
                return d
        return None

    def DeleteFromProject(self, event):
        is_file_selected = False
        is_folder_selected = False
        if self._HasFilesSelected():
            is_file_selected = True
        if self._HasFoldersSelected():
            is_folder_selected = True
        if is_file_selected and not is_folder_selected:
            yesNoMsg = wx.MessageDialog(self.GetFrame(),
                         _("Delete cannot be reversed.\n\nRemove the selected files from the\nproject and file system permanently?"),
                         _("Delete Files"),
                         wx.YES_NO|wx.ICON_QUESTION)
        elif is_folder_selected and not is_file_selected:
            yesNoMsg = wx.MessageDialog(self.GetFrame(),
                         _("Delete cannot be reversed.\n\nRemove the selected folder and its files from the\nproject and file system permanently?"),
                         _("Delete Folder"),
                         wx.YES_NO|wx.ICON_QUESTION)
        elif is_folder_selected and is_file_selected:
            yesNoMsg = wx.MessageDialog(self.GetFrame(),
             _("Delete cannot be reversed.\n\nRemove the selected folder and files from the\nproject and file system permanently?"),
             _("Delete Folder And Files"),
             wx.YES_NO|wx.ICON_QUESTION)
             
        yesNoMsg.CenterOnParent()
        status = yesNoMsg.ShowModal()
        yesNoMsg.Destroy()
        if status == wx.ID_NO:
            return
             
        items = self._treeCtrl.GetSelections()
        delFiles = []
        for item in items:
            if self._IsItemFile(item):
                filePath = self._GetItemFilePath(item)
                if filePath and filePath not in delFiles:
                    # remove selected files from file system
                    if os.path.exists(filePath):
                        try:
                            #close the open document first if file opened
                            open_doc =  self.GetOpenDocument(filePath)
                            if open_doc:
                                open_doc.Modify(False)  # make sure it doesn't ask to save the file
                                self.GetDocumentManager().CloseDocument(open_doc, True)
                            os.remove(filePath)
                        except:
                            wx.MessageBox("Could not delete '%s'.  %s" % (os.path.basename(filePath), sys.exc_value),
                                          _("Delete File"),
                                          wx.OK | wx.ICON_ERROR,
                                          self.GetFrame())
                            return
                    # remove selected files from project
                    self.GetDocument().RemoveFiles([filePath])
                    delFiles.append(filePath)
            else:
                file_items = self._GetFolderFileItems(item)
                for fileItem in file_items:
                    filePath = self._GetItemFilePath(fileItem)
                    open_doc = self.GetOpenDocument(filePath)
                    if open_doc:
                        open_doc.Modify(False)  # make sure it doesn't ask to save the file
                        self.GetDocumentManager().CloseDocument(open_doc, True)
                folderPath = self._GetItemFolderPath(item)
                self.GetDocument().GetCommandProcessor().Submit(ProjectRemoveFolderCommand(self, self.GetDocument(), folderPath,True))
            
    def OnDeleteFile(self, event):
        yesNoMsg = wx.MessageDialog(self.GetFrame(),
                                 _("Delete cannot be reversed.\n\nRemove the selected files from the\nproject and file system permanently?"),
                                 _("Delete File"),
                                 wx.YES_NO|wx.ICON_QUESTION)
        yesNoMsg.CenterOnParent()
        status = yesNoMsg.ShowModal()
        yesNoMsg.Destroy()
        if status == wx.ID_NO:
            return

        items = self._treeCtrl.GetSelections()
        delFiles = []
        for item in items:
            filePath = self._GetItemFilePath(item)
            if filePath and filePath not in delFiles:
                delFiles.append(filePath)

        # remove selected files from project
        self.GetDocument().RemoveFiles(delFiles)

        # remove selected files from file system
        for filePath in delFiles:
            if os.path.exists(filePath):
                try:
                    os.remove(filePath)
                except:
                    wx.MessageBox("Could not delete '%s'.  %s" % (os.path.basename(filePath), sys.exc_value),
                                  _("Delete File"),
                                  wx.OK | wx.ICON_EXCLAMATION,
                                  self.GetFrame())

    def OnDeleteProject(self, event=None, noPrompt=False, closeFiles=True, delFiles=True):
        
        class DeleteProjectDialog(wx.Dialog):
        
            def __init__(self, parent, doc):
                wx.Dialog.__init__(self, parent, -1, _("Delete Project"), size = (310, 330))
        
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(wx.StaticText(self, -1, _("Delete cannot be reversed.\nDeleted files are removed from the file system permanently.\n\nThe project file '%s' will be closed and deleted.") % os.path.basename(doc.GetFilename())), 0, wx.ALL, SPACE)
                self._delFilesCtrl = wx.CheckBox(self, -1, _("Delete all files in project"))
                self._delFilesCtrl.SetValue(True)
                self._delFilesCtrl.SetToolTipString(_("Deletes files from disk, whether open or closed"))
                sizer.Add(self._delFilesCtrl, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, SPACE)
                self._closeDeletedCtrl = wx.CheckBox(self, -1, _("Close open files belonging to project"))
                self._closeDeletedCtrl.SetValue(True)
                self._closeDeletedCtrl.SetToolTipString(_("Closes open editors for files belonging to project"))
                sizer.Add(self._closeDeletedCtrl, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, SPACE)
                
                sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.LEFT|wx.BOTTOM, SPACE)
        
                self.SetSizer(sizer)
                sizer.Fit(self)
                self.Layout()

        doc = self.GetDocument()
        if not noPrompt:
            dlg = DeleteProjectDialog(self.GetFrame(), doc)
            dlg.CenterOnParent()
            status = dlg.ShowModal()
            delFiles = dlg._delFilesCtrl.GetValue()
            closeFiles = dlg._closeDeletedCtrl.GetValue()
            dlg.Destroy()
            if status == wx.ID_CANCEL:
                return

        if closeFiles or delFiles:
            filesInProject = doc.GetFiles()
            if not ACTIVEGRID_BASE_IDE:
                deploymentFilePath = self.GetDocument().GetDeploymentFilepath()
                if deploymentFilePath:
                    filesInProject.append(deploymentFilePath)  # remove deployment file also.
                    import activegrid.server.secutils as secutils
                    keystoreFilePath = os.path.join(os.path.dirname(deploymentFilePath), secutils.AGKEYSTORE_FILENAME)
                    filesInProject.append(keystoreFilePath)  # remove keystore file also.
                
            # don't remove self prematurely
            filePath = doc.GetFilename()
            if filePath in filesInProject:
                filesInProject.remove(filePath)
            
            # don't close/delete files outside of project's directory
            homeDir = doc.GetModel().homeDir + os.sep
            for filePath in filesInProject[:]:
                fileDir = os.path.dirname(filePath) + os.sep
                if not fileDir.startswith(homeDir):  
                    filesInProject.remove(filePath)

        if closeFiles:
            # close any open views of documents in the project
            openDocs = self.GetDocumentManager().GetDocuments()[:]  # need copy or docs shift when closed
            for d in openDocs:
                if d.GetFilename() in filesInProject:
                    d.Modify(False)  # make sure it doesn't ask to save the file
                    if isinstance(d.GetDocumentTemplate(), ProjectTemplate):  # if project, remove from project list drop down
                        if self.GetDocumentManager().CloseDocument(d, True):
                            self.RemoveProjectUpdate(d)
                    else:  # regular file
                        self.GetDocumentManager().CloseDocument(d, True)
                
        # remove files in project from file system
        if delFiles:
            dirPaths = []
            for filePath in filesInProject:
                if os.path.isfile(filePath):
                    try:
                        dirPath = os.path.dirname(filePath)
                        if dirPath not in dirPaths:
                            dirPaths.append(dirPath)
                            
                        os.remove(filePath)
                    except:
                        wx.MessageBox("Could not delete file '%s'.\n%s" % (filePath, sys.exc_value),
                                      _("Delete Project"),
                                      wx.OK | wx.ICON_ERROR,
                                      self.GetFrame())
                                      
        filePath = doc.GetFilename()
        
        self.ClearFolderState()  # remove from registry folder settings
        #delete project regkey config
        wx.ConfigBase_Get().DeleteGroup(getProjectKeyName(doc.GetModel().Id))

        # close project
        if doc:            
            doc.Modify(False)  # make sure it doesn't ask to save the project
            if self.GetDocumentManager().CloseDocument(doc, True):
                self.RemoveCurrentDocumentUpdate()
            doc.document_watcher.RemoveFileDoc(doc)

        # remove project file
        if delFiles:
            dirPath = os.path.dirname(filePath)
            if dirPath not in dirPaths:
                dirPaths.append(dirPath)
        if os.path.isfile(filePath):
            try:
                os.remove(filePath)
            except:
                wx.MessageBox("Could not delete project file '%s'.\n%s" % (filePath, sys.exc_value),
                              _("Delete Prjoect"),
                              wx.OK | wx.ICON_EXCLAMATION,
                              self.GetFrame())
            
        # remove empty directories from file system
        if delFiles:
            dirPaths.sort()     # sorting puts parent directories ahead of child directories
            dirPaths.reverse()  # remove child directories first

            for dirPath in dirPaths:
                if os.path.isdir(dirPath):
                    files = os.listdir(dirPath)
                    if not files:
                        try:
                            os.rmdir(dirPath)
                        except:
                            wx.MessageBox("Could not delete empty directory '%s'.\n%s" % (dirPath, sys.exc_value),
                                          _("Delete Project"),
                                          wx.OK | wx.ICON_EXCLAMATION,
                                          self.GetFrame())
        

    def OnKeyPressed(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_DELETE:
            self.RemoveFromProject(event)
        else:
            event.Skip()


    def OnSelectAll(self, event):
        project = self.GetDocument()
        if project:
            self.DoSelectAll(self._treeCtrl.GetRootItem())


    def DoSelectAll(self, parentItem):
        (child, cookie) = self._treeCtrl.GetFirstChild(parentItem)
        while child.IsOk():
            if self._IsItemFile(child):
                self._treeCtrl.SelectItem(child)
            else:
                self.DoSelectAll(child)
            (child, cookie) = self._treeCtrl.GetNextChild(parentItem, cookie)


    def OnOpenSelectionSDI(self, event):
        # Do a call after so that the second mouseclick on a doubleclick doesn't reselect the project window
        wx.CallAfter(self.OnOpenSelection, None)

    def GetOpenDocumentTemplate(self,project_file):
        template = None
        document_template_name = utils.ProfileGet(self.GetDocument().GetFileKey(project_file,"Open"),"")
        filename = os.path.basename(project_file.filePath)
        if not document_template_name:
            document_template_name = utils.ProfileGet("Open/filenames/%s" % filename,"")
            if not document_template_name:
                document_template_name = utils.ProfileGet("Open/extensions/%s" % strutils.GetFileExt(filename),"")
        if document_template_name:
            template = wx.GetApp().GetDocumentManager().FindTemplateForDocumentType(document_template_name)
        return template
        
    def OnOpenSelectionWith(self, event):
        item_file = self._GetItemFile(self._treeCtrl.GetSingleSelectItem())
        selected_file_path = item_file.filePath
        dlg = ProjectUI.EditorSelectionDialog(wx.GetApp().GetTopWindow(),-1,_("Editor Selection"),item_file,self.GetDocument())
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            found_view = utils.GetOpenView(selected_file_path)
            if found_view:
                ret = wx.MessageBox(_("The document \"%s\" is already open,Do you want to close it?") %selected_file_path,style=wx.YES_NO|wx.ICON_QUESTION)
                if ret == wx.YES:
                    found_view.Close()
                    document = found_view.GetDocument()
                    if document in self.GetDocumentManager().GetDocuments():
                        document.Destroy()
                    frame = found_view.GetFrame()
                    if frame:
                        frame.Destroy()
                else:
                    return
            doc = self.GetDocumentManager().CreateTemplateDocument(dlg.selected_template,selected_file_path, wx.lib.docview.DOC_SILENT)
            if doc is not None and dlg._is_changed and utils.GetOpenView(selected_file_path):
                iconIndex = self._treeCtrl.GetTemplateIconIndex(dlg.selected_template)
                if dlg.OpenwithMode == dlg.OPEN_WITH_FILE_PATH:
                    utils.ProfileSet(self.GetDocument().GetFileKey(item_file,"Open"),\
                                     dlg.selected_template.GetDocumentName())
                    file_template = wx.GetApp().GetDocumentManager().FindTemplateForPath(selected_file_path)
                    if file_template != dlg.selected_template:
                        item = self._treeCtrl.GetSelections()[0]
                        if iconIndex != -1:
                            self._treeCtrl.SetItemImage(item, iconIndex, wx.TreeItemIcon_Normal)
                            self._treeCtrl.SetItemImage(item, iconIndex, wx.TreeItemIcon_Expanded)
                        
                elif dlg.OpenwithMode == dlg.OPEN_WITH_FILE_NAME:
                    filename = os.path.basename(selected_file_path)
                    utils.ProfileSet("Open/filenames/%s" % filename,dlg.selected_template.GetDocumentName())
                    if iconIndex != -1:
                        self.ChangeItemsImageWithFilename(self._treeCtrl.GetRootItem(),filename,iconIndex)
                elif dlg.OpenwithMode == dlg.OPEN_WITH_FILE_EXTENSION:
                    extension = strutils.GetFileExt(os.path.basename(selected_file_path))
                    utils.ProfileSet("Open/extensions/%s" % extension,dlg.selected_template.GetDocumentName())
                    if iconIndex != -1:
                        self.ChangeItemsImageWithExtension(self._treeCtrl.GetRootItem(),extension,iconIndex)
                else:
                    assert(False)
        dlg.Destroy()
        

    def ChangeItemsImageWithFilename(self,parent_item,filename,icon_index):
        if parent_item is None:
            return
        (item, cookie) = self._treeCtrl.GetFirstChild(parent_item)
        while item:
            if self._IsItemFile(item):
                file_name = self._treeCtrl.GetItemText(item)
                if file_name == filename:
                    self._treeCtrl.SetItemImage(item, icon_index, wx.TreeItemIcon_Normal)
                    self._treeCtrl.SetItemImage(item, icon_index, wx.TreeItemIcon_Expanded)
            self.ChangeItemsImageWithFilename(item,filename,icon_index)
            (item, cookie) = self._treeCtrl.GetNextChild(parent_item, cookie)
        
    def ChangeItemsImageWithExtension(self,parent_item,extension,icon_index):
        if parent_item is None:
            return
        (item, cookie) = self._treeCtrl.GetFirstChild(parent_item)
        while item:
            if self._IsItemFile(item):
                file_name = self._treeCtrl.GetItemText(item)
                if strutils.GetFileExt(file_name) == extension:
                    self._treeCtrl.SetItemImage(item, icon_index, wx.TreeItemIcon_Normal)
                    self._treeCtrl.SetItemImage(item, icon_index, wx.TreeItemIcon_Expanded)
            self.ChangeItemsImageWithExtension(item,extension,icon_index)
            (item, cookie) = self._treeCtrl.GetNextChild(parent_item, cookie)
        
    def OnOpenSelection(self, event):
        if self.GetMode() == ProjectView.RESOURCE_VIEW:
            item = event.GetItem()
            ResourceView.ResourceView(self).OpenSelection(item)
            event.Skip()
            return
        doc = None
        try:
            items = self._treeCtrl.GetSelections()[:]
            for item in items:
                filepath = self._GetItemFilePath(item)
                file_template = None
                if filepath:
                    if not os.path.exists(filepath):
                        msgTitle = wx.GetApp().GetAppName()
                        if not msgTitle:
                            msgTitle = _("File Not Found")
                        yesNoMsg = wx.MessageDialog(self.GetFrame(),
                                      _("The file '%s' was not found in '%s'.\n\nWould you like to browse for the file?") % (wx.lib.docview.FileNameFromPath(filepath), wx.lib.docview.PathOnly(filepath)),
                                      msgTitle,
                                      wx.YES_NO|wx.ICON_QUESTION
                                      )
                        yesNoMsg.CenterOnParent()
                        status = yesNoMsg.ShowModal()
                        yesNoMsg.Destroy()
                        if status == wx.ID_NO:
                            continue
                        findFileDlg = wx.FileDialog(self.GetFrame(),
                                                 _("Choose a file"),
                                                 defaultFile=wx.lib.docview.FileNameFromPath(filepath),
                                                 style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR
                                                )
                        # findFileDlg.CenterOnParent()  # wxBug: caused crash with wx.FileDialog
                        if findFileDlg.ShowModal() == wx.ID_OK:
                            newpath = findFileDlg.GetPath()
                        else:
                            newpath = None
                        findFileDlg.Destroy()
                        if newpath:
                            # update Project Model with new location
                            self.GetDocument().UpdateFilePath(filepath, newpath)
                            filepath = newpath
                        else:
                            continue
                    else:        
                        project_file = self._treeCtrl.GetPyData(item)
                        file_template = self.GetOpenDocumentTemplate(project_file)
                    if file_template:
                        doc = self.GetDocumentManager().CreateTemplateDocument(file_template,filepath, wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
                    else:
                        doc = self.GetDocumentManager().CreateDocument(filepath, wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
                    if not doc and filepath.endswith(PROJECT_EXTENSION):  # project already open
                        self.SetProject(filepath)
                    elif doc:
                        AddProjectMapping(doc)
                        

        except IOError, (code, message):
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            wx.MessageBox("Could not open '%s'." % wx.lib.docview.FileNameFromPath(filepath),
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION,
                          self.GetFrame())
        if event is None:
            return
        event.Skip()

    #----------------------------------------------------------------------------
    # Convenience methods
    #----------------------------------------------------------------------------

    def _HasFiles(self):
        if not self._treeCtrl:
            return False
        return self._treeCtrl.GetCount() > 1    #  1 item = root item, don't count as having files


    def _HasFilesSelected(self):
        if not self._treeCtrl:
            return False
        items = self._treeCtrl.GetSelections()
        if not items:
            return False
        for item in items:
            if self._IsItemFile(item):
                return True
        return False


    def _HasFoldersSelected(self):
        if not self._treeCtrl:
            return False
        items = self._treeCtrl.GetSelections()
        if not items:
            return False
        for item in items:
            if not self._IsItemFile(item):
                return True
        return False


    def _MakeProjectName(self, project):
        return project.GetPrintableName()


    def _GetItemFilePath(self, item):
        file = self._GetItemFile(item)
        if file:
            return file.filePath
        else:
            return None


    def _GetItemFolderPath(self, item):
        rootItem = self._treeCtrl.GetRootItem()
        if item == rootItem:
            return ""
            
        if self._IsItemFile(item):
            item = self._treeCtrl.GetItemParent(item)
        
        folderPath = ""
        while item != rootItem:
            if folderPath:
                folderPath = self._treeCtrl.GetItemText(item) + "/" + folderPath
            else:
                folderPath = self._treeCtrl.GetItemText(item)
            item = self._treeCtrl.GetItemParent(item)
            
        return folderPath

            
    def _GetItemFile(self, item):
        return self._treeCtrl.GetPyData(item)


    def _IsItemFile(self, item):
        return self._GetItemFile(item) != None


    def _IsItemProcessModelFile(self, item):
        if ACTIVEGRID_BASE_IDE:
            return False

        if self._IsItemFile(item):
            filepath = self._GetItemFilePath(item)
            ext = None
            for template in self.GetDocumentManager().GetTemplates():
                if template.GetDocumentType() == ProcessModelEditor.ProcessModelDocument:
                    ext = template.GetDefaultExtension()
                    break;
            if not ext:
                return False

            if filepath.endswith(ext):
                return True

        return False


    def _GetChildItems(self, parentItem):
        children = []
        (child, cookie) = self._treeCtrl.GetFirstChild(parentItem)
        while child.IsOk():
            children.append(child)
            (child, cookie) = self._treeCtrl.GetNextChild(parentItem, cookie)
        return children


    def _GetFolderItems(self, parentItem):
        folderItems = []
        childrenItems = self._GetChildItems(parentItem)
        for childItem in childrenItems:
            if not self._IsItemFile(childItem):
                folderItems.append(childItem)
                folderItems += self._GetFolderItems(childItem)
        return folderItems
        
    def _GetFolderFileItems(self, parentItem):
        fileItems = []
        childrenItems = self._GetChildItems(parentItem)
        for childItem in childrenItems:
            if self._IsItemFile(childItem):
                fileItems.append(childItem)
            else:
                fileItems.extend(self._GetFolderFileItems(childItem))
        return fileItems
        
    @WxThreadSafe.call_after
    def Alarm(self,alarm_type):
        if alarm_type == FileObserver.FileEventHandler.FILE_MODIFY_EVENT:
            ret = wx.MessageBox(_("Project File \"%s\" has already been modified outside,Do you want to reload It?") % self.GetDocument().GetFilename(), _("Reload Project.."),
                           wx.YES_NO  | wx.ICON_QUESTION,self.GetFrame())
            if ret == wx.YES:
                document = self.GetDocument()
                document.OnOpenDocument(document.GetFilename())
                
        elif alarm_type == FileObserver.FileEventHandler.FILE_MOVED_EVENT or \
             alarm_type == FileObserver.FileEventHandler.FILE_DELETED_EVENT:
            ret = wx.MessageBox(_("Project File \"%s\" has already been moved or deleted outside,Do you want to close this Project?") % self.GetDocument().GetFilename(), _("Project not exist.."),
                           wx.YES_NO  | wx.ICON_QUESTION ,self.GetFrame())
            document = self.GetDocument()
            if ret == wx.YES:
                self.CloseProject()
            else:
                document.Modify(True)


class ProjectFileDropTarget(wx.FileDropTarget):

    def __init__(self, view):
        wx.FileDropTarget.__init__(self)
        self._view = view


    def OnDropFiles(self, x, y, filePaths):
        """ Do actual work of dropping files into project """
        if self._view.GetDocument():
            folderPath = None
            if self._view.GetMode() == ProjectView.PROJECT_VIEW:
                folderItem = self._view._treeCtrl.FindClosestFolder(x,y)
                if folderItem:
                    folderPath = self._view._GetItemFolderPath(folderItem)
            self._view.DoAddFilesToProject(filePaths, folderPath)
            return True
        return False


    def OnDragOver(self, x, y, default):
        """ Feedback to show copy cursor if copy is allowed """
        if self._view.GetDocument():  # only allow drop if project exists
            return wx.DragCopy
        return wx.DragNone


class ProjectPropertiesDialog(wx.Dialog):
    RELATIVE_TO_PROJECT_FILE = _("relative to project file")

    def __init__(self, parent, document):
        wx.Dialog.__init__(self, parent, -1, _("Project Properties"), size = (310, 330))

        filePropertiesService = wx.GetApp().GetService(wx.lib.pydocview.FilePropertiesService)

        notebook = wx.Notebook(self, -1)
        
        tab = wx.Panel(notebook, -1)
        gridSizer = wx.FlexGridSizer(cols = 2, vgap = SPACE, hgap = SPACE)
        gridSizer.AddGrowableCol(1)
        gridSizer.Add(wx.StaticText(tab, -1, _("Filename:")))
        filename = document.GetFilename()
        if os.path.isfile(filename):
            gridSizer.Add(wx.StaticText(tab, -1, os.path.split(filename)[1]))

            gridSizer.Add(wx.StaticText(tab, -1, _("Location:")))
            gridSizer.Add(wx.StaticText(tab, -1, filePropertiesService.chopPath(os.path.dirname(filename), length=50)))

            gridSizer.Add(wx.StaticText(tab, -1, _("Size:")))
            gridSizer.Add(wx.StaticText(tab, -1, str(os.path.getsize(filename)) + ' ' + _("bytes")))

            lineSizer = wx.BoxSizer(wx.VERTICAL)    # let the line expand horizontally without vertical expansion
            lineSizer.Add(wx.StaticLine(tab, -1, size = (10,-1)), 0, wx.EXPAND)
            gridSizer.Add(lineSizer, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP)

            lineSizer = wx.BoxSizer(wx.VERTICAL)    # let the line expand horizontally without vertical expansion
            lineSizer.Add(wx.StaticLine(tab, -1, size = (10,-1)), 0, wx.EXPAND)
            gridSizer.Add(lineSizer, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP)

            gridSizer.Add(wx.StaticText(tab, -1, _("Created:")))
            gridSizer.Add(wx.StaticText(tab, -1, time.ctime(os.path.getctime(filename))))

            gridSizer.Add(wx.StaticText(tab, -1, _("Modified:")))
            gridSizer.Add(wx.StaticText(tab, -1, time.ctime(os.path.getmtime(filename))))

            gridSizer.Add(wx.StaticText(tab, -1, _("Accessed:")))
            gridSizer.Add(wx.StaticText(tab, -1, time.ctime(os.path.getatime(filename))))
        else:
            gridSizer.Add(wx.StaticText(tab, -1, os.path.split(filename)[1] + ' ' + _("[new project]")))
        spacerGrid = wx.BoxSizer(wx.HORIZONTAL)  # add a border around the inside of the tab
        spacerGrid.Add(gridSizer, 1, wx.ALL|wx.EXPAND, SPACE);
        tab.SetSizer(spacerGrid)
        notebook.AddPage(tab, _("General"))

        tab = wx.Panel(notebook, -1)
        spacerGrid = wx.BoxSizer(wx.VERTICAL)  # add a border around the inside of the tab
        homePathLabel = wx.StaticText(tab, -1, _("Home Dir:"))
        if document.GetModel().isDefaultHomeDir:
            defaultHomeDir = ProjectPropertiesDialog.RELATIVE_TO_PROJECT_FILE
        else:
            defaultHomeDir = document.GetModel().homeDir
        self._homeDirCtrl = wx.ComboBox(tab, -1, defaultHomeDir, size=(125,-1), choices=[ProjectPropertiesDialog.RELATIVE_TO_PROJECT_FILE, document.GetModel().homeDir])
        self._homeDirCtrl.SetToolTipString(self._homeDirCtrl.GetValue()) 
        if not document.GetModel().isDefaultHomeDir:
            self._homeDirCtrl.SetInsertionPointEnd()
        def OnDirChanged(event):
            self._homeDirCtrl.SetToolTip(wx.ToolTip(self._homeDirCtrl.GetValue()))  # wx.Bug: SetToolTipString only sets it for the dropdown control, not for the text edit control, so need to replace it completely
        wx.EVT_COMBOBOX(self._homeDirCtrl, -1, OnDirChanged)
        wx.EVT_TEXT(self._homeDirCtrl, -1, OnDirChanged)
        choosePathButton = wx.Button(tab, -1, _("Browse..."))
        def OnBrowseButton(event):
            if self._homeDirCtrl.GetValue() == ProjectPropertiesDialog.RELATIVE_TO_PROJECT_FILE:
                defaultHomeDir = document.GetModel().homeDir
            else:
                defaultHomeDir = self._homeDirCtrl.GetValue()
                
            dlg = wx.DirDialog(self, "Choose a directory:", defaultHomeDir,
                              style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
            if dlg.ShowModal() == wx.ID_OK:
                self._homeDirCtrl.SetValue(dlg.GetPath())
                self._homeDirCtrl.SetInsertionPointEnd()
                self._homeDirCtrl.SetToolTip(wx.ToolTip(dlg.GetPath()))  # wx.Bug: SetToolTipString only sets it for the dropdown control, not for the text edit control, so need to replace it completely
            dlg.Destroy()
        wx.EVT_BUTTON(choosePathButton, -1, OnBrowseButton)
        pathSizer = wx.BoxSizer(wx.HORIZONTAL)
        pathSizer.Add(homePathLabel, 0, wx.ALIGN_CENTER_VERTICAL)
        pathSizer.Add(self._homeDirCtrl, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT, HALF_SPACE)
        pathSizer.Add(choosePathButton, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, SPACE)
        spacerGrid.Add(pathSizer, 0, wx.ALL|wx.EXPAND, SPACE);
        instructionText = wx.StaticText(tab, -1, _("The physical view shows files relative to Home Dir.\nThe Home Dir default is the project file's directory.\nSetting the Home Dir overrides the default directory."))
        spacerGrid.Add(instructionText, 0, wx.ALL, SPACE);
        tab.SetSizer(spacerGrid)
        notebook.AddPage(tab, _("Physical View"))

        if wx.Platform == "__WXMSW__":
            notebook.SetPageSize((310,300))

        if not ACTIVEGRID_BASE_IDE:
            tab = wx.Panel(notebook, -1)
            self._appInfoCtrl = PropertyService.PropertyCtrl(tab, header=False)
            self._appInfoCtrl.SetDocument(document)
            self._appInfoCtrl.SetModel(document.GetAppInfo())
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(self._appInfoCtrl, 1, wx.EXPAND|wx.ALL, PropertyService.LEAVE_MARGIN)
            tab.SetSizer(sizer)
            notebook.AddPage(tab, _("App Info"))
            self._appInfoCtrl._grid.AutoSizeColumns()


        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 0, wx.ALL | wx.EXPAND, SPACE)
        sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, HALF_SPACE)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()


class ProjectOptionsPanel(wx.Panel):


    def __init__(self, parent, id,size):
        wx.Panel.__init__(self, parent, id,size=size)
        self._useSashMessageShown = False
        config = wx.ConfigBase_Get()
        self._projSaveDocsCheckBox = wx.CheckBox(self, -1, _("Remember open projects"))
        self._promptSaveCheckBox = wx.CheckBox(self, -1, _("Warn when run and save modify project files"))
        self._loadFolderStateCheckBox = wx.CheckBox(self, -1, _("Load folder state when open project"))
        self._projSaveDocsCheckBox.SetValue(config.ReadInt("ProjectSaveDocs", True))
        self._loadFolderStateCheckBox.SetValue(config.ReadInt("LoadFolderState", True))
        self._promptSaveCheckBox.SetValue(config.ReadInt("PromptSaveProjectFile", True))
        projectBorderSizer = wx.BoxSizer(wx.VERTICAL)
        projectSizer = wx.BoxSizer(wx.VERTICAL)
        projectSizer.Add(self._projSaveDocsCheckBox, 0, wx.ALL, HALF_SPACE)
        projectSizer.Add(self._promptSaveCheckBox, 0, wx.ALL, HALF_SPACE)
        projectSizer.Add(self._loadFolderStateCheckBox, 0, wx.ALL, HALF_SPACE)
        if not ACTIVEGRID_BASE_IDE:
            self._projShowWelcomeCheckBox = wx.CheckBox(self, -1, _("Show Welcome Dialog"))
            self._projShowWelcomeCheckBox.SetValue(config.ReadInt("RunWelcomeDialog2", True))
            projectSizer.Add(self._projShowWelcomeCheckBox, 0, wx.ALL, HALF_SPACE)
            
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(wx.StaticText(self, -1, _("Default language for projects:")), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, HALF_SPACE)
            self._langCtrl = wx.Choice(self, -1, choices=projectmodel.LANGUAGE_LIST)            
            self._langCtrl.SetStringSelection(config.Read(APP_LAST_LANGUAGE, projectmodel.LANGUAGE_DEFAULT))
            self._langCtrl.SetToolTipString(_("Programming language to be used throughout the project."))
            sizer.Add(self._langCtrl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, MAC_RIGHT_BORDER)
            projectSizer.Add(sizer, 0, wx.ALL, HALF_SPACE)

        projectBorderSizer.Add(projectSizer, 0, wx.ALL, SPACE)
        self.SetSizer(projectBorderSizer)
        self.Layout()


    def OnUseSashSelect(self, event):
        if not self._useSashMessageShown:
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("Document Options")
            wx.MessageBox("Project window embedded mode changes will not appear until the application is restarted.",
                          msgTitle,
                          wx.OK | wx.ICON_INFORMATION,
                          self.GetParent())
            self._useSashMessageShown = True


    def OnOK(self, optionsDialog):
        config = wx.ConfigBase_Get()
        config.WriteInt("ProjectSaveDocs", self._projSaveDocsCheckBox.GetValue())
        config.WriteInt("PromptSaveProjectFile", self._promptSaveCheckBox.GetValue())
        config.WriteInt("LoadFolderState", self._loadFolderStateCheckBox.GetValue())
        if not ACTIVEGRID_BASE_IDE:
            config.WriteInt("RunWelcomeDialog2", self._projShowWelcomeCheckBox.GetValue())
            config.Write(APP_LAST_LANGUAGE, self._langCtrl.GetStringSelection())
        return True


    def GetIcon(self):
        return getProjectIcon()


class ProjectService(Service.Service):

    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    SHOW_WINDOW = wx.NewId()  # keep this line for each subclass, need unique ID for each Service
    RUN_SELECTED_PM_ID = wx.NewId()
    RUN_SELECTED_PM_INTERNAL_WINDOW_ID = wx.NewId()
    RUN_SELECTED_PM_EXTERNAL_BROWSER_ID = wx.NewId()
    RUN_CURRENT_PM_ID = wx.NewId()
    RUN_CURRENT_PM_INTERNAL_WINDOW_ID = wx.NewId()
    RUN_CURRENT_PM_EXTERNAL_BROWSER_ID = wx.NewId()
    RENAME_ID = wx.NewId()
    START_DEBUG_ID = wx.NewId()
    START_RUN_ID = wx.NewId()
    OPEN_SELECTION_ID = wx.NewId()
    OPEN_SELECTION_WITH_ID = wx.NewId()
    REMOVE_FROM_PROJECT = wx.NewId()
    ADD_FILES_TO_PROJECT_ID = wx.NewId()
    ADD_CURRENT_FILE_TO_PROJECT_ID = wx.NewId()
    ADD_DIR_FILES_TO_PROJECT_ID = wx.NewId()
    CLOSE_PROJECT_ID = wx.NewId()
    PROJECT_PROPERTIES_ID = wx.NewId()
    ADD_FOLDER_ID = wx.NewId()
    DELETE_PROJECT_ID = wx.NewId()
    IMPORT_FILES_ID = wx.NewId()
    NEW_PROJECT_ID = wx.NewId()
    OPEN_PROJECT_PATH_ID = wx.NewId()
    OPEN_PROJECT_ID = wx.NewId()
    SAVE_PROJECT_ID = wx.NewId()
    CLEAN_PROJECT_ID = wx.NewId()
    ARCHIVE_PROJECT_ID = wx.NewId()
    ADD_PACKAGE_FOLDER_ID = wx.NewId()
    SET_PROJECT_STARTUP_FILE_ID = wx.NewId()
    ADD_NEW_FILE_ID = wx.NewId()
    
    OPEN_FOLDER_PATH_ID = wx.NewId()
    COPY_PATH_ID = wx.NewId()
    OPEN_TERMINAL_PATH_ID = wx.NewId()
    

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self, serviceName, embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_LEFT):
        Service.Service.__init__(self, serviceName, embeddedWindowLocation,icon_path="project/project_view.ico")
        self._runHandlers = []
        self._suppressOpenProjectMessages = False
        self._logicalViewDefaults = []
        self._logicalViewOpenDefaults = []
        self._fileTypeDefaults = []
        self._nameDefaults = []
        self._mapToProject = dict()
        self._is_loading_projects = False
        

    @property
    def IsLoadingProjects(self):
        return self._is_loading_projects

    def _CreateView(self):
        return ProjectView(self)

    def ShowWindow(self, show = True):
        """ Force showing of saved projects on opening, otherwise empty Project Window is disconcerting for user """
        Service.Service.ShowWindow(self, show)

        if show:
            project = self.GetView().GetDocument()
            if not project:
                self.LoadSavedProjects()


    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------

    def GetSuppressOpenProjectMessages(self):
        return self._suppressOpenProjectMessages


    def SetSuppressOpenProjectMessages(self, suppressOpenProjectMessages):
        self._suppressOpenProjectMessages = suppressOpenProjectMessages


    def GetRunHandlers(self):
        return self._runHandlers


    def AddRunHandler(self, runHandler):
        self._runHandlers.append(runHandler)


    def RemoveRunHandler(self, runHandler):
        self._runHandlers.remove(runHandler)


    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        Service.Service.InstallControls(self, frame, menuBar, toolBar, statusBar, document)

        projectMenu = wx.Menu()

##            accelTable = wx.AcceleratorTable([
##                eval(_("wx.ACCEL_CTRL, ord('R'), ProjectService.RUN_ID"))
##                ])
##            frame.SetAcceleratorTable(accelTable)
        isProjectDocument = document and document.GetDocumentTemplate().GetDocumentType() == ProjectDocument
        if wx.GetApp().IsMDI() or isProjectDocument:
            item = wx.MenuItem(projectMenu,ProjectService.NEW_PROJECT_ID, _("New Project"), _("New one project"))
            item.SetBitmap(images.load("project/new.png"))
            projectMenu.AppendItem(item)
            wx.EVT_MENU(frame, ProjectService.NEW_PROJECT_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ProjectService.NEW_PROJECT_ID, frame.ProcessUpdateUIEvent)
            
            item = wx.MenuItem(projectMenu,ProjectService.OPEN_PROJECT_ID, _("Open Project"), _("Open an existing project"))
            item.SetBitmap(images.load("project/open.png"))
            projectMenu.AppendItem(item)
            wx.EVT_MENU(frame, ProjectService.OPEN_PROJECT_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ProjectService.OPEN_PROJECT_ID, frame.ProcessUpdateUIEvent)
            
            if not menuBar.FindItemById(ProjectService.CLOSE_PROJECT_ID):
                projectMenu.Append(ProjectService.CLOSE_PROJECT_ID, _("Close Project"), _("Closes currently open project"))
                wx.EVT_MENU(frame, ProjectService.CLOSE_PROJECT_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.CLOSE_PROJECT_ID, frame.ProcessUpdateUIEvent)
            if not menuBar.FindItemById(ProjectService.SAVE_PROJECT_ID):
                item = wx.MenuItem(projectMenu,ProjectService.SAVE_PROJECT_ID, _("Save Project"), _("Save project to local disk"))
                item.SetBitmap(images.load("project/save.png"))
                projectMenu.AppendItem(item)
                wx.EVT_MENU(frame, ProjectService.SAVE_PROJECT_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.SAVE_PROJECT_ID, frame.ProcessUpdateUIEvent)
            if not menuBar.FindItemById(ProjectService.DELETE_PROJECT_ID):
                item = wx.MenuItem(projectMenu,ProjectService.DELETE_PROJECT_ID, _("Delete Project"), _("Delete currently open project and its files."))
                item.SetBitmap(images.load("project/trash.png"))
                projectMenu.AppendItem(item)
                wx.EVT_MENU(frame, ProjectService.DELETE_PROJECT_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.DELETE_PROJECT_ID, frame.ProcessUpdateUIEvent)
                
            if not menuBar.FindItemById(ProjectService.CLEAN_PROJECT_ID):
                item = wx.MenuItem(projectMenu,ProjectService.CLEAN_PROJECT_ID, _("Clean Project"), _("Clean project pyc and pyo files"))
                projectMenu.AppendItem(item)
                wx.EVT_MENU(frame, ProjectService.CLEAN_PROJECT_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.CLEAN_PROJECT_ID, frame.ProcessUpdateUIEvent)
                
            if not menuBar.FindItemById(ProjectService.ARCHIVE_PROJECT_ID):
                item = wx.MenuItem(projectMenu,ProjectService.ARCHIVE_PROJECT_ID, _("Archive Project"), _("Archive project to zip file"))
                item.SetBitmap(images.load("project/archive.png"))
                projectMenu.AppendItem(item)
                wx.EVT_MENU(frame, ProjectService.ARCHIVE_PROJECT_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.ARCHIVE_PROJECT_ID, frame.ProcessUpdateUIEvent)
            
            projectMenu.AppendSeparator()
            item = wx.MenuItem(projectMenu,ProjectService.IMPORT_FILES_ID, _("Import Files..."), _("Import files to the current project"))
            item.SetBitmap(images.load("project/import.png"))
            projectMenu.AppendItem(item)
            wx.EVT_MENU(frame, ProjectService.IMPORT_FILES_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ProjectService.IMPORT_FILES_ID, frame.ProcessUpdateUIEvent)
            if not menuBar.FindItemById(ProjectService.ADD_FILES_TO_PROJECT_ID):
                projectMenu.Append(ProjectService.ADD_FILES_TO_PROJECT_ID, _("Add &Files to Project..."), _("Adds a document to the current project"))
                wx.EVT_MENU(frame, ProjectService.ADD_FILES_TO_PROJECT_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.ADD_FILES_TO_PROJECT_ID, frame.ProcessUpdateUIEvent)
            if not menuBar.FindItemById(ProjectService.ADD_DIR_FILES_TO_PROJECT_ID):
                projectMenu.Append(ProjectService.ADD_DIR_FILES_TO_PROJECT_ID, _("Add Directory Files to Project..."), _("Adds a directory's documents to the current project"))
                wx.EVT_MENU(frame, ProjectService.ADD_DIR_FILES_TO_PROJECT_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.ADD_DIR_FILES_TO_PROJECT_ID, frame.ProcessUpdateUIEvent)
            if not menuBar.FindItemById(ProjectService.ADD_CURRENT_FILE_TO_PROJECT_ID):
                projectMenu.Append(ProjectService.ADD_CURRENT_FILE_TO_PROJECT_ID, _("&Add Active File to Project..."), _("Adds the active document to a project"))
                wx.EVT_MENU(frame, ProjectService.ADD_CURRENT_FILE_TO_PROJECT_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.ADD_CURRENT_FILE_TO_PROJECT_ID, frame.ProcessUpdateUIEvent)
            
            if not menuBar.FindItemById(ProjectService.ADD_NEW_FILE_ID):
                projectMenu.AppendSeparator()
                item = wx.MenuItem(projectMenu,ProjectService.ADD_NEW_FILE_ID, _("New File"), _("Creates a new file"))
                item.SetBitmap(images.load("project/new_file.png"))
                projectMenu.AppendItem(item)
                wx.EVT_MENU(frame, ProjectService.ADD_NEW_FILE_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.ADD_NEW_FILE_ID, frame.ProcessUpdateUIEvent)
                
            if not menuBar.FindItemById(ProjectService.ADD_FOLDER_ID):
                item = wx.MenuItem(projectMenu,ProjectService.ADD_FOLDER_ID, _("New Folder"), _("Creates a new folder"))
                item.SetBitmap(images.load("project/folder.png"))
                projectMenu.AppendItem(item)
                wx.EVT_MENU(frame, ProjectService.ADD_FOLDER_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.ADD_FOLDER_ID, frame.ProcessUpdateUIEvent)
            if not menuBar.FindItemById(ProjectService.ADD_PACKAGE_FOLDER_ID):
                item = wx.MenuItem(projectMenu,ProjectService.ADD_PACKAGE_FOLDER_ID, _("New Package Folder"), _("Creates a new package folder"))
                item.SetBitmap(images.load("project/package.png"))
                projectMenu.AppendItem(item)
                wx.EVT_MENU(frame, ProjectService.ADD_PACKAGE_FOLDER_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.ADD_PACKAGE_FOLDER_ID, frame.ProcessUpdateUIEvent)
                
            if not menuBar.FindItemById(ProjectService.PROJECT_PROPERTIES_ID):
                projectMenu.AppendSeparator()
               ## projectMenu.Append(ProjectService.PROJECT_PROPERTIES_ID, _("Project Properties"), _("Project Properties"))
                ###
                item = wx.MenuItem(projectMenu,ProjectService.PROJECT_PROPERTIES_ID, _("Project Properties"), _("Project Properties"))
                item.SetBitmap(images.load("project/properties.png"))
                projectMenu.AppendItem(item)
                wx.EVT_MENU(frame, ProjectService.PROJECT_PROPERTIES_ID, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ProjectService.PROJECT_PROPERTIES_ID, frame.ProcessUpdateUIEvent)
            projectMenu.Append(ProjectService.OPEN_PROJECT_PATH_ID, _("Open Project Path in Explorer"), _("Open Project Path"))
            wx.EVT_MENU(frame, ProjectService.OPEN_PROJECT_PATH_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ProjectService.OPEN_PROJECT_PATH_ID, frame.ProcessUpdateUIEvent)
        index = menuBar.FindMenu(_("&Format"))
        if index == -1:
            index = menuBar.FindMenu(_("&View"))
        menuBar.Insert(index + 1, projectMenu, _("&Project"))
        editMenu = menuBar.GetMenu(menuBar.FindMenu(_("&Edit")))
        if not menuBar.FindItemById(ProjectService.RENAME_ID):
            editMenu.Append(ProjectService.RENAME_ID, _("&Rename"), _("Renames the active item"))
            wx.EVT_MENU(frame, ProjectService.RENAME_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ProjectService.RENAME_ID, frame.ProcessUpdateUIEvent)
        return True


    def OnCloseFrame(self, event):
        if not self.GetView():
            return True

        if wx.GetApp().IsMDI():
            # close all non-project documents first
            for document in self.GetDocumentManager().GetDocuments()[:]:  # Cloning list to make sure we go through all docs even as they are deleted
                if document.GetDocumentTemplate().GetDocumentType() != ProjectDocument:
                    if not self.GetDocumentManager().CloseDocument(document, False):
                        return False

            # write project config afterwards because user may change filenames on closing of new documents
            self.GetView().WriteProjectConfig()  # Called onCloseWindow in all of the other services but needed to be factored out for ProjectService since it is called elsewhere

            # close all project documents after closing other documents
            # because user may save a new document with a new name or cancel closing a document
            for document in self.GetDocumentManager().GetDocuments()[:]:  # Cloning list to make sure we go through all docs even as they are deleted
                if document.GetDocumentTemplate().GetDocumentType() == ProjectDocument:
                    if not document.OnSaveModified():
                        return False
                    else:
                        if document.document_watcher.IsDocFileWatched(document):
                            document.document_watcher.RemoveFileDoc(document)

        # This is called when any SDI frame is closed, so need to check if message window is closing or some other window
        elif self.GetView() == event.GetEventObject().GetView():
            self.SetView(None)
        return True


    #----------------------------------------------------------------------------
    # Document Manager Methods
    #----------------------------------------------------------------------------

    def FindProjectFromMapping(self, key):
        """ Find which project a model or document belongs to """
        return self._mapToProject.get(key)
    

    def AddProjectMapping(self, key, projectDoc=None):
        """ Generate a mapping from model or document to project.  If no project given, use current project.
            e.g. Which project does this model or document belong to (when it was opened)?
        """
        if not projectDoc:
            projectDoc = self.GetCurrentProject()
        self._mapToProject[key] = projectDoc
        

    def RemoveProjectMapping(self, key):
        """ Remove mapping from model or document to project.  """
        if self._mapToProject.has_key(key):
            del self._mapToProject[key]
        

    #----------------------------------------------------------------------------
    # Default Logical View Folder Methods
    #----------------------------------------------------------------------------

    def AddLogicalViewFolderDefault(self, pattern, folder):
        self._logicalViewDefaults.append((pattern, folder))


    def FindLogicalViewFolderDefault(self, filename):
        for (pattern, folder) in self._logicalViewDefaults:
            if filename.endswith(pattern):
                return folder
        return None


    def AddLogicalViewFolderCollapsedDefault(self, folderName, collapsed=True):
        # default is collapsed, don't add to list if collapse is True
        if not collapsed:
            self._logicalViewOpenDefaults.append(folderName)
        

    def FindLogicalViewFolderCollapsedDefault(self, folderName):
        if folderName in self._logicalViewOpenDefaults:
            return False
        return True


    #----------------------------------------------------------------------------
    # Default File Type Methods
    #----------------------------------------------------------------------------

    def AddFileTypeDefault(self, pattern, type):
        self._fileTypeDefaults.append((pattern, type))


    def FindFileTypeDefault(self, filename):
        for (pattern, type) in self._fileTypeDefaults:
            if filename.endswith(pattern):
                return type
        return None


    #----------------------------------------------------------------------------
    # Default Name Methods
    #----------------------------------------------------------------------------

    def AddNameDefault(self, pattern, method):
        self._nameDefaults.append((pattern, method))


    def FindNameDefault(self, filename):
        for (pattern, method) in self._nameDefaults:
            if filename.endswith(pattern):
                return method(filename)
        return None
        

    def GetDefaultNameCallback(self, filename):
        """ A method for generating name from filepath for Project Service """
        return os.path.splitext(os.path.basename(filename))[0]
        

    #----------------------------------------------------------------------------
    # Event Processing Methods
    #----------------------------------------------------------------------------

    def ProcessEventBeforeWindows(self, event):
        id = event.GetId()

        if id == wx.ID_CLOSE_ALL:
            self.OnFileCloseAll(event)
            return True
        return False


    def ProcessUpdateUIEventBeforeWindows(self, event):
        id = event.GetId()

        if id == wx.ID_CLOSE_ALL:
            for document in self.GetDocumentManager().GetDocuments():
                if document.GetDocumentTemplate().GetDocumentType() != ProjectDocument:
                    event.Enable(True)
                    return True

            event.Enable(False)
            return True

        elif id == wx.ID_CLOSE:
            # "File | Close" is too confusing and hard to determine whether user wants to close a viewed file or the current project.
            # Disallow "File | Close" if project is current document or active in project view.
            # User must explicitly close project via "Project | Close Current Project".
            document = self.GetDocumentManager().GetCurrentDocument()
            if document and document.GetDocumentTemplate().GetDocumentType() == ProjectDocument:
                event.Enable(False)
                return True
            if self.GetView().ProcessUpdateUIEvent(event):
                return True
                
        return False


    def ProcessEvent(self, event):
        if Service.Service.ProcessEvent(self, event):
            return True

        id = event.GetId()
        if id == ProjectService.RUN_SELECTED_PM_ID:
            self.OnRunProcessModel(event, runSelected=True)
            return True
        elif id == ProjectService.RUN_SELECTED_PM_INTERNAL_WINDOW_ID:
            self.OnRunProcessModel(event, runSelected=True, newWindow=True, forceInternal=True)
            return True
        elif id == ProjectService.RUN_SELECTED_PM_EXTERNAL_BROWSER_ID:
            self.OnRunProcessModel(event, runSelected=True, newWindow=True, forceExternal=True)
            return True
        elif id == ProjectService.RUN_CURRENT_PM_ID:
            self.OnRunProcessModel(event, runCurrentFile=True)
            return True
        elif id == ProjectService.RUN_CURRENT_PM_INTERNAL_WINDOW_ID:
            self.OnRunProcessModel(event, runCurrentFile=True, newWindow=True, forceInternal=True)
            return True
        elif id == ProjectService.RUN_CURRENT_PM_EXTERNAL_BROWSER_ID:
            self.OnRunProcessModel(event, runCurrentFile=True, newWindow=True, forceExternal=True)
            return True
        elif id == ProjectService.ADD_CURRENT_FILE_TO_PROJECT_ID:
            self.OnAddCurrentFileToProject(event)
            return True
        elif (id == ProjectService.PROJECT_PROPERTIES_ID
        or id == Property.FilePropertiesService.PROPERTIES_ID
        or id == ProjectService.ADD_NEW_FILE_ID
        or id == ProjectService.ADD_FOLDER_ID
        or id == ProjectService.ADD_PACKAGE_FOLDER_ID
        or id == ProjectService.DELETE_PROJECT_ID
        or id == ProjectService.CLOSE_PROJECT_ID
        or id == ProjectService.IMPORT_FILES_ID
        or id == ProjectService.NEW_PROJECT_ID
        or id == ProjectService.OPEN_PROJECT_PATH_ID
        or id == ProjectService.OPEN_PROJECT_ID
        or id == ProjectService.SAVE_PROJECT_ID
        or id == ProjectService.ADD_NEW_FILE_ID
        or id == ProjectService.ARCHIVE_PROJECT_ID
        or id == ProjectService.CLEAN_PROJECT_ID):
            if self.GetView():
                return self.GetView().ProcessEvent(event)
            else:
                return False
        else:
            return False


    def ProcessUpdateUIEvent(self, event):
        if Service.Service.ProcessUpdateUIEvent(self, event):
            return True

        id = event.GetId()
        if id in [ProjectService.RUN_SELECTED_PM_ID,
        ProjectService.RUN_SELECTED_PM_INTERNAL_WINDOW_ID,
        ProjectService.RUN_SELECTED_PM_EXTERNAL_BROWSER_ID,
        ProjectService.RUN_CURRENT_PM_ID,
        ProjectService.RUN_CURRENT_PM_INTERNAL_WINDOW_ID,
        ProjectService.RUN_CURRENT_PM_EXTERNAL_BROWSER_ID]:
            event.Enable(True)
            return True
        elif id == ProjectService.ADD_CURRENT_FILE_TO_PROJECT_ID:
            event.Enable(self._CanAddCurrentFileToProject())
            return True
        elif id in [ProjectService.ADD_FILES_TO_PROJECT_ID,
        ProjectService.ADD_DIR_FILES_TO_PROJECT_ID,
        ProjectService.RENAME_ID,
        ProjectService.OPEN_SELECTION_ID]:
            event.Enable(False)
            return True
        elif id == ProjectService.PROJECT_PROPERTIES_ID:
            event.Enable(self._HasOpenedProjects())
            return True
        elif id in [Property.FilePropertiesService.PROPERTIES_ID,
            ProjectService.ADD_FOLDER_ID,
            ProjectService.ADD_PACKAGE_FOLDER_ID,
            ProjectService.ADD_NEW_FILE_ID,
            ProjectService.DELETE_PROJECT_ID,
            ProjectService.CLOSE_PROJECT_ID,
            ProjectService.SAVE_PROJECT_ID,
            ProjectService.OPEN_PROJECT_PATH_ID,
            ProjectService.IMPORT_FILES_ID,
            ProjectService.ARCHIVE_PROJECT_ID,
            ProjectService.CLEAN_PROJECT_ID]:
            if self.GetView():
                return self.GetView().ProcessUpdateUIEvent(event)
            else:
                return False
        else:
            return False


    def OnRunProcessModel(self, event, runSelected=False, runCurrentFile=False, newWindow=False, forceExternal=False, forceInternal=False):
        project = self.GetCurrentProject()

        if runCurrentFile:
            doc = self.GetDocumentManager().GetCurrentDocument()
            if not doc or not hasattr(doc, "GetFilename"):
                return
            fileToRun = doc.GetFilename()
            projects = self.FindProjectByFile(fileToRun)
            if not projects:
                return
            elif project in projects:
                # use current project
                pass
            elif len(projects) == 1:
                # only one project, display it
                project = projects[0]
                self.GetView().SetProject(project.GetFilename())
            elif len(projects) > 1:
                strings = map(lambda file: os.path.basename(file.GetFilename()), projects)
                res = wx.GetSingleChoiceIndex(_("More than one project uses '%s'.  Select project to run:") % os.path.basename(fileToRun),
                                              _("Select Project"),
                                              strings,
                                              self.GetView()._GetParentFrame())
                if res == -1:
                    return
                project = projects[res]
                self.GetView().SetProject(project.GetFilename())

        if project:
            ext = None
            for template in self.GetDocumentManager().GetTemplates():
                if template.GetDocumentType() == ProcessModelEditor.ProcessModelDocument:
                    ext = template.GetDefaultExtension()
                    break;
            if not ext:
                return

            files = filter(lambda f: f.endswith(ext), project.GetFiles())
            if not files:
                return

            docs = wx.GetApp().GetDocumentManager().GetDocuments()

            filesModified = False
            for doc in docs:
                if doc.IsModified():
                    filesModified = True
                    break
            if filesModified:
                frame = self.GetView().GetFrame()
                yesNoMsg = wx.MessageDialog(frame,
                              _("Files have been modified.  Process may not reflect your current changes.\n\nWould you like to save all files before running?"),
                              _("Run Process"),
                              wx.YES_NO|wx.ICON_QUESTION
                              )
                yesNoMsg.CenterOnParent()
                status = yesNoMsg.ShowModal()
                yesNoMsg.Destroy()
                if status == wx.ID_YES:
                    wx.GetTopLevelParent(frame).OnFileSaveAll(None)

            if runCurrentFile:
                fileToRun = self.GetDocumentManager().GetCurrentDocument().GetFilename()
            elif runSelected:
                fileToRun = self.GetView().GetSelectedFile()
            elif len(files) > 1:
                files.sort(lambda a, b: cmp(os.path.basename(a).lower(), os.path.basename(b).lower()))
                strings = map(lambda file: os.path.basename(file), files)
                res = wx.GetSingleChoiceIndex(_("Select a process to run:"),
                                              _("Run"),
                                              strings,
                                              self.GetView()._GetParentFrame())
                if res == -1:
                    return
                fileToRun = files[res]
            else:
                fileToRun = files[0]
                
            try:
                deployFilePath = project.GenerateDeployment()
            except DataServiceExistenceException, e:
                dataSourceName = str(e)
                self.PromptForMissingDataSource(dataSourceName)
                return
            self.RunProcessModel(fileToRun, project.GetAppInfo().language, deployFilePath, newWindow, forceExternal, forceInternal)


    def RunProcessModel(self, fileToRun, language, deployFilePath, newWindow=True, forceExternal=False, forceInternal=False):
        for runHandler in self.GetRunHandlers():
            if runHandler.RunProjectFile(fileToRun, language, deployFilePath, newWindow, forceExternal, forceInternal):
                return
        os.system('"' + fileToRun + '"')


    def _HasProcessModel(self):
        project = self.GetView().GetDocument()

        if project:
            ext = None
            for template in self.GetDocumentManager().GetTemplates():
                if template.GetDocumentType() == ProcessModelEditor.ProcessModelDocument:
                    ext = template.GetDefaultExtension()
                    break;
            if not ext:
                return False

            files = filter(lambda f: f.endswith(ext), project.GetFiles())
            if not files:
                return False

            if len(files):
                return True

        return False


    def _HasOpenedProjects(self):
        for document in self.GetDocumentManager().GetDocuments():
            if document.GetDocumentTemplate().GetDocumentType() == ProjectDocument:
                return True
        return False


    def _CanAddCurrentFileToProject(self):
        currentDoc = self.GetDocumentManager().GetCurrentDocument()
        if not currentDoc:
            return False
        if currentDoc.GetDocumentTemplate().GetDocumentType() == ProjectDocument:
            return False
        if not currentDoc._savedYet:
            return False
        if self.GetView().GetDocument():  # a project is open
            return True
        return False  # There are no documents open


    def GetFilesFromCurrentProject(self):
        view = self.GetView()
        if view:
            project = view.GetDocument()
            if project:
                return project.GetFiles()
        return None


    def GetCurrentProject(self):
        view = self.GetView()
        if view:
            return view.GetDocument()
        return None


    def GetOpenProjects(self):
        retval = []
        for document in self.GetDocumentManager().GetDocuments():
            if document.GetDocumentTemplate().GetDocumentType() == ProjectDocument:
                retval.append(document)
        return retval


    def FindProjectByFile(self, filename):
        retval = []
        for document in self.GetDocumentManager().GetDocuments():
            if document.GetDocumentTemplate().GetDocumentType() == ProjectDocument:
                if document.GetFilename() == filename:
                    retval.append(document)
                elif document.IsFileInProject(filename):
                    retval.append(document)
                    
        # make sure current project is first in list
        currProject = self.GetCurrentProject()
        if currProject and currProject in retval:
            retval.remove(currProject)
            retval.insert(0, currProject)
                
        return retval


    def OnAddCurrentFileToProject(self, event):
        doc = self.GetDocumentManager().GetCurrentDocument()
        filepath = doc.GetFilename()
        projectDoc = self.GetView().GetDocument()
        if projectDoc.IsFileInProject(filepath):
            wx.MessageBox(_("Current document is already in the project"),style = wx.OK|wx.ICON_WARNING)
            return
        folderPath = None
        if self.GetView().GetMode() == ProjectView.PROJECT_VIEW:
            selections = self.GetView()._treeCtrl.GetSelections()
            if selections:
                item = selections[0]
                folderPath = self.GetView()._GetItemFolderPath(item)
        if projectDoc.GetCommandProcessor().Submit(ProjectAddFilesCommand(projectDoc, [filepath],folderPath=folderPath)):
            AddProjectMapping(doc, projectDoc)
            self.GetView().Activate()  # after add, should put focus on project editor
            if folderPath is None:
                folderPath = ""
            newFilePath = os.path.join(projectDoc.GetModel().homeDir,folderPath,os.path.basename(filepath))
            if not os.path.exists(newFilePath):
                return
            if not parserutils.ComparePath(newFilePath,filepath):
                openDoc = doc.GetOpenDocument(newFilePath)
                if openDoc:
                    wx.MessageBox(_("Project file is already opened"),style = wx.OK|wx.ICON_WARNING)
                    openDoc.GetFirstView().GetFrame().SetFocus()
                    return
                doc.FileWatcher.StopWatchFile(doc)
                doc.SetFilename(newFilePath)
                doc.FileWatcher.StartWatchFile(doc)
            doc.SetDocumentModificationDate()

    def OnFileCloseAll(self, event):
        for document in self.GetDocumentManager().GetDocuments()[:]:  # Cloning list to make sure we go through all docs even as they are deleted
            if document.GetDocumentTemplate().GetDocumentType() != ProjectDocument:
                if not self.GetDocumentManager().CloseDocument(document, False):
                    return
                # document.DeleteAllViews() # Implicitly delete the document when the last view is removed


    def LoadSavedProjects(self):
        self._is_loading_projects = True
        config = wx.ConfigBase_Get()
        openedDocs = False
        if config.ReadInt("ProjectSaveDocs", True):
            docString = config.Read("ProjectSavedDocs")
            if docString:
                doc = None
                docList = eval(docString)
                self.GetView()._treeCtrl.Freeze()

                for fileName in docList:
                    if isinstance(fileName, types.StringTypes) and strutils.GetFileExt(fileName) == PROJECT_SHORT_EXTENSION:
                        fileName = fileName.decode("utf-8")
                        if os.path.exists(fileName):
                            doc = self.GetDocumentManager().CreateDocument(fileName, wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
                self.GetView()._treeCtrl.Thaw()
                if doc:
                    openedDocs = True
        self._is_loading_projects = False
        return openedDocs
        
    def SetCurrentProject(self):
        
        #if open project from command line ,will set it as current project
        open_project_path = wx.GetApp().OpenProjectPath
        if open_project_path is not None:
            self.GetView().SetProject(open_project_path)
        #otherwise will set the saved project as current project
        else:
            currProject = wx.ConfigBase_Get().Read("ProjectCurrent")
            docList = [document.GetFilename() for document in self.GetView().Documents]
            if currProject in docList:
                self.GetView().SetProject(currProject)


    def PromptForMissingDataSource(self, dataSourceName):
        prompt = "A required Data Source '%s' was not found.  The process cannot be run without this Data Source.\n\nWould you like to configure this Data Source now?" % dataSourceName
        msgTitle = "Unknown Data Source"
        dataSourceMissingDlg = wx.MessageDialog(self.GetView().GetFrame(), prompt, msgTitle, wx.YES_NO|wx.ICON_QUESTION)
        dataSourceMissingDlg.CenterOnParent()
        if dataSourceMissingDlg.ShowModal() == wx.ID_YES:
            dataSourceMissingDlg.Destroy()
            self._AddDataSource(dataSourceName)
        else:
            dataSourceMissingDlg.Destroy()


    def _AddDataSource(self, defaultDataSourceName=None):
        dataSourceService = wx.GetApp().GetService(DataModelEditor.DataSourceService)
        dsChoices = dataSourceService.getDataSourceNames()
        dlg = DataModelEditor.AddDataSourceDialog(self.GetView().GetFrame(), 'Add Data Source', dsChoices, defaultDataSourceName)
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            dataSource = dlg.GetDataSource()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False
        if (dataSource == None):
            wx.MessageBox(_("Error getting data source."), self._title)
        dataSourceService.updateDataSource(dataSource)
        if ((dsChoices == None) or (len(dsChoices) <= 0)):
            wx.ConfigBase_Get().Write(DataModelEditor.SchemaOptionsPanel.DEFAULT_DATASOURCE_KEY, dataSource.name)
        dataSourceService.save()
        return True


#----------------------------------------------------------------------------
# Icon Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import ImageFromStream, BitmapFromImage
import cStringIO

def getProjectBitmap():
    return images.load("project/project.png")

def getProjectIcon():
    return wx.IconFromBitmap(getProjectBitmap())

#----------------------------------------------------------------------
def getFolderClosedBitmap():
    return images.load("project/folder_close.png")

def getFolderClosedIcon():
    return wx.IconFromBitmap(getFolderClosedBitmap())

#----------------------------------------------------------------------
def getFolderOpenBitmap():
    return images.load("project/folder_open.png")

def getFolderOpenIcon():
    return wx.IconFromBitmap(getFolderOpenBitmap())
    
def getPackageFolderBitmap():
    return images.load("package_obj.gif")

def getPackageFolderIcon():
    return wx.IconFromBitmap(getPackageFolderBitmap())
    

#----------------------------------------------------------------------
def getLogicalModeOnData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x83IDAT8\x8d\xa5\x93\xcbJ\xc3@\x14\x86\xbfI\x83buS\xabE+TE\x04\x17\
\xde\xf0\x02\x82\xa0k\x17\n.\xdc\xf9\x1e.\xf4\x05\\\t\xfa\x18\x057\xe2\x0b\
\x08ue@\xa4`\xb0\x84J\xd0(M\xa3"\xb65\x8d5.jcbS\x14\xfdW3\xe7\xfc\xe7\x9b9\
\xc3\x19!\xa4\x08\xff\x91\xdcXT\x8d=\xb7\xf6\\\xa5\xe2\xd8\xf5\xfd\xab\t@\
\xdf\xfc\x81\xf8\x11PQw\xddHl\x99H\x0c\xda\xbe\x19\xce\x0f\r\x17@\xae]{\xb1\
\xf1\r\xc5\x83\n!E\xa8\xa8\xbb\xaeuw\x11zB\xbc\x7f24\xde1\xb6%\x02-\xb42\xbe\
\xc5\x06\xd12i\x00&V\xb6\x11m\x0e\x00\xd9\xf4\xac;\xbe\xa1\x88z\x0b\x8eM\xf5\
\xd5$1\xb3\xd9\x048\xde\xdf!%\xe5P4\x9b\x91\xc5+:{\x86\x03y\x19\xbe\x1e\xcc\
\xafR1\x8f\x96Ic\xe6\xb34g\xbf\x01\xfcE\x00%=\x83~z\xd4dv\nW\x94\xc2\x00o/\
\x0f\xc8]\xdd\xb4\xd7\xee\x00\xb8<="\x9a\x8c\xd37\x90"\x9a\xd4Qo\xba1\xf3Y\
\x00\xcf\x13z\x03\xd7\xd6\x01\x88&\xe3\x00\xdc\xdf\xea\x94\r\x8b\x94da~\xb6\
\xea\xda\x8f\x01\x80\x04\xf0TT\x91\x9d\x1b/8:\xb7D\xd9\xb0(\x1b\x16\x8af\xa3\
h\xf5\xe1\x8a\xf5\x04\xcek\xbe\x81_Sk\xeb\x98\xd7\x05\xf4\xf7\x02\x00\x0b\
\xd3\x89P_K\x00@\xefP\x82\xd5\xa1za\xee\xec\x84\xa7\xa2\xea\xe5\x1a\xd3\xd8\
\x12\x90;;\t\xec\xfd\xe3\xeb\x97h\xfc\xc6lz\xd6\xfdMAK\xc0_\xf5\x01\xf4\x01\
\x91\xdc\xfe\x86\x9e^\x00\x00\x00\x00IEND\xaeB`\x82' 

def getLogicalModeOnBitmap():
    return BitmapFromImage(getLogicalModeOnImage())

def getLogicalModeOnImage():
    stream = cStringIO.StringIO(getLogicalModeOnData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getLogicalModeOffData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x83IDAT8\x8d\xa5\x93\xcbJ\xc3@\x14\x86\xbfI\x83buS\xabE+TE\x04\x17\
\xde\xf0\x02\x82\xa0k\x17\n.\xdc\xf9\x1e.\xf4\x05\\\t\xfa\x18\x057\xe2\x0b\
\x08ue@\xa4`\xb0\x84J\xd0(M\xa3"\xb65\x8d5.jcbS\x14\xfdW3\xe7\xfc\xe7\x9b9\
\xc3\x19!\xa4\x08\xff\x91\xdcXT\x8d=\xb7\xf6\\\xa5\xe2\xd8\xf5\xfd\xab\t@\
\xdf\xfc\x81\xf8\x11PQw\xddHl\x99H\x0c\xda\xbe\x19\xce\x0f\r\x17@\xae]{\xb1\
\xf1\r\xc5\x83\n!E\xa8\xa8\xbb\xaeuw\x11zB\xbc\x7f24\xde1\xb6%\x02-\xb42\xbe\
\xc5\x06\xd12i\x00&V\xb6\x11m\x0e\x00\xd9\xf4\xac;\xbe\xa1\x88z\x0b\x8eM\xf5\
\xd5$1\xb3\xd9\x048\xde\xdf!%\xe5P4\x9b\x91\xc5+:{\x86\x03y\x19\xbe\x1e\xcc\
\xafR1\x8f\x96Ic\xe6\xb34g\xbf\x01\xfcE\x00%=\x83~z\xd4dv\nW\x94\xc2\x00o/\
\x0f\xc8]\xdd\xb4\xd7\xee\x00\xb8<="\x9a\x8c\xd37\x90"\x9a\xd4Qo\xba1\xf3Y\
\x00\xcf\x13z\x03\xd7\xd6\x01\x88&\xe3\x00\xdc\xdf\xea\x94\r\x8b\x94da~\xb6\
\xea\xda\x8f\x01\x80\x04\xf0TT\x91\x9d\x1b/8:\xb7D\xd9\xb0(\x1b\x16\x8af\xa3\
h\xf5\xe1\x8a\xf5\x04\xcek\xbe\x81_Sk\xeb\x98\xd7\x05\xf4\xf7\x02\x00\x0b\
\xd3\x89P_K\x00@\xefP\x82\xd5\xa1za\xee\xec\x84\xa7\xa2\xea\xe5\x1a\xd3\xd8\
\x12\x90;;\t\xec\xfd\xe3\xeb\x97h\xfc\xc6lz\xd6\xfdMAK\xc0_\xf5\x01\xf4\x01\
\x91\xdc\xfe\x86\x9e^\x00\x00\x00\x00IEND\xaeB`\x82' 

def getLogicalModeOffBitmap():
    return BitmapFromImage(getLogicalModeOffImage())

def getLogicalModeOffImage():
    stream = cStringIO.StringIO(getLogicalModeOffData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getPhysicalModeOnData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\xabIDAT8\x8d}\x931k\xdb@\x18\x86\x9f\xb3=\x98R\xb0\x06\xc7X\x01\x1d\
\x14\x1c\xeaA4?\xa0\xa1\x8b\x9d\x04C\xe6N\xed\xd8\xad\xbf\xc0\xbf!c\xb6@\x9d\
\xa1\xf4\'\xd4m\xd2l\x9dJ(\xb8R\x87\x90\x84\x80\xaeD\x8e\xad\xc1\xeePBIQ\x87\
\x8b.:+\xc9\x0b\x82\xef\xee\xd3\xf3\xde{\x1f\x9c\x10\xa52\xf7)\x99N\xd2q\x1c\
[{\xfe\xb3U\x91_\x8bE\x83E\xa8\xe9\xba\xa6\x1e\xc71*Rx\xd2\xa3\xe9\xba\xd4\
\x97\x1a\xa2\x92L\'i\xd6\xbc\x0bZ\xecy\xd2CE\n\x15)\x00*Y\xf3!hQ\x9e\xf4\xf8\
vt\xa4\r\xf2\xf0}\x90L|\xae\x93\xdb\xf5E;4uEE\xca\x184]\xd72\x91\x89\x0f\xc0\
\xe3\xf6\xaee\xf8\xe7\x83\xcf\x06\x00e\xc4`o/\r\x83\x80\x96\xf4x\xf9\xea\xb5\
I"\x13\xbf\x00ZJF\\\xec\xef >}\x1c\xa6\x00\x07\x87_hI\x8f\x17\x9d.*R<\x7f\
\xd43\xffZF7\xa0\xb9\xc2\xf9\xc91OV\x9e\xb2\xde\xe9Z\x07\\\'\xe0\xacip\xf6\
\xf5\xcdm\xfc\x08\x967\xde\xeaY\xec\xef\xe8!\x9e\x9f\x1c\x03\xf0[\xfe\x85\
\xa8\x98\xd6Y\xdb\x85d\xa4\xeb60>\x03\xe0\xe7!\x94N#E\xb5\xe6P\xad9\x06\x88\
\'\x97\x85\xfb\xea\xe1\x9c\x198Si\xbd\xd3%\x0c\x02\xae\xe63\x1a\xf3\x86\x15\
\xd5\x82\xf3\x9a^\xea\x0f(\xf5\xb6\xb6D\xbf\xdf\xa7Zs\x08\x83\x00\x80\xab\
\xf9\xac\x08g\'O\xedt\x15\x80\xfaRC\x00\x84?F\xe9\xbb\xc1\x80\x96\xf4t\xb7\
\xbezw\x82\x9c\n\x8f)\xaf_\xdb\xffR\xb8\x99z.\xc1\xc1\xfb\xef\x00l\x0e\xcb\
\xe2A\x83L\x9f{\xda(\xd3\xe6\xb0l\x9e\xf4\x7f\x85\x1d\xb2s\xbf\x8c\xaeh\x00\
\x00\x00\x00IEND\xaeB`\x82' 

def getPhysicalModeOnBitmap():
    return BitmapFromImage(getPhysicalModeOnImage())

def getPhysicalModeOnImage():
    stream = cStringIO.StringIO(getPhysicalModeOnData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getPhysicalModeOffData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\xabIDAT8\x8d}\x931k\xdb@\x18\x86\x9f\xb3=\x98R\xb0\x06\xc7X\x01\x1d\
\x14\x1c\xeaA4?\xa0\xa1\x8b\x9d\x04C\xe6N\xed\xd8\xad\xbf\xc0\xbf!c\xb6@\x9d\
\xa1\xf4\'\xd4m\xd2l\x9dJ(\xb8R\x87\x90\x84\x80\xaeD\x8e\xad\xc1\xeePBIQ\x87\
\x8b.:+\xc9\x0b\x82\xef\xee\xd3\xf3\xde{\x1f\x9c\x10\xa52\xf7)\x99N\xd2q\x1c\
[{\xfe\xb3U\x91_\x8bE\x83E\xa8\xe9\xba\xa6\x1e\xc71*Rx\xd2\xa3\xe9\xba\xd4\
\x97\x1a\xa2\x92L\'i\xd6\xbc\x0bZ\xecy\xd2CE\n\x15)\x00*Y\xf3!hQ\x9e\xf4\xf8\
vt\xa4\r\xf2\xf0}\x90L|\xae\x93\xdb\xf5E;4uEE\xca\x184]\xd72\x91\x89\x0f\xc0\
\xe3\xf6\xaee\xf8\xe7\x83\xcf\x06\x00e\xc4`o/\r\x83\x80\x96\xf4x\xf9\xea\xb5\
I"\x13\xbf\x00ZJF\\\xec\xef >}\x1c\xa6\x00\x07\x87_hI\x8f\x17\x9d.*R<\x7f\
\xd43\xffZF7\xa0\xb9\xc2\xf9\xc91OV\x9e\xb2\xde\xe9Z\x07\\\'\xe0\xacip\xf6\
\xf5\xcdm\xfc\x08\x967\xde\xeaY\xec\xef\xe8!\x9e\x9f\x1c\x03\xf0[\xfe\x85\
\xa8\x98\xd6Y\xdb\x85d\xa4\xeb60>\x03\xe0\xe7!\x94N#E\xb5\xe6P\xad9\x06\x88\
\'\x97\x85\xfb\xea\xe1\x9c\x198Si\xbd\xd3%\x0c\x02\xae\xe63\x1a\xf3\x86\x15\
\xd5\x82\xf3\x9a^\xea\x0f(\xf5\xb6\xb6D\xbf\xdf\xa7Zs\x08\x83\x00\x80\xab\
\xf9\xac\x08g\'O\xedt\x15\x80\xfaRC\x00\x84?F\xe9\xbb\xc1\x80\x96\xf4t\xb7\
\xbezw\x82\x9c\n\x8f)\xaf_\xdb\xffR\xb8\x99z.\xc1\xc1\xfb\xef\x00l\x0e\xcb\
\xe2A\x83L\x9f{\xda(\xd3\xe6\xb0l\x9e\xf4\x7f\x85\x1d\xb2s\xbf\x8c\xaeh\x00\
\x00\x00\x00IEND\xaeB`\x82' 

def getPhysicalModeOffBitmap():
    return BitmapFromImage(getPhysicalModeOffImage())

def getPhysicalModeOffImage():
    stream = cStringIO.StringIO(getPhysicalModeOffData())
    return ImageFromStream(stream)

