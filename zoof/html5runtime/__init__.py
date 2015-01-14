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
* browser-ff - launch firefox browser
* browser-chrome - launch chrome/chromium browser
* browser-ie - launch Internet Explorer


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


def launch(url, runtime=None, 
           title='', size=(640, 480), pos=None, icon=None):
    """ Launch an html5 runtime in a new process
    
    Returns an object that can be used to influence the runtime.
    """
    
    return XulRuntime(url=url, title=title, size=size, pos=pos, icon=icon)
