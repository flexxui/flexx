"""
Tests for Asset AssetStore and Session.

Note that our docs is very much a test for our export mechanism.
"""

import os
import sys
import tempfile
import shutil

from flexx.util.testing import run_tests_if_main, raises

from flexx.app._assetstore import assets, AssetStore as _AssetStore
from flexx.app._session import Session

from flexx import ui, app


N_STANDARD_ASSETS = 3

test_filename = os.path.join(tempfile.gettempdir(), 'flexx_asset_cache.test')


class AssetStore(_AssetStore):
    _test_mode = True


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


def test_asset_store_adding_assets():
    
    s = AssetStore()
    
    # Adding
    s.add_shared_asset('foo.js', 'XXX')
    
    with raises(ValueError):
        s.add_shared_asset('foo.js', 'XXX')  # asset with that name already present
    
    # Getting
    assert 'XXX' in s.get_asset('foo.js').to_string()
    
    with raises(ValueError):
        s.get_asset('foo.png')  # only .js and .css allowed
    
    with raises(KeyError):
        s.get_asset('foo-not-exists.js')  # does not exist


def test_associate_asset():
    
    s = AssetStore()
    
    with raises(TypeError):
        s.associate_asset('module.name1', 'foo.js')  # no source given
    
    s.associate_asset('module.name1', 'foo.js', 'xxx')
    assert s.get_asset('foo.js').to_string() == 'xxx'
    
    # Now we can "re-use" the asset
    s.associate_asset('module.name2', 'foo.js')
    
    # And its an error to overload it
    with raises(TypeError):
        s.associate_asset('module.name2', 'foo.js', 'zzz')
    
    # Add one more
    s.associate_asset('module.name2', 'bar.js', 'yyy')
    
    # Check
    assert s.get_associated_assets('module.name1') == ('foo.js', )
    assert s.get_associated_assets('module.name2') == ('foo.js', 'bar.js')


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
    
    # # Add url data
    # s.add_shared_data('readme', 'https://github.com/zoofIO/flexx/blob/master/README.md')
    # # assert 'Flexx is' in s.get_data('readme').decode()
    # assert s.get_data('readme').startswith('https://github')
    
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


def test_not_allowing_local_files():
    """ At some point, flexx allowed adding local files as data, but
    this was removed for its potential security whole. This test
    is a remnant to ensure its gone.
    """
    
    s = AssetStore()
    
    # Add shared data from local file, dont allow!
    filename = __file__
    assert os.path.isfile(filename)
    with raises(TypeError):
        s.add_shared_data('testfile3', 'file://' + filename)
    
    # Add local file without "file://" prefix
    if sys.version_info > (3, ):
        with raises(TypeError):
            s.add_shared_data('testfile4', filename)


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
    
    s = Session('', store)
    s.add_data('bar.png', b'x')
    
    store.export(dir)
    s._export_data(dir)
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


run_tests_if_main()
