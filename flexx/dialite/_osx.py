import subprocess

from ._base import BaseApp


class OSXApp(BaseApp):
    """ Implementation of dialogs for OS X, by making use of osascript.
    """
    
    def fail(self, title, message):
        self._message(title, message, 'with icon stop', 'buttons {"OK"}')
        return True
    
    def warn(self, title, message):
        self._message(title, message, 'with icon caution', 'buttons {"OK"}')
        return True
    
    def inform(self, title, message):
        self._message(title, message, 'buttons {"OK"}')
        return True
    
    def ask(self, title, message):
        return self._message(title, message, 'buttons {"Yes", "No"}')
    
    def _message(self, title, message, *more):
        message = message.replace('"', '\u201C').replace("'", '\u2018')
        t = 'tell app (path to frontmost application as text) '
        t += 'to display dialog "%s" with title "%s"'
        t += ' ' + ' '.join(more)
        res = subprocess.check_output(['osascript', '-e', t % (message, title)])
        res = res.decode().strip()
        res = res.split(':')[-1].lower()
        res = {'ok': True, 'yes': True, 'no': False}.get(res, False)
        print(res)
        return res
