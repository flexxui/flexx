from __future__ import print_function, division, absolute_import

import os
import tempfile
import subprocess

from ._base import BaseApp

# Note: confirmed this to work on Windows XP and Windows 10
# Docs: https://msdn.microsoft.com/en-us/library/x83z1d9f(v=vs.84).aspx

script = """
// Script used by the Python package dialite to display simple dialogs
var timeout = 0;  // no timeout
var type = WScript.arguments(0);
var title = WScript.arguments(1);
var message = WScript.arguments(2);
var sh = new ActiveXObject('WScript.Shell');
var ret = sh.Popup(message, timeout, title, type);
WScript.Echo(ret);
""".lstrip()


class WindowsApp(BaseApp):
    """ Implementation of dialogs for Windows, by making use of Windows Script
    Host (cscript.exe), and JScript as the ActiveX language.
    """
    
    def __init__(self, *args, **kwargs):
        BaseApp.__init__(self, *args, **kwargs)
        self._filename = os.path.join(tempfile.gettempdir(), 'dialite_win.js')
        with open(self._filename, 'wb') as f:
            f.write(script.encode())
    
    def fail(self, title, message):
        # 4096 makes it system modal
        self._message(16 + 0 + 4096, title, message)
    
    def warn(self, title, message):
        self._message(48 + 0, title, message)
    
    def inform(self, title, message):
        self._message(64 + 0, title, message)
    
    def verify(self, title, message):
        return self._message(32 + 1, title, message)
    
    def ask(self, title, message):
        return self._message(32 + 4, title, message)
    
    def _message(self, type, title, message):
        message = message.replace('"', '\u201C').replace("'", '\u2018')
        res = subprocess.check_output(['cscript', '//Nologo', self._filename,
                                       str(type), title, message])
        resmap = {'0': False, '1': True, '2': False, '6': True, '7': False}
        return resmap.get(res.decode().strip(), None)
