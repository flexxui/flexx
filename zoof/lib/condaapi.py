# -*- coding: utf-8 -*-
# Copyright (c) 2014, Zoof Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -*- coding: utf-8 -*-
# Copyright (c) 2014, Zoof Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

import sys
import os
import shutil

suffix = ''.join([str(s) for s in sys.version_info[:2]])

ZOOFDIR = os.path.expanduser('~/.zoofdir_py'+suffix)
# ZOOFDIR = '/usr/zoofdir'

# Set location of condarc file, from there we control most of
# conda's behavior, such as the root env to use.
# os.environ['CONDARC'] = '/home/almar/projects/pylib/zoof/condarc'
os.environ['CONDA_ROOT'] = ZOOFDIR


# todo: if possible just use directory of zoof
# todo: GUI
# todo: julia package

def condacmd(*args):
    
    # Ensure our dir exists
    if not os.path.isdir(ZOOFDIR):
        try:
            os.makedirs(ZOOFDIR)
        except OSError as err:
            raise RuntimeError('Cannot write zoof dir: %s' % str(err))
    
    # Check if we need to init
    if not os.path.isdir(os.path.join(ZOOFDIR, 'conda-meta')):
        if args != ('init', ):
            print(args)
            condacmd('init')  # recurse
    
    if not os.path.isdir(os.path.join(ZOOFDIR, 'bin')):
        os.makedirs(os.path.join(ZOOFDIR, 'bin'))
        for fname in ('conda', 'activate', 'deactivate'):
            filename = os.path.join(ZOOFDIR, 'bin', fname)
            os.symlink('/usr/local/bin/'+fname, filename)
            # todo: better way to establish real location
    
    oldargs = sys.argv
    
    try:
        import conda
        from conda.cli import main
        sys.argv = ['conda'] + list(args)
        main()
    except SystemExit as err:
        err = str(err)
        if len(err) > 4:  # Only print if looks like a message
            print(err)
#     except Exception as err:
#         print('Error in conda command:')
#         print(err)
        # todo: or raise?
    finally:
        sys.argv = oldargs

condacmd('list')
