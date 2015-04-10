""" An example that defines two apps, one with a single hbox and
one with hboxes in vboxes in hboxes. For performance testing
"""

import time
import flexx
from flexx import ui


class MyApp1(ui.App):
    
    def init(self):
        
        with ui.HBox(self):
            ui.Button(text='Box A', flex=0)
            ui.Button(text='Box B', flex=0)
            ui.Button(text='Box C is a bit longer', flex=0)


class MyApp2(ui.App):
    
    def init(self):
        
        with ui.HBox(self):
            
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


app = MyApp1()
ui.run()

#MyApp1.export('/home/almar/dev/pylib/flexx/_website/_static/boxdemo_table1.html')
#MyApp2.export('/home/almar/dev/pylib/flexx/_website/_static/boxdemo_table2.html')
