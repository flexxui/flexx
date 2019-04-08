""" Generate docs for ui classes.
"""

import os
import sys

from types import ModuleType
from flexx import ui, app, event


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
OUTPUT_DIR = os.path.join(DOC_DIR, 'ui')

created_files = []

def main():
    
    pages = {}
    class_names = []
    layouts = set()
    
    # Get all pages and class names
    namespace = {}; namespace.update(ui.__dict__); namespace.update(ui.layouts.__dict__); namespace.update(ui.widgets.__dict__); namespace.update(ui.pywidgets.__dict__)
    for mod in namespace.values():
        if isinstance(mod, ModuleType):
            classes = []
            for w in mod.__dict__.values():
                if isinstance(w, type) and issubclass(w, (app.PyComponent, app.JsComponent)):
                    if w.__module__ == mod.__name__ and not w.__name__.startswith("_"):
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
        # Get page name and title
        page_name = page_title = module_name.split('.')[-1].strip('_').capitalize()
        mdoc = sys.modules[module_name].__doc__
        if mdoc and 0 < len(mdoc.split('\n', 1)[0].strip()) <= 24:
            page_title = mdoc.split('\n', 1)[0].strip()
            sys.modules[module_name].__doc__ = sys.modules[module_name].__doc__.split('\n', 1)[-1]
        
        docs = '%s\n%s\n\n' % (page_title, '-' * len(page_title))
        docs += '.. automodule:: %s\n\n' % module_name
        docs += '----\n\n'
        
        # Include more docs?
        if module_name.endswith('_widget'):
            docs += '.. autofunction:: flexx.ui.create_element\n\n'
        
        for cls in classes:
            assert issubclass(cls, (ui.Widget, ui.PyWidget)), cls.__name__ + " is not a Widget or PyWidget"
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
            
            members = {}
            include = '_create_dom', '_render_dom'
            exclude = 'CODE', 'CSS', 'DEFAULT_MIN_SIZE'
            
            # Collect all stuff that's on the class.
            for n in list(cls.JS.__dict__):
                val = getattr(cls.JS, n)
                if n in exclude or not val.__doc__:
                    pass
                elif n.startswith('_') and n not in include:
                    pass
                elif isinstance(val, event._action.BaseDescriptor):
                    for tname, tclass in (('attributes', event._attribute.Attribute),
                                          ('properties', event._property.Property),
                                          ('actions', event._action.ActionDescriptor),
                                          ('reactions', event._reaction.ReactionDescriptor),
                                          ('emitters', event._emitter.EmitterDescriptor)):
                        if isinstance(val, tclass):
                            members.setdefault(tname, []).append(n)
                            break
                    else:
                        assert False
                elif getattr(val, '__doc__', None):
                    members.setdefault('methods', []).append(n)
            
            # Get canonical name
            full_name = '%s.%s' % (module_name, name)
            if getattr(ui, name, None):
                full_name = 'flexx.ui.%s' % name
            
            # Sort and combine
            order = 'attributes', 'properties', 'emitters', 'actions', 'reactions', 'methods'
            member_str = ' :members:'
            toc_str = '\n'
            for key in members:
                members[key].sort()
            assert not set(members).difference(order)
            for key in order:
                if key in members:
                    # Add to member string and toc
                    toc_str = toc_str.rstrip(',') + '\n\n    *{}*:'.format(key)
                    for n in members[key]:
                        member_str += ' {},'.format(n)
                        toc_str += ' `{} <#{}.{}>`__,'.format(n, full_name, n)  # __ means anonymous hyperlink
                    # Hack: put members back on Python class to have them documented
                    for n in members[key]:
                        if n not in cls.__dict__:
                            setattr(cls, n, cls.JS.__dict__[n])
            cls.__doc__ += toc_str.rstrip(',') + '\n\n'
            
            # Create rst for class
            docs += '.. autoclass:: %s\n' % full_name
            docs += member_str.rstrip(',') + '\n :member-order: alphabetical\n\n'
        
        # Write doc page
        filename = os.path.join(OUTPUT_DIR, page_name.lower() + '.rst')
        created_files.append(filename)
        open(filename, 'wt', encoding='utf-8').write(docs)
    
    # Create overview doc page
    docs = 'Widgets reference'
    docs += '\n' + '=' * len(docs) + '\n\n'
    docs += 'This is a list of all widget classes provided by ``flexx.ui``. '
    docs += 'The :class:`Widget <flexx.ui.Widget>` class is the base class of all widgets. '
    docs += '\n\n'
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
