""" Clear all .pyc modules and __pycache__ dirs
"""

import os
import shutil
import fnmatch

from make import ROOT_DIR


def clean(arg=''):
    
    count1, count2 = 0, 0
    
    for root, dirnames, filenames in os.walk(ROOT_DIR):
        for dirname in dirnames:
            if dirname == '__pycache__':
                shutil.rmtree(os.path.join(root, dirname))
                count1 += 1
    print('removed %i __pycache__ dirs' % count1)
    
    for root, dirnames, filenames in os.walk(ROOT_DIR):
        for filename in fnmatch.filter(filenames, '*.pyc'):
            os.remove(os.path.join(root, filename))
            count2 += 1
    print('removed %i .pyc files' % count2)
