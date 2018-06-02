
from bz2 import BZ2File
import os

if __name__ == "__main__":
    inpath = "PythonFile.tar.bz2"
    with BZ2File(inpath,"r") as f:
        #for i in xrange(3):
        for i,line in enumerate(f):
            if i == 0:
                continue
            print i,line,"========="
