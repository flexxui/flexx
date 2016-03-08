"""
Implementation of flexx.event in JS via PyScript.
"""

import json

from flexx.pyscript import py2js as py2js_, undefined
from flexx.pyscript.parser2 import get_class_definition

from flexx.event._emitters import BaseEmitter, Property
from flexx.event._handler import HandlerDescriptor, Handler
from flexx.event._hasevents import BaseHasEvents


Object = Date = None  # fool pyflake

reprs = json.dumps


def py2js(*args, **kwargs):
    kwargs['inline_stdlib'] = False
    kwargs['docstrings'] = False
    return py2js_(*args, **kwargs)


class HasEventsJS(BaseHasEvents):
    """ An implementation of the HasEvents class in PyScript. It has
    some boilerplate code to create handlers and emitters, but otherwise
    shares most of the code with the Python classes by transpiling their
    methods via PyScript. This ensures that the Python and JS
    implementation of this event system have the same API and have the
    same behavior.
    
    The Python version of this class has a ``JSCODE`` attribute that
    contains the auto-generated JavaScript for this class.
    """
    
    _HANDLER_COUNT = 0
    
    def __init__(self):
        super().__init__()
        
        for name in self.__handlers__:
            func = self['_' + name + '_func']
            self[name] = self.__create_Handler(func, name, func._connection_strings)
        # todo: turn on_xx into a handler
        # todo: connect method
        for name in self.__emitters__:
            func = self['_' + name + '_func']
            creator = self['__create_' + func._emitter_type]
            creator(func, name)
    
    def __create_Property(self, func, name):
        private_name = '_' + name + '_value'
        def getter():
            return self[private_name]
        def setter(x):
            self._set_prop(name, x)
        self[private_name] = func.apply(self, [])  # init
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_Readonly(self, func, name):
        private_name = '_' + name + '_value'
        def getter():
            return self[private_name]
        def setter(x):
            raise ValueError('Readonly %s is not settable' % name)
        self[private_name] = func.apply(self, [])  # init
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_Emitter(self, func, name):
        private_name = '_' + name + '_value'
        def getter():
            return func.bind(self)
        def setter(x):
            raise ValueError('Emitter %s is not settable' % name)
        opts = {'enumerable': True, 'configurable': True,  # i.e. overloadable
                'get': getter, 'set': setter}
        Object.defineProperty(self, name, opts)
    
    def __create_Handler(self, func, name, connection_strings):
        
        # Create function that becomes our "handler object"
        def handler(*events):
            return func.apply(self, events)
        
        # Attach methods to the function object (this gets replaced)
        HANDLER_METHODS_HOOK
        
        # Init handler
        that = this
        HasEvents.prototype._HANDLER_COUNT += 1
        handler._name = name
        handler._id = 'h' + str(HasEvents.prototype._HANDLER_COUNT)
        handler._ob = lambda : that  # no weakref in JS
        handler._init(connection_strings, self)
        
        return handler


# todo: can I turn this into one class instead of an inherited class?
def patch_HasEventsJS(jscode):
    code = '\n'
    for name, val in sorted(Handler.__dict__.items()):
        if not name.startswith('__') and callable(val):
            code += py2js(val, 'handler.' + name, indent=1, docstrings=False)
            code += '\n'
    code = code.replace('new Dict()', '{}')
    return jscode.replace('HANDLER_METHODS_HOOK', code)


HasEventsJS.JSCODE = patch_HasEventsJS(py2js(HasEventsJS, 'HasEvents'))



def create_js_hasevents_class(cls, cls_name, base_class='HasEvents.prototype'):
    """ Create the JS equivalent of a subclass of the HasEvents class.
    
    Given a Python class with handlers and emitters, this creates the
    code for the JS version of this class. It also supports class
    constants that are int/float/str, or a tuple/list thereof.
    """
    
    # todo: use tmp name instead of xxx.yyy.prototype.funcname.zzzzzz
    
    assert cls_name != 'HasEvents'  # we need this special class above instead
    
    emitters = []
    handlers = []
    properties = []
    total_code = []
    funcs_code = []  # functions and emitters go below class constants
    const_code = []
    err = ('Objects on JS HasEvents classes can only be int, float, str, '
           'or a list/tuple thereof. Not %s -> %r.')
    
    total_code.extend(get_class_definition(cls_name, base_class))
    prefix = '' if cls_name.count('.') else 'var '
    total_code[0] = prefix + total_code[0]
    
    for name, val in sorted(cls.__dict__.items()):
        name = name.replace('_JS__', '_%s__' % cls_name.split('.')[-1])  # fix mangling
        funcname = '_' + name + '_func'
        if isinstance(val, BaseEmitter):
            emitters.append(name)
            if isinstance(val, Property):
                properties.append(name)
            # Add function def
            code = py2js(val._func, cls_name + '.prototype.' + funcname)
            code = code.replace('super()', base_class)  # fix super
            funcs_code.append(code.rstrip())
            # Mark to not bind the func
            t = '%s.prototype.%s.nobind = true;'
            funcs_code.append(t % (cls_name, funcname))
            # Add type of emitter
            t = '%s.prototype.%s._emitter_type = %s;'
            emitter_type = val.__class__.__name__
            funcs_code.append(t % (cls_name, funcname, reprs(emitter_type)))
            funcs_code.append('')
        elif isinstance(val, HandlerDescriptor):
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
        elif name.startswith('__'):
            pass  # we create our own __emitters__ list
        else:
            try:
                serialized = json.dumps(val)
            except Exception as err:  # pragma: no cover
                raise ValueError('Attributes on JS HasEvents class must be '
                                 'JSON compatible.\n%s' % str(err))
            const_code.append('%s.prototype.%s = JSON.parse(%s)' %
                              (cls_name, name, reprs(serialized)))
    
    # Insert __emitters__ that we found
    if base_class in ('Object', 'HasEvents.prototype'):
        t = '%s.prototype.__emitters__ = %s;'
        total_code.append(t % (cls_name, reprs(list(sorted(emitters)))))
        t = '%s.prototype.__properties__ = %s;'
        total_code.append(t % (cls_name, reprs(list(sorted(properties)))))
        t = '%s.prototype.__handlers__ = %s;'
        total_code.append(t % (cls_name, reprs(list(sorted(handlers)))))
    else:
        t = '%s.prototype.__emitters__ = %s.__emitters__.concat(%s).sort();'
        total_code.append(t % (cls_name, base_class, reprs(emitters)))
        t = '%s.prototype.__properties__ = %s.__properties__.concat(%s).sort();'
        total_code.append(t % (cls_name, base_class, reprs(properties)))
        t = '%s.prototype.__handlers__ = %s.__handlers__.concat(%s).sort();'
        total_code.append(t % (cls_name, base_class, reprs(handlers)))
    
    total_code.append('')
    total_code.extend(const_code)
    total_code.append('')
    total_code.extend(funcs_code)
    return '\n'.join(total_code)


if __name__ == '__main__':
    from flexx import event
    from flexx.pyscript import evaljs, get_full_std_lib
    from flexx.pyscript.stdlib import get_std_info, get_partial_std_lib
    
    class Tester(event.HasEvents):
        
        # spam1 = 3
        # spam2 = 'x', 'y'
        
        @event.prop
        def foo(self, v=3):
            return int(v) + 10
        
        @event.connect('foo')
        def handle_foo(self, *events):
            print(events)
            #print('haha')
    
    code = ''
    code += py2js(BaseHasEvents)
    code += HasEventsJS.JSCODE
    code += create_js_hasevents_class(Tester, 'Tester')
    code += 'var x = new Tester(); x.foo=32; x.handle_foo.handle_now()'
    nargs, function_deps, method_deps = get_std_info(code)
    code = get_partial_std_lib(function_deps, method_deps, []) + code
    
    #print(py2js(BaseHasEvents))
    print(evaljs(code))
    
