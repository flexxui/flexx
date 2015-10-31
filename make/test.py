""" Run tests.
* unit - run unit tests
* style - flake style testing (PEP8 and more)
* cover - open html coverage report in web browser

For 'unit' and 'style' the relative dir to test can be specified as an
additional argument.
"""

import os
import sys

from make import ROOT_DIR, NAME, run


def test(arg='', *args):
   
    if not arg:
        return run('help', 'test')
    elif arg == 'unit':
        test_unit(*args)
    elif arg in ('style', 'flake', 'flake8'):
        test_style(*args)
    elif arg in ('cover', 'coverage'):
        show_coverage_html(*args)
    else:
        sys.exit('invalid test mode %r' % arg)


def test_unit(rel_path='.'):
    
    try:
        import pytest  # noqa
    except ImportError:
        sys.exit('Cannot do unit tests, pytest not installed')
    
    _enable_faulthandler()
    
    cov_report = '--cov-report=term --cov-report=html'
    os.chdir(ROOT_DIR)
    try:
        res = pytest.main('--cov %s --cov-config=.coveragerc %s %r' % 
                          (NAME, cov_report, rel_path))
        sys.exit(res)
    finally:
        m = __import__(NAME)
        print('Tests were performed on', str(m))


def show_coverage_term():
    from coverage import coverage
    cov = coverage(auto_data=False, branch=True, data_suffix=None,
                   source=['flexx'])  # should match testing/_coverage.py
    cov.load()
    cov.report()
    
    
def show_coverage_html():
    import webbrowser
    from coverage import coverage
    
    print('Generating HTML...')
    cov = coverage(auto_data=False, branch=True, data_suffix=None,
                   source=['flexx'])  # should match testing/_coverage.py
    cov.load()
    cov.html_report()
    print('Done, launching browser.')
    fname = os.path.join(os.getcwd(), 'htmlcov', 'index.html')
    if not os.path.isfile(fname):
        raise IOError('Generated file not found: %s' % fname)
    webbrowser.open_new_tab(fname)


def test_style(rel_path='.'):
    
    try:
        from flake8.main import main  # noqa
    except ImportError:
        sys.exit('Cannot do style test, flake8 not installed')
    
    orig_dir = os.getcwd()
    orig_argv = sys.argv
    
    os.chdir(ROOT_DIR)
    sys.argv[1:] = [rel_path]
    try:
        from flake8.main import main
        main()  # Raises SystemExit
    finally:
        os.chdir(orig_dir)
        sys.argv[:] = orig_argv


class FileForTesting(object):
    """ Alternative to stdout that makes path relative to ROOT_DIR
    """
    def __init__(self, original):
        self._original = original
    
    def write(self, msg):
        if msg.startswith(ROOT_DIR):
            msg = os.path.relpath(msg, ROOT_DIR)
        self._original.write(msg)
        self._original.flush()
    
    def flush(self):
        self._original.flush()
    
    def revert(self):
        sys.stdout = self._original


def _enable_faulthandler():
    """ Enable faulthandler (if we can), so that we get tracebacks
    on segfaults.
    """
    try:
        import faulthandler
        faulthandler.enable()
        print('Faulthandler enabled')
    except Exception:
        print('Could not enable faulthandler')
