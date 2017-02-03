from __future__ import print_function, division, absolute_import

import os
import sys
import webbrowser

from . import logger

if sys.version_info < (3, ):
    input = raw_input  # noqa


class BaseApp(object):
    """ The base app class. Acts as a placeholder to define the API
    that subclasses must implement.
    """
    
    def fail(self, title, message):
        raise NotImplementedError()
    
    def warn(self, title, message):
        raise NotImplementedError()
        
    def inform(self, title, message):
        raise NotImplementedError()
    
    def confirm(self, title, message):
        raise NotImplementedError()
    
    def ask(self, title, message):
        raise NotImplementedError()
    
    def works(self):
        return True


class TerminalApp(BaseApp):
    """ An application classes that uses input().
    """
    
    def works(self):
        return hastty()
    
    def fail(self, title, message):
        logger.error('%s: %s' % (title, message))
    
    def warn(self, title, message):
        logger.warning('%s: %s' % (title, message))
    
    def inform(self, title, message):
        logger.info('%s: %s' % (title, message))
    
    def confirm(self, title, message):
        text = '%s: %s' % (title, message)
        text += '\nproceed ([y]/n)? '
        return self._ask_yes_no(text)
    
    def ask(self, title, message):
        text = '%s: %s' % (title, message)
        text += '\nanswer ([y]/n)? '
        return self._ask_yes_no(text)
    
    def _ask_yes_no(self, text, default='y'):
        while True:
            res = input(text) or default
            if res.lower() in ('y', 'yes'):
                return True
            elif res.lower() in ('n', 'no'):
                return False
            else:
                print('invalid answer')


class StubApp(BaseApp):
    """ A stub application class for platforms that we do not support, and
    where no tty is available. Pass warning() and inform(), fail for anything
    else.
    """
    
    def _error(self, kind, title, message):
        # Show error in browser, because user may not be able to see exception
        show_error_via_browser()
        # Close program
        t = 'Cannot show %s-dialog on platform %s.\n  %s: %s'
        sys.exit(t % (kind, sys.platform, title, message))
    
    def fail(self, title, message):
        self._error('fail', title, message)
    
    def warn(self, title, message):
        logger.warning('%s: %s' % (title, message))
    
    def inform(self, title, message):
        logger.inform('%s: %s' % (title, message))
    
    def confirm(self, title, message):
        self._error('confirm', title, message)
    
    def ask(self, title, message):
        self._error('ask', title, message)


def hastty():
    """ Whether (it looks like) a tty is available.
    """
    try:
        return sys.stdin and sys.stdin.isatty()
    except Exception:
        return False  # i.e. no isatty method?


error_html = """
<html><body>
Flexx Dialite error:<br/>
Could not show dialog on this platform, and cannot fallback to a tty.
</body></html>
""".lstrip()


def show_error_via_browser():
    # Select file to write html log to
    dir = os.path.expanduser('~')
    for name in ('Desktop', 'desktop'):
        if os.path.isdir(os.path.join(dir, name)):
            dir = os.path.join(dir, name)
            break
    filename = os.path.join(dir, 'dialite_error.html')
    # Write file
    try:
        with open(filename, 'wb') as f:
            f.write(error_html.encode())
    except Exception:
        return  # no user directory, or rights to write there?
    # Open it in a browser
    try:
        webbrowser.open(filename)
    except Exception:
        return  # no browser?
