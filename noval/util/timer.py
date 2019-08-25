import sched
import time

import threading

class PyTimer(threading.Thread):
    """description of class"""

    def __init__(self,call_func,*args):
        threading.Thread.__init__(self)
        self._call_func = call_func
        self.schedule = sched.scheduler ( time.time, time.sleep)
        self._args = args

    def run(self):
        self.schedule.run()

    def Start(self,interval):
        self.schd = self.schedule.enter(interval,0,self.WarpCallFunc,())
        self.start()
        
    def Stop(self):
        if self.schd in self.schedule.queue:
            self.schedule.cancel(self.schd)
        
    def WarpCallFunc(self):
        print ('callback func')
        self._call_func()