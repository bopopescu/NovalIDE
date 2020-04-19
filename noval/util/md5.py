#coding:utf-8

#python 检测文件MD5值
 
import hashlib
import os,sys

def get_str_md5(content):
    '''
        将字符串用MD5加密
    '''
    m0=hashlib.md5()
    m0.update(content.encode('utf-8'))
    return m0.hexdigest()
 
#大文件的MD5值
def get_huge_file_md5(filename):

    myhash = hashlib.md5()
    f = file(filename,'rb')
    while True:
        b = f.read(8096)
        if not b :
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()
 
def calc_sha1(filepath):
    with open(filepath,'rb') as f:
        sha1obj = hashlib.sha1()
        sha1obj.update(f.read())
        hash = sha1obj.hexdigest()
        return hash
 
def get_normal_file_md5(filepath):
    with open(filepath,'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        hash = md5obj.hexdigest()
        return hash

#大文件的临界值
LIMIT_HUGE_SIZE = 1024*1024*1024

def get_file_md5(file_path):

    global LIMIT_HUGE_SIZE

    file_size = os.path.getsize(file_path)
    if file_size > LIMIT_HUGE_SIZE:
        return get_huge_file_md5(file_path)

    return get_normal_file_md5(file_path)