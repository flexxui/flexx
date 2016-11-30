""" This tests the Model class.
"""

from flexx.util.testing import run_tests_if_main, raises

import weakref
import gc
import logging
import tornado

from flexx.app._model import Model, _get_active_models
from flexx import event, app

class Foo1(Model):
    
    @event.prop
    def title(self, v=''):
        return v
    
    class JS:
        
        @event.prop
        def blue(self, v=0):
            return v

class Foo2(Foo1):
    
    class JS:
        
        @event.prop
        def red(self, v=0):
            return v


class Foo3(Foo2):
    py_attr = 42
    
    @event.prop
    def js_attr(self, v=0):
        return v
    
    class JS:
        js_attr = 42
        
        @event.prop
        def py_attr(self, v=0):
            return v

class Foo4(Foo3):
    
    @event.prop
    def title(self, v=''):
        return v + 'x'
    
    class JS:
        
        @event.prop
        def red(self, v=0):
            return v+1

class Foo5(Foo4):
    
    class Both:
        
        @event.prop
        def red(self, v=0):
            return v+1
        
        @event.prop
        def blue(self, v=0):
            return v+1
        
        @event.prop
        def purple(self, v=0):
            return v+1


class Foo6(Foo1):
    
    class JS:
        
        @event.emitter
        def my_awesome_event(self, x):
            """ docs on awesome event. """
            return {}


class Foo7(Model):
    
    def init(self, foo, bar=0):
        self.foo = foo
        self.bar = bar


def test_pairing1():
    
    assert isinstance(Foo1.title, event._emitters.Property)
    assert not hasattr(Foo1, 'blue')
    
    assert not hasattr(Foo1.JS, 'title')
    assert isinstance(Foo1.JS.blue, event._emitters.Property)


def test_no_clashes():
    
    # Attributes that already exist are not overwritten
    assert Foo3.py_attr == 42
    assert Foo3.JS.js_attr == 42
    
    assert isinstance(Foo3.js_attr, event._emitters.Property)
    assert isinstance(Foo3.JS.py_attr, event._emitters.Property)
    
    # Double check in subclass
    assert Foo4.py_attr == 42
    assert Foo4.JS.js_attr == 42
    
    assert isinstance(Foo4.js_attr, event._emitters.Property)
    assert isinstance(Foo4.JS.py_attr, event._emitters.Property)


def test_overloading():
    
    assert Foo2.title is Foo1.title
    assert Foo3.JS.red is Foo2.JS.red
    
    assert Foo4.title is not Foo1.title
    assert Foo4.JS.red is not Foo2.JS.red


def test_init_args():
    
    # This test needs a default session
    session = app.manager.get_default_session()
    if session is None:
        app.manager.create_default_session()
    
    with raises(TypeError):
        m = Model(2, 3)
    
    m = Foo7(2, 3)
    assert m.foo == 2
    assert m.bar == 3
    
    m = Foo7(2)
    assert m.foo == 2
    assert m.bar == 0
    
    with raises(TypeError):
        m = Foo7()
    
    with raises(TypeError):
        m = Foo7(2, 3, 4)


def test_both():
    # New prop
    assert Foo5.purple is Foo5.JS.purple
    # Overloaded existing props
    assert Foo5.red is Foo5.JS.red
    assert Foo5.blue is Foo5.JS.blue
    
    # But this fails
    
    with raises(TypeError):
        
        class Foo5_wrong1(Foo4):
            
            @event.prop
            def purple(self, v=0):
                return v+1
            
            class Both:
                
                @event.prop
                def purple(self, v=0):
                    return v+1
    
    with raises(TypeError):
        
        class Foo5_wrong2(Foo4):
            
            class JS:
                @event.prop
                def purple(self, v=0):
                    return v+1
            
            class Both:
                
                @event.prop
                def purple(self, v=0):
                    return v+1


def test_emitters_in_JS():
    # Emitters in JS get a dummy emitter in Py
    assert Foo6.my_awesome_event
    assert 'docs on awesome' in Foo6.my_awesome_event.__doc__
    

    with raises(RuntimeError):
        Foo6.my_awesome_event._func(None)


def test_no_duplicate_code():
    assert '.blue.' in Foo1.JS.CODE
    assert '.blue.' not in Foo2.JS.CODE
    assert '.blue.' not in Foo4.JS.CODE
    
    assert '.red.' not in Foo1.JS.CODE
    assert '.red.' in Foo2.JS.CODE
    assert '.red.' in Foo4.JS.CODE


def test_active_models():
    
    ioloop = app.create_server(port=0, new_loop=True).loop
    
    # This test needs a default session
    session = app.manager.get_default_session()
    if session is None:
        app.manager.create_default_session()
    
    # Test that by default there are no active models
    m = Model()
    assert not _get_active_models()
    
    # Test that model is active in its context
    with m:
        assert _get_active_models() == [m]
    
    # Can do this
    ioloop.run_sync(lambda x=None: None)
    
    
    class PMHandler(logging.Handler):
        def emit(self, record):
            if record.exc_info:
                self.last_type, self.last_value, self.last_traceback = record.exc_info
            return record
    
    handler = PMHandler()
    app.logger.addHandler(handler)
    
    # Test that we prevent going back to Tornado in context
    handler.last_type = None
    with m:
        assert _get_active_models() == [m]
        # This raises error, but gets caught by Tornado
        ioloop.run_sync(lambda x=None: None)
    assert handler.last_type is RuntimeError
    assert 'risk on race conditions' in str(handler.last_value)


class EmitInInit(app.Model):
    
    def init(self):
        self.res1 = []
        self.res2 = []
        self.emit('foo')
        self.emit('foo')
    
    @event.prop
    def bar(self, v=1):
        return v
    
    @event.connect('foo')
    def on_foo(self, *events):
        self.res1.append(len(events))
    
    @event.connect('bar')
    def on_bar(self, *events):
        self.res2.append(len(events))

def test_can_emit_in_init():
    m = EmitInInit()
    m.on_foo.handle_now()
    m.on_bar.handle_now()
    
    assert m.res1 == [2]
    assert m.res2 == [1]


def test_keep_alive():
    
    session = app.manager.get_default_session()
    if session is None:
        app.manager.create_default_session()
    
    class Foo:
        pass
    
    foo1, foo2, foo3 = Foo(), Foo(), Foo()
    foo1_ref = weakref.ref(foo1)
    foo2_ref = weakref.ref(foo2)
    foo3_ref = weakref.ref(foo3)
    
    session.keep_alive(foo1, 10)
    session.keep_alive(foo1, 5)  # should do nothing, longest time counts
    session.keep_alive(foo2, 5)
    session.keep_alive(foo2, 11)  # longest timeout counts
    session.keep_alive(foo3, 15)
    
    # Delete objects, session keeps them alive
    del foo1, foo2, foo3
    gc.collect()
    assert foo1_ref() is not None
    assert foo2_ref() is not None
    assert foo3_ref() is not None
    
    # Pong 4, too soon for the session to release the objects
    session._receive_pong(4)
    gc.collect()
    assert foo1_ref() is not None
    assert foo2_ref() is not None
    assert foo3_ref() is not None
    
    # Pong 7, still too soon
    session._receive_pong(7)
    gc.collect()
    assert foo1_ref() is not None
    assert foo2_ref() is not None
    assert foo3_ref() is not None
    
    # Pong 10, should remove foo1
    session._receive_pong(10)
    gc.collect()
    assert foo1_ref() is None
    assert foo2_ref() is not None
    assert foo3_ref() is not None
    
    # Pong 11, should remove foo2
    session._receive_pong(11)
    gc.collect()
    assert foo1_ref() is None
    assert foo2_ref() is None
    assert foo3_ref() is not None
    
    # Pong 20, should remove foo3
    session._receive_pong(20)
    gc.collect()
    assert foo1_ref() is None
    assert foo2_ref() is None
    assert foo3_ref() is None


def test_keep_alive_noleak1():
    
    class Foo:
        pass
    
    # Create a session and an object that has a reference to it (like Model)
    session = app.Session('test')
    foo = Foo()
    foo.session = session
    
    # Let the session keep the object alive, so it keeps its reference
    session.keep_alive(foo)
    
    session_ref = weakref.ref(session)
    foo_ref = weakref.ref(foo)
    
    # Removing object wont delete it
    del foo
    gc.collect()
    assert foo_ref() is not None
    
    # But closing the session will; session clears up after itself
    session.close()
    gc.collect()
    assert foo_ref() is None


def test_keep_alive_noleak2():
    # Even if the above would not work ...
    
    class Foo:
        pass
    
    # Create a session and an object that has a reference to it (like Model)
    session = app.Session('test')
    foo = Foo()
    foo.session = session
    
    # Let the session keep the object alive, so it keeps its reference
    session.keep_alive(foo)
    
    session_ref = weakref.ref(session)
    foo_ref = weakref.ref(foo)
    
    # Removing session wont delete it
    del session
    gc.collect()
    assert session_ref() is not None
    
    # But removing both will; gc is able to clear circular ref
    del foo
    gc.collect()
    assert session_ref() is None
    assert foo_ref() is None


run_tests_if_main()
