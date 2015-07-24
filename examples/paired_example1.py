from time import perf_counter
from flexx import react

from flexx import pair


@pair.app
class Name(pair.Pair):
    
    class JS:
        @react.input
        def first_name(n):
            return n
        
        @react.act('foo')
        def bar(v):
            print('hellow from JS, foo =', v)
            # trigger a change in name
            if v==7:
                self.last_name('klein')
            if v==8:
                return self  # to test that we get the Name instance in Py
    
    @react.input
    def last_name(n='doe'):
        return n
    
    @react.watch('first_name', 'last_name')
    def full_name(n1, n2):
        return n1 + ' ' + n2
    
    @react.act('full_name')
    def show_name(n):
        print('name is:', n)
    
    def set_first_name_in_js(self, n):
        self.call_js('first_name(%r)' % n)
    
    @react.input
    def foo(v=42):
        # todo: initial value received by JS is null
        return v
    
    @react.watch('bar')
    def bar_value(v):
        return v


name = Name.launch('nodejs')
name.set_first_name_in_js('almar')
