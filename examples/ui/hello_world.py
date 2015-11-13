"""
Simple hello world that does not explicitly create an app, making the
button appear in the "default" app. Convenient for interactive use.

This does currently not work anymore. We might enable creating widget
elements like this again, but for now, it would need to be associated
with a session explicitly.
"""

from flexx import app, ui

b = ui.Button(text='Hello world!')

app.run()
