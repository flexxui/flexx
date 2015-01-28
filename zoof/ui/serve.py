""" zoof.gui client based serving a web page using tornado.
"""

import logging

import tornado.web
import tornado.websocket

from .app import manager


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
    ws = new WebSocket("ws://" + loc.hostname + ':' + loc.port + "/" + loc.pathname + "/ws");
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
    
    ws.onclose = function(ev) {
        document.body.innerHTML = 'Lost connection with GUI server:<br >';
        document.body.innerHTML += ev.reason + " (" + ev.code + ")";
    };
    
    ws.onopen = function(ev) {
        var log = document.getElementById('log');
        log.innerHTML += 'Socket connected' + "<br />";
    };
    
    ws.onerror = function(ev) {
        var log = document.getElementById('log');
        log.innerHTML += 'Socket error' + ev.error + "<br />";
    };
    
    document.getElementById('send').onclick = function(ev) {
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


class MainHandler(tornado.web.RequestHandler):
    """ Handler for http requests: serve pages
    """
    def initialize(self, **kwargs):
        # kwargs == dict set as third arg in url spec
        # print('init request')
        pass
    
    def get(self, path=None):
        print('get', path)
        if not path:
            self.write('Root selected, apps available: %r' % 
                       manager.get_app_names())
        else:
            app_name = path.split('/')[0]
            if manager.has_app(app_name) and not '/' in path:
                self.write(HTML)
            else:
                #self.write('invalid resource')
                super().write_error(404)
    
    def write_error(self, status_code, **kwargs):
        # does not work?
        print('in write_error', repr(status_code))
        if status_code == 404:
            self.write('zoof.gui wants you to connect to root (404)')
        else:
            self.write('Zoof ui encountered an error: <br /><br />')
            super().write_error(status_code, **kwargs)
    
    def on_finish(self):
        pass  # print('finish request')


class WSHandler(tornado.websocket.WebSocketHandler):
    """ Handler for websocket.
    """
    
    # https://tools.ietf.org/html/rfc6455#section-7.4.1
    known_reasons = {1000: 'client done', 
                     1001: 'client closed', 
                     1002: 'protocol error', 
                     1003: 'could not accept data',
                     }
    
    # --- callbacks
    
    # todo: use ping() and close()
    def open(self, path=None):
        """ Called when a new connection is made.
        """
        # Don't collect messages to send them more efficiently, just send asap
        self.set_nodelay(True)
        
        print('new ws connection', path)
        app_name = path.strip('/')
        if manager.has_app(app_name):
            app = manager.connect_an_app(app_name, self)
            self.write_message("Hello World", binary=True)
        else:
            self.close(1003, "Could not associate socket with an app.")
    
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
    
    def on_pong(self, data):
        """ Called when our ping is returned.
        """
        print('PONG', data)
    
    # --- methdos
    
    def command(self, cmd):
        self.write_message(cmd, binary=True)
    
    def close_this(self):
        """ Call this to close the websocket
        """
        self.close(1000, 'closed by server')
    
    # Uncomment this to allow cross-domain access
    #def check_origin(self, origin):
    #    return True
