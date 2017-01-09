"""
Dialite: a lightweight Python package for cross-platform dialogs.

Dialite provides a handful of functions, each one a noun, that can be
used to inform(), warn() or fail() the user, or to verify() something
or ask() a yes-no question.

Dialite is pure Python, has no dependencies, works on Windows, Linux
and OS X. and is friendly to tools like cx_Freeze.
"""

from __future__ import print_function, division, absolute_import

import sys

# We import all modules; no dynamic loading. That will only complicate things,
# e.g. for tools like cx_Freeze.
from ._base import BaseApp, StubApp
from ._windows import WindowsApp
from ._linux import LinuxApp
from ._osx import OSXApp


def _select_app():
    if sys.platform.startswith('win'):
        return WindowsApp()
    elif sys.platform.startswith('linux'):
        return LinuxApp()
    elif sys.platform.startswith('darwin'):
        return OSXApp()
    else:
        return StubApp()

_the_app = _select_app()
assert isinstance(_the_app, BaseApp)


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
    if not isinstance(title, str):
        raise TypeError('fail() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('fail() message must be a string.')
    _the_app.fail(title, message)


def warn(title='Warning', message=''):
    """ Warn the user about something.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    """
    if not isinstance(title, str):
        raise TypeError('warn() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('warn() message must be a string.')
    _the_app.warn(title, message)


def inform(title='Info', message=''):
    """ Inform the user about something.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    """
    if not isinstance(title, str):
        raise TypeError('inform() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('inform() message must be a string.')
    _the_app.inform(title, message)


def verify(title='Verify', message=''):
    """ Ask the user to verify something via an ok-cancel question.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool): Whether the user selected "OK".
    """
    if not isinstance(title, str):
        raise TypeError('ask() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('ask() message must be a string.')
    return _the_app.verify(title, message)


def ask(title='Question', message=''):
    """ Ask the user a yes-no question.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool):  Whether the user selected "Yes".
    """
    if not isinstance(title, str):
        raise TypeError('ask() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('ask() message must be a string.')
    return _the_app.ask(title, message)
