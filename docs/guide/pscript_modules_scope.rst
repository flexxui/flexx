---------------------------
PScript, modules, and scope
---------------------------

In this guide, we've already seen several examples where we write Python
code that runs in JavaScript. This is done by *transpiling* the Python code
to JavaScript using a tool called `PScript <http://pscript.readthedocs.io>`_,
which is a spin-off of the Flexx project.

The compilation of Python code to JavaScript happens automatically, at the
moment that a ``JsComponent`` gets defined (i.e. imported). Flexx is aware
of the classes that the browsers needs to know about and sends the corresponding
code when needed. Therefore it's possible to dynamically import or
create new classes and use them.


PScript is almost Python
------------------------

PScript is syntactically compatible with Python, so you can write it inside
any Python module. PScript also feels a lot like Python, and it will probably
get better in the future, but sometimes the JavaScript shines through.
Thinks to watch out for:

* Accessing a nonexisting attribute will return ``undefined`` instead of
  raising an AttributeError.
* Keys in a dictionary are implicitly converted to strings.
* Classes must start with a captial letter, functions must not. This
  is simply good practice in Python, but PScript needs it to tell
  classes apart from functions.
* A function can accept keyword arguments if it has a `**kwargs` parameter or
  named arguments after `*args`. Passing keywords to a function that does not
  handle keyword arguments might result in confusing errors.

Things you can do, which you cannot do in Python:

* Access elements in a dict as attributes (e.g. `d.foo` instead of `d["foo"]`).
* Implicitly convert values to sting by adding them to a string.
* Divide by zero (results in `inf`).

Read more on http://pscript.readthedocs.io/.


Scope
-----

In Flexx, it's easy to possible to define PyComponents and JsComponents
in the same module. For the purpose of clarity, it's probably good to
avoid this for larger applications.

Inside the methods of a JsComponent you can make use of plain Python
functions and classes that are defined in the same module, provided
that these (and their dependencies) can be transpiled by PScript.
Similarly you can make use of objects defined or imported in the module.
These can be integers, lists, dicts (and any combination thereof), as
long as it can be JSON-serialized.

For every Python module that defines code that is used in JS, a corresponding
JS module is created. Flexx detects what variable names are used in the JS
code, but not declared in it, and tries to find the corresponding object in
the module. You can even import functions/classes from other modules.

.. code-block:: py

    from flexx import flx

    from foo import func1

    def func2():
        ...

    info = {'x': 1, 'y': 2}

    class MyComponent(flx.JsComponent):

        @flx.reaction('some.event')
        def handler(self, *events):
            func1(info)
            func2()

In the code above, Flexx will include the definition of ``func2`` and
``info`` in the same module that defines ``MyComponent``, and include
``func1`` in the JS module ``foo``. If ``MyComponent`` would not use these
functions, neither definition would be included in the JavaScript module.

A useful feature is that the ``RawJS`` class from PScript can be used
in modules to define objects in JS:

.. code-block:: py

    from flexx import flx

    my_js_object = RawJS('window.something.get_some_object()')

    class MyComponent(flx.JsComponent):

        @flx.reaction('some.event')
        def handler(self, *events):
            my_js_object.bar()

One can also assign ``__pscript__ = True`` to a module to make Flexx
transpile a module as a whole. A downside is that (at the moment) such
modules cannot use import.


Next
----


Next up: :doc:`Handling assets and data <assets_data>`.
