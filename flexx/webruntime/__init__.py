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

import sys
import logging
import traceback
from collections import OrderedDict
logger = logging.getLogger(__name__)
del logging

from .. import config
from .. import dialite

from ._manage import RUNTIME_DIR, TEMP_APP_DIR  # noqa
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

if sys.platform.startswith('win'):
    _aliases['app'] = 'firefox-app or chrome-app or nw-app'

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
        url (str): The url to open, e.g. ``'http://python.org'``. To open a
            local file use ``'file://...'``.
        runtime (str) : The runtime(s) to use. E.g. 'app' will open in a
            desktop-app-like runtime, 'browser' in a browser runtime. One can
            target specific runtimes, e.g. 'nw-app' or 'edge-browser', or
            a selection, e.g. 'chrome-browser or firefox-browser'. If not given
            uses the value of ``flexx.config.webruntime``, which defaults to
            ``'app or browser'``.
            See below for more information on available runtimes.
        kwargs: addition arguments specific to the runtime. See the
            docs of the runtime classes.
    
    Returns:
        runtime (BaseRuntime): An object that represents the runtime. For
        Desktop runtimes it can be used to close the runtime.
    
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
    
    * app: open as desktop app, using firefox-app or nw-app
      (and chrome-app on Windows).
    * firerox-app: open as desktop app, using Firefox' app framework (Xul).
    * nw-app: open as desktop app using NW.js.
    * chrome-app: open as desktop-like app via Chrome/Chromium (only works well
      on Windows).
    * pyqt-app: open as desktop-like app using PyQt/PySide.
    
    The most developed app runtimes are Firefox and NW. The former requires
    the user to have Firefox installed. The latter can be installed by the user
    simply by downloading the archive. Firefox is lighter (memory-wise), while
    NW is based on Chromium, making it heavier, but generally faster. The other
    app runtimes are useful for testing or development, but should generally be
    avoided when distributing apps.
    
    """
    
    # Resolve backward compat names, and select default runtime if not given
    if runtime in _aliases_compat:
        logger.warn('Runtime name %s is deprecated, use %s instead.' %
                    (runtime, _aliases_compat[runtime]))
        runtime = _aliases_compat[runtime]
    if not runtime or '!' in config.webruntime:
        runtime = config.webruntime.strip('!')
    if not runtime:
        runtime = 'app or browser'
    given_runtime = runtime
    
    # Normalize runtime, apply aliases
    runtimes = _expand_runtime_name(runtime)
    tried_runtimes = []
    errors = []
    
    # Attempt to launch runtimes, one by one
    for runtime in runtimes: 
        rt, launched, err = _launch(url, runtime, **kwargs)
        if rt and launched:
            return rt  # Hooray!
        if rt:
            tried_runtimes.append(rt)
        if err:
            errors.append(str(err).strip())
    
    # We end up here only when no suitable runtime was found.
    # Note that default-browser will always work, so by default we wont
    # end up here. We can well get here when runtime is 'app' though.
    
    # Show dialog to the user with information on how to install a runtime.
    # It is important that this is a dialog and not printed to stdout for
    # cases where an app is frozen (e.g. with cx_Freeze), because there is
    # no stdout in that case. Dialite will fallback to stdout if there is no
    # way to create a dialog, and if there is a tty, and attempt to show a
    # webpage with an error message otherwise.
    messages = []
    if not tried_runtimes:
        messages.append('Given runtime name "%s" does '
                        'not resolve to any known runtimes.' % given_runtime)
    elif len(tried_runtimes) == 1:
        # This app needs exactly this runtime
        rt = tried_runtimes[0]
        name = given_runtime if given_runtime.endswith('-browser') else rt.get_name()
        msg = 'Could not run app, because runtime %s ' % name
        msg += 'could not be used.' if errors else 'is not available.'
        messages.append(msg)
        if rt._get_install_instuctions():
            messages.append(rt._get_install_instuctions())
    else:
        # User has options
        seen = set()
        messages.append('Could not find a suitable runtime to run app. '
                        'Available options:')
        for c, rt in zip('ABCDEFGHIJK', tried_runtimes):
            if rt.get_name() in seen or not rt._get_install_instuctions():
                continue
            seen.add(rt.get_name())
            messages.append(c + ': ' + rt._get_install_instuctions())
    if errors:
        messages.append('Errors:')
        messages.extend(errors)
    messages = '\n\n'.join(messages)
    
    dialite.fail('Flexx - No suitable runtime available', messages)
    
    raise ValueError('Could not detect a suitable backend among %r.' % runtimes)



def _launch(url, runtime, **kwargs):
    """ Attempt to launch runtime by its name.
    Return (runtime_object, is_launched, error_object)
    """
    
    rt = None
    launched = False
    
    try:
    
        if runtime.endswith('-app'):
            # Desktop-like app runtime
            runtime = runtime.split('-')[0]
            Runtime = _runtimes.get(runtime, None)
            if Runtime is None:
                logger.warn('Unknown app runtime %r.' % runtime)
            else:
                rt = Runtime(**kwargs)
                if rt.is_available():
                    rt.launch_app(url)
                    launched = True
        
        elif runtime.startswith('selenium-'):
            # Selenium runtime - always try or fail
            if '-' in runtime:
                kwargs['type'] = runtime.split('-', 1)[1]
            rt = SeleniumRuntime(**kwargs)
            rt.launch_tab(url)
            launched = True
        
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
                    launched = True
            
            # Use browser runtime (i.e. webbrowser module)
            # Default-browser always works (from the runtime perspective)
            kwargs['type'] = runtime
            rt = BrowserRuntime(**kwargs)
            if rt.is_available():
                rt.launch_tab(url)
                launched = True
        else:
            logger.warn('Runtime names should be "app", "browser" or '
                        'end with "-app" or "-browser", not %r' % runtime)
    
    except Exception as err:
        type_, value, tb = sys.exc_info()
        trace = traceback.format_list(traceback.extract_tb(tb))
        del tb
        return rt, False, str(err) + '\n' + ''.join(trace[-1:])
    
    return rt, launched, None


def _expand_runtime_name(runtime):
    """ Apply aliases and map "x or y" to ['x', 'y'].
    """
    # Normalize
    for c in (' or ', ',', '|'):
        runtime = runtime.replace(c, ' ')
    # Expand
    runtimes = []
    for runtime in runtime.split(' '):
        runtime = runtime.strip().lower()
        if runtime in _aliases:
            runtimes.extend(_expand_runtime_name(_aliases[runtime]))
        else:
            runtimes.append(runtime)
    # Deduplicate
    runtimes2 = []
    for runtime in runtimes:
        if runtime not in runtimes2:
            runtimes2.append(runtime)
    return runtimes2


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
