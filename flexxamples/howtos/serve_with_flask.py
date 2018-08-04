"""
Example of serving a Flexx app using a regular web server. In this case flask.
See serve_with_aiohttp.py for a slightly more advanced example.
"""

from flask import Flask

from flexx import flx
from flexxamples.howtos.editor_cm import CodeEditor

# Define an app

class MyApp(flx.Widget):
    def init(self):
        with flx.HBox():
            CodeEditor(flex=1)
            flx.Widget(flex=1)


# Dump it to a dictionary of assets that we can serve. Make the main
# page index.html. The link=0 means to pack the whole app into a single
# html page (note that data (e.g. images) will still be separate).
app = flx.App(MyApp)
assets = app.dump('index.html', link=0)


# Do the flask thing

app = Flask(__name__)

@app.route('/')
def handler():
    return assets['index.html'].decode()


if __name__ == '__main__':
    app.run(host='localhost', port=8080)
