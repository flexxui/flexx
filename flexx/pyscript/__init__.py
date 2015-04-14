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
list below for what is currently supported.


Support
-------

Supported basics:

* numbers, strings, lists, dicts (the latter become JS arrays and objects)
* operations: binary, unary, boolean, power, integer division
* comparisons (``==`` -> ``==``, ``is`` -> ``===``)
* slicing (though not with step)
* if-statements and single-line if-expression
* while-loops and for-loops supporting continue, break, and else-clauses
* for-loops using `range()`
* for-loop over arrays
* for-loop over dict/object using ``.keys()``, ``.values()`` and ``.items()``
* function calls can have ``*args``
* function defs can have default arguments and ``*args``

Supported Python conveniences:

* use of ``self`` is translated to ``this``
* ``print()`` becomes ``console.log()`` (also support ``sep`` and ``end``)
* ``len(x)`` becomes ``x.length``

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

"""

# Note: the user guide is in the docs


from .baseparser import BaseParser, JSError
from .pythonicparser import PythonicParser
from .functions import JSFunction, js, py2js, evaljs, evalpy

# Some names that parties may want to import to fool pyflakes
window = 'JS-WINDOW'
undefined = 'JS-UNDEFINED'
