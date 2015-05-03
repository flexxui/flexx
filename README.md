Flexx
=====

Flexx is a cross-platform, pure Python tookit for creating graphical
user interfaces (GUI's), that uses web technology for its rendering.
You can use Flexx to create desktop applications as well as web
applications. 

Flexx can also be used to run a subset of Python in a web runtime (e.g.
Nodejs), and can be used from within the Jupyter notebook.

Flexx is pure Python, and its only dependencies are Tornado and a
browser. To run apps in desktop-mode, we recommend having Firefox
installed.

Flexx consists of several modules which can be individually used; none
of the modules are imported by default.

* ui - the ui toolkit, most people will use just this.
* webruntime - launch a web runtime (xul application, browser etc.).
* pyscript - Python to JavaScript compiler.
* properties - or util.properties? - A property system similar to IPython's
  traitlets or bokeh's properties.
* util - various utilities related to application development.
* lui - an experimental lightweight UI toolkit based on OpenGL designed
  to work everywhere that can be used as a fallback.


Current status
--------------

Flexx is still very much a work in progress. Please don't go use it
just yet. The ui part is not even working yet. The exception might be
the webruntime and pyscript modules, although their API's may still
change as well.
