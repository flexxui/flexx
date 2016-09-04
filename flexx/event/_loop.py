"""
Implementation of basic event loop object. Can be integrated a real
event loop such as tornado or Qt.
"""

import sys

from . import logger

# todo: maybe this can be the base class for the tornado loop that we use in flexx.app

class Loop:
    """ A simple proxy event loop. There is one instance in 
    ``flexx.event.loop``. This is used by handlers to register the
    handling of pending events. Users typically don't need to be aware
    of this.
    
    This proxy can integrate with an existing event loop (e.g. of Qt
    and Tornado). If Qt or Tornado is imported at the time that
    ``flexx.event`` gets imported, the loop is integrated automatically.
    This object can also be used as a context manager; events get
    processed when the context exits.
    """
    
    def __init__(self):
        self._pending_calls = []
        self._calllaterfunc = lambda x: None
        self._scheduled_update = False
    
    def call_later(self, func):
        """ Call the given function in the next iteration of the event loop.
        """
        self._pending_calls.append(func)
        if not self._scheduled_update:
            self._scheduled_update = True
            self._calllaterfunc(self.iter)
    
    def iter(self):
        """ Do one event loop iteration; process all pending function calls.
        """
        self._scheduled_update = False
        while self._pending_calls:
            func = self._pending_calls.pop(0)
            try:
                func()
            except Exception as err:
                logger.exception(err)
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.iter()
    
    def integrate(self, call_later_func=None, raise_on_fail=True):
        """ Integrate with an existing event loop system.
        
        Params:
            call_later_func (func): a function that can be called to
                schedule the calling of a given function. If not given,
                will try to connect to Tornado or Qt event loop, but only
                if either library is already imported.
            raise_on_fail (bool): whether to raise an error when the
                integration could not be performed.
        """
        if call_later_func is not None:
            if callable(call_later_func):
                self._calllaterfunc = call_later_func
                self._calllaterfunc(self.iter)
            else:
                raise ValueError('call_later_func must be a function')
        elif 'tornado' in sys.modules:
            self.integrate_tornado()
        elif 'PyQt4.QtGui' in sys.modules:  # pragma: no cover
            self.integrate_pyqt4()
        elif 'PySide.QtGui' in sys.modules:  # pragma: no cover
            self.integrate_pyside()
        elif raise_on_fail:  # pragma: no cover
            raise RuntimeError('Could not integrate flexx.event loop')
    
    def integrate_tornado(self):
        """ Integrate with tornado.
        """
        import tornado.ioloop
        loop = tornado.ioloop.IOLoop.current()
        self._calllaterfunc = loop.add_callback
        self._calllaterfunc(self.iter)
        logger.debug('Flexx event loop integrated with Tornado')
    
    def integrate_pyqt4(self):  # pragma: no cover
        """ Integrate with PyQt4.
        """
        from PyQt4 import QtCore, QtGui
        self._integrate_qt(QtCore, QtGui)
        logger.debug('Flexx event loop integrated with PyQt4')
    
    def integrate_pyside(self):  # pragma: no cover
        """ Integrate with PySide.
        """
        from PySide import QtCore, QtGui
        self._integrate_qt(QtCore, QtGui)
        logger.debug('Flexx event loop integrated with PySide')
    
    def _integrate_qt(self, QtCore, QtGui):  # pragma: no cover
        from queue import Queue, Empty
        
        class _CallbackEventHandler(QtCore.QObject):
            
            def __init__(self):
                QtCore.QObject.__init__(self)
                self.queue = Queue()
            
            def customEvent(self, event):
                while True:
                    try:
                        callback, args = self.queue.get_nowait()
                    except Empty:
                        break
                    try:
                        callback(*args)
                    except Exception as why:
                        print('callback failed: {}:\n{}'.format(callback, why))
            
            def postEventWithCallback(self, callback, *args):
                self.queue.put((callback, args))
                QtGui.qApp.postEvent(self, QtCore.QEvent(QtCore.QEvent.User))
        
        _callbackEventHandler = _CallbackEventHandler()
        self._calllaterfunc = _callbackEventHandler.postEventWithCallback
        self._calllaterfunc(self.iter)


loop = Loop()
loop.integrate(None, False)
