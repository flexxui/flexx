Flexx
=====

Flexx is a cross-platform, pure Python toolkit for creating graphical
user interfaces (GUI's), that uses web technology for its rendering.
You can use Flexx to create desktop applications as well as web
applications, and it can be used in the Jupyter notebook.

Flexx is pure Python, and its only dependencies are Tornado and a
browser. To run apps in desktop-mode, we recommend having Firefox
installed.

Flexx consists of several modules which can be individually used (none
of the modules are imported by default):

* ui - the ui toolkit, most people will use just this.
* app - event loop and friends .
* react - provided reactive programming.
* pyscript - Python to JavaScript transpiler.
* webruntime - launch a web runtime (xul application, browser etc.).
* util - utilities related to application development.

Example
-------

Working code example::

    from flexx import app, ui, react
    
    class Example(ui.Widget):
        
        def init(self):
            self.count = 0
            with ui.HBox():
                self.button = ui.Button(text='Click me', flex=0)
                self.label = ui.Label(flex=1)
        
        @react.connect('button.mouse_down')
        def _handle_click(self, down):
            if down:
                self.count += 1
                self.label.text('clicked %i times' % self.count)
    
    main = app.launch(Example)
    app.run()


Current status
--------------

Flexx is still very much a work in progress. Please don't go use it
just yet for anything serious. The public API can change without notice.
However, we're interested in feedback, so we invite you to play with
it!


Getting started
---------------

* clone the repo
* put the repo dir in your PYTHONPATH
* ``python setup.py install``
* run the examples

