"""
This module consists solely of widget classes. Once you are familiar with the
Widget class, understanding all other widgets should be straightforward.
The Widget class is the base component of all other ui classes. On
itself it does not do or show much, though we can make it visible:

.. UIExample:: 100
    
    from flexx import app, ui
    
    # A red widget
    class Example(ui.Widget):
        CSS = ".flx-example {background:#f00; min-width: 20px; min-height:20px}"

Widgets are also used as a container class:

.. UIExample:: 100
    
    from flexx import app, ui
    
    class Example(ui.Widget):
        
        def init(self):
            ui.Button(text='hello')
            ui.Button(text='world')

Such "compound widgets" can be used anywhere in your app. They are
constructed by implementing the ``init()`` method. Inside this method
the widget is the *default parent*.

Any widget class can also be used as a *context manager*. Within the context,
the widget is the default parent; any widgets created in that context
that do not specify a parent, will have the widget as a parent. (The
default-parent-mechanism is thread-safe, since there is a default widget
per thread.)

.. UIExample:: 100
    
    from flexx import app, ui
    
    class Example(ui.Widget):
        
        def init(self):
            with ui.HBox():
                ui.Button(flex=1, text='hello')
                ui.Button(flex=1, text='world')

To create an actual app, you need to mark a widget as an app:

.. code-block:: py
    
    from flexx import app, ui
    
    @app.make_app
    class Example(ui.Widget):
        def init(self):
            ui.Label(text='hello world')

Such an app can then be loaded by a client connecting to the server.
Or, for desktop use, you can launch an instance:

.. code-block:: py

    example = Example.launch('xul')  # specify runtime to run app in


Similarly, apps can be exported. If all user ineraction is implemented
in JS, the app can be served from a standalone HTML document:

.. code-block:: py
    
    Example.export('example.html')

To lean about the individual widgets, check the 
:doc:`list of widget classes <api>`.
"""

# We follow the convention of having one module per widget class (or a
# small set of closely related classes). In order not to pollute this
# namespace, we prefix the module names with an underscrore.

from ._widget import Widget

from ._layout import Layout
from ._box import Box, HBox, VBox
from ._splitter import Splitter, HSplitter, VSplitter
from ._formlayout import BaseTableLayout, FormLayout, GridLayout
from ._pinboardlayout import PinboardLayout

from ._button import Button
from ._slider import Slider
from ._lineedit import LineEdit

from ._label import Label
from ._panel import Panel
from ._progressbar import ProgressBar

from ._plotwidget import PlotWidget
from ._plotlayout import PlotLayout
