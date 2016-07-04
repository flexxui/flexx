"""
The webruntime module can be used to launch a runtime for applications
based on HTML/JS/CSS. This can be a browser or something that looks like
a desktop app.


Supported runtimes
------------------

Here's a quick overview of the supported runtimes. For details, see the
docs of the runtime classes below.

* xul - Mozilla's app framework. Available wherever Firefox is
  installed. Recommended.
* nwjs - An app runtime based on Chromium and node.js.
* pyqt - Use QWebkit as a runtime. Need PyQt4 or PySide with QWebkit installed. 
* chromeapp - Native-ish looking apps via Chrome/Chromium.
* browser - The default browser.
* browser-X - Where X should be supported by Python's webbrowser module.
* selenium-X - Where X should be supported by Selenium.
* nodejs - A runtime based on Chrome's V8 JavaScript engine. No UI.

Runtimes currently not supported:

* mshtml - uses the trident engine (like IE does), I think we want this one.
* electron - by github (electron.atom.io, based on Chromium)


Memory considerations
---------------------

* xul uses one process, taking about 45 MB app
* pyqt uses one process, taking about 48 MB per app
* chrome uses 4 process plus 3 per app, taking 100 MB plus 74 per app
* MSHTML todo

"""

import logging
logger = logging.getLogger(__name__)
del logging

from .. import config

from .common import BaseRuntime, DesktopRuntime  # noqa
from .xul import XulRuntime, has_firefox
from .nodewebkit import NodeWebkitRuntime
from .browser import BrowserRuntime
from .qtwebkit import PyQtRuntime
from .chromeapp import ChromeAppRuntime
from .nodejs import NodejsRuntime
from .selenium import SeleniumRuntime

# todo: make a 'desktop' runtime option that will try xul, nwjs, chromeapp, trident

# Definition of runtime names and their order
_runtimes = [
    ('xul', XulRuntime),
    ('nwjs', NodeWebkitRuntime),
    ('pyqt', PyQtRuntime),
    ('chromeapp', ChromeAppRuntime),
    ('browser', BrowserRuntime),
    ('browser-X', BrowserRuntime),
    ('selenium-X', SeleniumRuntime),
    ('nodejs', NodejsRuntime),
    ]


def launch(url, runtime=None, **kwargs):
    """ Launch a web runtime in a new process.
    
    Parameters:
        url (str): The url to open. To open a local file prefix with ``file://``.
        runtime (str) : The runtime to use.
            Can be SUPPORTED_RUNTIMES.
            By default uses 'xul' if available, and 'browser' otherwise.
        kwargs: addition arguments specific to the runtime. See the
            docs of the runtime classes.
    
    Returns:
        runtime (BaseRuntime): An object that can be used to control
        the runtime to some extend.
    """
    
    # Select default runtime if not given
    if not runtime:
        runtime = config.webruntime
    if not runtime:
        runtime = 'xul' if has_firefox() else 'browser'
    
    # Normalize runtime, apply aliases
    runtime = runtime.lower()
    aliases= {'firefox': 'browser-firefox', 'chrome': 'browser-chrome'}
    runtime = aliases.get(runtime, runtime)
    
    # Select Runtime class
    type = None
    for name, Cls in _runtimes:
        if name.endswith('-X'):
            if runtime == name[:-2]:
                Runtime = Cls
                break
            elif runtime.startswith(name[:-1]):
                Runtime = Cls
                type = runtime.split('-', 1)[1]
                break
        elif runtime == name:
            Runtime = Cls
            break
    else:
        raise ValueError('Unknown web runtime %r.' % runtime)
    
    # Create runtime, launch, and return 
    if type is not None:
        kwargs['type'] = type
    kwargs['url'] = url
    rt = Runtime(**kwargs)
    return rt


launch.__doc__ = launch.__doc__.replace('SUPPORTED_RUNTIMES', 
                                        ', '.join([repr(n) for n, c in _runtimes]))


def _print_autoclasses():  # pragma: no cover
    """ Call this to get ``.. autoclass::`` definitions to put in the docs.
    """
    lines = []
    seen = set()
    for name in ('BaseRuntime', 'DesktopRuntime'):
        lines.append('.. autoclass:: flexx.webruntime.%s\n  :members:' % name)
    for name, Cls in _runtimes:
        if Cls in seen:
            continue
        seen.add(Cls)
        lines.append('.. autoclass:: flexx.webruntime.%s\n  :members:' % Cls.__name__)
    print('\n\n'.join(lines))
