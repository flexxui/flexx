--------------
Widgets basics
--------------

If you're interested in Flexx, the first thing that you probably want to do is
create a UI. So let's see how that works, and talk about
:doc:`components <widgets_components>`, :doc:`events <event_system>`
and :doc:`reactions <reactions>` later.

Your first widget
-----------------

The :class:`Widget <flexx.ui.Widget>` class is the base class of all
other ui classes. On itself it does not do or show much. What you'll
typically do, is subclass it to create a new widget that contains ui
elements:


.. UIExample:: 100
    from flexx import flx

    class Example(flx.Widget):

        def init(self):
            flx.Button(text='hello')
            flx.Button(text='world')

The above is usually not the layout that you want. Therefore there are layout widgets
which distribute the space among its children in a more sensible manner. Like the
:class:`HBox <flexx.ui.HBox>`:


.. UIExample:: 100

    from flexx import flx

    class Example(flx.Widget):

        def init(self):
            with flx.HBox():
                flx.Button(text='hello', flex=1)
                flx.Button(text='world', flex=2)

The ``HBox`` and ``Button`` are all widgets too. The example widgets that we
created above are also refered to as "compound widgets"; widgets that contain
other widgets. This is the most used way to create new UI elements.


The init method
---------------

In the above example one can see the use of the ``init()`` method, which
is a common use in Flexx. It is generally better to use it instead of ``__init__()``,
because Flexx calls it at a very approproate time in the initialization process.
For example, when ``init()`` is called, the corresponding widget is the *default parent*.

Further, the ``init()`` gets the positional instantiation arguments: creating
a component ``Person("john", 32)`` matches ``def init(self, name, age)``.


Structuring widgets
-------------------

Flexx comes with it's own layout system. (Therefore you should generally
not use CSS for widget layout, though you can very well use CSS
*inside* a widget).

Any widget class can also be used as a *context manager*. Within the context,
that widget is the default parent; any widget that is created in that context
and that does not specify a parent will have that widget as a parent. (This
mechanism is thread-safe.) This allows for a style of writing that
clearly shows the structure of your app:

.. UIExample:: 100

    from flexx import flx

    class Example(flx.Widget):

        def init(self):
            with flx.HSplit():
                flx.Button(text='foo')
                with flx.VBox():
                    flx.Widget(style='background:red;', flex=1)
                    flx.Widget(style='background:blue;', flex=1)


Turning a widget into an app
----------------------------

To create an actual app from a widget, simply wrap it into an :class:`App <flexx.app.App>`.
You can then ``launch()`` it as a desktop app, ``serve()`` it as a web app,
``dump()`` the assets, ``export()`` it as a standalone HTML document, or
even ``publish()`` it online (experimental). Later in this guide we dive deeper
into the different ways that you can run your app.

.. code-block:: py

    from flexx import flx

    class Example(flx.Widget):
        def init(self):
            flx.Label(text='hello world')

    app = flx.App(Example)
    app.export('example.html', link=0)  # Export to single file

To actually show the app, use launch:

.. code-block:: py

    app.launch('browser')  # show it now in a browser
    flx.run()  # enter the mainloop



Using widgets the Python way
----------------------------

In the above examples, we've used the "classic" way to build applications
from basic components. Flexx provides a variety of layout widgets as well
as leaf widgets (i.e. controls), see the  :doc:`list of widget classes <../ui/api>`.

Further, we've created high-level widgets by subclassing the ``flx.Widget`` class.
These classes operate in JavaScript, because they are what we call ``JsComponent``'s,
more on that later. Effectively, we are able to show the widgets live inside the guide itself.
However, if you are developing a desktop app, consider subclassing from ``PyWidget``
instead: this will make that your widgets operatate in Python instead of JavaScript.
We talk more about this in the next page of the guide.


Using widgets the web way
-------------------------

An approach that might be more familiar for web developers, and which is
inspired by frameworks such as React is to build custom widgets using
html elements. If you're used to Python and the below looks odd to you, don't
worry, you don't need it:

.. UIExample:: 150

    from flexx import flx

    class Example(flx.Widget):

        name = flx.StringProp('John Doe', settable=True)
        age =  flx.IntProp(22, settable=True)

        @flx.action
        def increase_age(self):
            self._mutate_age(self.age + 1)

        def _create_dom(self):
            # Use this method to create a root element for this widget.
            # If you just want a <div> you don't have to implement this.
            return flx.create_element('div')  # the default is <div>

        def _render_dom(self):
            # Use this to determine the content. This method may return a
            # string, a list of virtual nodes, or a single virtual node
            # (which must match the type produced in _create_dom()).
            return [flx.create_element('span', {},
                        'Hello', flx.create_element('b', {}, self.name), '! '),
                    flx.create_element('span', {},
                        'I happen to know that your age is %i.' % self.age),
                    flx.create_element('br'),
                    flx.create_element('button', {'onclick': self.increase_age},
                        'Next year ...')
                    ]

The ``_render_dom()`` method is called from an implicit reaction. This means
that when any properties that are accessed during this function change,
the function is automatically called again. This thus provides a declerative
way to define the appearance of a widget using HTML elements.

Above, the third argument in ``create_element()`` is a string, but this may
also be a list of dicts (``create_element()`` returns a dict).


Next
----

Next up: :doc:`Widgets are components <widgets_components>`.
