"""
Automatic test for dialite. There's not that much code, really, so the manual
test is way more important...
"""

import os
import sys

from flexx.util.testing import raises

from flexx import dialite
from flexx.dialite import BaseApp, StubApp, WindowsApp, LinuxApp, OSXApp


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


def test_all_backends_are_complete():
    
    for cls in (StubApp, WindowsApp, LinuxApp, OSXApp):
        assert issubclass(cls, BaseApp)
        for name in dir(BaseApp):
            if name.startswith('_'):
                continue
            # Check that all methods are overloaded
            assert getattr(cls, name) is not getattr(BaseApp, name)


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


def test_unsupported_platform():
    
    o_platform = sys.platform
    o_stdin = sys.stdin
    o_app = dialite._the_app
    sys.platform = 'meh'
    sys.stdin = None
    
    try:
        
        if not os.getenv('CI'):
            assert dialite.is_supported()
        
        app = dialite._select_app()
        assert isinstance(app, StubApp)
        dialite._the_app = app
        
        assert not dialite.is_supported()
        
        # with raises(SystemExit):
        #     dialite.inform()
        dialite.inform()  # no problem
        
        # with raises(SystemExit):
        #     dialite.warn()
        dialite.warn()  # no problem
        
        with raises(SystemExit):
            dialite.fail()
        
        with raises(SystemExit):
            dialite.ask_ok()
        
        with raises(SystemExit):
            dialite.ask_retry()
            
        with raises(SystemExit):
            dialite.ask_yesno()
    
    except SystemExit:
        # mmm, SystemExit can fall through silently under certain circumstances
        # in an interactive IDE
        raise RuntimeError('Test tried to exit!')
    
    finally:
        sys.platform = o_platform
        sys.stdin = o_stdin
        dialite._the_app = o_app


if __name__ == '__main__':
    test_all_backends_are_complete()
    test_main_funcs()
    test_unsupported_platform()
