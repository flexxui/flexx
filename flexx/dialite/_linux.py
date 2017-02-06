from __future__ import print_function, division, absolute_import

import os

from ._base import BaseApp, check_output, test_call


# Note: zenity returns 1 (i.e. False) when the dialig is closed by
# pressing the cross, but since that does not mean anything for
# info/warn/fail, we ignore that.


class LinuxApp(BaseApp):
    """ Implementation of dialogs for Linux, by making use of Zenity.
    """
    
    def works(self):
        return test_call(['zenity', '--version'])
    
    def fail(self, title, message):
        self._message('--error', title, message)
    
    def warn(self, title, message):
        self._message('--warning', title, message)
    
    def inform(self, title, message):
        self._message('--info', title, message)
    
    def ask_ok(self, title, message):
        return self._message('--question', title, message,
                             '--ok-label', 'OK', '--cancel-label', 'Cancel')
    
    def ask_retry(self, title, message):
        return self._message('--question', title, message,
                             '--ok-label', 'Retry', '--cancel-label', 'Cancel')
    
    def ask_yesno(self, title, message):
        return self._message('--question', title, message,
                             '--ok-label', 'Yes', '--cancel-label', 'No')
    
    def _message(self, type, title, message, *more):
        env = os.environ.copy()
        env['WINDOWID'] = ''
        message = message.replace('"', '\u201C').replace("'", '\u2018')
        res, _ = check_output(['zenity', type, '--title', title,
                               '--text', message] + list(more), env=env)
        return not res  # an exit-code of zero means yes/ok
