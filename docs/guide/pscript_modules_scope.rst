---------------------------
PScript, modules, and scope
---------------------------

Inside the methods of a component you can make use of functions, classes, and
values that are defined in the same module. Even in a ``JsComponent``
(as long as they can be transpiled or serialized).

For every Python module that defines code that is used in JS, a corresponding
JS module is created. Flexx detects what variable names are used in the JS
code, but not declared in it, and tries to find the corresponding object in
the module. You can even import functions/classes from other modules.

.. code-block:: py

    from flexx import app

    from foo import func1

    def func2():
        ...

    info = {'x': 1, 'y': 2}

    class MyComponent(app.JsComponent):

        @event.reaction('some.event')
        def handler(self, *events):
            func1(info)
            func2()

In the code above, Flexx will include the definition of ``func2`` and
``info`` in the same module that defines ``MyComponent``, and include
``func1`` in the JS module ``foo``. If ``MyComponent`` would not
use these functions, neither definition would be included in the JavaScript.

A useful feature is that the ``RawJS`` class from PScript can be used
in modules to define objects in JS:

.. code-block:: py

    from flexx import app

    my_js_module = RawJS('require("myjsmodule.js")')

    class MyComponent(app.JsComponent):

        @event.reaction('some.event')
        def handler(self, *events):
            my_js_module.foo.bar()

One can also assign ``__pscript__ = True`` to a module to make Flexx
transpile a module as a whole. A downside is that (at the moment) such
modules cannot use import.