Flexx
=====

[![Build Status](https://travis-ci.org/zoofIO/flexx.svg)](https://travis-ci.org/zoofIO/flexx)
[![Documentation Status](https://readthedocs.org/projects/flexx/badge/?version=latest)](https://flexx.readthedocs.org)

Introduction
------------

Flexx is a pure Python toolkit for creating graphical user interfaces
(GUI's), that uses web technology for its rendering. Apps are written
purely in Python; Flexx' transpiler generates the necessary JavaScript
on the fly.

You can use Flexx to create (cross platform) desktop applications, web
applications, and (if designed well) export an app to a standalone HTML
document. It also works in the Jupyter notebook.

The docs are on [Readthedocs](http://flexx.readthedocs.org)
the code is on [Github](http://github.com/zoofio/flexx)
Flexx is currently in alpha status; any part of the public API may
change without notice. Feedback is welcome.

Flexx has a modular design, consisting of a few subpackages, which can
also be used by themselves:

* [flexx.ui](http://flexx.readthedocs.io/en/stable/ui/)
  - the widgets
* [flexx.app](http://flexx.readthedocs.io/en/stable/app/)
  - the event loop and server
* [flexx.event](http://flexx.readthedocs.io/en/stable/event/)
  - properties and events
* [flexx.pyscript](http://flexx.readthedocs.io/en/stable/pyscript/)
  - Python to JavaScript transpiler
* [flexx.webruntime](http://flexx.readthedocs.io/en/stable/webruntime/)
  - to launch a runtime
* [flexx.util](http://flexx.readthedocs.io/en/stable/util/)
  - utilities


Example
-------

Click the image below for an interactive example:
[![demo](https://dl.dropboxusercontent.com/u/1463853/images/flexx_demo_300.png)](http://flexx.readthedocs.io/en/latest/ui/examples/splines_src.html)

There is an Amazon instance running some demos on http://52.21.93.28:8000/ 
(it might not always be on).


Motivation
----------

The primary motivation for Flexx is the undeniable fact that the web
(i.e. browser technology) has become an increasingly popular method for
delivering applications to users, also for (interactive) scientific
content.

The purpose of Flexx is to provide a single application framework to
create desktop applications, web apps, and (hopefully soon) mobile apps.
By making use of browser technology, the library itself can be
relatively small and pure Python, making it widely available and easy
to use.


Installation
------------

Flexx requires Python 2.7 or Python 3.2+ and also works on pypy. Further,
it needs the [tornado](http://www.tornadoweb.org) library (pure Python).
For running desktop apps, it is recommended to have Firefox installed.

To install use any of:
* ``conda install flexx -c conda-forge``
* ``pip install flexx``
* Clone the repo and add it to your PYTHONPATH, or ``python setup.py install``.


License
-------

FLexx makes use of the liberal 2-clause BSD license. See LICENSE for details.
