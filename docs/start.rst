---------------
Getting started
---------------

Installation
------------

* ``conda install flexx -c conda-forge``
* ``pip install flexx``
* Old school: ``python setup.py install``
* Clone the repo and add the root dir to your PYTHONPATH (developer mode)

When using Pip or Conda, the dependencies will be installed automatically.


Dependencies
------------

Being pure Python and cross platform, it should work (almost) anywhere
where there's Python and a browser.
Flexx is written for Python 3.5+ and also works on Pypy.
Flexx actively supports Firefox, Chrome and (with minor limitations) MS Edge.

Flexx further depends on:
    
* `Tornado <http://tornado.readthedocs.io>`_
* `PScript <http://pscript.readthedocs.io>`_
* `Webruntime <http://webruntime.readthedocs.io>`_
* `Dialite <http://dialite.readthedocs.io>`_

All are pure Python packages, and the latter three are projects under the
flexxui umbrella. Further, Flexx needs a browser. To run apps that look like
desktop apps, we recommend having Firefox installed.


Supported browsers
------------------

Flexx aims to support all modern browsers, including Firefox, Chrome and Edge.
Internet Explorer version 10 and up should work, but some things may be flaky.


Current status
--------------

Since Flexx version 0.5, it is in beta status; some parts of the API
may change, but we do care about backwards compatibility.


