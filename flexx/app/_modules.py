"""
The JSModule class represents the JS module corresponding to a Python module.
The code here resolves dependencies of names used in the JS code, either
by including more JS or by adding a dependency on another JSModule.
"""

import sys
import json
import time
import types

from ..pyscript import py2js, RawJS, JSConstant, create_js_module, get_all_std_names

from ._model import Model
from ._asset import Asset, get_mod_name, module_is_package
from . import logger


pyscript_types = type, types.FunctionType  # class or function

if sys.version_info > (3, ):
    json_types = None.__class__, bool, int, float, str, tuple, list, dict
else:  # pragma: no cover
    json_types = None.__class__, bool, int, float, basestring, tuple, list, dict  # noqa, bah

# In essense, the idea of modules is all about propagating dependencies:
# 
# * In PyScript we detect unresolved dependencies in JS code, and move these up
#   the namespace stack.
# * The create_js_hasevents_class() function and ModelMeta class collect the
#   dependencies from the different code pieces.
# * In JSModule we resolve some dependencies and let other propagate into
#   module dependencies.
# * In the Bundle class, again some dependencies are resolved due to bundling,
#   and others propagate to dependencies between bundles.


class JSModule:
    """
    A JSModule object represents the JavaScript (and CSS) corresponding
    to a Python module, which either defines one or more Model classes,
    or PyScript transpilable functions or classes. Intended for internal
    use only.
    
    Modules are collected in a "store" which is simply a dictionary. The
    flexx asset system has this dict in ``app.assets.modules``.
    
    The module contains the JS corresponding to the variables that are
    marked as used (by calling the ``add_variable()`` method), and the
    variables that are used by the included JavaScript.
    
    The JS code includes: 
    
    * The JS code corresponding to all used Model classes defined in the module.
    * The transpiled JS from (PySript compatible) functions and classes that
      are defined in this module and marked as used.
    * Variables with json-compatible values that are used by JS in this module.
    * Imports of names from other modules.
    * ... unless this module defines ``__pyscript__ = True``, in which case
      the module is transpiled as a whole.
    
    A module can also have dependencies:
    
    * The modules that define the base classes of the classes defined
      in this module.
    * The modules that define functions/classes that are used by this module.
    * Assets that are present in the module.
    
    Notes on how the Flexx asset system uses modules:
    
    The asset system will generate JSModule objects for all Python
    modules that define Model subclasses. The session is aware of the
    Model classes that it uses (and their base classes), and can
    therefore determine what modules (and assets) need to be loaded.
    """
    
    def __init__(self, name, store):
        if not isinstance(name, str):
            raise TypeError('JSModule needs a str name.')
        if not isinstance(store, dict):
            raise TypeError('JSModule needs a dict store.')
        
        # Resolve name of Python module
        py_name = name
        if name.endswith('.__init__'):
            py_name = name.rsplit('.', 1)[0]
        if py_name not in sys.modules:
            raise ValueError("Cannot find Python module coresponding to %s." % name)
        
        # Store module and name
        self._pymodule = sys.modules[py_name]
        self._name = get_mod_name(self._pymodule)
        
        # Check if name matches the kind of module
        is_package = module_is_package(self._pymodule)
        if is_package and not name.endswith('.__init__'):
            raise ValueError('Modules representing the __init__ of a package '
                             'should end with ".__init__".')
        elif not is_package and name.endswith('.__init__'):
            raise ValueError('Plain modules should not end with ".__init__".')
        
        # Self-register
        self._store = store
        if self.name in self._store:
            raise RuntimeError('Module %s already exists!' % self.name)
        self._store[self.name] = self
        
        # Bookkeeping content of the module
        self._provided_names = set()
        self._imported_names = set()
        # Stuff defined in this module (in JS)
        # We use dicts so that we can "overwrite" them in interactive mode
        self._model_classes = {}
        self._pyscript_code = {}
        self._js_values = {}
        # Dependencies
        self._deps = {}  # mod_name -> [mod_as_name, *imports]
        # Caches
        self._js_cache = None
        self._css_cache = None
        
        if getattr(self._pymodule, '__pyscript__', False):
            # PyScript module; transpile as a whole
            js = py2js(self._pymodule, inline_stdlib=False, docstrings=False)
            self._pyscript_code['__all__'] = js
            self._provided_names.update([n for n in js.meta['vars_defined']
                                         if not n.startswith('_')])
    
    def __repr__(self):
        return '<%s %s with %i definitions>' % (self.__class__.__name__,
                                                self.name,
                                                len(self._provided_names))
    
    @property
    def name(self):
        """ The (qualified) name of this module.
        """
        return self._name
    
    @property
    def filename(self):
        """ The filename of the Python file that defines
        (the contents of) this module. Can be '__main__'.
        """
        # E.g. __main__ does not have __file__
        return getattr(self._pymodule, '__file__', self.name)
    
    @property
    def deps(self):
        """ The (unsorted) set of dependencies (names of other modules) for
        this module.
        """
        return set(self._deps.keys())
    
    @property
    def model_classes(self):
        """ The Model classes defined in this module.
        """
        return set(self._model_classes.values())
    
    def _import(self, mod_name, name, as_name):
        """ Import a name from another module. This also ensures that the
        other module exists.
        """
        # Create module, if we must
        if mod_name == self.name:
            return self
        elif mod_name not in self._deps:
            if mod_name not in self._store:
                JSModule(mod_name, store=self._store)
        m = self._store[mod_name]
        # Define imports and if necessary, the name that we import
        imports = self._deps.setdefault(mod_name, [mod_name])
        if name:
            self._imported_names.add(as_name)
            m.add_variable(name)
            line = '%s as %s' % (name, as_name)
            if line not in imports:
                imports.append(line)
        return m
    
    @property
    def variables(self):
        """ The names of variables provided by this module.
        A name passed to add_variable, might not end up in this list
        if its imported into this module rather than defined here.
        """
        return self._provided_names
    
    def add_variable(self, name, is_global=False):
        """ Mark the variable with the given name as used by JavaScript.
        The corresponding object must be a module, Model, class or function,
        or a json serializable value.
        
        If the object is defined here (or a json value) it will add JS to
        this module. Otherwise this module will import the name from 
        another module.
        
        If ``is_global``, the name is considered declared global in this module.
        """
        if name in self._imported_names:
            return
        elif name in self._provided_names and self.name != '__main__':
            return  # in __main__ we allow redefinitions
        if getattr(self._pymodule, '__pyscript__', False):
            return  # everything is transpiled and exported already
        
        # Try getting value. We warn if there is no variable to match, but
        # if we do find a value we're either including it or raising an error
        try:
            val = getattr(self._pymodule, name)
        except AttributeError:
            msg = 'JS in "%s" uses undefined variable %r.' % (self.filename, name)
            if is_global:
                raise ValueError(msg)
            logger.warn(msg)
            return
        
        # Stubs
        if isinstance(val, (JSConstant, Asset)) or name in ('Infinity', 'NaN'):
            return
        elif val is None and not is_global:  # pragma: no cover
            logger.warn('JS in "%s" uses variable %r that is None; '
                        'I will assume its a stub and ignore it. Declare %s '
                        'as global (where it\'s used) to use it anyway, or '
                        'use "from flexx.pyscript.stubs import %s" to mark '
                        'it as a stub'
                        % (self.filename, name, name, name))
            return
        
        # Mark dirty
        self._changed_time = time.time()
        self._js_cache = self._css_cache = None
        
        if isinstance(val, types.ModuleType):
            # Modules as a whole can be converted if its a PyScript module
            if getattr(val, '__pyscript__', False):
                self._import(val.__name__, None, None)
                self._deps[val.__name__][0] = name  # set/overwrite as-name
            else:
                t = 'JS in "%s" cannot use module %s directly unless it defines %s.'
                raise ValueError(t % (self.filename, val.__name__, '"__pyscript__"'))
        
        elif isinstance(val, type) and issubclass(val, Model):
            # Model class; we know that we can get the JS for this
            if val.__jsmodule__ == self.name:
                # Define here
                self._provided_names.add(name)
                self._model_classes[name] = val
                # Recurse
                self._collect_dependencies_from_bases(val)
                self._collect_dependencies(**val.JS.CODE.meta)
            else:
                # Import from another module
                # not needed per see; bound via window.flexx.classes
                self._import(val.__jsmodule__, val.__name__, name)
        
        elif isinstance(val, pyscript_types) and hasattr(val, '__module__'):
            # Looks like something we can convert using PyScript
            mod_name = get_mod_name(val)
            if mod_name == self.name:
                # Define here
                try:
                    js = py2js(val, inline_stdlib=False, docstrings=False)
                except Exception as err:
                    t = 'JS in "%s" uses %r but cannot transpile it with PyScript:\n%s'
                    raise ValueError(t % (self.filename, name, str(err)))
                self._provided_names.add(name)
                self._pyscript_code[name] = js
                # Recurse
                if isinstance(val, type):
                    self._collect_dependencies_from_bases(val)
                self._collect_dependencies(**js.meta)
            else:
                # Import from another module
                self._import(mod_name, val.__name__, name)
        
        elif isinstance(val, RawJS):
            # Verbatim JS
            if val.__module__ == self.name:
                self._provided_names.add(name)
                self._js_values[name] = val.get_code()
            else:
                self._import(val.__module__, val.get_defined_name(name), name)
        
        elif isinstance(val, json_types):
            # Looks like something we can serialize
            # Unlike with RawJS, we have no way to determine where it is defined
            try:
                js = json.dumps(val)
            except Exception as err:
                t = 'JS in "%s" uses %r but cannot serialize that value:\n%s'
                raise ValueError(t % (self.filename, name, str(err)))
            self._provided_names.add(name)
            self._js_values[name] = js
        
        elif (getattr(val, '__module__', None) and
              getattr(sys.modules[val.__module__], '__pyscript__', False) and
              val is getattr(sys.modules[val.__module__], name, 'unlikely-val')):
            # An instance from a pyscript module!
            # We cannot know the "name" as its known in the module, but
            # we assume that its the same as as_name and test whether
            # it matches in the test above.
            self._import(val.__module__, name, name)
        
        else:
            # Cannot convert to JS
            t = 'JS in "%s" uses %r but cannot convert %s to JS.'
            raise ValueError(t % (self.filename, name, val.__class__))
    
    def _collect_dependencies(self, vars_unknown=None, vars_global=None, **kwargs):
        """
        Collect dependencies corresponding to names used in the JS.
        """
        assert not (vars_unknown is None or vars_global is None)
        for name in reversed(sorted(vars_unknown)):
            self.add_variable(name, name in vars_global)
    
    def _collect_dependencies_from_bases(self, cls):
        """
        Collect dependencies based on the base classes of a class.
        """
        if cls is Model:
            return
        if len(cls.__bases__) != 1:  # pragma: no cover
            raise TypeError('PyScript classes do not (yet) support '
                            'multiple inheritance.')
        for base_cls in cls.__bases__:
            if base_cls is object:
                continue
            m = self._import(get_mod_name(base_cls), None, None)
            m.add_variable(base_cls.__name__)  # note: m can be self, which is ok
    
    def get_js(self):
        """ Get the JS code for this module.
        """
        if self._js_cache is None:
            # Collect JS and sort by linenr
            js = [cls.JS.CODE for cls in self._model_classes.values()]
            js += list(self._pyscript_code.values())
            js.sort(key=lambda x: x.meta['linenr'])
            # todo: collect stdlib funcs here
            # Insert serialized values
            value_lines = []
            for key in sorted(self._js_values):
                value_lines.append('var %s = %s;' % (key, self._js_values[key]))
            js.insert(0, '')
            js.insert(0, '\n'.join(value_lines))
            # Prepare imports and exports
            exports = tuple(sorted(self._provided_names))
            imports = ['pyscript-std.js as _py']
            # Handle dependency imports
            for dep_name in reversed(sorted(self._deps)):
                names = self._deps[dep_name]
                mod_name = names[0].replace('.', '_')  # can still be dep_name
                imports.append(dep_name + ' as ' + mod_name)
                for name in names[1:]:
                    as_name = name
                    if ' as ' in name:
                        name, _, as_name = name.partition(' as ')
                    pieces = ['%s = %s.%s' % (as_name, mod_name, name)]
                    js.insert(0, 'var ' + (', '.join(pieces)) + ';')
            # Import stdlib
            # todo: either include only std of what we use, or use _py.xxx
            func_names, method_names = get_all_std_names()
            pre1 = ', '.join(['%s = _py.%s' % (n, n) for n in func_names])
            pre2 = ', '.join(['%s = _py.%s' % (n, n) for n in method_names])
            js.insert(0, 'var %s;\nvar %s;' % (pre1, pre2))
            # Create module
            self._js_cache = create_js_module(self.name, '\n\n'.join(js),
                                              imports, exports, 'amd-flexx')
            self._js_cache = self._js_cache
        return self._js_cache
    
    def get_css(self):
        """ Get the CSS code for this module.
        """
        if self._css_cache is None:
            css = []
            sorter = lambda x: x.JS.CODE.meta['linenr']
            for cls in sorted(self._model_classes.values(), key=sorter):
                css.append(cls.CSS)
            self._css_cache = '\n\n'.join(css)
        return self._css_cache
