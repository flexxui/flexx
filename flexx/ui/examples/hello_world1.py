"""
Simple hello world that demonstrates an interactive style for writing
simple apps. An empty widget is launched as an app, and other widgets
are added to it.

In an environment that runs the Tornado event loop in the REPL (e.g.
the Jupyter notebook or Pyzo) one can add and remove widgets
interactively.
"""

from flexx import app, ui

m = app.launch(ui.Widget)  # Main widget

b1 = ui.Button(text='Hello', parent=m)
b2 = ui.Button(text='world', parent=m)

app.run()
