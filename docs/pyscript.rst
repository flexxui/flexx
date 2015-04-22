-------------------
The pyscript module
-------------------

Introduction
============

.. automodule:: flexx.pyscript


Pyscript API
============


The PyScript module has a few dummy constants that can be imported and
used in your code to let e.g. pyflakes know that the variable exists.

.. data:: undefined
.. data:: window
.. data:: document
.. data:: Object


----

.. autofunction:: flexx.pyscript.py2js

.. autofunction:: flexx.pyscript.js

.. autofunction:: flexx.pyscript.evaljs

.. autofunction:: flexx.pyscript.evalpy

----

Most users probably want to use the above functions, but you can also
get closer to the metal by using and/or extending the parser classes.

.. autoclass:: flexx.pyscript.Parser

.. autoclass:: flexx.pyscript.BasicParser

----


Quick user guide
================

.. automodule:: flexx.pyscript.parser1

.. automodule:: flexx.pyscript.parser2

.. automodule:: flexx.pyscript.parser3
