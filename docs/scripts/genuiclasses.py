""" Generate docs for ui classes.
"""

import os
from flexx import ui, pair


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
OUTPUT_DIR = os.path.join(DOC_DIR, 'ui')

created_files = []

def main():
    
    # Get all widget classes (sorted by name)
    classes = pair.pair.get_pair_classes()
    classes = [cls for cls in classes if issubclass(cls, ui.Widget)]
    classes.sort(key = lambda x: x.__name__)
    
    class_names = []
    for cls in classes:
        name = cls.__name__
        class_names.append(name)
        
        # Insert info on base clases
        bases = [':doc:`%s`' % bcls.__name__ for bcls in cls.__bases__]
        line = 'Inherits from: ' + ', '.join(bases) 
        cls.__doc__ = line + '\n\n' + (cls.__doc__ or '')
        
        # Create doc page
        docs = name
        docs += '\n' + '=' * len(docs) + '\n\n'
        docs += '.. autoclass:: flexx.ui.%s\n' % name
        docs += ' :members:\n' 
        
        # Write doc page
        filename = os.path.join(OUTPUT_DIR, name + '.rst')
        created_files.append(filename)
        open(filename, 'wt').write(docs)
    
    # Create overview doc page
    docs = 'List of the widget classes'
    docs += '\n' + '=' * len(docs) + '\n\n'
    docs += '.. toctree::\n  :maxdepth: 1\n\n'
    for name in class_names:
        docs += '  %s <%s>\n' % (name, name)
    
    # Write overview doc page
    filename = os.path.join(OUTPUT_DIR, 'classlist.rst')
    created_files.append(filename)
    open(filename, 'wt').write(docs)
    
    print('  generated %i class docs (and a list)' % len(class_names))


def clean():
    while created_files:
        filename = created_files.pop()
        if os.path.isfile(filename):
            os.remove(filename)
