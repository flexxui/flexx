.. Flexx documentation master file, created by
   sphinx-quickstart on Fri Apr 10 15:35:18 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flexx's documentation!
=================================

Flexx is a pure Python toolkit for creating graphical user interfaces
(GUI's), that uses web technology for its rendering. Apps are written
purely in Python; Flexx' transpiler generates the necessary JavaScript
on the fly.

You can use Flexx to create (cross platform) desktop applications, web
applications, and (if designed well) export an app to a standalone HTML
document. It also works in the Jupyter notebook.

The Flexx docs are on `readthedocs <http://flexx.readthedocs.org>`_,
the code is on `Github <http://github.com/zoofio/flexx>`_.
Flexx is currently in alpha status; any part of the public API may
change without notice. Feedback is welcome. We're definitely
converging to a more stable API though ...

Flexx has a modular design, consisting of a few subpackages, which can
also be used by themselves. See the table of contents below. For building
apps these three modules are most relevant:

* :doc:`flexx.ui <ui/index>` - the widgets
* :doc:`flexx.app <app/index>` - the event loop and server
* :doc:`flexx.event <event/index>` - properties and events


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
   util/index
   
   cli_and_config
   releasenotes


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
