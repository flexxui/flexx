"""
Automatic test for dialite. There's not that much code, really, so the manual
test is way more important...
"""

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
    
    def verify(self, title, message):
        self.res.append(title)
        return True
    
    def ask(self, title, message):
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
                     dialite.verify, dialite.ask):
            func()
        #
        assert app.res == ['Info', 'Warning', 'Error', 'Verify', 'Question']
        
        # With args
        dialite._the_app = app = NoopApp()
        for func in (dialite.inform, dialite.warn, dialite.fail,
                     dialite.verify, dialite.ask):
            func(func.__name__, 'meh bla')
        #
        assert app.res == ['inform', 'warn', 'fail', 'verify', 'ask']
        
        # Fails
        for func in (dialite.inform, dialite.warn, dialite.fail,
                     dialite.verify, dialite.ask):
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
    o_app = dialite._the_app
    sys.platform = 'meh'
    
    try:
        
        assert dialite.is_supported()
        
        app = dialite._select_app()
        assert isinstance(app, StubApp)
        dialite._the_app = app
        
        assert not dialite.is_supported()
        
        with raises(RuntimeError):
            dialite.inform()
        
        with raises(RuntimeError):
            dialite.warn()
        
        with raises(RuntimeError):
            dialite.fail()
        
        with raises(RuntimeError):
            dialite.verify()
        
        with raises(RuntimeError):
            dialite.ask()
    
    finally:
        sys.platform = o_platform
        dialite._the_app = o_app
