# -*- coding: utf-8 -*-
# Copyright (c) 2014, Almar Klein
#
# This file is distributed under the terms of the (new) BSD License.

""" Module that serves as a proxy for loading Qt libraries.

This module has several goals:
  * Import QtCore, QtGui, etc. from PyQt5, PyQt4 or PySide (whichever
    is available).
  * Fix some incompatibilities between the two.
  * For applications that bring their own Qt libs, avoid clashes.

To use do ``from zoof.qt import QtCore, QtGui``. Note that this proxy
package is designed to be portable; it should be possible to use it in
your own application or library.

To use in frozen applications, create a qt.conf next to the executable,
that has text as specified in DEFAULT_QT_CONF_TEXT. By modifying the 
text, preferences can be changed.


Notes
-----

To prevent colliding of Qt libs when an app brings its own libs, in
particular on KDE, the plugins of Qt should be disabled. This needs
to be done in two places:
  * via qt.conf "Plugins = ''"
  * set the QT_PLUGIN_PATH variable to empty string

The latter is equivalent to QtGui.QApplication.setLibraryPaths([]),
but has the advantage that it can be set beforehand.

A downside of the plugins being disabled is that the native style
(GTK+, Oxygen) cannot be used and other features (Unity integrated
toolbar) are not available.

"""

import sys
import os
import imp
import importlib

VERBOSE = False



def qt_name():
    """ Return the name of the Qt lib in use: 'PyQt5', 'PyQt4',
    'PySide', or None.
    """
    try:
        importer_instance._import_qt()
    except ImportError:
        pass
    else:
        return importer_instance._qtPackage.__name__



def loadWidget(filename, parent=None):
    """ Load a widget from a .ui file. Returns a QWidget object.
    """
    
    # Note that PyQt4 has PyQt4.uic.loadUi(filename, basewidget)
    # allowing the newly created widget to inherit from a given widget
    # instance. This is not supported in PySide and therefore not
    # suported by this function.
    
    # Check
    if not os.path.isfile(filename):
        raise ValueError('Filename in loadWidget() is not a valid file.')
    
    if qt_name().lower() == 'pyside':
        # Import (from PySide import QtCore, QtUiTools)
        QtCore = importer_instance.load_module('QtCore')
        QtUiTools = importer_instance.load_module('QtUiTools')
        # Create loader and load widget
        loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(filename)
        uifile.open(QtCore.QFile.ReadOnly)
        w = loader.load(uifile, parent)
        uifile.close()
        return w
    else:
        # Import (from PyQt4 import QtCore, uic)
        QtCore = importer_instance.load_module('QtCore')
        uic = importer_instance.load_module('uic')
        # Load widget
        w = uic.loadUi(filename)
        # We set the parent explicitly
        if parent is not None:
            w.setParent(parent)
        return w



class QtProxyImporter:
    """ Importer to import Qt modules, either from PySide or from PyQt,
    and either from this Python's version, or the system ones (if
    available and matching).
    """
    
    def __init__(self):
        self._qtPackage = None
        self._enabled = True
    
    
    def find_module(self, fullname, path=None):
        """ This is called by Python's import mechanism. We return ourself
        only if this really looks like a Qt import, and when its imported
        as a submodule from this stub package.
        """
        
        # Only proceed if we are enabled
        if not self._enabled:
            return None
        
        # Get different parts of the module name
        nameparts = fullname.split('.') 
        
        # sip is required by PyQt
        if fullname == 'sip':
            self._import_qt()
            return self
        
        # If the import is relative to this package, we will try to
        # import relative to the selected qtPackage
        if '.'.join(nameparts[:-1]) == __name__:
            self._import_qt()
            return self
    
    
    def load_module(self, fullname):
        """ This method is called by Python's import mechanism after
        this instance has been returned from find_module. Here we
        actually import the module and do some furher processing.
        """
        
        # Get different parts of the module name
        nameparts = fullname.split('.') 
        modulename = nameparts[-1]
        
        # We can only proceed if qtPackage was loaded
        if self._qtPackage is None:
            raise ImportError()
        
        # Get real name and path to load it from    
        if fullname == self._qtPackage.__name__:
            return self._qtPackage
        elif fullname == 'sip':
            realmodulename = 'sip'
        elif modulename.startswith('Qt') or modulename == 'uic':
            realmodulename = '%s.%s' % (self._qtPackage.__name__, modulename)
        else:
            raise ImportError()
        
        # Module can be inside a zip-file when frozen
        # Import normally, and disable ourselves so we do not recurse
        if VERBOSE: print('load_module normally: %s' % realmodulename)
        self._enabled = False
        try:
            p = __import__(realmodulename)
        finally:
            self._enabled = True
        # Get the actual modele
        if '.' in realmodulename:
            m = getattr(p, modulename)
        else:
            m = p
        
        # Also register in sys.modules under the name as it was imported
        sys.modules[realmodulename] = m
        sys.modules[fullname] = m
        
        # Fix some compatibility issues
        self._fix_compat(m)
        
        # Done
        return m
    
    
    def _determine_preference(self):
        """ Determine preference by reading from qt.conf.
        """
        
        # Get dirs to look for qt.conf
        dirs = []
        script_dir = ''
        if sys.path and sys.path[0]:
            scriptdir = sys.path[0]
            if getattr(sys, 'frozen', None):
                scriptdir = os.path.dirname(scriptdir)
            dirs.append(os.path.abspath(scriptdir))
        dirs.append(os.path.dirname(sys.executable))
        
        # Read qt.conf
        for dir in dirs:
            qt_conf = os.path.join(dir, 'qt.conf')
            if os.path.isfile(qt_conf):
                text = open(qt_conf, 'rb').read().decode('utf-8', 'ignore')
                break
        else:
            text = ''
        
        # Parse qt.conf
        prefer_toolkit = ''
        #
        for line in text.splitlines():
            line = line.split('#',1)[0].strip()
            if '=' not in line:
                continue
            key, val = [i.strip() for i in line.split('=', 1)]
            if key == 'PreferToolkit':
                prefer_toolkit = val
        
        return prefer_toolkit
    
    
    def _import_qt(self, toolkit=None):
        """ This is where we import either PyQt5, PyQt4 or PySide.
        This is done only once.
        """
        
        # Make qtPackage global and only proceed if its not set yet
        if self._qtPackage is not None:
            return
        
        # Establish preference
        prefer_toolkit = self._determine_preference()
        
        # Check toolkit, use pyside by default
        prefer_toolkit = toolkit or prefer_toolkit or 'PyQt4'
        if prefer_toolkit.lower() not in ('pyqt5', 'pyqt4', 'pyside'):
            prefer_toolkit = 'pyqt4'
            print('Invalid Qt toolit preference given: "%s"' % prefer_toolkit)
        
        # Really import
        self._qtPackage = self._import_qt_for_real(prefer_toolkit)
        
        # Disable plugins if necessary
        if self._qtPackage and sys.platform.startswith('linux'):
            if not self._qtPackage.__file__.startswith('/usr'):
                os.environ['QT_PLUGIN_PATH'] = ''
    
    
    def _import_qt_for_real(self, prefer_toolkit):
        """ The actual importing.
        """
        
        # Perhaps it is already loaded
        if 'PyQt5' in sys.modules:
            return sys.modules['PyQt5']
        elif 'PyQt4' in sys.modules:
            return sys.modules['PyQt4']
        elif 'PySide' in sys.modules:
            return sys.modules['PySide']
        
        # Combine imports in right order
        if 'pyqt5' == prefer_toolkit.lower():
            imports = 'PyQt5', 'PyQt4', 'PySide'
        elif 'pyqt4' == prefer_toolkit.lower():
            imports = 'PyQt4', 'PyQt5', 'PySide'
        elif 'pyside' == prefer_toolkit.lower():
            imports = 'PySide', 'PyQt4', 'PyQt5'
        else:
            imports = 'PyQt5', 'PyQt4', 'PySide'
        
        # Try importing
        package = None
        for package_name in imports:
            if VERBOSE: print('Attempting to import %s' % package_name)
            try:
                return __import__(package_name, level=0)
            except ImportError as err:
                if VERBOSE: print('Import failed')
        else:
            raise ImportError('Could not import PySide nor PyQt4.')
    
    
    def _fix_compat(self, m):
        """ Fix incompatibilities between PySide and PyQt4. 
        """
        if self._qtPackage.__name__ == 'PySide':
            pass
        else:
            if m.__name__.endswith('QtCore'):
                m.Signal = m.pyqtSignal
        
        # todo: more compat, like uic loading


importer_instance = QtProxyImporter()
sys.meta_path.insert(0, importer_instance)




DEFAULT_QT_CONF_TEXT = """## This file contains configuration options for Qt.
## It disables plugins so that an application that brings its own 
## Qt libraries do not clashs with the native Qt. It also has options
## that the pyzolib.qt proxy uses to allow you to use your system
## PySide/PyQt4 libraries.

[Py]

## Preferred toolkit: PyQt5, PyQt4, or PySide
PreferToolkit = PyQt4

## Uncomment if pyzolib.qt should try to use the system libraries
## Note that you version of Python must be ABI compatible with the
## version on your system for this to work
#PreferSystem = yes


[Paths]

## This disables plugins, avoiding Qt library clashes
Plugins = ''

## On Ubuntu Unity, if PreferSystem is enabled, uncomment this to
## enable the fancy menu bar.
#Plugins = /usr/lib/x86_64-linux-gnu/qt4/plugins

"""
