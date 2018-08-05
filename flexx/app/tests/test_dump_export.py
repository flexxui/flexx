"""
Test dumping apps to static assets, and exporting. The exporting
mechanism uses the dump() method, so testing either, tests the other
too to some extend. Also note that our docs is very much a test for our
export mechanism.
"""

import os
import shutil
import tempfile

from flexx import flx

from flexx.util.testing import run_tests_if_main, raises, skip



def setup_module():
    flx.manager._clear_old_pending_sessions(1)
    flx.assets.__init__()
    
    flx.assets.associate_asset(__name__, 'foo.js', 'xx')
    flx.assets.associate_asset(__name__,
        'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.21.0/codemirror.min.js')


def teardown_module():
    flx.manager._clear_old_pending_sessions(1)
    flx.assets.__init__()


class MyExportTestApp(flx.JsComponent):
    pass


def test_dump():

    # Standalone apps

    app = flx.App(MyExportTestApp)
    d = app.dump(None, 0)
    assert len(d) == 1 and 'myexporttestapp.html' in d.keys()

    app = flx.App(MyExportTestApp)
    app.serve('')
    d = app.dump(None, 0)
    assert len(d) == 1 and 'index.html' in d.keys()

    with raises(ValueError):
        d = app.dump('', 0)

    d = app.dump('index.htm', 0)
    assert len(d) == 1 and 'index.htm' in d.keys()

    # Multiple files

    d = app.dump('index.html', 2)
    fnames = list(d.keys())
    assert len(fnames) == 6 and 'index.html' in fnames
    assert 'flexx/assets/shared/foo.js' in d
    assert 'flexx/assets/shared/flexx-core.js' in d
    assert 'flexx/assets/shared/codemirror.min.js' in d

    d = app.dump('index.html', 3)
    fnames = list(d.keys())
    assert len(fnames) == 5 and 'index.html' in fnames
    assert 'flexx/assets/shared/foo.js' in d
    assert 'flexx/assets/shared/flexx-core.js' in d
    assert 'flexx/assets/shared/codemirror.min.js' not in d


def test_export():

    dir = os.path.join(tempfile.gettempdir(), 'flexx_export')
    if os.path.isdir(dir):
        shutil.rmtree(dir)

    # os.mkdir(dir) -> No, export can create this dir!

    # Create app and export
    app = flx.App(MyExportTestApp)
    app.export(dir, 0)  # standalone

    assert len(os.listdir(dir)) == 1
    assert os.path.isfile(os.path.join(dir, 'myexporttestapp.html'))

    # Expor again, now with external assets
    app.export(dir, 3)

    assert len(os.listdir(dir)) == 2
    assert os.path.isfile(os.path.join(dir, 'flexx', 'assets', 'shared', 'reset.css'))
    assert os.path.isfile(os.path.join(dir, 'flexx', 'assets', 'shared', 'flexx-core.js'))
    assert os.path.isfile(os.path.join(dir, 'flexx', 'assets', 'shared', 'foo.js'))

    # Export under specific name
    app.export(os.path.join(dir, 'foo.html'))

    assert len(os.listdir(dir)) == 3
    assert os.path.isfile(os.path.join(dir, 'foo.html'))


def test_assetstore_data():

    store = flx.assets.__class__()  # new AssetStore
    store.add_shared_data('foo.png', b'xx')

    d = store._dump_data()
    assert len(d) == 1 and 'flexx/data/shared/foo.png' in d.keys()


run_tests_if_main()
