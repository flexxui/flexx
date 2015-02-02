import zoof
from zoof import ui

def keep_alive():
    __iep__.process_commands()
    ui.call_later(0.1, keep_alive)


class MyApp(ui.App):
    def init(self):
        self.title = 'Zoof test app'
        self.add_icon('/home/almar/projects/pyapps/iep/default/iep/resources/appicons/ieplogo.ico')
        
        self.b0 = ui.Button(self, 'Hello world foo bar')
        
        self.layout = ui.HBoxLayout(self)
        self.b1 = ui.Button(self.layout, 'Hola', flex=1)
        self.b2 = ui.Button(self.layout, 'Hello world', flex=0)
        self.b3 = ui.Button(self.layout, 'Foo bar', flex=3)
        self.layout.update()  # would be auto-called when used in context
        
        #self.win = ui.Window(self, 'A new window!')

# class MyApp2(ui.App):
#     def init(self):
#         self.b = ui.Button(self, 'Hello world')

app = MyApp()
keep_alive()
ui.run(runtime='xul')
