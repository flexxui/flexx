from flexx import app, ui

class MyApp(ui.Widget):
    def init(self):
        self.b = ui.Button(text='Hello world!')

app.launch(MyApp)
app.start()
