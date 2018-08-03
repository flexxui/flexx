"""
Example that demonstrates how to add cusom Tornado handlers, for
instance to serve a custom HTML page, or a (REST) api from the same
process.

For the sake of the example, we alo serve two example web apps.

Goto:

* http://localhost:port/ to see a list of served web apps
* http://localhost:port/about to see a the custom about page
* http://localhost:port/api/foo/bar to see the echo api in action


"""

from flexx import flx
from flexxamples.demos.drawing import Drawing
from flexxamples.demos.chatroom import ChatRoom

import tornado.web

# Serve some web apps, just for fun
flx.serve(Drawing)
flx.serve(ChatRoom)


class MyAboutHandler(tornado.web.RequestHandler):

    def get(self):
        self.write('<html>This is just an <i>example</i>.</html>')


class MyAPIHandler(tornado.web.RequestHandler):

    def get(self, path):
        # self.request.path -> full path
        # path -> the regexp group specified in add_handlers
        self.write('echo ' + path)


# Get a ref to the tornado.web.Application object
tornado_app = flx.current_server().app

# Add our handler
tornado_app.add_handlers(r".*", [(r"/about", MyAboutHandler),
                                 (r"/api/(.*)", MyAPIHandler)])

# Note: Tornado tries to match handlers in order, but the handlers
# specified in the constructor come last. Therefore we can easily add
# specific handlers here even though Flexx' main handler is very
# generic.

flx.start()
