# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        fileutils.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-22
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import _
import logging
import copy
import os
import shutil
import sys
import zipfile
import noval.util.logger as logger
import noval.util.apputils as apputils
import noval.util.utillang as utillang
import subprocess
import noval.util.strutils as strutils
import chardet
import noval.util.txtutils as txtutils
import noval.syntax.lang as lang
import noval.syntax.syntax as syntax
global fileutilsLogger
from tkinter import messagebox
import getpass
import stat
fileutilsLogger = logging.getLogger("activegrid.util.fileutils")
_Checker = txtutils.FileTypeChecker()

def addRef(varname):
    return "${%s}" % varname

AG_SYSTEM_VAR_NAMES = [] # all AG System vars, with ${} syntax

AG_SYSTEM_VAR = "AG_SYSTEM"
AG_SYSTEM_VAR_REF = addRef(AG_SYSTEM_VAR)
AG_SYSTEM_VAR_NAMES.append(AG_SYSTEM_VAR_REF)

AG_SYSTEM_STATIC_VAR = "AG_SYSTEM_STATIC"
AG_SYSTEM_STATIC_VAR_REF = addRef(AG_SYSTEM_STATIC_VAR)
AG_SYSTEM_VAR_NAMES.append(AG_SYSTEM_STATIC_VAR_REF)

AG_APP_VAR = "AG_APP"
AG_APP_STATIC_VAR = "AG_APP_STATIC"

# _initAGSystemVars needs to be called to initialize the following two
# containers:
EXPANDED_AG_SYSTEM_VARS = {} # ${varname} -> value (path)
# ${varname}, ordered from longest to shortest path value
AG_SYSTEM_VARS_LENGTH_ORDER = [] 

def _initAGSystemVars():
    if (len(EXPANDED_AG_SYSTEM_VARS) > 0):
        return
    
    for v in AG_SYSTEM_VAR_NAMES:
        EXPANDED_AG_SYSTEM_VARS[v] = os.path.abspath(expandVars(v))
        AG_SYSTEM_VARS_LENGTH_ORDER.append(v)
        
    AG_SYSTEM_VARS_LENGTH_ORDER.sort(_sortByValLength)


def parameterizePathWithAGSystemVar(inpath):
    """Returns parameterized path if path starts with a known AG directory. Otherwise returns path as it was passed in."""
    _initAGSystemVars()
    path = inpath
    if not sysutils.isWindows():
        # ensure we have forward slashes
        path = path.replace("\\", "/")
        
    path = os.path.abspath(path)

    for varname in AG_SYSTEM_VARS_LENGTH_ORDER:
        varval = EXPANDED_AG_SYSTEM_VARS[varname]
        if path.startswith(varval):
            return path.replace(varval, varname)
        
    return inpath

def startsWithAgSystemVar(path):
    """Returns True if path starts with a known AG system env var, False otherwise."""
    for varname in AG_SYSTEM_VAR_NAMES:
        if path.startswith(varname):
            return True
    return False
        
def _sortByValLength(v1, v2):
    return len(EXPANDED_AG_SYSTEM_VARS[v2]) - len(EXPANDED_AG_SYSTEM_VARS[v1])

def makeDirsForFile(filename):
    d = os.path.dirname(filename)
    if (not os.path.exists(d)):
        os.makedirs(d)

def createFile(filename, mode='w'):
    f = None
    if (not os.path.exists(filename)):
        makeDirsForFile(filename)
    f = file(filename, mode)
    return f

def compareFiles(file1, file2, ignore=None):
##    result = filecmp.cmp(file1, file2)
##    if result:
##        return 0
##    return -1
    file1.seek(0)
    file2.seek(0)
    while True:
        line1 = file1.readline()
        line2 = file2.readline()
        if (len(line1) == 0):
            if (len(line2) == 0):
                return 0
            else:
                return -1
        elif (len(line2) == 0):
            return -1
        elif (line1 != line2):
            if (ignore != None):
                if (line1.startswith(ignore) or line2.startswith(ignore)):
                    continue
            line1 = line1.replace(" ", "")
            line2 = line2.replace(" ", "")
            if (line1 != line2):
                len1 = len(line1)
                len2 = len(line2)
                if ((abs(len1 - len2) == 1) and (len1 > 0) and (len2 > 0) 
                    and (line1[-1] == "\n") and (line2[-1] == "\n")):
                    if (len1 > len2):
                        longer = line1
                        shorter = line2
                    else:
                        shorter = line1
                        longer = line2
                    if ((longer[-2] == "\r") and (longer[:-2] == shorter[:-1])):
                        continue
                    if ((longer[-2:] == shorter[-2:]) and (longer[-3] == "\r") and (longer[:-3] == shorter[:-2])):
                        continue
                return -1

def expandKnownAGVars(value):
    return expandVars(value, includeEnv=False)

def expandVars(value, includeEnv=True):
    """Syntax: ${myvar,default="default value"}"""
    import activegrid.runtime as runtime
    sx = value.find("${")
    if (sx >= 0):
        result = asString(value[:sx])
        endx = value.find("}")
        if (endx > 1):
            defaultValue = None
            defsx = value.find(",default=\"")
            if ((defsx > sx) and (defsx < endx)):
                varname = value[sx+2:defsx]
                if (value[endx-1] == '"'):
                    defaultValue = value[defsx+10:endx-1]
            if (defaultValue == None):
                varname = value[sx+2:endx]
            if (varname == AG_SYSTEM_VAR):
                varval = runtime.appInfo.getSystemDir()
            elif (varname == AG_SYSTEM_STATIC_VAR):
                varval = runtime.appInfo.getSystemStaticDir()
            elif (varname == AG_APP_VAR):
                varval = runtime.appInfo.getAppDir()
            elif (varname == AG_APP_STATIC_VAR):
                varval = runtime.appInfo.getAppStaticDir()
            else:
                if (includeEnv):
                    varval = os.getenv(varname)
                else:
                    varval = None
            if ((varval == None) and (defaultValue != None)):
                varval = defaultValue
            if (varval == None):
                result += value[sx:endx+1]
            else:
                result += varval
            return result + expandVars(value[endx+1:])
    return value

def toPHPpath(path, otherdir=None):
    return convertSourcePath(path, "php", otherdir=otherdir)
                    
def toPythonpath(path, otherdir=None):
    return convertSourcePath(path, "python", otherdir=otherdir)
                    
def toUnixPath(path):
    if (path != None and os.sep != '/'):
        path = path.replace(os.sep, '/')
    return path

def convertSourcePath(path, to, otherdir=None):
    fromname = "python"
    if (to == "python"):
        fromname = "php"
    pythonNode = os.sep + fromname + os.sep
    ix = path.find(pythonNode)
    if (ix < 0):
        ix = path.find(fromname) - 1
        if ((ix < 0) or (len(path) <= ix+7)
            or (path[ix] not in ("\\", "/")) or (path[ix+7]  not in ("\\", "/"))):
            raise Exception("Not in a %s source tree.  Cannot create file name for %s." % (fromname, path))
        if (otherdir == None):
            return path[:ix+1] + to + path[ix+7:]
        else:
            return otherdir + path[ix+7:]
    if (otherdir == None):
        return path.replace(pythonNode, os.sep + to + os.sep)
    else:
        return otherdir + path[ix+7:]


def visit(directory, files, extension, maxLevel=None, level=1):
    testdirs = os.listdir(directory)
    for thing in testdirs:
        fullpath = os.path.join(directory, thing)
        if (os.path.isdir(fullpath) and (maxLevel == None or level < maxLevel)):
            visit(fullpath, files, extension, maxLevel, level+1)
        elif thing.endswith(extension):
            fullname = os.path.normpath(os.path.join(directory, thing))
            if not fullname in files:
                files.append(fullname)
 
def listFilesByExtensionInPath(path=[], extension='.lyt', maxLevel=None):
    retval = []
    for directory in path:
        visit(directory, retval, extension, maxLevel)
    return retval

def getFileLastModificationTime(fileName):
    return os.path.getmtime(fileName)

def findFileLocation(location, fileName):
    i = fileName.rfind(os.sep)
    if i > 0:
        fileName = fileName[:i]
    while location[0:2] == '..' and location[2:3] == os.sep:
        location = location[3:]
        i = fileName.rfind(os.sep)
        fileName = fileName[:i]
    absPath = fileName + os.sep + location
    return absPath

def getAllExistingFiles(files, basepath=None, forceForwardSlashes=False):
    """For each file in files, if it exists, adds its absolute path to the rtn list. If file is a dir, calls this function recursively on all child files in the dir.
    If basepath is set, and if the file being processed is relative to basedir, adds that relative path to rtn list instead of the abs path.
    Is this is Windows, and forceForwardSlashes is True, make sure returned paths only have forward slashes."""
    
    if apputils.is_py3_plus():
        basestring_ = str
    elif apputils.is_py2():
        basestring_ = basestring
    if isinstance(files, basestring_):
        files = [files]
    rtn = []
    for file in files:
        if os.path.exists(file): 
            if os.path.isfile(file):
                if basepath and hasAncestorDir(file, basepath):
                    rtn.append(getRelativePath(file, basepath))
                else:
                    rtn.append(os.path.abspath(str(file)))
            elif os.path.isdir(file):
                dircontent = [os.path.join(file, f) for f in os.listdir(file)]
                rtn.extend(getAllExistingFiles(dircontent, basepath))
                
    if forceForwardSlashes and sysutils.isWindows():
        newRtn = []
        for f in rtn:
            newRtn.append(f.replace("\\", "/"))
        rtn = newRtn
        
    return rtn

def hasAncestorDir(file, parent):
    """Returns true if file has the dir 'parent' as some parent in its path."""
    return getRelativePath(file, parent) != None

def getRelativePath(file, basedir):
    """Returns relative path from 'basedir' to 'file', assuming 'file' lives beneath 'basedir'. If it doesn't, returns None."""
    file = os.path.abspath(file)
    parent = os.path.abspath(basedir)

    if file == parent:
        return None

    if file.startswith(parent):
        return file[len(parent)+1:]
    
    return None

def isEmptyDir(dir):
    if not os.path.isdir(dir):
        return False
    return len(os.listdir(dir)) == 0

def zip(zipfilepath, basedir=None, files=None):
    """Zip all files in files and save zip as zipfilepath. If files is None, zip all files in basedir. For all files to be zipped, if they are relative to basedir, include the relative path in the archive."""
    
    if files is None and basedir is None:
        raise AssertionError("Either 'basedir' or 'files' must be set")
    if files is None:
        logger.debug(fileutilsLogger,\
                        "Looking for files to zip in %s" % basedir)
        files = getAllExistingFiles(basedir)
    else:
        # removes files that don't exist and gets abs for each
        files = getAllExistingFiles(files) 
    if len(files) == 0:
        logger.debug(fileutilsLogger, "No files to zip, nothing to do")
        raise ValueError(_("No files to zip, nothing to do!"))
    
    z = zipfile.ZipFile(zipfilepath, mode="w", compression=zipfile.ZIP_DEFLATED)

    try:
        for file in files:
            arcname = None
            if basedir:
                arcname = getRelativePath(file, basedir)
            if not arcname:
                arcname = file
                fileutilsLogger.debug("%s: adding %s with arcname %s" %(zipfilepath, file, arcname))
            z.write(file, arcname)
    finally:
        z.close()        

def unzip(zipfilepath, extractdir):
    """Unzip zipfilepath into extractdir."""
    z = zipfile.ZipFile(zipfilepath, mode="r")
    for info in z.infolist():
        filename = os.path.join(extractdir, info.filename)
        try:
            dir = os.path.dirname(filename)
            logger.debug(fileutilsLogger, "Creating dir %s" % dir)
            os.makedirs(dir) # do we have to worry about permissions?
        except:
            pass
        if os.path.isdir(filename):
            continue
        logger.debug(fileutilsLogger,\
                       ("Writing arcfile %s to %s" % (info.filename, filename)))
        f = open(filename, "w")
        f.write(z.read(info.filename))
        f.close()


def copyFile(src, dest):
    """Copies file src to dest. Creates directories in 'dest' path if necessary."""
    destdir = os.path.dirname(dest)
    if not os.path.exists(destdir):
        os.makedirs(destdir)
    shutil.copy(src, dest)

def copyDir(src, dest):
    """Copies dir 'src' into dir 'dest'. Creates 'dest' if it does not exist."""
    shutil.copytree(src, dest)

def safe_remove(file):
    if not os.path.exists(file):
        return
    try:
        #删除只读文件之前需要设置文件可写
        os.chmod(file, stat.S_IWRITE)
    except:
        pass
    if os.path.isfile(file):
        try:
            os.remove(file)
        except:
            pass
    elif os.path.isdir(file):
        try:
            shutil.rmtree(file)
        except:
            pass

#@accepts str, dict, str, str, boolean
def replaceToken(infilepath, tokens={}, outfilepath=None, delim="@@",\
                 useEnv=False):
    """Replaces tokens of form 'delim'<tokenname>'delim' in file at 'infilepath', using values in dict 'tokens'. If 'outfilepath' is set, writes output to 'outfilepath', if not set, overwrites original file. If 'useEnv' is True, adds os.environ to 'tokens'. This makes it possible to define an env var FOO=BLAH, and have @@FOO@@ be replaced with BLAH, without explicitly passing FOO=BLAH in 'tokens'. Note that entries in 'tokens' take precedence over entries in os.environ."""

    if useEnv:
        for key, val in os.environ.items():
            # passed in tokens take precedence
            if not tokens.has_key(key):
                tokens[key] = val        
    
    f = open(infilepath, "r")
    try:
        content = f.read()
    finally:
        if f: f.close()

    for token, value in tokens.items():
        content = content.replace("%s%s%s" % (delim, token , delim), str(value))

    if not outfilepath: outfilepath = infilepath
    f = open(outfilepath, "w")
    try:
        f.write(content)
    finally:
        if f: f.close()

def open_file_directory(file_path):
    """
        Opens the parent directory of a file, selecting the file if possible.
    """
    ret = 0
    err_msg = ''
    if apputils.is_windows():
        # Normally we can just run `explorer /select, filename`, but Python 2
        # always calls CreateProcessA, which doesn't support Unicode. We could
        # call CreateProcessW with ctypes, but the following is more robust.
        import ctypes
        import win32api
        
        ctypes.windll.ole32.CoInitialize(None)
        # Not sure why this is always UTF-8.
        pidl = ctypes.windll.shell32.ILCreateFromPathW(file_path)
        if 0 == pidl:
            pidl = ctypes.windll.shell32.ILCreateFromPathA(file_path)
            
        if 0 == pidl:
            ret = ctypes.windll.kernel32.GetLastError()
            err_msg = win32api.FormatMessage(ret)
            if apputils.is_py2():
                err_msg = err_msg.decode(apputils.get_default_encoding())
        try:
            ctypes.windll.shell32.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
            ctypes.windll.shell32.ILFree(pidl)
            ctypes.windll.ole32.CoUninitialize()
        except:
            #选中指定对象.如果使用"/select",则父目录被打开,并选中指定对象,请注意命令中"/select"参数后面的逗号
            subprocess.Popen(["explorer", "/select," + file_path])
    else:
        try:
            subprocess.Popen(["nautilus", file_path])
        except Exception as e:
            ret = -1
            err_msg = str(e)
            
    if ret != 0:
        raise RuntimeError(err_msg)

def open_path_in_terminator(file_path):
    ret = 0
    err_msg = ''
    sys_encoding = apputils.get_default_encoding()
    if apputils.is_windows():
        import ctypes
        import win32api
        try:
            if apputils.is_py2():
                file_path = file_path.encode(sys_encoding)
            subprocess.Popen('start cmd.exe',shell=True,cwd=file_path)
        except:
            ret = ctypes.windll.kernel32.GetLastError()
            err_msg = win32api.FormatMessage(ret)
            if apputils.is_py2():
                err_msg = err_msg.decode(apputils.get_default_encoding())
    else:
        try:
            subprocess.Popen('gnome-terminal',shell=True,cwd=file_path.encode(sys_encoding))
        except Exception as e:
            ret = -1
            err_msg = str(e)
    if ret != 0:
        raise RuntimeError(err_msg)
        
def startfile(file_path):
    if apputils.is_windows():
        os.startfile(file_path)
    else:
        subprocess.call(["xdg-open", file_path])
        

def is_path_hidden(path):
    
    def is_windows_file_hidden(path):
        import win32con
        import win32file
        file_flag = win32file.GetFileAttributesW(path)
        hidden_flag = file_flag & win32con.FILE_ATTRIBUTE_HIDDEN
        is_hidden = True if hidden_flag == win32con.FILE_ATTRIBUTE_HIDDEN else False
        return is_hidden
    
    if os.path.basename(path).startswith("."):
        return True
    elif apputils.is_windows():
        return is_windows_file_hidden(path)
        
def is_file_path_hidden(path):
    '''
        检查文件或目录是否隐藏,只要全路径中的某一段路径具有隐藏属性,则该全路径是隐藏的
    '''
    if apputils.is_windows():
        is_hidden = False
        if os.path.isfile(path):
            is_hidden = is_path_hidden(path)
        ###files or dirs in hidden dir is not hidden,so we shoud rotate to hidden dir
        else:
            while True:
                if os.path.dirname(path) == path:
                    break
                is_hidden = is_path_hidden(path)
                if is_hidden:
                    break
                path = os.path.dirname(path)
        return is_hidden
    else:
        is_hidden = False
        if os.path.isfile(path):
            is_hidden = is_path_hidden(path)
        else:
            while True:
                dirname = os.path.basename(path)
                if dirname == "" or dirname == "/":
                    break
                is_hidden = is_path_hidden(path)
                if is_hidden:
                    break
                path = os.path.dirname(path)
        return is_hidden
        
def GetDirFiles(path,file_list,filters=[],rejects=[]):
    for f in os.listdir(path):
        file_path = os.path.join(path, f)
        if os.path.isfile(file_path):
            ext = strutils.get_file_extension(file_path)
            if ext in rejects :
                continue
            if filters == []:
                file_list.append(file_path)
            else:
                if ext in filters:
                    file_list.append(file_path)
                        


def detect(byte_str):
    """
    Detect the encoding of the given byte string.

    :param byte_str:     The byte sequence to examine.
    :type byte_str:      ``bytes`` or ``bytearray``
    """
    if not isinstance(byte_str, bytearray):
        if not isinstance(byte_str, bytes):
            raise TypeError('Expected object of type bytes or bytearray, got: '
                            '{0}'.format(type(byte_str)))
        else:
            byte_str = bytearray(byte_str)
    pre_read = 4096
    if not _Checker.IsUnicode(byte_str[0:pre_read]) and _Checker.IsBinaryBytes(byte_str[0:pre_read]):
        return {'encoding':'binary'}
    detector = chardet.UniversalDetector(chardet.enums.LanguageFilter.CHINESE)
    detector.feed(byte_str)
    return detector.close()
    
def is_python_file(file_path):
    lexer = syntax.SyntaxThemeManager().GetLexer(lang.ID_LANG_PYTHON)
    ext = strutils.get_file_extension(file_path)
    return lexer.ContainExt(ext)

def RemoveDir(dir_path):
    files = os.listdir(dir_path)
    for f in files:
        file_path = os.path.join(dir_path, f)
        if os.path.isdir(file_path):
            RemoveDir(file_path)
        else:
            os.remove(file_path)
    os.rmdir(dir_path)
    

if apputils.is_windows():
    def is_writable(path, user=None):
        return True
else:
    import pwd
    def is_writable(path, user=None):
        if not user:
            user = getpass.getuser()
        user_info = pwd.getpwnam(user)
        uid = user_info.pw_uid
        gid = user_info.pw_gid
        s = os.stat(path)
        mode = s[stat.ST_MODE]
        return (
            ((s[stat.ST_UID] == uid) and (mode & stat.S_IWUSR > 0)) or
            ((s[stat.ST_GID] == gid) and (mode & stat.S_IWGRP > 0)) or
            (mode & stat.S_IWOTH > 0)
         )

def opj(path):
    """Convert paths to the platform-specific separator"""
   ### st = apply(os.path.join, tuple(path.split('/')))
    split_paths = path.split('/')
    #修复os.path.join bug,在windows下硬盘符号后面必须添加路径分隔符
    if split_paths[0].endswith(":") and not path.startswith('/'):
        split_paths[0] += os.sep
    paths = tuple(split_paths)
    st = os.path.join(*paths)
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        st = '/' + st
    return st
    
def get_filename_from_path(path):
    """
    Returns the filename for a full path.
    """
    return os.path.split(path)[1]
    

def get_filepath_from_path(path):
    """
    Returns the filename for a full path.
    """
    return os.path.split(path)[0]

def safe_open_file_directory(path):
    try:
        open_file_directory(path)
    except RuntimeError as e:
        messagebox.showerror(_("Error"),str(e))
