import zoof
from zoof import ui

def keep_alive():
    __iep__.process_commands()
    ui.call_later(0.1, keep_alive)



class MyApp(ui.App):
    
    _config = ui.App.Config(title='Zoof test app', size=(400, 300),
                            icon='https://assets-cdn.github.com/favicon.ico')
               
    def init(self):
        
        self.b0 = ui.Button(self, 'Hello world foo bar')
        
        with ui.HBoxLayout(self) as self.layout:
            self.b1 = ui.Button(text='Hola', flex=1)
            self.b2 = ui.Button(text='Hello world', flex=0)
            self.b3 = ui.Button(text='Foo bar', flex=3)
        #self.win = ui.Window(self, 'A new window!')

# class MyApp2(ui.App):
#     def init(self):
#         self.b = ui.Button(self, 'Hello world')

app = MyApp()
keep_alive()
ui.run(runtime='xul')
