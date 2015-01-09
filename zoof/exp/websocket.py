"""
Combine this with the websockt hello world in the sandbox.
"""
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import webbrowser

HTML = """
<!doctype html>
<html>
  <head>
    <title>WebSockets Hello World</title>
    <meta charset="utf-8" />
    <style type="text/css">
      body {
        text-align: center;
        min-width: 500px;
      }
    </style>
    <script src="http://code.jquery.com/jquery.min.js"></script>
    <script>
      $(document).ready(function () {
        
        var ws;
        
        ws = new WebSocket("ws://localhost:8888/ws");

        //s.onmessage = function(evt) {alert("message received: " + evt.data)};
        ws.onmessage = function(evt) {
            var cur = $("#log").html();
            $("#log").html(cur + evt.data + "<br />");
        };
        
        ws.onclose = function(evt) {
            var cur = $("#log").html();
            $("#log").html(cur + 'Socket closed' + "<br />");
        };
        
        ws.onopen =  function(evt) {
            var cur = $("#log").html();
            $("#log").html(cur + 'Socket connected' + "<br />");
        };
        
        $("#send").click(function(evt) {
          var msg = $("#msg").val();
          ws.send(msg)
        });       
 
      });
    </script>
  </head>
 
  <body>
    <h1>WebSockets Hello World</h1>
    <div>
      <input type="text" id="msg" value="message">
      <input type="submit" id="send" value="send" /><br />
     <div id="log"> LOG:<br><br></div>
    </div>
  </body>
</html>
"""


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, **kwargs):
        print('init request')
    
    def get(self, path=None):
        print('get', path)
        self.write(HTML)
    
    def write_error(self, status_code, **kwargs):
        # does not work?
        print(repr(status_code))
        if status_code == 404:
            self.write('zoof.gui wants you to connect to root (404)')
        else:
            super().write_error(status_code, **kwargs)
    
    def on_finish(self):
        print('finish request')


class WSHandler(tornado.websocket.WebSocketHandler):
    
    _sockets = []  # todo: weakrefs
    
    # https://tools.ietf.org/html/rfc6455#section-7.4.1
    known_reasons = {1000: 'client done', 
                     1001: 'client closed', 
                     1002: 'protocol error', 
                     1003: 'could not accept data',
                     }
    
    # todo: use ping() and close()
    def open(self):
        print('new ws connection')
        self.write_message("Hello World")
        
        self._sockets.append(self)
        # Don't collect messages to send them more efficiently, just send asap
        self.set_nodelay(True)
    
    def on_message(self, message):
        print('message received %s' % message)
        self.write_message('echo ' + message)
 
    def on_close(self):
        code = self.close_code or 0
        reason = self.close_reason or self.known_reasons.get(code, '')
        print('detected close: %s (%i)' % (reason, code))
    
    def close_this(self):
        self.close(1000, 'closed by server')
    
    def on_pong(self, data):
        print('PONG', data)
    
    # Uncomment this to allow cross-domain access
    #def check_origin(self, origin):
    #    return True


application = tornado.web.Application([
    (r'/ws', WSHandler),
    (r"/(.*)", MainHandler),
])
 
 
if __name__ == "__main__":
    #http_server = tornado.httpserver.HTTPServer(application)
    #http_server.listen(8888)
    
    application.listen(8888)
    
    webbrowser.open('http://localhost:8888')
    
    # Start the main loop (http://www.tornadoweb.org/en/stable/ioloop.html)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.instance().start()
    ioloop.run_sync(lambda x=None: None)  # == process_events
    
    # Also see ioloop.call_later() and ioloop.add_callback()
    
