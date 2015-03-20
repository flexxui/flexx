/*
    Main script for zoof.js
*/

/* JSLint config */
/*global zoof, decodeUtf8 */
/*jslint browser: true, node: true, continue:true */
"use strict";



zoof.init = function () {
    if (zoof.isExported) {
        zoof.runExportedApp();
    } else {
        zoof.initSocket();
        zoof.initLogging();
    }
};


zoof.exit = function () {
    if (zoof.ws) {
        zoof.ws.close();
    }
};


window.addEventListener('load', zoof.init, false);
window.addEventListener('beforeunload', zoof.exit, false);


zoof.command = function (msg) {
    var log, link;
    log = document.getElementById('log');
    if (msg.search('EVAL ') === 0) {
        /*jslint nomen: true, evil: true*/
        window._ = eval(msg.slice(5));
        zoof.ws.send('RET ' + window._);  // send back result

    } else if (msg.search('EXEC ') === 0) {
        /*jslint nomen: true, evil: true*/
        eval(msg.slice(5));  // like eval, but do not return result
        /*jslint nomen: false, evil: false*/
    } else if (msg.search('TITLE ') === 0) {
        document.title = msg.slice(6);
    } else if (msg.search('ICON ') === 0) {
        link = document.createElement('link');
        link.rel = 'icon';
        link.href = msg.slice(5);
        document.getElementsByTagName('head')[0].appendChild(link);
    } else if (msg.search('OPEN ') === 0) {
        window.win1 = window.open(msg.slice(5), 'new', 'chrome');
    } else {
        log.innerHTML += msg + "<br />";
    }
};


zoof.initSocket = function () {
    var loc, url, ws;
    
    zoof.lastmsg = null;
    
    // Check WebSocket support
    if (window.WebSocket === undefined) {
        document.body.innerHTML = 'This browser does not support WebSockets';
        return;
    }
    
    // Open web socket in binary mode
    //loc = location;
    //url = "ws://" + loc.hostname + ':' + loc.port + "/" + loc.pathname + "/ws";
    url = zoof.ws_url;
    ws = new window.WebSocket(url);
    zoof.ws = ws;
    ws.binaryType = "arraybuffer";
    
    ws.onmessage = function (evt) {
        var msg;
        zoof.lastmsg = evt.data;
        msg = decodeUtf8(evt.data);
        zoof.command(msg);
    };
    
    ws.onclose = function (ev) {
        var msg = '';
        msg += 'Lost connection with GUI server: ';
        msg += ev.reason + " (" + ev.code + ")";
        if (zoof.is_full_page) {
            document.body.innerHTML = msg;
        } else {
            console.info(msg);
        }
    };
    
    ws.onopen = function (ev) {
        console.info('Socket connected');
    };
    
    ws.onerror = function (ev) {
        console.error('Socket connected');
    };
};


zoof.initLogging = function () {
    var errorHandler;
    if (console.ori_log) {
        return;  // already initialized the loggers
    }
    // Keep originals
    console.ori_log = console.log;
    console.ori_info = console.info || console.log;
    console.ori_warn = console.warn || console.log;
    
    // Set new functions
    console.log = function (msg) {
        zoof.ws.send("PRINT " + msg);
        console.ori_log(msg);
    };
    console.info = function (msg) {
        zoof.ws.send("INFO " + msg);
        console.ori_info(msg);
    };
    console.warn = function (msg) {
        zoof.ws.send("WARN " + msg);
        console.ori_warn(msg);
    };
    
    // Create error handlers, so that JS errors get into Python
    window.addEventListener('error', errorHandler, false);
    
    errorHandler = function (ev) {
        // ev: message, url, linenumber
        var intro = "On line " + ev.lineno + " in " + ev.filename + ":";
        zoof.ws.send("ERROR " + intro + '\n    ' + ev.message);
    };
};
