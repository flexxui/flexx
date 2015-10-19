
import os
import time
import tempfile
import subprocess

from flexx.util import icon

import pytest
from flexx.util.testing import run_tests_if_main

from flexx.webruntime.common import BaseRuntime
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
    open(fname, 'wt', encoding='utf-8').write(HTML)
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
    exe = webruntime.nodewebkit.get_nodewebkit_exe or 'nw'
    try:
        subprocess.check_call([exe, '--version'], shell=True)
    except Exception:
        return False
    return True


def has_chrome():
    return (webruntime.chromeapp.get_chrome_exe() or
            webruntime.chromeapp.get_chromium_exe())


## Misc

def test_iconize():

    # Default icon
    icn = webruntime.common.iconize(None)
    assert isinstance(icn, icon.Icon)

    fname = os.path.join(tempfile.gettempdir(), 'flexx_testicon.ico')
    icn.write(fname)

    # Load from file
    icn = webruntime.common.iconize(fname)
    assert isinstance(icn, icon.Icon)

    # Load from icon (noop)
    assert webruntime.common.iconize(icn) is icn

    # Error
    pytest.raises(ValueError, webruntime.common.iconize, [])


## Runtimes


@pytest.mark.skipif(not has_qt(), reason='need qt')
def test_qtwebkit():
    p = launch(URL, 'pyqt')
    assert p._proc
    p.close()


def test_xul():
    p = launch(URL, 'xul')
    assert p._proc

    p.close()
    p.close()  # should do no harm


@pytest.mark.skipif(not has_nw(), reason='need nw')
def test_nwjs():
    p = launch(URL, 'nwjs')
    assert p._proc
    p.close()


@pytest.mark.skipif(not has_chrome(), reason='need chrome/chromium')
def test_chomeapp():
    p = launch(URL, 'chromeapp')
    assert p._proc
    p.close()


def test_nodejs():
    code = 'console.log("hello!")'
    p = launch(URL, 'nodejs', code=code)
    assert p._proc
    p.close()


def test_browser():
    p = launch(URL, 'browser')
    assert p._proc is None


def test_browser_ff():
    p = launch(URL, 'browser-firefox')
    assert p._proc is None


def test_browser_fallback():
    p = launch(URL, 'browser-foo')
    assert p._proc is None


@pytest.mark.skipif(os.getenv('TRAVIS') == 'true', reason='skip selenium on Travis')
def test_selenium():
    p = launch(URL, 'selenium-firefox')
    assert p._proc is None
    assert p.driver
    time.sleep(0.5)
    p.close()
    pytest.raises(ValueError, launch, URL, 'selenium')


def test_unknown():
    pytest.raises(ValueError, launch, URL, 'foo')


def test_default():
    p = launch(URL)
    assert p.__class__.__name__ == 'XulRuntime'
    p.close()


def test_base_runtime_must_have_url_in_kwargs():
    with pytest.raises(KeyError) as excinfo:
        BaseRuntime()

    assert 'url' in str(excinfo.value)


run_tests_if_main()
