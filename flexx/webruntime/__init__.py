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

"""

import logging
from collections import OrderedDict
logger = logging.getLogger(__name__)
del logging

from .. import config

from ._manage import RUNTIME_DIR, TEMP_APP_DIR
from ._common import BaseRuntime, DesktopRuntime  # noqa
from ._firefox import FirefoxRuntime
from ._nw import NWRuntime
from ._browser import BrowserRuntime
from ._qt import PyQtRuntime
from ._chrome import ChromeRuntime, GoogleChromeRuntime, ChromiumRuntime
from ._ms import IERuntime, EdgeRuntime
from ._selenium import SeleniumRuntime


# Definition of all runtime names and their order
_runtimes = OrderedDict()
_runtimes['firefox'] = FirefoxRuntime
_runtimes['nw'] = NWRuntime
_runtimes['pyqt'] = PyQtRuntime
_runtimes['chrome'] = ChromeRuntime  # though handled via aliases
_runtimes['googlechrome'] = GoogleChromeRuntime
_runtimes['chromium'] = ChromiumRuntime
_runtimes['edge'] = EdgeRuntime
_runtimes['ie'] = IERuntime
_runtimes['browser'] = BrowserRuntime


_aliases = {'app': 'firefox-app or nw-app',
            'browser': ('chrome-browser or firefox-browser or edge-browser '
                        'or default-browser'),
            'chrome-browser': 'googlechrome-browser or chromium-browser',
            'chrome-app': 'googlechrome-app or chromium-app',
            }


# We require to specify -app or -browser suffixes, though old names still work
_aliases_compat = {
            'xul': 'firefox-app',
            'nw': 'nw-app',
            'nwjs': 'nw-app',
            'chromeapp': 'chrome-app',
            'pyqt': 'pyqt-app',
            'firefox': 'firefox-browser',
            'chrome': 'chrome-browser',
}


def launch(url, runtime=None, **kwargs):
    """ Launch a web runtime in a new process.
    
    Parameters:
        url (str): The url to open. To open a local file prefix with ``file://``.
        runtime (str) : The runtime(s) to use. E.g. 'app' will open in a
            desktop-app-like runtime, 'browser' in a browser runtime. One can
            target specific runtimes, e.g. 'nw-app' or 'edge-browser', or
            a selection, e.g. 'chrome-browser or firefox-browser'. By default
            uses the value of ``flexx.config.webruntime`` or 'app or browser'.
            See below for more information on available runtimes.
        kwargs: addition arguments specific to the runtime. See the
            docs of the runtime classes.
    
    Returns:
        runtime (BaseRuntime): An object that can sometimes be used to control
        the runtime to some extend.
    
    Browser runtimes:
    
    * browser: open in a browser. Firefox, Chrome and Edge are prefered over
      the default browser.
    * default-browser: open in the system default browser.
    * firefox-browser: open in Firefox browser.
    * chrome-browser: open in Chrome/Chromium browser.
    * googlechrome-browser or chromium-browser: like chrome-browser, but specific.
    * edge-browser: open in Microsoft Edge browser.
    * ie-browser: open in Microsoft Internet Explorer browser.
    * xx-browser: use webbrowser module to open in browser "xx".
    
    App runtimes:
    
    * app: open as desktop app, using either firefox-app or nw-app.
    * firerox-app: open as desktop app, using Firefox' app framework.
    * nw-app: open as desktop app using NW.js.
    * pyqt-app: open as desktop-like app using PyQt/PySide.
    * chrome-app: open as desktop-like app via Chrome/Chromium.
    
    The most developed app runtimes are Firefox and NW. The former requires
    the user to have Firefox installed. The latter requires Flexx to download
    the runtime on first use. Firefox is lighter (memory-wise), while NW is
    based on Chromium, making it heavier, but generally faster. The other app
    runtimes are useful for testing or development, but should generally be
    avoided when distributing apps.
    
    """
    
    # Resolve backward compat names, and select default runtime if not given
    if runtime in _aliases_compat:
        logger.warn('Runtime name %s is deprecated, use %s instead.' %
                    (runtime, _aliases_compat[runtime]))
        runtime = _aliases_compat[runtime]
    if not runtime:
        runtime = config.webruntime
    if not runtime:
        runtime = 'app or browser'
    
    # Normalize runtime, apply aliases
    runtimes = _expand_runtime_name(runtime)
    
    for runtime in runtimes: 
    
        if runtime.endswith('-app'):
            # Desktop-like app runtime
            runtime = runtime.split('-')[0]
            Runtime = _runtimes.get(runtime, None)
            if Runtime is None:
                logger.warn('Unknown app runtime %r.' % runtime)
                continue
            else:
                rt = Runtime(**kwargs)
                if not rt.is_available():
                    continue
                rt.launch_app(url)
                return rt
        
        elif runtime.startswith('selenium-'):
            # Selenium runtime
            if '-' in runtime:
                kwargs['type'] = runtime.split('-', 1)[1]
            rt = SeleniumRuntime(**kwargs)
            rt.launch_tab(url)
            return rt
        
        elif runtime.endswith('-browser'):
            # Browser runtime
            runtime = runtime.split('-')[0]
            
            # Try using our own runtimes to open in tab, because
            # the webbrowser module is not that good at opening specific browsers.
            Runtime = _runtimes.get(runtime, None)
            if Runtime is not None:
                rt = Runtime(**kwargs)
                if rt.is_available():
                    rt.launch_tab(url)
                    return rt
            
            # Use browser runtime (i.e. webbrowser module)
            kwargs['type'] = runtime
            rt = BrowserRuntime(**kwargs)
            if rt.is_available():
                rt.launch_tab(url)
                return rt
        else:
            logger.warn('Runtime names should be "app", "browser" or '
                        'end with "-app" or "-browser", not %r' % runtime)
    
    else:
        raise ValueError('Could not detect a suitable backend among %r.' % runtimes)



def _expand_runtime_name(runtime):
    """ Apply aliases and map "x or y" to ['x', 'y'].
    """
    for c in (' or ', ',', '|'):
        runtime = runtime.replace(c, ' ')
    runtimes = []
    for runtime in runtime.split(' '):
        runtime = runtime.strip().lower()
        if runtime in _aliases:
            runtimes.extend(_expand_runtime_name(_aliases[runtime]))
        else:
            runtimes.append(runtime)
    return runtimes


##

def _print_autoclasses():  # pragma: no cover
    """ Run this code to get ``.. autoclass::`` definitions to put in the docs.
    """
    from flexx.webruntime import _runtimes
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
