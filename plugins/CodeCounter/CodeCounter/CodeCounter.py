#coding=utf-8
import sys
import os
import datetime
import argparse
import chardet
import re

import noval.syntax.syntax as syntax
from noval.util import logger
import noval.util.utils as utils
import noval.syntax.lang as lang

import easyplugindev as epd
from easyplugindev import _

def getResourcePath():
    from pkg_resources import resource_filename
    path = resource_filename(__name__,'')  
    clone_local_img_path = os.path.join(path,"codecounter.png") # 导入同一个包下的文件.
    return clone_local_img_path
    
def isFileExclude(fullFilePath,excludeDirs,excludeFiles):#目前尚未做排除单个文件的工作。
    fullFilePath=fullFilePath.replace('\\','/')
    
    for d in excludeDirs:
        d = d.replace('\\','/')
        
        if(fullFilePath.find(d)!=-1):
            return True
    return False

def isDirExclude(path,excludeDirs):

    if path in excludeDirs:
        return True
    
    loopPath = os.path.dirname(root)
    while loopPath:
        if loopPath in excludeDirs:
            return True
        parentPath = os.path.dirname(loopPath)
        if parentPath == loopPath:
            break
        loopPath = parentPath
    
    return False
def isCommentLine(line,lineCommentFlag):
    
    if lineCommentFlag == None:
        return False
    
    if line.startswith(lineCommentFlag):
        return True
    return False

def isBlockCommentStart(line,blockCommentStartFlag):
    if blockCommentStartFlag == None:
        return False

    return isCommentLine(line,blockCommentStartFlag)

def isBlockCommentEnd(line,blockCommentEndFlag):
    if blockCommentEndFlag == None:
        return False

    line = line.rstrip()
    if line.endswith(blockCommentEndFlag):
        return True
    return False

def adaptEncoding(f):#自适应编码方式
    text = f.read()
        
    encoding=chardet.detect(text)['encoding']
    if(encoding==None):#对于无法检测出编码的文件，可以跳过去。所以直接返回None等待处理。
        return None
    return text.decode(encoding)
    
blockCommentStartFlagDict={"md":None,'py':('\'\'\'','\"\"\"','r\"\"\"'),'c':('/*'),'css':'/*'}
blockCommentEndFlagDict={"md":None,'py':('\'\'\'','\"\"\"'),'c':('*/'),'css':'*/'}
lineCommentFlagDict={"md":None,'py':('#'),'c':('//'),'css':'/*'}
lineCommentEndDict={"css":"*/"}

def getCommentPatternByExtName(ext=''):
##    try:
    fileLexer=syntax.SyntaxThemeManager().GetLangLexerFromExt(ext)
    langId=fileLexer.GetLangId()
    if(langId==lang.ID_LANG_TXT):
        return None,None,None,True
    pattern=fileLexer.GetCommentPatterns()
    

    if(len(pattern)==1):# 前三位分别是单行注释、多行注释开始、多行注释结束。第四位是是否为纯文本文件。
        if(len(pattern[0])==1):
            
            return pattern[0][0],None,None,False
        else:
            return pattern[0][0],pattern[0][1],None,False
    elif(len(pattern)==2):
        if(len(pattern[0])==1):
            return pattern[0][1],pattern[1][0],pattern[1][1],False
        else:
            return pattern[0][0],pattern[0][1],pattern[1][0],False
        
    else:
        return pattern[2],pattern[0],pattern[1],False

def countPlainText(content):
    validLinesCount=0
    blankLinesCount=0
    
    for i,line in enumerate(content):
        
        if line.strip() == "":
            blankLinesCount+=1
        else:
            validLinesCount+=1
    return [0,blankLinesCount,0,blankLinesCount+validLinesCount]   

def countFileLine(filePath):
    global blockCommentStartFlagDict,blockCommentEndFlagDict,lineCommentFlag
    
    fileType=filePath.split('.')[-1]
    
    lineCommentFlag, blockCommentStartFlag, blockCommentEndFlag,isTxt=getCommentPatternByExtName(fileType)
    with open(filePath,'rb') as f: # 打开文件开始扫描
        
        content= adaptEncoding(f)
        if(content==None):# 如果没有内容就返回[0,0,0]
            return [0,0,0,0]
            
        content = content.strip() # 预先剪掉content头部和尾部的赘余，以免计入文件结尾的空行。
        lines = content.split('\n') # re.split(r"([\n])", content)# 正则表达式应用。
        
        if(isTxt==True):# 如果没有“单行注释”这一说的话(说明多行注释也没有)
            return countPlainText(lines)
        isInBlockComment = False
        count = 0
        validLinesCount=0
        commentLinesCount=0
        blankLinesCount=0
        for i,line in enumerate(lines): # 一行一行的扫描文件内部。
            #print(i,line)
            count += 1
            line = line.strip()
            
            if line == "":
                blankLinesCount+=1
                continue
            
            if isInBlockComment==True:
                commentLinesCount+=1
                if isBlockCommentEnd(line,blockCommentEndFlag):#如果是注释结束，就将标识符置为否
                    isInBlockComment = False
                    continue  
                else:
                    continue    
            else:         
                if isBlockCommentStart(line,blockCommentStartFlag):#如果是注释开始，就将标识符置为是
                    isInBlockComment = True
                    commentLinesCount+=1
                    continue
               
     
            if isCommentLine(line,lineCommentFlag):#如果是注释行，那么就跳转。
                commentLinesCount+=1
                continue      
            
            validLinesCount+=1
    return [validLinesCount,blankLinesCount,commentLinesCount,validLinesCount+blankLinesCount+commentLinesCount]


def getFileNames(dirPath,fileList):    
    filenames=[]
    if(dirPath!=''):
        if(fileList!=[]):
            raise Exception('不得同时输入文件列表和搜索的文件夹路径！')
        else:
            for root,dirnames,tmpFilenames in os.walk(dirPath):
                root=os.path.abspath(root)
                
                for filename in tmpFilenames:
                    
                    
                    fullFilePath=os.path.join(root,filename)
                    filenames.append(fullFilePath)
        
    else:#如果入口参数是个列表的话，就这么统计。
        filenames=fileList
       
    return filenames
def countDirFileLines(dirPath='',fileList=[],excludeDirs=[],excludeFiles=[],includeExts=[],
                      progressBar=None,table=None,main=None,countingFlag=True):
    if(main!=None):
        table=main.table
        countingFlag=main.countingFlag
        
    excludeDirs=set(excludeDirs)
    excludeFiles=set(excludeFiles)
    includeExts=set(includeExts)
   
    totalLineCount = [0,0,0] # 分别对应valid,comment和blank三种内容。
    totalFileCount = 0
    
    


    def isSupportedFileType(ext):
        if ext in includeExts:
            return True
        else:
            return False
    filenames=getFileNames(dirPath=dirPath,fileList=fileList)
    filesToWalk=len(filenames)# 取得需要遍历的文件数量列表。
    
    
    walkedFiles=0
    totalSumCount=0
    
    for filename in filenames:
        walkedFiles+=1
        if(progressBar!=None):#在调用的时候，如果有进度条的选项，就更新它。
            progressBar['value']=walkedFiles/filesToWalk*100
        fileType=filename.split('.')[-1] # 取文件名的最后一项,也就是扩展名

        
        if(isSupportedFileType(fileType)!=True): # 如果不是支持的文件类型，就跳过这个文件的扫描。
            continue
        
        if isFileExclude(filename,excludeDirs,excludeFiles):
            continue
        
        if not os.path.exists(filename):# 如果文件不存在，就跳过循环。
            continue
        countList= countFileLine(filename)
        
        for i in range(3):
            totalLineCount[i] += countList[i]  
            
        countSum=countList[3]
        totalSumCount+=countSum
        
        totalFileCount += 1
       
        if(main!=None):
            if(main.countingFlag==False):
                main.progressBar['value']=0
                main.clearResultTable()
                return
            
            main.table.insert("",0,values=[epd.formatPathForPlatform(filename)]+countList+[countSum])#构造列表，直接插入表格。
    if(main!=None):
        main.table.insert("",0,values=[_("Counted:%d Files. Total:")%totalFileCount]+totalLineCount+[totalSumCount])
        main.startCountingButton.config(text=_("Start Counting!"))
        main.countingFlag=False
        return totalFileCount



if __name__ == "__main__":
    pass
##    r=countDirFileLines(r'C:\Users\hzy\Documents\python\NovalIDE\plugins\CodeCounter',excludeDirs=[],excludeFiles=[],includeExts=['py'])
##    import noval.util.utils as utils
##    utils.get_logger().info("sssssss")
