from flexx import ui

class MyApp(ui.App):
    def init(self):
        self.b = ui.Button(self, 'Hello world!')

ui.run()
