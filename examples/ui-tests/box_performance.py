""" An example that defines two apps, one with a single hbox and
one with hboxes in vboxes in hboxes. For performance testing
"""

from flexx import ui


class MyApp1(ui.App):
    
    def init(self):
        
        with ui.VBox() as self.l1:
            ui.Button(text='Box A', flex=0)
            ui.Button(text='Box B', flex=0)
            ui.Button(text='Box C is a bit longer', flex=0)


class MyApp2(ui.App):
    
    def init(self):
        
        with ui.HBox():
            
            with ui.VBox():
                
                with ui.HBox(flex=1):
                    ui.Button(text='Box A', flex=0)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=0)
                with ui.HBox(flex=0):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=1)
                    ui.Button(text='Box C is a bit longer', flex=1)
                with ui.HBox(flex=1):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=2)
                with ui.HBox(flex=2):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=2)
                    ui.Button(text='Box C is a bit longer', flex=3)
            
            with ui.VBox():
                
                with ui.HBox(flex=1):
                    ui.Button(text='Box A', flex=0)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=0)
                with ui.HBox(flex=0):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=1)
                    ui.Button(text='Box C is a bit longer', flex=1)
                with ui.HBox(flex=1):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=2)
                with ui.HBox(flex=2):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=2)
                    ui.Button(text='Box C is a bit longer', flex=3)


class MyApp3(ui.App):
    
    def init(self):
        with ui.HBox(spacing=20):
            with ui.FormLayout() as self.form:
                # todo: can this be written with one line per row?
                # e.g. self.b1 = ui.Button(label='Name', text='Hola')
                ui.Label(text='Name:')
                self.b1 = ui.Button(text='Hola')
                ui.Label(text='Age:')
                self.b2 = ui.Button(text='Hello world')
                ui.Label(text='Favorite color:')
                self.b3 = ui.Button(text='Foo bar')
                #ui.Widget(flex=1)
            with ui.FormLayout() as self.form:
                # e.g. self.b1 = ui.Button(label='Name', text='Hola')
                ui.Widget(flex=1)  # Add a flexer
                ui.Widget()
                ui.Label(text='Pet name:')
                self.b1 = ui.Button(text='Hola')
                ui.Label(text='Pet Age:')
                self.b2 = ui.Button(text='Hello world')
                ui.Label(text='Pet\'s Favorite color:')
                self.b3 = ui.Button(text='Foo bar')
                ui.Widget(flex=2)

class MyApp4(ui.App):
    def init(self):
        with ui.PinboardLayout():
            self.b1 = ui.Button(text='Stuck at (20, 20)', pos=(20, 30))
            self.b2 = ui.Button(text='Dynamic at (20%, 20%)', pos=(0.2, 0.2))
            self.b3 = ui.Button(text='Dynamic at (50%, 70%)', pos=(0.5, 0.7))


class MyApp5(ui.App):
    def init(self):
        with ui.HSplitter() as self.l1:
            ui.Button(text='Right A')
            with ui.VSplitter() as self.l2:
                ui.Button(text='Right B')
                ui.Button(text='Right C')
                ui.Button(text='Right D')


class MyApp6(ui.App):
        def init(self):
            layout = ui.PlotLayout()
            layout.add_tools('Edit plot',
                                ui.Button(text='do this'),
                                ui.Button(text='do that'))
            layout.add_tools('Plot info', 
                                ui.ProgressBar(value='0.3'),
                                ui.Label(text='The plot aint pretty'))

app = MyApp1(runtime='browser')
ui.run()

#MyApp1.export('/home/almar/dev/pylib/flexx/_website/_static/boxdemo_table1.html')
#MyApp2.export('/home/almar/dev/pylib/flexx/_website/_static/boxdemo_table2.html')
