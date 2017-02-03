"""
Benchmark PyScript, to compare with CPython, Pypy, Brython, etc.

It appears that PyScript is significantly faster than Brython, which
seems to be the fastest Python-in-the-brower so far. It is also faster
than CPython and for some tests on par with Pypy.

See also http://brythonista.wordpress.com/2015/03/28

"""

# Measured results, in pystones/second, measured on 05-03-2016,
# on Win 10, Intel i7-4710 HQ 2.5GHz
RESULTS = [(124863, 'CPython 3.4', 'blue'),
           (137250, 'CPython 3.5', 'blue'),
           (3927770, 'Pypy4', 'blue'),
           (3739170, 'Pypy3', 'blue'),
           (127957, 'PyScript on Firefox', 'orange'),
           (79517, 'PyScript on Chrome', 'orange'),
           (128325, 'PyScript on MS Edge', 'orange'),
           (2982, 'Brython', 'magenta'),
           (2780, 'Skulpt', 'magenta'),
           (268817, 'PypyJS', 'magenta'),
           ]

import sys
from time import time
import platform
from test.pystone import main as pystone_main
from test import pystone

from flexx import app

# Mark the pystone module to be transpiled as a whole. It uses globals
# a lot, which somehow causes inifinite loops if its transpiled in parts.
pystone.__pyscript__ = True

# Backend selection
BACKEND = 'firefox-app or chrome-app'
if sys.argv[1:]:
    BACKEND = sys.argv[1]


def plot_results():
    import matplotlib.pyplot as plt
    plt.ion()
    
    data = list(reversed(RESULTS))
    plt.figure(1)
    plt.clf()
    ax = plt.subplot(111)
    ax.barh([i for i in range(len(data))], [x[0] for x in data],
            color=[x[2] for x in data])
    ax.set_yticks([i+0.3 for i in range(len(data))])
    ax.set_yticklabels([x[1] for x in data])
    ax.set_xscale('log')


class window:
    # Trick to be able to use the same code in JS and Python
    
    @classmethod
    def Float32Array(cls, n):
        """ Factory function. """
        return [0.0] * n


def convolve():
    N = 400000
    data = window.Float32Array(N)
    support = 3
    t0 = time()
    for i in range(support, N-support):
        for j in range(-support, support+1):
            data[i] += data[i+j] * (1/support*2)
    t1 = time()
    print('convolution took %f s' % (t1-t0))
    

def bench_str():
    """ From http://brythonista.wordpress.com/2015/03/28
    """
    print('String benchmarks:')
    
    t0 = time()
    for i in range(1000000):
        a = 1
    print("  assignment.py", time()-t0)
    
    t0 = time()
    a = 0
    for i in range(1000000):
        a += 1
    print("  augm_assign.py", time()-t0)
    
    t0 = time()
    for i in range(1000000):
        a = 1.0
    print("  assignment_float.py", time()-t0)
    
    t0 = time()
    for i in range(1000000):
        a = {0: 0}
    print("  build_dict.py", time()-t0)
    
    t0 = time()
    a = {0: 0}
    
    for i in range(1000000):
        a[0] = i
    
    assert a[0]==999999
    print("  set_dict_item.py", time()-t0)
    
    t0 = time()
    for i in range(1000000):
        a = [1, 2, 3]
    print("  build_list.py", time()-t0)
    
    t0 = time()
    a = [0]
    
    for i in range(1000000):
        a[0] = i
    print("  set_list_item.py", time()-t0)
    
    t0 = time()
    a, b, c = 1, 2, 3
    for i in range(1000000):
        a + b + c
    print("  add_integers.py", time()-t0)
    
    t0 = time()
    a, b, c = 'a', 'b', 'c'
    for i in range(1000000):
        a + b + c
    print("  add_strings.py", time()-t0)
    
    t0 = time()
    for _i in range(100000):
        str(_i)
    print("  str_of_int.py", time()-t0)
    
    t0 = time()
    for i in range(1000000):
        def f():
            pass
    print("  create_function.py", time()-t0)
    
    t0 = time()
    def g(x):
        return x
    for i in range(1000000):
        g(i)
    print("  function_call.py", time()-t0)


class Benchmarker(app.Model):
    
    def run_js_benchmark(self):
        self.call_js('_benchmark()')
    
    def benchmark(self):
        print('\n==== Python %s %s =====\n' % (platform.python_implementation(), 
                                               platform.python_version()))
        pystone_main()
        convolve()
        bench_str()
        
        # Trigger benchmark in JS
        self.run_js_benchmark()
    
    class JS:
        
        def _benchmark(self):
            print()
            print('==== PyScript on %s =====' % BACKEND)
            print()
            pystone_main()
            convolve()
            bench_str()


b = app.launch(Benchmarker, BACKEND)
b.benchmark()
app.run()
