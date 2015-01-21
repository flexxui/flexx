""" Web runtime based on qt-webkit.
"""

import sys
import time

from .common import WebRuntime

# todo: set size, pos, icon, title
# Note that this runtime allows us a very high degree of control by
# e.g. passing commands through stdin.

CODE_TO_RUN = """
from zoof.qt import QtGui, QtCore, QtWebKit
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
