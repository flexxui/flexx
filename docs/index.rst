.. Flexx documentation master file, created by
   sphinx-quickstart on Fri Apr 10 15:35:18 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flexx's documentation!
=================================

Flexx is a pure Python toolkit for creating graphical user interfaces
(GUI's), that uses web technology for its rendering. You can use Flexx
to create desktop applications, web applications, and (if designed well)
export an app to a standalone HTML document. It also works in the
Jupyter notebook.

Being pure Python and cross platform, it should work anywhere where
there's Python and a browser.

Flexx has a modular design, consisting of a few subpackages, which can
also be used by themselves:

* :doc:`ui <ui/index>` - the widgets
* :doc:`app <app/index>` - the event loop and server
* :doc:`event <event/index>` - properties and events
* :doc:`pyscript <pyscript/index>` - Python to JavaScript transpiler
* :doc:`webruntime <webruntime/index>` - to launch a runtime


Status
------

* Alpha status, any part of the public API may change. Looking for feedback though!
* Currently, only Firefox and Chrome are supported.
* Flexx is CPython 3.x only for now. Support for Pypy very likely. Support
  for 2.x maybe.


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
   app/index
   event/index
   pyscript/index
   webruntime/index
   util
   
   cli
   releasenotes


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
