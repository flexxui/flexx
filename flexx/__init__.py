"""
`Flexx <https://flexx.readthedocs.io>`_ is a pure Python toolkit for
creating graphical user interfaces (GUI's), that uses web technology
for its rendering. Apps are written purely in Python; The
`PScript <https://pscript.readthedocs.io>`_ transpiler generates the
necessary JavaScript on the fly.

You can use Flexx to create (cross platform) desktop applications, web
applications, and export an app to a standalone HTML document. It also
works in the Jupyter notebook.

The docs are on `Readthedocs <http://flexx.readthedocs.io>`_,
the code is on `Github <http://github.com/flexxui/flexx>`_,
and there is a `demo server <http://demo.flexx.app>`_.
Once you've got started, the most important page is probably the
:doc:`Widget reference <ui/api>`.

----

For more information, see http://flexx.readthedocs.io.
"""

# NOTES ON DOCS:
# There are 2 places that define the short summary of Flexx: the
# __init__.py and the README.md. Their summaries should be kept equal.
# The index.rst for the docs uses the summary from __init__.py (the
# part after the "----" is stripped. The long-description for Pypi is
# obtained by converting README.md to RST.

__version__ = '0.8.0'

# Assert compatibility
import sys
if sys.version_info < (3, 5):  # pragma: no cover
    raise RuntimeError('Flexx needs at least Python 3.5')

# Import config object
from ._config import config  # noqa
from .util.logging import set_log_level  # noqa
set_log_level(config.log_level)

del sys
