PyScript API
============

.. autofunction:: flexx.pyscript.py2js

.. autofunction:: flexx.pyscript.evaljs

.. autofunction:: flexx.pyscript.evalpy

.. autofunction:: flexx.pyscript.script2js

.. autofunction:: flexx.pyscript.js_rename

.. autofunction:: flexx.pyscript.get_full_std_lib

.. autofunction:: flexx.pyscript.get_all_std_names

.. autofunction:: flexx.pyscript.create_js_module

----

Most users probably want to use the above functions, but you can also
get closer to the metal by using and/or extending the parser class.

.. autoclass:: flexx.pyscript.Parser

----

PyScript allows embedding raw JavaScript using the ``RawJS`` class.

.. autoclass:: flexx.pyscript.RawJS

----

The PyScript module has a few dummy constants that can be imported and
used in your code to let e.g. pyflakes know that the variable exists. E.g.
``from flexx.pyscript import undefined, window Infinity, NaN``.
Arbitrary dummy variables can be imported using
``from flexx.pyscript.stubs import JSON, foo, bar``.

Marking a variable as global is also a good approach to tell pyflakes that
the variable exists.
