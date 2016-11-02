"""
Test the Module class that represents a JS module corresponding to a
Python module.
"""

import os
import sys
import tempfile
import shutil

from flexx.util.testing import run_tests_if_main, raises
from flexx.util.logging import capture_log

from flexx import ui, app
from flexx.app.modules import JSModule

tempdirname = os.path.join(tempfile.gettempdir(), 'flexx_module_test')

files = {}

files['foo'] = """
    from flexx import app, pyscript
    from lib3 import tan, atan
    from lib4 import magic_number, random
    
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
    import lib1
    import lib2
    from lib2 import AA
    from foo import Foo
    
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
        with AA():  # no with-statement in Flexx
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
    
    import sys
    sas = None
    
    offset = 3
    
    def cos(t):
        return t + offset
    
    def acos(t):
        return t - offset
    
    class AA:
        pass
    
"""

files['lib3'] = """
    from lib1 import sin
    from lib2 import cos, offset
    
    def tan(t):
        return sin(t) / cos(t) + offset * 0
    
    def atan(t):
        return 1/tan(t)
"""

files['lib4'] = """
    magic_number = 42
    def random():
        return 1
"""



def setup_module():
    if not os.path.isdir(tempdirname):
        os.makedirs(tempdirname)
    
    sys.path.insert(0, tempdirname)
    
    for name in files:
        # Mangle names
        text = '\n'.join(line[4:] for line in files[name].splitlines())
        for key in files:
            text = text.replace(key, 'flexx_' + key)
        # Write code
        filename = os.path.join(tempdirname, 'flexx_' + name + '.py')
        with open(filename, 'wb') as f:
            f.write(text.encode())


def teardown_module():
    if os.path.isdir(tempdirname):
        shutil.rmtree(tempdirname)

    while tempdirname in sys.path:
        sys.path.remove(tempdirname)


def test_modules():
    
    import flexx_foo
    
    store = {}
    
    m = JSModule(flexx_foo, store)
    
    assert len(store) == 1
    
    # Add Foo, this will bring everything else in
    m.add_variable('Foo')
    
    # Modules exists
    assert len(store) == 5
    assert 'flexx_foo' in store
    assert 'flexx_lib1' in store
    assert 'flexx_lib2' in store
    assert 'flexx_lib3' in store
    assert 'flexx.app.model' in store
    
    # CSS
    assert 'foo-css-rule' in store['flexx_foo'].get_css()
    
    # Stubs prevented loading of console
    assert 'console =' not in store['flexx_foo'].get_js()
    
    # Function defs defined
    assert 'sin = function' in store['flexx_lib1'].get_js()
    assert 'asin = function' in store['flexx_lib1'].get_js()  # __pyscript__
    assert 'cos = function' in store['flexx_lib2'].get_js()
    assert 'acos = function' not in store['flexx_lib2'].get_js()  # not __pyscript__
    assert 'tan = function' in store['flexx_lib3'].get_js()
    assert 'do_something = function' in store['flexx_foo'].get_js()
    
    # Function defs imported
    assert 'sin = flexx_lib1.sin' in store['flexx_lib3'].get_js()
    assert 'cos = flexx_lib2.cos' in store['flexx_lib3'].get_js()
    assert 'tan = flexx_lib3.tan' in store['flexx_foo'].get_js()
    
    # Unused constants 
    assert 'sys' not in store['flexx_foo'].get_js()
    assert 'sas' not in store['flexx_foo'].get_js()
    assert 'sys' not in store['flexx_lib2'].get_js()
    assert 'sas' not in store['flexx_lib2'].get_js()
    assert 'sas' in store['flexx_lib1'].get_js()  # __pyscript__
    
    # Constants replicate, not import
    assert 'offset = 3' in store['flexx_lib2'].get_js()
    assert 'offset = 3' in store['flexx_lib3'].get_js()
    
    # So ,,, lib4 is omitted, right?
    assert 'flexx_lib4' not in store
    assert 'magic_number' not in store['flexx_foo'].get_js()
    assert 'random' not in store['flexx_foo'].get_js()
    assert 'atan' not in store['flexx_foo'].get_js()
    assert 'atan' not in store['flexx_lib3'].get_js()
    
    # Use more of foo module
    m.add_variable('do_more')
    
    # Now, lib4 is used
    assert len(store) == 6
    assert 'flexx_lib4' in store
    
    # And names added in foo
    assert 'magic_number = 42' in store['flexx_foo'].get_js()
    assert 'random' in store['flexx_foo'].get_js()
    assert 'atan' in store['flexx_foo'].get_js()
    assert 'atan' in store['flexx_lib3'].get_js()


def test_misc():
    import flexx_foo
    store = {}
    
    # repr
    m = JSModule(flexx_foo, store)
    assert '0' in repr(m)
    m.add_variable('do_something')
    assert '1' in repr(m)
    m.add_variable('do_more')
    assert '3' in repr(m)  # also the const
    
    # Deps
    assert len(m.deps) == 2
    assert 'flexx_lib3' in m.deps
    assert 'flexx_lib4' in m.deps
    #
    m.add_variable('Foo')
    assert len(m.deps) == 3
    assert 'flexx.app.model' in m.deps


def test_add_variable():
    import flexx_foo
    import flexx_bar
    store = {}
    
    m = JSModule(flexx_foo, store)
    m.add_variable('Foo')
    
    # add_variable is ignored for pyscript mods
    assert not store['flexx_lib1'].deps
    with capture_log('info') as log:
        store['flexx_lib1'].add_variable('spam')  
    assert not log
    
    # add_variable warns for other mods
    with capture_log('info') as log:
        store['flexx_lib2'].add_variable('spam')  
    assert len(log) == 1 and 'does not have variable' in log[0]
    
    
    m = JSModule(flexx_bar, store)
    
    # Can use stuff from module if its a __pyscript__ modules
    m.add_variable('use_flexx_lib1')
    
    # Even if name makes no sense; maybe it has exports that we do not know of
    m.add_variable('use_flexx_lib1_wrong')
    
    # But not for regular modules
    with raises(ValueError) as err:
        m.add_variable('use_flexx_lib2')
    assert '__pyscript__' in str(err)


def test_subclasses():
    
    import flexx_foo
    import flexx_bar
    
    # Using a class CC > BB > AA > object
    store = {}
    JSModule(flexx_foo, store).add_variable('Foo')
    m = JSModule(flexx_bar, store)
    #
    assert 'CC' not in m.get_js()
    assert 'BB' not in m.get_js()
    assert 'AA' not in store['flexx_lib2'].get_js()
    #
    m.add_variable('CC')
    assert 'CC' in m.get_js()
    assert 'BB' in m.get_js()
    assert 'AA' in store['flexx_lib2'].get_js()
    
    # Using a class Spam > Bar > Foo > Model
    store = {}
    m = JSModule(flexx_bar, store)
    assert 'flexx_foo' not in store
    #
    m.add_variable('Spam')
    assert 'flexx_foo' in store
    assert 'flexx.app.model' in store
    
    # Using Foo in modules that imports it
    store = {}
    m = JSModule(flexx_bar, store)
    assert 'flexx_foo' not in store
    #
    m.add_variable('Foo')
    assert 'flexx_foo' in store
    assert 'flexx.app.model' in store


def test_fails():
    
    import flexx_foo
    import flexx_bar
    
    assert JSModule(flexx_foo, {})
    
    # Wrong init
    with raises(TypeError):
        JSModule()
    with raises(TypeError):
        JSModule(flexx_foo)
    with raises(TypeError):
        JSModule(3, {})
    with raises(TypeError):
        JSModule(flexx_foo, 3)
    with raises(TypeError):
        JSModule(flexx_foo, {}, 3)
    
    # Cannot create module with same name twice (in same store)
    store = {}
    JSModule(flexx_foo, store)
    with raises(RuntimeError):
        JSModule(flexx_foo, store)
    JSModule(flexx_foo, {})  # in alt store its ok though
    
    # Untranspilable
    m = JSModule(flexx_bar, {})
    with raises(ValueError) as err:
        m.add_variable('cannot_transpile')
    assert 'cannot transpile' in str(err)
    
    # Unserializable
    m = JSModule(flexx_bar, {})
    with raises(ValueError) as err:
        m.add_variable('cannot_serialize')
    assert 'cannot serialize' in str(err)
    
    # Un-anythingable
    m = JSModule(flexx_bar, {})
    with raises(ValueError) as err:
        m.add_variable('cannot_do_anything')
    assert 'cannot convert' in str(err)


if __name__ == '__main__':
    print(tempdirname)
    teardown_module()
    setup_module()

    test_modules()
    test_misc()
    test_add_variable()
    test_subclasses()
    test_fails()
    
    
    run_tests_if_main()
