"""
This example demonstrates how Python code can be run in NodeJS (or
Firefox), which is for many things faster than CPython. We run the exact
same code to find the n-th prime on both Python and JS and measure the
performance.
"""

from flexx import app


def _find_prime(self, n):
    """ The code that is executed on both Python and JS (via PyScript)
    """
    primes = []
    
    def isprime(x):
        if x <= 1:
            return False
        elif x == 2:
            return True
        for i in range(2, x//2+1):
            if x % i == 0:
                return False
        return True
    
    import time  # import here, so PyScript picks is up
    t0 = time.perf_counter()
    i = 0
    while len(primes) < n:
        i += 1
        if isprime(i):
            primes.append(i)
    t1 = time.perf_counter()
    print(i, 'found in ', t1-t0, 'seconds')


class PrimeFinder(app.Model):
    
    _find_prime = _find_prime
    
    def find_prime_py(self, n):
        self._find_prime(n)
    
    class JS:
        _find_prime = _find_prime
        
    def find_prime_js(self, n):
        self.call_js('_find_prime(%i)' % n)


if __name__ == '__main__':
    
    # Create app instance
    finder = app.launch(PrimeFinder, 'nodejs')  # can also use Firefox or Chrome
    
    finder.find_prime_py(2000)  # 0.7 s
    finder.find_prime_js(2000)  # 0.2 s
    
    app.run()
