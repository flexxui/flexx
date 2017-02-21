"""
Test that importing flexx subpackages does not pull in any more flexx
submodules than strictly necessary, and not any more 3d party
dependencies than expected.
"""

import os
import sys
import subprocess

from flexx.util.testing import run_tests_if_main, raises, skip

import flexx

if '__pypy__' in sys.builtin_module_names and os.getenv('TRAVIS', '') == 'true':
    skip('These import tests are slow on pypy')

# minimum that will be imported when importing flexx
PROJECT_MODULE = flexx
MIN_MODULES = ['flexx', 'flexx.util', 'flexx._config']
PROJECT_NAME = 'flexx'

## Generic code

def loaded_modules(import_module, depth=None, all_modules=False):
    """ Import the given module in subprocess and return loaded modules

    Import a certain module in a clean subprocess and return the
    projects modules that are subsequently loaded. The given depth
    indicates the module level (i.e. depth=1 will only yield 'X.app'
    but not 'X.app.backends').
    """

    project_dir = os.path.dirname(os.path.dirname(PROJECT_MODULE.__file__))

    # Get the loaded modules in a clean interpreter
    code = "import sys, %s; print(', '.join(sys.modules))" % import_module
    res = subprocess.check_output([sys.executable, '-c', code], cwd=project_dir,
                                  stderr=subprocess.STDOUT).decode()
    loaded_modules = [name.strip() for name in res.split(',')]
    
    # Tweaks for legacy Python
    loaded_modules = [name.replace('flexx_legacy', 'flexx') for name in loaded_modules]
    if 'flexx.sys' in loaded_modules:
        loaded_modules.remove('flexx.sys')
    
    if all_modules:
        return loaded_modules

    # Select project modules at the given depth
    project_modules = set()
    for m in loaded_modules:
        if m.startswith(PROJECT_NAME) and '__future__' not in m:
            if depth:
                parts = m.split('.')
                m = '.'.join(parts[:depth])
            project_modules.add(m)
    
    return project_modules


def test_import_nothing():
    """ Not importing anything should not import any project modules. """
    modnames = loaded_modules('os', 2)
    assert modnames == set()


def test_import_project():
    """ Importing project should only pull in the minimal submodules. """
    modnames = loaded_modules(PROJECT_NAME, 2)
    assert modnames == set(MIN_MODULES)


def test_import_project_fail():
    raises(Exception, loaded_modules, PROJECT_NAME + '.foobarxx')


## below it's project specific

def test_import_flexx_util():
    modnames = loaded_modules('flexx.util', 2)
    assert modnames == set(MIN_MODULES + ['flexx.util'])

def test_import_flexx_pyscript():
    modnames = loaded_modules('flexx.pyscript', 2)
    assert modnames == set(MIN_MODULES + ['flexx.pyscript'])

def test_import_flexx_event():
    modnames = loaded_modules('flexx.event', 2)
    assert modnames == set(MIN_MODULES + ['flexx.event'])

def test_import_flexx_webruntime():
    modnames = loaded_modules('flexx.webruntime', 2)
    assert modnames == set(MIN_MODULES + ['flexx.util', 'flexx.dialite', 'flexx.webruntime'])

def test_import_flexx_app():
    modnames = loaded_modules('flexx.app', 2)
    assert modnames == set(MIN_MODULES + ['flexx.app', 'flexx.util', 'flexx.dialite', 'flexx.webruntime',
                                          'flexx.event', 'flexx.pyscript'])

def test_import_flexx_ui():
    modnames = loaded_modules('flexx.ui', 2)
    assert modnames == set(MIN_MODULES + ['flexx.app', 'flexx.util', 'flexx.dialite', 'flexx.webruntime',
                                          'flexx.event', 'flexx.pyscript', 'flexx.ui'])

def test_import_deps():
    # These do not depend on tornado
    deps = set(['tornado'])
    assert deps.difference(loaded_modules('flexx.util', 2, True)) == deps
    assert deps.difference(loaded_modules('flexx.pyscript', 2, True)) == deps
    assert deps.difference(loaded_modules('flexx.webruntime', 2, True)) == deps
    assert deps.difference(loaded_modules('flexx.event', 2, True)) == deps
    
    # But app and ui do
    assert deps.difference(loaded_modules('flexx.app', 2, True)) == set()


run_tests_if_main()
