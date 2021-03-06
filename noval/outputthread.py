# -*- coding: utf-8 -*-
import threading

class OutputThread(threading.Thread):
    
    def __init__(self,stdout,process,output_ctrl,call_after = False):
        threading.Thread.__init__(self)
        self._stdout = stdout
        self._process = process
        self._output_ctrl = output_ctrl
        self._is_running = False
        self._call_after = call_after
        
    def run(self):
        while True:
            self._is_running = True
            out = self._stdout.readline()
            if out == b'':
                if self._process.poll() is not None:
                    self._is_running = False
                    break
            else:
                self.Callback(out)
                    

    def Callback(self,out):
        if not self._call_after:
            self._output_ctrl.call_back(out)
        else:
            self._output_ctrl.after(100,self._output_ctrl.call_back,out)
                    
    @property
    def IsRunning(self):
        return self._is_running
            
class SynchronizeOutputThread(OutputThread):
    '''
        同步实时读取进程的输出
    '''
    def run(self):
        temp = b''
        while True:
            self._is_running = True
            out = self._stdout.read(1)
            if out == b'':
                if self._process.poll() is not None:
                    self._is_running = False
                    self.Callback(temp)
                    break
            #换行输出
            elif out == b'\r' or out == b'\n':
                self.Callback(temp)
                temp = b''
            else:
                temp += out