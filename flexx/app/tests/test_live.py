""" Test a live app connection.
"""

import os
import time
import sys

import tornado

from flexx import app, event, webruntime
from flexx.pyscript import this_is_js

from flexx.util.testing import run_tests_if_main, raises, skip


ON_TRAVIS = os.getenv('TRAVIS', '') == 'true'
ON_PYPY = '__pypy__' in sys.builtin_module_names

TIMEOUT1 = 10.0  # Failsafe
TIMEOUT2 = 1.0


def runner(cls):
    
    # Run with a fresh server
    server = app.create_server(port=0, new_loop=True)
    
    t = app.launch(cls, 'firefox-app')
    t.test_init()
    t.test_set_result()
    # Install failsafe. Use a closure so failsafe wont spoil a future test
    isrunning = True
    def stop():
        if isrunning:
            app.stop()
    app.call_later(TIMEOUT1, stop)
    # Enter main loop until we get out
    t0 = time.time()
    app.start()
    print('ran %f seconds' % (time.time()-t0))
    isrunning = False
    # Check result
    if True:  # not (ON_TRAVIS and ON_PYPY):  # has intermittent fails on pypy3
        t.test_check()
    # Shut down
    t.session.close()


class Model0(app.Model):
    """ Base tester class.
    """
    def test_init(self):
        pass
    
    def test_set_result(self):
        self.call_js('set_result_later()')

    def test_check(self):
        pass
    
    class Both:
        
        @event.prop
        def result(self, v=None):
            if not this_is_js():
                if v:
                    print('stopping by ourselves', v)
                    app.call_later(TIMEOUT2, app.stop)
            return v

    class JS:
        
        def set_result_later(self):
            # Do in next event loop iter
            window.setTimeout(self.set_result, 0)
        
        def set_result(self):
            pass


class ModelA(Model0):
    """ Test both props, py-only props and js-only props.
    """
    
    def test_init(self):
        assert self.foo1 == 1
    
    def test_check(self):
        assert self.foo1 == 1
        assert self.foo2 == 1
        #
        assert self.spam1 == 1
        assert self.spam2 == 1
        assert self.result == '1 1 - 1 1'
        print('A ok')
    
    @event.prop
    def spam1(self, v=0):
        return int(v+1)
    
    @event.prop
    def spam2(self, v=0):
        return int(v+1)
    
    class Both:
        
        @event.prop
        def foo1(self, v=0):
            return float(v+1)
        
        @event.prop
        def foo2(self, v=0):
            return float(v+1)
        
    class JS:
        
        @event.prop
        def bar1(self, v=0):
            return int(v+1)
        
        @event.prop
        def bar2(self, v=0):
            return int(v+1)
        
        def set_result(self):
            self.result = ' '.join([self.foo1, self.foo2, '-',
                                    self.bar1, self.bar2])

class ModelB(ModelA):
    """ Like A, but some inheritance in the mix.
    """
    
    def test_check(self):
        assert self.foo1 == 1
        assert self.foo2 == 2
        assert self.foo3 == 2
        #
        assert self.spam1 == 1
        assert self.spam2 == 2
        assert self.spam3 == 2
        assert self.result == '1 2 2 - 1 2 2'
        print('B ok')
    
    @event.prop
    def spam2(self, v=0):
        return int(v+2)
    
    @event.prop
    def spam3(self, v=0):
        return int(v+2)
    
    class Both:
        
        @event.prop
        def foo2(self, v=0):
            return int(v+2)
        
        @event.prop
        def foo3(self, v=0):
            return int(v+2)
    
    class JS:
        
        @event.prop
        def bar2(self, v=0):
            return int(v+2)
        
        @event.prop
        def bar3(self, v=0):
            return int(v+2)
        
        def set_result(self):
            self.result = ' '.join([self.foo1, self.foo2, self.foo3, '-',
                                    self.bar1, self.bar2, self.bar3])


class ModelC(ModelB):
    """ Test properties and local properties, no duplicates etc.
    """
    
    def test_check(self):
        py_result = ' '.join(self.__properties__) + ' - ' + ' '.join(self.__local_properties__)
        js_result = self.result
        assert py_result == 'foo1 foo2 foo3 result spam1 spam2 spam3 sync_props - spam1 spam2 spam3 sync_props'
        assert js_result == 'bar1 bar2 bar3 foo1 foo2 foo3 result - bar1 bar2 bar3'
        print('C ok')
    
    class JS:
        
        def set_result(self):
            self.result = ' '.join(self.__properties__) + ' - ' + ' '.join(self.__local_properties__)


class ModelD(ModelB):
    """ Test setting properties
    """
    
    def test_init(self):
        
        assert self.foo2 == 2
        self.foo2 = 10
        self.spam2 = 10
        assert self.foo2 == 12
    
    def test_check(self):
        
        assert self.result == 'ok'
        
        assert self.foo2 == 16  # +2 in py - js - py
        assert self.foo3 == 14  # +2 in js - py
        assert self.spam2 == 12
    
    class JS:
        
        def init(self):
            super().init()
            print(self.foo3, self.bar3)
            
            assert self.foo3 == 2
            self.foo3 = 10
            assert self.foo3 == 12
            
            assert self.bar3 == 2
            self.bar3 = 10
            assert self.bar3 == 12
        
        def set_result(self):
            assert self.foo2 == 14  # +2 +2
            assert self.foo3 == 12
            assert self.bar3 == 12
            self.result = 'ok'


class ModelE(ModelA):
    """ Test counting events
    """
    
    def test_init(self):
        self.res1 = []
        self.res2 = []
        
        self.emit('foo', {})
        self.emit('foo', {})
    
    @event.connect('foo')
    def foo_handler(self, *events):
        self.res1.append(len(events))
        print('Py saw %i foo events' % len(events))
    
    @event.connect('bar')
    def bar_handler(self, *events):
        self.res2.append(len(events))
        print('Py saw %i bar events' % len(events))
    
    def test_check(self):
        result_py = self.res1 + [''] + self.res2
        result_js = self.result
        print('result_py', result_py)
        print('result_js', result_js)
        assert result_py == [2, '', 2]
        if False:  # ON_TRAVIS:  # Ok, good enough Travis ...
            assert result_js == [2, '', 2] or result_js == [1, 1, '', 2]
        else:
            assert result_js == [2, '', 2]
    
    class JS:
        
        def init(self):
            self.res3 = []
            self.res4 = []
        
            self.emit('bar', {})
            self.emit('bar', {})
        
        @event.connect('foo')
        def foo_handler(self, *events):
            self.res3.append(len(events))
            print('JS saw %i foo events' % len(events))
        
        @event.connect('bar')
        def bar_handler(self, *events):
            self.res4.append(len(events))
            print('JS saw %i bar events' % len(events))
        
        def set_result(self):
            print('setting result in js' + (self.res3 + [''] + self.res4) )
            self.result = self.res3 + [''] + self.res4


class ModelF(ModelA):
    """ Test that props emit events (even for local props).
    """
    
    def test_init(self):
        self.res = []
        
        self.foo1 = 2
        self.spam1 = 2
    
    def test_check(self):
        assert self.res.count('foo1') == 3  # bit of a glitch bc we do +1
        assert self.res.count('foo2') == 2
        assert self.res.count('bar1') == 2
        assert self.res.count('spam1') == 2
        
        assert self.result.count('foo1') == 2
        assert self.result.count('foo2') == 2
        assert self.result.count('bar1') == 2
        assert self.result.count('spam1') == 2
        
        print('F ok')
    
    @event.connect('foo1', 'foo2', 'spam1', 'bar1')
    def on_prop_change(self, *events):
        for ev in events:
            self.res.append(ev.type)
    
    class JS:
        
        def init(self):
            super().init()
            self.res = []
        
        @event.connect('foo1', 'foo2', 'spam1', 'bar1')
        def on_prop_change(self, *events):
            for ev in events:
                self.res.append(ev.type)
        
        def set_result(self):
            self.foo2 = 10
            self.bar1 = 10
            self.on_prop_change.handle_now()
            
            self.result = self.res

##


def test_generated_javascript():
    # Test that there are no diplicate funcs etc.
    
    codeA, codeB = ModelA.JS.CODE, ModelB.JS.CODE
    
    assert codeA.count('.foo1 = function') == 1
    assert codeA.count('.foo2 = function') == 1
    assert codeA.count('.foo3 = function') == 0
    assert codeA.count('.bar1 = function') == 1
    assert codeA.count('.bar2 = function') == 1
    assert codeA.count('.bar3 = function') == 0
    
    assert codeB.count('.foo1 = function') == 0
    assert codeB.count('.foo2 = function') == 1
    assert codeB.count('.foo3 = function') == 1
    assert codeB.count('.bar1 = function') == 0
    assert codeB.count('.bar2 = function') == 1
    assert codeB.count('.bar3 = function') == 1


def test_apps():
    
    if not webruntime.FirefoxRuntime().is_available():
        skip('This live test needs firefox.')
    
    runner(ModelA)
    runner(ModelB)
    runner(ModelC)
    runner(ModelD)
    runner(ModelE)


# NOTE: beware future self: if running this in Pyzo, turn off GUI integration!

#runner(ModelE)
run_tests_if_main()
