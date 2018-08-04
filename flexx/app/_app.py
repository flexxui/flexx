"""
Definition of the App class and app manager.
"""

import os
import io
import time
import shutil
import weakref
import zipfile
import tempfile
from base64 import encodestring as encodebytes

import webruntime

from .. import config, event

from ._component2 import PyComponent, JsComponent
from ._server import current_server
from ._session import Session, get_page_for_export
from ._assetstore import assets
from . import logger


class ExporterWebSocketDummy:
    """ Object that can be used by an app inplace of the websocket to
    export apps to standalone HTML. The object tracks the commands send
    by the app, so that these can be re-played in the exported document.
    """
    close_code = None

    def __init__(self):
        self.commands = []

    def write_command(self, cmd):
        self.commands.append(cmd)


class App:
    """ Specification of a Flexx app.

    Strictly speaking, this is a container for a ``PyComponent``/``JsComponent``
    class plus the args and kwargs that it is to be instantiated with.

    Arguments:
        cls (Component): the PyComponent or JsComponent class (e.g. Widget) that
            represents this app.
        args: positional arguments used to instantiate the class (and received
            in its ``init()`` method).
        kwargs: keyword arguments used to initialize the component's properties.
    """

    def __init__(self, cls, *args, **kwargs):
        if not isinstance(cls, type) and issubclass(type, (PyComponent, JsComponent)):
            raise ValueError('App needs a PyComponent or JsComponent class '
                             'as its first argument.')
        self._cls = cls
        self.args = args
        self.kwargs = kwargs
        self._path = cls.__name__  # can be overloaded by serve()
        self._is_served = False

        # Handle good defaults
        if hasattr(cls, 'title') and self.kwargs.get('title', None) is None:
            self.kwargs['title'] = 'Flexx app - ' + cls.__name__
        if hasattr(cls, 'set_icon') and self.kwargs.get('icon', None) is None:
            # Set icon as base64 str; exported apps can still be standalone
            fname = os.path.abspath(os.path.join(__file__, '..', '..',
                                                    'resources', 'flexx.ico'))
            icon_str = encodebytes(open(fname, 'rb').read()).decode()
            self.kwargs['icon'] = 'data:image/ico;base64,' + icon_str

    def __call__(self, *args, **kwargs):
        a = list(self.args) + list(args)
        kw = {}
        kw.update(self.kwargs)
        kw.update(kwargs)
        return self.cls(*a, **kw)

    def __repr__(self):
        t = '<App based on class %s pre-initialized with %i args and %i kwargs>'
        return t % (self.cls.__name__, len(self.args), len(self.kwargs))

    @property
    def cls(self):
        """ The Component class that is the basis of this app.
        """
        return self._cls

    @property
    def is_served(self):
        """ Whether this app is already registered by the app manager.
        """
        return self._is_served

    @property
    def url(self):
        """ The url to acces this app. This raises an error if serve() has not
        been called yet or if Flexx' server is not yet running.
        """
        server = current_server(False)
        if not self._is_served:
            raise RuntimeError('Cannot determine app url if app is not yet "served".')
        elif not (server and server.serving):
            raise RuntimeError('Cannot determine app url if the server is not '
                               'yet running.')
        else:
            proto = server.protocol
            host, port = server.serving
            path = self._path + '/' if self._path else ''
            return '%s://%s:%i/%s' % (proto, host, port, path)

    @property
    def name(self):
        """ The name of the app, i.e. the url path that this app is served at.
        """
        return self._path or '__main__'

    def serve(self, name=None):
        """ Start serving this app.

        This registers the given class with the internal app manager. The
        app can be loaded via 'http://hostname:port/name'.

        Arguments:
            name (str, optional): the relative URL path to serve the app on.
                If this is ``''`` (the empty string), this will be the main app.
                If not given or None, the name of the component class is used.
        """
        # Note: this talks to the manager; it has nothing to do with the server
        if self._is_served:
            raise RuntimeError('This app (%s) is already served.' % self.name)
        if name is not None:
            self._path = name
        manager.register_app(self)
        self._is_served = True

    def launch(self, runtime=None, **runtime_kwargs):
        """ Launch this app as a desktop app in the given runtime.

        Arguments:
            runtime (str): the runtime to launch the application in.
                Default 'app or browser'.
            runtime_kwargs: kwargs to pass to the ``webruntime.launch`` function.
                A few names are passed to runtime kwargs if not already present
                ('title' and 'icon').

        Returns:
            Component: an instance of the given class.
        """
        # creates server (and event loop) if it did not yet exist
        current_server()

        # Create session
        if not self._is_served:
            self.serve()
        session = manager.create_session(self.name)

        # Transfer title and icon
        if runtime_kwargs.get('title', None) is None and 'title' in self.kwargs:
            runtime_kwargs['title'] = self.kwargs['title']
        if runtime_kwargs.get('icon', None) is None and 'icon' in self.kwargs:
            runtime_kwargs['icon'] = self.kwargs['icon']
        # Launch web runtime, the server will wait for the connection
        url = self.url + '?session_id=%s' % session.id
        if not runtime or '!' in config.webruntime:
            runtime = config.webruntime.strip('!')
        session._runtime = webruntime.launch(url, runtime=runtime, **runtime_kwargs)
        return session.app

    def dump(self, fname=None, link=0):
        """ Get a dictionary of web assets that statically represents the app.

        The returned dict contains at least one "html file". Any session-specific
        or shared data is also included. If link is 2 or 3, all shared assets
        are included too (because the main document links to them).

        Arguments:
            fname (str, optional): the name of the main html asset.
                If not given or None, the name of the component class
                is used. Must end in .html/.htm/.hta.
            link (int): whether to link (JS and CSS) assets or embed them:
                A values of 0/1 is recommended for single (and standalone) apps,
                while multiple apps can share common assets by using 2/3.
                * 0: all assets are embedded (default).
                * 1: normal assets are embedded, remote assets remain remote.
                * 2: all assets are linked (as separate files).
                * 3: normal assets are linked, remote assets remain remote.

        Returns:
            dict: A collection of assets.
        """

        # Get asset name
        if fname is None:
            if self.name in ('__main__', ''):
                fname = 'index.html'
            else:
                fname = self.name.lower() + '.html'

        # Validate fname
        if os.path.basename(fname) != fname:
            raise ValueError('App.dump() fname must not contain directory names.')
        elif not fname.lower().endswith(('.html', 'htm', '.hta')):
            raise ValueError('Invalid extension for dumping {}'.format(fname))

        # We need to serve the app, i.e. notify the mananger about this app
        if not self._is_served:
            name = fname.split('.')[0].replace('-', '_').replace(' ', '_')
            self.serve(name)

        # Create session with id equal to the app name. This would not be strictly
        # necessary to make exports work, but it makes sure that exporting twice
        # generates the exact same thing (no randomly generated dir names).
        session = manager.create_session(self.name, self.name)

        # Make fake connection using exporter object
        exporter = ExporterWebSocketDummy()
        manager.connect_client(exporter, session.app_name, session.id)

        # Clean up again - NO keep in memory to ensure two sessions dont get same id
        # manager.disconnect_client(session)

        assert link in (0, 1, 2, 3), "Expecting link to be in (0, 1, 2, 3)."

        # Warn for PyComponents
        if issubclass(self.cls, PyComponent):
            logger.warn('Exporting a PyComponent - any Python interactivity will '
                        'not work in exported apps.')

        d = {}

        # Get main HTML page
        html = get_page_for_export(session, exporter.commands, link)
        if fname.lower().endswith('.hta'):
            hta_tag = '<meta http-equiv="x-ua-compatible" content="ie=edge" />'
            html = html.replace('<head>', '<head>\n    ' + hta_tag, 1)
        d[fname] = html.encode()

        # Add shares assets if we link to it from the main page
        if link in (2, 3):
            d.update(assets._dump_assets(link==2))  # also_remote if link==2

        # Add session specific, and shared data
        d.update(session._dump_data())
        d.update(assets._dump_data())

        return d

    def export(self, filename, link=0, overwrite=True):
        """ Export this app to a static website.

        Also see dump(). An app that contains no data, can be exported to a
        single html document by setting link to 0 or 1.

        Arguments:
            filename (str): Path to write the HTML document to.
                If the filename ends with .hta, a Windows HTML Application is
                created. If a directory is given, the app is exported to
                appname.html in that directory.
            link (int): whether to link (JS and CSS) assets or embed them:
                * 0: all assets are embedded (default).
                * 1: normal assets are embedded, remote assets remain remote.
                * 2: all assets are linked (as separate files).
                * 3: normal assets are linked, remote assets remain remote.
            overwrite (bool, optional): if True (default) will overwrite files
                that already exist. Otherwise existing files are skipped.
                The latter makes it possible to efficiently export a series of
                apps to the same directory and have them share common assets.
        """

        # Derive dirname and app name
        if not isinstance(filename, str):
            raise ValueError('str filename required, use dump() for in-memory export.')
        filename = os.path.abspath(os.path.expanduser(filename))
        if (
                os.path.isdir(filename) or
                filename.endswith(('/', '\\')) or
                '.' not in os.path.basename(filename)
                ):
            dirname = filename
            fname = None
        else:
            dirname, fname = os.path.split(filename)

        # Collect asset dict
        d = self.dump(fname, link)

        # Write all assets to file
        for fname, blob in d.items():
            filename = os.path.join(dirname, fname)
            if not overwrite and os.path.isfile(filename):
                continue
            dname = os.path.dirname(filename)
            if not os.path.isdir(dname):
                os.makedirs(dname)
            with open(filename, 'wb') as f:
                f.write(blob)

        app_type = 'standalone app' if len(d) == 1 else 'app'
        logger.info('Exported %s to %r' % (app_type, filename))

    def publish(self, name, token, url=None):
        """ Publish this app as static HTML on the web.

        This is an experimental feature! We will try to keep your app published,
        but make no guarantees. We reserve the right to remove apps or shut down
        the web server completely.

        Arguments:
            name (str): The name by which to publish this app. Must be unique
                within the scope of the published site.
            token (str): a secret token. This is stored at the target website.
                Subsequent publications of the same app name must have the same
                token.
            url (str): The url to POST the app to. If None (default),
                the default Flexx live website url will be used.
        """
        # todo: also use dump
        # Export to disk
        dirname = os.path.join(tempfile.gettempdir(), 'flexx_exports', name)
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)
        os.makedirs(dirname)
        self.export(dirname, link=3, write_shared=True)
        # Zip it up
        f = io.BytesIO()
        with zipfile.ZipFile(f, 'w') as zf:
            for root, dirs, files in os.walk(dirname):
                for fname in files:
                    filename = os.path.join(root, fname)
                    zf.write(filename, os.path.relpath(filename, dirname))
        # Clear temp dir
        shutil.rmtree(dirname)
        # POST
        try:
            import requests
        except ImportError:
            raise ImportError('App.publish() needs requests lib: pip install requests')
        url = url or 'http://flexx.app/submit/{name}/{token}'
        real_url = url.format(name=name, token=token)
        r = requests.post(real_url, data=f.getvalue())
        if r.status_code != 200:
            raise RuntimeError('Publish failed: ' + r.text)
        else:
            print('Publish succeeded, ' + r.text)
            if url.startswith('http://flexx.app'):
                print('You app is now available at '
                      'http://flexx.app/open/%s/' % name)

# todo: thread safety

def valid_app_name(name):
    T = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789'
    return name and name[0] in T[:-10] and all([c in T for c in name])


# Note that the AppManager is a Component (but not a PyComponent)

class AppManager(event.Component):
    """ Manage apps, or more specifically, the session objects.

    There is one AppManager class (in ``flexx.app.manager``). It's
    purpose is to manage the application classes and instances. It is mostly
    intended for internal use, but users can use it to e.g. monitor connections.
    Create a reaction using ``@app.manager.reaction('connections_changed')``
    to track when the number of connected session changes.
    """

    total_sessions = 0  # Keep track how many sessesions we've served in total

    def __init__(self):
        super().__init__()
        # name -> (app, pending, connected) - lists contain Session objects
        self._appinfo = {}
        self._session_map = weakref.WeakValueDictionary()
        self._last_check_time = time.time()

    def register_app(self, app):
        """ Register an app (an object that wraps a Component class plus init args).
        After registering an app (and starting the server) it is
        possible to connect to "http://address:port/app_name".
        """
        assert isinstance(app, App)
        name = app.name
        if not valid_app_name(name):
            raise ValueError('Given app does not have a valid name %r' % name)
        pending, connected = [], []
        if name in self._appinfo:
            old_app, pending, connected = self._appinfo[name]
            if app.cls is not old_app.cls:  # if app is not old_app:
                logger.warn('Re-defining app class %r' % name)
        self._appinfo[name] = app, pending, connected

    def create_default_session(self, cls=None):
        """ Create a default session for interactive use (e.g. the notebook).
        """

        if '__default__' in self._appinfo:
            raise RuntimeError('The default session can only be created once.')

        if cls is None:
            cls = JsComponent
        if not isinstance(cls, type) and issubclass(cls, (PyComponent, JsComponent)):
            raise TypeError('create_default_session() needs a JsComponent subclass.')

        # Create app and register it by __default__ name
        app = App(cls)
        app.serve('__default__')  # calls register_app()

        # Create the session instance and register it
        session = Session('__default__')
        self._session_map[session.id] = session
        _, pending, connected = self._appinfo['__default__']
        pending.append(session)

        # Instantiate the component
        app(flx_session=session, flx_is_app=True)

        return session

    def remove_default_session(self):
        """ Remove default session if there is one, closing the session.
        """
        s = self.get_default_session()
        if s is not None:
            s.close()
        self._appinfo.pop('__default__', None)

    def get_default_session(self):
        """ Get the default session that is used for interactive use.
        Returns None unless create_default_session() was called earlier.

        When a JsComponent class is created without a session, this method
        is called to get one (and will then fail if it's None).
        """
        x = self._appinfo.get('__default__', None)
        if x is None:
            return None
        else:
            _, pending, connected = x
            sessions = pending + connected
            if sessions:
                return sessions[-1]

    def _clear_old_pending_sessions(self, max_age=30):
        try:

            count = 0
            for name in self._appinfo:
                if name == '__default__':
                    continue
                _, pending, _ = self._appinfo[name]
                to_remove = [s for s in pending
                             if (time.time() - s._creation_time) > max_age]
                for s in to_remove:
                    self._session_map.pop(s.id, None)
                    pending.remove(s)
                count += len(to_remove)
            if count:
                logger.warn('Cleared %i old pending sessions' % count)

        except Exception as err:
            logger.error('Error when clearing old pending sessions: %s' % str(err))

    def create_session(self, name, id=None, request=None):
        """ Create a session for the app with the given name.

        Instantiate an app and matching session object corresponding
        to the given name, and return the session. The client should
        be connected later via connect_client().
        """
        # Called by the server when a client connects, and from the
        # launch and export functions.

        if time.time() - self._last_check_time > 5:
            self._last_check_time = time.time()
            self._clear_old_pending_sessions()

        if name == '__default__':
            raise RuntimeError('There can be only one __default__ session.')
        elif name not in self._appinfo:
            raise ValueError('Can only instantiate a session with a valid app name.')

        app, pending, connected = self._appinfo[name]

        # Create the session
        session = Session(name, request=request)
        if id is not None:
            session._id = id  # used by app.export
        self._session_map[session.id] = session
        # Instantiate the component
        # This represents the "instance" of the App object (Component class + args)
        app(flx_session=session, flx_is_app=True)

        # Now wait for the client to connect. The client will be served
        # a page that contains the session_id. Upon connecting, the id
        # will be communicated, so it connects to the correct session.
        pending.append(session)

        logger.debug('Instantiate app client %s' % session.app_name)
        return session

    def connect_client(self, ws, name, session_id, cookies=None):
        """ Connect a client to a session that was previously created.
        """
        _, pending, connected = self._appinfo[name]
        # Search for the session with the specific id
        for session in pending:
            if session.id == session_id:
                pending.remove(session)
                break
        else:
            raise RuntimeError('Asked for session id %r, but could not find it' %
                               session_id)

        # Add app to connected, set ws
        assert session.id == session_id
        assert session.status == Session.STATUS.PENDING
        logger.info('New session %s %s' % (name, session_id))
        session._set_cookies(cookies)
        session._set_ws(ws)
        connected.append(session)
        AppManager.total_sessions += 1
        self.connections_changed(session.app_name)
        return session  # For the ws

    def disconnect_client(self, session):
        """ Close a connection to a client.

        This is called by the websocket when the connection is closed.
        The manager will remove the session from the list of connected
        instances.
        """
        if session.app_name == '__default__':
            logger.info('Default session lost connection to client.')
            return  # The default session awaits a re-connect

        _, pending, connected = self._appinfo[session.app_name]
        try:
            connected.remove(session)
        except ValueError:
            pass
        logger.info('Session closed %s %s' %(session.app_name, session.id))
        session.close()
        self.connections_changed(session.app_name)

    def has_app_name(self, name):
        """ Returns the case-corrected name if the given name matches
        a registered appliciation (case insensitive). Returns None if the
        given name does not match any applications.
        """
        name = name.lower()
        for key in self._appinfo.keys():
            if key.lower() == name:
                return key
        else:
            return None

    def get_app_names(self):
        """ Get a list of registered application names.
        """
        return [name for name in sorted(self._appinfo.keys())]

    def get_session_by_id(self, id):
        """ Get session object by its id, or None.
        """
        return self._session_map.get(id, None)

    def get_connections(self, name):
        """ Given an app name, return the connected session objects.
        """
        _, pending, connected = self._appinfo[name]
        return list(connected)

    @event.emitter
    def connections_changed(self, name):
        """ Emits an event with the name of the app for which a
        connection is added or removed.
        """
        return dict(name=str(name))


# Create global app manager object
manager = AppManager()
