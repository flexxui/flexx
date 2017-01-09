from __future__ import print_function, division, absolute_import

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
    
    def warn(self, title, message):
        self._message('--warning', title, message)
    
    def inform(self, title, message):
        self._message('--info', title, message)
    
    def verify(self, title, message):
        return self._message('--question', title, message,
                             '--ok-label', 'OK', '--cancel-label', 'Cancel')
    
    def ask(self, title, message):
        return self._message('--question', title, message,
                             '--ok-label', 'Yes', '--cancel-label', 'No')
    
    def _message(self, type, title, message, *more):
        message = message.replace('"', '\u201C').replace("'", '\u2018')
        res = subprocess.call(['zenity', type, '--title', title,
                               '--text', message] + list(more))
        return not res  # an exit-code of zero means yes/ok
