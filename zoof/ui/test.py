import zoof
from zoof import ui

def keep_alive():
    __iep__.process_commands()
    ui.call_later(0.1, keep_alive)



class MyApp(ui.App):
    
    _config = ui.App.Config(title='Zoof test app', size=(400, 300),
                            icon='https://assets-cdn.github.com/favicon.ico')
               
    def init(self):
        
        #self.b0 = ui.Button(self, 'This is behind the box layout')
        
        TEST = 2
        
        if TEST == 1:
            with ui.HBox(self, flex=1) as self.hbox1:
                self.b1 = ui.Button(text='Hola', flex=1)
                self.b2 = ui.Button(text='Hello world', flex=0)
                self.b3 = ui.Button(text='Foo bar', flex=3)
        
        if TEST == 2:
            with ui.VBox(self) as self.vbox:
                
                ui.Button(text='Flex 0 0 0', flex=0)
                with ui.HBox(flex=0) as self.hbox2:
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Button(text='Flex 1 0 3', flex=0)
                with ui.HBox(flex=0) as self.hbox1:
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=3)
                
                ui.Button(text='margin 10 (around layout)', flex=0)
                with ui.HBox(flex=0, margin=10) as self.hbox2:
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Button(text='spacing 10 (inter-widget)', flex=0)
                with ui.HBox(flex=0, spacing=10) as self.hbox2:
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Button(text='-- stretch --', flex=1)
        #self.win = ui.Window(self, 'A new window!')
        
# class MyApp2(ui.App):
#     def init(self):
#         self.b = ui.Button(self, 'Hello world')

app = MyApp()
keep_alive()
ui.run(runtime='xul')
