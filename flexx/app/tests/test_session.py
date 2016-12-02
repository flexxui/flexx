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
    
    # Add url data
    s.add_data('readme', 'https://github.com/zoofIO/flexx/blob/master/README.md')
    assert 'Flexx is' in s.get_data('readme').decode()
    
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
    assert not s.used_modules
    
    s._register_model_class(ui.Button)
    assert len(s.used_modules) == 2
    assert 'flexx.ui._widget' in s.used_modules
    assert 'flexx.ui.widgets._button' in s.used_modules
    assert len(s._used_classes) == 6  # Because a module was loaded that has more widgets
    assert ui.Button in s._used_classes
    assert ui.RadioButton in s._used_classes
    assert ui.CheckBox in s._used_classes
    assert ui.ToggleButton in s._used_classes
    assert ui.BaseButton in s._used_classes
    assert ui.Widget in s._used_classes
    
    with raises(TypeError):
         s._register_model_class(3)


run_tests_if_main()
