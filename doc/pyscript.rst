---------------
PyScript module
---------------

.. automodule:: flexx.pyscript


Pyscript API
------------


The PyScript module has a few dummy constants that can be imported and
used in your code to let e.g. pyflakes know that the variable exists.

.. data:: window
.. data:: undefined
    

----

.. autofunction:: flexx.pyscript.py2js

.. autofunction:: flexx.pyscript.js

.. autofunction:: flexx.pyscript.evaljs

.. autofunction:: flexx.pyscript.evalpy

----

Most users probably want to use the above functions, but you can also
get closer to the metal by using and/or extending the parser classes.

.. autoclass:: flexx.pyscript.BaseParser

.. autoclass:: flexx.pyscript.PythonicParser

----


Quick user guide
----------------

.. pyscript_example::
    
    ## Basics
    
    # Simple operations
    3 + 4 -1
    3 * 7 / 9
    5**2
    7 // 2
    
    # Basic types
    [True, False, None]
    
    # Lists and dicts
    foo = [1,2,3]
    bar = {'a': 1, b: 2}
    
    
    ## Arrays
    
    foo = [1,2,3,4,5]
    foo[2:]
    foo[2:-2]
    
    
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
    
    
    ## Instance testing using isinstance
    
    # Basic types
    isinstance(3, float)  # in JS there are no ints
    isinstance('', str)
    isinstance([], list)
    isinstance({}, dict)
    isinstance(foo, types.FunctionType)
    
    # Can also use JS strings
    isinstance(3, 'number')
    isinstance('', 'string')
    isinstance([], 'array')
    isinstance({}, 'object')
    isinstance(foo, 'function')
    
    # You can use it on your own types too ...
    isinstance(x, MyClass)
    isinstance(x, 'MyClass')  # equivalent
    isinstance(x, 'Object')  # also yields true (subclass of Object)
    
    
    ## If statements
    
    if val > 7:
        result = 42
    elif val > 1:
        result = 1
    else:
        result = 0
    
    # One-line if
    result = 42 if truth else 0
    
    
    ## While loop
    
    # While loops map well to JS
    val = 0
    while val < 10:
        val += 1
    
    
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
    
    
    ## Functions
    
    def display(val):
        print(val)
    
    # Support for *args
    def foo(x, *values):
        bar(x+1, *values)
    
    # To write raw JS, define a function with only a docstring
    def bar(a, b):
        """
        var c = 4;
        return a + b + c;
        """
