import os
import tempfile

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
    
    open(test_filename, 'wb').write(b'bar')
    
    s.add_asset('foo.css', b'foo')
    s.add_asset('foo.js', test_filename)
    
    assert s.get_asset_names() == ['foo.css', 'foo.js']  # alphabetically
    assert s.load_asset('foo.css') == b'foo'
    assert s.load_asset('foo.js') == b'bar'
    # Check caching
    open(test_filename, 'wb').write(b'foo')
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
    
    # Assets from http (not currently supported)
    s.add_asset('webresource.js', 'https://foo.com/x.js')
    raises(NotImplementedError, s.load_asset, 'webresource.js')
    
    # Fail load_asset
    raises(IndexError, s.load_asset, 'nonexistent.js')


def test_cache_submodules():
    
    s = AssetStore()
    
    s.create_module_assets('flexx.ui.widgets')
    s.create_module_assets('flexx.ui.widgets._button')
    s.create_module_assets('flexx.ui')
    
    s.get_module_name_for_pair_class(ui.Slider) == 'flexx.ui.widgets'
    s.get_module_name_for_pair_class(ui.Button) == 'flexx.ui.widgets._button'
    s.get_module_name_for_pair_class(ui.BoxLayout) == 'flexx.ui'


def test_session_assets():
    
    store = AssetStore()
    s = SessionAssets(store)
    
    assert not s.get_used_asset_names()
    
    open(test_filename, 'wb').write(b'bar')
    
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
    s.use_asset('spam.js')
    assert s.get_used_asset_names()[-1] == 'spam.js'
    raises(IndexError, s.use_asset, 'unknown-asset.js')
    
    # Add assets after loading page
    s.get_page()
    s.use_asset('spam.js')  # prints a warning, but it does work

    # Global assets
    s.add_global_asset('eggs.js', b'12345')
    assert s.get_used_asset_names()[-1] == 'eggs.js'
    assert store.load_asset('eggs.js') == b'12345'


def test_session_registering_pair_classes():
    
    store = AssetStore()
    s = SessionAssets(store)
    
    store.create_module_assets('flexx.ui.layouts')
    
    raises(ValueError, s._register_pair_class, 4)  # must be a Pair class
    
    s._register_pair_class(ui.Slider)
    assert len(s._known_classes) == 3  # Slider, Widget, and Pair
    s._register_pair_class(ui.Slider)  # no duplicates!
    assert len(s._known_classes) == 3
    
    s._register_pair_class(ui.BoxLayout)
    s._register_pair_class(ui.Button)
    
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
    s._register_pair_class(ui.BoxLayout)
    assert len(commands) == 0  # already known
    s._register_pair_class(ui.FormLayout)
    assert len(commands) == 0  # already in module asset
    #
    s._register_pair_class(ui.Label)
    assert '.Label = function' in commands[0]  # JS
    assert 'flx-' in commands[1]  # CSS


test_session_registering_pair_classes()

run_tests_if_main()
