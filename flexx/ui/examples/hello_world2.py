"""
Hello world that creats an app from a custom Widget.
"""


from flexx import app, ui

class MyApp(ui.Widget):
    def init(self):
        ui.Button(text='Hello world!')

main = app.launch(MyApp)
app.run()
