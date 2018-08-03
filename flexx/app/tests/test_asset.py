"""
Tests for Asset AssetStore and SessionAssets.

Note that our docs is very much a test for our export mechanism.
"""

import os
import sys
import tempfile
import shutil

from flexx.util.testing import run_tests_if_main, raises, skip

from flexx.app._asset import solve_dependencies, get_mod_name, module_is_package
from flexx.util.logging import capture_log
from flexx import app


N_STANDARD_ASSETS = 3

test_filename = os.path.join(tempfile.gettempdir(), 'flexx_asset_cache.test')


class WTF:
    pass


def test_get_mod_name():
    assert get_mod_name(app.PyComponent) == 'flexx.app._component2'
    assert get_mod_name(app._component2) == 'flexx.app._component2'
    assert get_mod_name(app) == 'flexx.app.__init__'


def test_asset():

    # Initialization

    asset1 = app.Asset('foo.js', 'foo=3')
    assert 'foo.js' in repr(asset1)
    assert 'foo.js' == asset1.name
    assert asset1.source == 'foo=3'

    asset2 = app.Asset('bar.css', 'bar=2')
    assert 'bar.css' in repr(asset2)
    assert 'bar.css' == asset2.name
    assert asset2.source == 'bar=2'

    with raises(TypeError):
        app.Asset()  # :/
    with raises(TypeError):
        app.Asset('foo.js')  # need source

    with raises(TypeError):
        app.Asset(3, 'bar=2')  # name not a str
    with raises(ValueError):
        app.Asset('foo.png', '')  # js and css only
    with raises(TypeError):
        app.Asset('bar.css', 3)  # source not str
    with raises(TypeError):
        app.Asset('bar.css', ['a'])  # source not str

    # To html JS
    asset = app.Asset('foo.js', 'foo=3;bar=3')
    code = asset.to_html('', 0)
    assert code.startswith('<script') and code.strip().endswith('</script>')
    assert 'foo=3' in code
    assert '\n' not in code  # because source had no newlines

    asset = app.Asset('foo.js', 'foo=3\nbar=3')
    code = asset.to_html('', 0)
    assert code.startswith('<script') and code.strip().endswith('</script>')
    assert '\nfoo=3\nbar=3\n' in code  # note the newlines

    asset = app.Asset('foo.js', 'foo=3\nbar=3')
    code = asset.to_html()
    assert code.startswith('<script ') and code.strip().endswith('</script>')
    assert 'foo=' not in code
    assert '\n' not in code  # because its a link

    # To html CSS
    asset = app.Asset('bar.css', 'foo=3;bar=3')
    code = asset.to_html('', 0)
    assert code.startswith('<style') and code.strip().endswith('</style>')
    assert 'foo=' in code
    assert '\n' not in code  # because source had no newlines

    asset = app.Asset('bar.css', 'foo=3\nbar=3')
    code = asset.to_html('', 0)
    assert code.startswith('<style') and code.strip().endswith('</style>')
    assert '\nfoo=3\nbar=3\n' in code  # note the newlines

    asset = app.Asset('bar.css', 'foo=3\nbar=3')
    code = asset.to_html()
    assert code.startswith('<link') and code.strip().endswith('/>')
    assert 'foo-' not in code
    assert '\n' not in code  # becasue its a link

    # Test asset via uri
    fname = 'file:///home/xx/foobar.css'
    with raises(TypeError):
        app.Asset('bar.css', fname)
    with raises(TypeError):
        app.Asset(fname)


def test_remote_asset():

    # Prepare example asset info
    # Note: use http instead of https to avoid spurious certificate errors
    bootstrap_url = 'http://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
    jquery_url = 'http://code.jquery.com/jquery-3.1.1.slim.min.js'
    with open(test_filename + '.js', 'wb') as f:
        f.write('var blablabla=7;'.encode())

    # JS from url
    asset = app.Asset(jquery_url)
    assert asset.remote
    assert asset.source == jquery_url
    assert 'jQuery v3.1.1' in asset.to_string()
    assert 'jQuery v3.1.1' in asset.to_html('{}', 0)
    assert 'jQuery v3.1.1' not in asset.to_html('{}', 1)
    assert 'jQuery v3.1.1' not in asset.to_html('{}', 2)
    assert 'jQuery v3.1.1' not in asset.to_html('{}', 3)
    assert 'src=' not in asset.to_html('{}', 0)
    assert 'src=' in asset.to_html('{}', 1)
    assert 'src=' in asset.to_html('{}', 2)
    assert 'src=' in asset.to_html('{}', 3)
    assert 'http://' in asset.to_html('{}', 1)
    assert 'http://' not in asset.to_html('{}', 2)
    assert 'http://' in asset.to_html('{}', 3)

    # CSS from url
    asset = app.Asset(bootstrap_url)
    assert asset.remote
    assert asset.source == bootstrap_url
    assert 'Bootstrap v3.3.7' in asset.to_string()
    assert 'Bootstrap v3.3.7' in asset.to_html('{}', 0)
    assert 'Bootstrap v3.3.7' not in asset.to_html('{}', 1)
    assert 'Bootstrap v3.3.7' not in asset.to_html('{}', 2)
    assert 'Bootstrap v3.3.7' not in asset.to_html('{}', 3)
    assert 'href=' not in asset.to_html('{}', 0)
    assert 'href=' in asset.to_html('{}', 1)
    assert 'href=' in asset.to_html('{}', 2)
    assert 'href=' in asset.to_html('{}', 3)
    assert 'http://' in asset.to_html('{}', 1)
    assert 'http://' not in asset.to_html('{}', 2)
    assert 'http://' in asset.to_html('{}', 3)

    # Falis
    with raises(TypeError):  # JS from file - not allowed
        app.Asset('file://' + test_filename + '.js')
    with raises(TypeError):
         app.Asset(jquery_url, 'foo=3')  # no sources for remote asset
    with raises(TypeError):
         app.Asset(jquery_url, ['foo=3'])  # no sources for remote asset


def test_lazy_asset():
    side_effect = []

    def lazy():
        side_effect.append(True)
        return 'spaaam'

    asset = app.Asset('foo.js', lazy)
    assert asset.source is lazy
    assert not side_effect

    assert asset.to_string() == 'spaaam'
    assert side_effect

    while side_effect:
        side_effect.pop(0)

    assert asset.to_string() == 'spaaam'
    assert not side_effect

    # Fail

    def lazy_wrong():
        return None

    asset = app.Asset('foo.js', lazy_wrong)
    assert asset.source is lazy_wrong

    with raises(ValueError):
        asset.to_string()


def test_bundle():

    try:
        from flexx import ui
    except ImportError:
        skip('no flexx.ui')

    store = {}
    m1 = app.JSModule('flexx.ui.widgets._button', store)
    m1.add_variable('Button')
    m2 = app.JSModule('flexx.ui.widgets._tree', store)
    m2.add_variable('TreeWidget')
    m3 = store['flexx.ui._widget']  # because its a dep of the above

    # JS bundle
    bundle = app.Bundle('flexx.ui.js')
    assert 'flexx.ui' in repr(bundle)

    bundle.add_module(m1)
    bundle.add_module(m2)
    bundle.add_module(m3)

    # Modules are sorted
    assert bundle.modules == (m3, m1, m2)

    # Deps are agregated
    assert 'flexx.app.js' in bundle.deps
    assert 'flexx.app._component2.js' in bundle.deps
    assert not any('flexx.ui' in dep for dep in bundle.deps)

    # Strings are combined
    code = bundle.to_string()
    assert '$Widget =' in code
    assert '$Button =' in code
    assert '$TreeWidget =' in code

    # CSS bundle
    bundle = app.Bundle('flexx.ui.css')
    bundle.add_module(m1)
    bundle.add_module(m2)
    bundle.add_module(m3)
    #
    code = bundle.to_string()
    assert '.Widget =' not in code
    assert '.flx-Widget {' in code
    assert '.flx-TreeWidget {' in code

    # This works too
    bundle = app.Bundle('-foo.js')
    bundle.add_module(m1)

    # But this does not
    bundle = app.Bundle('foo.js')
    with raises(ValueError):
        bundle.add_module(m1)

    # Assets can be bundled too

    bundle = app.Bundle('flexx.ui.css')
    bundle.add_module(m1)
    bundle.add_module(m2)

    a1 = app.Asset('foo.css', 'foo-xxx')
    a2 = app.Asset('bar.css', 'bar-yyy')
    bundle.add_asset(a1)
    bundle.add_asset(a2)

    assert a1 in bundle.assets
    assert a2 in bundle.assets

    code = bundle.to_string()
    assert 'foo-xxx' in code
    assert 'bar-yyy' in code

    with raises(TypeError):
        bundle.add_asset()
    with raises(TypeError):
        bundle.add_asset(3)
    with raises(TypeError):
        bundle.add_asset(bundle)  # no bundles


## Sorting


class Thing:
    """ An object that can be sorted with solve_dependencies().
    """

    def __init__(self, name, deps):
        self.name = name
        self.deps = deps


def test_dependency_resolution_1():
    """ No deps, maintain order. """

    a1 = Thing('a1.js', [])
    a2 = Thing('a2.js', [])
    a3 = Thing('a3.js', [])

    aa = a1, a2, a3
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['a1.js', 'a2.js', 'a3.js']


def test_dependency_resolution_2():
    """ One chain of deps """

    a1 = Thing('a1.js', ['b1.js'])
    b1 = Thing('b1.js', ['c1.js'])
    c1 = Thing('c1.js', ['d1.js'])
    d1 = Thing('d1.js', ['e1.js'])
    e1 = Thing('e1.js', [])
    # e1 = Thing('e1.js', '', ['f1.js'])
    # f1 = Thing('f1.js', '', ['g1.js'])
    # g1 = Thing('g1.js', '', [])

    aa = a1, b1, c1, d1, e1
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['e1.js', 'd1.js', 'c1.js', 'b1.js', 'a1.js']

    aa = a1, d1, e1, b1, c1
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['e1.js', 'd1.js', 'c1.js', 'b1.js', 'a1.js']


def test_dependency_resolution_3():
    """ Unkown deps are ignored (but warned for) """

    a1 = Thing('a1.js', ['b1.js'])
    b1 = Thing('b1.js', ['bar.js', 'c1.js'])
    c1 = Thing('c1.js', ['d1.js', 'foo.js'])
    d1 = Thing('d1.js', ['e1.js'])
    e1 = Thing('e1.js', [])

    aa = a1, b1, c1, d1, e1
    with capture_log('warning') as logs:
        aa = solve_dependencies(aa, warn_missing=True)
    assert logs and 'missing dependency' in logs[0]
    assert [a.name for a in aa] == ['e1.js', 'd1.js', 'c1.js', 'b1.js', 'a1.js']


def test_dependency_resolution_4():
    """ Circular deps """

    a1 = Thing('a1.js', ['b1.js'])
    b1 = Thing('b1.js', ['c1.js'])
    c1 = Thing('c1.js', ['d1.js'])
    d1 = Thing('d1.js', ['e1.js', 'a1.js'])
    e1 = Thing('e1.js', [])

    aa = a1, b1, c1, d1, e1
    with raises(RuntimeError):
        aa = solve_dependencies(aa)


def test_dependency_resolution_5():
    """ Two chains """

    a1 = Thing('a1.js', ['b1.js'])
    b1 = Thing('b1.js', ['c1.js'])
    c1 = Thing('c1.js', ['d1.js'])

    a2 = Thing('a2.js', ['b2.js'])
    b2 = Thing('b2.js', ['c2.js'])
    c2 = Thing('c2.js', ['d2.js'])

    # First the chain 1
    aa = a1, b1, c1, a2, b2, c2
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['c1.js', 'b1.js', 'a1.js', 'c2.js', 'b2.js', 'a2.js']

    # First the chain 2
    aa = a2, b2, c2, a1, b1, c1
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == [ 'c2.js', 'b2.js', 'a2.js', 'c1.js', 'b1.js', 'a1.js']

    # Mix, put el from chain 1 first
    aa = a1, a2, b1, b2, c1, c2
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['c1.js', 'b1.js', 'a1.js', 'c2.js', 'b2.js', 'a2.js']

    # Mix, put el from chain 2 first
    aa = a2, a1, b1, b2, c1, c2
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == [ 'c2.js', 'b2.js', 'a2.js', 'c1.js', 'b1.js', 'a1.js']


def test_dependency_resolution_6():
    """ Multiple deps - order """

    a1 = Thing('a1.js', ['b1.js', 'b2.js'])
    b1 = Thing('b1.js', ['c1.js', 'c2.js'])
    b2 = Thing('b2.js', ['c2.js', 'c3.js'])
    c1 = Thing('c1.js', [])
    c2 = Thing('c2.js', [])
    c3 = Thing('c3.js', [])

    aa = a1, b1, b2, c1, c2, c3
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == [ 'c1.js', 'c2.js', 'b1.js', 'c3.js', 'b2.js', 'a1.js']


def test_dependency_resolution_7():
    """ Shared deps """

    a1 = Thing('a1.js', ['b1.js', 'b2.js'])
    b1 = Thing('b1.js', ['c1.js'])
    b2 = Thing('b2.js', ['d1.js'])
    c1 = Thing('c1.js', ['d1.js'])
    d1 = Thing('d1.js', [])

    aa = a1, b1, b2, c1, d1
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['d1.js', 'c1.js', 'b1.js', 'b2.js', 'a1.js']


def test_dependency_resolution_8():
    """ Position of singleton thing """

    a0 = Thing('a0.js', [])
    a1 = Thing('a1.js', ['b1.js', 'b2.js'])
    b1 = Thing('b1.js', ['c1.js'])
    b2 = Thing('b2.js', ['d1.js'])
    c1 = Thing('c1.js', ['d1.js'])
    d1 = Thing('d1.js', [])

    # Stay in front
    #    \/
    aa = a0, a1, b1, b2, c1, d1
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['a0.js', 'd1.js', 'c1.js', 'b1.js', 'b2.js', 'a1.js']

    # Get send to back - after a1, and a1 gets send to back due to its deps
    #        \/
    aa = a1, a0, b1, b2, c1, d1
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['d1.js', 'c1.js', 'b1.js', 'b2.js', 'a1.js', 'a0.js']

    # Stay behind b1
    #        \/
    aa = b1, a0, a1, b2, c1, d1
    aa = solve_dependencies(aa)
    assert [a.name for a in aa] == ['d1.js', 'c1.js', 'b1.js', 'a0.js', 'b2.js', 'a1.js']


run_tests_if_main()
