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

**v0.3** (upcoming)

The most important changes with respect to the previous release are:
    
- Flexx now works on Legacy Python (i.e. Python 2.7). The source code is
  automatically translated upon installation.
- Improvements to nested FlexLayout on Chrome
- A command-line tool to stop and get info on running Flexx servers.
- More tests
- A new Canvas widget

Also see the
`overview of pull request <https://github.com/zoofIO/flexx/issues?q=is%3Apr+milestone%3Av0.3>`_
and
`overview of issues <https://github.com/zoofIO/flexx/issues?q=is%3Aissue+milestone%3Av0.3>`_
corresponding to this release.

**v0.2** (13-10-2015)

We changed a lot, broke API's, improved things, and probbaly broke other
things. Here's a summary of the most important bits:

- Set up Travis CI, and added more unit tests.
- Layout of ui widgets is based on Phosphorjs.
- Style compliance (and tested on Travis).
- Refactored PyScript, and made it much more feature complete.
- PyScript makes use of common ast, and now works on 3.2-3.5, and pypy.
- We now have a way to include assets (js, css, images).
- The assets make it possible to e.g. embed a Bokeh plot, or a jQuery widget.

Also see the
`overview of pull request <https://github.com/zoofIO/flexx/issues?q=is%3Apr+milestone%3Av0.2>`_
and
`overview of issues <https://github.com/zoofIO/flexx/issues?q=is%3Aissue+milestone%3Av0.2>`_
corresponding to this release.


**v0.1** (27-08-2015)

First release.
