Flexx
=====

[![Build Status](https://travis-ci.org/flexxui/flexx.svg)](https://travis-ci.org/flexxui/flexx)
[![Documentation Status](https://readthedocs.org/projects/flexx/badge/?version=latest)](https://flexx.readthedocs.org)

Want to stay up-to-date about (changes to) Flexx? Subscribe to the [NEWS issue](https://github.com/flexxui/flexx/issues/477).


Introduction
------------

[Flexx](https://flexx.readthedocs.io) is a pure Python toolkit for
creating graphical user interfaces (GUI's), that uses web technology
for its rendering. Apps are written purely in Python; The
[PScript](https://pscript.readthedocs.io) transpiler generates the
necessary JavaScript on the fly.

You can use Flexx to create (cross platform) desktop applications, web
applications, and export an app to a standalone HTML document. It also
works in the Jupyter notebook.

The docs are on [Readthedocs](http://flexx.readthedocs.io).
the code is on [Github](http://github.com/flexxui/flexx).


Example
-------

Click the image below for an interactive example:

[![demo](https://dl.dropboxusercontent.com/s/x4s7wgv6tpyqsqo/flexx_demo_300.png)](http://flexx.readthedocs.io/en/latest/examples/demo_src.html)

There is a demo server at http://demo.flexx.app .


Motivation
----------

The primary motivation for Flexx is the undeniable fact that the web
(i.e. browser technology) has become an increasingly popular method for
delivering applications to users, also for (interactive) scientific
content.

The purpose of Flexx is to provide a single application framework to
create desktop applications, web apps, and (hopefully someday) mobile apps.
By making use of browser technology, the library itself can be
relatively small and pure Python, making it widely available and easy
to use.


A word of caution
-----------------

Flexx is very versatile and
[can be used in different ways](https://flexx.readthedocs.io/en/stable/guide/running.html).
It also makes it easy to mix Python that runs on the server and Python that
runs in the browser. This is a powerful feature but this also makes it easy
to create code that becomes difficult to maintain. You, the developer, must
ensure that Python and PScript code are clearly separated.


Installation
------------

Flexx requires Python 3.5+ and also works on pypy. Further,
it depends on:

* the [Tornado](http://www.tornadoweb.org) library (pure Python).
* the [PScript](http://github.com/flexxui/pscript) library (a pure Python flexxui project).
* the [Webruntime](http://github.com/flexxui/webruntime) library (a pure Python flexxui project).
* the [Dialite](http://github.com/flexxui/dialite) library (a pure Python flexxui project).

To install the latest release (and dependencies), use either of these commands:

* ``pip install flexx``
* ``conda install flexx -c conda-forge``

Or get the bleeding edge with:

* ``pip install https://github.com/flexxui/flexx/archive/master.zip``


Supported browsers
------------------

Flexx aims to support all modern browsers, including Firefox, Chrome and Edge.
Internet Explorer version 10 and up should work, but some things may be flaky.

For running desktop apps, it is needed to have Firefox or NW.js installed.


License
-------

Flexx makes use of the liberal 2-clause BSD license. See LICENSE for details.
