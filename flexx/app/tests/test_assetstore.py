"""
Tests for Asset AssetStore and SessionAssets.

Note that our docs is very much a test for our export mechanism.
"""

import os
import sys
import tempfile
import shutil

from flexx.util.testing import run_tests_if_main, raises

from flexx.app.assetstore import assets, AssetStore, SessionAssets

from flexx import ui, app


N_STANDARD_ASSETS = 3

test_filename = os.path.join(tempfile.gettempdir(), 'flexx_asset_cache.test')


class WTF:
    pass


def test_asset():
    
    # Initialization
    
    asset1 = app.Asset('foo.js', 'foo=3', [])
    assert 'foo.js' in repr(asset1)
    assert 'foo.js' == asset1.name
    assert asset1.deps == ()
    
    asset2 = app.Asset('bar.css', 'bar=2', [])
    assert 'bar.css' in repr(asset2)
    assert 'bar.css' == asset2.name
    
    with raises(TypeError):
        app.Asset()  # :/
    with raises(TypeError):
        app.Asset('foo.js')  # need sources
    with raises(TypeError):
        app.Asset('foo.js', 'bla=3')  # need deps
    
    with raises(TypeError):
        app.Asset(3, 'bar=2', [])  # name not a str
    with raises(ValueError):
        app.Asset('foo.png', '', [])  # js and css only
    with raises(TypeError):
        app.Asset('bar.css', 3, [])  # source not str/list
    with raises(TypeError):
        app.Asset('bar.css', [3], [])  # source not convertable to code
    with raises(TypeError):
        app.Asset('bar.css', ['bla=2'], 2)  # deps not list
    with raises(TypeError):
        app.Asset('bar.css', ['bla=2'], [2])  # deps not list of str
    
    # Code composition 
    
    asset = app.Asset('foo.js', ['foo=3', 'bar=2', app.Model, WTF], [])
    code = asset.to_string()
    assert 'foo=3\n' in code  # note the newline
    assert 'bar=2\n' in code
    assert 'Model = function (' in code
    assert 'WTF = function (' in code
    
    with raises(TypeError):
        app.Asset('foo.js', [4], [])
    with raises(TypeError):
        app.Asset('foo.css', [WTF], [])
    
    # To html JS
    asset = app.Asset('foo.js', ['foo=3', 'bar=2', app.Model, WTF], [])
    code = asset.to_html('', 0)
    assert code.startswith('<script') and code.strip().endswith('</script>')
    assert 'foo=3\n' in code  # note the newline
    assert 'bar=2\n' in code
    assert 'Model = function (' in code
    assert 'WTF = function (' in code
    assert all([c in code for c in ['foo=', 'bar=', 'WTF', 'Model']])
    
    asset = app.Asset('foo.js', ['foo=3', 'bar=2', app.Model, WTF], [])
    code = asset.to_html()
    assert code.startswith('<script ') and code.strip().endswith('</script>')
    assert not any([c in code for c in ['foo=', 'bar=', 'WTF', 'Model']])
    
    def foo(x):
        with x:
            pass
    with raises(ValueError):
        app.Asset('foo.js', [foo], [])  # caught during pyscript conversion
    
    # To html CSS
    asset = app.Asset('bar.css', ['foo=3', 'bar=2', app.Model], [])
    code = asset.to_html('', 0)
    assert code.startswith('<style>') and code.strip().endswith('</style>')
    assert all([c in code for c in ['foo=', 'bar=']])
    
    asset = app.Asset('bar.css', ['foo=3', 'bar=2', app.Model], [])
    code = asset.to_html()
    assert code.startswith('<link') and code.strip().endswith('/>')
    assert not any([c in code for c in ['foo=', 'bar=']])
    
    # Test asset via uri
    with open(test_filename, 'wb') as f:
        f.write('var blablabla=7;'.encode())
    asset = app.Asset('bar.css', ['foo=3', 'bar=2', 'file://' + test_filename,
                      'http://code.jquery.com/jquery-3.1.1.slim.min.js'], [])
    code = asset.to_string()
    assert 'blablabla=7' in code
    assert 'jQuery v3.1.1' in code


def test_remote_asset():
    
    # Prepare example asset info
    bootstrap_url = 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
    jquery_url = 'https://code.jquery.com/jquery-3.1.1.slim.min.js'
    with open(test_filename + '.js', 'wb') as f:
        f.write('var blablabla=7;'.encode())
    
    # JS from url
    asset = app.Asset(jquery_url)
    assert asset.remote == jquery_url
    assert 'jQuery v3.1.1' in asset.to_string()
    assert 'jQuery v3.1.1' in asset.to_html('{}', 0)
    assert 'jQuery v3.1.1' in asset.to_html('{}', 0)
    assert 'jQuery v3.1.1' not in asset.to_html('{}', 1)
    assert 'jQuery v3.1.1' not in asset.to_html('{}', 2)
    assert 'src=' not in asset.to_html('{}', 0)
    assert 'src=' in asset.to_html('{}', 1)
    assert 'src=' in asset.to_html('{}', 2)
    assert 'https://' not in asset.to_html('{}', 1)
    assert 'https://' in asset.to_html('{}', 2)
    
    # CSS from url
    asset = app.Asset(bootstrap_url)
    assert asset.remote == bootstrap_url
    assert 'Bootstrap v3.3.7' in asset.to_string()
    assert 'Bootstrap v3.3.7' in asset.to_html('{}', 0)
    assert 'Bootstrap v3.3.7' not in asset.to_html('{}', 1)
    assert 'Bootstrap v3.3.7' not in asset.to_html('{}', 2)
    assert 'href=' not in asset.to_html('{}', 0)
    assert 'href=' in asset.to_html('{}', 1)
    assert 'href=' in asset.to_html('{}', 2)
    assert 'https://' not in asset.to_html('{}', 1)
    assert 'https://' in asset.to_html('{}', 2)
    
    # JS from file
    asset = app.Asset('file://' + test_filename + '.js')
    assert test_filename in asset.remote
    assert 'blablabla=7' in asset.to_string()
    assert 'blablabla=7' in asset.to_html('{}', 0)
    assert 'blablabla=7' not in asset.to_html('{}', 1)
    assert 'blablabla=7' not in asset.to_html('{}', 2)
    
    with raises(TypeError):
         app.Asset(jquery_url, 'foo=3')  # no sources for remote asset
    with raises(TypeError):
         app.Asset(jquery_url, ['foo=3'])  # no sources for remote asset


def test_module_asset():
    
    # By defining exports, it becomes a module asset
    asset = app.Asset('foo.js', 'var foo = 7;', [], ['foo'])
    assert asset.deps == ()
    assert asset.exports == ('foo', )
    assert 'define(' in asset.to_string()
    assert 'return {foo: foo};' in asset.to_string()
    
    # Exports can be str
    asset = app.Asset('foo.js', 'var foo = 7;', [], 'foo')
    assert asset.exports == 'foo'
    assert 'define(' in asset.to_string()
    assert 'return foo;' in asset.to_string()
    
    # Exports can be empty list
    asset = app.Asset('foo.js', 'var foo = 7;', [], [])
    assert asset.exports == ()
    assert 'define(' in asset.to_string()
    assert 'return {};' in asset.to_string()
    
    # Exports ara auto-populated
    asset = app.Asset('foo.js', ['var foo = 7;', WTF], [], ['foo'])
    assert asset.exports == ('foo', 'WTF')
    assert 'define(' in asset.to_string()
    assert 'return {foo: foo, WTF: WTF};' in asset.to_string()
    
    # Exports ara NOT auto-populated if exports is str
    asset = app.Asset('foo.js', ['var foo = 7;', WTF], [], 'foo')
    assert asset.exports == 'foo'
    assert 'define(' in asset.to_string()
    assert 'return foo;' in asset.to_string()
    
    # But if exports not given or None, its not a module
    asset = app.Asset('foo.js', 'var foo = 7;', [], None)
    assert asset.exports is None
    assert 'define(' not in asset.to_string()
    
    with raises(TypeError):
        app.Asset('foo.css', ['.xxx {}'], [], [])  # No css
    with raises(TypeError):
        app.Asset('foo.js', 'var foo = 7;', [], 3)  # exports not str or list
    with raises(TypeError):
        app.Asset('foo.js', 'var foo = 7;', [], [3])  # exports element not str
    
    # Deps ...
    
    asset = app.Asset('foo.js', 'var foo = 7;', ['xxx.py'], ['foo'])
    assert 'xxx.py' in asset.deps
    assert 'xxx.py' not in asset.to_string()
    
    asset = app.Asset('foo.js', 'var foo = 7;', ['xxx.py as xxx'], ['foo'])
    assert 'xxx.py' in asset.deps
    assert 'xxx.py' in asset.to_string()


def test_asset_store_assets():
    
    s = AssetStore()
    assert len(s.get_asset_names()) == N_STANDARD_ASSETS
    assert len(s.get_data_names()) == 0
    
    # Add assets
    asset1 = app.Asset('foo.js', '-foo=7-', [])
    s.add_shared_asset(asset1)
    asset2 = app.Asset('bar.js', '-bar=8-', [])
    s.add_shared_asset(asset2)
    #
    assert len(s.get_asset_names()) == N_STANDARD_ASSETS + 2
    assert len(s.get_data_names()) == 0
    assert 'foo.js' in s.get_asset_names()
    assert 'foo.js' in repr(s)
    assert 'bar.js' in s.get_asset_names()
    assert 'bar.js' in repr(s)
    
    # get_asset()
    assert s.get_asset('foo.js') is asset1
    assert s.get_asset('spam.js') is None
    with raises(ValueError):
        s.get_asset('fooo')  # must ends with .js or .css
    
    # Add asset with same name
    asset = app.Asset('bar.js', '-bar=1-', [])
    with raises(ValueError):
        s.add_shared_asset(asset)
    
    # Add BS asset
    with raises(TypeError):
        s.add_shared_asset()  # no asset nor kwargs
    with raises(TypeError):
        s.add_shared_asset(asset, name='asd.js')  # both is also wrong
    with raises(TypeError):
        s.add_shared_asset(4)  # not an asset
    with raises(TypeError):
        s.add_shared_asset('not an asset')


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
    assert 'xx' in repr(s)
    assert 'yy' in repr(s)
    
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
    
    dir = os.path.join(tempfile.gettempdir(), 'flexx_export')
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    
    # os.mkdir(dir) -> No, export can create this dir!
    
    store = AssetStore()
    store.add_shared_asset(app.Asset('foo.css', '', []))
    store.add_shared_data('foo.png', b'x')
    
    s = SessionAssets(store)
    s.add_asset(app.Asset('bar.js', '', []))
    s.add_data('bar.png', b'x')
    
    store.export(dir)
    s._export(dir)
    assert len(os.listdir(dir)) == 2
    assert os.path.isfile(os.path.join(dir, '_assets', 'shared', 'reset.css'))
    assert os.path.isfile(os.path.join(dir, '_assets', 'shared', 'foo.css'))
    assert os.path.isfile(os.path.join(dir, '_data', 'shared', 'foo.png'))
    assert os.path.isfile(os.path.join(dir, '_assets', s.id, 'bar.js'))
    assert os.path.isfile(os.path.join(dir, '_data', s.id, 'bar.png'))

    # Will only create a dir that is one level deep
    with raises(ValueError):
        store.export(os.path.join(dir, 'not', 'exist'))

# def test_cache_submodules():
#     
#     s = AssetStore()
#     
#     s.create_module_assets('flexx.ui.widgets')
#     s.create_module_assets('flexx.ui.widgets._button')
#     s.create_module_assets('flexx.ui')
#     
#     s.get_module_name_for_model_class(ui.Slider) == 'flexx.ui.widgets'
#     s.get_module_name_for_model_class(ui.Button) == 'flexx.ui.widgets._button'
#     s.get_module_name_for_model_class(ui.BoxLayout) == 'flexx.ui'


def test_session_assets():
    
    store = AssetStore()
    store.add_shared_asset(app.Asset('spam.css', '', []))
    s = SessionAssets(store)
    s._send_command = lambda x: None
    assert s.id
    
    assert len(s.get_asset_names()) == 0
    assert len(s.get_data_names()) == 0
    
    # Adding assets ..
    
    # Add an asset
    asset = app.Asset('foo.js', '-foo=7-', [])
    s.add_asset(asset)
    #
    assert len(s.get_asset_names()) == 1
    assert len(s.get_data_names()) == 0
    assert 'foo.js' in s.get_asset_names()
    
    # Add another asset
    asset = app.Asset('bar.js', '-bar=8-', [])
    s.add_asset(asset)
    #
    assert len(s.get_asset_names()) == 2
    assert 'bar.js' in s.get_asset_names()
    
    # Add asset from store
    s.add_asset('spam.css')
    assert len(s.get_asset_names()) == 3
    assert 'spam.css' in s.get_asset_names()
    
    # Add asset via kwargs
    s.add_asset(name='eggs.js', sources=['x=3'], deps=[])
    assert len(s.get_asset_names()) == 4
    assert 'eggs.js' in s.get_asset_names()
    
    # Use store asset again: ok
    s.add_asset('spam.css')
    # Use asset that's already used: ok
    s.add_asset(asset)
    
    # Add unknown store asset
    with raises(ValueError):
        s.add_asset('spam.js')
    # Not an asset instance
    with raises(TypeError):
        s.add_asset()
    with raises(TypeError):
        s.add_asset('spam.js', name='foo.j2')
    with raises(TypeError):
        s.add_asset(3)
    # New asset with existing name
    asset3 = app.Asset('bar.js', '-bar=1-', [])
    with raises(ValueError):
        s.add_asset(asset3)
    
    # get_asset()
    assert s.get_asset('bar.js') is asset
    assert s.get_asset('spam.css') is store.get_asset('spam.css')
    assert s.get_asset('spam.css').name == 'spam.css'
    assert s.get_asset('bla.css') is None
    with raises(ValueError):
        s.get_asset('fooo')  # must ends with .js or .css

def test_session_assets_data():
    
    store = AssetStore()
    store.add_shared_data('ww', b'wwww')
    s = SessionAssets(store)
    s._send_command = lambda x: None
    assert s.id
    
    # Add data
    s.add_data('xx', b'xxxx')
    s.add_data('yy', b'yyyy')
    assert len(s.get_asset_names()) == 0
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


def get_assets_in_order(s):
    """ Version of Session._get_assets_in_order() that strips the 
    standard assets.
    """
    js_assets, css_assets = s.get_assets_in_order()
    return js_assets[2:], css_assets


def test_dependency_resolution_1():
    """ No deps, maintain order. """
    store = AssetStore()
    s = SessionAssets(store)
    
    a1 = app.Asset('a1.js', '', [])
    a2 = app.Asset('a2.js', '', [])
    a3 = app.Asset('a3.js', '', [])
    
    s.add_asset(a1)
    s.add_asset(a2)
    s.add_asset(a3)
    
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['a1.js', 'a2.js', 'a3.js']
    

def test_dependency_resolution_2():
    """ One chain of deps """
    
    store = AssetStore()
    
    a1 = app.Asset('a1.js', '', ['b1.js'])
    b1 = app.Asset('b1.js', '', ['c1.js'])
    c1 = app.Asset('c1.js', '', ['d1.js'])
    d1 = app.Asset('d1.js', '', ['e1.js'])
    e1 = app.Asset('e1.js', '', [])
    # e1 = app.Asset('e1.js', '', ['f1.js'])
    # f1 = app.Asset('f1.js', '', ['g1.js'])
    # g1 = app.Asset('g1.js', '', [])
    
    for asset in [a1, b1, c1, d1, e1]:
        store.add_shared_asset(asset)
    
    # Add first
    s = SessionAssets(store)
    s.add_asset(a1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['e1.js', 'd1.js', 'c1.js', 'b1.js', 'a1.js']
    
    # Add middle
    s = SessionAssets(store)
    s.add_asset(c1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['e1.js', 'd1.js', 'c1.js']
    
    # Add last
    s = SessionAssets(store)
    s.add_asset(e1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['e1.js']
    
    # Add first and middle
    s = SessionAssets(store)
    s.add_asset(a1)
    s.add_asset(c1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['e1.js', 'd1.js', 'c1.js', 'b1.js', 'a1.js']
    
    # Add first and last
    s = SessionAssets(store)
    s.add_asset(e1)
    s.add_asset(a1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['e1.js', 'd1.js', 'c1.js', 'b1.js', 'a1.js']


def test_dependency_resolution_3():
    """ Unkown deps are ignored (but warned for) """
    
    store = AssetStore()
    
    a1 = app.Asset('a1.js', '', ['b1.js'])
    b1 = app.Asset('b1.js', '', ['bar.js', 'c1.js'])
    c1 = app.Asset('c1.js', '', ['d1.js', 'foo.js'])
    d1 = app.Asset('d1.js', '', ['e1.js'])
    e1 = app.Asset('e1.js', '', [])
    
    for asset in [a1, b1, c1, d1, e1]:
        store.add_shared_asset(asset)
    
    s = SessionAssets(store)
    s.add_asset(a1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['e1.js', 'd1.js', 'c1.js', 'b1.js', 'a1.js']


def test_dependency_resolution_4():
    """ Circular deps """
    
    store = AssetStore()
    
    a1 = app.Asset('a1.js', '', ['b1.js'])
    b1 = app.Asset('b1.js', '', ['c1.js'])
    c1 = app.Asset('c1.js', '', ['d1.js'])
    d1 = app.Asset('d1.js', '', ['e1.js', 'a1.js'])
    e1 = app.Asset('e1.js', '', [])
    
    for asset in [a1, b1, c1, d1, e1]:
        store.add_shared_asset(asset)
    
    s = SessionAssets(store)
    s.add_asset(a1)
    #
    with raises(RuntimeError):
        aa, _ = get_assets_in_order(s)


def test_dependency_resolution_5():
    """ Two chains """
    
    store = AssetStore()
    
    a1 = app.Asset('a1.js', '', ['b1.js'])
    b1 = app.Asset('b1.js', '', ['c1.js'])
    c1 = app.Asset('c1.js', '', ['d1.js'])
    
    a2 = app.Asset('a2.js', '', ['b2.js'])
    b2 = app.Asset('b2.js', '', ['c2.js'])
    c2 = app.Asset('c2.js', '', ['d2.js'])
    
    for asset in [a1, b1, c1, a2, b2, c2]:
        store.add_shared_asset(asset)
    
    # Only chain 1
    s = SessionAssets(store)
    s.add_asset(a1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['c1.js', 'b1.js', 'a1.js']
    
    # Only chain 2
    s = SessionAssets(store)
    s.add_asset(a2)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['c2.js', 'b2.js', 'a2.js']
    
    # Both chains, first 1
    s = SessionAssets(store)
    s.add_asset(a1)
    s.add_asset(a2)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['c1.js', 'b1.js', 'a1.js', 'c2.js', 'b2.js', 'a2.js']
    
    # Both chains, first 2
    s = SessionAssets(store)
    s.add_asset(a2)
    s.add_asset(a1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == [ 'c2.js', 'b2.js', 'a2.js', 'c1.js', 'b1.js', 'a1.js']


def test_dependency_resolution_6(): 
    """ Multiple deps - order """
    
    store = AssetStore()
    
    a1 = app.Asset('a1.js', '', ['b1.js', 'b2.js'])
    b1 = app.Asset('b1.js', '', ['c1.js', 'c2.js'])
    b2 = app.Asset('b2.js', '', ['c2.js', 'c3.js'])
    c1 = app.Asset('c1.js', '', [])
    c2 = app.Asset('c2.js', '', [])
    c3 = app.Asset('c3.js', '', [])
    
    for asset in [a1, b1, b2, c1, c2, c3]:
        store.add_shared_asset(asset)
    
    s = SessionAssets(store)
    s.add_asset(a1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == [ 'c1.js', 'c2.js', 'b1.js', 'c3.js', 'b2.js', 'a1.js']


def test_dependency_resolution_7(): 
    """ Shared deps """
    
    store = AssetStore()
    
    a1 = app.Asset('a1.js', '', ['b1.js', 'b2.js'])
    b1 = app.Asset('b1.js', '', ['c1.js'])
    b2 = app.Asset('b2.js', '', ['d1.js'])
    c1 = app.Asset('c1.js', '', ['d1.js'])
    d1 = app.Asset('d1.js', '', [])
    
    for asset in [a1, b1, b2, c1, d1]:
        store.add_shared_asset(asset)
    
    s = SessionAssets(store)
    s.add_asset(a1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['d1.js', 'c1.js', 'b1.js', 'b2.js', 'a1.js']


def test_dependency_resolution_8(): 
    """ Position of singleton asset """
    
    store = AssetStore()
    a0 = app.Asset('a0.js', '', [])
    a1 = app.Asset('a1.js', '', ['b1.js', 'b2.js'])
    b1 = app.Asset('b1.js', '', ['c1.js'])
    b2 = app.Asset('b2.js', '', ['d1.js'])
    c1 = app.Asset('c1.js', '', ['d1.js'])
    d1 = app.Asset('d1.js', '', [])
    
    for asset in [a1, b1, b2, c1, d1]:
        store.add_shared_asset(asset)
    
    s = SessionAssets(store)
    s.add_asset(a0)
    s.add_asset(a1)
    #
    aa, _ = get_assets_in_order(s)
    assert [a.name for a in aa] == ['a0.js', 'd1.js', 'c1.js', 'b1.js', 'b2.js', 'a1.js']

# 
# def test_session_registering_model_classes():
#     
#     store = AssetStore()
#     s = SessionAssets(store)
#     s._send_command = lambda x: None
#     
#     store.create_module_assets('flexx.ui.layouts')
#     
#     raises(ValueError, s.register_model_class, 4)  # must be a Model class
#     
#     s.register_model_class(ui.Slider)
#     assert len(s._known_classes) == 3  # Slider, Widget, and Model
#     s.register_model_class(ui.Slider)  # no duplicates!
#     assert len(s._known_classes) == 3
#     
#     s.register_model_class(ui.BoxLayout)
#     s.register_model_class(ui.Button)
#     
#     # Get result
#     js = s.get_js_only()
#     assert js.count('.Button = function ') == 1
#     assert js.count('.Slider = function ') == 1
#     assert js.count('.Widget = function ') == 1
#     assert js.count('.BoxLayout = function ') == 1
#     
#     # Check that module indeed only has layout widgets
#     jsmodule = store.load_asset('flexx-ui-layouts.js').decode()
#     assert jsmodule.count('.BoxLayout = function ') == 1
#     assert jsmodule.count('.Button = function ') == 0
#     assert jsmodule.count('.Widget = function ') == 0
#     
#     # Check that page contains the rest
#     page = s.get_page()
#     assert page.count('.BoxLayout = function ') == 0
#     assert page.count('.Button = function ') == 1
#     assert page.count('.Widget = function ') == 1
#     
#     # Check that a single page export has it all
#     export  = s.get_page_for_export([], True)
#     assert export.count('.BoxLayout = function ') == 1
#     assert export.count('.Button = function ') == 1
#     assert export.count('.Widget = function ') == 1
#     
#     # Patch - this func is normally provided by the Session subclass
#     commands = []
#     s._send_command = lambda x: commands.append(x)
#     
#     # Dynamic
#     s.register_model_class(ui.BoxLayout)
#     assert len(commands) == 0  # already known
#     s.register_model_class(ui.FormLayout)
#     assert len(commands) == 0  # already in module asset
#     #
#     s.register_model_class(ui.Label)
#     assert '.Label = function' in commands[0]  # JS
#     assert 'flx-' in commands[1]  # CSS


run_tests_if_main()
