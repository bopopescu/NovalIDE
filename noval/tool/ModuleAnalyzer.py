import noval.parser.codeparser as codeparser
import threading
import noval.parser.scope as scope
import noval.util.utils as utils
import wx

class PythonModuleAnalyzer(object):
    """description of class"""
    
    STATUS_START_ANALYZING = 0
    STATUS_PARSING_SYNTAX = 1
    STATUS_LOADING_SYNTAX_TREE = 2
    STATUS_FINISH_ANALYZING = 3
    
    def __init__(self,mod_view):
        self._mod_view = mod_view
        self._status = self.STATUS_START_ANALYZING
        self._lock = threading.Lock()
        #when close window,the flag is set to true
        self._is_analyzing_stoped = False
        self._module_scope = None

    def LoadModule(self,filename):
        self._status = self.STATUS_PARSING_SYNTAX
        self._code_parser = codeparser.CodeParser(filename)
        module = self._code_parser.ParseContent(self._mod_view.GetCtrl().GetValue(),self._mod_view.GetDocument().file_encoding)
        if module is None:
            self.FinishAnalyzing()
            return
        module_scope = scope.ModuleScope(module,self._mod_view.GetCtrl().GetLineCount())
        if not self.IsAnalyzingStopped():
            module_scope.MakeModuleScopes()
        else:
            utils.GetLogger().debug("analyze module file %s is canceled by user,will not make module scopes step",filename)
        if not self.IsAnalyzingStopped():
            module_scope.RouteChildScopes()
        else:
            utils.GetLogger().debug("analyze module file %s is canceled by user,will not route child scopes step",filename)
        self.ModuleScope = module_scope
        
    def AnalyzeModuleSynchronizeTree(self,view,force,treeCtrl,outlineService,lineNum):
        t = threading.Thread(target=self.LoadMouduleSynchronizeTree,args=(view,force,treeCtrl,outlineService,lineNum))
        t.start()

    def LoadMouduleSynchronizeTree(self,view,force,treeCtrl,outlineService,lineNum):
        with self._lock:
            if self.IsAnalyzing():
                print 'document %s is analyzing,will not analyze again' % self._mod_view.GetDocument().GetFilename()
                return True
            document = self._mod_view.GetDocument()
            filename = document.GetFilename()
            if force:
                self.LoadModule(filename)
            self._status = self.STATUS_LOADING_SYNTAX_TREE
            if self.ModuleScope == None:
                if view is None or filename != view.GetDocument().GetFilename():
                    wx.CallAfter(treeCtrl.DeleteAllItems)
            else:
                #should freeze control to prevent update and treectrl flick
                if not self.IsAnalyzingStopped():
                    treeCtrl.LoadModuleAst(self.ModuleScope,self,outlineService,lineNum)
                else:
                    utils.GetLogger().debug("analyze module file %s is canceled by user,will not load and synchronize tree",filename)
            self.FinishAnalyzing()
            return True

    @property
    def ModuleScope(self):
        return self._module_scope
        
    @property
    def SyntaxError(self):
        return self._code_parser.SyntaxError
        
    @ModuleScope.setter
    def ModuleScope(self,module_scope):
        self._module_scope = module_scope
        
    @property
    def View(self):
        return self._mod_view
        
    def StopAnalyzing(self):
        self._is_analyzing_stoped = True
        
    def IsAnalyzingStopped(self):
        return self._is_analyzing_stoped
        
    def IsAnalyzing(self):
        return self._status == self.STATUS_PARSING_SYNTAX or self._status == self.STATUS_LOADING_SYNTAX_TREE
        
    def FinishAnalyzing(self):
        self._status = self.STATUS_FINISH_ANALYZING