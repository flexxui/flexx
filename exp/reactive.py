""" Attempt to implement a reactive system in Python. With that I mean
a system in which signals are bound implicitly, as in Shiny.

The Signal is the core element here. It is like the Property in
HasProps. A function can easily be turned into a Signal object by
decorating it.

Other than Properties, signals have a function associated with them.
that compute stuff (maybe rename signal to behavior). They also cache their
value.

"""

import re
import sys
import time
import inspect


class Signal:
    #todo: or is this a "behavior"?
    """ Wrap a function in a class to allow marking it dirty and caching
    last result.
    """
    def __init__(self, fun):
        self._fun = fun
        self._value = None
        self._dirty = True
        self._dependers = []
    
    def __call__(self, *args):
        if self._dirty:
            self._value = self._fun(*args)
            self._dirty = False
        return self._value
    
    def set_dirty(self):
        self._dirty = True
        for dep in self._dependers:
            dep.set_dirty()
            dep()


class Input(Signal):
    """ A signal defined simply by a value that can be set. You can
    consider this a source signal.
    """
    def __init__(self):
        Signal.__init__(self, lambda x=None:None)
    
    def set(self, value):
        self._value = value
        self.set_dirty()


class Output(Signal):
    pass  # I don't think that I need this?


def check_deps(fun, locals, globals):
    """ Analyse the source code of fun to get the signals that the reactive
    function depends on. It then registers the function at these signals.
    """
    
    # Get source of function and find uses of inputs
    # todo: use AST parsing instead
    s = inspect.getsource(fun._fun)
    matches = re.findall(r'([a-zA-Z0-9_.]+?)\.get_signal\([\'\"](\w+?)[\'\"]\)', s)
    fun._nmatches = 0
    
    # print('found %i deps on %r' % (len(matches), fun))
    # For each used input, try to retrieve the actual object
    for match in matches:
        ob = locals.get(match[0], globals.get(match[0], None))
        if ob is None:
            print('could not locate dependency %r' % match[0])
        else:
            ob._bind_signal(match[1], fun)
            fun._nmatches += 1
            # print('bound signal for', ob)
            #dep = getattr(ob, 'input_'+match[1])
            #print('found dep ', dep)
    
    # Detect outputs
    #matches = re.findall(r'([a-zA-Z0-9_.]+?)\.set_output\([\'\"](\w+?)[\'\"]\,', s)
    
    # Detect calls
    if fun._nmatches:
        matches = re.findall(r'([a-zA-Z0-9_.]+?)\(', s)
        for match in matches:
            ob = locals.get(match[0], globals.get(match[0], None))
            if isinstance(ob, Signal):
                ob._dependers.append(fun)
    
    # # For each used input, try to retrieve the actual object
    # for match in matches:
    #     ob = locals.get(match[0], globals.get(match[0], None))
    #     if ob is None:
    #         print('could not locate dependency %r' % match[0])
    #     else:
    #         ob._bind_signal(match[1], fun2)
    fun._deps_checked = len(matches)
    

def react(fun):
    """ decorator
    """
    # fun should be called, when any of its deps gets called
    # can I get that info?
    # Probably with sys.settrace(), but that is CPython specific.
    # Evaluating source code via inspect?
    # Evaluating the AST?
    # -> We can detect "input.slider" or something, but can we detect
    #    what object its called on? What is "w"?
    
    # Note: only works on Python implementations that have a stack
    _frame = sys._getframe(1)  
    
    # todo: from trellis:
    # if isinstance(rule, types.FunctionType): # only pick up name if a function
    #     if frame.f_locals.get(rule.__name__) is rule:   # and locally-defined!
    #         name = name or rule.__name__
    
    if not isinstance(fun, Signal):
        fun = Signal(fun)
    
    check_deps(fun, _frame.f_locals, _frame.f_globals)
    
    if fun._nmatches:
        return fun
    else:
        return fun._fun  # return original, its probbaly a method that we shoukd try later


class Reactive:
    """ Base class for classes that can have signals and reactive
    methods.
    """
    
    SIGNALS = []
    
    def __init__(self):
        self._signals = {}
        self._downstream = {}
        
        for name, val in self.SIGNALS:
            self._signals[name] = val
        
        for name in dir(self.__class__):
            cls_ob = getattr(self.__class__, name)
            if hasattr(cls_ob, '_deps_checked'):
                fun = getattr(self, name)
                # print('re-trying reactive')
                react(fun)
    
    def _emit_signal(self, name, value):
        self._signals[name] = value
        for f in self._downstream.get(name, ()):
            f.set_dirty()
            f()
    
    def _bind_signal(self, name, fun):
        funcs = self._downstream.setdefault(name, [])
        if fun not in funcs:
            funcs.append(fun)
    
    def bind_signals(self, *args):
        # Alternative: explicit binding
        
        def bind(fun):
            if not isinstance(fun, Signal):
                fun = Signal(fun)
            for name in names:
                funcs = self._downstream.setdefault(name, [])
                if fun not in funcs:
                    funcs.append(fun)
            return fun
        
        fun = None
        names = []
        for arg in args:
            if callable(arg):
                fun = arg
            else:
                names.append(arg)
        
        print('binding ', names)
        if fun is None:
            return bind
        else:
            return bin(fun)
    
    def get_signal(self, name):
        # i = inspect.getframeinfo(inspect.currentframe())
        if False:
            s = inspect.stack()
            caller = s[1]
            print(caller[0].f_locals.keys())
            print(caller[0].f_globals.keys())
            id = caller[1], caller[2], caller[3]
            # if 'self' in f_locals:
            #     fun = f_locals()
            self.caller = caller
            self.caller2 = sys._getframe(1)
            fun = caller[0].f_globals[id[-1]]
            print(id, fun)
            self._bind_signal(name, fun)
        return self._signals[name]
    
    def set_output(self, name, value):
        # def xx(fun):
        #     def yy():
        #         value = fun()        
        #         f = getattr(self, 'on_' + name)
        #         f(value)
        #     fun()
        #     return yy
        # return xx
        f = getattr(self, 'on_' + name)
        f(value)


print('-----')



class Widget(Reactive):
    
    SIGNALS = [('slider1', 0), ('slider2', 0)]
    
    def manual_slider1(self, v):
        """ Simulate changing a slider value.
        """
        # if this is called, outpus should be shown
        # todo: also store latest value
        self._emit_signal('slider1', v)
    
    def manual_slider2(self, v):
        self._emit_signal('slider2', v)
    
    def on_show(self, val):
        print('hooray!', val)


class Widget1(Widget):
    
    @react
    def bla1(self):
        x = self.get_signal('slider1') * 3
        self.set_output('show', x)

w = Widget1()


@react
def something_that_takes_long():
    # when slider1 changes, it should invoke bla! (and other inputs/signals that depend on it
    print('this may take a while')
    time.sleep(1)
    return w.get_signal('slider1') * 2

@react
def bla():
    # to an output.
    x = something_that_takes_long()
    x += w.get_signal('slider2')
    w.set_output('show', x - 1)
    # todo: set_output, or return and connect somehow?


print('-----')

    
class Widget2(Widget):
    
    def on_slider1_change(self):  # but can only bind to single change
        x = self.get_signal('slider1') * 3
        self.set_output('show', x)
        
    # # maybe this? but then slider1 of what?
    # @binding('slider1', 'slider2')
    # def xxx(self):
    #     pass

w2 = Widget2()


@w2.bind_signals('slider1')
def something_that_takes_long():
    # when slider1 changes, it should invoke bla! (and other inputs/signals that depend on it
    print('this may take a while')
    time.sleep(1)
    return w2.get_signal('slider1') * 2


#@some_widget.bind_signals('foo')
#@some_other_widget.bind_signals('bar')
@w2.bind_signals('slider2')
# todo: w2.bind_signals('slider2', something_that_takes_long)
def bla():
    # to an output.
    x = something_that_takes_long()
    x += w2.get_signal('slider2')
    w2.set_output('show', x - 1)
    # todo: set_output, or return and connect somehow?



print('-----')


class Temp2(Reactive):
    """ Simple example of object that has signals for temperature in both
    Celcius and Fahrenheit. Changing either automatically changes the other.
    """
    
    SIGNALS = [('C', 0), ('F', 32)]
    
t2 = Temp2()
self = t2

@t2.bind_signals('F')
def _c2f():
    self._signals['C'] = (self.get_signal('F')-32) / 1.8

@t2.bind_signals('C')
def _f2c():
    self._signals['F'] = self.get_signal('C') * 1.8 + 32

@t2.bind_signals('C', 'F')
def _show():
    print('C:', self.get_signal('C'))
    print('F:', self.get_signal('F'))


    
    

