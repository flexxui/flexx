import time
import zoof
from zoof import ui

import faulthandler
faulthandler.enable()

class MyApp(ui.App):
    
    _config = ui.App.Config(title='Zoof test app', size=(400, 300),
                            icon='https://assets-cdn.github.com/favicon.ico')
               
    def init(self):
        
        #self.b0 = ui.Button(self, 'This is behind the box layout')
        
        TEST = 2
        
        if TEST == 1:
            with ui.VBox(self, flex=1) as self.hbox1:
                self.b1 = ui.Button(text='Hola', flex=1)
                self.b2 = ui.Button(text='Hello world', flex=0)
                self.b2 = ui.Button(text='Hello world', flex=0)
                self.b2 = ui.Button(text='Hello world', flex=0)
                self.b3 = ui.Button(text='Foo bar', flex=1)
        
        if TEST == 2:
            with self:
                with ui.HBox():
                    ui.Widget(flex=1)
                    
                    with ui.VBox(flex=0) as self.vbox:
                        
                        ui.Label(text='Flex 0 0 0', flex=0)
                        with ui.HBox(flex=0) as self.hbox2:
                            self.b1 = ui.Button(text='Hola', flex=0)
                            self.b2 = ui.Button(text='Hello world', flex=0)
                            self.b3 = ui.Button(text='Foo bar', flex=0)
                        
                        ui.Label(text='Flex 1 0 3', flex=0)
                        with ui.HBox(flex=0) as self.hbox1:
                            self.b1 = ui.Button(text='Hola', flex=1)
                            self.b2 = ui.Button(text='Hello world', flex=0)
                            self.b3 = ui.Button(text='Foo bar', flex=3)
                        
                        ui.Label(text='margin 10 (around layout)', flex=0)
                        with ui.HBox(flex=0, margin=10) as self.hbox2:
                            self.b1 = ui.Button(text='Hola', flex=0)
                            self.b2 = ui.Button(text='Hello world', flex=0)
                            self.b3 = ui.Button(text='Foo bar', flex=0)
                        
                        ui.Label(text='spacing 10 (inter-widget)', flex=0)
                        with ui.HBox(flex=0, spacing=10) as self.hbox2:
                            self.b1 = ui.Button(text='Hola', flex=0)
                            self.b2 = ui.Button(text='Hello world', flex=0)
                            self.b3 = ui.Button(text='Foo bar', flex=0)
                        
                        ui.Widget(flex=1)
                        ui.Label(text='Note the spacer Widget above', flex=0)
        
        if TEST == 3:
            with ui.HBox(self, spacing=20):
                with ui.Form() as self.form:
                    # todo: can this be written with one line per row?
                    # e.g. self.b1 = ui.Button(label='Name', text='Hola')
                    ui.Label(text='Name:')
                    self.b1 = ui.Button(text='Hola')
                    ui.Label(text='Age:')
                    self.b2 = ui.Button(text='Hello world')
                    ui.Label(text='Favorite color:')
                    self.b3 = ui.Button(text='Foo bar')
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
                    ui.Widget(flex=1)
        if TEST == 4:
            with ui.Grid(self) as self.grid:
                self.b1 = ui.Button(text='No flex', pos=(0, 0))
                self.b2 = ui.Button(text='Hola', pos=(1, 1), flex=(1, 1))
                self.b3 = ui.Button(text='Hello world', pos=(2, 2), flex=(2, 1))
                self.b4 = ui.Button(text='Foo bar', pos=(4, 4), flex=(1, 2))
                self.b5 = ui.Button(text='no flex again', pos=(5, 5))
        
        if TEST == 5:
            with ui.PinBoard(self) as self.grid:
                self.b1 = ui.Button(text='Stuck at (20, 20)', pos=(20, 30))
                self.b2 = ui.Button(text='Dynamic at (20%, 20%)', pos=(0.2, 0.2))
                self.b3 = ui.Button(text='Dynamic at (50%, 70%)', pos=(0.5, 0.7))
        
        if TEST == 6:
            with ui.HSplit(self):
                ui.Button(text='Right A', min_width=120)
                ui.Button(text='Right B', min_width=70)
                ui.Button(text='Right C')
                # ui.Button(text='Right D', flex=2)
                # ui.Button(text='Right E', flex=2)
                # ui.Button(text='Right F', flex=2)
    
        if TEST == 7:
            with ui.HBox(self):
                ui.Button(text='Button in hbox', flex=0)
                with ui.HSplit(flex=1):
                    ui.Button(text='Button in splitter', min_width=100)
                    with ui.HBox(min_width=100):
                        ui.Button(text='Right A', flex=0, css='background:#f00; padding:2em;')
                        ui.Button(text='Right B', flex=1)
                        ui.Button(text='Right C', flex=2)
                
        #self.win = ui.Window(self, 'A new window!')


class MyApp2(ui.App):
    def init(self):
        self.b = ui.Button(self, 'Hello world')


app = MyApp('xul')
ui.run()
# app.b1.set_text('asdasd')

# MyApp.export('/home/almar/test.html')
