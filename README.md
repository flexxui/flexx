Flexx
=====

[Flexx](https://flexx.readthedocs.org) is a pure Python toolkit for creating
graphical user interfaces (GUI's), that uses web technology for its
rendering. You can use Flexx to create desktop applications, web
applications, and (if designed well) export an app to a standalone HTML
document. It also works in the Jupyter notebook.

Being pure Python and cross platform, it should work anywhere where
there's Python and a browser. To run apps in desktop-mode, we recommend having Firefox
installed.

Flexx has a modular design, consisting of a few subpackages, which can
also be used by themselves:

* ui - the widgets
* app - the event loop and server
* react - reactive programming (how information flows through your program)
* pyscript - Python to JavaScript transpiler
* webruntime - to launch a runtime

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


Demo server
-----------

There is an Amazon instance running some demos on http://52.21.93.28:8000/ 
(unless I turned it off for testing, etc.).
