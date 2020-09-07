-------------
Release notes
-------------

**v0.8.1** (07-09-2020)

* Support for Python 3.8.
* Support for latest Tornado (includes a workaround for py38+win).
* Several fixes to various widgets.
* Various fixes to the docs.
* A few new examples.


**v0.8.0** (26-04-2019)

* Adds a `PyWidget` class that can be used as a base class for your high-level
  widgets. Because it is a PyComponent, this makes it much easier to write apps
  that fully work in Python (desktop-like apps).
* The ``FormLayout`` uses CSS ``grid`` instead of ``<table>``.
* A new ``GridLayout`` widget.
* A new ``MultiLineEdit`` widget.
* Improvements to docs and guide.
* Support for freezing Flexx apps to standalone executables (via PyInstaller).

Also see the
`overview of 0.8 issues and pull request <https://github.com/flexxui/flexx/milestone/13?closed=1>`_


**v0.7.1** (03-12-2018)

* Improved shutdown behavior (#533).
* Small fix in App.export (#532).
* Fix bahevior when navigating *back* to a Flexx app (#536).


**v0.7.0** (02-11-2018)

* New examples for Openlayers and including local assets (by @ocobacho).
* Tests, demos and readme are included in the sdist, helping packaging on Linux (by @toddrme2178).
* Some performance tweaks which should help in larger applications.
* Add ``outernode`` attribute in `TreeItem`` widget, enabling more powerful subclasses.
* The ``Combobox`` is smarter about the placement of the "dropdown".
* A new ``RangeSlider`` widget.

Also see the
`overview of 0.7 issues and pull request <https://github.com/flexxui/flexx/milestone/9?closed=1>`_


**v0.6.2** (04-10-2018)

- Bugfix in combobox.
- BSDF check dtype in JS.


**v0.6.0** (02-10-2018)

Most notable changes:

* Add ``Widget.minsize_from_children`` property (#497).
* Update BSDF (data serialization).
* Widgets van be orphaned upon initialization by setting parent to None (#493)
* Some internal improvements on the dropdown widget.

Also see the
`overview of 0.6 issues and pull request <https://github.com/flexxui/flexx/milestone/7?closed=1>`_


**v0.5.0** (13-09-2018)

This release marks the end of the alpha stage of Flexx. Until now, we took the liberty
to redesign various parts of Flexx and break the API several times. From now on,
we care a lot more about backwards compatibility.

Some highlights of changes from the last release:

* A major refactoring of the event system.
* We spun out the PyScript transpiler into the PScript project, as well
  as the webruntime and dialite project. This means that Flexx itself
  is focussed on the GUI aspect alone.
* Added touch support.
* Dropped the depency on Phosphor.js.
* A new combined namespace: ``from flexx import flx``.
* A proper guide in the docs.
* More examples.

Also see the
`overview of 0.5 pull request <https://github.com/flexxui/flexx/issues?q=is%3Apr+milestone%3Av0.5>`_
and
`overview of 0.5 issues <https://github.com/flexxui/flexx/issues?q=is%3Aissue+milestone%3Av0.5>`_
corresponding to this release.


**v0.4.2** (13-10-2017)

This release was not published to Pypi. It served mainly as a tag right before
the big refactoring. There were a lot of improvements, but we felt that the state of Flexx
was still very much in flux (no pun intended).


Also see the
`overview of 0.4.2 pull request <https://github.com/flexxui/flexx/issues?q=is%3Apr+milestone%3Av0.4.2>`_
and
`overview of 0.4.2 issues <https://github.com/flexxui/flexx/issues?q=is%3Aissue+milestone%3Av0.4.2>`_
corresponding to this release.


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
