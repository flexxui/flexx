""" Generate docs for ui classes.
"""

import os
from types import ModuleType
from flexx import ui, app


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
OUTPUT_DIR = os.path.join(DOC_DIR, 'ui')

created_files = []

def main():
    
    pages = {}
    class_names = []
    layouts = set()
    
    # Get all pages and class names
    namespace = {}; namespace.update(ui.__dict__); namespace.update(ui.layouts.__dict__); namespace.update(ui.widgets.__dict__)
    for mod in namespace.values():
        if isinstance(mod, ModuleType):
            classes = []
            for w in mod.__dict__.values():
                if isinstance(w, type) and issubclass(w, app.Model):  # Model, cause e.g. TreeItem
                    if w.__module__ == mod.__name__:
                        classes.append(w)
                        if issubclass(w, ui.Layout):
                            layouts.add(w.__name__)
            if classes:
                classes.sort(key=lambda x: x.__name__)
                classes.sort(key=lambda x: len(x.mro()))
                class_names.extend([w.__name__ for w in classes])
                pages[mod.__name__] = classes
    
    # Create page for each module
    for module_name, classes in sorted(pages.items()):
        page_name = module_name.split('.')[-1].strip('_').capitalize()
        docs = '%s\n%s\n\n' % (page_name, '-' * len(page_name))
        
        docs += '.. automodule:: %s\n\n' % module_name
        
        docs += '----\n\n'
        
        for cls in classes:
            name = cls.__name__
            
            # Insert info on base clases
            if 'Inherits from' not in cls.__doc__:
                bases = []
                for bcls in cls.__bases__:
                    if getattr(ui, bcls.__name__, None):
                        bases.append(':class:`%s <flexx.ui.%s>`' % (bcls.__name__, bcls.__name__))
                    elif getattr(app, bcls.__name__, None):
                        bases.append(':class:`%s <flexx.app.%s>`' % (bcls.__name__, bcls.__name__))
                    else:
                        bases.append(':class:`%s <%s.%s>`' % (bcls.__name__, bcls.__module__, bcls.__name__))
                line = '    *Inherits from:* ' + ', '.join(bases)
                cls.__doc__ = line + '\n\n    ' + (cls.__doc__ or '').lstrip()
            
            # Create doc for class
            if getattr(ui, name, None):
                docs += '.. autoclass:: flexx.ui.%s\n' % name
            else:
                docs += '.. autoclass:: %s.%s\n' % (module_name, name)
            docs += ' :members:\n\n' 
        
        # Write doc page
        filename = os.path.join(OUTPUT_DIR, page_name.lower() + '.rst')
        created_files.append(filename)
        open(filename, 'wt', encoding='utf-8').write(docs)
    
    # Create overview doc page
    docs = 'Ui API'
    docs += '\n' + '=' * len(docs) + '\n\n'
    docs += 'This is a list of all widget classes provided by ``flexx.ui``. '
    docs += ':class:`Widget <flexx.ui.Widget>` is the base class of all widgets. '
    docs += 'There is one document per widget type. Each document contains '
    docs += 'examples with the widget(s) defined within.\n\n'
    docs += '\nBase widget:\n\n'
    if True:
        docs += '* :class:`%s <flexx.ui.%s>`\n' % ('Widget', 'Widget')
    docs += '\nLayouts:\n\n'
    for name in [n for n in sorted(class_names) if n in layouts if getattr(ui, n, None)]:
        docs += '* :class:`%s <flexx.ui.%s>`\n' % (name, name)
    docs += '\nWidgets:\n\n'
    for name in [n for n in sorted(class_names) if n not in layouts if getattr(ui, n, None)]:
        docs += '* :class:`%s <flexx.ui.%s>`\n' % (name, name)
    docs += '\n.. toctree::\n  :maxdepth: 1\n  :hidden:\n\n'
    for module_name in sorted(pages.keys()):
        docs += '  %s\n' % module_name.split('.')[-1].strip('_').lower()
    
    # Write overview doc page
    filename = os.path.join(OUTPUT_DIR, 'api.rst')
    created_files.append(filename)
    open(filename, 'wt', encoding='utf-8').write(docs)
    
    print('  generated widget docs with %i pages and %i widgets' % (len(pages), len(class_names)))


def clean():
    while created_files:
        filename = created_files.pop()
        if os.path.isfile(filename):
            os.remove(filename)
