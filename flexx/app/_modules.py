"""
The JSModule class represents the JS module corresponding to a Python module.
The code here resolves dependencies of names used in the JS code, either
by including more JS or by adding a dependency on another JSModule.
"""

import re
import sys
import json
import time
import types
import logging

from pscript import (py2js, JSString, RawJS, JSConstant, create_js_module,
                        get_all_std_names)
from pscript.stdlib import FUNCTION_PREFIX, METHOD_PREFIX

from .. import event
from ..event import Component, Property, loop
from ..event._js import create_js_component_class

from ._clientcore import bsdf
from ._component2 import BaseAppComponent, PyComponent, JsComponent, StubComponent
from ._asset import Asset, get_mod_name, module_is_package
from . import logger


pscript_types = type, types.FunctionType  # class or function

if sys.version_info > (3, ):
    json_types = None.__class__, bool, int, float, str, tuple, list, dict
else:  # pragma: no cover
    json_types = None.__class__, bool, int, float, basestring, tuple, list, dict  # noqa, bah

# In essense, the idea of modules is all about propagating dependencies:
#
# * In PScript we detect unresolved dependencies in JS code, and move these up
#   the namespace stack.
# * The create_js_component_class() function and AppComponentMeta class collect the
#   dependencies from the different code pieces.
# * In JSModule we resolve some dependencies and let other propagate into
#   module dependencies.
# * In the Bundle class, again some dependencies are resolved due to bundling,
#   and others propagate to dependencies between bundles.


def mangle_dotted_vars(jscode, names_to_mangle):
    """ Mangle the names of unknown variables that have dots in them, so that
    they become simple identifiers. We use $ because thats not valid in Python
    (i.e. no name clashes).
    """
    for name in list(names_to_mangle):
        if '.' in name:
            # Replace dots with $
            name1 = name.replace('.', r'\.')
            name2 = name.replace('.', '$')
            jscode = re.sub(r"\b(" + name1 + r")\b", name2, jscode,
                            flags=re.UNICODE | re.MULTILINE)
            # Fix calls with *args to funcs that have dots in name
            jscode = jscode.replace(
                name2 + '.apply(' + name2.rsplit('$', 1)[0] + ', [].concat',
                name2 + '.apply(null, [].concat')
    return jscode


def is_pscript_module(m):
    return (getattr(m, '__pscript__', False) or
            getattr(m, '__pyscript__', False))


class JSModule:
    """
    A JSModule object represents the JavaScript (and CSS) corresponding
    to a Python module, which either defines one or more
    PyComponent/JsCompontent classes, or PScript transpilable functions or
    classes. Intended for internal use only.

    Modules are collected in a "store" which is simply a dictionary. The
    flexx asset system has this dict in ``app.assets.modules``.

    The module contains the JS corresponding to the variables that are
    marked as used (by calling the ``add_variable()`` method), and the
    variables that are used by the included JavaScript.

    The JS code includes:

    * The JS code corresponding to all used Component classes defined in the module.
    * The transpiled JS from (PySript compatible) functions and classes that
      are defined in this module and marked as used.
    * Variables with json-compatible values that are used by JS in this module.
    * Imports of names from other modules.
    * ... unless this module defines ``__pscript__ = True``, in which case
      the module is transpiled as a whole.

    A module can also have dependencies:

    * The modules that define the base classes of the classes defined
      in this module.
    * The modules that define functions/classes that are used by this module.
    * Assets that are present in the module.

    Notes on how the Flexx asset system uses modules:

    The asset system will generate JSModule objects for all Python modules
    that define PyComponent or JsComponent subclasses. The session is aware of
    the Component classes that it uses (and their base classes), and can
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
        self._component_classes = {}
        self._pscript_code = {}
        self._js_values = {}
        # Dependencies
        self._deps = {}  # mod_name -> [mod_as_name, *imports]
        # Caches
        self._js_cache = None
        self._css_cache = None

        if is_pscript_module(self._pymodule):
            # PScript module; transpile as a whole
            js = py2js(self._pymodule, inline_stdlib=False, docstrings=False)
            self._pscript_code['__all__'] = js
            self._provided_names.update([n for n in js.meta['vars_defined']
                                         if not n.startswith('_')])
        else:
            self._init_default_objects()

    def __repr__(self):
        return '<%s %s with %i definitions>' % (self.__class__.__name__,
                                                self.name,
                                                len(self._provided_names))

    def _init_default_objects(self):
        # Component classes
        # Add property classes ...
        for name, val in self._pymodule.__dict__.items():
            if isinstance(val, type) and issubclass(val, Property):
                self.add_variable(name)

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
    def component_classes(self):
        """ The PyComponent and JsComponent classes defined in this module.
        """
        return set(self._component_classes.values())

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

    def add_variable(self, name, is_global=False, _dep_stack=None):
        """ Mark the variable with the given name as used by JavaScript.
        The corresponding object must be a module, Component, class or function,
        or a json serializable value.

        If the object is defined here (or a json value) it will add JS to
        this module. Otherwise this module will import the name from
        another module.

        If ``is_global``, the name is considered global; it may be declared in
        this module, but it may also be a JS global. So we try to resolve the
        name, but do not care if it fails.
        """
        _dep_stack = _dep_stack or []
        if name in self._imported_names:
            return
        elif name in _dep_stack:
            return  # avoid dependency recursion
        elif name in ('Infinity', 'NaN'):
            return  # stubs
        elif name in self._provided_names and self.name != '__main__':
            return  # in __main__ we allow redefinitions
        if is_pscript_module(self._pymodule):
            return  # everything is transpiled and exported already
        _dep_stack.append(name)

        # Try getting value. We warn if there is no variable to match, but
        # if we do find a value we're either including it or raising an error
        try:
            val = self._pymodule
            nameparts = name.split('.')
            for i in range(len(nameparts)):
                val = getattr(val, nameparts[i])
                # Maybe we "know" (this kind of) value ...
                if isinstance(val, json_types):
                    name = '.'.join(nameparts[:i+1])
                    break
                elif isinstance(val, type) and issubclass(val, JsComponent):
                    name = '.'.join(nameparts[:i+1])
                    break
                elif val is loop and i == 0:
                    return self._add_dep_from_event_module('loop', nameparts[0])
                elif isinstance(val, (JSConstant, Asset)):
                    return  # stubs
                elif isinstance(val, logging.Logger) and i == 0:
                    # todo: hehe, we can do more here (issue #179)
                    return self._add_dep_from_event_module('logger', nameparts[0])
        except AttributeError:
            msg = 'JS in "%s" uses undefined variable %r.' % (self.filename, name)
            if is_global:
                pass  # it may be a JS-global
            elif val is self._pymodule:
                # Did not resolve first part of the name, so cannot be a JS global
                logger.warning(msg)
            else:
                raise RuntimeError(msg)  # E.g. typo in ui.Buttom
            return

        # Mark dirty
        self._changed_time = time.time()
        self._js_cache = self._css_cache = None

        if isinstance(val, types.ModuleType):
            # Modules as a whole can be converted if its a PScript module
            if is_pscript_module(val):
                self._import(val.__name__, None, None)
                self._deps[val.__name__][0] = name  # set/overwrite as-name
            else:
                t = 'JS in "%s" cannot use module %s directly unless it defines %s.'
                raise ValueError(t % (self.filename, val.__name__, '"__pscript__"'))

        elif isinstance(val, type) and issubclass(val, Component):
            if val is Component:
                return self._add_dep_from_event_module('Component')
            elif val is BaseAppComponent or val.mro()[1] is BaseAppComponent:
                # BaseAppComponent, PyComponent, JsComponent or StubComponent
                # are covered in _component2.py
                return
            elif issubclass(val, (PyComponent, JsComponent)):
                # App Component class; we know that we can get the JS for this
                if val.__jsmodule__ == self.name:
                    # Define here
                    self._provided_names.add(name)
                    self._component_classes[name] = val
                    # Recurse
                    self._collect_dependencies_from_bases(val)
                    self._collect_dependencies(val.JS.CODE, _dep_stack)
                else:
                    # Import from another module
                    self._import(val.__jsmodule__, val.__name__, name)
            else:
                # Regular Component, similar to other classes,
                # but using create_js_component_class()
                mod_name = get_mod_name(val)
                if mod_name == self.name:
                    # Define here
                    js = create_js_component_class(val, val.__name__)
                    self._provided_names.add(name)
                    self._pscript_code[name] = js
                    # Recurse
                    self._collect_dependencies_from_bases(val)
                    self._collect_dependencies(js, _dep_stack)
                else:
                    # Import from another module
                    self._import(mod_name, val.__name__, name)

        elif isinstance(val, type) and issubclass(val, bsdf.Extension):
            # A bit hacky mechanism to define BSDF extensions that also work in JS.
            # todo: can we make this better? See also app/_component2.py (issue #429)
            js = 'var %s = {name: "%s"' % (name, val.name)
            for mname in ('match', 'encode', 'decode'):
                func = getattr(val, mname + '_js')
                funccode = py2js(func, indent=1, inline_stdlib=False, docstrings=False)
                js += ',\n    ' + mname + ':' + funccode.split('=', 1)[1].rstrip(' \n;')
                self._collect_dependencies(funccode, _dep_stack)
            js += '};\n'
            js += 'serializer.add_extension(%s);\n' % name
            js = JSString(js)
            js.meta = funccode.meta
            self._pscript_code[name] = js
            self._deps.setdefault('flexx.app._clientcore',
                                 ['flexx.app._clientcore']).append('serializer')

        elif isinstance(val, pscript_types) and hasattr(val, '__module__'):
            # Looks like something we can convert using PScript
            mod_name = get_mod_name(val)
            if mod_name == self.name:
                # Define here
                try:
                    js = py2js(val, inline_stdlib=False, docstrings=False)
                except Exception as err:
                    t = 'JS in "%s" uses %r but cannot transpile it with PScript:\n%s'
                    raise ValueError(t % (self.filename, name, str(err)))
                self._provided_names.add(name)
                self._pscript_code[name] = js
                # Recurse
                if isinstance(val, type):
                    self._collect_dependencies_from_bases(val)
                self._collect_dependencies(js, _dep_stack)
            elif mod_name.endswith('.event._property'):
                return self._add_dep_from_event_module(name.split('.')[-1], name)
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
              is_pscript_module(sys.modules[val.__module__]) and
              val is getattr(sys.modules[val.__module__], name, 'unlikely-val')):
            # An instance from a pscript module!
            # We cannot know the "name" as its known in the module, but
            # we assume that its the same as as_name and test whether
            # it matches in the test above.
            self._import(val.__module__, name, name)

        else:
            # Cannot convert to JS
            t = 'JS in "%s" uses %r but cannot convert %s to JS.'
            raise ValueError(t % (self.filename, name, val.__class__))

    def _collect_dependencies(self, js, _dep_stack):
        """
        Collect dependencies corresponding to names used in the JS.
        """
        vars_unknown = js.meta['vars_unknown']
        vars_global = js.meta['vars_global']
        for name in reversed(sorted(vars_unknown)):
            if name.startswith('event.'):
                self._deps.setdefault('flexx.event.js', ['event'])
            elif self._name_ispropclass(name):
                self._add_dep_from_event_module(name, name)
            else:
                self.add_variable(name, _dep_stack=_dep_stack)
        for name in reversed(sorted(vars_global)):
            self.add_variable(name, True, _dep_stack=_dep_stack)

    def _name_ispropclass(self, name):
        ob = getattr(event._property, name, None)
        if ob is not None:
            return isinstance(ob, type) and issubclass(ob, Property)
        return False

    def _collect_dependencies_from_bases(self, cls):
        """
        Collect dependencies based on the base classes of a class.
        """
        if len(cls.__bases__) != 1:  # pragma: no cover
            raise TypeError('PScript classes do not (yet) support '
                            'multiple inheritance.')
        if cls is PyComponent or cls is JsComponent or cls is StubComponent:
            return self._add_dep_from_event_module('Component')
        for base_cls in cls.__bases__:
            if base_cls is object:
                return
            elif base_cls is Component:
                return self._add_dep_from_event_module('Component')
            elif base_cls.__module__.endswith('.event._property'):  # base properties
                return self._add_dep_from_event_module(cls.__name__)
            m = self._import(get_mod_name(base_cls),
                             base_cls.__name__, base_cls.__name__)
            m.add_variable(base_cls.__name__)  # note: m can be self, which is ok

    def _add_dep_from_event_module(self, name, asname=None):
        asname = asname or name
        entry = '%s as %s' % (name, asname)
        imports = self._deps.setdefault('flexx.event.js', ['event'])
        self._imported_names.add(asname)
        if entry not in imports:
            imports.append(entry)

    def get_js(self):
        """ Get the JS code for this module.
        """
        if self._js_cache is None:
            # Collect JS and sort by linenr
            js = [cls.JS.CODE for cls in self._component_classes.values()]
            js += list(self._pscript_code.values())
            js.sort(key=lambda x: x.meta['linenr'])
            used_std_functions, used_std_methods = set(), set()
            for code in js:
                used_std_functions.update(code.meta['std_functions'])
                used_std_methods.update(code.meta['std_methods'])
            # Mangle dotted names
            for i in range(len(js)):
                js[i] = mangle_dotted_vars(js[i], self._imported_names)
            # Insert serialized values
            value_lines = []
            for name in sorted(self._js_values):
                if '.' in name:
                    for i in range(len(js)):
                        js[i] = mangle_dotted_vars(js[i], [name])
                value_lines.append('var %s = %s;' % (name.replace('.', '$'),
                                                     self._js_values[name]))
            js.insert(0, '')
            js.insert(0, '\n'.join(value_lines))
            # Prepare imports and exports
            exports = tuple(sorted(n for n in self._provided_names if '.' not in n))
            imports = ['pscript-std.js as _py']
            # Handle dependency imports
            for dep_name in reversed(sorted(self._deps)):
                names = self._deps[dep_name]
                mod_name = names[0].replace('.', '$')  # mangle module name
                imports.append(dep_name + ' as ' + mod_name)
                for name in names[1:]:
                    as_name = name
                    if ' as ' in name:
                        name, _, as_name = name.partition(' as ')
                        as_name = as_name.replace('.', '$')  # mangle dotted name
                    pieces = ['%s = %s.%s' % (as_name, mod_name, name)]
                    js.insert(0, 'var ' + (', '.join(pieces)) + ';')
            # Import stdlib
            func_names, method_names = get_all_std_names()
            pre1 = ', '.join(['%s%s = _py.%s%s' %
                              (FUNCTION_PREFIX, n, FUNCTION_PREFIX, n)
                              for n in sorted(used_std_functions)])
            pre2 = ', '.join(['%s%s = _py.%s%s' %
                              (METHOD_PREFIX, n, METHOD_PREFIX, n)
                              for n in sorted(used_std_methods)])
            if pre2:
                js.insert(0, 'var %s;' % pre2)
            if pre1:
                js.insert(0, 'var %s;' % pre1)
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
            for cls in sorted(self._component_classes.values(), key=sorter):
                css.append(cls.CSS)
            self._css_cache = '\n\n'.join(css)
        return self._css_cache
