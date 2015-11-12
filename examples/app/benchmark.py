"""
Benchmark PyScript, to compare with CPython, Pypy, Brython, etc.

It appears that PyScript is significantly faster than Brython, which
seems to be the fastest Python-in-the-brower so far. It is also faster
than CPython and for some tests on par with Pypy.

See also http://brythonista.wordpress.com/2015/03/28

Some quick pystone results on my machine (Win 10, Intel i7-4710 HQ 2.5GHz):

* CPython 3.4:          126396 pystones / second
* Pypy3:                980334 pystones / second
* PyScript on Firefox:  443478 pystones / second
* PyScript on Chrome:   268225 pystones / second
* PyScript on MS Edge:  347451 pystones / second
* Brython (debug off):    4751 pystones / second
"""

import sys
import platform
from test import pystone

from flexx import app, react, pyscript

# Backend selection
BACKEND = 'xul'
if sys.argv[1:]:
    BACKEND = sys.argv[1]

# Get pystone code
pycode = open(pystone.__file__, 'rb').read().decode()
jscode = pyscript.py2js(pycode, module='pystone')


def convolve():
    import time
    N = 10000
    data = [0] * N
    support = 3
    t0 = time.time()
    time.sleep(0.5)
    for iter in range(10):
        for i in range(support, N-support):
            for j in range(-support, support+1):
                data[i] += data[i+j] * (1/support*2)
    t1 = time.time()
    print('convolution took %f s' % (t1-t0))
    

def bench_str():
    """ From http://brythonista.wordpress.com/2015/03/28
    """
    import time
    
    t0 = time.time()
    for i in range(1000000):
        a = 1
    print("assignment.py", time.time()-t0)
    
    t0 = time.time()
    a = 0
    for i in range(1000000):
        a += 1
    print("augm_assign.py", time.time()-t0)
    
    t0 = time.time()
    for i in range(1000000):
        a = 1.0
    print("assignment_float.py", time.time()-t0)
    
    t0 = time.time()
    for i in range(1000000):
        a = {0: 0}
    print("build_dict.py", time.time()-t0)
    
    t0 = time.time()
    a = {0: 0}
    
    for i in range(1000000):
        a[0] = i
    
    assert a[0]==999999
    print("set_dict_item.py", time.time()-t0)
    
    t0 = time.time()
    for i in range(1000000):
        a = [1, 2, 3]
    print("build_list.py", time.time()-t0)
    
    t0 = time.time()
    a = [0]
    
    for i in range(1000000):
        a[0] = i
    print("set_list_item.py", time.time()-t0)
    
    t0 = time.time()
    a, b, c = 1, 2, 3
    for i in range(1000000):
        a + b + c
    print("add_integers.py", time.time()-t0)
    
    t0 = time.time()
    a, b, c = 'a', 'b', 'c'
    for i in range(1000000):
        a + b + c
    print("add_strings.py", time.time()-t0)
    
    t0 = time.time()
    for _i in range(100000):
        str(_i)
    print("str_of_int.py", time.time()-t0)
    
    t0 = time.time()
    for i in range(1000000):
        def f():
            pass
    print("create_function.py", time.time()-t0)
    
    t0 = time.time()
    def g(x):
        return x
    for i in range(1000000):
        g(i)
    print("function_call.py", time.time()-t0)


class Benchmarker(app.Model):
    
    def _init(self):
        self.session.add_asset('pystone.js', jscode.encode())
    
    @react.source
    def run_js_tests(v):
        return v
    
    def benchmark(self):
        print('\n==== Python %s %s =====\n' % (platform.python_implementation(), 
                                               platform.python_version()))
        pystone.main()
        convolve()
        bench_str()
        
        # Trigger benchmark in JS
        self.run_js_tests._set(1)
    
    class JS:
        
        BACKEND = BACKEND
        convolve = convolve
        bench_str = bench_str
        
        @react.connect('run_js_tests')
        def _benchmark(self):
            print()
            print('==== PyScript on %s =====' % self.BACKEND)
            print()
            pystone.main()
            self.convolve()
            self.bench_str()


b = app.launch(Benchmarker, BACKEND)
b.benchmark()
app.run()
