"""
The pyscript module provides functionality for transpiling Python code
to JavaScript.

Goals
-----

There is an increase in Python projects that target web technology to
handle visualization and user interaction.
PyScript grew out of a desire to allow writing JavaScript callbacks in
Python, to allow user-defined interaction to be flexible, fast, and
stand-alone.

This resulted in the following two main goals: 

* To make writing JavaScript easier and less frustrating, by letting
  people write it with the Python syntax and buildins, and fixing some
  of JavaScripts quirks.
* To allow JavaScript snippets to be defined naturally inside a Python
  program.

Code produced by PyScript works standalone. Any (PyScript-compatible)
Python snippet can be converted to JS; you don't need another JS library
to run it.

PyScript can also be used to develop standalone JavaScript (AMD) modules.
Although ``import`` is currently not yet supported. We'll have to see
how that works out.


PyScript is just JavaScript
---------------------------

The purpose of projects like Skulpt or PyJS is to enable full Python
support in the browser. This approach will always be plagued by a
fundamental limitation: libraries that are not pure Python (like numpy)
will not work.

PyScript takes a more modest approach; it is a tool that allows one to
write JavaScript with a Python syntax. PyScript is just JavaScript.

This means that depending on what you want to achieve, you still need
to know a thing or two about how JavaScript works. Further, not all Python
code can be converted (e.g. ``**kwargs`` are not supported), and
lists and dicts are really just JavaScript arrays and objects, respectively.


Pythonic
--------

PyScript makes writing JS more "Pythonic". Apart from allowing Python syntax
for loops, classes, etc, all relevant Python buildins are supported,
and all methods of list, dict and str as well (WIP). E.g. you can use
``print()``, ``range()``, ``L.append()``, ``L.remove()``, etc.

Also, the empty list and dict evaluate to false (whereas in JS it's
true), and ``isinstance()`` just works (whereas JS' ``typeof`` is broken).


Caveats
-------

PyScript fixes some of JS's quirks, but it's still just JavaScript.
Here's a list of things to keep an eye out for. This list is likely
incomplete. We recommend familiarizing yourself with JavaScript if you
plan to make heavy use of PyScript.

* JavasScript has a concept of ``null`` (i.e. ``None``), as well as
  ``undefined``. Sometimes you may want to use ``if x is None or x is
  undefined: ...``.
* Accessing an attribute that does not exist will not raise an
  AttributeError but yield ``undefined``.
* When storing a method in a new variable and then calling it 
  (``foo = x.foo; foo()``), self/this is null.
* Cannot compare lists and dicts: ``[1, 2] == [1, 2]`` yields ``False``.
  (may fix this)
* Multiplying a string with a number will yield NaN (but the reverse
  is probably different). (may fix this)
* You cannot concatenate lists with the plus operator, use ``.extend()``
  instead. (may fix this)


PyScript is valid Python
------------------------

Other than e.g. RapydScript, PyScript is valid Python. This allows
creating modules that are a mix of real Python and PyScript. You can easily
write code that runs correctly both as Python and PyScript. Raw JS can
be included by defining a function with only a docstring.

PyScript itself (the compiler) is written in Python. Perhaps PyScript can
at some point compile itself, so that it becomes possible to define
PyScript inside HTML documents.


Support
-------

This is an overview of the language features that PyScript
supports. Also see the quick user guide.

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
* list comprehensions
* classes, with (single) inheritance, and the use of ``super()``
* raising and catching exceptions, assertions
* Creation of "modules"

Supported Python conveniences:

* use of ``self`` is translated to ``this``
* ``print()`` becomes ``console.log()`` (also supports ``sep`` and ``end``)
* ``isinstance()`` Just Works (for primitive types as well as
  user-defined classes)
* an empty list or dict evaluates to False as in Python.
* all Python buildin functions that make sense in JS are supported:
  isinstance, issubclass, callable, hasattr, getattr, setattr, delattr,
  print, len, max, min, chr, ord, dict, list, tuple, range, pow, sum,
  round, int, float, str, bool, abs, divmod, all, any, enumerate, zip,
  reversed, sorted, filter, map.
* some methods fo list, dict and str are supported. We plan to support
  (almost) all methods soon.
* the default return value of a function is ``None``/``null`` instead
  of ``undefined``.

Not currently supported:

* importing (maybe we'll add this as a means for binding similar to require.js)
* the ``set`` class (JS has no set, but we could create one?)
* slicing with steps (JS does not support this)
* support for ``**kwargs`` (maps badly to JS call mechanism)
* The ``with`` statement (no equivalent in JS)
* Generators, i.e. ``yield`` (not widely supported in JS)

"""

# NOTE: The code for the parser is quite long, especially if you want
# to document it well. Therefore it is split in multiple modules, which
# are simply numbered 0, 1, 2, etc. Here in the __init__, we define
# which parser is *the* parser. This gives us the freedom to split the
# parser in smaller pieces if we want.
#
# In the docstring of every parser module we maintain a brief user-guide
# demonstrating the features defined in that module. In the docs these
# docstrings are combined into one complete guide.

import sys

from .parser0 import Parser0, JSError  # noqa
from .parser1 import Parser1  # noqa
from .parser2 import Parser2  # noqa
from .parser3 import Parser3  # noqa

# Assert py3k
if sys.version_info < (3, 2):
    raise RuntimeError('flexx.pyscript needs Python 3.2 or higher')


class BasicParser(Parser2):
    """ A parser without the Pythonic features for converting builtin
    functions and common methods.
    """
    pass


class Parser(Parser3):
    # Re-use docs from Parser0
    Parser0.__doc__.split('Parameters:', 1)[1] + """
    Parser to convert Python to JavaScript.
    
    Instantiate this class with the Python code. Retrieve the JS code
    using the dump() method.
    
    In a subclass, you can implement methods called "function_x" or
    "method_x", which will then be called during parsing when a
    function/method with name "x" is encountered. Several methods and
    functions are already implemented in this way.
    
    While working on ast parsing, this resource is very helpful:
    https://greentreesnakes.readthedocs.org
    
    Parameters:
    
    """
    pass


from .functions import py2js, evaljs, evalpy, script2js, clean_code, js_rename  # noqa
