"""
The pyscript module provides functionality for converting Python code
to JavaScript. In contrast to projects like Skulpt or PyJS, the purpose
is *not* to enable full Python support in the browser. PyScript allows
you to write JavaScript using Python syntax, but (simular to
CoffeeScript), it's just JavaScript.

Code produced by PyScript works standalone; you don't need another JS
library in order to run it.


Purpose
-------

The purpose of PyScript is to allow developers to write JavaScript in
Python. The main motivation was to allow mixing Python and JS in a
single file. Depending on what you want to achieve, you still need
to know a thing or two about how JavaScript works.


Pythonic
--------
Because PyScript is just JavaScript, not all Python code can be
converted. Further, lists are really just JavaScript arrays, and dicts
are JavaScript objects. PyScript allows writing Pythonic code by
converting a subset of functions and methods. E.g. you can use
``print()``, ``len()`` and ``max()``, ``L.append()``, ``L.remove()``,
and this functionality will probably be extended over time. See the
lists below for what is currently supported.


Support
-------

Supported basics:

* numbers, strings
* binary, unary and boolean operations
* power and integer division operations
* multiple variable assignment
* lists, tuples, dicts (respectively become JS arrays, arrays, objects)
* comparisons (== -> ==, is -> ===)
* if-statements and single-line if-expression
* while-loops
* for-loops using range()
* for-loop over arrays
* for-loop over dict/object ``.keys()``, ``.values()`` and ``.items()``
* while and for loops support continue, break, and else-clauses
* function calls can have ``*args`` (but no keywords or ``**kwargs``)
* function defs can have default arguments, ``*args`` (but not ``**kwargs``)
* Slicing (though not with step)
* Use of ``self`` is translated to ``this``

Supported Python conveniences:

* print() becomes console.log (no ``end`` and ``sep`` though)
* len(x) becomes x.length 

Not currently supported:

* the ``in`` operator 
* tuple packing/unpacking
* exceptions, assertions, delete
* importing
* most Python builtin functions

Probably never suppored (because it's hard to map to JS):

* slicing with steps
* the set class (JS has no set)
* support for ``**kwargs``


Quick user guide
----------------

.. pyscript_example::
    
    ## Basics
    
    # Creating lists and dicts
    foo = [1,2,3]
    bar = {'a': 1, b: 2}
    
    # If statements
    foo = bar if True else None


    ## For loops

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
    
    # Which is why we recommend using keys(), values(), or items()
    for key in d.keys():
        print(key)
    
    for val in d.values():
        print(val)
    
    for key, val in d.items():
        print(key, val, sep=': ')


    ## Pythonic sugar

    # "self" is replaced with "this"
    self.foo
    
    # Printing just works
    print('some test')
    print(a, b, c, sep='-')
    
    # Call a.append() if it exists, otherwise a.push()
    a.append(x)
    
    # Similar for remove()
    a.remove(x)

"""

from .baseparser import BaseParser, JSError
from .pythonicparser import PythonicParser
from .functions import JSFunction, js, py2js, evaljs, evalpy

# Some names that parties may want to import to fool pyflakes
window = 'JS-WINDOW'
undefined = 'JS-UNDEFINED'
