""" flexx.ui client serving a web page using Tornado.
"""

import sys
import os
import logging
import urllib
import traceback

import tornado.web
import tornado.websocket

from ...webruntime.common import default_icon

from .app import manager, call_later
from .clientcode import clientCode

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
HTML_DIR = os.path.join(os.path.dirname(THIS_DIR), 'html')


def _flexx_run_callback(self, callback, *args, **kwargs):
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
        
        if not hasattr(WebSocketProtocol, 'async_callback'):
            WebSocketProtocol._orig_run_callback = WebSocketProtocol._run_callback
            WebSocketProtocol._run_callback = _flexx_run_callback
        else:
            WebSocketProtocol._orig_run_callback = WebSocketProtocol.async_callback
            WebSocketProtocol.async_callback = _flexx_run_callback


_patch_tornado()


class FlexxTornadoApplication(tornado.web.Application):
    """ Simple subclass of tornado Application.
    
    Has functionality for serving our html/css/js files, and caching them.
    """
    def __init__(self):
        tornado.web.Application.__init__(self, 
            [(r"/(.*)/ws", WSHandler), (r"/(.*)", MainHandler), ])
        self._cache = {}
    
    # def load(self, fname):
    #     """ Load a file with the given name. Returns bytes.
    #     """
    #     if fname not in self._cache:
    #         filename = os.path.join(HTML_DIR, fname)
    #         blob = open(filename, 'rb').read()
    #         return blob  # todo: bypasse cache
    #         self._cache[fname] = blob
    #     return self._cache[fname]


class MainHandler(tornado.web.RequestHandler):
    """ Handler for http requests: serve pages
    """
    def initialize(self, **kwargs):
        # kwargs == dict set as third arg in url spec
        # print('init request')
        pass
    
    def get(self, path=None):
        print('get', path)
        
        # Analyze path to derive components
        # app_name - class name of the app, must be a valid identifier
        # app_id - optional id to associate connection to a specific instance
        # file_name - path (can have slashes) to a file
        parts = [p for p in path.split('/') if p]
        if parts and parts[0].split('-')[0].isidentifier():
            app_name, _, app_id = parts[0].partition('-')
            file_name = '/'.join(parts[1:])
        else:
            app_name, app_id = None, None
            file_name = '/'.join(parts)
        
        # todo: maybe when app_id is given, redirect to normal name, but
        # modify flexx.app_id in index.html, so that the websocket can connect
        # with id ... (mmm also not very nice)
        
        if not path:
            # Not a path, index / home page
            all_apps = ['<a href="%s">%s</a>' % (name, name) for name in 
                        manager.get_app_names()]
            all_apps = ', '.join(all_apps)
            self.write('Root selected, apps available: %s' % all_apps)
        
        elif app_name:
            # App name given. But is it the app, or a resource for it?
            
            if not file_name:
                # This looks like an app, redirect, serve app, or error
                if not '/' in path:
                    self.redirect('/%s/' % app_name)
                elif app_id:
                    proxy = manager.get_proxy_by_id(app_name, app_id)
                    if proxy:
                        self.write(clientCode.get_page().encode())
                    else:
                        self.write('App %r with id %r is not available' % 
                                   (app_name, app_id))
                elif manager.has_app_name(app_name):
                    #self.write(self.application.load('index.html'))
                    #self.serve_index()
                    self.write(clientCode.get_page().encode())
                else:
                    self.write('No app %r is hosted right now' % app_name)
            elif file_name.endswith('.ico'):
                # Icon, look it up from the app instance
                id = file_name.split('.')[0]
                if manager.has_app_name(app_name):
                    client = manager.get_proxy_by_id(app_name, id)
                    # todo: serve icon stored on app widget
                    #if app:
                    #    self.write(app._config.icon.to_bytes())
            elif file_name:
                # A resource, e.g. js/css/icon
                if file_name.endswith('.css'):
                    self.set_header("Content-Type", 'text/css')
                elif file_name.endswith('.js'):
                    self.set_header("Content-Type", 'application/x-javascript')
                try:
                    #raise RuntimeError('This is for page_light, but we might never implement that')
                    #res = self.application.load(file_name)
                    res = clientCode.load(file_name).encode()
                except IOError:
                    #self.write('invalid resource')
                    super().write_error(404)
                else:
                    self.write(res)
        
        elif file_name:
            # filename in root. We don't support that yet
            self.write('Invalid file % r' % file_name)
        
        else:
            # In theory this cannot happen
            self.write('This should not happen')
    
    # def serve_index(self):
    #     src = self.application.load('index.html')
    #     from .mirrored import get_mirrored_classes
    #     js = '\n'
    #     for cls in get_mirrored_classes():
    #         js += '\n' + cls.get_js()
    #     src = src.replace(b'JS_INSERT_HERE', js.encode())
    #     self.write(src)
    
    def write_error(self, status_code, **kwargs):
        if status_code == 404:  # does not work?
            self.write('flexx.ui wants you to connect to root (404)')
        else:
            msg = 'Flexx.ui encountered an error: <br /><br />'
            try:  # try providing a useful message; tough luck if this fails
                type, value, tb = kwargs['exc_info']
                tb_str = ''.join(traceback.format_tb(tb))
                msg += '<pre>%s\n%s</pre>' % (tb_str, str(value))
            except Exception:
                pass
            self.write(msg)
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
        if not hasattr(self, 'close_code'):  # old version of Tornado?
            self.close_code, self.close_reason = None, None
        
        # Don't collect messages to send them more efficiently, just send asap
        self.set_nodelay(True)
        if isinstance(path, bytes):
            path = path.decode()
        print('new ws connection', path)
        app_name, _, app_id = path.strip('/').partition('-')
        if manager.has_app_name(app_name):
            try:
                self._proxy = manager.connect_client(self, app_name, app_id)
            except Exception as err:
                self.close(1003, "Could not launch app: %r" % err)
                raise
            self.write_message("PRINT Hello World from server", binary=True)
        else:
            self.close(1003, "Could not associate socket with an app.")
    
    def on_message(self, message):
        """ Called when a new message is received from JS.
        
        We now have a very basic protocol for receiving messages,
        we should at some point define a real formalized protocol.
        """
        self._proxy._receive_command(message)
 
    def on_close(self):
        """ Called when the connection is closed.
        """
        self.close_code = code = self.close_code or 0
        reason = self.close_reason or self.known_reasons.get(code, '')
        print('detected close: %s (%i)' % (reason, code))
        if hasattr(self, '_proxy'):
            manager.disconnect_client(self._proxy)
            self._proxy = None  # Allow cleaning up
    
    def on_pong(self, data):
        """ Called when our ping is returned.
        """
        print('PONG', data)
    
    # --- methdos
    
    def command(self, cmd):
        self.write_message(cmd, binary=True)
    
    def close(self, *args):
        try:
            tornado.websocket.WebSocketHandler.close(self, *args)
        except TypeError:
            tornado.websocket.WebSocketHandler.close(self)  # older Tornado
    
    def close_this(self):
        """ Call this to close the websocket
        """
        self.close(1000, 'closed by server')
    
    def check_origin(self, origin):
        """ Handle cross-domain access; override default same origin
        policy. By default the hostname and port must be equal. We only
        requirde de portname to be equal. This allows us to embed in
        the IPython notebook.
        """
        host, port = self.application.serving_at  # set by us
        incoming_host = urllib.parse.urlparse(origin).hostname
        if host == incoming_host:
            return True
        else:
            print('Connection refused from %s' % origin)
            return False
