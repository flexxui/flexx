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
    # Ensure we have pytest
    try:
        import pytest  # noqa
    except ImportError:
        sys.exit('Cannot do unit tests, pytest not installed')
    # Get path to test
    py2 = sys.version_info[0] == 2
    rel_path = 'flexx_legacy/' + rel_path if py2 else 'flexx/' + rel_path
    test_path = os.path.join(ROOT_DIR, rel_path)
    # Import flexx, from installed, or from ROOT_DIR
    if py2 or os.getenv('TEST_INSTALL', '').lower() in ('1', 'yes', 'true'):
        if ROOT_DIR in sys.path:
            sys.path.remove(ROOT_DIR)
        os.chdir(os.path.expanduser('~'))
        m = __import__(NAME)
        assert ROOT_DIR not in os.path.abspath(m.__path__[0])
    else:
        os.chdir(ROOT_DIR)
        m = __import__(NAME)
        assert ROOT_DIR in os.path.abspath(m.__path__[0])
    # Start tests
    _enable_faulthandler()
    cov_report = '--cov-report=term --cov-report=html'
    try:
        res = pytest.main('--cov %s --cov-config=.coveragerc %s %r' % 
                          (NAME, cov_report, test_path))
        sys.exit(res)
    finally:
        m = __import__(NAME)
        print('Unit tests were performed on', str(m))


def show_coverage_term():
    from coverage import coverage
    cov = coverage(auto_data=False, branch=True, data_suffix=None,
                   source=[NAME])  # should match testing/_coverage.py
    cov.load()
    cov.report()
    
    
def show_coverage_html():
    import webbrowser
    from coverage import coverage
    
    print('Generating HTML...')
    cov = coverage(auto_data=False, branch=True, data_suffix=None,
                   source=[NAME])  # should match testing/_coverage.py
    cov.load()
    cov.html_report()
    print('Done, launching browser.')
    fname = os.path.join(os.getcwd(), 'htmlcov', 'index.html')
    if not os.path.isfile(fname):
        raise IOError('Generated file not found: %s' % fname)
    webbrowser.open_new_tab(fname)


def test_style(rel_path='.'):
    # Ensure we have flake8
    try:
        import flake8  # noqa
        from flake8.main.application import Application
    except ImportError as err:
        sys.exit('Cannot do style test: ' + str(err))
    # Prepare
    os.chdir(ROOT_DIR)
    sys.argv[1:] = [rel_path]
    # Do test
    print('Running flake8 tests ...')
    app = Application()
    app.run()
    # Report
    nerrors = app.result_count
    if nerrors:
        print('Arg! Found %i style errors.' % nerrors)
    else:
        print('Hooray, no style errors found!')
    # Exit (will exit(1) if errors)
    app.exit()


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
