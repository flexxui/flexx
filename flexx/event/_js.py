"""
Implementation of flexx.event in JS via PyScript.

In this module we compile Loop, Reaction and Component to JavaScript,
by transpiling most methods from the Python classes. This module
implements a JS variant of these classes to overload certain behavior
in JS. E.g. the JS implementation of the Component class has some
boilerplate code to create actions, reactions, emitters and properties,

By reusing as much code as possible, we reduce maintencance costs, and
make it easier to realize that the Python and JS implementation of this
event system have the same API and behavior.

"""

import re
import sys
import json

from flexx.pyscript import JSString, py2js as py2js_
from flexx.pyscript.parser2 import get_class_definition

from flexx.event._loop import Loop
from flexx.event._action import ActionDescriptor
from flexx.event._reaction import ReactionDescriptor, Reaction
from flexx.event._property import Property
from flexx.event._emitter import EmitterDescriptor
from flexx.event._component import Component, _mutate_array_js


Object = Date = console = setTimeout = undefined = loop = None  # fool pyflake

reprs = json.dumps


def py2js(*args, **kwargs):
    kwargs['inline_stdlib'] = False
    kwargs['docstrings'] = False
    return py2js_(*args, **kwargs)


## The JS class variants


JS_LOGGER = """
var Logger = function () {
    this.level = 25;
}
var $Logger = Logger.prototype;
$Logger.debug = function (msg) {
    if (this.level <= 10) { console.info(msg); }
};
$Logger.info = function (msg) {
    if (this.level <= 20) { console.info(msg); }
};
$Logger.warn = function (msg) {
    if (this.level <= 30) { console.warn(msg); }
};
$Logger.exception = function (msg) {
    console.error(msg);
};
$Logger.error = function (msg) {
    console.error(msg);
};
var logger = new Logger();
"""


class LoopJS:  # pragma: no cover
    """ JS variant of the Loop class.
    """
    
    def __init__(self):
        self.reset()
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.iter()
    
    def _calllaterfunc(self, func):
        setTimeout(func, 0)
    
    def _ensure_thread_match(self):
        pass  # JS has threads, but worker threads are unlikely to touch this


# todo: validate that these get cleaned up ... e.f. the on1 lambda is suspicious

class ReactionJS:  # pragma: no cover
    """ JS variant of the Reaction class.
    """
    
    _COUNT = 0
    
    def __init__(self, func, ob, name, connection_strings):
        Reaction.prototype._COUNT += 1
        self._id = 'r' + str(self._COUNT)
        self._func = func
        self._ob1 = lambda: ob  # no weakref in JS
        self._name = name
        self._init(connection_strings, ob)


class ComponentJS:  # pragma: no cover
    """ JS variant of the Component class.
    """
    
    _IS_COMPONENT = True
    _REACTION_COUNT = 0
    _COUNT = 0
    
    def __init__(self, **property_values):
        
        Component.prototype._COUNT += 1
        self._id = 'c' + str(Component.prototype._COUNT)
        
        # Init some internal variables
        self.__handlers = {}  # reactions connecting to this component
        self.__props_being_set = {}
        self.__props_ever_set = {}
        self.__pending_events = {}
        
        init_handlers = property_values.pop('_init_handlers', True)
        
        # Init actions
        for name in self.__actions__:
            self.__create_action(self[name], name)
        
        # Init emitters
        for name in self.__emitters__:
            self.__handlers.setdefault(name, [])
            self.__create_emitter(self[name], name)
        
        # Init properties and their default value
        for name in self.__properties__:
            self.__handlers.setdefault(name, [])
            self.__create_property(name)
            # self._mutate(name, prop._default) but with shortcuts
            value_name = '_' + name + '_value'
            value2 = self['_' + name + '_validate'](self[value_name])
            self[value_name] = value2
            self.emit(name, dict(new_value=value2, old_value=value2, mutation='set'))
        
        # Invoke initial set actions for properties
        for name in sorted(property_values):  # sort for deterministic order
            if name in self.__properties__:
                prop_setter_name = 'set_' + name
                setter_func = getattr(self, prop_setter_name, None)
                if setter_func is None:
                    raise TypeError('%s does not have a set_%s() action.' %
                                    (self._class_name, name))
                else:
                    setter_func(property_values[name])
            else:
                raise AttributeError('%s does not have a property %r' %
                                     (self._class_name, name))
        
        # Init handlers and properties now, or later?
        if init_handlers:
            self._init_handlers()
    
    # todo: rename handler -> reaction
    def _init_handlers2(self):
        # Create (and connect) handlers
        for name in self.__reactions__:
            func = self[name]
            r = self.__create_reaction(func, name, func._connection_strings or ())
            if not r.is_explicit():
                ev = dict(source=self, type='', label='')
                loop.add_reaction_event(r, ev)
    
    def _reaction(self, *connection_strings):
        # The JS version (no decorator functionality)
        
        if len(connection_strings) < 2:
            raise RuntimeError('connect() (js) needs a function and one or ' +
                               'more connection strings.')
        
        # Get callable
        if callable(connection_strings[0]):
            func = connection_strings[0]
            connection_strings = connection_strings[1:]
        elif callable(connection_strings[-1]):
            func = connection_strings[-1]
            connection_strings = connection_strings[:-1]
        else:
            raise TypeError('connect() decorator requires a callable.')
        
        # Verify connection strings
        for s in connection_strings:
            if not (isinstance(s, str) and len(s)):
                raise ValueError('Connection string must be nonempty strings.')
        
        # Get function name (Flexx sets __name__ on methods)
        name = func.__name__ or func.name or 'anonymous'
        name = name.split(' ')[-1].split('flx_')[-1]
        return self.__create_reaction_object(func, name, connection_strings)
    
    def __create_action(self, action_func, name):
        # Keep a ref to the action func, which is a class attribute. The object
        # attribute with the same name will be overwritten with the property below.
        # Because the class attribute is the underlying function, super() works.
        def action(*args):  # this func should return None, so super() works correct
            if loop.is_processing_actions():
                res = action_func.apply(self, args)
                if res is not None:
                    logger.warn('Action (%s) is not supposed to return a value' % name)
            else:
                loop.add_action_invokation(action, args)
        def getter():
            return action
        def setter(x):
            raise AttributeError('Action %s is not settable' % name)
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_property(self, name):
        private_name = '_' + name + '_value'
        def getter():
            loop.register_prop_access(self, name)
            return self[private_name]
        def setter(x):
            raise AttributeError('Cannot set property %r; properties can only '
                                 'be mutated by actions.' % name)
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_emitter(self, emitter_func, name):
        # Keep a ref to the emitter func, see comment in __create_action()
        def func(*args):  # this func should return None, so super() works correct
            ev = emitter_func.apply(self, args)
            if ev is not None:
                self.emit(name, ev)
        def getter():
            return func
        def setter(x):
            raise AttributeError('Emitter %s is not settable' % name)
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_reaction(self, reaction_func, name, connection_strings):
        reaction = self.__create_reaction_object(reaction_func, name, connection_strings)
        def getter():
            return reaction
        def setter(x):
            raise AttributeError('Reaction %s is not settable' % name)
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
        return reaction
        
    def __create_reaction_object(self, reaction_func, name, connection_strings):
        # Keep ref to the reaction function, see comment in create_action().
        
        # reaction = Reaction(reaction_func, self, name, connection_strings)
        # return reaction
        
        # todo: remove the below
        
        # Create function that becomes our "reaction object"
        def reaction(*events):
            return reaction_func.apply(self, events)
        
        # Attach methods to the function object (this gets replaced)
        REACTION_METHODS_HOOK  # noqa
        
        # Init reaction
        that = self
        Component.prototype._REACTION_COUNT += 1
        reaction._id = 'r' + str(Component.prototype._REACTION_COUNT)
        reaction._name = name
        reaction._ob1 = lambda : that  # no weakref in JS
        reaction._init(connection_strings, self)
        
        return reaction


## Compile functions

def _create_js_class(PyClass, JSClass, ignore=()):
    """ Create the JS code for Loop, Reaction and Component based on their
    Python and JS variants.
    """
    cname = PyClass.__name__
    # Start with our special JS version
    jscode = [py2js(JSClass, cname)]
    jscode[0] = jscode[0].replace('}\n',
                                  '}\nvar $%s = %s.prototype;\n' % (cname, cname),
                                  1
                        ).replace('%s.prototype.' % cname,
                                  '$%s.' % cname)
    # Add the Python class methods
    for name, val in sorted(PyClass.__dict__.items()):
        #if not name.startswith(('__', '_%s__' % cname)):
        if not name.startswith('__') and name not in ignore:
            if not hasattr(JSClass, name) and callable(val):
                jscode.append(py2js(val, '$' + cname + '.' + name))
    # Compose
    jscode = '\n'.join(jscode)
    # Add the reaction methods to component
    if PyClass is Component:
        code = '\n'
        for name, val in sorted(Reaction.__dict__.items()):
            if not name.startswith('__') and callable(val):
                code += py2js(val, 'reaction.' + name, indent=1)[4:] + '\n'
        jscode = jscode.replace('REACTION_METHODS_HOOK', code)
    # Optimizations, e.g. remove threading lock context in Loop
    if PyClass is Loop:
        p = r"this\._lock\.__enter.+?try {(.+?)} catch.+?else.+?exit__.+?}"
        jscode= re.sub(p, r'{/* with lock */\1}', jscode, 0, re.MULTILINE | re.DOTALL)
        jscode = jscode.replace('this._ensure_thread_', '//this._ensure_thread_')
        jscode = jscode.replace('threading.get_ident()', '0')
    # Almost done
    jscode = jscode.replace('new Dict()', '{}').replace('new Dict(', '_pyfunc_dict(')
    return jscode


IGNORE = ('_integrate_qt', 'integrate_tornado', 'integrate_pyqt4', 'integrate_pyside'
          )

# todo: see if we can optimize this somewhat
# Generate the code
JS_FUNCS = py2js(_mutate_array_js) + '\nvar mutate_array = _mutate_array_js;\n'
JS_LOOP = _create_js_class(Loop, LoopJS, IGNORE) + '\nvar loop = new Loop();\n'
# JS_REACTION = _create_js_class(Reaction, ReactionJS)
JS_COMPONENT = _create_js_class(Component, ComponentJS)
JS_EVENT = JS_FUNCS + JS_LOGGER + JS_LOOP + JS_COMPONENT


def create_js_component_class(cls, cls_name, base_class='Component.prototype'):
    """ Create the JS equivalent of a subclass of the Component class.
    
    Given a Python class with actions, properties, emitters and reactions,
    this creates the code for the JS version of the class. It also supports
    class constants that are int/float/str, or a tuple/list thereof.
    The given class does not have to be a subclass of Component.
    
    This more or less does what ComponentMeta does, but for JS.
    """
    
    assert cls_name != 'Component'  # we need this special class above instead
    
    # Collect meta information of all code pieces that we collect
    meta = {'vars_unknown': set(), 'vars_global': set(), 'std_functions': set(),
            'std_methods': set(), 'linenr': 1e9}
    def py2js_local(*args, **kwargs):
        code = py2js(*args, **kwargs)
        for key in meta:
            if key == 'linenr':
                meta[key] = min(meta[key], code.meta[key])
            else:
                meta[key].update(code.meta[key])
        return code
    
    total_code = []
    funcs_code = []  # functions and emitters go below class constants
    const_code = []
    err = ('Objects on JS Component classes can only be int, float, str, '
           'or a list/tuple thereof. Not %s -> %r.')
    
    total_code.append('\n'.join(get_class_definition(cls_name, base_class)).rstrip())
    prefix = '' if cls_name.count('.') else 'var '
    total_code[0] = prefix + total_code[0]
    prototype_prefix = '$' + cls_name.split('.')[-1] + '.'
    total_code.append('var %s = %s.prototype;' % (prototype_prefix[:-1], cls_name))
    # Functions to ignore
    OK_MAGICS = ('__actions__', '__properties__', '__emitters__',
                 '__reactions__', '__local_properties__')
    
    # Process class items in original order or sorted by name if we cant
    class_items = cls.__dict__.items()
    if sys.version_info < (3, 6):  # pragma: no cover
        class_items = sorted(class_items)
    
    for name, val in class_items:
        # fix double underscore mangling
        name = name.replace('_JS__', '_%s__' % cls_name.split('.')[-1])
        
        if isinstance(val, ActionDescriptor):
            # Set underlying function as class attribute. This is overwritten
            # by the instance, but this way super() works.
            funcname = name
            # Add function def
            code = py2js_local(val._func, prototype_prefix + funcname)
            code = code.replace('super()', base_class)  # fix super
            # Tweak if this was an autogenerated action
            if name.startswith('set_') and val._func.__name__ == 'setter':
                code = code.replace("this._mutate(name,",
                                    "this._mutate('%s'," % name[4:])
            funcs_code.append(code.rstrip())
            # Mark to not bind the func
            funcs_code.append(prototype_prefix + funcname + '.nobind = true;')
            funcs_code.append('')
        elif isinstance(val, ReactionDescriptor):
            funcname = name  # funcname is simply name, so that super() works
            # Add function def
            code = py2js_local(val._func, prototype_prefix + funcname)
            code = code.replace('super()', base_class)  # fix super
            funcs_code.append(code.rstrip())
            # Mark to not bind the func
            funcs_code.append(prototype_prefix + funcname + '.nobind = true;')
            # Add connection strings, but not for implicit reactions
            if val._connection_strings:
                funcs_code.append(prototype_prefix + funcname +
                                  '._connection_strings = ' +
                                  reprs(val._connection_strings))
            funcs_code.append('')
        elif isinstance(val, EmitterDescriptor):
            funcname = name
            # Add function def
            code = py2js_local(val._func, prototype_prefix + funcname)
            code = code.replace('super()', base_class)  # fix super
            funcs_code.append(code.rstrip())
            # Mark to not bind the func
            funcs_code.append(prototype_prefix + funcname + '.nobind = true;')
            funcs_code.append('')
        elif isinstance(val, Property):
            # Mutator and validator functions are picked up as normal functions.
            # Set default value on class.
            default_val = json.dumps(val._default)
            t = '%s_%s_value = %s;'
            const_code.append(t % (prototype_prefix, name, default_val))
        elif callable(val):
            # Functions, including methods attached by the meta class
            code = py2js_local(val, prototype_prefix + name)
            code = code.replace('super()', base_class)  # fix super
            # todo: or define mutators in __create_property?
            if name.startswith('_mutate_') and name[8:] in cls.__properties__:
                code = code.replace("[name]", "['%s']" % name[8:])
            funcs_code.append(code.rstrip())
            funcs_code.append('')
        elif name in OK_MAGICS:
            const_code.append(prototype_prefix + name + ' = ' + reprs(val))
        elif name.startswith('__'):
            pass  # we create our own __emitters__, etc.
        else:
            try:
                serialized = json.dumps(val)
            except Exception as err:  # pragma: no cover
                raise ValueError('Attributes on JS Component class must be '
                                 'JSON compatible.\n%s' % str(err))
            const_code.append(prototype_prefix + name + ' = ' + serialized)
    
    if const_code:
        total_code.append('')
        total_code.extend(const_code)
    if funcs_code:
        total_code.append('')
        total_code.extend(funcs_code)
    total_code.append('')
    
    # Return string with meta info (similar to what py2js returns)
    js = JSString('\n'.join(total_code))
    js.meta = meta
    return js


if __name__ == '__main__':
    
    # Testing ...
    from flexx import event
    
    class Foo(Component):
        
        foo = event.StringProp('asd', settable=True)
        
        @event.action
        def do_bar(self, v=0):
            print(v)
        
        @event.reaction
        def react2foo(self):
            print(self.foo)
    
    toprint = JS_LOOP  # or JS_LOOP JS_REACTION JS_COMPONENT JS_EVENT
    print('-' * 80)
    print(toprint)  
    print('-' * 80)
    print(len(toprint), 'of', len(JS_EVENT), 'bytes in total')  # 29546 before refactor
    print('-' * 80)
    
    print(create_js_component_class(Foo, 'Foo'))
