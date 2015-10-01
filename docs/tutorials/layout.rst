======
Layout
======

There are a variety of ways to layout widgets in `flexx.ui`. The most
common is to align things horizonaltally or vertically using a box layout.
A form layout can also be convenient. For more control there is a grid,
and for more flexibility there is PinBoard layout.


.. note::
    These examples are all working code. When building the docs, the
    Python code of the examples is executed and the resulting app is
    exported to a standalone html file. These html files are displayed
    in this page in iframes. In a proper browser the example apps can
    be resized.


No layout
---------

Let's start by looking at what would happen without any layout. We just
create an app with three buttons. 

.. UIExample:: 100
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            self.b1 = ui.Button(text='Hello world')
            self.b2 = ui.Button(text='Foo')
            self.b3 = ui.Button(text='Bar')

What happens is that this is HTML, so the buttons will simply be placed
after each-other until they no longer fit on one row. By applying
appropriate styling you can make them each appear on a line, or e.g. 
``float: left``. But real GUI-like layout is best done using actual
layout classes!


HBox and VBox
-------------

With the `HBox` class, you can layout widgets horizontally. Note the use of
the flex argument. It determines how the widget is stretched. A flex of 0
means to not stretch, but use the minumum sensible width. This is either
the manually set min-width, or the browser-computed natural width,
whichever is largest.

.. UIExample:: 100
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.HBox():
                self.b1 = ui.Button(text='Hola', flex=0)
                self.b2 = ui.Button(text='Hello world', flex=1)
                self.b3 = ui.Button(text='Foo bar', flex=2)


You can see how the layout is used as context manager. Inside this
context, the layout automatically becomes the parent of the newly
created widgets. A nice side-effect is that the source gets structured
in a way that reflects the structure of the elements.


The `VBox` class is similar to the `HBox`, except now the widgets are
aligned vertically. Note how we don't specify a flex here, effectively 
giving the buttons a (vertical) flex of 0. 

.. UIExample:: 100
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.VBox():
                self.b1 = ui.Button(text='Hola')
                self.b2 = ui.Button(text='Hello world')
                self.b3 = ui.Button(text='Foo bar')
                ui.Widget(flex=1)

In the above app, we use an empty widget as a spacer. This is because
the VBox and HBox always want to fill their space. If we would not put
the stub widged at the end, there would be space between the elements
to fill up the whole space.

.. UIExample:: 120
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.VBox():
                self.b1 = ui.Button(text='Hola')
                self.b2 = ui.Button(text='Hello world')
                self.b3 = ui.Button(text='Foo bar')

One difference you can observe between HBox and VBox is that the
elements in the VBox get fully stretched horizontally, while the elements
in a HBox do *not* get stretched vertically. This is because elements
(e.g. buttons) still look ok when they are wider than necessary, but look
strange when they are higher than necessary. We may add arguments to the
layout to influence this behavior.

Now for a more complex example. A couple of HBox'es in a VBox, to show
some possible variations. Also note how this syntax for writing out the
layout leads to a clear structure that corresponds to how the the
widgets are organized.

.. UIExample:: 300
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.VBox():
                
                ui.Label(text='Flex 0 0 0')
                with ui.HBox(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Label(text='Flex 1 0 3')
                with ui.HBox(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=3)
                
                ui.Label(text='margin 10 (around layout)')
                with ui.HBox(flex=0, margin=10):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Label(text='spacing 10 (inter-widget)')
                with ui.HBox(flex=0, spacing=10):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Widget(flex=1)
                ui.Label(text='Note the spacer Widget above')


    
FormLayout
----------

The FormLayout is a specific case of the Grid layout (which will be
discussed next). It is a very convenient layout when you have a bunch
of widgets (or labels) next to labels to describe them. Like in a form.

As you can see, you simply specify the elements, and each pair of elements
is placed on a row. The left row has an implicit flex of zero, and the right
row an implicit flex of 1. To not stretch the rows, we add a simple stretcher
element at the end. In the Form layout, the specified flex applies to
the vertical direction.

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.FormLayout():
                ui.Label(text='Pet name:')
                self.b1 = ui.Button(text='Hola')
                ui.Label(text='Pet Age:')
                self.b2 = ui.Button(text='Hello world')
                ui.Label(text='Pet\'s Favorite color:')
                self.b3 = ui.Button(text='Foo bar')
                ui.Widget(flex=1)
    
    
GridLayout
----------

In a GridLayout, child widgets are aligned in a two-dimensional grid.
This is currently not implemented, but is a relatively simple extension
of the FormLayout. The main challenge is in the API design to allow the
user to specify a flex value for both the horizontal and vertical
direction. 


PinboardLayout
--------------

The PinboardLayout layout provides a free layout without any form of
alignment. Child widgets are given a certain position (and optionally
size). When the position or size is larger than 1, it's in pixels. When
it's smaller than 1, it is regarded a fractional position (i.e. as in
a percentage of the parent size).

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.PinboardLayout():
                self.b1 = ui.Button(text='Stuck at (20, 20)', pos=(20, 30))
                self.b2 = ui.Button(text='Dynamic at (30%, 30%)', pos=(0.3, 0.3))
                self.b3 = ui.Button(text='Dynamic at (50%, 70%)', pos=(0.5, 0.7))


Splitters
---------

The splitters split the available space in regions, which size can be
set by the user by dragging the divider. Unlike an HBox or VBox, a
splitter is not aware of the natural size of its content, and only takes
the minimum size of its children into account. A splitter sets its own
minimum size as the combined minimum size of its children (plus a little
extra).

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.SplitPanel(orientation='v'):
                ui.Button(text='Right A')
                ui.Button(text='Right B')
                ui.Button(text='Right C')

Let's make it more interesting, a splitter inside a HBox, where the splitter has
a button on the left and a hbox on the right (min_size is currently not implemented):


.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.HBox():
                ui.Button(text='Button in hbox', flex=0, style='min-width:110px;')
                with ui.SplitPanel(flex=2):
                    ui.Button(text='Button in hsplit', style='min-width:110px;')
                    with ui.HBox():
                        ui.Button(text='Right A', flex=0)
                        ui.Button(text='Right B', flex=1)
                        ui.Button(text='Right C', flex=2)


.. raw:: html

    <!-- Some exta space to allow easy resizing of the last example -->
    <br /><br /><br /><br /><br />
