import subprocess

from ._base import BaseApp


# Note: zenity returns 1 (i.e. False) when the dialig is closed by
# pressing the cross, but since that does not mean anything for
# info/warn/fail, we ignore that.


class LinuxApp(BaseApp):
    """ Implementation of dialogs for Linux, by making use of Zenity.
    """
    
    def fail(self, title, message):
        self._message('--error', title, message)
        return True
    
    def warn(self, title, message):
        self._message('--warning', title, message)
        return True
    
    def inform(self, title, message):
        self._message('--info', title, message)
        return True
    
    def ask(self, title, message):
        return self._message('--question', title, message)
    
    def _message(self, type, title, message, *more):
        res = subprocess.call(['zenity', type,
                               '--title', title, '--text', message] + list(more))
        res = not res  # an exit-code of zero means yes/ok
        print(res)
        return res
