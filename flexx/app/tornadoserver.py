"""
Serve web page and handle web sockets. Uses Tornado, though this
can be generalized.
"""

import time
import logging
import urllib
import traceback
# from concurrent.futures import ThreadPoolExecutor

import tornado.web
import tornado.ioloop
import tornado.websocket
from tornado import gen

from .session import manager
from .assetstore import assets

# todo: threading, or even multi-process
#executor = ThreadPoolExecutor(4)


class AbstractServer:
    """ This is an attempt to generalize the server, so that in the
    future we may have e.g. a Pyramid server.
    
    A server must implement this, and use the manager to instantiate,
    connect and disconnect proxies. The assets object must be used to
    server assets to the client.
    """
    
    def open(self, host, port):
        """ Open the connection as a host. If port is None, auto-select one. """
        raise NotImplementedError()
    
    def start(self):
        """ Start the event loop. """
        raise NotImplementedError()
    
    def stop(self):
        """ Stop the event loop. """
        raise NotImplementedError()
    
    def call_later(self, delay, callback, *args, **kwargs):
        """ Call a function in a later event loop iteration. """
        raise NotImplementedError()


class TornadoServer(AbstractServer):
    """ Flexx Server implemented in Tornado.
    """
    
    def __init__(self):
        self._app = None
        self._loop = tornado.ioloop.IOLoop.instance()
    
    def open(self, host, port):
        
        # Check that its not already running
        if self._app is not None:
            # return
            raise RuntimeError('flexx server is already hosting.')
        
        # Create server
        self._app = tornado.web.Application([(r"/(.*)/ws", WSHandler), 
                                             (r"/(.*)", MainHandler), ])
        
        # Start server (find free port number if port not given)
        if port is not None:
            port = int(port)
            self._app.listen(port, host)
        else:
            for i in range(100):
                port = port_hash('flexx%i' % i)
                try:
                    self._app.listen(port, host)
                    break
                except OSError:
                    pass  # address already in use
            else:
                raise RuntimeError('Could not bind to free address')    
        
        # Notify address, so its easy to e.g. copy and paste in the browser
        self.serving_at = self._app.serving_at = host, port
        print('Serving apps at http://%s:%i/' % (host, port))
    
    def start(self):
        if not getattr(self._loop, '_running', False):
            self._loop.start()
    
    def stop(self):
        self._loop.stop()
    
    def call_later(self, delay, callback, *args, **kwargs):
        if delay <= 0:
            self._loop.add_callback(callback, *args, **kwargs)
        else:
            self._loop.add_timeout(self._loop.time() + delay, callback, *args, **kwargs)
            #self._loop.call_later(delay, callback, *args, **kwargs)  # v4.0+

# Create server instance
server = TornadoServer()


def port_hash(name):
    """ Given a string, returns a port number between 49152 and 65535
    
    This range (of 2**14 posibilities) is the range for dynamic and/or
    private ports (ephemeral ports) specified by iana.org. The algorithm
    is deterministic.
    """
    fac = 0xd2d84a61
    val = 0
    for c in name:
        val += (val >> 3) + (ord(c) * fac)
    val += (val >> 3) + (len(name) * fac)
    return 49152 + (val % 2**14)


class MainHandler(tornado.web.RequestHandler):
    """ Handler for http requests: serve pages
    """
    def initialize(self, **kwargs):
        # kwargs == dict set as third arg in url spec
        # print('init request')
        pass
    
    @gen.coroutine
    def get(self, path=None):
        
        # Analyze path to derive components
        # app_name - class name of the app, must be a valid identifier
        # file_name - path (can have slashes) to a file
        parts = [p for p in path.split('/') if p]
        if parts and parts[0].isidentifier():
            app_name, file_name = parts[0], '/'.join(parts[1:])
        else:
            app_name, file_name = None, '/'.join(parts)
        
        # Session id (if any) is provided via "?session_id=X"
        session_id = self.get_argument('session_id', None)
        
        if not path:
            # Not a path, index / home page
            # todo: allow __index__ app
            all_apps = ['<a href="%s">%s</a>' % (name, name) for name in 
                        manager.get_app_names()]
            all_apps = ', '.join(all_apps)
            self.write('Root selected, apps available: %s' % all_apps)
        
        elif app_name:
            # App name given. But is it the app, or a resource for it?
            
            if not file_name:
                # This looks like an app, redirect, serve app, or error
                if '/' not in path:
                    self.redirect('/%s/' % app_name)
                elif session_id:
                    # If session_id matches a pending app, use that session
                    session = manager.get_session_by_id(app_name, session_id)
                    if session and session.status == session.STATUS.PENDING:
                        self.write(session.get_page().encode())
                    else:
                        self.redirect('/%s/' % app_name)  # redirect for normal serve
                elif manager.has_app_name(app_name):
                    # Create session - client will connect to it via session_id
                    session = manager.create_session(app_name)
                    self.write(session.get_page().encode())
                else:
                    self.write('No app %r is currently hosted.' % app_name)
            elif file_name:
                # A resource, e.g. js/css/icon
                if file_name.endswith('.css'):
                    self.set_header("Content-Type", 'text/css')
                elif file_name.endswith('.js'):
                    self.set_header("Content-Type", 'application/x-javascript')
                try:
                    res = assets.load_asset(file_name)
                except (IOError, IndexError):
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
    
    def open(self, path=None):
        """ Called when a new connection is made.
        """
        if not hasattr(self, 'close_code'):  # old version of Tornado?
            self.close_code, self.close_reason = None, None
        
        self._session = None
        
        # Don't collect messages to send them more efficiently, just send asap
        self.set_nodelay(True)
        
        if isinstance(path, bytes):
            path = path.decode()
        self.app_name = path.strip('/')
        
        print('new ws connection', path)
        if manager.has_app_name(self.app_name):
            if tornado.version_info < (4, ):
                tornado.ioloop.IOLoop.current().add_callback(self.pinger)
            else:
                tornado.ioloop.IOLoop.current().spawn_callback(self.pinger)
        else:
            self.close(1003, "Could not associate socket with an app.")
    
    # todo: @gen.coroutine?
    def on_message(self, message):
        """ Called when a new message is received from JS.
        
        We now have a very basic protocol for receiving messages,
        we should at some point define a real formalized protocol.
        """
        self._pongtime = time.time()
        if self._session is None:
            if message.startswith('hiflexx '):
                session_id = message.split(' ', 1)[1].strip()
                try:
                    self._session = manager.connect_client(self, self.app_name,
                                                           session_id)
                except Exception as err:
                    self.close(1003, "Could not launch app: %r" % err)
                    raise
                self.write_message("PRINT Flexx server says hi", binary=True)
        else:
            self._session._receive_command(message)
    
    def on_close(self):
        """ Called when the connection is closed.
        """
        self.close_code = code = self.close_code or 0
        reason = self.close_reason or self.known_reasons.get(code, '')
        print('detected close: %s (%i)' % (reason, code))
        if self._session is not None:
            manager.disconnect_client(self._session)
            self._session = None  # Allow cleaning up
    
    @gen.coroutine
    def pinger(self):
        """ Check for timeouts. This helps remove lingering false connections.
        """
        self._pongtime = time.time()
        while self.close_code is None:
            self.ping(b'x')
            yield gen.sleep(2)
            if time.time() - self._pongtime > 20:
                self.close(1000, 'Conection timed out (no pong).')
                return
    
    def on_pong(self, data):
        """ Called when our ping is returned.
        """
        logging.debug('pong')
        self._pongtime = time.time()
    
    # --- methods
    
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
        """ Handle cross-domain access; override default same origin policy.
        """
        host, port = self.application.serving_at  # set by us
        incoming_host = urllib.parse.urlparse(origin).hostname
        if host == 'localhost':
            return True  # Safe
        elif host == '0.0.0.0':
            return True  # we cannot know if the origin matches
        elif host == incoming_host:
            return True
        else:
            print('Connection refused from %s' % origin)
            return False
