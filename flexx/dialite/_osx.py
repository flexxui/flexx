import subprocess

from ._base import BaseApp


class OSXApp(BaseApp):
    """ Implementation of dialogs for OS X, by making use of osascript.
    """
    
    def fail(self, title, message):
        self._message(title, message, 'with icon stop', 'buttons {"OK"}')
    
    def warn(self, title, message):
        self._message(title, message, 'with icon caution', 'buttons {"OK"}')
    
    def inform(self, title, message):
        self._message(title, message, 'buttons {"OK"}')
    
    def verify(self, title, message):
        return self._message(title, message, 'buttons {"Ok", "Cancel"}')
    
    def ask(self, title, message):
        return self._message(title, message, 'buttons {"Yes", "No"}')
    
    def _message(self, title, message, *more):
        message = message.replace('"', '\u201C').replace("'", '\u2018')
        t = 'tell app (path to frontmost application as text) '
        t += 'to display dialog "%s" with title "%s"'
        t += ' ' + ' '.join(more)
        res = subprocess.check_output(['osascript', '-e', t % (message, title)])
        resmap = {'ok': True, 'yes': True, 'no': False, 'cancel': False}
        res = resmap.get(res.decode().strip().split(':')[-1].lower(), None)
        print(res)
        return res
