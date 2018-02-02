Flexx
=====

[![Join the chat at https://gitter.im/flexxui/flexx](https://badges.gitter.im/flexxui/flexx.svg)](https://gitter.im/flexxui/flexx?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/flexxui/flexx.svg)](https://travis-ci.org/flexxui/flexx)
[![Documentation Status](https://readthedocs.org/projects/flexx/badge/?version=latest)](https://flexx.readthedocs.org)

<i>Notice: Flexx is being [refactored](https://github.com/zoofIO/flexx/pull/408) right now, which should be ready before/in Januari 2018. These changes are driven by feedback from building real world Flexx-based apps over the past year and a half, and will improve Flexx on many fronts (e.g. make it scale better). It does mean that the API will change in a few ways though!</i>

Introduction
------------

Flexx is a pure Python toolkit for creating graphical user interfaces
(GUI's), that uses web technology for its rendering. Apps are written
purely in Python; Flexx' transpiler generates the necessary JavaScript
on the fly.

You can use Flexx to create (cross platform) desktop applications, web
applications, and (if designed well) export an app to a standalone HTML
document. It also works in the Jupyter notebook.

The docs are on [Readthedocs](http://flexx.readthedocs.io).
the code is on [Github](http://github.com/flexxui/flexx).
Flexx is currently in alpha status; any part of the public API may
change without notice. Feedback is welcome.

Flexx has a modular design, consisting of a few subpackages, which can
also be used by themselves:

* [flexx.ui](http://flexx.readthedocs.io/en/stable/ui/) - the widgets
* [flexx.app](http://flexx.readthedocs.io/en/stable/app/) - the event loop and server
* [flexx.event](http://flexx.readthedocs.io/en/stable/event/) - properties and events
* [flexx.pyscript](http://flexx.readthedocs.io/en/stable/pyscript/) - Python to JavaScript transpiler
* [flexx.webruntime](http://flexx.readthedocs.io/en/stable/webruntime/) - to launch a runtime
* [flexx.util](http://flexx.readthedocs.io/en/stable/util/) - utilities


Status
------

Early 2017 we were close to a new release and moving to beta-status.
However, we found that in some real (bigger) applications written in Flexx,
we were hitting certain boundaries. We believe that these boundaries prevent
Flexx from being usable at a large scale.

We've since looked at what does boundaries are and how Flexx would need to
change to be able to remove or move beyond these boundaries. This has culminated
in a [plan](https://github.com/zoofIO/flexx/pull/367) to refactor Flexx, and the
refactoring is currently [being done](https://github.com/zoofIO/flexx/pull/408).

These changes are quite substantial. E.g. a central idea of the current
Flexx is having objects that exist in both Python and JS and have
properties that are settable from both ends. This will be no more.
Instead, objects live/operate *either* in Python or JS, but objects in JS
can still be referenced and influenced from Py.


Example
-------

Click the image below for an interactive example:

[![demo](https://dl.dropboxusercontent.com/s/x4s7wgv6tpyqsqo/flexx_demo_300.png)](http://flexx.readthedocs.io/en/latest/ui/examples/demo_src.html)

There are two demo servers at http://flexx1.zoof.io (an instance in Amazon's cloud)
and http://flexx2.zoof.io/ (a Raspberry pi). Either might not always be on.


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

Flexx makes use of the liberal 2-clause BSD license. See LICENSE for details.
