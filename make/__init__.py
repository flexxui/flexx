# License: consider this public domain

"""
Convenience tools for developers

    python make command [arg]

"""

from __future__ import absolute_import, division, print_function

import os
import sys

# Get root directory of the package and select it
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)
os.chdir(ROOT_DIR)

# Definions - these can change per project
NAME = 'flexx'
DOC_DIR = os.path.join(ROOT_DIR, 'doc')
DOC_BUILD_DIR = os.path.join(DOC_DIR, '_build')


def main():
    if len(sys.argv) == 1:
        run('help', '')
    else:
        command = sys.argv[1].strip()
        arg = ' '.join(sys.argv[2:]).strip()
        run(command, arg)


def run(command, arg):
    # Import the module that defines the command
    if not os.path.isfile(os.path.join(THIS_DIR, command + '.py')):
        sys.exit('Invalid command: %r' % command)
    makemodule = __import__('make.'+command)
    # Get the corresponding function
    m = getattr(makemodule, command)
    f = getattr(m, command, None)
    # Call or fail
    if f is None:
        sys.exit('Module %s.py does not contain function %s().' % 
                 (command, command))
    f(arg)


def help(arg=''):
    run('help', arg)
