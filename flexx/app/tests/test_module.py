"""
Test the Module class that represents a JS module corresponding to a
Python module.
"""

import os
import sys
import time
import tempfile
import shutil

from flexx.util.testing import run_tests_if_main, raises
from flexx.util.logging import capture_log

from flexx import ui, app
from flexx.app._modules import JSModule

tempdirname = os.path.join(tempfile.gettempdir(), 'flexx_module_test')

files = {}

files['__init__'] = """
    def x():
        pass
"""

files['foo'] = """
    from flexx import app, pyscript
    from flxtest.lib3 import tan, atan
    from flxtest.lib4 import magic_number, random
    
    import sys
    sas = None
    console = pyscript.JSConstant('console')
    
    def do_something():
        console.log('do something')
        return 40 + tan(1)
    
    def do_more():
        return atan(1) + random(magic_number)
    
    class Foo(app.Model):
        
        CSS = ".foo-css-rule {}"
        
        class JS:
            def init(self):
                do_something()
"""

files['bar'] = """
    from flxtest import lib1
    from flxtest import lib2
    from flxtest.lib2 import AA
    from flxtest.foo import Foo
    
    def use_lib1():
        return lib1.sin
    
    def use_lib1_wrong():
        return lib1.sinasappel
    
    def use_lib2():
        return lib2.cos
    
    class BB(AA):
        pass
    
    class CC(BB):
        pass
    
    class Bar(Foo):
        pass
    
    class Spam(Bar):
        pass
    
    def cannot_transpile():
        with AA(object):  # no with-statement in Flexx
            pass
    
    cannot_serialize = [1, 2, use_lib1]
    
    cannot_do_anything = BB()
"""

files['lib1'] = """
    __pyscript__ = True
    
    sas = None
    
    offset = 2
    def sin(t):
        return t + offset
    
    def asin(t):
        return t - offset
    
"""

files['lib2'] = """
    
    from flexx.pyscript import RawJS
    
    import sys
    sas = None
    
    offset = 3
    bias = RawJS("[]")
    
    def cos(t):
        return t + offset + bias
    
    def acos(t):
        return t - offset + bias
    
    class AA(object):
        pass
    
"""

files['lib3'] = """
    from flxtest.lib1 import sin
    from flxtest.lib2 import cos, offset, bias
    from flxtest import x
    
    def tan(t):
        return sin(t) / cos(t) + offset * 0 + bias + x()
    
    def atan(t):
        return 1/tan(t)
"""

files['lib4'] = """
    magic_number = 42
    def random():
        return 1
"""


PKG_NAME = 'flxtest'

def setup_module():
    packdirname = os.path.join(tempdirname, PKG_NAME)
    if not os.path.isdir(tempdirname):
        os.makedirs(tempdirname)
    if not os.path.isdir(packdirname):
        os.makedirs(packdirname)
    
    sys.path.insert(0, tempdirname)
    
    for name in files:
        # Mangle names
        text = '\n'.join(line[4:] for line in files[name].splitlines())
        # Write code
        filename = os.path.join(packdirname, name + '.py')
        with open(filename, 'wb') as f:
            f.write(text.encode())


def teardown_module():
    if os.path.isdir(tempdirname):
        shutil.rmtree(tempdirname)

    while tempdirname in sys.path:
        sys.path.remove(tempdirname)
    
    # Remove trace of these classes, since their source no longer exists,
    # Pyscript wont be able to resolve them for JS
    for cls in list(app.Model.CLASSES):
        if cls.__jsmodule__.startswith(PKG_NAME + '.'):
            app.Model.CLASSES.remove(cls)


def test_modules():
    
    import flxtest.foo
    
    store = {}
    
    m = JSModule('flxtest.foo', store)
    
    assert len(store) == 1
    
    # Add Foo, this will bring everything else in
    m.add_variable('Foo')
    
    assert len(m.model_classes) == 1
    assert m.model_classes.pop().__name__ == 'Foo'
    
    # Modules exists
    assert len(store) == 7
    assert 'flxtest.foo' in store
    assert 'flxtest.lib1' in store
    assert 'flxtest.lib2' in store
    assert 'flxtest.lib3' in store
    assert 'flxtest.__init__' in store  # different from how Python works!
    assert 'flexx.app._model' in store  # + what it depends on
    
    # CSS
    assert 'foo-css-rule' in store['flxtest.foo'].get_css()
    
    # Stubs prevented loading of console
    assert 'console =' not in store['flxtest.foo'].get_js()
    
    # Function defs defined
    assert 'sin = function' in store['flxtest.lib1'].get_js()
    assert 'asin = function' in store['flxtest.lib1'].get_js()  # __pyscript__
    assert 'cos = function' in store['flxtest.lib2'].get_js()
    assert 'acos = function' not in store['flxtest.lib2'].get_js()  # not __pyscript__
    assert 'tan = function' in store['flxtest.lib3'].get_js()
    assert 'do_something = function' in store['flxtest.foo'].get_js()
    
    # Function defs imported
    assert 'sin = flxtest_lib1.sin' in store['flxtest.lib3'].get_js()
    assert 'cos = flxtest_lib2.cos' in store['flxtest.lib3'].get_js()
    assert 'tan = flxtest_lib3.tan' in store['flxtest.foo'].get_js()
    
    # Unused constants 
    assert 'sys' not in store['flxtest.foo'].get_js()
    assert 'sas' not in store['flxtest.foo'].get_js()
    assert 'sys' not in store['flxtest.lib2'].get_js()
    assert 'sas' not in store['flxtest.lib2'].get_js()
    assert 'sas' in store['flxtest.lib1'].get_js()  # __pyscript__
    
    # Constants replicate, not import
    assert 'offset = 3' in store['flxtest.lib2'].get_js()
    assert 'offset = 3' in store['flxtest.lib3'].get_js()
    
    # But RawJS constants can be shared!
    assert 'bias = []' in store['flxtest.lib2'].get_js()
    assert 'bias = flxtest_lib2.bias' in store['flxtest.lib3'].get_js()
    
    # So ,,, lib4 is omitted, right?
    assert 'flxtest.lib4' not in store
    assert 'magic_number' not in store['flxtest.foo'].get_js()
    assert 'random' not in store['flxtest.foo'].get_js()
    assert 'atan' not in store['flxtest.foo'].get_js()
    assert 'atan' not in store['flxtest.lib3'].get_js()
    
    # Use more of foo module
    m.add_variable('do_more')
    
    # Now, lib4 is used
    assert len(store) == 8
    assert 'flxtest.lib4' in store
    
    # And names added in foo
    assert 'magic_number = 42' in store['flxtest.foo'].get_js()
    assert 'random' in store['flxtest.foo'].get_js()
    assert 'atan' in store['flxtest.foo'].get_js()
    assert 'atan' in store['flxtest.lib3'].get_js()


def test_misc():
    import flxtest.foo
    store = {}
    
    # repr
    m = JSModule('flxtest.foo', store)
    assert '0' in repr(m)
    m.add_variable('do_something')
    assert '1' in repr(m)
    m.add_variable('do_more')
    assert '3' in repr(m)  # also the const
    
    # Deps
    assert len(m.deps) == 2
    assert 'flxtest.lib3' in m.deps
    assert 'flxtest.lib4' in m.deps
    #
    m.add_variable('Foo')
    assert len(m.deps) == 3
    assert 'flexx.app._model' in m.deps


def test_add_variable():
    import flxtest.foo
    import flxtest.bar
    store = {}
    
    m = JSModule('flxtest.foo', store)
    
    assert not m.variables
    m.add_variable('Foo')
    assert 'Foo' in m.variables
    
    # add_variable is ignored for pyscript mods
    assert not store['flxtest.lib1'].deps
    with capture_log('info') as log:
        store['flxtest.lib1'].add_variable('spam')  
    assert not log
    
    # add_variable warns for other mods
    with capture_log('info') as log:
        store['flxtest.lib2'].add_variable('spam')  
    assert len(log) == 1 and 'undefined variable' in log[0]
    
    with raises(ValueError):
        store['flxtest.lib2'].add_variable('spam', is_global=True)
    
    m = JSModule('flxtest.bar', store)
    
    # Can use stuff from module if its a __pyscript__ modules
    m.add_variable('use_lib1')
    
    # Even if name makes no sense; maybe it has exports that we do not know of
    m.add_variable('use_lib1_wrong')
    
    # But not for regular modules
    with raises(ValueError) as err:
        m.add_variable('use_lib2')
    assert '__pyscript__' in str(err)
    
    
    # Has changed flag
    our_time = time.time(); time.sleep(0.01)
    m = JSModule('flxtest.bar', {})
    time.sleep(0.01); our_time = time.time();
    m.get_js()
    #
    our_time = time.time(); time.sleep(0.01)
    m.add_variable('use_lib1')
    m.add_variable('AA')
    #
    our_time = time.time(); time.sleep(0.01)
    m.add_variable('use_lib1')  # no effect because already known
    #
    m.add_variable('AA')  # no effect bacause is imported name


def test_subclasses():
    
    import flxtest.foo
    import flxtest.bar
    
    # Using a class CC > BB > AA > object
    store = {}
    JSModule('flxtest.foo', store).add_variable('Foo')
    m = JSModule('flxtest.bar', store)
    #
    assert 'CC' not in m.get_js()
    assert 'BB' not in m.get_js()
    assert 'AA' not in store['flxtest.lib2'].get_js()
    #
    m.add_variable('CC')
    assert 'CC' in m.get_js()
    assert 'BB' in m.get_js()
    assert 'AA' in store['flxtest.lib2'].get_js()
    
    # Using a class Spam > Bar > Foo > Model
    store = {}
    m = JSModule('flxtest.bar', store)
    assert 'flxtest.foo' not in store
    #
    m.add_variable('Spam')
    assert 'flxtest.foo' in store
    assert 'flexx.app._model' in store
    
    # Using Foo in modules that imports it
    store = {}
    m = JSModule('flxtest.bar', store)
    assert 'flxtest.foo' not in store
    #
    m.add_variable('Foo')
    assert 'flxtest.foo' in store
    assert 'flexx.app._model' in store


def test_fails():
    
    import flxtest.foo
    import flxtest.bar
    
    assert JSModule('flxtest.foo', {})
    
    # Wrong init
    with raises(TypeError):
        JSModule()
    with raises(TypeError):
        JSModule('flxtest.foo')
    with raises(TypeError):
        JSModule(3, {})
    with raises(TypeError):
        JSModule('flxtest.foo', 3)
    with raises(TypeError):
        JSModule('flxtest.foo', {}, 3)
    
    # Name issues
    with raises(ValueError):
        JSModule('flxtest.doesnotexist', {})
    with raises(ValueError):
        JSModule('flxtest', {})  # must be flxtest.__init__
    with raises(ValueError):
        JSModule('flxtest.foo.__init__', {})  # only for actual package names!
        
    # Cannot create module with same name twice (in same store)
    store = {}
    JSModule('flxtest.foo', store)
    with raises(RuntimeError):
        JSModule('flxtest.foo', store)
    JSModule('flxtest.foo', {})  # in alt store its ok though
    
    # Untranspilable
    m = JSModule('flxtest.bar', {})
    with raises(ValueError) as err:
        m.add_variable('cannot_transpile')
    assert 'cannot transpile' in str(err)
    
    # Unserializable
    m = JSModule('flxtest.bar', {})
    with raises(ValueError) as err:
        m.add_variable('cannot_serialize')
    assert 'cannot serialize' in str(err)
    
    # Un-anythingable
    m = JSModule('flxtest.bar', {})
    with raises(ValueError) as err:
        m.add_variable('cannot_do_anything')
    assert 'cannot convert' in str(err)


run_tests_if_main()
