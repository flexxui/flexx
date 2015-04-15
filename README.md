Flexx
=====

Flexx is a Python tookit for creating user interfaces (UI's), that uses
web technology for its rendering. You can use Flexx to create desktop
applications as well as web applications. Flexx can also be used from
within the Jupyter notebook.

Flexx is pure Python, and has no dependencies other than the browser
that's already installed on the system. To run apps in desktop-mode,
we recommend having Firefox installed.

Flexx consists of several modules which can be individually used; none
of the modules are imported by default.

* ui - the ui toolkit, most people will use just this
* webruntime - launch a web runtime (xul application, browser etc.)
* pyscript - Python to JavaScript compiler
* properties - or util.properties? - A property system similar to IPython's 
  traitlets or bokeh's properties.
* util - various utilities related to application development
* lui - a lightweight UI toolkit based on OpenGL designed to work
  everywhere that can be used as a fallback
