from flexx.util.testing import run_tests_if_main, raises

import sys

from flexx import app
from flexx.app import Session
from flexx.app._assetstore import assets, AssetStore as _AssetStore


class AssetStore(_AssetStore):
    _test_mode = True


class Fooo1(app.Model):
    x = 3


def test_session_basics():
    
    s = Session('xx')
    assert s.app_name == 'xx'
    assert 'xx' in repr(s)


def test_get_model_instance_by_id():
    # is really a test for the session, but historically, the test is done here
    
    # This test needs a default session
    session = app.manager.get_default_session()
    if session is None:
        session = app.manager.create_default_session()
    
    m1 = Fooo1()
    m2 = Fooo1()
    
    assert m1 is not m2
    assert session.get_model_instance_by_id(m1.id) is m1
    assert session.get_model_instance_by_id(m2.id) is m2
    assert session.get_model_instance_by_id('blaaaa') is None


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
    # s.add_data('readme', 'https://github.com/zoofIO/flexx/blob/master/README.md')
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


def test_session_registering_model_classes():
    
    from flexx import ui
    
    store = AssetStore()
    store.update_modules()
    
    s = Session('', store)
    commands = []
    s._send_command = lambda x: commands.append(x)
    assert not s.present_modules
    
    s._register_model_class(ui.Button)
    assert len(s.present_modules) == 2
    assert 'flexx.ui._widget' in s.present_modules
    assert 'flexx.ui.widgets._button' in s.present_modules
    assert len(s._present_classes) == 6  # Because a module was loaded that has more widgets
    assert ui.Button in s._present_classes
    assert ui.RadioButton in s._present_classes
    assert ui.CheckBox in s._present_classes
    assert ui.ToggleButton in s._present_classes
    assert ui.BaseButton in s._present_classes
    assert ui.Widget in s._present_classes
    
    with raises(TypeError):
         s._register_model_class(3)


## Prepare module loading tests

from flexx.app._model import new_type


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
    for cls in list(app.Model.CLASSES):
        if cls.__jsmodule__.startswith(PKG_NAME + '.'):
            app.Model.CLASSES.remove(cls)


def fakemodel_init(self, s):
    self._session = s
    self._id = 'FakeModel'

def fakemodel_setattr(self, s, v):
    return object.__setattr__(self, s, v)

def fakemodel_del(self):
    pass

Model_overload = dict(__init__=fakemodel_init,
                      __setattr__=fakemodel_setattr,
                      __del__=fakemodel_del,
                      )


class SessionTester(Session):
    """ A session subclass that keeps track of DEFINE commands.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assets_js = []
        self.assets_css = []
    
    def _send_command(self, command):
        if command.startswith('DEFINE-JS'):
            _, name, _ = command.split(' ', 2)
            self.assets_js.append(name)
        elif command.startswith('DEFINE-CSS'):
            _, name, _ = command.split(' ', 2)
            self.assets_css.append(name)


class FakeModule:
    """ An object that looks and walks like a JSModule. Enough to fool
    Flexx' internals.
    """
    def __init__(self, store, name):
        self.name = add_prefix(name)
        self.deps = set()
        self.model_classes = set()
        store._modules[self.name] = self
        
        b1 = app.Bundle(self.name + '.js')
        b2 = app.Bundle(self.name + '.css')
        b1.add_module(self)
        b2.add_module(self)
        store._assets[b1.name] = b1
        store._assets[b2.name] = b2
    
    def make_model_class(self, name, base=app.Model):
        cls = new_type(name, (base, ), Model_overload)
        self.model_classes.add(cls)
        cls.__module__ = self.name
        cls.__jsmodule__ = self.name
        self.deps.add(base.__jsmodule__)
        return cls
    
    def add_variable(self, name):
        assert name in [m.__name__ for m in self.model_classes]
    
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
    
    Ma = m1.make_model_class('Ma')
    Mb = m1.make_model_class('Mb')
    Mc = m2.make_model_class('Mc')
    
    s._register_model(Ma(s))
    s._register_model(Mb(s))
    s._register_model(Mc(s))
    
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
    
    Ma = m2.make_model_class('Ma')
    # m2.deps = add_prefix(['foo.m3'])
    # m3.deps = add_prefix(['foo.m1'])
    
    s._register_model(Ma(s))
    
    assert s.assets_js == add_prefix(['foo.m2.js'])


def test_module_loading3():
    """ Dependencies get defined too (and before) """
    clear_test_classes()
    
    store = AssetStore()
    s = SessionTester('', store)
    
    m1 = FakeModule(store, 'foo.m1')
    m2 = FakeModule(store, 'foo.m2')
    m3 = FakeModule(store, 'foo.m3')
    
    Ma = m2.make_model_class('Ma')
    m2.deps = add_prefix(['foo.m3'])
    m3.deps = add_prefix(['foo.m1'])
    
    s._register_model(Ma(s))
    
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
    
    Ma = m2.make_model_class('Ma')
    Mb = m3.make_model_class('Mb', Ma)
    Mc = m1.make_model_class('Mc', Mb)
    
    s._register_model(Mc(s))
    
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
    
    Ma = m1.make_model_class('Ma')
    Mb = m2.make_model_class('Mb')
    Mc = m3.make_model_class('Mc')
    
    s._register_model(Ma(s))
    s._register_model(Mb(s))
    s._register_model(Mc(s))
    
    assert s.assets_js == add_prefix(['spam.js', 'foo.m1.js', 'eggs.js', 'foo.m2.js', 'foo.m3.js'])
    assert s.assets_css == add_prefix(['foo.m1.css', 'bla.css', 'foo.m2.css', 'foo.m3.css'])


# clear_test_classes()
# test_module_loading5()
# clear_test_classes()

run_tests_if_main()
