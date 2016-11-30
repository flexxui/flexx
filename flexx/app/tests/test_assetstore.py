"""
Tests for Asset AssetStore and SessionAssets.

Note that our docs is very much a test for our export mechanism.
"""

import os
import sys
import tempfile
import shutil

from flexx.util.testing import run_tests_if_main, raises

from flexx.app._assetstore import assets, AssetStore
from flexx.app._session import SessionAssets

from flexx import ui, app


N_STANDARD_ASSETS = 3

test_filename = os.path.join(tempfile.gettempdir(), 'flexx_asset_cache.test')


def test_asset_store_collect():
    
    from flexx import ui
    
    s = AssetStore()
    s.update_modules()
    assert len(s.modules) > 10
    assert 'flexx.ui._widget' in s.modules
    assert 'flexx.app._model' in s.modules
    
    assert '.Widget =' in s.get_asset('flexx.ui._widget.js').to_string()
    assert '.Widget =' in s.get_asset('flexx.ui.js').to_string()
    assert '.Widget =' in s.get_asset('flexx.js').to_string()
    assert '.Widget =' not in s.get_asset('flexx.app.js').to_string()
    
    assert '.Model =' in s.get_asset('flexx.app._model.js').to_string()
    assert '.Model =' in s.get_asset('flexx.app.js').to_string()
    assert '.Model =' in s.get_asset('flexx.js').to_string()
    assert '.Model =' not in s.get_asset('flexx.ui.js').to_string()


def test_asset_store_data():
    
    s = AssetStore()
    assert len(s.get_asset_names()) == N_STANDARD_ASSETS
    assert len(s.get_data_names()) == 0
    
    # Add data
    s.add_shared_data('xx', b'xxxx')
    s.add_shared_data('yy', b'yyyy')
    assert len(s.get_asset_names()) == N_STANDARD_ASSETS
    assert len(s.get_data_names()) == 2
    assert 'xx' in s.get_data_names()
    assert 'yy' in s.get_data_names()
    assert '2 data' in repr(s)
    
    # get_data()
    assert s.get_data('xx') == b'xxxx'
    assert s.get_data('zz') is None
    
    # Add data with same name
    with raises(ValueError):
        s.add_shared_data('xx', b'zzzz')
    
    # Add url data
    s.add_shared_data('readme', 'https://github.com/zoofIO/flexx/blob/master/README.md')
    assert 'Flexx is' in s.get_data('readme').decode()
    
    # Add BS data
    with raises(TypeError):
        s.add_shared_data('dd')  # no data
    with raises(TypeError):
        s.add_shared_data('dd', 4)  # not an asset
    if sys.version_info > (3, ):
        with raises(TypeError):
            s.add_shared_data('dd', 'not bytes')
        with raises(TypeError):
            s.add_shared_data(b'dd', b'yes, bytes')  # name not str
    with raises(TypeError):
        s.add_shared_data(4, b'zzzz')  # name not a str


def test_asset_store_export():
    
    from flexx import ui
    
    dir = os.path.join(tempfile.gettempdir(), 'flexx_export')
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    
    # os.mkdir(dir) -> No, export can create this dir!
    
    store = AssetStore()
    store.update_modules()
    
    # Getting an asset marks them as used
    store.get_asset('flexx.ui.js')
    store.get_asset('flexx.app.js')
    store.get_asset('flexx.js')
    store.get_asset('reset.css')
    
    store.add_shared_data('foo.png', b'x')
    
    s = SessionAssets(store)
    s.add_data('bar.png', b'x')
    
    store.export(dir)
    s._export(dir)
    assert len(os.listdir(dir)) == 2
    assert os.path.isfile(os.path.join(dir, '_assets', 'shared', 'reset.css'))
    assert os.path.isfile(os.path.join(dir, '_assets', 'shared', 'flexx.ui.js'))
    assert os.path.isfile(os.path.join(dir, '_assets', 'shared', 'flexx.app.js'))
    assert os.path.isfile(os.path.join(dir, '_assets', 'shared', 'flexx.js'))
    assert not os.path.isfile(os.path.join(dir, '_assets', 'shared', 'flexx.ui._widget.js'))
    assert os.path.isfile(os.path.join(dir, '_data', 'shared', 'foo.png'))
    assert os.path.isfile(os.path.join(dir, '_data', s.id, 'bar.png'))

    # Will only create a dir that is one level deep
    with raises(ValueError):
        store.export(os.path.join(dir, 'not', 'exist'))


# def test_session_assets():
#     
#     store = AssetStore()
#     store.add_shared_asset(app.Asset('spam.css', '', []))
#     s = SessionAssets(store)
#     s._send_command = lambda x: None
#     assert s.id
#     
#     assert len(s.get_asset_names()) == 0
#     assert len(s.get_data_names()) == 0
#     
#     # Adding assets ..
#     
#     # Add an asset
#     asset = app.Asset('foo.js', '-foo=7-', [])
#     s.add_asset(asset)
#     #
#     assert len(s.get_asset_names()) == 1
#     assert len(s.get_data_names()) == 0
#     assert 'foo.js' in s.get_asset_names()
#     
#     # Add another asset
#     asset = app.Asset('bar.js', '-bar=8-', [])
#     s.add_asset(asset)
#     #
#     assert len(s.get_asset_names()) == 2
#     assert 'bar.js' in s.get_asset_names()
#     
#     # Add asset from store
#     s.add_asset('spam.css')
#     assert len(s.get_asset_names()) == 3
#     assert 'spam.css' in s.get_asset_names()
#     
#     # Add asset via kwargs
#     s.add_asset(name='eggs.js', sources=['x=3'], deps=[])
#     assert len(s.get_asset_names()) == 4
#     assert 'eggs.js' in s.get_asset_names()
#     
#     # Use store asset again: ok
#     s.add_asset('spam.css')
#     # Use asset that's already used: ok
#     s.add_asset(asset)
#     
#     # Add unknown store asset
#     with raises(ValueError):
#         s.add_asset('spam.js')
#     # Not an asset instance
#     with raises(TypeError):
#         s.add_asset()
#     with raises(TypeError):
#         s.add_asset('spam.js', name='foo.j2')
#     with raises(TypeError):
#         s.add_asset(3)
#     # New asset with existing name
#     asset3 = app.Asset('bar.js', '-bar=1-', [])
#     with raises(ValueError):
#         s.add_asset(asset3)
#     
#     # get_asset()
#     assert s.get_asset('bar.js') is asset
#     assert s.get_asset('spam.css') is store.get_asset('spam.css')
#     assert s.get_asset('spam.css').name == 'spam.css'
#     assert s.get_asset('bla.css') is None
#     with raises(ValueError):
#         s.get_asset('fooo')  # must ends with .js or .css


def test_session_assets_data():
    
    store = AssetStore()
    store.add_shared_data('ww', b'wwww')
    s = SessionAssets(store)
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
    
    s = SessionAssets(store)
    commands = []
    s._send_command = lambda x: commands.append(x)
    assert not s._used_modules
    
    # Register button, pulls in all dependent modules
    s.register_model_class(ui.Button)
    assert ui.Button.__jsmodule__ in s._used_modules
    assert ui.BaseButton.__jsmodule__ in s._used_modules
    assert ui.Widget.__jsmodule__ in s._used_modules
    assert 'flexx.app._model' in s._used_modules
    
    # Get assets, level 9
    js_assets, css_assets = s.get_assets_in_order(bundle_level=9)
    names = [a.name for a in js_assets]
    assert 'flexx.app._model.js' in names
    assert 'flexx.ui.widgets._button.js' in names
    
    # Get assets, level 2
    js_assets, css_assets = s.get_assets_in_order(bundle_level=2)
    names = [a.name for a in js_assets]
    assert 'flexx.app.js' in names
    assert 'flexx.ui.js' in names
    assert 'flexx.ui.widgets._button.js' not in names
    
    # Get assets, level 1
    js_assets, css_assets = s.get_assets_in_order(bundle_level=1)
    names = [a.name for a in js_assets]
    assert 'flexx.js' in names
    assert 'flexx.ui.js' not in names
    assert 'flexx.ui.widgets._button.js' not in names
    
    # Get page
    code = s.get_page()
    assert '<html>' in code
    code = s.get_page_for_export([])
    assert '<html>' in code
    
    # dynamic loading ...
    
    # No commands so far
    assert not commands
    
    s.register_model_class(ui.html.ul)
    assert commands


run_tests_if_main()
