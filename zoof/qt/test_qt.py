""" Tests for zoof.qt
"""

import os
import sys
import tempfile

import pytest
from zoof.lib.testing import run_tests_if_main

import zoof.qt


def test_qt_preference():
    """ Test preference set in qt.conf """
    
    # Get importer instance to test
    importer = zoof.qt.QtProxyImporter()
    
    # Get location of qt.conf
    tempdir = tempfile.gettempdir()  # THE temp dir
    fname = os.path.join(tempdir, 'qt.conf')
    
    # Write text and modify sys.path to make importer find it
    text = zoof.qt.DEFAULT_QT_CONF_TEXT
    open(fname, 'wb').write(text.encode('utf-8'))
    sys.path.insert(0, tempdir)
    # Test
    try:
        pref = importer._determine_preference()
        assert pref == 'PyQt4'
    finally:
        os.remove(fname)
        sys.path.pop(0)
    
    # Again ...
    text = zoof.qt.DEFAULT_QT_CONF_TEXT.replace('= PyQt4', '= PySide')
    open(fname, 'wb').write(text.encode('utf-8'))
    sys.path.insert(0, tempdir)
    # Test
    try:
        pref = importer._determine_preference()
        assert pref == 'PySide'
    finally:
        os.remove(fname)
        sys.path.pop(0)

sys._called = 0
def test_qt_importing():
    """ Test import triaging for qt proxy """
    # Get importer instance to test
    importer = zoof.qt.QtProxyImporter()
    
    # Test that a module that is already imported gets preferred
    orig_modules = sys.modules
    try:
        sys.modules = {'PyQt5': 'DUMMY_QT_MODULE_PYQT5'}
        assert importer._import_qt_for_real('') == 'DUMMY_QT_MODULE_PYQT5'
        sys.modules = {'PyQt4': 'DUMMY_QT_MODULE_PYQT4'}
        assert importer._import_qt_for_real('') == 'DUMMY_QT_MODULE_PYQT4'
        sys.modules = {'PySide': 'DUMMY_QT_MODULE_PYSIDE'}
        assert importer._import_qt_for_real('') == 'DUMMY_QT_MODULE_PYSIDE'
    finally:
        sys.modules = orig_modules
    
    # Test that preference is considered
    def stub_import1(modulename, **kwargs):
        return 'SUCCESS ' + modulename
    def stub_import2(modulename, **kwargs):
        raise ImportError()
    orig_modules = sys.modules
    try:
        sys.modules = {}
        # Simulate that any module will work
        zoof.qt.__import__ = stub_import1
        assert importer._import_qt_for_real('PyQt5') == 'SUCCESS PyQt5'
        assert importer._import_qt_for_real('PyQt4') == 'SUCCESS PyQt4'
        assert importer._import_qt_for_real('PySide') == 'SUCCESS PySide'
        # Simulate no module will work
        zoof.qt.__import__ = stub_import2
        pytest.raises(ImportError, importer._import_qt_for_real, '')
    finally:
        sys.modules = orig_modules
        zoof.qt.__import__ = __import__


# todo: this tests needs qt (the above tests do not)
def test_plain():
    """ Test just importing qt via zoof.qt """
    # This should take care of a great deal of coverage
    from zoof.qt import QtCore


run_tests_if_main()
