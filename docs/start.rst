---------------
Getting started
---------------


Dependencies
------------

Being pure Python and cross platform, it should work (almost) anywhere
where there's Python and a browser.
Flexx is written for Python 3.5+ and also works on Pypy.
Flexx actively supports Firefox, Chrome and (with minor limitations) IE/Edge.

Flexx depends on ``tornado``, ``pscript``, ``webruntime`` and ``dialite``. 
All are pure Python packages, and the latter three are projects under the
flexxui umbrella. Further, Flexx needs a browser. To run apps that look like
desktop apps, we recommend having Firefox installed.

Developers that want to run the tests need:

* pytest and pytest-cov (get them via conda or pip)
* flake8 (get it via conda or pip)
* Nodejs
* Firefox


Current status
--------------

Flexx is in development and is in alpha status. Any part of the public
API may change without notice.


Installation
------------

* ``conda install flexx -c conda-forge``
* ``pip install flexx``
* Old school: ``python setup.py install``
* Clone the repo and add the root dir to your PYTHONPATH (developer
  mode, not possible for Python 2.7)


Motivation
----------

The primary motivation for Flexx is the undeniable fact that the web
(i.e. browser technology) has become an increasingly popular method for
delivering applications to users, also for (interactive) scientific
content.

The purpose of Flexx is to provide a single application framework to
create desktop applications and web apps. By making use of browser
technology, the library itself can be relatively small and pure Python,
making it widely and easily available.

By making use of PScript (Python to JavaScript translation), the entire
library is written without a line of JavaScript. This makes it easier
to develop than if we would have a corresponding "flexx.js" to maintain.
Further, it allows users to easily define callback methods that are
executed in JavaScript, allowing for higher performance when needed.

Libraries written for Python, but not *in* Python have a much harder
time to survive, because users don't easily become contributors. This
is one of the reasons of the success of e.g. scikit-image, and the
demise of e.g. Mayavi. Since Flexx is written in a combination of Python
and PScript, its user community is more likely to take an active role
in its development.


Flexx overview
--------------

TODO: rework this

.. image:: _static/overview.svg

The image above outlines the structure of Flexx. 
The *event* module provides a powerful property and event system that
makes it easy to connect different parts of your application.
In the *app* module the app mainloop is defined, running the server to
which the web runtime connects (via a websocket). Further, it extends
the ``event.Component`` class into the ``PyComponent`` and
``JsComponent`` classes;
a class for which its instances have a corresponding representation in
JavaScript. Properties are synced both ways, and it allows subclasses
to define methods for the JS version of the object in Python code (or
PScript, to be precise). This is the base class for all widgets, but
could in principle also be useful in other situations where a tight
connection between Python and JS is required.
In the *ui* module all widgets are implemented.

In this documentation, we include a separate reference for each
subpackage. We recommend starting with the *ui* module, and not to worry
about the other modules until they're needed.

Notebooks
---------

There is a collection of 
`notebooks on Github <https://github.com/flexxui/flexx-notebooks>`_.
The tutorial notebooks are also listed in the examples section of each
subpackage in the reference docs.

The notebooks containing widgets are best viewed live or in the nbviewer.
