"""
Sample Python code with syntax that's only available in Python 3.
"""


a, *b = 1, 2, 3

# Python > 3.3: does not work on pypy
# def yield_from_function(x):
#     yield from range(x, 0, -1)
#     yield from range(x)

# keyword only arguments
def spam(a, b, *arg, c, d): pass
def spam(a, b, *, c, d): pass
def spam(a=1, b=1, *, c=1, d=1): pass
def spam(a, b=1, *, c, d=1): pass

lambda a, b, *, c, d: a+b+c+d
lambda a=1, b=1, *, c=1, d=1: a+b+c+d


class Spam(*bases): pass
class Spam(A, *bases): pass

class Foo(base1, base2, metaclass=mymeta): pass
class Foo(base1, base2, metaclass=mymeta, foo=True): pass
class Foo(base1, base2, metaclass=mymeta, **foo): pass


def spam(x,y,z):
    def eggs():
        nonlocal x, y
        foo()
        nonlocal z

# Function annotations
def foo(a:3, b:'bla'=2, c:(int, float)=3) -> (some + thing):
    pass

def foo(*args:'one star', **kwargs:'two stars') -> 'return thingy':
    pass
