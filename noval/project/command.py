# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        command.py
# Purpose:     项目文件操作命令,包含添加文件,添加文件夹,删除文件,重命名文件等.
#
# Author:      wukan
#
# Created:     2019-03-22
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------

import noval.util.singleton as singleton
import noval.consts as consts
import os

class Command(object):
    """
    wxCommand is a base class for modelling an application command, which is
    an action usually performed by selecting a menu item, pressing a toolbar
    button or any other means provided by the application to change the data
    or view.
    """


    def __init__(self, canUndo = False, name = None):
        """
        Constructor. wxCommand is an abstract class, so you will need to
        derive a new class and call this constructor from your own constructor.

        canUndo tells the command processor whether this command is undo-able.
        You can achieve the same functionality by overriding the CanUndo member
        function (if for example the criteria for undoability is context-
        dependent).

        name must be supplied for the command processor to display the command
        name in the application's edit menu.
        """
        self._canUndo = canUndo
        self._name = name


    def CanUndo(self):
        """
        Returns true if the command can be undone, false otherwise.
        """
        return self._canUndo


    def GetName(self):
        """
        Returns the command name.
        """
        return self._name


    def Do(self):
        """
        Override this member function to execute the appropriate action when
        called. Return true to indicate that the action has taken place, false
        otherwise. Returning false will indicate to the command processor that
        the action is not undoable and should not be added to the command
        history.
        """
        return True


    def Undo(self):
        """
        Override this member function to un-execute a previous Do. Return true
        to indicate that the action has taken place, false otherwise. Returning
        false will indicate to the command processor that the action is not
        redoable and no change should be made to the command history.

        How you implement this command is totally application dependent, but
        typical strategies include:

        Perform an inverse operation on the last modified piece of data in the
        document. When redone, a copy of data stored in command is pasted back
        or some operation reapplied. This relies on the fact that you know the
        ordering of Undos; the user can never Undo at an arbitrary position in
        he command history.

        Restore the entire document state (perhaps using document
        transactioning). Potentially very inefficient, but possibly easier to
        code if the user interface and data are complex, and an 'inverse
        execute' operation is hard to write.
        """
        return True

@singleton.Singleton
class CommandProcessor(object):
    """
    wxCommandProcessor is a class that maintains a history of wxCommands, with
    undo/redo functionality built-in. Derive a new class from this if you want
    different behaviour.
    """


    def __init__(self, maxCommands=-1):
        """
        Constructor.  maxCommands may be set to a positive integer to limit
        the number of commands stored to it, otherwise (and by default) the
        list of commands can grow arbitrarily.
        """
        self._maxCommands = maxCommands
        self._editMenu = None
        self._undoAccelerator = "Ctrl+Z"
        self._redoAccelerator = "Ctrl+Y"
        self.ClearCommands()


    def _GetCurrentCommand(self):
        if len(self._commands) == 0:
            return None
        else:
            return self._commands[-1]


    def _GetCurrentRedoCommand(self):
        if len(self._redoCommands) == 0:
            return None
        else:
            return self._redoCommands[-1]


    def GetMaxCommands(self):
        """
        Returns the maximum number of commands that the command processor
        stores.

        """
        return self._maxCommands


    def GetCommands(self):
        """
        Returns the list of commands.
        """
        return self._commands


    def ClearCommands(self):
        """
        Deletes all the commands in the list and sets the current command
        pointer to None.
        """
        self._commands = []
        self._redoCommands = []


    def GetEditMenu(self):
        """
        Returns the edit menu associated with the command processor.
        """
        return self._editMenu


    def SetEditMenu(self, menu):
        """
        Tells the command processor to update the Undo and Redo items on this
        menu as appropriate. Set this to NULL if the menu is about to be
        destroyed and command operations may still be performed, or the
        command processor may try to access an invalid pointer.
        """
        self._editMenu = menu


    def GetUndoAccelerator(self):
        """
        Returns the string that will be appended to the Undo menu item.
        """
        return self._undoAccelerator


    def SetUndoAccelerator(self, accel):
        """
        Sets the string that will be appended to the Redo menu item.
        """
        self._undoAccelerator = accel


    def GetRedoAccelerator(self):
        """
        Returns the string that will be appended to the Redo menu item.
        """
        return self._redoAccelerator


    def SetRedoAccelerator(self, accel):
        """
        Sets the string that will be appended to the Redo menu item.
        """
        self._redoAccelerator = accel


    def SetMenuStrings(self):
        """
        Sets the menu labels according to the currently set menu and the
        current command state.
        """
        if self.GetEditMenu() != None:
            undoCommand = self._GetCurrentCommand()
            redoCommand = self._GetCurrentRedoCommand()
            undoItem = self.GetEditMenu().FindItemById(wx.ID_UNDO)
            redoItem = self.GetEditMenu().FindItemById(wx.ID_REDO)
            if self.GetUndoAccelerator():
                undoAccel = '\t' + self.GetUndoAccelerator()
            else:
                undoAccel = ''
            if self.GetRedoAccelerator():
                redoAccel = '\t' + self.GetRedoAccelerator()
            else:
                redoAccel = ''
            if undoCommand and undoItem and undoCommand.CanUndo():
                undoItem.SetText(_("&Undo ") + undoCommand.GetName() + undoAccel)
            #elif undoCommand and not undoCommand.CanUndo():
            #    undoItem.SetText(_("Can't Undo") + undoAccel)
            else:
                undoItem.SetText(_("&Undo" + undoAccel))
            if redoCommand and redoItem:
                redoItem.SetText(_("&Redo ") + redoCommand.GetName() + redoAccel)
            else:
                redoItem.SetText(_("&Redo") + redoAccel)


    def CanUndo(self):
        """
        Returns true if the currently-active command can be undone, false
        otherwise.
        """
        if self._GetCurrentCommand() == None:
            return False
        return self._GetCurrentCommand().CanUndo()


    def CanRedo(self):
        """
        Returns true if the currently-active command can be redone, false
        otherwise.
        """
        return self._GetCurrentRedoCommand() != None


    def Submit(self, command, storeIt=True):
        """
        Submits a new command to the command processor. The command processor
        calls wxCommand::Do to execute the command; if it succeeds, the
        command is stored in the history list, and the associated edit menu
        (if any) updated appropriately. If it fails, the command is deleted
        immediately. Once Submit has been called, the passed command should
        not be deleted directly by the application.

        storeIt indicates whether the successful command should be stored in
        the history list.
        """
        done = command.Do()
        if done:
            del self._redoCommands[:]
            if storeIt:
                self._commands.append(command)
        if self._maxCommands > -1:
            if len(self._commands) > self._maxCommands:
                del self._commands[0]
        return done


    def Redo(self):
        """
        Redoes the command just undone.
        """
        cmd = self._GetCurrentRedoCommand()
        if not cmd:
            return False
        done = cmd.Do()
        if done:
            self._commands.append(self._redoCommands.pop())
        return done


    def Undo(self):
        """
        Undoes the command just executed.
        """
        cmd = self._GetCurrentCommand()
        if not cmd:
            return False
        done = cmd.Undo()
        if done:
            self._redoCommands.append(self._commands.pop())
        return done
        


class ProjectAddFilesCommand(Command):
    '''
        添加项目文件操作命令
    '''

    def __init__(self, projectDoc, filePaths, folderPath=None, types=None, names=None):
        Command.__init__(self, canUndo = True)
        self._projectDoc = projectDoc
        self._allFilePaths = filePaths
        self._folderPath = folderPath
        self._types = types
        self._names = names
        
        if not self._types:
            self._types = []
          #  projectService = wx.GetApp().GetService(ProjectService)
           # for filePath in self._allFilePaths:
            #    self._types.append(projectService.FindFileTypeDefault(filePath))

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
        
class ProjectAddProgressFilesCommand(Command):

    def __init__(self, progress_ui,projectDoc, filePaths, que,folderPath=None, types=None, names=None,range_value=0):
        Command.__init__(self, canUndo = False)
        self._projectDoc = projectDoc
        self._allFilePaths = filePaths
        self._folderPath = folderPath
        self._types = types
        self._names = names
        self._progress_ui = progress_ui
        self._que = que
        
        if not self._types:
            self._types = []
        self._range_value = range_value

    def Do(self):
        return self._projectDoc.AddProgressFiles(self._progress_ui,self._que,self._allFilePaths, self._folderPath, \
                    self._types, self._names,self._range_value)
        
    def Undo(self):
        return False


class ProjectRemoveFilesCommand(Command):


    def __init__(self, projectDoc, files):
        Command.__init__(self, canUndo = True)
        self._projectDoc = projectDoc
        self._files = files


    def GetName(self):
        if len(self._files) == 1:
            return _("Remove File %s") % os.path.basename(self._files[0].filePath)
        else:
            return _("Remove Files")


    def Do(self):
        return self._projectDoc.RemoveFiles(filePaths=self._files)


    def Undo(self):
        return self._projectDoc.AddFiles(files=self._files)

class ProjectRenameFileCommand(Command):


    def __init__(self, projectDoc, oldFilePath, newFilePath, isProject = False):
        Command.__init__(self, canUndo = True)
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


class ProjectRenameFolderCommand(Command):
    def __init__(self, doc, oldFolderPath, newFolderPath):
        Command.__init__(self, canUndo = True)
        self._doc = doc
        self._oldFolderPath = oldFolderPath
        self._newFolderPath = newFolderPath


    def GetName(self):
        return _("Rename Folder %s to %s") % (os.path.basename(self._oldFolderPath), os.path.basename(self._newFolderPath))


    def Do(self):
        return self._doc.RenameFolder(self._oldFolderPath, self._newFolderPath)


    def Undo(self):
        return self._doc.RenameFolder(self._newFolderPath, self._oldFolderPath)
    

class ProjectAddFolderCommand(Command):
    '''
        添加项目文件夹命令
    '''
    def __init__(self, view, doc, folderpath):
        Command.__init__(self, canUndo = True)
        self._doc = doc
        self._view = view
        self._folderpath = folderpath

    def GetName(self):
        return _("Add Folder %s") % (os.path.basename(self._folderpath))
        
    def AddFolder(self):
        status = self._view.AddFolder(self._folderpath)
        if not status:
            return status
        projectdir = self._doc.GetModel().homeDir
        destfolderPath = os.path.join(projectdir,self._folderpath)
        dummy_file = os.path.join(destfolderPath,consts.DUMMY_NODE_TEXT)
        self._doc.GetCommandProcessor().Submit(ProjectAddFilesCommand(self._doc,[dummy_file],self._folderpath))
        return True

    def Do(self):
        if self._view.GetDocument() != self._doc:
            return True
        status = self.AddFolder()
        if status:
            ###self._view._treeCtrl.UnselectAll()
            item = self._view._treeCtrl.FindFolder(self._folderpath)
            self._view._treeCtrl.SelectItem(item)
        return status


    def Undo(self):
        if self._view.GetDocument() != self._doc:
            return True
        return self._view.DeleteFolder(self._folderpath)
        

class ProjectAddPackagefolderCommand(ProjectAddFolderCommand):
    def __init__(self, view, doc, folderpath):
        ProjectAddFolderCommand.__init__(self,view,doc,folderpath)
        
    def AddFolder(self):
        return self._view.AddPackageFolder(self._folderpath)

class ProjectRemoveFolderCommand(Command):
    def __init__(self, view, doc, folderpath,delete_folder_files = False):
        Command.__init__(self, canUndo = True)
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


class ProjectMoveFilesCommand(Command):

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
