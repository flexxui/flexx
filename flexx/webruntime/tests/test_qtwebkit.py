
import pytest
from flexx.util.testing import run_tests_if_main

from flexx.webruntime import launch


def has_qt():
    try:
        from PyQt4 import QtWebKit
    except ImportError:
        try:
            from PySide import QtWebKit
        except ImportError:
            return False
    return True


@pytest.mark.skipif(not has_qt(), reason='need qt')
def test_qtwebkit():
    p = launch('http://google.com', 'pyqt')
    assert p._proc
    p.close()

run_tests_if_main()
