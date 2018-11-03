import logging
import os

class LogCtrlHandler(logging.Handler):
    
    def __init__(self, log_view):
        logging.Handler.__init__(self)
        self._log_view = log_view
        
        self.setLevel(logging.DEBUG)
        self.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s"))
        
    def emit(self, record):
        level = record.levelno
        msg = self.format(record)
        self._log_view.AddLogger(record.name)
        self._log_view.AddLine(msg + os.linesep ,level)
        
    def ClearFilters(self):
        self.filters = []
        
    def addFilter(self, filter):
        self.ClearFilters()
        logging.Handler.addFilter(self,filter)
