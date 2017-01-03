"""
Flexx is a pure Python toolkit for creating graphical user interfaces
(GUI's), that uses web technology for its rendering. Apps are written
purely in Python; Flexx' transpiler generates the necessary JavaScript
on the fly.

You can use Flexx to create (cross platform) desktop applications, web
applications, and (if designed well) export an app to a standalone HTML
document. It also works in the Jupyter notebook.

The docs are on `Readthedocs <http://flexx.readthedocs.io>`_,
the code is on `Github <http://github.com/zoofio/flexx>`_,
and there is a `demo server on AWS <http://flexx1.zoof.io>`_
and `another on a Raspberry pi <http://flexx2.zoof.io>`_.
Flexx is currently in alpha status; any part of the public API may
change without notice. Feedback is welcome.

----

Flexx has a modular design, consisting of a few subpackages, which can
also be used by themselves:

* flexx.ui - the widgets
* flexx.app - the event loop and server
* flexx.event - properties and events
* flexx.pyscript - Python to JavaScript transpiler
* flexx.webruntime - to launch a runtime
* flexx.util - utilities

For more information, see http://flexx.readthedocs.io.
"""

# NOTES ON DOCS:
# There are 2 places that define the short summary of Flexx: the
# __init__.py and the README.md. Their summaries should be kept equal.
# The index.rst for the docs uses the summary from __init__.py (the
# part after the "----" is stripped. The long-description for Pypi is
# obtained by converting README.md to RST.

__version__ = '0.4.1-dev'


# Assert compatibility and redirect to legacy version on Python 2.7
import sys
ok = True
if sys.version_info[0] == 2:  # pragma: no cover
    if sys.version_info < (2, 7):
        raise RuntimeError('Flexx needs at least Python 2.7')
    if type(b'') == type(''):  # noqa - will be str and unicode after conversion
        sys.modules[__name__] = __import__(__name__ + '_legacy')
        ok = False

# Import config object
if ok:
    from ._config import config  # noqa
    from .util.logging import set_log_level  # noqa
    set_log_level(config.log_level)
    
del sys, ok
