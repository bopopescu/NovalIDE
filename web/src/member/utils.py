import os
import sys

def MakeDirs(dirname):
    dirname = os.path.abspath(dirname)
    dirname = dirname.replace("\\","/")
    dirnames = dirname.split("/")
    destdir = ""
    destdir = os.path.join(dirnames[0] + "/",dirnames[1])
    
    if not os.path.exists(destdir):
        os.mkdir(destdir)
        
    for name in dirnames[2:]:
        destdir=os.path.join(destdir,name)
        if not os.path.exists(destdir):
            os.mkdir(destdir)
    
def CalcVersionValue(ver_str="0.0.0"):
    """Calculates a version value from the provided dot-formated string

    1) SPECIFICATION: Version value calculation AA.BBB.CCC
         - major values: < 1     (i.e 0.0.85 = 0.850)
         - minor values: 1 - 999 (i.e 0.1.85 = 1.850)
         - micro values: >= 1000 (i.e 1.1.85 = 1001.850)

    @keyword ver_str: Version string to calculate value of

    """
    ver_str = ''.join([char for char in ver_str
                       if char.isdigit() or char == '.'])
    ver_lvl = ver_str.split(u".")
    if len(ver_lvl) < 3:
        return 0

    major = int(ver_lvl[0]) * 1000
    minor = int(ver_lvl[1])
    if len(ver_lvl[2]) <= 2:
        ver_lvl[2] += u'0'
    micro = float(ver_lvl[2]) / 1000
    return float(major) + float(minor) + micro
    
def CompareAppVersion(new_version,old_version):
    if CalcVersionValue(new_version) <= CalcVersionValue(old_version):
        return 0
    return 1