-----------------------
Sensible usage patterns
-----------------------

This chapter discusses some patterns that can be adopted to structure your
applications. Which kind of pattern(s) make sense depends on the use-case
and personal preference. Also, don't be dogmatic, these are only intended
to give a sensible direction.


The observer pattern
--------------------

The idea of the observer pattern is that observers keep track of (the
state of) other objects, and that these objects themselves are agnostic
about what it's tracked by. For example, in a music player, instead of
writing code to update the window-title inside the function that starts
a song, there would be a concept of a "current song", and the window
would listen for changes to the current song to update the title when
it changes.

This is a pattern worth following in almost all sceneario's. Flexx reaction
system was designed to make this as natural as possible. This idea is also
at the core of the next pattern.


Use of a central data store
---------------------------

When one part of your application needs to react to something in another
part of your application, it is possible to create a reaction that connects
to the event in question directly. However, as your app grows, this can
start to feel like spaghetti.

It might be better to define a central place that represents the state
of the application, e.g. on the root component, or on a separate object
that can easily be accessed from the root component. In this way, all 
parts of your application stay self-contained and can be updated/replaced
without the need for changes in other places of the application.

.. UIExample:: 100

    from flexx import flx
    
    class UserInput(flx.Widget):
        
        def init(self):
            with flx.VBox():
                self.edit = flx.LineEdit(placeholder_text='Your name')
                flx.Widget(flex=1)
        
        @flx.reaction('edit.user_done')
        def update_user(self, *events):
            self.root.store.set_username(self.edit.text)
    
    class SomeInfoWidget(flx.Widget):
        
        def init(self):
            with flx.FormLayout():
                flx.Label(title='name:', text=lambda: self.root.store.username)
                flx.Widget(flex=1)
    
    class Store(flx.JsComponent):
        
        username = flx.StringProp(settable=True)
    
    class Example(flx.Widget):
        
        store = flx.ComponentProp()
        
        def init(self):
            
            # Create our store instance
            self._mutate_store(Store())
            
            # Imagine this being a large application with many sub-widgets,
            # and the UserInput and SomeInfoWidget being used somewhere inside it.
            with flx.HSplit():
                UserInput()
                flx.Widget(style='background:#eee;')
                SomeInfoWidget()


Lean towards Python
-------------------

If your application is a Python app that just happens to use Flexx instead
of Qt, you may try to stay in Python-land as much as possible by making
use of ``PyWidget`` and ``PyComponent``.

We repeat the above example, but now most of the logic will happen in Python.
(The result will be nearly the same, but if we'd display it on this page it
would not be interactive, because there is no Python.)

.. code-block:: py

    from flexx import flx
    
    class UserInput(flx.PyWidget):
        
        def init(self):
            with flx.VBox():
                self.edit = flx.LineEdit(placeholder_text='Your name')
                flx.Widget(flex=1)
        
        @flx.reaction('edit.user_done')
        def update_user(self, *events):
            self.root.store.set_username(self.edit.text)
    
    class SomeInfoWidget(flx.PyWidget):
        
        def init(self):
            with flx.FormLayout():
                self.label = flx.Label(title='name:')
                flx.Widget(flex=1)
            
        @flx.reaction
        def update_label(self):
            self.label.set_text(self.root.store.username)
    
    class Store(flx.PyComponent):
        
        username = flx.StringProp(settable=True)
    
    class Example(flx.PyWidget):
        
        store = flx.ComponentProp()
        
        def init(self):
            
            # Create our store instance
            self._mutate_store(Store())
            
            # Imagine this being a large application with many sub-widgets,
            # and the UserInput and SomeInfoWidget being used somewhere inside it.
            with flx.HSplit():
                UserInput()
                flx.Widget(style='background:#eee;')
                SomeInfoWidget()


Only JS
-------

If you want to be able to publish your app to the web as a static page, you will
need to base it completely on JsComponents.

For web apps that serve many users and/or is a long-running process, it is
recommended to use Flexx to build the JS-only front-end, and implement the
back-end using a classic http framework (such as aiohttp, flask, asgineer, etc.).
The next chapter goes into detail how to do this.


Clear separation
----------------

If your use-case falls somewhere in between the two above patterns, you'll use
more of a mix of PyComponents and JsComponents.

In general, it is good to clearly separate the Python logic from the JavaScript
logic. E.g. by implementing the whole UI using widgets and JsComponents, and
implementing the "business logic" using one or more PyComponents.


Next
----

Next up: :doc:`Different ways to run a Flexx app <running>`.
