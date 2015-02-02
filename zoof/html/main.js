/*
    Main script for zoof.js
*/

var lastmsg;
var ws;

window.addEventListener('load', initZoof, false);

function initZoof() {
    initSocket();
    initLogging();
}


function initSocket() {
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
        } else if (msg.search('TITLE ') === 0) {
            document.title = msg.slice(6);
        } else if (msg.search('ICON ') === 0) {
            var link = document.createElement('link');
            link.rel = 'icon';
            link.href = msg.slice(5);
            document.getElementsByTagName('head')[0].appendChild(link);
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
}


function initLogging() {
    // Keep originals
    console._log = console.log;
    console._info = console.info || console.log;
    console._warn = console.warn || console.log;
    
    // Set new functions
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
    
    // Create error handlers, so that JS errors get into Python
    window.addEventListener('error', errorHandler, false);
    
    function errorHandler (ev){
        // ev: message, url, linenumber
        var intro = "On line " + ev.lineno + " in " + ev.filename + ":";
        ws.send("ERROR " + intro + '\\n    ' + ev.message);
    }
}
