""" Generate docs for commonast.
"""

import os
import sys
from types import ModuleType
from pscript import commonast

# Hack
sys.modules['commonast'] = commonast

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
OUTPUT_DIR = os.path.join(DOC_DIR, 'pscript')

created_files = []

def main():
    
    # Create overview doc page
    docs = 'Common AST'
    docs += '\n' + '=' * len(docs) + '\n\n'
    docs += '.. automodule:: commonast\n\n'
    docs += '.. autofunction:: commonast.parse\n\n'
    
    docs += '----\n\n'
    docs += 'The nodes\n---------\n\n'
    
    docs += '.. autoclass:: commonast.Node\n    :members:\n\n'
    
    code = open(commonast.__file__, 'rb').read().decode()
    status = 0
    for line in code.splitlines():
        if status == 0:
            if line.startswith('## --'):
                status = 1
        elif status == 1:
            if line.startswith('## --'):
                break
            elif line.startswith('## '):
                title = line[3:].strip()
                docs += '%s\n%s\n\n' % (title, '-' * len(title))
            elif line.startswith('class '):
                clsname = line[6:].split('(')[0]
                docs += '.. autoclass:: %s\n\n' % ('commonast.' + clsname)
                cls = getattr(commonast, clsname)
                #cls.__doc__ = '%s(%s)\n%s' % (clsname, ', '.join(cls.__slots__), cls.__doc__) 
                cls.__doc__ = '%s()\n%s' % (clsname, cls.__doc__) 
    
    # Write overview doc page
    filename = os.path.join(OUTPUT_DIR, 'commonast.rst')
    created_files.append(filename)
    open(filename, 'wt', encoding='utf-8').write(docs)
    
    print('  generated commonast page')


def clean():
    while created_files:
        filename = created_files.pop()
        if os.path.isfile(filename):
            os.remove(filename)
