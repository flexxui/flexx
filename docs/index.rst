.. Flexx documentation master file, created by
   sphinx-quickstart on Fri Apr 10 15:35:18 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flexx's documentation!
=================================

Flexx is a Python tookit for designing user interfaces (UI's), that
uses web technology for its rendering. You can use Flexx to create
desktop applications as well as web applications.

Flexx is pure Python, and has no dependencies other than the browser
that's already installed on the system.

Current status
--------------

Flexx is in development and is in alpha status. Any part of the public
API may change without notice. Status of subpackages:
   
* The ``flexx.pyscript`` module is in a good state and has 100% test
  coverage. Needs methods for list/dict/str, but is otherwise very
  complete.
* The ``flexx.react`` module is in a good state, with good test
  coverage, but needs some work for functionals. 
* The ``flexx.webruntime`` module works well, but needs
  tests and should support more runtimes. 
* The ``flexx.app`` module is in a flux.
* The ``flexx.ui`` module is in a flux.


Links
-----

   * Flexx website: http://flexx.readthedocs.org
   * Flexx code: http://github.com/zoofio/flexx


Contents
--------

.. toctree::
   :maxdepth: 2
   
   start
   
   ui/index
   pyscript/index
   react/index
   webruntime
   util
   
   releasenotes


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
