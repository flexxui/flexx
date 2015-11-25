-------------------------
Release notes and roadmap
-------------------------

Roadmap
-------

* More tests
* More widgets
* Probably a refactoring (and rename) of ``flexx.react``.


Release notes
-------------

**v0.2**

We changed a lot, broke API's, improved things, and probbaly broke other
things. Here's a summary of the most important bits:

- Set up Travis CI, and added more unit tests.
- Layout of ui widgets is based on Phosphorjs.
- Style compliance (and tested on Travis).
- Refactored PyScript, and made it much more feature complete.
- PyScript makes use of common ast, and now works on 3.2-3.5, and pypy.
- We now have a way to include assets (js, css, images).
- The assets make it possible to e.g. embed a Bokeh plot, or a jQuery widget.



**v0.1**

First release.
