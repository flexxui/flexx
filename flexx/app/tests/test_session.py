from flexx.util.testing import run_tests_if_main, raises, skip

import gc
import sys
import weakref
import asyncio

from flexx import app
from flexx.app import Session
from flexx.app._assetstore import assets, AssetStore as _AssetStore


class AssetStore(_AssetStore):
    _test_mode = True


class Fooo1(app.PyComponent):
    x = 3


def test_session_basics():

    s = Session('xx')
    assert s.app_name == 'xx'
    assert 'xx' in repr(s)


def test_get_component_instance_by_id():
    # is really a test for the session, but historically, the test is done here

    # This test needs a default session
    session = app.manager.get_default_session()
    if session is None:
        session = app.manager.create_default_session()

    m1 = Fooo1()
    m2 = Fooo1()

    assert m1 is not m2
    assert session.get_component_instance(m1.id) is m1
    assert session.get_component_instance(m2.id) is m2
    assert session.get_component_instance('blaaaa') is None


def test_session_assets_data():

    store = AssetStore()
    store.add_shared_data('ww', b'wwww')
    s = Session('', store)
    s._send_command = lambda x: None
    assert s.id

    # Add data
    s.add_data('xx', b'xxxx')
    s.add_data('yy', b'yyyy')
    assert len(s.get_data_names()) == 2
    assert 'xx' in s.get_data_names()
    assert 'yy' in s.get_data_names()

    # get_data()
    assert s.get_data('xx') == b'xxxx'
    assert s.get_data('zz') is None
    assert s.get_data('ww') is b'wwww'

    # # Add url data
    # s.add_data('readme', 'https://github.com/flexxui/flexx/blob/master/README.md')
    # #assert 'Flexx is' in s.get_data('readme').decode()
    # assert s.get_data('readme').startswith('https://github')

    # Add data with same name
    with raises(ValueError):
        s.add_data('xx', b'zzzz')

    # Add BS data
    with raises(TypeError):
        s.add_data('dd')  # no data
    with raises(TypeError):
        s.add_data('dd', 4)  # not an asset
    if sys.version_info > (3, ):
        with raises(TypeError):
            s.add_data('dd', 'not bytes')
        with raises(TypeError):
            s.add_data(b'dd', b'yes, bytes')  # name not str
    with raises(TypeError):
        s.add_data(4, b'zzzz')  # name not a str

    # get_data()
    assert s.get_data('xx') is b'xxxx'
    assert s.get_data('ww') is store.get_data('ww')
    assert s.get_data('ww') == b'wwww'
    assert s.get_data('bla') is None


def test_session_registering_component_classes():
    try:
        from flexx import ui
    except ImportError:
        skip('no flexx.ui')

    store = AssetStore()
    store.update_modules()

    s = Session('', store)
    commands = []
    s._send_command = lambda x: commands.append(x)
    assert not s.present_modules

    s._register_component_class(ui.Button)
    assert len(s.present_modules) == 2
    assert 'flexx.ui._widget' in s.present_modules
    assert 'flexx.ui.widgets._button' in s.present_modules
    assert len(s._present_classes) == 7  # Because a module was loaded that has more widgets
    assert ui.Button in s._present_classes
    assert ui.RadioButton in s._present_classes
    assert ui.CheckBox in s._present_classes
    assert ui.ToggleButton in s._present_classes
    assert ui.BaseButton in s._present_classes
    assert ui.Widget in s._present_classes

    with raises(TypeError):
         s._register_component_class(3)


## Prepare module loading tests

from flexx.event._component import new_type


PKG_NAME = 'flxtest2'

def add_prefix(n):
    if isinstance(n, list):
        return [add_prefix(i) for i in n]
    elif n.startswith('foo.'):
        return PKG_NAME + '.' + n
    else:
        return n


def teardown_module():
    clear_test_classes()


def clear_test_classes():
    classes = app._component2.AppComponentMeta.CLASSES
    for cls in list(classes):
        if cls.__jsmodule__.startswith(PKG_NAME + '.'):
            classes.remove(cls)


def fakecomponent_init(self, s):
    self._session = s
    self._id = 'FakeComponent'

def fakecomponent_setattr(self, s, v):
    return object.__setattr__(self, s, v)

def fakecomponent_del(self):
    pass

Component_overload = dict(__linenr__=0,
                          __init__=fakecomponent_init,
                          __setattr__=fakecomponent_setattr,
                          __del__=fakecomponent_del,
                          )


class SessionTester(Session):
    """ A session subclass that keeps track of DEFINE commands.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assets_js = []
        self.assets_css = []

    def send_command(self, *command):
        if command[0] == 'DEFINE':
            if 'JS' in command[1]:
                _, _, name, _ = command
                self.assets_js.append(name)
            elif 'CSS' in command[1]:
                _, _, name, _ = command
                self.assets_css.append(name)


class FakeModule:
    """ An object that looks and walks like a JSModule. Enough to fool
    Flexx' internals.
    """
    def __init__(self, store, name):
        self.name = add_prefix(name)
        self.deps = set()
        self.component_classes = set()
        store._modules[self.name] = self

        b1 = app.Bundle(self.name + '.js')
        b2 = app.Bundle(self.name + '.css')
        b1.add_module(self)
        b2.add_module(self)
        store._assets[b1.name] = b1
        store._assets[b2.name] = b2

    def make_component_class(self, name, base=app.JsComponent):
        cls = new_type(name, (base, ), Component_overload.copy())
        self.component_classes.add(cls)
        cls.__module__ = self.name
        cls.__jsmodule__ = self.name
        self.deps.add(base.__jsmodule__)
        return cls

    def add_variable(self, name):
        assert name in [m.__name__ for m in self.component_classes]

    def get_js(self):
        return self.name + '-JS'

    def get_css(self):
        return self.name + '-CSS'


## Test module loading

def test_module_loading1():
    """ Simple case. """
    clear_test_classes()

    store = AssetStore()
    s = SessionTester('', store)

    m1 = FakeModule(store, 'foo.m1')
    m2 = FakeModule(store, 'foo.m2')

    Ma = m1.make_component_class('Maa')
    Mb = m1.make_component_class('Mbb')
    Mc = m2.make_component_class('Mcc')

    s._register_component(Ma(flx_session=s))
    s._register_component(Mb(flx_session=s))
    s._register_component(Mc(flx_session=s))

    assert s.assets_js == add_prefix(['foo.m1.js', 'foo.m2.js'])
    assert s.assets_css == add_prefix(['foo.m1.css', 'foo.m2.css'])


def test_module_loading2():
    """ No deps """
    clear_test_classes()

    store = AssetStore()
    s = SessionTester('', store)

    m1 = FakeModule(store, 'foo.m1')
    m2 = FakeModule(store, 'foo.m2')
    m3 = FakeModule(store, 'foo.m3')

    Ma = m2.make_component_class('Ma')
    # m2.deps = add_prefix(['foo.m3'])
    # m3.deps = add_prefix(['foo.m1'])

    s._register_component(Ma(flx_session=s))

    assert s.assets_js == add_prefix(['foo.m2.js'])


def test_module_loading3():
    """ Dependencies get defined too (and before) """
    clear_test_classes()

    store = AssetStore()
    s = SessionTester('', store)

    m1 = FakeModule(store, 'foo.m1')
    m2 = FakeModule(store, 'foo.m2')
    m3 = FakeModule(store, 'foo.m3')

    Ma = m2.make_component_class('Ma')
    m2.deps = add_prefix(['foo.m3'])
    m3.deps = add_prefix(['foo.m1'])

    s._register_component(Ma(flx_session=s))

    assert s.assets_js == add_prefix(['foo.m1.js', 'foo.m3.js', 'foo.m2.js'])


def test_module_loading4():
    """ Dependencies by inheritance """
    # A bit silly; the JSModule (and our FakeModule) handles this dependency

    clear_test_classes()

    store = AssetStore()
    s = SessionTester('', store)

    m1 = FakeModule(store, 'foo.m1')
    m2 = FakeModule(store, 'foo.m2')
    m3 = FakeModule(store, 'foo.m3')

    Ma = m2.make_component_class('Ma')
    Mb = m3.make_component_class('Mb', Ma)
    Mc = m1.make_component_class('Mc', Mb)

    s._register_component(Mc(flx_session=s))

    assert s.assets_js == add_prefix(['foo.m2.js', 'foo.m3.js', 'foo.m1.js'])


def test_module_loading5():
    """ Associated assets """
    # A bit silly; the JSModule (and our FakeModule) handles this dependency

    clear_test_classes()

    store = AssetStore()
    s = SessionTester('', store)

    m1 = FakeModule(store, 'foo.m1')
    m2 = FakeModule(store, 'foo.m2')
    m3 = FakeModule(store, 'foo.m3')

    store.add_shared_asset('spam.js', 'XX')
    store.associate_asset(add_prefix('foo.m1'), 'spam.js')
    store.associate_asset(add_prefix('foo.m2'), 'eggs.js', 'YY')
    store.associate_asset(add_prefix('foo.m2'), 'spam.js')
    store.associate_asset(add_prefix('foo.m2'), 'bla.css', 'ZZ')
    store.associate_asset(add_prefix('foo.m3'), 'bla.css')

    Ma = m1.make_component_class('Ma')
    Mb = m2.make_component_class('Mb')
    Mc = m3.make_component_class('Mc')

    s._register_component(Ma(flx_session=s))
    s._register_component(Mb(flx_session=s))
    s._register_component(Mc(flx_session=s))

    assert s.assets_js == add_prefix(['spam.js', 'foo.m1.js', 'eggs.js', 'foo.m2.js', 'foo.m3.js'])
    assert s.assets_css == add_prefix(['foo.m1.css', 'bla.css', 'foo.m2.css', 'foo.m3.css'])


# clear_test_classes()
# test_module_loading5()
# clear_test_classes()

##

def pongit(session, n):
    for i in range(n):
        c = session._ping_counter
        session._ping_counter += 1
        session._receive_pong(c)
        loop = asyncio.get_event_loop()
        for j in range(2):
            loop.call_soon(loop.stop)
            loop.run_forever()
        session._ping_counter = c + 1

# def pongit(session, n):
#     max_timeout = session._ping_counter + n
#     loop = asyncio.get_event_loop()
#     def check():
#         if session._ping_counter >= max_timeout:
#             loop.stop()
#         else:
#             loop.call_soon(check)
#     loop.run_forever()


def test_keep_alive():

    # Avoid Pyzo hijack
    asyncio.set_event_loop(asyncio.new_event_loop())

    session = app.manager.get_default_session()
    if session is None:
        session = app.manager.create_default_session()

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
    pongit(session, 4)
    gc.collect()
    assert foo1_ref() is not None
    assert foo2_ref() is not None
    assert foo3_ref() is not None

    # Pong 7, still too soon
    pongit(session, 3)
    gc.collect()
    assert foo1_ref() is not None
    assert foo2_ref() is not None
    assert foo3_ref() is not None

    # Pong 10, should remove foo1
    pongit(session, 4)
    gc.collect()
    assert foo1_ref() is None
    assert foo2_ref() is not None
    assert foo3_ref() is not None

    # Pong 11, should remove foo2
    pongit(session, 1)
    gc.collect()
    assert foo1_ref() is None
    assert foo2_ref() is None
    assert foo3_ref() is not None

    # Pong 20, should remove foo3
    pongit(session, 10)
    gc.collect()
    assert foo1_ref() is None
    assert foo2_ref() is None
    assert foo3_ref() is None


def test_keep_alive_noleak1():

    class Foo:
        pass

    # Create a session and an object that has a reference to it (like Component)
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

    # Create a session and an object that has a reference to it (like Component)
    session = app.Session('test')
    foo = Foo()
    foo.session = session

    # Let the session keep the object alive, so it keeps its reference
    session.keep_alive(foo)

    session_ref = weakref.ref(session)
    foo_ref = weakref.ref(foo)

    # Removing object alone wont delete it
    del foo
    gc.collect()
    assert foo_ref() is not None

    # But removing both will; gc is able to clear circular ref
    del session
    gc.collect()
    assert session_ref() is None
    assert foo_ref() is None



run_tests_if_main()
