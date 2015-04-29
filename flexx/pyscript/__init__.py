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
* operations: binary, unary, boolean, power, integer division, ``in`` operator
* comparisons (``==`` -> ``==``, ``is`` -> ``===``)
* tuple packing and unpacking
* basic string formatting
* slicing with start end end (though not with step)
* if-statements and single-line if-expressions
* while-loops and for-loops supporting continue, break, and else-clauses
* for-loops using ``range()``
* for-loop over arrays
* for-loop over dict/object using ``.keys()``, ``.values()`` and ``.items()``
* function calls can have ``*args``
* function defs can have default arguments and ``*args``
* lambda expressions
* classes, with (single) inheritance, and the use of ``super()``
* Creation of "modules"
* raising and catching exceptions
* assertions

Supported Python conveniences:

* use of ``self`` is translated to ``this``
* ``print()`` becomes ``console.log()`` (also supports ``sep`` and ``end``)
* ``isinstance()`` Just Works (for primitive types as well as
  user-defined classes)
* ``len(x)`` becomes ``x.length``
* ``min()``, ``max()`` and ``sum()``

Not currently supported:

* list comprehensions (will certainly be supported at some point)
* more Python builtin functions (e.g. ``issubclass``, ``zip``, ``sorted``, ...)
* importing (as a means for binding similar to require.js)
* the ``set`` class (JS has no set, but we could create one?)
* slicing with steps (JS does not support this)
* support for ``**kwargs`` (maps badly to JS call mechanism)
* The ``with`` statement (no equivalent in JS)
* Generators (i.e. ``yield``)?

Caveats:

* PyScript does no attempt to fix the weird truthfulness rules of
  JavaScript. Empty arrays and empty dicts evaluate to True. Use
  ``len(arr)`` and ``len(d.keys())`` to work around this.
* JavasScript has a concept of `null` (i.e. `None`), as well as
  `undefined`. Sometimes you may want to use ``if x is None or x is
  undefined: ...``.

"""

# NOTE: The code for the parser is quite long, especially if you want
# to document it well. Therefore it is split in multiple modules, which
# are simply numbered 0, 1, 2, etc. Here in the __init__, we define
# which parser is *the* parser. This gives us the freedom to split the
# parser in smaller piecers if we want.
#
# In the docstring of every parser module we maintain a brief user-guide
# demonstrating the features defined in that module. In the docs these
# docstrings are combined into one complete guide.

from .parser0 import JSError  # noqa
from .parser3 import Parser2
from .parser3 import Parser3


class BasicParser(Parser2):
    """ A parser without the Pythonic features for converting builtin
    functions and common methods.
    """
    pass


class Parser(Parser3):
    """ Parser to convert Python to JavaScript.
    
    Instantiate this class with the Python code. Retrieve the JS code
    using the dump() method.
    
    In a subclass, you can implement methods called "function_x" or
    "method_x", which will then be called during parsing when a
    function/method with name "x" is encountered. Several methods and
    functions are already implemented in this way.
    
    While working on ast parsing, this resource is very helpful:
    https://greentreesnakes.readthedocs.org
    
    parameters:
        code (str): the Python code to parse.
        module (str, optional): if given, put the resulting JS in a
            module with the given name.
    """
    pass


from .functions import JSCode, js, py2js, evaljs, evalpy  # noqa


# Some names that users may want to import to fool pyflakes
window = 'JS-WINDOW'  # noqa
undefined = 'JS-UNDEFINED'  # noqa
document = 'JS-DOCUMENT'  # noqa
Object = 'JS-OBJECT'  # noqa
