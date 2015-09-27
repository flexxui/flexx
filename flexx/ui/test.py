import time
import logging

import flexx
from flexx import app, ui

import faulthandler
faulthandler.enable()
#logging.log


class MyApp(ui.Widget):
    
    #_config = ui.App.Config(title='Flexx test app', size=(400, 300),
    #                        )#icon='https://assets-cdn.github.com/favicon.ico')
               
    def init(self):
        
        #self.b0 = ui.Button(self, 'This is behind the box layout')
        
        TEST = 6
        
        if TEST == 0:
            ui.Button(text='Hola', flex=1)
            
        if TEST == 1:
            with ui.HBox(flex=1) as self.hbox1:
                self.b1 = ui.Widget(flex=1, style='background: #a22; min-width:100px; max-width:500px')
                self.b2 = ui.Widget(flex=0, style='background: #2a2; min-width:100px; max-width:500px')
                self.b3 = ui.Widget(flex=0, style='background: #22a; min-width:100px; max-width:500px')
                self.b4 = ui.Widget(flex=1, style='background: #aaa; min-width:100px; max-width:500px')
        
        if TEST == 2:
            with self:
                with ui.HBox():
                    ui.Widget(flex=1)
                    
                    with ui.VBox(flex=1) as self.vbox:
                        
                        ui.Label(text='Flex 0 0 0', flex=0)
                        with ui.HBox(flex=0) as self.hbox1:
                            self.b1 = ui.Button(text='Hola', flex=0)
                            self.b2 = ui.Button(text='Hello world', flex=0)
                            self.b3 = ui.Button(text='Foo bar', flex=0)
                        
                        ui.Label(text='Flex 1 0 3', flex=0)
                        with ui.HBox(flex=0) as self.hbox2:
                            self.b1 = ui.Button(text='Hola', flex=1)
                            self.b2 = ui.Button(text='Hello world', flex=0)
                            self.b3 = ui.Button(text='Foo bar', flex=3)
                        
                        ui.Label(text='margin 10 (around layout)', flex=0)
                        with ui.HBox(flex=0, margin=10) as self.hbox3:
                            self.b1 = ui.Button(text='Hola', flex=1)
                            self.b2 = ui.Button(text='Hello world', flex=1)
                            self.b3 = ui.Button(text='Foo bar', flex=1)
                        
                        ui.Label(text='spacing 10 (inter-widget)', flex=0)
                        with ui.HBox(flex=0, spacing=10) as self.hbox3:
                            self.b1 = ui.Button(text='Hola', flex=1)
                            self.b2 = ui.Button(text='Hello world', flex=1)
                            self.b3 = ui.Button(text='Foo bar', flex=1)
                        
                        ui.Widget(flex=1)
                        ui.Label(text='Note the spacer Widget above', flex=0)
        
        if TEST == 3:
            with ui.HBox(spacing=20):
                with ui.FormLayout() as self.form:
                    # todo: can this be written with one line per row?
                    # e.g. self.b1 = ui.Button(label='Name', text='Hola')
                    self.b1 = ui.Button(title='Name:', text='Hola')
                    self.b2 = ui.Button(title='Age:', text='Hello world')
                    self.b3 = ui.Button(title='Favorite color:', text='Foo bar')
                with ui.FormLayout() as self.form:
                    # e.g. self.b1 = ui.Button(label='Name', text='Hola')
                    ui.Widget(flex=1)  # Add a flexer
                    self.b1 = ui.Button(title='Name:', text='Hola')
                    self.b2 = ui.Button(title='Age:', text='Hello world')
                    self.b3 = ui.Button(title='Favorite color:', text='Foo bar')
                    ui.Widget(flex=1)
        if TEST == 4:
            with ui.GridLayout(self) as self.grid:
                self.b1 = ui.Button(text='No flex', pos=(0, 0))
                self.b2 = ui.Button(text='Hola', pos=(1, 1), flex=(1, 1))
                self.b3 = ui.Button(text='Hello world', pos=(2, 2), flex=(2, 1))
                self.b4 = ui.Button(text='Foo bar', pos=(4, 4), flex=(1, 2))
                self.b5 = ui.Button(text='no flex again', pos=(5, 5))
        
        if TEST == 5:
            with ui.Splitter():
                ui.Widget(style='background:#aaa;')
                with ui.PinboardLayout() as self.grid:
                    self.b1 = ui.Button(text='Stuck at (20, 20)', pos=(20, 30))
                    self.b2 = ui.Button(text='Dynamic at (20%, 20%)', pos=(0.2, 0.2))
                    self.b3 = ui.Button(text='Dynamic at (50%, 70%)', pos=(0.5, 0.7))
                    with ui.DockLayout(pos=(0.5, 0.5), size=(0.3, 0.3)) as self.d:
                        self.a = ui.Widget(style='background:#a00;')
                        self.b = ui.Widget(style='background:#0a0;')
                        self.c = ui.Widget(style='background:#00a;')
        
        if TEST == 6:
            with ui.HSplitter():
                self.a = ui.Button(text='Right A', min_size=(120, 0))
                self.b = ui.Button(text='Right B', min_size=(70, 0))
                with ui.VSplitter():
                    self.c = ui.Button(text='Right C')
                    self.d = ui.Button(text='Right D')
                    with ui.DockLayout():
                        ui.Slider(title='slider')
                        ui.LineEdit(title='edit', text='AAA')
                        self.g = ui.ProgressBar(title='progress', value=0.4)
    
        if TEST == 7:
            with ui.HBox(self):
                ui.Button(text='Button in hbox', flex=0)
                with ui.HSplit(flex=1):
                    ui.Button(text='Button in splitter', min_size=(100, 0))
                    with ui.HBox(min_size=(100, 0)):
                        ui.Button(text='Right A', flex=0, css='background:#f00; padding:2em;')
                        ui.Button(text='Right B', flex=1)
                        ui.Button(text='Right C', flex=2)
        
        if TEST == 8:
            with ui.MenuBar(self):
                with ui.MenuItem(text='File'):
                    ui.MenuItem(text='New')
                    ui.MenuItem(text='Open')
                    ui.MenuItem(text='Save')
                with ui.MenuItem(text='Edit'):
                    ui.MenuItem(text='Cut')
                    ui.MenuItem(text='Copy')
                    ui.MenuItem(text='Paste')
        
        if TEST == 9:
            with ui.VBox():
                ui.Button(text='AAA', flex=0)
                with ui.HSplitter(flex=1):
                    ui.Button(text='CCC')
                    ui.Button(text='DDD')
                    self.e = ui.Button(text='EEE')
                ui.Button(text='BBB', flex=1)
                         
        if TEST == 10:
            with ui.TabLayout():
                self.a = ui.Widget(title='red', style='background:#a00;')
                self.b = ui.Widget(title='green', style='background:#0a0;')
                self.c = ui.Widget(title='blue', style='background:#00a;')
        #self.win = ui.Window(self, 'A new window!')



a = app.launch(MyApp, 'firefox')
app.start()
# app.b1.set_text('asdasd')

# MyApp.export('/home/almar/test.html')
