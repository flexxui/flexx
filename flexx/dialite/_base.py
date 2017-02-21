from __future__ import print_function, division, absolute_import

import os
import sys
import time
import subprocess
import webbrowser

from . import logger

if sys.version_info < (3, ):  # pragma: no cover
    input = raw_input  # noqa


class BaseApp(object):
    """ The base app class. Acts as a placeholder to define the API
    that subclasses must implement.
    """
    
    def works(self):
        raise NotImplementedError()  # to test whether the app actually works
    
    def fail(self, title, message):
        raise NotImplementedError()
    
    def warn(self, title, message):
        raise NotImplementedError()
        
    def inform(self, title, message):
        raise NotImplementedError()
    
    def ask_ok(self, title, message):
        raise NotImplementedError()
    
    def ask_retry(self, title, message):
        raise NotImplementedError()
    
    def ask_yesno(self, title, message):
        raise NotImplementedError()


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
    
    def ask_ok(self, title, message):
        text = '%s: %s' % (title, message)
        text += '\nconfirm ([y]/n)? '
        return self._ask_yes_no(text)
    
    def ask_retry(self, title, message):
        text = '%s: %s' % (title, message)
        text += '\nretry ([y]/n)? '
        return self._ask_yes_no(text)
    
    def ask_yesno(self, title, message):
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
    
    def works(self):
        return True
    
    def _error(self, kind, title, message):
        # Show error in browser, because user may not be able to see exception
        show_error_via_browser()
        # Close program
        t = 'Cannot show %s-dialog on platform %s.\n  %s: %s'
        sys.exit(t % (kind, sys.platform, title, message))
    
    def fail(self, title, message):
        logger.error('fail', title, message)
    
    def warn(self, title, message):
        logger.warning('%s: %s' % (title, message))
    
    def inform(self, title, message):
        logger.info('%s: %s' % (title, message))
    
    def ask_ok(self, title, message):
        self._error('confirm', title, message)
    
    def ask_retry(self, title, message):
        self._error('retry', title, message)
    
    def ask_yesno(self, title, message):
        self._error('yesno', title, message)


def check_output(*args, **kwargs):
    """ Call a subprocess, return return-code and stdout.
    When *this* process exits, kills the subprocess.
    """
    kwargs['stdout'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.STDOUT
    
    p = subprocess.Popen(*args, **kwargs)
    
    try:
        while p.poll() is None:
            time.sleep(0.002)
        return p.poll(), p.stdout.read().decode('utf-8', 'ignore')
    finally:
        if p.poll() is None:  # pragma: no cover
            p.kill()


def test_call(*args, **kwargs):
    """ Test whether a subprocess call succeeds.
    """
    try:
        subprocess.check_output(*args, **kwargs)
        return True
    except Exception:
        return False


def hastty():
    """ Whether (it looks like) a tty is available.
    """
    try:
        return sys.stdin and sys.stdin.isatty()
    except Exception:  # pragma: no cover
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
            f.write(error_html.encode('utf-8'))
    except Exception:  # pragma: no cover
        return  # no user directory, or rights to write there?
    # Open it in a browser
    try:
        webbrowser.open(filename)
    except Exception:  # pragma: no cover
        return  # no browser?
