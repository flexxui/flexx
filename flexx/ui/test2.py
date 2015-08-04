# todo: Get app sorted out (incl. via IPython)
# todo: make it work when methods are js-ed
# todo: callbacks, back and forth

"""

## ===== Plug-n-play mode =====
from flexx import ui
ui.HBox(children=[ui.Button(), ui.Button()])
ui.run()
# Launches browser with singleton default app. Allows just one connection.
# When in Jupyter, will run there.

## ===== Web app mode =====
from flexx import ui
class MyApp(ui.App):
    def init(self):
        with ui.HBox():
            ui.Button()
            ui.Button()
app = MyApp(runtime='xul')
ui.run()
# Hosts the app. One MyApp gets instantiated per connection
# The explicitly created app instance gets "tied" to a runtime of our choice

## ===== Hybrid mode =====
from flexx import ui
class MyApp(ui.App):
    ...
ui.HBox(children=[ui.Button(), ui.Button()])
ui.run()
# Hosts MyApp as before. The plain HBox ends up in the default app.

"""
##

import flexx
from flexx import ui


@ui.app(title='My app, new style!')
class Main(ui.Widget):
    
    def init(self):
        with ui.HBox() as self._hbox:
            self._b1 = ui.Button(text='Foo', flex=1)
            self._b2 = ui.Button(text='Bar', flex=2)


# client=Client(runtime='xul')  # Users should not have to care about client
# m = Main.launch(runtime='xul')  # pollute all widgets with extra name

m = Main.launch(runtime='firefox')
#m = Main()


# ##
# from flexx import ui
# from flexx.pyscript import js
# 
# #b1 = ui.Button(text='foo')
# box = None
# # box = ui.VBox()
# b1 = ui.Button(parent=box, text='Foo', flex=1)
# b2 = ui.Button(parent=box, text='Bar', flex=2)
# ui.run()


