import zoof
from zoof import ui

def keep_alive():
    __iep__.process_commands()
    app.call_later(0.1, keep_alive)

app = ui.App(runtime='browser')

b = ui.Button(app, 'Foo')


# Run
keep_alive()
app.start()
