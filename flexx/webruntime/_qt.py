""" Web runtime based on qt-webkit. Requires PyQt4 or PySide.
"""

import os
import sys

from ._common import DesktopRuntime
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

# todo: maximized / fullscreen can certainly be implemented,
# but I don't care much about this runtime now, so I did not do it yet.


class PyQtRuntime(DesktopRuntime):
    """ Desktop runtime based on qt-webkit. Launches a new Python
    process (the same version as the current), and uses PyQt4, PyQt5 or PySide
    to display the page.
    
    This runtime is not suited for hosting apps created with flexx.ui; it is
    included for completeness but should generally be avoided.
    """
    
    def _get_name(self):
        return 'pyqt'
    
    def _get_install_instuctions(self):
        return ('To enable the Pyqt runtime, install Pyqt5, Pyqt4, '
                'Pyside2 or Pyside in your Python environment.')
    
    def _get_exe(self):
        return sys.executable
        # todo: perhaps we should test whether pyqt is available, but
        # don't want to do that by importing it... meeh, this runtime
        # is not that serious anyway.
    
    def _get_version(self):
        return None  # we could report the Qt version here (or pyqt version?)
    
    def _get_system_version(self):
        return None, None  # stub
    
    def _install_runtime(self, sys_path, dest_path):
        pass  # is never called
    
    def _launch_tab(self, url):
        raise RuntimeError('PyQt runtime cannot launch tabs.')
    
    def _launch_app(self, url):
        
        # We don't call self.get_runtime_dir() so we don't need to implement
        # _install_runtime()
        
        # Write icon - assume that we have a 16x16 icon
        app_path = create_temp_app_dir('pyqt')
        self._icon.write(os.path.join(app_path, 'icon.png'))
        iconfile = os.path.join(app_path, 'icon%i.png' % self._icon.image_sizes()[0])
        
        code = CODE_TO_RUN.format(url=repr(url),
                                  title=repr(self._title),
                                  icon=repr(iconfile),
                                  size=repr(self._size),
                                  pos=repr(self._pos),
                                  )
        self._start_subprocess([self.get_exe(), '-c', code])
