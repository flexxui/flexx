""" An example that defines two apps, one with a single hbox and
one with hboxes in vboxes in hboxes. For performance testing
"""

import time
import flexx
from flexx import ui


class MyApp1(ui.App):
    
    def init(self):
        
        with ui.HBox():
            ui.Button(text='Box A', flex=0)
            ui.Button(text='Box B', flex=0)
            ui.Button(text='Box C is a bit longer', flex=1)


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
            with ui.Form() as self.form:
                # todo: can this be written with one line per row?
                # e.g. self.b1 = ui.Button(label='Name', text='Hola')
                ui.Label(text='Name:')
                self.b1 = ui.Button(text='Hola')
                ui.Label(text='Age:')
                self.b2 = ui.Button(text='Hello world')
                ui.Label(text='Favorite color:')
                self.b3 = ui.Button(text='Foo bar')
                #ui.Widget(flex=1)
            with ui.Form() as self.form:
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

app = MyApp3(runtime='browser')
ui.run()

#MyApp1.export('/home/almar/dev/pylib/flexx/_website/_static/boxdemo_table1.html')
#MyApp2.export('/home/almar/dev/pylib/flexx/_website/_static/boxdemo_table2.html')
