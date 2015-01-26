""" zoof.gui client based serving a web page using tornado.
"""

import tornado.httpserver
import tornado.websocket
import tornado.web

import logging

HTML = """
<!doctype html>
<html>
<head>
    <title>WebSockets Hello World</title>
</head>

<body>

<style type="text/css">
    body {
    text-align: center;
    min-width: 500px;
    }
</style>
    
<script>
var lastmsg;
var ws;

document.body.onload = function () {
    
    // Send log messages to the server
    console._log = console.log;
    console._info = console.info || console.log;
    console._warn = console.warn || console.log;
    
    console.log = function (msg) {
        console._log(msg);
        ws.send("INFO " + msg);
    };
    console.info = function (msg) {
        console._info(msg);
        ws.send("INFO " + msg);
    };
    console.warn = function (msg) {
        console._warn(msg);
        ws.send("WARN " + msg);
    };
    window.addEventListener('error', errorHandler, false);
    
    function errorHandler (ev){
        // ev: message, url, linenumber
        var intro = "On line " + ev.lineno + " in " + ev.filename + ":";
        ws.send("ERROR " + intro + '\\n    ' + ev.message);
    }
    
    // Open web socket in binary mode
    var loc = location;
    ws = new WebSocket("ws://" + loc.hostname + ':' + loc.port + "/ws");
    ws.binaryType = "arraybuffer";
    
    ws.onmessage = function(evt) {
        var log = document.getElementById('log');
        lastmsg = evt.data;
        var msg = decodeUtf8(evt.data);
        if (msg.search('EVAL ') === 0) {
            window._ = eval(msg.slice(5));  // eval
            ws.send('RET ' + window._);  // send back result
        } else if (msg.search('OPEN ') === 0) {
            window.win1 = window.open(msg.slice(5), 'new', 'chrome');
        } else {
            log.innerHTML += msg + "<br />";
        }
    };
    
    ws.onclose = function(evt) {
        document.body.innerHTML = 'Lost connection with GUI server'
    };
    
    ws.onopen = function(evt) {
        var log = document.getElementById('log');
        log.innerHTML += 'Socket connected' + "<br />";
    };
    
    ws.onerror = function(evt) {
        var log = document.getElementById('log');
        log.innerHTML += 'Socket error' + evt.error + "<br />";
    };
    
    document.getElementById('send').onclick = function(evt) {
        var msg = document.getElementById('msg').value;
        ws.send(msg)
    };       

};

function decodeUtf8(arrayBuffer) {
  var result = "";
  var i = 0;
  var c = 0;
  var c1 = 0;
  var c2 = 0;

  var data = new Uint8Array(arrayBuffer);

  // If we have a BOM skip it
  if (data.length >= 3 && data[0] === 0xef && data[1] === 0xbb && data[2] === 0xbf) {
    i = 3;
  }

  while (i < data.length) {
    c = data[i];

    if (c < 128) {
      result += String.fromCharCode(c);
      i++;
    } else if (c > 191 && c < 224) {
      if( i+1 >= data.length ) {
        throw "UTF-8 Decode failed. Two byte character was truncated.";
      }
      c2 = data[i+1];
      result += String.fromCharCode( ((c&31)<<6) | (c2&63) );
      i += 2;
    } else {
      if (i+2 >= data.length) {
        throw "UTF-8 Decode failed. Multi byte character was truncated.";
      }
      c2 = data[i+1];
      c3 = data[i+2];
      result += String.fromCharCode( ((c&15)<<12) | ((c2&63)<<6) | (c3&63) );
      i += 3;
    }
  }
  return result;
};


</script>

<h1>WebSockets Hello World</h1>
<div>
    <input type="text" id="msg" value="message">
    <input type="submit" id="send" value="send" /><br />
    <div id="log"> LOG:<br><br></div>
</div>
</body>
</html>
""".lstrip()


class TornadoApplication(tornado.web.Application):
    """ We have one tornado application per Zoof application. I think.
    We'll have to see how we'll deal with multiple windows later.
    
    Each application can have multiple sockets. I think. Maybe we should
    limit it to exactly one. In any case, we must ensure a consistent
    state between server and client.
    
    The purpose of this subclass is to provide a central part where we
    keep track of the web socket objects. So that these, and the main handler
    can act accordingly.
    """
    
    def __init__(self):
        tornado.web.Application.__init__(self,
            [(r'/ws', WSHandler), (r"/(.*)", MainHandler), ])
        
        self._sockets = []
    
    def register_socket(self, s):
        self._sockets.append(s)
    
    def write_message(self, msg):
        for s in self._sockets:
            s.write_message(msg, binary=True)


class MainHandler(tornado.web.RequestHandler):
    """ Handler for http requests: server pages
    """
    def initialize(self, **kwargs):
        print('init request')
    
    def get(self, path=None):
        print('get', path)
        if self.application._sockets:
            self.write('Connection already claimed')
        else:
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
    """ Handler for websocket.
    """
    
    # https://tools.ietf.org/html/rfc6455#section-7.4.1
    known_reasons = {1000: 'client done', 
                     1001: 'client closed', 
                     1002: 'protocol error', 
                     1003: 'could not accept data',
                     }
    
    # todo: use ping() and close()
    def open(self):
        """ Called when a new connection is made.
        """
        print('new ws connection')
        self.write_message("Hello World", binary=True)
        
        self.application.register_socket(self)
        # Don't collect messages to send them more efficiently, just send asap
        self.set_nodelay(True)
    
    def on_message(self, message):
        """ Called when a new message is received from JS.
        
        We now have a very basic protocol for receiving messages,
        we should at some point define a real formalized protocol.
        """
        
        if message.startswith('RET '):
            print(message[4:])  # Return value
        elif message.startswith('ERROR '):
            logging.error('JS - ' + message[6:].strip())
        elif message.startswith('WARN '):
            logging.warn('JS - ' + message[5:].strip())
        elif message.startswith('INFO '):
            logging.info('JS - ' + message[5:].strip())
        else:
            print('message received %s' % message)
            self.write_message('echo ' + message, binary=True)
 
    def on_close(self):
        """ Called when the connection is closed.
        """
        code = self.close_code or 0
        reason = self.close_reason or self.known_reasons.get(code, '')
        print('detected close: %s (%i)' % (reason, code))
    
    def close_this(self):
        """ We can call this to close the websocket
        """
        self.close(1000, 'closed by server')
    
    def on_pong(self, data):
        """ Called when our ping is returned.
        """
        print('PONG', data)
    
    # Uncomment this to allow cross-domain access
    #def check_origin(self, origin):
    #    return True


 
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
    
