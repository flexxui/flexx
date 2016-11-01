"""
Serve web page and handle web sockets. Uses Tornado, though this
can be generalized.
"""

import json
import time
import socket
import traceback
import threading
from urllib.parse import urlparse
# from concurrent.futures import ThreadPoolExecutor

import tornado.web
import tornado.websocket
import tornado.httpserver
from tornado.ioloop import IOLoop
from tornado import gen
from tornado import netutil

from .session import manager, valid_app_name
from .assetstore import assets
from . import logger
from .. import config


if tornado.version_info < (4, ):
    raise RuntimeError('Flexx requires Tornado v4.0 or higher.')

# todo: threading, or even multi-process
#executor = ThreadPoolExecutor(4)

# Use a binary websocket or not?
BINARY = False


def is_main_thread():
    """ Get whether this is the main thread. """
    return isinstance(threading.current_thread(), threading._MainThread)


class AbstractServer:
    """ This is an attempt to generalize the server, so that in the
    future we may have e.g. a Flask or Pyramid server.
    
    A server must implement this, and use the manager to instantiate,
    connect and disconnect sessions. The assets object must be used to
    server assets to the client.
    
    Arguments:
        host (str): the hostname to serve at
        port (int): the port to serve at. None or 0 mean to autoselect a port.
    """
    
    def __init__(self, host, port):
        self._open(host, port)
        # Check that subclass set private variables
        assert self._serving
        self._running = False
    
    def start(self):
        """ Start the event loop. """
        if not self._serving:
            raise RuntimeError('Cannot start a closed server!')
        if self._running:
            raise RuntimeError('Cannot start a running server.')
        self._running = True
        try:
            self._start()
        finally:
            self._running = False
    
    def stop(self):
        """ Stop the event loop. This does not close the connection; the server
        can be restarted. Thread safe. """
        self.call_later(0, self._stop)
    
    def close(self):
        """ Close the connection. A closed server cannot be used again. """
        if self._running:
            raise RuntimeError('Cannot close a running server; need to stop first.')
        self._serving = None
        self._close()
    
    def _open(self, host, port):
        raise NotImplementedError()
    
    def _start(self):
        raise NotImplementedError()
    
    def _stop(self):
        raise NotImplementedError()
    
    def _close(self):
        raise NotImplementedError()
    
    # This method must be implemented directly for performance (its used a lot)
    def call_later(self, delay, callback, *args, **kwargs):
        """ Call a function in a later event loop iteration. """
        raise NotImplementedError()
    
    @property
    def serving(self):
        """ Get a tuple (hostname, port) that is being served. """
        return self._serving


class TornadoServer(AbstractServer):
    """ Flexx Server implemented in Tornado.
    """
    
    def __init__(self, host, port, new_loop):
        self._new_loop = new_loop
        super().__init__(host, port)
    
    def _open(self, host, port):
        
        # Get a new ioloop or the current ioloop for this thread
        if self._new_loop:
            self._loop = IOLoop()
        else:
            self._loop = IOLoop.current(instance=is_main_thread())
            if self._loop is None:
                self._loop = IOLoop(make_current=True)
        
        # Create tornado application
        self._app = tornado.web.Application([(r"/(.*)/ws", WSHandler), 
                                             (r"/(.*)", MainHandler), ])
        # Create tornado server, bound to our own ioloop
        self._server = tornado.httpserver.HTTPServer(self._app, io_loop=self._loop)
        
        # Start server (find free port number if port not given)
        if port:
            # Turn port into int, use hashed port number if a string was given
            try:
                port = int(port)
            except ValueError:
                port = port_hash(port)
            self._server.listen(port, host)
        else:
            # Try N ports in a repeatable range (easier, browser history, etc.)
            prefered_port = port_hash('Flexx')
            for i in range(8):
                port = prefered_port + i
                try:
                    self._server.listen(port, host)
                    break
                except OSError:
                    pass  # address already in use
            else:
                # Ok, let Tornado figure out a port
                [sock] = netutil.bind_sockets(None, host, family=socket.AF_INET)
                self._server.add_sockets([sock])
                port = sock.getsockname()[1]
        
        # Notify address, so its easy to e.g. copy and paste in the browser
        self._serving = self._app._flexx_serving = host, port
        logger.info('Serving apps at http://%s:%i/' % (host, port))
    
    def _start(self):
        # Ensure that our loop is the current loop for this thread
        if self._new_loop:
            self._loop.make_current()
        elif IOLoop.current(instance=is_main_thread()) is not self._loop:
            raise RuntimeError('Server must use ioloop that is current to this thread.')
        # Make use of the semi-standard defined by IPython to determine
        # if the ioloop is "hijacked" (e.g. in Pyzo). There is no public
        # way to determine if a loop is already running, but the
        # AbstractServer class keeps track of this.
        if not getattr(self._loop, '_in_event_loop', False):
            self._loop.start()
    
    def _stop(self):
        # todo: explicitly close all websocket connections
        logger.debug('Stopping Tornado server')
        self._loop.stop()
    
    def _close(self):
        self._server.stop()
    
    def call_later(self, delay, callback, *args, **kwargs):
        # We use a wrapper func so that exceptions are processed via our
        # logging system. Also fixes that Tornado seems to close websockets
        # when an exception occurs (issue #164) though one could also
        # use ``with tornado.stack_context.NullContext()`` to make callbacks
        # be called more "independently".
        def wrapper():
            try:
                callback(*args, **kwargs)
            except Exception as err:
                err.skip_tb = 1
                logger.exception(err)
        
        if delay <= 0:
            self._loop.add_callback(wrapper)
        else:
            self._loop.call_later(delay, wrapper)
    
    @property
    def app(self):
        """ The Tornado Application object being used."""
        return self._app
    
    @property
    def loop(self):
        """ The Tornado IOLoop object being used."""
        return self._loop
    
    @property
    def server(self):
        """ The Tornado HttpServer object being used."""
        return self._server


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
        pass
    
    @gen.coroutine
    def get(self, path=None):
        
        logger.debug('Incoming request at %s' % path)
        
        # Analyze path to derive components
        # app_name - name of the app, must be a valid identifier
        # file_name - path (can have slashes) to a file
        parts = [p for p in path.split('/') if p]
        if parts and valid_app_name(parts[0]):
            app_name, file_name = parts[0], '/'.join(parts[1:])
        else:
            app_name = '__main__' if manager.has_app_name('__main__') else '__index__'
            file_name = '/'.join(parts)
        
        # Session id (if any) is provided via "?session_id=X"
        session_id = self.get_argument('session_id', None)
        
        # Redirect to fixed app name?
        correct_app_name = manager.has_app_name(app_name)
        if correct_app_name and app_name in path and ('/' not in path or
                                                      correct_app_name != app_name):
            self.redirect('/%s/%s' % (correct_app_name, file_name))
        
        elif app_name == '__index__':
            # Show plain index page
            all_apps = ['<li><a href="%s/">%s</a></li>' % (name, name) for name in 
                        manager.get_app_names()]
            the_list = '<ul>%s</ul>' % ''.join(all_apps) if all_apps else 'no apps'
            self.write('Index of available apps: ' + the_list)
        
        elif app_name == '__cmd__':
            # Control the server using http, but only from localhost
            if not self.request.host.startswith('localhost:'):
                self.write('403')
                return
            
            if file_name == 'info':
                info = dict(address=self.application._flexx_serving,
                            app_names=manager.get_app_names(),
                            nsessions=sum([len(manager.get_connections(x))
                                           for x in manager.get_app_names()]),
                            )
                self.write(json.dumps(info))
            elif file_name == 'stop':
                loop = IOLoop.current()
                loop.add_callback(loop.stop)
            else:
                self.write('unknown command')
        
        elif correct_app_name:
            # App name given. But is it the app, or a resource for it?
            
            # idea: if file_name.startswith('api/foo/bar') -> send foo/bar to app
            
            if not file_name:
                # This looks like an app, redirect, serve app, or error
                if session_id:
                    # If session_id matches a pending app, use that session
                    session = manager.get_session_by_id(app_name, session_id)
                    if session and session.status == session.STATUS.PENDING:
                        self.write(session.get_page().encode())
                    else:
                        self.redirect('/%s/' % app_name)  # redirect for normal serve
                else:
                    # Create session - client will connect to it via session_id
                    session = manager.create_session(app_name)
                    self.write(session.get_page().encode())
            elif file_name and ('.js:' in file_name or file_name.startswith(':')):
                # Request for a view of a JS source file at a certain line, redirect
                fname, where = file_name.split(':')[:2]
                self.redirect('/%s/%s.debug%s#L%s' %
                              (app_name, fname.replace('/:', ':'), where, where))
            elif file_name and '.debug' in file_name:
                # Show JS source file at a certain line
                fname, lineno = file_name.split('.debug', 1)
                if not fname:  # root app
                    session = manager.create_session(app_name)
                    res = session.get_page().encode()
                    session.close()
                else:
                    res = assets.get_asset(fname)
                    if res is not None:
                        res = res.to_string()
                    else:
                        self.write('Asset %r unavailable\n' % fname)
                        return
                # Build HTML page
                lines = ['<html><head><style>%s</style></head><body>' % 
                            "pre {display:inline} #L%s {background:#cca;}" % lineno]
                for i, line in enumerate(res.splitlines()):
                    table = {ord('&'): '&amp;', ord('<'): '&lt;', ord('>'): '&gt;'}
                    line = line.translate(table).replace('\t', '    ')
                    lines.append('<a id="L%i">%i<pre>  %s</pre></a><br />' %
                                    (i+1, i+1, line))
                lines.append('</body></html>')
                self.write('\n'.join(lines))
            elif file_name:
                # A resource, e.g. js/css/icon
                if file_name.endswith('.css'):
                    self.set_header("Content-Type", 'text/css')
                elif file_name.endswith('.js'):
                    self.set_header("Content-Type", 'application/x-javascript')
                res = assets.get_asset(file_name)
                if res is not None:
                    self.write(res.to_string())
                else:
                    self.write('Could not load asset %r' % file_name)
        
        elif file_name:
            # filename in root. We don't support anything like that
            self.write('Flexx only provides files relative to an app (%r)' % file_name)
        
        else:
            # In theory this cannot happen
            self.write('No app "%s" is currently hosted.' % app_name)
    
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
        pass



class MessageCounter:
    """ Simple class to count incoming messages and periodically log
    the number of messages per second.
    """
    
    def __init__(self):
        self._collect_interval = 0.2  # period over which to collect messages
        self._notify_interval = 3.0  # period on which to log the mps
        self._window_interval = 4.0  # size of sliding window
        
        self._mps = [(time.time(), 0)]  # tuples of (time, count)
        self._collect_count = 0
        self._collect_stoptime = 0
        
        self._stop = False
        self._notify()
    
    def trigger(self):
        t = time.time()
        if t < self._collect_stoptime:
            self._collect_count += 1
        else:
            self._mps.append((self._collect_stoptime, self._collect_count))
            self._collect_count = 1
            self._collect_stoptime = t + self._collect_interval
    
    def _notify(self):
        mintime = time.time() - self._window_interval
        self._mps = [x for x in self._mps if x[0] > mintime]
        if self._mps:
            n = sum([x[1] for x in self._mps])
            T = self._mps[-1][0] - self._mps[0][0] + self._collect_interval
        else:
            n, T = 0, self._collect_interval
        logger.debug('Websocket messages per second: %1.1f' % (n / T))
        
        if not self._stop:
            loop = IOLoop.current()
            loop.call_later(self._notify_interval, self._notify)
    
    def stop(self):
        self._stop = True


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
        self._mps_counter = MessageCounter()
        
        # Don't collect messages to send them more efficiently, just send asap
        # self.set_nodelay(True)
        
        if isinstance(path, bytes):
            path = path.decode()
        self.app_name = path.strip('/')
        
        logger.debug('New websocket connection %s' % path)
        if manager.has_app_name(self.app_name):
            IOLoop.current().spawn_callback(self.pinger1)
            IOLoop.current().spawn_callback(self.pinger2)
        else:
            self.close(1003, "Could not associate socket with an app.")
    
    # todo: @gen.coroutine?
    def on_message(self, message):
        """ Called when a new message is received from JS.
        
        This handles one message per event loop iteration.
        
        We now have a very basic protocol for receiving messages,
        we should at some point define a real formalized protocol.
        """
        self._mps_counter.trigger()
        
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
                self.write_message("PRINT Flexx server says hi", binary=BINARY)
        elif message.startswith('PONG '):
            self.on_pong2(message[5:])
        else:
            try:
                self._session._receive_command(message)
            except Exception as err:
                err.skip_tb = 1
                logger.exception(err)
    
    def on_close(self):
        """ Called when the connection is closed.
        """
        self.close_code = code = self.close_code or 0
        reason = self.close_reason or self.known_reasons.get(code, '')
        logger.debug('Websocket closed: %s (%i)' % (reason, code))
        self._mps_counter.stop()
        if self._session is not None:
            manager.disconnect_client(self._session)
            self._session = None  # Allow cleaning up
    
    @gen.coroutine
    def pinger1(self):
        """ Check for timeouts. This helps remove lingering false connections.
        
        This uses the websocket's native ping-ping mechanism. On the
        browser side, pongs work even if JS is busy. On the Python side
        we perform a check whether we were really waiting or whether Python 
        was too busy to detect the pong.
        """
        self._pongtime = time.time()
        self._pingtime = pingtime = 0
        
        while self.close_code is None:
            dt = config.ws_timeout
            
            # Ping, but don't spam
            if pingtime <= self._pongtime:
                self.ping(b'x')
                pingtime = self._pingtime = time.time()
                iters_since_ping = 0
            
            yield gen.sleep(dt / 5)
            
            # Check pong status
            iters_since_ping += 1
            if iters_since_ping < 5:
                pass  # we might have missed the pong
            elif time.time() - self._pongtime > dt:
                # Delay is so big that connection probably dropped.
                # Note that a browser sends a pong even if JS is busy
                logger.warn('Closing connection due to lack of pong')
                self.close(1000, 'Conection timed out (no pong).')
                return
    
    def on_pong(self, data):
        """ Implement the ws's on_pong() method. Called when our ping
        is returned by the browser.
        """
        self._pongtime = time.time()
    
    @property
    def ping_counter(self):
        """ Counter indicating the number of pings so far. This measure is
        used by ``Session.keep_alive()``.
        """
        return self._ping_counter
    
    @gen.coroutine
    def pinger2(self):
        """ Ticker so we have a signal of sorts to indicate round-trips.
        
        This is used to implement session.call_on_next_pong(), which
        is sort of like call_later(), but waits for both Py and JS to "flush"
        their current events.
        
        This uses a ping-pong mechanism implemented *atop* the websocket.
        When JS is working, it is not able to send a pong (which is what we
        want in this case).
        """
        self._ping_counter = 0
        self._pong_counter = 0
        while self.close_code is None:
            if self._pong_counter >= self._ping_counter:
                self._ping_counter += 1
                self.command('PING %i' % self._ping_counter)
            yield gen.sleep(1.0)
    
    def on_pong2(self, data):
        """ Called when our ping is returned by Flexx.
        """
        self._pong_counter = int(data)
        if self._session:
            self._session._receive_pong(self._pong_counter)
    
    # --- methods
    
    def command(self, cmd):
        self.write_message(cmd, binary=BINARY)
    
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
        host, port = self.application._flexx_serving  # set by us
        incoming_host = urlparse(origin).hostname
        if host == 'localhost':
            return True  # Safe
        elif host == '0.0.0.0':
            return True  # we cannot know if the origin matches
        elif host == incoming_host:
            return True
        else:
            logger.info('Connection refused from %s' % origin)
            return False
