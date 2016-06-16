"""
Implementation of flexx.event in JS via PyScript.
"""

import json

from flexx.pyscript import py2js as py2js_
from flexx.pyscript.parser2 import get_class_definition

from flexx.event._emitters import BaseEmitter, Property
from flexx.event._handler import HandlerDescriptor, Handler
from flexx.event._hasevents import HasEvents


Object = Date = undefined = None  # fool pyflake

reprs = json.dumps


def py2js(*args, **kwargs):
    kwargs['inline_stdlib'] = False
    kwargs['docstrings'] = False
    return py2js_(*args, **kwargs)


class HasEventsJS:
    """ An implementation of the HasEvents class in PyScript. It has
    some boilerplate code to create handlers and emitters, but otherwise
    shares most of the code with the Python classes by transpiling their
    methods via PyScript. This ensures that the Python and JS
    implementation of this event system have the same API and behavior.
    
    The Python version of this class has a ``JSCODE`` attribute that
    contains the auto-generated JavaScript for this class.
    """
    
    _HANDLER_COUNT = 0
    _IS_HASEVENTS = True
    
    def __init__(self, init_handlers=True):
        
        # Init some internal variables
        self.__handlers = {}
        self.__props_being_set = {}
        self.__initial_pending_events = []
        
        # Create properties
        for name in self.__properties__:
            self.__handlers.setdefault(name, [])
            self['_' + name + '_value'] = None  # need *something*
        for name in self.__properties__:
            func = self['_' + name + '_func']
            creator = self['__create_' + func.emitter_type]
            creator(name)
            if func.default is not undefined:
                self._set_prop(name, func.default, True)
        
        # Create emitters
        for name in self.__emitters__:
            self.__handlers.setdefault(name, [])
            func = self['_' + name + '_func']
            self.__create_Emitter(name)
        
        # Init handlers and properties now, or later?
        if init_handlers:
            self._init_handlers()
    
    def __init_handlers(self, initial_pending_events):
        # Create handlers
        for name in self.__handlers__:
            func = self[name]
            self[name] = self.__create_Handler(func, name, func._connection_strings)
        # Emit events for properties
        for ev in initial_pending_events:
            self._emit(ev)
    
    def __connect(self, *connection_strings):
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
        
        return self.__create_Handler(func, func.name or 'anonymous', connection_strings)
    
    def __create_PyProperty(self, name):
        self.__create_Property(name)
    
    def __create_Property(self, name):
        private_name = '_' + name + '_value'
        def getter():
            return self[private_name]
        def setter(x):
            self._set_prop(name, x)
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_Readonly(self, name):
        private_name = '_' + name + '_value'
        def getter():
            return self[private_name]
        def setter(x):
            raise AttributeError('Readonly %s is not settable' % name)
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_Emitter(self, name):
        def getter():
            return self._get_emitter(name)
        def setter(x):
            raise AttributeError('Emitter %s is not settable' % name)
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_Handler(self, func, name, connection_strings):
        
        # Create function that becomes our "handler object"
        def handler(*events):
            return func.apply(self, events)
        
        # Attach methods to the function object (this gets replaced)
        HANDLER_METHODS_HOOK  # noqa
        
        # Init handler
        that = self
        HasEvents.prototype._HANDLER_COUNT += 1
        handler._name = name
        handler._id = 'h' + str(HasEvents.prototype._HANDLER_COUNT)
        handler._ob = lambda : that  # no weakref in JS
        handler._init(connection_strings, self)
        
        return handler


def get_HasEvents_js():
    """ Get the final code for the JavaScript version of the HasEvents class.
    """
    # Start with our special JS version
    jscode = py2js(HasEventsJS, 'HasEvents')
    # Add the Handler methods
    code = '\n'
    for name, val in sorted(Handler.__dict__.items()):
        if not name.startswith('__') and callable(val):
            code += py2js(val, 'handler.' + name, indent=1)[4:]
            code += '\n'
    jscode = jscode.replace('HANDLER_METHODS_HOOK', code)
    # Add the methods from the Python HasEvents class
    code = '\n'
    for name, val in sorted(HasEvents.__dict__.items()):
        if name.startswith(('__', '_HasEvents__')) or not callable(val):
            continue
        code += py2js(val, 'HasEvents.prototype.' + name)
        code += '\n'
    jscode += code
    # Almost done
    jscode = jscode.replace('new Dict()', '{}').replace('new Dict(', '_pyfunc_dict(')
    return jscode


HasEventsJS.JSCODE = get_HasEvents_js()


def create_js_hasevents_class(cls, cls_name, base_class='HasEvents.prototype'):
    """ Create the JS equivalent of a subclass of the HasEvents class.
    
    Given a Python class with handlers, properties and emitters, this
    creates the code for the JS version of this class. It also supports
    class constants that are int/float/str, or a tuple/list thereof.
    The given class does not have to be a subclass of HasEvents.
    
    This more or less does what HasEventsMeta does, but for JS.
    """
    
    assert cls_name != 'HasEvents'  # we need this special class above instead
    
    handlers = []
    emitters = []
    properties = []
    total_code = []
    funcs_code = []  # functions and emitters go below class constants
    const_code = []
    err = ('Objects on JS HasEvents classes can only be int, float, str, '
           'or a list/tuple thereof. Not %s -> %r.')
    
    total_code.append('\n'.join(get_class_definition(cls_name, base_class)).rstrip())
    prefix = '' if cls_name.count('.') else 'var '
    total_code[0] = prefix + total_code[0]
    
    # Functions to ignore
    special_funcs = ['_%s_func' % name for name in 
                     (cls.__handlers__ + cls.__emitters__ + cls.__properties__)]
    OK_MAGICS = ('__properties__', '__emitters__', '__handlers__',
                 '__local_properties__')
    
    for name, val in sorted(cls.__dict__.items()):
        name = name.replace('_JS__', '_%s__' % cls_name.split('.')[-1])  # fix mangling
        if name in special_funcs:
            pass
        elif isinstance(val, BaseEmitter):
            funcname = '_' + name + '_func'
            if isinstance(val, Property):
                properties.append(name)
            else:
                emitters.append(name)
            # Add function def
            code = py2js(val._func, cls_name + '.prototype.' + funcname)
            code = code.replace('super()', base_class)  # fix super
            funcs_code.append(code.rstrip())
            # Mark to not bind the func
            t = '%s.prototype.%s.nobind = true;'
            funcs_code.append(t % (cls_name, funcname))
            # Has default val?
            if isinstance(val, Property) and val._defaults:
                default_val = json.dumps(val._defaults[0])
                t = '%s.prototype.%s.default = %s;'
                funcs_code.append(t % (cls_name, funcname, default_val))
            # Add type of emitter
            t = '%s.prototype.%s.emitter_type = %s;'
            emitter_type = val.__class__.__name__
            funcs_code.append(t % (cls_name, funcname, reprs(emitter_type)))
            funcs_code.append('')
        elif isinstance(val, HandlerDescriptor):
            funcname = name  # funcname is simply name, so that super() works
            handlers.append(name)
            # Add function def
            code = py2js(val._func, cls_name + '.prototype.' + funcname)
            code = code.replace('super()', base_class)  # fix super
            funcs_code.append(code.rstrip())
            # Mark to not bind the func
            t = '%s.prototype.%s.nobind = true;'
            funcs_code.append(t % (cls_name, funcname))
            # Add connection strings to the function object
            t = '%s.prototype.%s._connection_strings = %s;'
            funcs_code.append(t % (cls_name, funcname, reprs(val._connection_strings)))
            funcs_code.append('')
        elif callable(val):
            code = py2js(val, cls_name + '.prototype.' + name)
            code = code.replace('super()', base_class)  # fix super
            funcs_code.append(code.rstrip())
            funcs_code.append('')
        elif name in OK_MAGICS:
            t = '%s.prototype.%s = %s;'
            const_code.append(t % (cls_name, name, reprs(val)))
        elif name.startswith('__'):
            pass  # we create our own __emitters__, etc.
        else:
            try:
                serialized = json.dumps(val)
            except Exception as err:  # pragma: no cover
                raise ValueError('Attributes on JS HasEvents class must be '
                                 'JSON compatible.\n%s' % str(err))
            #const_code.append('%s.prototype.%s = JSON.parse(%s)' %
            #                  (cls_name, name, reprs(serialized)))
            const_code.append('%s.prototype.%s = %s;' % (cls_name, name, serialized))
    
    if const_code:
        total_code.append('')
        total_code.extend(const_code)
    if funcs_code:
        total_code.append('')
        total_code.extend(funcs_code)
    total_code.append('')
    return '\n'.join(total_code)


if __name__ == '__main__':
    # Testing ...
    from flexx import event
    class Foo(HasEvents):
        @event.prop
        def foo(self, v=0):
            return v
        
    print(HasEventsJS.JSCODE)
    print(len(HasEventsJS.JSCODE))
    #print(create_js_hasevents_class(Foo, 'Foo'))
