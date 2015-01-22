""" Definition of application class
"""

import tornado.ioloop
import tornado.web

from .serve import TornadoApplication

from zoof.webruntime import launch


def port_hash(name):
    """ port_hash(name)
    
    Given a string, returns a port number between 49152 and 65535. 
    (2**14 (16384) different posibilities)
    This range is the range for dynamic and/or private ports 
    (ephemeral ports) specified by iana.org.
    The algorithm is deterministic, thus providing a way to map names
    to port numbers.
    
    """
    fac = 0xd2d84a61
    val = 0
    for c in name:
        val += ( val>>3 ) + ( ord(c)*fac )
    val += (val>>3) + (len(name)*fac)
    return 49152 + (val % 2**14)


class App(object):
    
    def __init__(self, runtime='xul'):
        # todo: singleton?
        self._ioloop = tornado.ioloop.IOLoop.instance()
        
        self._tornado_app = TornadoApplication()
        
        # Set host. localhost is safer
        host = 'localhost'  # or other host name or known ip address.
        
        # Find free port number
        for i in range(100):
            port = port_hash('zoof+%i' % i)
            try:
                self._tornado_app.listen(port, host)
                break
            except OSError:
                pass  # address already in use
        else:
            raise RuntimeError('Could not bind to free address')    
        
        self._tornado_app.zoof_port = port
        self._runtime = launch('http://localhost:%i' % port, runtime)
    
    def eval(self, code):
        self._tornado_app.write_message('EVAL ' + code)
    
    def start(self):  # todo: or run()?
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
            self._ioloop.call_later(delay, callback, *args, **kwargs)



class NativeElement(object):
    
    def __init__(self, id):
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        # ... get __dir__ from JS and allow live inspection of DOM elements
        # That would be great for debugging ...


class Widget(object):
    _counter = 0
    pass

class Label(Widget):
    pass

class Button(Widget):
    _TEMPLATE = """
        var e = document.createElement("button");
        e.id = '{id}';
        e.innerHTML = '{text}'
        document.body.appendChild(e);
        """
    
    def __init__(self, parent, text='Click me'):
        Widget._counter += 1
        self._parent = parent
        self._id = 'but%i' % Widget._counter
        parent.eval(self._TEMPLATE.format(id=self._id, text=text))
    
    def set_text(self, text):
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        self._parent.eval(t.format(id=self._id, text=text))


class Window(object):
    
    __slots__ = ['_title']
    
    def set_title(self, title):
        pass
        # todo: properties or functions?
