"""
The pyscript module provides functionality for converting Python code
to JavaScript.

PyScript is just JavaScript
---------------------------

In contrast to projects like Skulpt or PyJS, the purpose is *not* to
enable full Python support in the browser. PyScript allows you to write
JavaScript using Python syntax, but (simular to CoffeeScript), it's
just JavaScript.

This means that depending on what you want to achieve, you still need
to know a thing or two about how JavaScript works.

Code produced by PyScript works standalone; you don't need another JS
library to run it.

PyScript is just Python
-----------------------

Other than e.g. RapydScript, PyScript is valid Python. This allows
creating modules that are a mix of real Python and PyScript. You could even
write code that runs correctly both as Python and PyScript. Raw JS can
be included by defining a function with only a docstring.

PyScript itself (the compiler) is written in Python. Perhaps PyScript can
at some point compile itself, so that it becomes possible to define
PyScript in HTML.

Pythonic
--------

Because PyScript is just JavaScript, not all Python code can be
converted. Further, lists are really just JavaScript arrays, and dicts
are JavaScript objects. PyScript allows writing Pythonic code by
converting a subset of functions and methods. E.g. you can use
``print()``, ``len()``, ``L.append()``, ``L.remove()``,
and this functionality will probably be extended over time. See the
list below for what is currently supported.

Purpose
-------

The primary purpose is to allow frameworks that consist of both Python
and JavaScript to be developed easier, using one language. In
particular, it allows the implementation of the Python and JS part of
widgets in ``flexx.ui`` to be in the same class definition.

It could probably also be used to develop standalone JavaScript
libraries. Although ``import`` is currently not yet supported. We'll
have to see how that works.


Support
-------

Supported basics:

* numbers, strings, lists, dicts (the latter become JS arrays and objects)
* operations: binary, unary, boolean, power, integer division
* comparisons (``==`` -> ``==``, ``is`` -> ``===``)
* tuple packing and unpacking
* ``isinstance()`` without the crappyness of ``typeof``
* slicing (though not with step)
* if-statements and single-line if-expression
* while-loops and for-loops supporting continue, break, and else-clauses
* for-loops using `range()`
* for-loop over arrays
* for-loop over dict/object using ``.keys()``, ``.values()`` and ``.items()``
* function calls can have ``*args``
* function defs can have default arguments and ``*args``
* lambda expressions
* classes, with (single) inheritance
* the use of super()
* Creation of "modules"

Supported Python conveniences:

* use of ``self`` is translated to ``this``
* ``print()`` becomes ``console.log()`` (also support ``sep`` and ``end``)
* ``len(x)`` becomes ``x.length``
* min(), max() and sum()

Not currently supported:

* the ``in`` operator
* raising and catching exceptions
* assertions
* delete
* List comprehensions
* importing
* most Python builtin functions

Probably never suppored (because it's hard to map to JS):

* slicing with steps
* the set class (JS has no set)
* support for ``**kwargs``
* The ``with`` statement
* Generators (i.e. ``yield``)

"""

# Note: the user guide is in the docs


from .baseparser import BaseParser, JSError  # noqa
from .pythonicparser import PythonicParser  # noqa
from .functions import JSCode, js, py2js, evaljs, evalpy  # noqa

# Some names that parties may want to import to fool pyflakes
window = 'JS-WINDOW'  # noqa
undefined = 'JS-UNDEFINED'  # noqa
document = 'JS-DOCUMENT'  # noqa
Object = 'JS-OBJECT'  # noqa
