#coding:utf-8
import md5

def get_range_size(range_size_bytes):

    if range_size_bytes < 1024*1024:
        range_size = "%.2fK" % (range_size_bytes/1024.0)
    else:
        range_size = "%.2fM" % (range_size_bytes/1024.0/1024.0)

    return range_size

class FileRange(object):

    '''
        文件分块类
    '''

    def __init__(self,file_path,range_id,start,end,block_size,is_last = False):

        self._file_path = file_path
        self._start_byte = start
        self._end_byte = end
        self._block_size = block_size
        self._range_id = range_id
        self._is_last_range = is_last
    
    @property
    def range_id(self):
        '''
            分块id
        '''
        return self._range_id
    
    @property
    def file_path(self):
        '''
            分块文件路径
        '''
        return self._file_path
    
    @file_path.setter
    def file_path(self,path):
        '''
            设置分块文件路径
        '''
        self._file_path = path
    
    @property
    def start(self):
        '''
            分块在文件的开始位置
        '''
        return self._start_byte
    
    @property
    def end(self):
        '''
            分块在文件的结束位置
        '''
        return self._end_byte
    
    @property
    def size(self):
        '''
            分块的大小,其值应为分块的end字节位置-分块的start字节位置
        '''
        return self._block_size
   
    @property
    def is_last(self):
        '''
            是否是最后一个分块
        '''
        return self._is_last_range
 
    def __str__(self):

        range_size = get_range_size(self.size)
        file_range_str = 'file_path:%s id:%d,range_start:%ld,range_end:%ld,range_size:%s,is_last_range:%s' % (self.file_path,self.range_id,self.start,self.end,range_size,self.is_last)
        return file_range_str

    
def get_file_range(file_path,part_id,file_size,block_size,is_last_block=False):

    if not is_last_block:
        start_byte = block_size *(part_id -1)
        end_byte = block_size*(part_id)
    else:
        start_byte = block_size *(part_id -1)
        end_byte = file_size
        block_size = file_size - block_size * (part_id -1)

    return FileRange(file_path,part_id,start_byte,end_byte,block_size,is_last_block)


def get_file_ranges_by_part(file_path,part_number,file_size):

    '''
        文件分块方法1：
        按固定分块个数对文件进行分块，分块的个数是固定的，分块的大小随分块个数变化，最后一个分块大小必须特殊处理
    '''

    block_size = file_size/part_number
    file_ranges = []
    for i in range(part_number):
        part_id = i + 1 
        is_last_block = False
        if part_id == part_number:
            is_last_block = True

        file_range = get_file_range(file_path,part_id,file_size,block_size,is_last_block)
        file_ranges.append(file_range)

    return file_ranges
    
def get_file_ranges_by_size(file_path,part_size,file_size):
    
    '''
        文件分块方法2：
        按固定分块大小对文件进行分块，分块的大小是固定的，分块个数随分块的大小而变化，最后一个分块大小必须特殊处理
    '''
    block_size = part_size
    part_number = file_size / block_size
    remain_block_size = file_size % block_size 
    if remain_block_size > 0:
        part_number += 1

    file_ranges = []
    for i in range(part_number):
        part_id = i + 1 
        is_last_block = False
        if part_id == part_number:
            is_last_block = True

        file_range = get_file_range(file_path,part_id,file_size,block_size,is_last_block)
        file_ranges.append(file_range)

        if is_last_block and remain_block_size > 0:
            assert(remain_block_size == file_range.size)

    return file_ranges
   
