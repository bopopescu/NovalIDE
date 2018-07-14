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