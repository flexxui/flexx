from __future__ import print_function, division, absolute_import

import sys

# Other dialog ideas: get_int, get_float, get_item, get_text, progress.


class BaseApp(object):
    """ The base app class. Acts as a placeholder to define the API
    that subclasses must implement.
    """
    
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


class StubApp(BaseApp):
    """ A stub application class for platforms that we do not support.
    It always fails.
    """
    
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
