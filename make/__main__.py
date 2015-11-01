# License: consider this public domain

from __future__ import absolute_import, division, print_function

import sys
import os
import os.path as op


THIS_DIR = op.dirname(op.abspath(__file__))
ROOT_DIR = op.dirname(THIS_DIR)

# Setup paths
os.chdir(ROOT_DIR)
sys.path.insert(0, '.')
if 'make' in sys.path:
    sys.path.remove('make')

# Import __init__ with project specific dirs
import make
assert ROOT_DIR == make.ROOT_DIR


def run(command, *args):
    """ Run command with specified args.
    """
    # Import the module that defines the command
    if not op.isfile(op.join(THIS_DIR, command + '.py')):
        sys.exit('Invalid command: %r' % command)
    makemodule = __import__('make.'+command)
    # Get the corresponding function
    m = getattr(makemodule, command)
    f = getattr(m, command, None)
    # Call or fail
    if f is None:
        sys.exit('Module %s.py does not contain function %s().' % 
                 (command, command))
    f(*args)


def main():
    if len(sys.argv) == 1:
        run('help')
    else:
        command = sys.argv[1].strip()
        run(command, *sys.argv[2:])


# Put some funcs in make namespace
make.run = run

main()
