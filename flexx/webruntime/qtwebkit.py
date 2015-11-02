""" Web runtime based on qt-webkit. Requires PyQt4 or PySide.
"""

import os
import sys

from .common import DesktopRuntime, create_temp_app_dir

# Note that setting icon on Ubuntu (and possibly on other OS-es is broken for PyQt)

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
        try:
            from PyQt5 import QtCore, QtGui, QtWebKit, QtWidgets, QtWebKitWidgets
            qt = 'pyqt5'
        except ImportError:
            pass

if not qt:
    sys.exit('Cannot import Qt')

url = "{url}"
title = "{title}"
icon = "{icon}"
size = {size}
pos = {pos}

if qt != 'pyqt5':
    app = QtGui.QApplication([])
    m = QtWebKit.QWebView(None)
    
else:
    app = QtWidgets.QApplication([])
    m = QtWebKitWidgets.QWebView(None)

m.setUrl(QtCore.QUrl(url))
m.setWindowTitle(title)
if icon:
    i = QtGui.QIcon()
    i.addFile(icon, QtCore.QSize(16, 16))
    m.setWindowIcon(i)
if size:
    m.resize(*size)
if pos:
    m.move(*pos)

m.show()
app.exec_()
"""


class PyQtRuntime(DesktopRuntime):
    """ Desktop runtime based on qt-webkit. Launches a new Python
    process (the same version as the current), and uses PyQt4 or PySide
    to display the page.
    """
    _app_count = 0
    
    def _launch(self):
        
        # Write icon
        iconfile = ''
        self.__class__._app_count += 1
        if self._kwargs.get('icon'):
            app_path = create_temp_app_dir('qwebkit', str(self.__class__._app_count))
            icon = self._kwargs.get('icon')
            iconfile = os.path.join(app_path, 'icon.png')
            icon.write(iconfile)
        
        code = CODE_TO_RUN.format(url=self._kwargs['url'],
                                  title=self._kwargs.get('title', 'QWebkit runtime'),
                                  icon=iconfile,
                                  size=repr(self._kwargs.get('size', None)),
                                  pos=repr(self._kwargs.get('pos', None)),
                                  )
        self._start_subprocess([sys.executable, '-c', code])
