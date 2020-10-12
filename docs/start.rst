---------------
Getting started
---------------

Installation
------------

* ``pip install flexx``
* ``conda install flexx -c conda-forge``
* Old school: ``python setup.py install``
* Clone the repo and add the root dir to your PYTHONPATH (developer mode)

When using Pip or Conda, the dependencies will be installed automatically.


Dependencies
------------

Being pure Python and cross platform, Flexx should work (almost)
anywhere where there's Python and a browser. Flexx is written for Python
3.5+ and also works on Pypy.

Flexx further depends on the following packages (all are pure Python,
and the latter three are projects under the flexxui umbrella):

* `Tornado <http://tornado.readthedocs.io>`_
* `PScript <http://pscript.readthedocs.io>`_
* `Webruntime <http://webruntime.readthedocs.io>`_
* `Dialite <http://dialite.readthedocs.io>`_


Supported browsers
------------------

Flexx aims to support all modern browsers, including Firefox, Chrome and Edge.
Internet Explorer version 10 and up should work, but some things may be flaky.

To run apps that look like desktop apps, we recommend having Firefox or nw.js installed.


Current status
--------------

Flexx is in beta status; some
parts of the API may change, but we do care about backwards compatibility.
