import os
import tempfile
import shutil

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.app.assetstore import assets, AssetStore, SessionAssets
from flexx import ui, app


test_filename = os.path.join(tempfile.gettempdir(), 'flexx_asset_cache.test')


def test_asset_store_simple():
    
    s = AssetStore()
    assert not s.get_asset_names()
    assert not s._cache
    
    raises(IndexError, s.load_asset, 'foo.js')
    
    with open(test_filename, 'wb') as f:
        f.write(b'bar')
    
    s.add_asset('foo.css', b'foo')
    s.add_asset('foo.js', test_filename)
    
    assert s.get_asset_names() == ['foo.css', 'foo.js']  # alphabetically
    assert s.load_asset('foo.css') == b'foo'
    assert s.load_asset('foo.js') == b'bar'
    # Check caching
    with open(test_filename, 'wb') as f:
        f.write(b'foo')
    assert s.load_asset('foo.js') == b'bar'
    
    # Setting same asset
    s.add_asset('foo.css', b'foo')
    s.add_asset('foo.js', test_filename)
    raises(ValueError, s.add_asset, 'foo.css', b'fooo')
    raises(ValueError, s.add_asset, 'foo.js', b'foo')
    raises(ValueError, s.add_asset, 'foo.js', b'bar')
    
    # Fail add_asset
    raises(ValueError, s.add_asset, 'xxx', 3)  # value must be str or bytes
    raises(ValueError, s.add_asset, 'xxx', 'some file that does not exist')  # str means filename
    raises(RuntimeError, s._cache_get, 'nonexistent.ever')  # Runtime error, because this should never happen
    
    # Assets from http 
    s.add_asset('webresource.js', 'http://code.jquery.com/jquery.min.js')
    assert len(s.load_asset('webresource.js')) > 0
    
    # Fail load_asset
    raises(IndexError, s.load_asset, 'nonexistent.js')


def test_asset_store_export():
    
    dir = os.path.join(tempfile.gettempdir(), 'flexx_export')
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    
    s = AssetStore()
    
    s.export(dir)
    assert not os.listdir(dir)
    
    s.add_asset('foo.js', b'xx')
    s.add_asset('foo.css', b'xx')
    s.export(dir)
    assert len(os.listdir(dir)) == 2
    
    # Fail
    raises(ValueError, s.export, os.path.join(dir, 'doesnotexist'))


def test_cache_submodules():
    
    s = AssetStore()
    
    s.create_module_assets('flexx.ui.widgets')
    s.create_module_assets('flexx.ui.widgets._button')
    s.create_module_assets('flexx.ui')
    
    s.get_module_name_for_model_class(ui.Slider) == 'flexx.ui.widgets'
    s.get_module_name_for_model_class(ui.Button) == 'flexx.ui.widgets._button'
    s.get_module_name_for_model_class(ui.BoxLayout) == 'flexx.ui'


def test_session_assets():
    
    store = AssetStore()
    s = SessionAssets(store)
    s._send_command = lambda x: None
    
    assert not s.get_used_asset_names()
    
    with open(test_filename, 'wb') as f:
        f.write(b'bar')
    
    # Add assets, check mangles name
    a1 = s.add_asset('foo.css', b'foo')
    a2 = s.add_asset('foo.js', test_filename)
    assert 'foo' in a1 and s.id in a1 and a1.endswith('.css')
    assert 'foo' in a2 and s.id in a2 and a2.endswith('.js')
    assert s.get_used_asset_names() == [a1, a2]  # order in which it came
    
    # Get the asset
    raises(IndexError, store.load_asset, 'foo.css')
    raises(IndexError, store.load_asset, 'foo.js')
    assert store.load_asset(a1) == b'foo'
    assert store.load_asset(a2) == b'bar'
    
    # Use asset
    store.add_asset('spam.js', b'1234')
    s.use_global_asset('spam.js')
    assert s.get_used_asset_names()[-1] == 'spam.js'
    raises(IndexError, s.use_global_asset, 'unknown-asset.js')
    raises(ValueError, s.add_asset, 3, b'a')
    
    # Add assets after loading page
    s.get_page()
    s.use_global_asset('spam.js')  # prints a warning, but it does work

    # Global assets
    s.add_global_asset('eggs.js', b'12345')
    assert s.get_used_asset_names()[-1] == 'eggs.js'
    assert store.load_asset('eggs.js') == b'12345'
    raises(ValueError, s.use_global_asset, 3)
    
    # Remote assets
    s.use_remote_asset('http://linked.com/not/verified.js')
    s.use_remote_asset('http://linked.com/not/verified.css')
    s.use_remote_asset('http://linked.com/not/verified.css')  # twice is ok
    raises(ValueError, s.use_remote_asset, 3)
    page = s.get_page()
    assert 'not/verified.js' in page
    assert 'not/verified.css' in page


def test_session_registering_model_classes():
    
    store = AssetStore()
    s = SessionAssets(store)
    s._send_command = lambda x: None
    
    store.create_module_assets('flexx.ui.layouts')
    
    raises(ValueError, s.register_model_class, 4)  # must be a Model class
    
    s.register_model_class(ui.Slider)
    assert len(s._known_classes) == 3  # Slider, Widget, and Model
    s.register_model_class(ui.Slider)  # no duplicates!
    assert len(s._known_classes) == 3
    
    s.register_model_class(ui.BoxLayout)
    s.register_model_class(ui.Button)
    
    # Get result
    css, js = s.get_all_css_and_js()
    assert js.count('.Button = function ') == 1
    assert js.count('.Slider = function ') == 1
    assert js.count('.Widget = function ') == 1
    assert js.count('.BoxLayout = function ') == 1
    
    # Check that module indeed only has layout widgets
    jsmodule = store.load_asset('flexx-ui-layouts.js').decode()
    assert jsmodule.count('.BoxLayout = function ') == 1
    assert jsmodule.count('.Button = function ') == 0
    assert jsmodule.count('.Widget = function ') == 0
    
    # Check that page contains the rest
    page = s.get_page()
    assert page.count('.BoxLayout = function ') == 0
    assert page.count('.Button = function ') == 1
    assert page.count('.Widget = function ') == 1
    
    # Check that a single page export has it all
    export  = s.get_page_for_export([], True)
    assert export.count('.BoxLayout = function ') == 1
    assert export.count('.Button = function ') == 1
    assert export.count('.Widget = function ') == 1
    
    # Patch - this func is normally provided by the Session subclass
    commands = []
    s._send_command = lambda x: commands.append(x)
    
    # Dynamic
    s.register_model_class(ui.BoxLayout)
    assert len(commands) == 0  # already known
    s.register_model_class(ui.FormLayout)
    assert len(commands) == 0  # already in module asset
    #
    s.register_model_class(ui.Label)
    assert '.Label = function' in commands[0]  # JS
    assert 'flx-' in commands[1]  # CSS


run_tests_if_main()
