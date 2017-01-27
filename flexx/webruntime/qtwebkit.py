""" Web runtime based on qt-webkit. Requires PyQt4 or PySide.
"""

import os
import sys

from .common import DesktopRuntime
from ._manage import create_temp_app_dir

# Note that setting icon on Ubuntu (and possibly on other OS-es is broken for PyQt)

# Note that this runtime could allow us a very high degree of control
# by e.g. passing commands through stdin. However, Qt webkit cannot
# render Flexx ui apps.

CODE_TO_RUN = """
import sys

qt = None
for iter in range(4):
    try:
        if iter == 0:
            from PyQt5 import QtCore, QtGui, QtWebKit, QtWidgets, QtWebKitWidgets
            qt = 'pyqt5'
        elif iter == 1:
            from PyQt4 import QtCore, QtGui, QtWebKit
            qt = 'pyqt4'
        elif iter == 2:
            from PySide import QtCore, QtGui, QtWebKit
            qt = 'pyside'
        elif iter == 3:
            from PySide2 import QtCore, QtGui, QtWebKit, QtWidgets, QtWebKitWidgets
            qt = 'pyside2'
        break
    except ImportError:
        pass

if not qt:
    sys.exit('Cannot import Qt')

url = {url}
title = {title}
icon = {icon}
size = {size}
pos = {pos}

if qt not in ['pyqt5', 'pyside2']:
    app = QtGui.QApplication([])
    m = QtWebKit.QWebView(None)
    
else:
    app = QtWidgets.QApplication([])
    m = QtWebKitWidgets.QWebView(None)

m.setUrl(QtCore.QUrl(url))
m.setWindowTitle(title + ' (%s)' % qt)
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
    process (the same version as the current), and uses PyQt4, PyQt5 or PySide
    to display the page.
    
    This runtime is not suited for hosting apps created with flexx.ui; it is
    included for completeness but should generally be avoided.
    """
    
    def _get_name(self):
        return 'pyqt'
    
    def _get_exe(self):
        return sys.executable
        # todo: perhaps we should test whether pyqt is available, but
        # don't want to do that by importing it... meeh, this runtime
        # is not that serious anyway.
    
    def _get_version(self):
        return None  # we could report the Qt version here (or pyqt version?)
    
    def _launch_tab(self, url):
        raise RuntimeError('PyQt runtime cannot launch tabs.')
    
    def _launch_app(self, url):
        
        # We don't call self.get_runtime() so we don't need to implement
        # _install_runtime()
        
        # Write icon
        iconfile = ''
        if self._kwargs.get('icon'):
            app_path = create_temp_app_dir('qwebkit')
            icon = self._kwargs.get('icon')
            iconfile = os.path.join(app_path, 'icon.png')
            icon.write(iconfile)
        
        code = CODE_TO_RUN.format(url=repr(url),
                                  title=repr(self._kwargs.get('title',
                                                              'QWebkit runtime')),
                                  icon=repr(iconfile),
                                  size=repr(self._kwargs.get('size', None)),
                                  pos=repr(self._kwargs.get('pos', None)),
                                  )
        self._start_subprocess([self.get_exe(), '-c', code])
