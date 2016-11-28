"""
The pyscript module provides functionality for transpiling Python code
to JavaScript.

Quick intro
-----------

This is a brief intro for using PyScript. For more details see the
sections below.

PyScript is a tool to write JavaScript using (a subset) of the Python
language. All relevant buildins, and the methods of list, dict and str
are supported. Not supported are set, slicing with steps,
``**kwargs``, ``with``, ``yield``. Imports are not supported. Other than that,
most Python code should work as expected, though if you pry hard enough the
JavaScript may shine through. As a rule of thumb, the code should behave
as expected when correct, but error reporting may not be very Pythonic.

The most important functions you need to know about are
:func:`py2js <flexx.pyscript.py2js>` and 
:func:`evalpy <flexx.pyscript.evalpy>`.
In principal you do not need knowledge of JavaScript to write PyScript
code.


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


PyScript is just JavaScript
---------------------------

The purpose of projects like Skulpt or PyJS is to enable full Python
support in the browser. This approach will always be plagued by a
fundamental limitation: libraries that are not pure Python (like numpy)
will not work.

PyScript takes a more modest approach; it is a tool that allows one to
write JavaScript with a Python syntax. PyScript is just JavaScript.

This means that depending on what you want to achieve, you may still need
to know a thing or two about how JavaScript works. Further, not all Python
code can be converted (e.g. ``**kwargs`` are not supported), and
lists and dicts are really just JavaScript arrays and objects, respectively.


Pythonic
--------

PyScript makes writing JS more "Pythonic". Apart from allowing Python syntax
for loops, classes, etc, all relevant Python buildins are supported,
as well as the methods of list, dict and str. E.g. you can use
``print()``, ``range()``, ``L.append()``, ``D.update()``, etc.

The empty list and dict evaluate to false (whereas in JS it's
true), and ``isinstance()`` just works (whereas JS' ``typeof`` is
broken). 

Deep comparisons are supported (e.g. for ``==`` and ``in``), so you can
actually compare two lists or dicts, or even a structure of nested
lists/dicts. Lists can be combined with the plus operator, and lists
and strings can be repeated with the multiply (star) operator. Class
methods are bound functions.

.. _pyscript-caveats:

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
* Magic functions on classes (e.g. for operator overloading) do not work.
* Calling an object that starts with a capital letter is assumed to be
  a class instantiation (using ``new``): PyScript classes *must* start
  with a capital letter, and any other callables must not.

PyScript is valid Python
------------------------

Other than e.g. RapydScript, PyScript is valid Python. This allows
creating modules that are a mix of real Python and PyScript. You can easily
write code that runs correctly both as Python and PyScript. Raw JS can
be included by defining a function with only a docstring.

PyScript itself (the compiler) is written in Python. Perhaps PyScript can
at some point compile itself, so that it becomes possible to define
PyScript inside HTML documents.

Performance
-----------

Because PyScript produces relatively bare JavaScript, it is pretty fast.
Faster than CPython, and significantly faster than Brython and friends.
Check out ``examples/app/benchmark.py``.

Nevertheless, the overhead to realize the more Pythonic behavior can
have a negative impact on performance in tight loops (in comparison to
writing the JS by hand). The recommended approach is to write
performance critical code in pure JavaScript if necessary. This can be
done by defining a function with only a docstring (containing the JS
code).

.. _pyscript-support:

Support
-------

This is an overview of the language features that PyScript
supports/lacks. 

Not currently supported:

* import (maybe we should translate an import to ``require()``?)
* the ``set`` class (JS has no set, but we could create one?)
* slicing with steps (JS does not support this)
* support for ``**kwargs`` (maps badly to JS call mechanism)
* The ``with`` statement (no equivalent in JS)
* Generators, i.e. ``yield`` (not widely supported in JS)

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
* creation of "modules"
* globals / nonlocal

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
* all methods of list, dict and str are supported (except a few string
  methods: encode format format_map isdecimal isdigit isprintable maketrans)
* the default return value of a function is ``None``/``null`` instead
  of ``undefined``.
* list concatenation using the plus operator, and list/str repeating
  using the star operator.
* deep comparisons.
* class methods are bound functions (i.e. ``this`` is fixed to the
  instance).
* functions that are defined in another function (a.k.a closures) that do not
  have self/this as a first argument, are bound the the same instance as the
  function in which it is defined.


Other functionality
-------------------

The PyScript package provides a few other "utilities" to deal with JS code,
such as renaming function/class definitions, and creating JS modules
(AMD, UMD, etc.).

"""

import logging
logger = logging.getLogger(__name__)
del logging

# NOTE: The code for the parser is quite long, especially if you want
# to document it well. Therefore it is split in multiple modules, which
# are simply numbered 0, 1, 2, etc. Here in the __init__, we define
# which parser is *the* parser. This gives us the freedom to split the
# parser in smaller pieces if we want.
#
# In the docstring of every parser module we maintain a brief user-guide
# demonstrating the features defined in that module. In the docs these
# docstrings are combined into one complete guide.

# flake8: noqa

from .parser0 import Parser0, JSError
from .parser1 import Parser1
from .parser2 import Parser2
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
    
    Parameters:
        code (str): the Python source code.
        pysource (tuple): the filename and line number that contain the source.
        indent (int): the base indentation level (default 0). One
            indentation level means 4 spaces.
        docstrings (bool): whether docstrings are included in JS
            (default True).
        inline_stdlib (bool): whether the used stdlib functions are inlined
            (default True). Set to False if the stdlib is already loaded.
    """
    pass


from .functions import py2js, evaljs, evalpy, JSString
from .functions import script2js, js_rename, create_js_module
from .stdlib import get_full_std_lib, get_all_std_names
from .stubs import RawJS, JSConstant, window, undefined

# Create stubs that mean something
Infinity = float('inf')
NaN = float('nan')

def this_is_js():
    """ Function available in both JS and Py that returns whether the code is running
    on Python or JavaScript.
    """
    return False
