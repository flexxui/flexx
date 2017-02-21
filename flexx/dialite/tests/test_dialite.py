"""
Automatic test for dialite. There's not that much code, really, so the manual
test is way more important...
"""

import os
import sys
import webbrowser

from flexx.util.testing import raises, run_tests_if_main
from flexx.util.logging import capture_log

from flexx import dialite
from flexx.dialite import BaseApp, StubApp
from flexx.dialite import TerminalApp, WindowsApp, LinuxApp, OSXApp


class FakeStdin(object):
    
    answer = 'y'
    
    def isatty(self):
        return True
    
    def readline(self):
        return self.answer


class FakeWindowsApp(WindowsApp):
    
    def __init__(self, *args, **kwargs):
        self._messages = []
        super().__init__(*args, **kwargs)
    
    def _message(self, type, *args, **kwargs):
        self._messages.append(type)
        return True


class FakeLinuxApp(LinuxApp):
    
    def __init__(self, *args, **kwargs):
        self._messages = []
        super().__init__(*args, **kwargs)
    
    def _message(self, type, *args, **kwargs):
        self._messages.append(type)
        return True


class FakeOSXApp(OSXApp):
    
    def __init__(self, *args, **kwargs):
        self._messages = []
        super().__init__(*args, **kwargs)
    
    def _message(self, type, *args, **kwargs):
        self._messages.append(type)
        return True


class NoopApp(BaseApp):
    """ An application class that does nothing.
    """
    
    def __init__(self):
        self.res = []
    
    def fail(self, title, message):
        self.res.append(title)
        return True
    
    def warn(self, title, message):
        self.res.append(title)
        return True
    
    def inform(self, title, message):
        self.res.append(title)
        return True
    
    def ask_ok(self, title, message):
        self.res.append(title)
        return True
    
    def ask_retry(self, title, message):
        self.res.append(title)
        return True
    
    def ask_yesno(self, title, message):
        self.res.append(title)
        return True


def test_check_output():
    retcode, out = dialite._base.check_output('cd', shell=True)
    assert retcode == 0


def test_all_backends_are_complete():
    
    for cls in (StubApp, WindowsApp, LinuxApp, OSXApp):
        assert issubclass(cls, BaseApp)
        for name in dir(BaseApp):
            if name.startswith('_'):
                continue
            # Check that all methods are overloaded
            assert getattr(cls, name) is not getattr(BaseApp, name)


def test_get_app():
    
    app1 = dialite._get_app()
    app2 = dialite._get_app()
    app3 = dialite._get_app(True)
    app4 = dialite._get_app()
    assert app1 is app2
    assert app3 is app4
    assert app1 is not app3
    assert type(app1) is type(app3)


def test_context_manager():
    
    app1 = dialite._get_app()
    with dialite.NoDialogs():
        app2 = dialite._get_app()
    app3 = dialite._get_app()
    
    assert app1 is app3
    assert app1 is not app2
    assert isinstance(app2, StubApp)


def test_main_funcs():
    o_app = dialite._the_app
    
    try:
        
        # No args
        dialite._the_app = app = NoopApp()
        for func in (dialite.inform, dialite.warn, dialite.fail,
                     dialite.ask_ok, dialite.ask_retry, dialite.ask_yesno):
            func()
        #
        assert app.res == ['Info', 'Warning', 'Error',
                           'Confirm', 'Retry', 'Question']
        
        # With args
        dialite._the_app = app = NoopApp()
        for func in (dialite.inform, dialite.warn, dialite.fail,
                     dialite.ask_ok, dialite.ask_retry, dialite.ask_yesno):
            func(func.__name__, 'meh bla')
        #
        assert app.res == ['inform', 'warn', 'fail',
                           'ask_ok', 'ask_retry', 'ask_yesno']
        
        # Fails
        for func in (dialite.inform, dialite.warn, dialite.fail,
                     dialite.ask_ok, dialite.ask_retry, dialite.ask_yesno):
            with raises(TypeError):
                func(3, 'meh')
            with raises(TypeError):
                func('meh', 3)
            with raises(TypeError):
                func('meh', 'bla', 'foo')  # need exactly two args
    
    finally:
        dialite._the_app = o_app


def test_windows():
    """ Pretend that this is Windows. """
    
    o_platform = sys.platform
    o_app = dialite._the_app
    sys.platform = 'win32'
    
    try:
        
        app = FakeWindowsApp()
        # assert app.works()
        assert isinstance(app, WindowsApp)
        dialite._the_app = app
        
        assert dialite.is_supported()
        
        dialite.inform()
        assert len(app._messages) == 1
        
        dialite.warn()
        assert len(app._messages) == 2
        
        dialite.fail()
        assert len(app._messages) == 3
        
        assert dialite.ask_ok()
        assert len(app._messages) == 4
        
        assert dialite.ask_retry()
        assert len(app._messages) == 5
        
        assert dialite.ask_yesno()
        assert len(app._messages) == 6
    
    finally:
        sys.platform = o_platform
        dialite._the_app = o_app


def test_linux():
    """ Pretend that this is Linux. """
    
    o_platform = sys.platform
    o_app = dialite._the_app
    sys.platform = 'linux'
    
    try:
        
        app = FakeLinuxApp()
        # assert app.works()
        assert isinstance(app, LinuxApp)
        dialite._the_app = app
        
        assert dialite.is_supported()
        
        dialite.inform()
        assert len(app._messages) == 1 and 'info' in app._messages[-1]
        
        dialite.warn()
        assert len(app._messages) == 2 and 'warn' in app._messages[-1]
        
        dialite.fail()
        assert len(app._messages) == 3 and 'error' in app._messages[-1]
        
        assert dialite.ask_ok()
        assert len(app._messages) == 4 and 'question' in app._messages[-1]
        
        assert dialite.ask_retry()
        assert len(app._messages) == 5 and 'question' in app._messages[-1]
        
        assert dialite.ask_yesno()
        assert len(app._messages) == 6 and 'question' in app._messages[-1]
    
    finally:
        sys.platform = o_platform
        dialite._the_app = o_app


def test_osx():
    """ Pretend that this is OS X. """
    
    o_platform = sys.platform
    o_app = dialite._the_app
    sys.platform = 'darwin'
    
    try:
        
        app = FakeOSXApp()
        # assert app.works()
        assert isinstance(app, OSXApp)
        dialite._the_app = app
        
        assert dialite.is_supported()
        
        dialite.inform()
        assert len(app._messages) == 1
        
        dialite.warn()
        assert len(app._messages) == 2
        
        dialite.fail()
        assert len(app._messages) == 3
        
        assert dialite.ask_ok()
        assert len(app._messages) == 4
        
        assert dialite.ask_retry()
        assert len(app._messages) == 5
        
        assert dialite.ask_yesno()
        assert len(app._messages) == 6
    
    finally:
        sys.platform = o_platform
        dialite._the_app = o_app


def test_unsupported_platform1():
    """ Unsupported platform, fallback to terminal. """
    
    o_platform = sys.platform
    o_stdin = sys.stdin
    o_app = dialite._the_app
    
    sys.platform = 'meh'
    
    sys.stdin = FakeStdin()
    
    try:
        
        app = dialite._get_app(True)
        assert app.works()
        assert isinstance(app, TerminalApp)
        
        assert dialite.is_supported()
        
        with capture_log('info') as log:
            dialite.inform()
        assert len(log) == 1 and '[I' in log[0]
        
        with capture_log('info') as log:
            dialite.warn()  # no problem
        assert len(log) == 1 and '[W' in log[0]
        
        with capture_log('info') as log:
            dialite.fail()
        assert len(log) == 1 and '[E' in log[0]
        
        assert dialite.ask_ok()
        assert dialite.ask_retry()
        assert dialite.ask_yesno()
        
        sys.stdin.answer = 'no'
        assert not dialite.ask_ok()
        assert not dialite.ask_retry()
        assert not dialite.ask_yesno()
    
    finally:
        sys.platform = o_platform
        sys.stdin = o_stdin
        dialite._the_app = o_app


def test_unsupported_platform2():
    """ Unsupported platform, and also no terminal. """
    
    o_platform = sys.platform
    o_stdin = sys.stdin
    o_app = dialite._the_app
    o_open = webbrowser.open
    
    sys.platform = 'meh'
    sys.stdin = None
    webbrowser.open = lambda x:None
    
    try:
        
        app = dialite._get_app(True)
        assert app.works()
        assert isinstance(app, StubApp)
        
        assert not dialite.is_supported()
        
        dialite.inform()  # no problem
        
        dialite.warn()  # no problem
        
        dialite.fail()  # no problem
        # with raises(SystemExit):
        #     dialite.fail()
        
        with raises(SystemExit):
            dialite.ask_ok()
        
        with raises(SystemExit):
            dialite.ask_retry()
            
        with raises(SystemExit):
            dialite.ask_yesno()
    
    finally:
        sys.platform = o_platform
        sys.stdin = o_stdin
        dialite._the_app = o_app
        webbrowser.open = o_open


run_tests_if_main()
