""" Run tests.
* unit - run unit tests
* style - flake style testing (PEP8 and more)
* cover - open html coverage report in web browser
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


def test_unit(rel_path=''):
    """ Peform unit tests using flake
    """
    # Test if pytest is there
    try:
        import pytest  # noqa
    except ImportError:
        sys.exit('Cannot do unit tests, pytest not installed')
    _enable_faulthandler()
    cov_report = '--cov-report=term --cov-report=html'
    os.chdir(ROOT_DIR)
    try:
        return pytest.main('-v --cov %s --cov-config=.coveragerc %s %r' % 
                            (NAME, cov_report, rel_path))
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


def test_style(rel_path=''):
    """ Test style using flake8
    """
    # Test if flake is there
    try:
        from flake8.main import main  # noqa
    except ImportError:
        sys.exit('Cannot do flake8 test, flake8 not installed')
    
    path = os.path.join(ROOT_DIR, rel_path)
    
    # Reporting
    print('Running flake8 on %s' % path)
    sys.stdout = FileForTesting(sys.stdout)
    
    # Init
    #ignores = STYLE_IGNORES.copy()
    fail = False
    count_ok, count_fail = 0, 0
    
    # Iterate over files
    for dir, dirnames, filenames in os.walk(path):
        dir = os.path.relpath(dir, path)
        # Skip this dir?
        exclude_dirs = set(['.git', 'docs', 'build', 'dist', '__pycache__'])
        if exclude_dirs.intersection(dir.split(os.path.sep)):
            continue
        # Check all files ...
        for fname in filenames:
            if fname.endswith('.py'):
                # Get test options for this file
                filename = os.path.join(path, dir, fname)
                #skip, extra_ignores = _get_style_test_options(filename)
                #if skip:
                #    continue
                # Test
                thisfail = _test_style(filename, [])#, ignores + extra_ignores)
                if thisfail:
                    count_fail += 1
                    fail = True
                    print('----')
                else:
                    count_ok += 1
                sys.stdout.flush()
    
    # Report result
    count_total = count_ok + count_fail
    sys.stdout.revert()
    if count_total == 0:
        raise RuntimeError('    Arg! flake8 did not check any files')
    elif count_fail:
        raise RuntimeError('    Arg! flake8 failed (errors in %i/%i files)' % 
                           (count_fail, count_total))
    else:
        print('    Hooray! flake8 passed (checked %i files)' % count_total)


def _test_style(filename, ignore):
    """ Test style for a certain file.
    """
    if isinstance(ignore, (list, tuple)):
        ignore = ','.join(ignore)
    
    orig_dir = os.getcwd()
    orig_argv = sys.argv
    
    os.chdir(ROOT_DIR)
    sys.argv[1:] = [filename]
    sys.argv.append('--ignore=' + ignore)
    try:
        from flake8.main import main
        main()
    except SystemExit as ex:
        if ex.code in (None, 0):
            return False
        else:
            return True
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
