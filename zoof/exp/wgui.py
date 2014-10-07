""" 
Experiments with the purpose for creating a GUI toolkit based
on web technologies like HTML/CSS/JS.

Applications build with such a GUI can be easily deployed on all platforms
and also run in a web browser...

Usefull links:
* http://www.aclevername.com/articles/python-webgui/

"""

import time

from zoof.qt import QtCore, QtWebKit


HTML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html
      PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:svg="http://www.w3.org/2000/svg"
      xmlns:xlink="http://www.w3.org/1999/xlink">

  <head>

    <title></title>

    <link href="demo.css" rel="stylesheet" type="text/css"></link>
    
    <!-- <script src="jquery-1.11.1.min.js"></script> -->
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>
    <script type="text/javascript">
// <![CDATA[

function send(msg) {
    document.title = "null";
    document.title = msg;
}
// NOTE: jQuery would make this all much cleaner!  You need it!


function got_a_click(e) {
    send('got-a-click:' + e.target.id);
}

function got_a_move(e) {
    if (e.clientX & e.clientY) {
        //send('got-a-move:' + e.target.id);
        send('got-a-move:' + e.target.id + '-' + e.clientX + ',' + e.clientY);
    }
}

/*
function document_ready() {
    send('"document-ready"');
    document.getElementById('messages').addEventListener('click', got_a_click, false);
}
*/

$(document).ready(function() {
     $('#messages').click(got_a_click);
     //send($.toJSON('document.ready'));
     send('document.ready');
})



//document.addEventListener('DOMContentLoaded', document_ready, false);

// ]]>
</script>


  </head>

  <body>

    <h1>Python + Web GUI Demo</h1>

    <h2>Uptime</h2>

    <p class="uptime">
      Python uptime:
      <span id="uptime-value">?</span> seconds.
    </p>

    <h2>Messages</h2>

    <p id="messages">
      Click here (yes, anywhere here)...<br/>
    </p>

  </body>

</html>
"""


class Page(QtWebKit.QWebPage):
    def javaScriptConsoleMessage(self, msg, linenr, sourceID):
        print('ERROR: on line %i in %r: %s' % (linenr, sourceID, msg))
    
    def javaScriptAlert(self, frame, msg):
        print('ALERT:', msg)
    
    def javaScriptConfirm(self, frame, msg):
        while True:
            a = input('Need confirm from JS: msg [Y/n] ')
            if not a or a.lower() == 'y':
                return True
            elif a.lower() == 'n':
                return False

    # def javaScriptPrompt


class Main(QtWebKit.QWebView):
    def __init__(self):
        super().__init__(None)
        
        self.setPage(Page(self))
        self.page().mainFrame().setHtml(HTML)
        
        self.titleChanged.connect(self.on_title_changed)
        
        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self.on_timer)
        self._timer.start(207)
        self._t0 = time.time()
    
    def on_error(self, msg):
        print('ERROR:', msg)
    
    def on_timer(self):
        t = time.time() - self._t0
        msg = 'document.getElementById("uptime-value").innerHTML = %1.01f' % t
        self.web_send(msg)
    
    def web_send(self, msg):
        f = self.page().mainFrame()
        f.evaluateJavaScript(msg)
    
    def on_title_changed(self, title):
        if title == 'null':
            return
        print('MSG:', title)
        if title.startswith("got-a-move:test-widget"):
            xy = title.split('-')[-1]
            x, y = [int(i) for i in xy.split(',')]
            msg =  'document.getElementById("test-widget").style.left = "%ipx";' % x
            msg += 'document.getElementById("test-widget").style.top = "%ipx";' % y
            self.web_send(msg)
            print(title)
            
        if title == "got-a-click:messages":
            #self.web_send("confirm('Please confitm');")
            #self.web_send("alert('wooot');")
            
            self.web_send("""
                        $(document.body).append("<div id='test-widget' class='draggable'>This is a paragraph</div>");
                        $("#test-widget").css({   "width": "100px", 
                                                    "height": "35px",
                                                    "position":"absolute",
                                                    //"display": "none",
                                                    "top":"100px",
                                                    "left":"100px",
                                                    "background": "red",
                                                    "overflow":"hidden",
                                                    "user-select": "none",
                                                    "handle": "",
                                                    "cursor": "move",
                                                });
                        $("#test-widget")._down = false;
                        $("#test-widget").mousedown(function(e){this._down=true});
                        $("#test-widget").mouseup(function(e){this._down=false});
                        $("#test-widget").mousemove(function(e){if (this._down) {got_a_move(e);}});
                        
                        /*
                        $("#test-widget").bind('drag', got_a_move);
                        $("#test-widget").bind('dragstart', function(e){
                            e.preventDefault();
                        });
                        $("#test-widget").bind('dragstart', function(e){
                            e.dataTransfer.setData('text/plain', 'This text may be dragged')
                        });
                        $("#test-widget").bind('drag', function(){
                            alert('moveing');
                        });
                        //$("#test-widget").mousemove(got_a_move);
                        */
                        /*
                        var x = document.createElement("DIV");
                        var t = document.createTextNode("This is a paragraph.");
                        x.appendChild(t);
                        document.body.appendChild(x);
                        x.style.width = '100px';
                        x.style.height = '35px';
                        x.style.position = 'fixed';
                        x.style.top = '100px';
                        x.style.left = '100px';
                        x.style['background'] = 'red';
                        x.style.overflow = 'hidden';
                        x.id = 'test-widget';
                        //x.draggable = true;
                        $.toJSON('asd');
                        $('#test-widget').draggable();
                        //document.getElementById('test-widget').addEventListener('click', got_a_click, false);
                        //x.addEventListener('click', function(){got_a_click(x)}, false);
                        x.addEventListener('click', got_a_click, false);
                        //x.addEventListener('drag', got_a_move, false); // drag mousemove
                        */
                        """)
        
    

if __name__ == '__main__':
    m = Main()
    m.show()
