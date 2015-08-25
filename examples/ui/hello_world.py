"""
Simple hello world that does not explicitly create an app, making the
button appear in the "default" app. Convenient for interactive use.
"""

from flexx import app, ui

b = ui.Button(text='Hello world!')

app.start()
