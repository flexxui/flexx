""" Implementation of flexx.reactive in JS via PyScript.
"""

from flexx.pyscript import js, evaljs, evalpy
from flexx.pyscript.parser2 import get_class_definition


@js
class HasSignals:
    
    __signals__ = []
    
    def __init__(self):
        self._create_signals()
        self.connect_signals(False)
    
    def connect_signals(self, raise_on_fail=True):
        success = True
        for name in self.__signals__:
            if name in self.__props__:
                continue
            s = self[name]
            if s.not_connected:
                connected = s.connect(raise_on_fail)  # dont combine this with next line
                success = success and connected
        return success 
    
    def _create_property(obj, name, private_name, initial):
        def getter():
            return obj[private_name]
        def setter():
            raise ValueError(name + ' is not settable')
        obj[private_name] = initial
        opts = {"enumerable": True, 'get': getter, 'set': setter}
        Object.defineProperty(obj, name, opts)
    
    def _create_signals():
        self.__props__ = []  # todo: get rid of this?
        for name in self.__signals__:
            func = self['_' + name + '_func']
            creator = self['_create_' + func._signal_type]
            signal = creator.call(self, func, func._upstream)
            self._create_property(self, name, '_' + name + '_signal', signal)
    
    def _create_SourceSignal(func, upstream, selff):
        
        selff = self._create_Signal(func, upstream, selff)
        
        def _update_value():
            if selff._timestamp == 0:
                ok = False
                selff._dirty = False
                try:
                    value = selff._call_func()
                    ok = value is not undefined
                except Exception:
                    pass
                if ok:
                    selff._set_value(value)
                    return  # do not get from upstream initially
            
            # Get value from upstream
            if len(selff._upstream):
                #args = [s() for s in selff._upstream]
                args = [selff._value]  # todo: pyscript support for list comprehension
                for s in selff._upstream:
                    args.append(s())  # can raise SignalConnectionError
                value = selff._call_func(*args)
                selff._set_value(value)
        
        def _set(value):
            selff._set_value(selff._call_func(value))
            for s in selff._downstream:
                s._set_dirty(selff)  # do not set this signal dirty!
        
        original_set_dirty = selff._set_dirty
        def _set_dirty(initiator=None):
            original_set_dirty(initiator)
            selff._save_update()
        
        # Overload signal methods
        selff._update_value = _update_value
        selff._set = _set
        selff._set_dirty = _set_dirty
        
        return selff
    
    def _create_InputSignal(func, upstream):
        
        def selff(*args):
            if not len(args):
                return selff._get_value()
            elif len(args) == 1:
                return selff._set(args[0])
            else:
                raise ValueError('Setting an input signal requires exactly one argument')
        
        return self._create_SourceSignal(func, upstream, selff)
    
    def _create_WatchSignal(func, upstream, selff=None):
        return self._create_Signal(func, upstream, selff)
    
    def _create_ActSignal(func, upstream):
        selff = self._create_Signal(func, upstream)
        
        original_set_dirty = selff._set_dirty
        def _set_dirty(initiator=None):
            original_set_dirty(initiator)
            selff._save_update()
        
        selff._set_dirty = _set_dirty
        return selff
    
    def _create_Signal(func, upstream, selff=None):
        # We create the selff function which then serves as the signal object
        # that we populate with attributres, properties and functions.
        obj = this
        
        if selff is None:
            def selff(*args):
                if not len(args):
                    return selff._get_value()
                else:
                    raise RuntimeError('Can only set signal values of InputSignal objects.')
        
        # Create public attributes
        self._create_property(selff, 'value', '_value', None)
        self._create_property(selff, 'last_value', '_last_value', None)
        self._create_property(selff, 'timestamp', '_timestamp', 0)
        self._create_property(selff, 'last_timestamp', '_last_timestamp', 0)
        self._create_property(selff, 'not_connected', '_not_connected', 'No connection attempt yet.')
        #self._create_property(selff, 'name', '_name', func.name)  already is a property
        
        # Create private attributes
        selff.IS_SIGNAL = True
        selff._func = func
        selff._dirty = True
        selff.__self__ = obj  # note: not a weakref...
        selff._upstream = []
        selff._upstream_given = upstream
        selff._downstream = []
        
        def connect(raise_on_fail=True):
            # Resolve signals
            selff._not_connected = selff._resolve_signals()
            if selff._not_connected:
                if raise_on_fail:
                    raise RuntimeError('Connection error in signal "%s": ' % selff._name + selff._not_connected)
                return False
            # Subscribe
            for s in selff._upstream:
                s._subscribe(selff)
            # If connecting complete, update (or not)
            selff._set_dirty()
        
        def disconnect():
            while len(selff._upstream):
                s = selff._upstream.pop(0)
                s._unsubscribe(selff)
            selff._not_connected = 'Explicitly disconnected via disconnect()'
            selff._set_dirty()
        
        def _resolve_signals():
            upstream = []
            for fullname in selff._upstream_given:
                nameparts = fullname.split('.')
                # Obtain first part of path from the frame that we have
                ob = obj[nameparts[0]]
                # Walk down the object tree to obtain the full path
                for name in nameparts[1:]:
                    if ob is undefined:
                        break
                    if ob.IS_SIGNAL:
                        ob = ob()
                    ob = ob[name]
                # Add to list or fail
                if ob is undefined:
                    return 'Signal "%s" does not exist.' % fullname
                elif not ob.IS_SIGNAL:
                    return 'Object "%s" is not a signal.' % fullname
                upstream.append(ob)
            
            selff._upstream = upstream
            return False  # no error
        
        def _subscribe(s):
            if s not in selff._downstream:
                selff._downstream.append(s)
        
        def _unsubscribe(s):
            while s in selff._downstream:
                selff._downstream.remove(s)
        
        def _save_update():
            try:
                selff()
            except SignalConnectionError:
                pass
            except Exception as err:
                #print('Error updating signal:', err.stack)
                console.error('Error updating signal:', err)
        
        def _set_value(value):
            selff._last_value = selff._value
            selff._value = value
            selff._last_timestamp = selff._timestamp
            selff._timestamp = Date().getTime() / 1000
            selff._dirty = False
        
        def _get_value():
            if selff._not_connected:
                selff.connect(False)
            if selff._not_connected:
                raise SignalConnectionError()
            if selff._dirty:
                selff._update_value()
            return selff._value
        
        def _update_value():
            #args = [s() for s in selff._upstream]
            args = []  # todo: pyscript support for list comprehension
            for s in selff._upstream:
                args.append(s())  # can raise SignalConnectionError
            value = selff._call_func(*args)
            selff._set_value(value)
        
        def _call_func(*args):
            return func.apply(obj, args)
        
        def _set_dirty(initiator=None):
            if selff._dirty or selff is initiator:
                return
            elif initiator is None:
                initiator = selff
            # Update self
            selff._dirty = True
            # Allow downstream to update
            for s in selff._downstream:
                s._set_dirty(initiator)
        
        # Put functions on the signal
        selff.connect = connect
        selff.disconnect = disconnect
        selff._resolve_signals = _resolve_signals
        selff._subscribe = _subscribe
        selff._unsubscribe = _unsubscribe
        selff._save_update = _save_update
        selff._set_value = _set_value
        selff._get_value = _get_value
        selff._update_value = _update_value
        selff._call_func = _call_func
        selff._set_dirty = _set_dirty
        
        return selff

HasSignalsJS = HasSignals

def create_js_signals_class(cls, cls_name, base_class='HasSignals.prototype'):
    """ Create the JS equivalent of a subclass of the HasSignals class.
    
    Given a Python class with signals attached to it, this creates the
    code for the JS version of this class. Apart from converting the
    signals, it also supports class constants that are int/float/str,
    or a tuple/list thereof.
    """
    
    signals = []
    total_code = []
    funcs_code = []  # functions and signals go below class constants
    err = ('Objects on JS HasSignals classes can only be int, float, str, '
           'or a list/tuple thereof. Not %s -> %r.')
    
    total_code.extend(get_class_definition(cls_name, base_class))
    total_code[0] = 'var ' + total_code[0]
    
    for name, val in sorted(cls.__dict__.items()):
        if isinstance(val, Signal):
            code = js(val._func).jscode
            code = code.replace('super()', base_class)  # fix super
            signals.append(name)
            funcname = '_' + name + '_func'
            # Add function def
            t = '%s.prototype.%s = %s'
            funcs_code.append(t % (cls_name, funcname, code))
            # Add upstream signal names to the function object
            t = '%s.prototype.%s._upstream = %r;\n'
            funcs_code.append(t % (cls_name, funcname, val._upstream_given))
            # Add type of signal too
            t = '%s.prototype.%s._signal_type = %r;\n'
            signal_type = val.__class__.__name__
            funcs_code.append(t % (cls_name, funcname, signal_type))
        elif callable(val):
            code = js(val).jscode
            code = code.replace('super()', base_class)  # fix super
            funcs_code.append('%s.prototype.%s = %s' % (cls_name, name, code))
        elif name.startswith('__'):
            pass  # we create our own __signals__ list
        elif isinstance(val, (int, float, str)):
            total_code.append('%s.prototype.%s = %r' % (cls_name, name, val))
        elif isinstance(val, (tuple, list)):
            for item in val:
                if not isinstance(item, (float, int, str)):
                    raise ValueError(err % (name, item))
            total_code.append('%s.prototype.%s = %r' % (cls_name, name, list(val)))
        else:
            raise ValueError(err % (name, val))
    
    # Insert __signals__ that we found
    t = '%s.prototype.__signals__ = %s.__signals__.concat(%r).sort();'
    total_code.append(t % (cls_name, base_class, signals))
    
    total_code.extend(funcs_code)
    return '\n'.join(total_code)


from flexx.reactive import input, watch, act, source, HasSignals, Signal

class Foo:
    
    N = 4
    FMT = 'XX'
    
    def __init__(self):
        super().__init__()
    
    @input
    def title(v=''):
        return str(v)
    
    @watch('title')
    def title_len(v):
        return len(v)
    
    @act('title_len')
    def show_title(v):
        result.append(v)

if __name__ == '__main__':
    print(createHasSignalsClass(Foo, 'Foo'))

#code = 'var make_signal = ' + make_signal.jscode
#code += 'function foo (x) {console.log("haha", x); return x;}; var s = make_signal(foo); s(3); s.value'
#print(evaljs(code))