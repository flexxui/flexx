"""
Verify that the app runtimes do not leave profile directories around. We've
had xul spam the  user directory before, and we want to make sure that does not
happen again.
"""

import os
import time
import tempfile

from flexx import webruntime
from flexx.util.testing import run_tests_if_main

userdir = os.path.expanduser('~')


def index():
    """ Get a set of filenames for the current user directory.
    """
    filenames = set()
    for root, dirs, files in os.walk(userdir):
        for fname in files:
            filenames.add(os.path.join(root, fname))
    return filenames


def notrailtester(runtime, n=4):
    
    html_filename = os.path.join(tempfile.gettempdir(), 'flexx_empty_page.html')
    with open(html_filename, 'wb') as f:
        f.write('<html><body>test page</body></html>'.encode())
    
    before = index()
    
    for i in range(n):
        x = webruntime.launch(html_filename, 'xul')
        time.sleep(1.5)
        x.close()
        time.sleep(0.5)
    
    after = index()
    
    extra_files = after.difference(before)
    extra_files2 = [f for f in extra_files
                    if not f.startswith((webruntime.TEMP_APP_DIR,
                                         webruntime.RUNTIME_DIR))]
    
    print(extra_files2)
    assert len(extra_files2) < n


def test_notrail_xul():
    notrailtester('xul')


def test_notrail_xul():
    notrailtester('nwjs')


run_tests_if_main()
