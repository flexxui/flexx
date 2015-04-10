""" Generate html report from .coverage and show in HTML
"""

import os
import os.path as op
import webbrowser

from coverage import coverage as coverage_

def coverage(arg):
    print('Generating HTML...')
    cov = coverage_(auto_data=False, branch=True, data_suffix=None,
                   source=['flexx'])  # should match testing/_coverage.py
    cov.load()
    cov.html_report()
    print('Done, launching browser.')
    fname = op.join(os.getcwd(), 'htmlcov', 'index.html')
    if not op.isfile(fname):
        raise IOError('Generated file not found: %s' % fname)
    webbrowser.open_new_tab(fname)