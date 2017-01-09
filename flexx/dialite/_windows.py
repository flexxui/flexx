import os
import subprocess

from ._base import BaseApp


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
FLEXX_RESOURCES_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', 'resources'))
scriptfile = os.path.join(FLEXX_RESOURCES_DIR, 'dialite_windows.js')

# Note: confirmed this to work on Windows XP and Windows 10


class WindowsApp(BaseApp):
    """ Implementation of dialogs for Windows, by making use of Windows Script
    Host (cscript.exe), and JScript as the ActiveX language.
    """
    
    def fail(self, title, message):
        # 4096 makes it system modal
        return self._message(16 + 0 + 4096, title, message)
    
    def warn(self, title, message):
        return self._message(48 + 0, title, message)
    
    def inform(self, title, message):
        return self._message(64 + 0, title, message)
    
    def ask(self, title, message):
        return self._message(32 + 4, title, message)
    
    def _message(self, type, title, message):
        res = subprocess.check_output(['cscript', '//Nologo',  scriptfile, str(type), title, message])
        res = int(res.decode().strip())
        res = {0: False, 1: True, 6: True, 7: False}.get(res, res)
        print(res)
        return res
