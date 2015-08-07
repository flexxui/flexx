from flexx import ui, app

@app.make_app(title='Sinoid plot')
class App(ui.Widget):
    def init(self):
        layout = ui.PlotLayout()
        layout.add_tools('Edit plot', 
                            ui.Button(text='do this'),
                            ui.Button(text='do that'))
        layout.add_tools('Plot info', 
                            ui.Label(text='Sinoid phase'),
                            ui.ProgressBar(value='0.3'))

m = App.launch('firefox')
