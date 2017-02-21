"""
Dialite is a pure Python package to show dialogs. It is lightweight,
cross-platform, and has no dependencies. It provides a handful of
functions, each a verb, that can be used to inform(), warn() or fail()
the user, or to ask_ok(), ask_retry() or ask_yesno().

Dialite can show dialogs on Window, OS X and Linux, and falls back to
a terminal interface if dialogs are unavailable (e.g. if not supported
by the platform, or for SSH connections).

On Windows, it uses Windows Script Host (cscript.exe). On OS X it uses
osascript to show a dialog from the frontmost application. On Linux it
uses Zenity.

"""

from __future__ import print_function, division, absolute_import

import sys

import logging
logger = logging.getLogger(__name__)
del logging

# We import all modules; no dynamic loading. That will only complicate things,
# e.g. for tools like cx_Freeze.
from ._base import BaseApp, TerminalApp, StubApp
from ._windows import WindowsApp
from ._linux import LinuxApp
from ._osx import OSXApp


if sys.version_info > (3, ):
    string_types = str,  # noqa
else:  # pragma: no cover
    string_types = basestring,  # noqa


_the_app = None
_disabled = 0

def _get_app(force_new=False):
    """ Internal function to get the app that should be used.
    """
    global _the_app
    if _disabled:
        return StubApp()
    if _the_app is not None and not force_new:
        assert isinstance(_the_app, BaseApp)
        return _the_app
    
    # Select preferred app
    if sys.platform.startswith('win'):
        app = WindowsApp()
    elif sys.platform.startswith('linux'):
        app = LinuxApp()
    elif sys.platform.startswith('darwin'):
        app = OSXApp()
    else:
        app = TerminalApp()
    
    # Fall back to tty, or to stub that fails on anything other than info/warn
    if not app.works():
        app = TerminalApp()
    if not app.works():
        app = StubApp()
    
    _the_app = app
    return app


class NoDialogs(object):
    """ Context manager to temporarily disable dialogs, e.g. during tests.
    Note that (currenty) the questions that require user input will raise
    SystemExit. Also note thate on CI dialogs are generally already disabled.
    """
    
    def __enter__(self):
        global _disabled
        _disabled += 1
        return self
    
    def __exit__(self, type, value, traceback):
        global _disabled
        _disabled -= 1


def is_supported():
    """ Get whether Dialite is supported for the current platform.
    """
    return not isinstance(_the_app, StubApp)


def fail(title='Error', message=''):
    """ Show a message to let the user know that something failed.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    """
    if not isinstance(title, string_types):
        raise TypeError('fail() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('fail() message must be a string.')
    _get_app().fail(title, message)


def warn(title='Warning', message=''):
    """ Warn the user about something.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    """
    if not isinstance(title, string_types):
        raise TypeError('warn() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('warn() message must be a string.')
    _get_app().warn(title, message)


def inform(title='Info', message=''):
    """ Inform the user about something.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    """
    if not isinstance(title, string_types):
        raise TypeError('inform() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('inform() message must be a string.')
    _get_app().inform(title, message)


def ask_ok(title='Confirm', message=''):
    """ Ask the user to confirm something via an ok-cancel question.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool): Whether the user selected "OK".
    """
    if not isinstance(title, string_types):
        raise TypeError('ask_ok() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('ask_ok() message must be a string.')
    return _get_app().ask_ok(title, message)


def ask_retry(title='Retry', message=''):
    """ Ask the user whether to retry something via a retry-cancel question.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool): Whether the user selected "Retry".
    """
    if not isinstance(title, string_types):
        raise TypeError('ask_retry() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('ask_retry() message must be a string.')
    return _get_app().ask_retry(title, message)


def ask_yesno(title='Question', message=''):
    """ Ask the user a yes-no question.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool):  Whether the user selected "Yes".
    """
    if not isinstance(title, string_types):
        raise TypeError('ask_yesno() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('ask_yesno() message must be a string.')
    return _get_app().ask_yesno(title, message)
