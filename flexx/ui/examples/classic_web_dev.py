# doc-export: Example
"""
This example illustrates some of the approaches by which Flexx can be used
in a way that might be more familiar to web developers.

The main tool is the ``flexx.ui.html`` factory object. It looks like a
module that contains HTML-specific widgets, but in fact you can use any
name, and an HTML element will be created with the corresponding name.
Also, case does not matter.

Html widgets inherit from Widget, so you can use e.g. mouse events as
usual. Widgets/elements can also be nested using the ``with`` statement 
as usual.

Unlike normal Flexx widgets, Html widgets do not come with any default
styling, i.e. they act/lool like common HTML elements. Elements can
be styled either using their ``style`` property, or by providing CSS
and using the ``css_class`` property.

A programmer can build content using these html widgets (as in list 1),
or embed plain HTML inside one such widget (as in list 2). In the
first approach the widgets can still be used in the Flexx way, but the
second approach is a bit "lighter" (e.g. the elements don't have a
representation on the Python side).

Widgets programmed in this way are widgets like any other and can
naturally be embedded in a larger Flexx application. This makes it
possible to mix styles depending on needs or programmer preferences.
"""

from flexx import app, event, ui

window = None  # fool pyflakes
html = ui.html  # shorthand

LIPSUM = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex
ea commodo consequat. Duis aute irure dolor in reprehenderit in
voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur
sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
mollit anim id est laborum.
"""


class Example(ui.Widget):
    
    CSS = """
    .flx-Example {
        overflow: auto;  /* make this a scrollable page rather than a desktop look */
    }
    
    .leftimage {
        float: left;
    }
    .leftimage > img {
        width: 200px;
    }
    """
    
    def init(self):
        
        self.im = html.Div(text='<img src="https://github.com/fluidicon.png">',
                           css_class='leftimage')
        self.text = html.Div(text=LIPSUM*10)
        
        # First list, still a bit the "Flexx way"
        html.h1(text='List 1')
        with html.Ul() as self.thelist:
            html.Li(text='Foo')
            html.Li(text='Bar')
            html.Li(text='Spam')
        
        # Second list, let's just embed HTML
        html.h1(text='List 2')
        html.Div(text="""<ul>
                            <li>Foo</li>
                            <li>Bar</li>
                            <li>Spam</li>
                        </ul>""")

    class JS:
        
        @event.connect('text.mouse_down')
        def on_text_clicked(self, *events):
            self.thelist.children[-1].text = window.Date.now()


if __name__ == '__main__':
    m = app.launch(Example, 'browser')
    app.run()
