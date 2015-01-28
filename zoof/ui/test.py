import zoof
from zoof import ui

def keep_alive():
    __iep__.process_commands()
    ui.call_later(0.1, keep_alive)


class MyApp(ui.App):
    def init(self):
        self.b = ui.Button(self, 'Hello world')
        self.win = ui.Window(self, 'A new window!')

# class MyApp2(ui.App):
#     def init(self):
#         self.b = ui.Button(self, 'Hello world')

app = MyApp()
keep_alive()
ui.run(runtime='xul')
