from __future__ import print_function, division, absolute_import

import sys


class BaseApp(object):
    
    def fail(self, title, message):
        raise NotImplementedError()
    
    def warn(self, title, message):
        raise NotImplementedError()
        
    def inform(self, title, message):
        raise NotImplementedError()
    
    def verify(self, title, message):
        raise NotImplementedError()
    
    def ask(self, title, message):
        raise NotImplementedError()
    
    # def get_int()
    # 
    # def get_float()
    # 
    # def get_choice()  # or question
    # 
    # def get_item()
    # 
    # def get_text()
    # 
    # def progress()
    # 

class StubApp(BaseApp):
    
    def _error(self, kind, title, message):
        t = 'Cannot show %s-dialog on platform %s.\n  %s: %s'
        raise RuntimeError(t % (kind, sys.platform, title, message))
    
    def fail(self, title, message):
        self._error('fail', title, message)
    
    def warn(self, title, message):
        self._error('warn', title, message)
        
    def inform(self, title, message):
        self._error('inform', title, message)
    
    def verify(self, title, message):
        self._error('verify', title, message)
    
    def ask(self, title, message):
        self._error('ask', title, message)
