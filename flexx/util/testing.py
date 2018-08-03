# -*- coding: utf-8 -*-
# Copyright (c) 2016, Almar Klein
# Distributed under the (new) BSD License.

"""
Functionality used for testing, based on pytest. This module is designed
to just work, without modification, in most projects.

Write your tests like this:

    from yourproject.xxx.testing import run_tests_if_main, raises, skipif
    ...
    run_tests_if_main()

Then you can run the test file as a script, which will run all tests
and report coverage. Magic!
"""


from __future__ import absolute_import, print_function, division

import os
import sys
import inspect

import pytest


PACKAGE_NAME = __name__.split('.')[0]

# Get project root dir
THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = THIS_DIR
for i in range(9):
    ROOT_DIR = os.path.dirname(ROOT_DIR)
    if os.path.basename(ROOT_DIR) == PACKAGE_NAME:
        ROOT_DIR = os.path.dirname(ROOT_DIR)
        break
else:
    print('testing.py could not find project root dir, '
          'using testing.py directory instead.')
    ROOT_DIR = THIS_DIR


# Inject some function names so they can be obtained with one import
raises = pytest.raises
skipif = pytest.mark.skipif
skip = pytest.skip


def run_tests_if_main(show_coverage=False):
    """ Run tests in a given file if it is run as a script

    Coverage is reported for running this single test. Set show_coverage to
    launch the report in the web browser.
    """
    local_vars = inspect.currentframe().f_back.f_locals
    if not local_vars.get('__name__', '') == '__main__':
        return
    # we are in a "__main__"
    os.chdir(ROOT_DIR)
    fname = str(local_vars['__file__'])
    _clear_our_modules()
    _enable_faulthandler()
    pytest.main(['-v', '-x', '--color=yes', '--cov', PACKAGE_NAME,
                 '--cov-config', '.coveragerc', '--cov-report', 'html', fname])
    if show_coverage:
        import webbrowser
        fname = os.path.join(ROOT_DIR, 'htmlcov', 'index.html')
        webbrowser.open_new_tab(fname)


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


def _clear_our_modules():
    """ Remove ourselves from sys.modules to force an import.
    """
    for key in list(sys.modules.keys()):
        if key.startswith(PACKAGE_NAME) and 'testing' not in key:
            del sys.modules[key]
