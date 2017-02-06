from __future__ import print_function, division, absolute_import

from ._base import BaseApp, check_output, test_call


class OSXApp(BaseApp):
    """ Implementation of dialogs for OS X, by making use of osascript.
    """
    
    def works(self):
        return test_call(['osascript', '-e', 'return "hi"'])
    
    def fail(self, title, message):
        self._message(title, message, 'with icon stop', 'buttons {"OK"}')
    
    def warn(self, title, message):
        self._message(title, message, 'with icon caution', 'buttons {"OK"}')
    
    def inform(self, title, message):
        self._message(title, message, 'buttons {"OK"}')
    
    def ask_ok(self, title, message):
        # The extra space in "Cancel " is to prevent osascript from
        # seeing it as a cancel button. Otherwise clicking it would
        # produce a nonzero error code because the user "cancelled".
        return self._message(title, message, 'buttons {"OK", "Cancel "}')
    
    def ask_retry(self, title, message):
        return self._message(title, message, 'buttons {"Retry", "Cancel "}')
    
    def ask_yesno(self, title, message):
        return self._message(title, message, 'buttons {"Yes", "No"}')
    
    def _message(self, title, message, *more):
        message = message.replace('"', '\u201C').replace("'", '\u2018')
        t = 'tell app (path to frontmost application as text) '
        t += 'to display dialog "%s" with title "%s"'
        t += ' ' + ' '.join(more)
        retcode, res = check_output(['osascript', '-e',
                                     t % (message, title)])
        resmap = {'no': False, 'cancel': False,
                  'ok': True, 'retry': True, 'yes': True}
        return resmap.get(res.strip().split(':')[-1].lower(), None)
