-------------------------
Release notes and roadmap
-------------------------

Roadmap
-------

Things to work on for the relative short term:

* Visual tests and Selenium tests.
* A more complete widget set.
* Support for mobile apps.
* Support to run native apps on Windows without needing Firefox.
* Support for sending (large) binary data to the client for scientific applications.


Release notes
-------------

**v0.4.1** (10-07-2016)

A few [fixes](https://github.com/flexxui/flexx/milestone/8).


**v0.4** (07-07-2016)

A lot of work and major changes compared to the previous release. Most notably:

* Completely new event system ``flexx.event`` replaces ``flexx.react``.
* System for configure Flexx through config files, env variables and command line arguments.
* Better logging.
* More widgets, more examples.
* Better notebook support.
* Fixed nasty bug where new profile data was stored on each launch of the XUL runtime.
* Better support for testing and running Flexx in a separate thread.

Also see the
`overview of 0.4 pull request <https://github.com/flexxui/flexx/issues?q=is%3Apr+milestone%3Av0.4>`_
and
`overview of 0.4 issues <https://github.com/flexxui/flexx/issues?q=is%3Aissue+milestone%3Av0.4>`_
corresponding to this release.


**v0.3.1** (19-02-2016)

A few small fixes, and improvements to distribution. The universal wheel
on Pypi for v0.3 did not work on Python 2.7. Flexx now includes
a recipe to build a noarch conda package.

Also see the
`overview of 0.3.1 pull request <https://github.com/flexxui/flexx/issues?q=is%3Apr+milestone%3Av0.3.1>`_.


**v0.3** (15-02-2016)

The most important changes with respect to the previous release are:
    
- Flexx now works on Legacy Python (i.e. Python 2.7). The source code is
  automatically translated during installation.
- Improvements to nested FlexLayout on Chrome
- A command-line tool to stop and get info on running Flexx servers.
- More tests
- A new Canvas widget.
- PyScript uses bound functions for methods and functions without selt/this
  as first arg.

Also see the
`overview of 0.3 pull request <https://github.com/flexxui/flexx/issues?q=is%3Apr+milestone%3Av0.3>`_
and
`overview of 0.3 issues <https://github.com/flexxui/flexx/issues?q=is%3Aissue+milestone%3Av0.3>`_
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
`overview of 0.2 pull request <https://github.com/flexxui/flexx/issues?q=is%3Apr+milestone%3Av0.2>`_
and
`overview of 0.2 issues <https://github.com/flexxui/flexx/issues?q=is%3Aissue+milestone%3Av0.2>`_
corresponding to this release.


**v0.1** (27-08-2015)

First release.
