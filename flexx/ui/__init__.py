"""

Once you are familiar with :class:`JsComponent <flexx.app.JsComponent>` and
the :class:`Widget <flexx.ui.Widget>` class, understanding all other widgets
should be relatively straightforward. The ``Widget`` class is the base class
of all other ui classes. On itself it does not do or show much, though we can make it
visible by changing the background color:

.. UIExample:: 100

    from flexx import app, ui

    class Example(ui.HSplit):

        def init(self):
            ui.Widget(style='background:red;')
            ui.Widget(style='background:blue;')


Widgets can also used as a container for other widgets:

.. UIExample:: 100

    from flexx import app, ui

    class Example(ui.Widget):

        def init(self):
            ui.Button(text='hello')
            ui.Button(text='world')

The above is usually not the layout that you want. Therefore there are layout widgets
which distribute the space among its children in a more sensible manner. Like the
``HSplit`` in the first example.

Compound widgets can be used anywhere in your app. They are
constructed by implementing the ``init()`` method. Inside this method
the widget is the *default parent*.

Any widget class can also be used as a *context manager*. Within the context,
the widget is the default parent; any widget that is created in that context
and that does not specify a parent will have the widget as a parent. (The
default-parent-mechanism is thread-safe, since there is a default widget
per thread.)

.. UIExample:: 100

    from flexx import app, ui

    class Example(ui.Widget):

        def init(self):
            with ui.HSplit():
                ui.Button(text='foo')
                with ui.VBox():
                    ui.Button(flex=1, text='bar')
                    ui.Button(flex=1, text='spam')


To create an actual app from a widget, there are three possibilities:
``serve()`` it as a web app, ``launch()`` it as a desktop app or
``export()`` it as a standalone HTML document:

.. code-block:: py

    from flexx import app, ui

    @app.serve
    class Example(ui.Widget):
        def init(self):
            ui.Label(text='hello world')

    example = app.launch(Example)
    app.export(Example, 'example.html')



Using widgets the classic way
-----------------------------

In the above examples, we've used the "classic" way to build applications
from basic components. Flexx provides a variety of layout widgets as well
as leaf widgets (i.e. controls), see the  :doc:`list of widget classes <api>`.


Using widgets the web way
-------------------------

An approach that might be more familiar for web developers, and which is
inspired by frameworks such as React is to build custom widgets using
html elements:

.. UIExample:: 150

    from flexx import app, event, ui

    class Example(ui.Widget):

        name = event.StringProp('John Doe', settable=True)
        age =  event.IntProp(22, settable=True)

        @event.action
        def increase_age(self):
            self._mutate_age(self.age + 1)

        def _create_dom(self):
            # Use this method to create a root element for this widget.
            # If you just want a <div> you don't have to implement this.
            return ui.create_element('div')  # the default is <div>

        def _render_dom(self):
            # Use this to determine the content. This method may return a
            # string, a list of virtual nodes, or a single virtual node
            # (which must match the type produced in _create_dom()).
            return [ui.create_element('span', {},
                        'Hello', ui.create_element('b', {}, self.name), '! '),
                    ui.create_element('span', {},
                        'I happen to know that your age is %i.' % self.age),
                    ui.create_element('br'),
                    ui.create_element('button', {'onclick': self.increase_age},
                        'Next year ...')
                    ]

The ``_render_dom()`` method is called from an implicit reaction. This means
that when any properties that are accessed during this function change,
the function is automatically called again. This thus provides a declerative
way to define the appearance of a widget using HTML elements.

Above, the third argument in ``create_element()`` is a string, but this may
also be a list of dicts (``create_element()`` returns a dict).
"""

import logging
logger = logging.getLogger(__name__)
del logging

# flake8: noqa

# We follow the convention of having one module per widget class (or a
# small set of closely related classes). In order not to pollute the
# namespaces, we prefix the module names with an underscrore.

from ._widget import Widget, create_element
from .layouts import *
from .widgets import *
