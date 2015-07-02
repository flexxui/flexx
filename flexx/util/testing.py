# -*- coding: utf-8 -*-
# Copyright (c) 2015, Almar Klein
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

""" Functionality used for testing. This code itself is not covered in tests.
"""

from __future__ import absolute_import, print_function, division

import os
import sys
import inspect
import shutil
import atexit

import pytest
from _pytest import runner

# Get root dir
PACKAGE_NAME = __name__.split('.')[0]

# Get root dir
THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = THIS_DIR
for i in range(9):
    ROOT_DIR = os.path.dirname(ROOT_DIR)
    if os.path.isfile(os.path.join(ROOT_DIR, '.gitignore')):
        break


STYLE_IGNORES = ['E226', 
                 'E241', 
                 'E265', 
                 'E266',  # too many leading '#' for block comment
                 'E402',  # module level import not at top of file
                 'E731',  # do not assign a lambda expression, use a def
                 'W291', 
                 'W293',
                 ]


## Functions to use in tests

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
    pytest.main('-v -x --color=yes --cov flexx '
                '--cov-config .coveragerc --cov-report html %s' % repr(fname))
    if show_coverage:
        import webbrowser
        fname = os.path.join(ROOT_DIR, 'htmlcov', 'index.html')
        webbrowser.open_new_tab(fname)


## Functions to use from make

def test_unit(cov_report='term'):
    """ Run all unit tests. Returns exit code.
    """
    orig_dir = os.getcwd()
    os.chdir(ROOT_DIR)
    try:
        _clear_our_modules()
        _enable_faulthandler()
        return pytest.main('-v --cov %s --cov-config .coveragerc '
                           '--cov-report %s tests' % (PACKAGE_NAME, cov_report))
    finally:
        os.chdir(orig_dir)
        m = __import__(PACKAGE_NAME)
        print('Tests were performed on', str(m))


## Requirements

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
    # Remove ourselves from sys.modules to force an import
    for key in list(sys.modules.keys()):
        if key.startswith(PACKAGE_NAME) and not 'testing' in key:
            del sys.modules[key]


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
