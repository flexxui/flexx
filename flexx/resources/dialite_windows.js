// https://msdn.microsoft.com/en-us/library/x83z1d9f(v=vs.84).aspx
var timeout = 0;  // no timeout
var type = WScript.arguments(0);
var title = WScript.arguments(1);
var message = WScript.arguments(2);
var sh = new ActiveXObject('WScript.Shell');
var ret = sh.Popup(message, timeout, title, type);
WScript.Echo(ret);
