"""
Flexx is a pure Python toolkit for creating
graphical user interfaces (GUI's), that uses web technology for its
rendering. You can use Flexx to create desktop applications, web
applications, and (if designed well) export an app to a standalone HTML
document. It also works in the Jupyter notebook.

Being pure Python and cross platform, it should work anywhere where
there's Python and a browser. To run apps in desktop-mode, we recommend having Firefox
installed.

Flexx has a modular design, consisting of a few subpackages, which can
also be used by themselves:

* ui - the widgets
* app - the event loop and server
* react - reactive programming (how information flows through your program)
* pyscript - Python to JavaScript transpiler
* webruntime - to launch a runtime

For more information, see http://flexx.readthedocs.org.
"""

__version__ = '0.3.1'


# Assert compatibility and redirect to legacy version on Python 2.7
import sys
if sys.version_info[0] == 2:  # pragma: no cover
    if sys.version_info < (2, 7):
        raise RuntimeError('Flexx needs at least Python 2.7')
    if type(b'') == type(''):  # noqa - will be str and unicode after conversion
        sys.modules[__name__] = __import__(__name__ + '_legacy')

from flexx.util.config import Config
config = Config('flexx', '~appdata/.flexx.cfg',
                dummy=(0, int, 'Flexx does not have any config options yet')
                )

del sys, Config
