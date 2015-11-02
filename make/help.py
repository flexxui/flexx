# License: consider this public domain

"""
Show the list of available commands, or details on a command.
* python make help - show list of commands
* python make help foo - show details on command "foo"
"""

import os
import sys

from make import THIS_DIR, NAME


def help(command=''):

    if not command:
        # List all commands
        fnames = [fname for fname in os.listdir(THIS_DIR) if
                  os.path.isfile(os.path.join(THIS_DIR, fname)) and
                  fname.endswith('.py') and
                  fname.count('.') == 1 and
                  not fname.startswith('_')]
        print('Developer tools for project %s\n' % NAME.capitalize())
        print('  python make <command> [arg]\n')
        for fname in sorted(fnames):
            modname = fname[:-3]
            doc = get_doc_for_file(fname)
            summary = doc.split('\n', 1)[0] if doc else ''
            print(modname.ljust(15) + ' ' + summary)
    
    else:
        # Give more detailed info on command
        fname = command + '.py'
        if not os.path.isfile(os.path.join(THIS_DIR, fname)):
            sys.exit('Not a known command: %r' % command)
        doc = get_doc_for_file(fname) or ''
        print('\n%s - %s\n' % (command, doc))


def get_doc_for_file(fname):
    """ Get the module docstring of the given file. Returns string with
    quotes and whitespace stripped, and only LF newlines.
    """
    # Read code
    try:
        code = open(os.path.join(THIS_DIR, fname), 'rt', encoding='utf-8').read()
    except Exception as err:
        return 'Error: could not read %r: %s' % (fname, str(err))
    
    # Search for closes multiline string
    qsingle, qdouble = "'''", '"""'
    ii = [(code.find(needle), needle) for needle in (qsingle, qdouble)]
    ii = [(i, needle) for i, needle in ii if i >= 0]
    ii.sort(key=lambda x: x[0])
    
    # Find where it ends
    if ii:
        i1, needle = ii[0]
        i2 = code.find(needle, i1+3)
        if i2 > 0:
            doc = code[i1:i2].strip('"\'').strip()
            return doc.replace('\r\n', '\n').replace('\r', '\n')
