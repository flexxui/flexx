"""
The webruntime module can be used to launch a runtime for applications
based on HTML/JS/CSS. This can be a browser or something that looks like
a desktop app.
"""

"""
Memory considerations
---------------------

* xul uses one process, taking about 45 MB app
* pyqt uses one process, taking about 48 MB per app
* chrome uses 4 process plus 3 per app, taking 100 MB plus 74 per app
* MSHTML todo

"""

import logging
from collections import OrderedDict
logger = logging.getLogger(__name__)
del logging

from .. import config

from ._manage import RUNTIME_DIR
from .common import BaseRuntime, DesktopRuntime  # noqa
from .xul import FirefoxRuntime
from .nodewebkit import NWRuntime
from .browser import BrowserRuntime
from .qtwebkit import PyQtRuntime
from .chromeapp import ChromeRuntime, ChromiumRuntime
from .mshtml import IERuntime, EdgeRuntime
from .selenium import SeleniumRuntime

# todo: allow "xul or nw" and have an alias that maps to it

# Definition of all runtime names and their order
_runtimes = OrderedDict(firefox=FirefoxRuntime,
                        nw=NWRuntime,
                        pyqt=PyQtRuntime,
                        chrome=ChromeRuntime,
                        chromium=ChromiumRuntime,
                        edge=EdgeRuntime,
                        ie=IERuntime,
                        browser=BrowserRuntime,
                        )

# App runtimes have a "-app" suffix, but for all serieus app runtimes
# we provide a single-word alias.
_aliases = {'nw': 'nw-app',
            'nwjs': 'nw-app',  # backward compat
            'xul': 'firefox-app',
            'chromeapp': 'chrome-app',  # backward compat
            }

# _aliases = {'firefox': 'browser-firefox',
#             'chrome': 'browser-chrome',
#             'chromium': 'browser-chromium',
#             'edge': 'browser-edge',
#             'ie': 'browser-ie',
#             'nw': 'app-nw',
#             'nwjs': 'app-nw',  # backward compat
#             'xul': 'app-firefox',
#             'chromeapp': 'app-chrome',
#             }

def launch(url, runtime=None, **kwargs):
    """ Launch a web runtime in a new process.
    
    Parameters:
        url (str): The url to open. To open a local file prefix with ``file://``.
        runtime (str) : The runtime to use. See below.
            By default uses 'xul' if available, and 'browser' otherwise.
        kwargs: addition arguments specific to the runtime. See the
            docs of the runtime classes.
    
    Returns:
        runtime (BaseRuntime): An object that can sometimes be used to control
        the runtime to some extend.
    
    Browser runtimes:
        
    * firefox: open url in Firefox browser.
    * chrome/chromium: open url in Chrome/Chromium browser.
    * edge: open url in Microsoft Edge browser.
    * ie: open url in Microsoft Internet Explorer browser.
    * browser: open in the default browser.
    * xx: unknown names are assumed to be a browser name, and
      attempted to be opened using the webbrowser module.
    
    App runtimes:
    
    * xul (alias for firerox-app): open url as desktop app, using
      Firefox' app framework.
    * pyqt: open url as desktop-like app using PyQt/PySide.
    * nw: open url as desktop app using NW.js.
    * chrome-app/chromium-app: open url as desktop-like app.
    
    The most developed desktop runtimes are XUL and NW. The former requires
    the user to have Firefox installed. The latter requires Flexx to download
    the runtime on first use. XUL is lighter (memory-wise), while NW is based
    on Chromium, making it heavier, but generally faster. The other app
    runtimes are useful for testing or development, but should be avoided when
    distributing apps.
    
    """
    
    # Select default runtime if not given
    if not runtime:
        runtime = config.webruntime
    if not runtime:
        runtime = 'xul' if FirefoxRuntime().is_available() else 'browser'
    
    # Normalize runtime, apply aliases
    runtime = runtime.lower()
    runtime = _aliases.get(runtime, runtime)
    
    if runtime.endswith('-app'):
        # Desktop-like app runtime
        runtime = runtime.split('-')[0]
        Runtime = _runtimes.get(runtime, None)
        if Runtime is None:
            raise ValueError('Unknown app runtime %r.' % runtime)
        else:
            rt = Runtime(**kwargs)
            rt.launch_app(url)
            return rt
    
    elif runtime.startswith('selenium-'):
        # Selenium runtime
        if '-' in runtime:
            kwargs['type'] = runtime.split('-', 1)[1]
        rt = SeleniumRuntime(**kwargs)
        rt.launch_tab(url)
        return rt
    
    else:
        # Browser runtime
        if runtime.startswith('browser-'):
            runtime = runtime.split('-', 1)[1]  # backwards compat
        
        # Try using our own runtimes to open in tab, because
        # the webbrowser module is not that good at opening specific browsers.
        Runtime = _runtimes.get(runtime, None)
        if Runtime is not None:
            rt = Runtime(**kwargs)
            if rt.is_available():
                rt.launch_tab(url)
                return rt
        
        # Use browser runtime (i.e. webbrowser module)
        if runtime and runtime not in ('default', 'browser'):
            kwargs['type'] = runtime
        rt = BrowserRuntime(**kwargs)
        if rt.is_available():
            rt.launch_tab(url)
            return rt
    
    raise ValueError('Unknown runtime or browser %r.' % runtime)


launch.__doc__ = launch.__doc__.replace('SUPPORTED_RUNTIMES', 
                                        ', '.join([repr(n) for n in _runtimes]))


def _print_autoclasses():  # pragma: no cover
    """ Call this to get ``.. autoclass::`` definitions to put in the docs.
    """
    lines = []
    seen = set()
    for name in ('BaseRuntime', 'DesktopRuntime'):
        lines.append('.. autoclass:: flexx.webruntime.%s\n  :members:' % name)
    for name, Cls in _runtimes.items():
        if Cls in seen:
            continue
        seen.add(Cls)
        lines.append('.. autoclass:: flexx.webruntime.%s\n  :members:' % Cls.__name__)
    print('\n\n'.join(lines))
