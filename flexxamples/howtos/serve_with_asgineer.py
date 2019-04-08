"""
Example of serving a Flexx app using a regular web server. In this case Asgineer.
https://github.com/almarklein/asgineer
"""

import asgineer

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


# Do the Asgineer thing. Use make_asset_handler() for a solid and
# lightning fast way to serve assets from memory (it includes HTTP
# caching and compression).

asset_handler = asgineer.utils.make_asset_handler(assets)

@asgineer.to_asgi
async def main_handler(request):
    return await asset_handler(request)


if __name__ == '__main__':
    asgineer.run(main_handler, "uvicorn", "localhost:8080")
