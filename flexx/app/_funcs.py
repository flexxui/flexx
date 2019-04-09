"""
Functional API for flexx.app
"""

import json
import base64

import webruntime

from .. import config, set_log_level

from ._app import App, manager
from ._component2 import PyComponent, JsComponent
from ._server import current_server
from ._assetstore import assets
from ._clientcore import serializer
from . import logger

reprs = json.dumps

## Main loop functions


def start():
    """
    Start the server and event loop. This function generally does not
    return until the application is stopped (although it may in
    interactive environments (e.g. Pyzo)).

    In more detail, this calls ``run_forever()`` on the asyncio event loop
    associated with the current server.
    """
    server = current_server()
    server.start()


def run():
    """
    Start the event loop in desktop app mode; the server will close
    down when there are no more connections.
    """
    server = current_server()
    server._auto_stop = True
    return start()


def stop():
    """
    Stop the event loop. This function is thread safe (it can be used
    even if ``app.start()`` was called from another thread).
    The server can be restarted after it has been stopped. Note that
    calling ``stop()`` too often will cause a subsequent call to ``start()``
    to return almost immediately.
    """
    server = current_server()
    server.stop()


@manager.reaction('connections_changed')
def _auto_closer(*events):
    server = current_server()
    if not getattr(server, '_auto_stop', False):
        return
    for name in manager.get_app_names():
        proxies = manager.get_connections(name)
        if proxies:
            return
    else:
        server.stop()


## App functions


class NoteBookHelper:
    """ Object that captures commands send to the websocket during the
    execution of a cell, and then applies these commands using a script
    node. This way, Flexx widgets keep working in the exported notebook.
    """

    close_code = None

    def __init__(self, session):
        self._session = session
        self._real_ws = None
        self._commands = []
        self.enable()

    def enable(self):
        get_ipython = None
        exec("from IPython import get_ipython")  # noqa - dont trigger e.g. PyInstaller
        ip = get_ipython()
        ip.events.register('pre_execute', self.capture)
        ip.events.register('post_execute', self.release)

    def capture(self):
        if self._real_ws is not None:
            logger.warning('Notebookhelper already is in capture mode.')
        else:
            if self._session._ws is None:
                raise RuntimeError(
                    'Session is missing a websocket connection. If you are '
                    'running in JupyterLab, this could be due to '
                    'https://github.com/jupyterlab/jupyterlab/issues/3118')
            self._real_ws = self._session._ws
            self._session._ws = self

    def release(self):
        if self._session._ws is self:
            self._session._ws = self._real_ws
        self._real_ws = None
        if self._commands:
            display = Javascript = None
            exec("from IPython.display import display, Javascript")  # noqa - dont trigger e.g. PyInstaller
            lines = []
            lines.append('var bb64 =  flexx.require("bb64");')
            lines.append('function cmd(c) {'
                            'flexx.s1._receive_command('
                            'flexx.serializer.decode('
                            'bb64.decode(c)));}')
            for command in self._commands:  # also DEFINE commands!
                command_str = base64.encodebytes(serializer.encode(command)).decode()
                lines.append('cmd("' + command_str.replace('\n', '') + '");')
            self._commands = []
            display(Javascript('\n'.join(lines)))

    def write_command(self, cmd):
        assert isinstance(cmd, tuple) and len(cmd) >= 1
        self._commands.append(cmd)


def init_notebook():
    """ Initialize the Jupyter notebook by injecting the necessary CSS
    and JS into the browser. Note that any Flexx-based libraries that
    you plan to use should probably be imported *before* calling this.

    Does not currently work in JupyterLab because
    https://github.com/jupyterlab/jupyterlab/issues/3118.
    """

    # Note: not using IPython Comm objects yet, since they seem rather
    # undocumented and I could not get them to work when I tried for a bit.
    # This means though, that flexx in the notebook only works on localhost.
    display = clear_output = HTML = None
    exec("from IPython.display import display, clear_output, HTML")  # noqa - dont trigger e.g. PyInstaller
    # from .. import ui  # noqa - make ui assets available

    # Make default log level warning instead of "info" to avoid spamming
    # This preserves the log level set by the user
    config.load_from_string('log_level = warning', 'init_notebook')
    set_log_level(config.log_level)

    # Get session or create new
    session = manager.get_default_session()
    if session is None:
        session = manager.create_default_session()

    # Check if already loaded, if so, re-connect
    if not getattr(session, 'init_notebook_done', False):
        session.init_notebook_done = True
    else:
        display(HTML("<i>Flexx already loaded (the notebook cannot export now)</i>"))
        return  # Don't inject Flexx twice

    # Open server - the notebook helper takes care of the JS resulting
    # from running a cell, but any interaction goes over the websocket.
    server = current_server()
    host, port = server.serving

    # Install helper to make things work in exported notebooks
    NoteBookHelper(session)

    proto = 'wss' if server.protocol == 'https' else 'ws'

    url = '%s://%s:%i/flexx/ws/%s' % (proto, host, port, session.app_name)

    # Determine JS snippets to run before and after init. The former is only
    # run in live notebooks.
    flexx_pre_init = "<script>window.flexx = {is_live_notebook: true};</script>"
    flexx_post_init = """<script>
            flexx.is_notebook = true;
            flexx.is_exported = !flexx.is_live_notebook;
            /* If Phosphor is already loaded, disable our Phosphor CSS. */
            if (window.jupyter && window.jupyter.lab) {
                document.getElementById('phosphor-all.css').disabled = true;
            }
            flexx.init();
            flexx.create_session("%s", "%s", "%s");
            </script>""" % (session.app_name, session.id, url)
    # Compose HTML to inject
    t = assets.get_asset('flexx-core.js').to_html('{}', 0)
    t += flexx_post_init
    t += "<i>Flexx is ready for use</i>\n"

    display(HTML(flexx_pre_init))  # Create initial Flexx info dict
    clear_output()  # Make sure the info dict is gone in exported notebooks
    display(HTML(t))

    # Note: the Widget._repr_html_() method is responsible for making
    # the widget show up in the notebook output area.

    # Note: asyncio will need to be enabled via %gui asyncio


# Keep serve and launch, they are still quite nice shorthands to quickly
# get something done.

def serve(cls, name=None, properties=None):
    """ Shorthand for ``app.App(cls).serve(name)``.
    """
    if properties is not None:
        raise RuntimeError('serve(... properties) is deprecated, '
                           'use app.App().serve() instead.')
    # Note: this talks to the manager; it has nothing to do with the server
    assert (isinstance(cls, type) and issubclass(cls, (PyComponent, JsComponent)))
    a = App(cls)
    a.serve(name)
    return cls


def launch(cls, runtime=None, properties=None, **runtime_kwargs):
    """ Shorthand for ``app.App(cls).launch(runtime, **runtime_kwargs)``.
    """
    if properties is not None:
        raise RuntimeError('launch(... properties) is deprecated, '
                           'use app.App().launch() instead.')
    if isinstance(cls, str):
        return webruntime.launch(cls, runtime, **runtime_kwargs)
    assert (isinstance(cls, type) and issubclass(cls, (PyComponent, JsComponent)))
    a = App(cls)
    return a.launch(runtime, **runtime_kwargs)


def export(cls, filename, properties=None, **kwargs):
    """ Shorthand for ``app.App(cls).export(filename, ...)``.
    """
    if properties is not None:
        raise RuntimeError('export(... properties) is deprecated, '
                           'use app.App(...).export() instead.')
    assert (isinstance(cls, type) and issubclass(cls, (PyComponent, JsComponent)))
    a = App(cls)
    return a.export(filename, **kwargs)
