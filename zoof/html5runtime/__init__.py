"""
This module provides a runtime to run applications based on HTML5 and
associated technologies. There are several runtimes available:


App runtimes
------------

* xul - Mozilla's app framework. Make use of the same engine as Firefox.
  Available where Firefox is installed.
* nodewebkit - Node webkit is an app runtime based on Chromium and node.js.
* pyqt - Use QWebkit as a runtime. No WebGL here though.
* chrome-app


Browsers
--------

* browser - launch the default browser
* browser-firefox - launch firefox browser
* browser-chrome - launch chrome/chromium browser
* browser-x = launch browser x (if supported by webbrowser module)


Other runtimes currently not supported
--------------------------------------

* MSHTML - uses the trident engine (like IE does), I think we want this one
* pywebkitgtk - not really cross-platform


Memory considerations
---------------------

* xul uses one process, taking about 45 MB app
* pyqt uses one process, taking about 48 MB per app
* chrome uses 4 process plus 3 per app, taking 100 MB plus 74 per app
* MSHTML todo

"""

from .common import HTML5Runtime
from .xul import XulRuntime
from .nodewebkit import NodeWebkitRuntime
from .browser import BrowserRuntime


# todo: select a runtime that is available


def launch(url, runtime=None, 
           title='', size=(640, 480), pos=None, icon=None):
    """ Launch an html5 runtime in a new process
    
    Returns an object that can be used to influence the runtime.
    
    Parameters
    ----------
    url : str
        The url to open. Can be a local file (prefix with file://).
    runtime : str
        The runtime to use. Can be 'xul', 'nodewebkit', 'browser', 
        'browser-firefox', 'browser-chrome', and more.
    title : str
        Window title. Some runtimes may override this with the title
        in the HTML head section.
    size: tuple of ints
        The size in pixels of the window. Some runtimes may ignore this.
    pos : tuple of ints
        The position of the window. Some runtimes may ignore this.
    icon : str
        Path to an icon file (png recommended). Some runtimes may ignore this.
    
    """
    
    runtime = runtime or 'xul'
    runtime = runtime.lower()
    
    # Aliases
    aliases= {'firefox': 'browser-firefox', 'chrome': 'browser-chrome'}
    runtime = aliases.get(runtime, runtime)
    
    browsertype = None
    
    if runtime == 'xul':
        Runtime = XulRuntime
    elif runtime == 'nodewebkit':
        Runtime = NodeWebkitRuntime
    elif runtime == 'browser':
        Runtime = BrowserRuntime
    elif runtime.startswith('browser-'):
        Runtime = BrowserRuntime
        browsertype = runtime.split('-', 1)[1]
    else:
        raise ValueError('Unknown html5 runtime %r.' % runtime)
    
    
    return Runtime(url=url, title=title, size=size, pos=pos, icon=icon, 
                   browsertype=browsertype)
