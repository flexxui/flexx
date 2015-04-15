""" Web runtime based on qt-webkit. Requires PyQt4 or PySide.
"""

import sys
import time

from .common import WebRuntime

# todo: set size, pos, icon, title
# Note that this runtime could allow us a very high degree of control by
# e.g. passing commands through stdin.

CODE_TO_RUN = """
import sys

qt = None
try:
    from PyQt4 import QtCore, QtGui, QtWebKit
    qt = 'pyqt4'
except ImportError:
    try:
        from PySide import QtCore, QtGui, QtWebKit
        qt = 'pyside'
    except ImportError:
        pass

if not qt:
    sys.exit('Cannot import Qt')

url = "{url}"
app = QtGui.QApplication([])
m = QtWebKit.QWebView(None)
m.show()
m.setUrl(QtCore.QUrl(url))
app.exec_()
"""


class PyQtRuntime(WebRuntime):
    """ Web runtime based on qt-webkit.
    """
    
    def _launch(self):
        code = CODE_TO_RUN.format(url=self._kwargs['url'])
        self._start_subprocess([sys.executable, '-c', code])
