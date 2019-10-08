# -*- coding: utf-8 -*-
from noval import GetApp
import tkinter as tk
import noval.util.appdirs as appdirs
import os
from PIL import Image,ImageTk
import noval.util.utils as utils

try:
    import StringIO
except ImportError:
    import io as StringIO
#----------------------------------------------------------------------


def getImageData():
    return \
b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x017IDAT8\x8dcddbfh\x9f\xb3\xf3?\x03\x0e\xf0\xfc\xc5[\x0c\xb1\xfb\x0f\
\x9f10000l\x9e]\xc2\xc8\x02\x13,Ot\xc6e\x06V\xe0\x9f1\x81\x81\x81\x81\x81\
\x81\x05Y\xf0\xdc\x0b\x88C\x1e|\xfc\xc2\xf0\xe3\xf7\x01\x86{\x1fO20000(\xf1\
\x9b3p\xb0:\xc0\xd5\x05\xa9\xf3\xc2\xd9L\xe8&\xa3kf```8\xfah-\xc3\xb57\x9d\
\x0c?~\x1f\xc0p\t\x86\x01\xe8\x9aa\xe0\xf9\xc7\'X\xc5Q\x0c\x90\xe1c\xc4P\xf4\
\xfc\xe3\x13\x14\xb6\x02?\x0f~\x17(\xf1\x9bc\xd5\xcc\xc0\xc0\xc0 \xc9/\x03g_\
\xbbx\ta\x00,\xaa\xc4\xb8\x18\x18\x8c%\xd5\xb0j\x86\x19n$\xc1\x88"\xc6\x82\
\xaeH]X\x9d!T#\x96\xe1\xec\xf3[\x0cG\x1f\xade````\xb0\x96\x0bf0\x96TcP\x17V\
\xc70\x14\xc3\x00\x98!\xea\xc2\xea\x0c\xb7\x1a\x1a\x19\x18\x18\x18\x18\xa2\
\xd6,\xc0\xa6\x0c\xe1\x05J\x00\x0b\x03\x03"iz,\xd3A\x91|l\xf2\x8a\x81\x81\
\x81\x81au\x87\x18\x8a\xf8\xd5\x8aW\xc4\xb9@VN\x0c\x9f4v\x03\x94\x05LH2\x04%\
\x10wD]!h#N\x03`\xb9\x0b\x06`\t\x85\x10\x00\x00\xe4\x0ecz\x94h\xf0\x8e\x00\
\x00\x00\x00IEND\xaeB`\x82' 

def getBlankIcon():
    return load_image("","file/blank.png")

def getTextIcon():
    return load_image("","file/file.gif")

def getCFileBitmap():
    cfile_image_path = os.path.join(appdirs.GetAppImageDirLocation(), "c_file.gif")
    cfile_image = wx.Image(cfile_image_path, wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(cfile_image)
    
def getCFileIcon():
    return wx.IconFromBitmap(getCFileBitmap())
#----------------------------------------------------------------------

def getCppFileBitmap():
    cpp_file_image_path = os.path.join(appdirs.GetAppImageDirLocation(), "cpp.png")
    cpp_file_image = wx.Image(cpp_file_image_path, wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(cpp_file_image)
    
def getCppFileIcon():
    return wx.IconFromBitmap(getCppFileBitmap())
#----------------------------------------------------------------------

def getCHeaderFileBitmap():
    c_hfile_image_path = os.path.join(appdirs.GetAppImageDirLocation(), "h_file.gif")
    c_hfile_image = wx.Image(c_hfile_image_path, wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(c_hfile_image)
    
def getCHeaderFileIcon():
    return wx.IconFromBitmap(getCHeaderFileBitmap())
#----------------------------------------------------------------------

def getCSSBitmap():
    blank_image_path = os.path.join(appdirs.GetAppImageDirLocation(), "css.png")
    blank_image = wx.Image(blank_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(blank_image)
    
def getCSSFileIcon():
    return wx.IconFromBitmap(getCSSBitmap())
    
#----------------------------------------------------------------------
    
def getConfigBitmap():
    blank_image_path = os.path.join(appdirs.GetAppImageDirLocation(), "config.png")
    blank_image = wx.Image(blank_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(blank_image)
    
def getConfigFileIcon():
    return wx.IconFromBitmap(getConfigBitmap())
    
#----------------------------------------------------------------------
    
def getJavaScriptBitmap():
    blank_image_path = os.path.join(appdirs.GetAppImageDirLocation(), "javaScript.png")
    blank_image = wx.Image(blank_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(blank_image)
    
def getJavaScriptFileIcon():
    return wx.IconFromBitmap(getJavaScriptBitmap())
    
#----------------------------------------------------------------------

def load_image(tk_name,image_path,scaling_factor=None):
    if scaling_factor is None:
        scaling_factor = GetApp()._scaling_factor
    if not os.path.isabs(image_path):
        image_path = os.path.join(appdirs.get_app_image_location(), image_path)
    try:
        #tk图片随ui缩放比例缩放
        if scaling_factor >= 2.0:
            img = tk.PhotoImage(file=image_path)
            # can't use zoom method, because this doesn't allow name
            tk_img = tk.PhotoImage(tk_name)
            GetApp().tk.call(
                tk_img,
                "copy",
                img.name,
                "-zoom",
                int(scaling_factor),
                int(scaling_factor),
            )
        else:
            tk_img = tk.PhotoImage(tk_name, file=image_path)
    except Exception as e:
        utils.get_logger().debug("tk open image %s fail,%s",image_path,e)
        img = Image.open(image_path)
        #pil图片随ui缩放比例缩放
        if scaling_factor >= 2.0:
            width = int(img.width*scaling_factor)
            height = int(img.height*scaling_factor)
            img = img.resize((width, height),Image.ANTIALIAS)
        tk_img = ImageTk.PhotoImage(img)
    return tk_img

def getShellFileIcon():
    return load_icon("shell.png")
    
def getWebIcon():
    return load_icon("web.png")

def get_default_icon():
    default_image_path = os.path.join(appdirs.get_app_path(),"noval.ico")
    return load_image("",default_image_path)
    
def load_image_from_stream(image_data):
    if utils.is_py2():
        stream = StringIO.StringIO(image_data)
    elif utils.is_py3_plus():
        stream = StringIO.BytesIO(image_data)
    img = ImageTk.PhotoImage(Image.open(stream))
    return img
    
def get_image_file_icon():
    return load_image_from_stream(getImageData())

def getPythonIcon():
    return load_image("","file/python_module.png")

def getProjectIcon():
    return load_image("","project/project.png")

def getPackageFolderIcon():
    return load_image("","project/python/package_obj.gif")

def getFolderClosedIcon():
    return load_image("","project/folder_close.png")

def getFolderOpenIcon():
    return load_image("","project/folder_open.png")