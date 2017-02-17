
import os
import time
import tempfile
import subprocess

from flexx.util import icon

from flexx.util.testing import run_tests_if_main, raises, skipif

from flexx.webruntime import BaseRuntime
from flexx.webruntime import launch
from flexx import webruntime


URL = None

HTML = """
<html>
<head>
<meta charset="utf-8">
<style>
    body {background: #00aa00;}
</style>
</head
<body></body>
</html>
"""


def setup_module():
    global URL, FILE
    fname = os.path.join(tempfile.gettempdir(), 'flexx_testpage.html')
    with open(fname, 'wb') as f:
        f.write(HTML.encode())
    URL = 'file://' + fname


def has_qt():
    try:
        from PyQt4 import QtWebKit
    except ImportError:
        try:
            from PySide import QtWebKit
        except ImportError:
            return False
    return True


def has_nw():
    return webruntime.NWRuntime().is_available()


def has_chrome():
    return webruntime.ChromeRuntime().is_available()


## Misc

def test_iconize():

    # Default icon
    icn = webruntime._common.iconize(None)
    assert isinstance(icn, icon.Icon)

    fname = os.path.join(tempfile.gettempdir(), 'flexx_testicon.ico')
    icn.write(fname)

    # Load from file
    icn = webruntime._common.iconize(fname)
    assert isinstance(icn, icon.Icon)

    # Load from icon (noop)
    assert webruntime._common.iconize(icn) is icn

    # Error
    raises(ValueError, webruntime._common.iconize, [])


## Runtimes


@skipif(not has_qt(), reason='need qt')
def test_qtwebkit():
    p = launch(URL, 'pyqt-app')
    assert p._proc
    p.close()


def test_xul():
    p = launch(URL, 'firefox-app')
    assert p._proc

    p.close()
    p.close()  # should do no harm


@skipif(not has_nw(), reason='need nw')
def test_nwjs():
    p = launch(URL, 'nw-app')
    assert p._proc
    p.close()


@skipif(not has_chrome(), reason='need chrome/chromium')
def test_chomeapp():
    p = launch(URL, 'chrome-app')
    assert p._proc
    p.close()


def test_browser():
    p = launch(URL, 'default-browser')
    assert p._proc is None


def test_browser_ff():
    p = launch(URL, 'firefox-browser')
    assert p._proc is None


#@skipif(os.getenv('TRAVIS') == 'true', reason='skip selenium on Travis')
@skipif(True, reason='meh selenium')
def test_selenium():
    p = launch(URL, 'selenium-firefox')
    assert p._proc is None
    assert p.driver
    time.sleep(0.5)
    p.close()
    raises(ValueError, launch, URL, 'selenium')


def test_unknown():
    # Suppress dialog temporarily
    from flexx import dialite
    with dialite.NoDialogs():
        raises(ValueError, launch, URL, 'foo')


def test_default():
    p = launch(URL)
    assert p.__class__.__name__ == 'FirefoxRuntime'
    p.close()


run_tests_if_main()
