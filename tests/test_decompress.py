# -*- coding: utf-8 -*-

import zlib

def decompress(infile, dst):
    infile = open(infile, 'rb')
    dst = open(dst, 'wb')
    decompress = zlib.decompressobj()
    data = infile.read(1024)
    while data:
        dst.write(decompress.decompress(data))
        data = infile.read(1024)
    dst.write(decompress.flush())
    
def compress(data, dst, level=9):
    dst = open(dst, 'wb')
    compress = zlib.compressobj(level)
    dst.write(compress.compress(data))
    dst.write(compress.flush())
    dst.close()
    
data_str = '''This class is an abstract base class for some wxWidgets 
controls which contain several items such as wx.ListBox,wx.CheckListBox, 
wx.ComboBox or wx.Choice.

It defines an interface which is implemented by all controls which 
have string subitems each of which may be selected.

wx.ItemContainer extends wx.ItemContainerImmutable interface with 
methods for adding/removing items.

It defines the methods for accessing the controls items and although 
each of the derived classes implements them differently,they still 
all conform to the same interface.
'''
compress(data_str,r"D:\env\Noval\noval\tool\data\sample\txt.sample")
decompress(r"D:\env\Noval\noval\tool\data\sample\txt.sample",r"D:\env\Noval\noval\tool\data\sample\txt_src.sample")
###decompress(u"D:\\env\\软件项目\\FoxCop\\Release\\sample\\cpp.sp",u"D:\\env\\软件项目\\FoxCop\\Release\\sample\\cpp_code.sp")
