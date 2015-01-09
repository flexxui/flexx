""" Definition of application class
"""

import tornado.ioloop


class Application(object):
    
    def __init__(self):
        # todo: singleton?
        self._ioloop = tornado.ioloop.IOLoop.instance()
    
    def start(self):
        self._ioloop.start()
    
    def stop(self):
        self._ioloop.stop()
    
    def process_events(self):
        self._ioloop.run_sync(lambda x=None: None)
    
    def call_later(self, delay, callback, *args, **kwargs):
        """ Call the given callback after delay seconds. If delay is zero, 
        call in the next event loop iteration.
        """
        if delay <= 0:
            self._ioloop.add_callback(callback, *args, **kwargs)
        else:
            self._ioloop.call_later(delay * 1000, callback, *args, **kwargs)



class Widget(object):
    pass


class Button(Widget):
    pass


class Window(object):
    
    __slots__ = ['_title']
    
    def set_title(self, title):
        pass
        # todo: properties or functions?
