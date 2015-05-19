Flexx
=====

Flexx is a cross-platform, pure Python toolkit for creating graphical
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
* properties - A property system similar to IPython's traitlets or
  bokeh's properties.
* util - various utilities related to application development.
* lui - an experimental lightweight UI toolkit based on OpenGL designed
  to work everywhere that can be used as a fallback.


Example
-------

Working code example showing buttons layed out using different flex factors::

    from flexx import ui

    class MyApp(ui.App):
        
        def init(self):
            
            with ui.VBox():
                
                with ui.HBox(flex=1):
                    ui.Button(text='Box A', flex=0)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=0)
                with ui.HBox(flex=0):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=1)
                    ui.Button(text='Box C is a bit longer', flex=1)
                with ui.HBox(flex=1):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=2)
                with ui.HBox(flex=2):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=2)
                    ui.Button(text='Box C is a bit longer', flex=3)
    
    app = MyApp()
    ui.run()


Current status
--------------

Flexx is still very much a work in progress. Please don't go use it
just yet for anything serious. Most code premature and API's subject
to change. The exception might be the webruntime and pyscript modules,
although their API's may change as well.

Using flexx from the Jupyter notebooks is currently broken.


Getting started
---------------

In case you want to play with the code:

* clone the repo
* put the repo dir in your PYTHONPATH
* ``python setup.py install`` may work (or it may not)
* run the examples (they may not all work currently)
