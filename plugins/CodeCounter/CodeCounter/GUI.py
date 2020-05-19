#coding=utf-8

import tkinter as tk
import os
import threading
import time
from tkinter import ttk

from tkinter.filedialog import askdirectory,askopenfilename
from codecounter import CodeCounter

from noval import GetApp
import noval.consts as consts
import noval.syntax.syntax as syntax

import easyplugindev as epd
from easyplugindev import _
from easyplugindev import ListboxFrame

def getResourcePath():
    from pkg_resources import resource_filename
    path = resource_filename(__name__,'')  
    clone_local_img_path = os.path.join(path,"codecounter.png") # 导入同一个包下的文件.
    return clone_local_img_path
def getCurrentProjectDocuments():
    try:
        app=GetApp()
        projBrowser=GetApp().MainFrame.GetView(consts.PROJECT_VIEW_NAME)
        return projBrowser.GetView().GetDocument().GetModel().filePaths
    except Exception as e:
        #print(e)
        return ['/media/hzy/程序/novalide/NovalIDE/plugins/CodeCounter/codecounter/TextFile1.txt',
                '/media/hzy/程序/novalide/NovalIDE/plugins/CodeCounter/codecounter/GUI.py',
                '/media/hzy/程序/novalide/NovalIDE/plugins/CodeCounter/codecounter/test1.c',
                '/media/hzy/程序/novalide/NovalIDE/plugins/CodeCounter/codecounter/TextFile2 (copy).logger',
                '/media/hzy/程序/novalide/NovalIDE/plugins/CodeCounter/codecounter/TextFile2.log'
                ]
                                  # 这一部分用于调试。

def getSupportedDocuments():
    try:
        allLanguageLexers=syntax.SyntaxThemeManager().Lexers#获取ide支持的全部语言。
        
        s=''
        for item in allLanguageLexers:
            st=item.GetExt()
            #print(st)
            s+=' '+st
        s=s.replace(' ',';')#扩展名中间以分号分隔。
        s=s.strip(';')
        return s
    except:
        return 'c;py;txt;md'
 
def stdInputHandler(entry):
    s=entry.get()
    #处理输入输出的标准接口函数。将以分号隔开的字符串分割成列表
    if(s.strip()==''):
        return s,[]
    s=s.replace('；',';')
    s=s.replace('.','')
    s.replace('\\','/')
    tmpList=s.split(';')
    entry.delete(0,tk.END)
    entry.insert(0,s)

    return s,tmpList # 返回数组和字符串

       
class CodeCounterDialog(epd.ModalDialog):
    def __init__(self, master,title,label,selection=-1,show_scrollbar=False):
        epd.ModalDialog.__init__(self, master, takefocus=1)
        self.title(title)
        self.projectDocs=getCurrentProjectDocuments()

        self.resizable(height=tk.FALSE, width=tk.FALSE)

        self.path = ''
     
        self.pathMode = tk.IntVar()#0为当前项目，1为选择其他文件。
       
        var0=0
        
        self.pathMode.set(var0)#默认勾选当前项目。

            
        promptFrame=ttk.Frame(self.main_frame)
        radioButton1 = ttk.Radiobutton(promptFrame,text=_("Current Project"), value=0, 
                                       variable=self.pathMode,command=self.changePathMode)
        radioButton2 = ttk.Radiobutton(promptFrame,text=_("Folder"), value=1,
                                        variable=self.pathMode,command=self.changePathMode)
        labelPrompt1 = ttk.Label(promptFrame,text=_("Choose"))#提示标签
        labelPrompt2 = ttk.Label(promptFrame,text=_("to Count Lines"))#提示标签
#--------------  标签栏与radioButton
        labelPrompt1.pack(side=tk.LEFT,anchor=tk.W,expand=0,fill=None,padx=consts.DEFAUT_CONTRL_PAD_X)
        radioButton1.pack(side=tk.LEFT)
        radioButton2.pack(side=tk.LEFT)
        labelPrompt2.pack(side=tk.LEFT)
        promptFrame.pack()
        
# ---------------row=2
            
        self.pathFrame=ttk.Frame(self.main_frame)
        self.pathEntry=ttk.Entry(self.pathFrame)
        labelForPath=ttk.Label(self.pathFrame,text=_("Source Path:\t"))
        labelForPath.pack(side=tk.LEFT,anchor=tk.W,expand=0,fill=None)
        self.pathEntry.delete(0,tk.END)
        self.pathEntry.pack(side=tk.LEFT,fill=tk.X,expand=1, padx=(consts.DEFAUT_CONTRL_PAD_X,consts.DEFAUT_CONTRL_PAD_X))
        
        if(self.pathMode.get()==0):
            state='disabled'
        else:
            state='normal'
            

        self.pathEntry['state']=state#默认为选择当前项目的文件，因此无需任何输入。
        
        

        self.askpathButton = ttk.Button(self.pathFrame,command=self.chooseDir,
                                        text="...",state=state,width=1)
        
        self.askpathButton.pack(side=tk.LEFT)
        self.pathFrame.pack(expand=1,fill=tk.X,padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
 # --------------输入扩展名的框     
        
        self.supportedDocExts=getSupportedDocuments()
        

        extFrame=ttk.Frame(self.main_frame)
        extPromptLabel=ttk.Label(extFrame,text=_('Filter file Types:\t'))
        extPromptLabel.pack(side=tk.LEFT)
        self.extEntry = ttk.Entry(extFrame,text=self.supportedDocExts)
        
        tempLabel=ttk.Label(extFrame,text='   ',width=2)#这个标签是占位用的。
        

        self.extEntry.pack(side=tk.LEFT,expand=1,fill=tk.X,padx=(consts.DEFAUT_CONTRL_PAD_X,consts.DEFAUT_CONTRL_PAD_X))
        self.extEntry.delete(0,tk.END)
        self.extEntry.insert(0,self.supportedDocExts)
        
        tempLabel.pack(side=tk.LEFT)
        
        extFrame.pack(expand=1,fill=tk.X,padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
# ----------输入排除路径的列表
        excludePromptLabelFrame=ttk.Frame(self.main_frame)
        excludePromptLabel = ttk.Label(excludePromptLabelFrame,text=_('Exclude Path:'),anchor=tk.W)
        excludePromptLabel.pack(side=tk.LEFT)
        excludePromptLabelFrame.pack(expand=1,fill=tk.X,
                                      padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        
               
        ## 这个frame放了排除路径有关的所有控件。
        excludePathFrame=ttk.Frame(self.main_frame)
       ##这个frame是装了两个按钮，用来添加和减少路径的。
  
        
        excludePathButtonFrame=ttk.Frame(excludePathFrame)
        self.askexcludePathButton = ttk.Button(excludePathButtonFrame,command=self.chooseExcludedDir,
                                        text="+",width=1)
        self.removePathButton=ttk.Button(excludePathButtonFrame,command=self.removeExcludedDir,
                                         text="-",width=1)
        self.askexcludePathButton.pack(pady=consts.DEFAUT_CONTRL_PAD_Y)
        self.removePathButton.pack(pady=consts.DEFAUT_CONTRL_PAD_Y)
        
        # 这个frame是装了列表和滚动条的。
        self.excludeFolderListFrame=ListboxFrame(excludePathFrame)
        self.excludeFolderListBox=self.excludeFolderListFrame.listbox
##        self.excludeFolderListBox.insert(0,'')
        self.excludeFolderListBox.config(height=5)
        self.excludeFolderListFrame.pack(expand=1,side=tk.LEFT,fill=tk.X,
                                     padx=(consts.DEFAUT_CONTRL_PAD_X,consts.DEFAUT_CONTRL_PAD_X))
        excludePathButtonFrame.pack(side=tk.LEFT)
        excludePathFrame.pack(expand=1,fill=tk.X,
                                     padx=(consts.DEFAUT_CONTRL_PAD_X,consts.DEFAUT_CONTRL_PAD_X))
# --------开始计算的按钮
        self.startCountingButton = ttk.Button(self.main_frame,
                                        command=self.startCounting,text=_("Start Counting!"))


        self.startCountingButton.pack(expand=1,fill=tk.X,padx=consts.DEFAUT_CONTRL_PAD_X,pady=(
            consts.DEFAUT_CONTRL_PAD_Y,consts.DEFAUT_CONTRL_PAD_Y))
        
#--------表格窗体、滚动条等。
          
        self.tableFrame=ttk.Frame(self.main_frame)
        self.scrollbar=ttk.Scrollbar(self.tableFrame,orient=tk.VERTICAL)
        self.table = ttk.Treeview(self.tableFrame,show="headings")
        self.scrollbar.config(command=self.table.yview)
        self.table.configure(yscrollcommand=self.scrollbar.set)
        
        # 定义列
        self.table['columns'] = ['fileName','validLines',
                                 'blankLines','commentLines','allRows']
        # 设置列宽度
        self.table.column('fileName',width=400)
        self.table.column('validLines',width=80)
        
        self.table.column('blankLines',width=80)
        self.table.column('commentLines',width=100)
        self.table.column('allRows',width=80)
        # 添加列名
        self.table.heading('fileName',text=_('File Path'))
        self.table.heading('validLines',text=_('Code Lines'))  

        self.table.heading('blankLines',text=_('Blank Lines'))
        self.table.heading('commentLines',text=_('Comment Lines'))
        self.table.heading('allRows',text=_('Total Lines'))
        
        self.table.pack(side=tk.LEFT,fill=tk.X,expand=1)
        self.scrollbar.pack(side=tk.RIGHT,fill=tk.Y,expand=1)
        self.tableFrame.pack(padx=consts.DEFAUT_CONTRL_PAD_X,pady=(0,consts.DEFAUT_CONTRL_PAD_Y))
        self.progressBar = ttk.Progressbar(self.main_frame, orient = tk.HORIZONTAL,
              length = 100, mode = 'determinate')
              
        self.progressBar.pack(expand=1,fill=tk.X,padx=consts.DEFAUT_CONTRL_PAD_X,pady=(consts.DEFAUT_CONTRL_PAD_Y,consts.DEFAUT_CONTRL_PAD_Y))
        
        self.countingFlag=False
        self.countingThread=threading.Thread(target=self.count)# 统计行数的线程。


    def startCounting(self):
        
        if(self.countingFlag==False):
            if(self.countingThread.isAlive()):
                #print('isAlive!!!!!!')
                self.countingFlag=False
                return #等待直到线程退出为止
            
            self.countingFlag=True
            self.startCountingButton.config(text=_("Stop Counting!"))
            self.countingThread=threading.Thread(target=self.count)
            self.countingThread.setDaemon(True)
            self.countingThread.start()
            
        else:
            self.countingFlag=False
            self.startCountingButton.config(text=_("Start Counting!"))
            
    
    def removeExcludedDir(self):
        selIndex=self.excludeFolderListBox.curselection()
        self.excludeFolderListBox.delete(selIndex)
        
    def popWarningWindow(self,message):
        tk.messagebox.showinfo(_('Warning'),message)
        
    def chooseExcludedDir(self):

        self.excludeFolderListBox.selection_clear(0,self.excludeFolderListBox.size()-1)
        path = askdirectory()
        if(path!=''):
            path=epd.formatPathForPlatform(path)
            pathList=self.excludeFolderListBox.get(0,self.excludeFolderListBox.size()-1)
            
            if(path not in pathList):#文件名不重复的话就加上
                self.excludeFolderListBox.insert('end',path)
            else:#如果有重复，就将重复选项设置为选中。
                index = pathList.index(path)
                self.excludeFolderListBox.selection_set(index)
        
        
    def getAllExcludedFolders(self):
        f=self.excludeFolderListBox.get(0,self.excludeFolderListBox.size()-1)
        
        #print(f)
        return list(f)
        
    
    def clearResultTable(self):
        for child in self.table.get_children():# 首先将列表中已有的元素清除。经测试，即使列表中啥都没有，
                                               # 也能顺利运行，所以就不做判断非空了。
            self.table.delete(child)

    def count(self):

        extStr,extNameList=stdInputHandler(self.extEntry)
        excFolderList=self.getAllExcludedFolders()

        self.clearResultTable()
        self.progressBar['value']=0

        
        if(self.pathMode.get()==1):
            self.path=self.pathEntry.get().strip()# 每次要从文本框中获取一次路径。
            if(os.path.isdir(self.path)):#判断路径是否存在。如果存在，执行if中的语句。
                result=CodeCounter.countDirFileLines(self.path,excludeDirs=excFolderList,excludeFiles=[],
                                                 includeExts=extNameList,progressBar=self.progressBar,master=self)
        else:
            self.projectDocs=getCurrentProjectDocuments()
            #print(self.projectDocs)

            fileNum=CodeCounter.countDirFileLines(fileList=self.projectDocs,excludeDirs=excFolderList,excludeFiles=[],
                                                 includeExts=extNameList,progressBar=self.progressBar,master=self)
            if(fileNum==0):
                #self.popWarningWindow("Current Project is Empty!")
                #self.wait_window() 
                pass
        time.sleep(3)
        self.progressBar['value']=0
    
        
    def changePathMode(self):
        if(self.pathMode.get()==1):
            
            self.askpathButton['state']='normal'
            self.pathEntry['state']='normal'
        else:
            self.askpathButton['state']='disable'
            self.pathEntry['state']='disable'
        
    
    def chooseDir(self):
        self.pathMode.set(1)
        
        if(self.pathMode.get()==1):
           path = askdirectory()
        elif(self.pathMode.get()==0):
           path = askopenfilename()
        self.pathEntry.delete(0,tk.END)
        self.pathEntry.insert(0,epd.formatPathForPlatform(path))
        self.path=path
        
        
    def _ok(self, event=None):
        pass
        
    def GetStringSelection(self):
        return self.listbox.get(self.listbox.curselection()[0])


def startDialog(app,ico):#这个函数用来启动插件。无论是装入IDE时还是调试时，都调用这个函数。
      dialog=CodeCounterDialog(app,title=_("CodeCounter"),label="dadadadadada")
      print(ico)
      dialog.iconphoto(False, tk.PhotoImage(file=ico))
      dialog.ShowModal()

class BaseAppForTest:#这是用于测试的基底界面，插件安装后不会运行。
    def __init__(self, master):
        self.master = master
        self.initWidgets()
 
    def initWidgets(self):
        
        ttk.Button(self.master, text='打开Dialog',
                   command=self.openDialog # 绑定 openDialog 方法
                   ).pack(side=tk.LEFT, ipadx=5, ipady=5, padx=10)
    
    def openDialog(self):
        startDialog(self.master)



def main(ico):#当插件未装入IDE的时候，因其无基底界面，所以无法调试。为了解决这个
    #问题，便要新建一个临时APP的基底,用于界面测试。

    app = GetApp()
    startDialog(app,ico)

   
   
if __name__ == "__main__":
    getSupportedDocuments()
    #main()
    
