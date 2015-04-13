"""



Supported basics:

* numbers, strings
* Binary, unary and boolean operations
* power and integer division operations
* multiple variable assignment
* lists, tuples, dicts (respectively become JS arrays, arrays, objects)
* comparisons (== -> ==, is -> ===)
* if-statements and single-line if-expression
* while-loops
* for-loops using range()
* while and for loops support continue, break, and else-clauses
* function calls can have *args (but no keywords or **kwargs)
* function defs can have default arguments, *args (but no kwargs)
* Slicing (though not with step)
* Use of ``self`` is translated to ``this``

Supported Python conveniences:

* print() becomes console.log (no ``end`` and ``sep`` though)
* len(x) becomes x.length 

Not currently supported:

* The ``in`` operator 
* tuple packing/unpacking
* function defs cannot have ``**kwargs``
* cannot call a function with ``*args``
* Exceptions, assertions, delete

Probably never suppored:

* Slicing with steps
* set (JS has no set)
* Most Python buildins
* importing


User guide stuff:
    
    # "self" is replaced with "this"
    self.foo
    
    # Printing just works
    print('some test')
    print(a, b, c, sep='-')
    
    ## For loops
    
    # You can use range for explicit for-loops. You can also iterate
    # directly over values in an array, string or dict. In case of
    # dicts, we using ``.keys()``, ``.values()`` and
    # ``items()`` should provide slightly increased performance.
    
    # Using range() yields true for-loops
    for i in range(10):
        print(i)
    for i in range(100, 10, -2):
        print(i)
    
    # One way to iterate over an array
    for i in range(len(arr)):
        print(arr[i])
    
    # But this is equally valid (and fast)
    for element in arr:
        print(element)
    
    # Similarly, iteration over strings
    for char in "foo bar":
        print(c)
    
    # Plain iteration over a dict costs a small overhead
    for key in d:
        print(key)
        
    # Which is why we recommend the following syntax
    for key in d.keys():
        print(key)
    for val in d.values():
        print(val)
    for key, val in d.items():
        print(key, val, sep=': ')
    
    # Some methods get replaced
    a.append(x)
"""

from .baseparser import BaseParser, JSError
from .pythonicparser import PythonicParser
from .functions import JSFunction, js, py2js, evaljs, evalpy

# Some names that parties may want to import to fool pyflakes
window = 'JS-WINDOW'
undefined = 'JS-UNDEFINED'
