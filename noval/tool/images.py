import wx
from wx import ImageFromStream, BitmapFromImage
import noval.util.appdirs as appdirs
import os

#----------------------------------------------------------------------
def getBlankBitmap():
    blank_image_path = os.path.join(appdirs.GetAppImageDirLocation(), "blank.png")
    blank_image = wx.Image(blank_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(blank_image)

def getBlankIcon():
    return wx.IconFromBitmap(getBlankBitmap())
#----------------------------------------------------------------------

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

def load(image_path):
    if not os.path.isabs(image_path):
        image_path = os.path.join(appdirs.GetAppImageDirLocation(), image_path)
    img = wx.Image(image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(img)
    
def load_icon(icon_path):
    if icon_path.lower().endswith(".ico"):
        if not os.path.isabs(icon_path):
            icon_path = os.path.join(appdirs.GetAppImageDirLocation(), icon_path)
        return wx.Icon(icon_path, wx.BITMAP_TYPE_ICO)
    return wx.IconFromBitmap(load(icon_path))
    