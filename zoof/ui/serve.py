""" zoof.gui client based serving a web page using tornado.
"""

import sys
import os
import logging

import tornado.web
import tornado.websocket

from ..webruntime.common import default_icon
from .app import manager, call_later

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

HTML_DIR = os.path.join(os.path.dirname(THIS_DIR), 'html')


def _zoof_run_callback(self, callback, *args, **kwargs):
    """ Patched version of Tornado's _run_callback that sets traceback
    info when an exception occurs, so that we can do PM debugging.
    """
    def _callback(*args, **kwargs):
        try:
            callback(*args, **kwargs)
        except Exception:
            type, value, tb = sys.exc_info()
            tb = tb.tb_next  # Skip *this* frame
            sys.last_type = type
            sys.last_value = value
            sys.last_traceback = tb
            del tb  # Get rid of it in this namespace
            raise
    return self._orig_run_callback(_callback, *args, **kwargs)


def _patch_tornado():
    WebSocketProtocol = tornado.websocket.WebSocketProtocol
    if not hasattr(WebSocketProtocol, '_orig_run_callback'):
        WebSocketProtocol._orig_run_callback = WebSocketProtocol._run_callback
        WebSocketProtocol._run_callback = _zoof_run_callback


_patch_tornado()


class ZoofTornadoApplication(tornado.web.Application):
    """ Simple subclass of tornado Application.
    
    Has functionality for serving our html/css/js files, and caching them.
    """
    def __init__(self):
        tornado.web.Application.__init__(self, 
            [(r"/(.*)/ws", WSHandler), (r"/(.*)", MainHandler), ])
        self._cache = {}
    
    def load(self, fname):
        """ Load a file with the given name. Returns bytes.
        """
        if fname not in self._cache:
            filename = os.path.join(HTML_DIR, fname)
            blob = open(filename, 'rb').read()
            return blob  # todo: bypasse cache
            self._cache[fname] = blob
        return self._cache[fname]


class MainHandler(tornado.web.RequestHandler):
    """ Handler for http requests: serve pages
    """
    def initialize(self, **kwargs):
        # kwargs == dict set as third arg in url spec
        # print('init request')
        pass
    
    def get(self, path=None):
        print('get', path)
        app_name = path.rstrip('/')
        app_name = app_name if app_name.isidentifier() else None
        
        if not path:
            # Not a path, index / home page
            self.write('Root selected, apps available: %r' % 
                       manager.get_app_names())
        elif app_name:
            # This looks like an app, redirect, serve app, or error
            if not '/' in path:
                self.redirect('/%s/' % app_name)
            elif manager.has_app_name(app_name):
                self.write(self.application.load('index.html'))
            else:
                self.write('No app %r is being hosted right now' % app_name)
        elif path.endswith('.ico') and '/' in path:
            # Icon, look it up from the app instance
            app_name, filename = path.split('/', 1)
            id = filename.split('.')[0]
            if manager.has_app_name(app_name):
                app = manager.get_app_by_id(app_name, id)
                if app:
                    self.write(app._config.icon.to_bytes())
        else:
            # Another resource, e.g. js/css/icon
            app_name, filename = path.split('/', 1)
            if path.endswith('.css'):
                self.set_header("Content-Type", 'text/css')
            try:
                res = self.application.load(filename)
            except IOError:
                #self.write('invalid resource')
                super().write_error(404)
            else:
                self.write(res)
    
    def write_error(self, status_code, **kwargs):
        # does not work?
        print('in write_error', repr(status_code))
        if status_code == 404:
            self.write('zoof.gui wants you to connect to root (404)')
        else:
            self.write('Zoof ui encountered an error: <br /><br />')
            super().write_error(status_code, **kwargs)
    
    def on_finish(self):
        pass  # print('finish request')


class WSHandler(tornado.websocket.WebSocketHandler):
    """ Handler for websocket.
    """
    
    # https://tools.ietf.org/html/rfc6455#section-7.4.1
    known_reasons = {1000: 'client done', 
                     1001: 'client closed', 
                     1002: 'protocol error', 
                     1003: 'could not accept data',
                     }
    
    # --- callbacks
    
    # todo: use ping() and close()
    def open(self, path=None):
        """ Called when a new connection is made.
        """
        # Don't collect messages to send them more efficiently, just send asap
        self.set_nodelay(True)
        
        print('new ws connection', path)
        app_name = path.strip('/')
        if manager.has_app_name(app_name):
            app = manager.connect_an_app(app_name, self)
            self.write_message("Hello World", binary=True)
        else:
            self.close(1003, "Could not associate socket with an app.")
    
    def on_message(self, message):
        """ Called when a new message is received from JS.
        
        We now have a very basic protocol for receiving messages,
        we should at some point define a real formalized protocol.
        """
        if message.startswith('RET '):
            print(message[4:])  # Return value
        elif message.startswith('ERROR '):
            logging.error('JS - ' + message[6:].strip())
        elif message.startswith('WARN '):
            logging.warn('JS - ' + message[5:].strip())
        elif message.startswith('INFO '):
            logging.info('JS - ' + message[5:].strip())
        else:
            print('message received %s' % message)
            self.write_message('echo ' + message, binary=True)
 
    def on_close(self):
        """ Called when the connection is closed.
        """
        code = self.close_code or 0
        reason = self.close_reason or self.known_reasons.get(code, '')
        print('detected close: %s (%i)' % (reason, code))
    
    def on_pong(self, data):
        """ Called when our ping is returned.
        """
        print('PONG', data)
    
    # --- methdos
    
    def command(self, cmd):
        self.write_message(cmd, binary=True)
    
    def close_this(self):
        """ Call this to close the websocket
        """
        self.close(1000, 'closed by server')
    
    # Uncomment this to allow cross-domain access
    #def check_origin(self, origin):
    #    return True
