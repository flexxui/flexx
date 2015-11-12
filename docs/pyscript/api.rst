PyScript API
============

.. autofunction:: flexx.pyscript.py2js

.. autofunction:: flexx.pyscript.evaljs

.. autofunction:: flexx.pyscript.evalpy

.. autofunction:: flexx.pyscript.script2js

.. autofunction:: flexx.pyscript.js_rename

.. autofunction:: flexx.pyscript.get_full_std_lib

----

Most users probably want to use the above functions, but you can also
get closer to the metal by using and/or extending the parser class.

.. autoclass:: flexx.pyscript.Parser

----

The PyScript module has a few dummy constants that can be imported and
used in your code to let e.g. pyflakes know that the variable exists. E.g.
``from flexx.pyscript.stubs import undefined, window``.

.. data:: undefined
.. data:: window
.. data:: root
.. data:: document
.. data:: console
.. data:: module
.. data:: typeof
.. data:: require
.. data:: Object
.. data:: Math
.. data:: RegExp
.. data:: Infinity
.. data:: NaN
