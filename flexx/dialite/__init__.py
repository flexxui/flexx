"""
Dialite is a lightweight Python package for cross-platform dialogs.
It provides a handful of functions, each one a verb, that can be
used to inform(), warn() or fail() the user, or to confirm() something
or ask() a yes-no question.
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
    string_types = str,
else:
    string_types = basestring,


def _select_app():
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
    return app

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
    if not isinstance(title, string_types):
        raise TypeError('fail() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('fail() message must be a string.')
    _the_app.fail(title, message)


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
    _the_app.warn(title, message)


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
    _the_app.inform(title, message)


def confirm(title='Confirm', message=''):
    """ Ask the user to confirm something via an ok-cancel question.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool): Whether the user selected "OK".
    """
    if not isinstance(title, string_types):
        raise TypeError('ask() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('ask() message must be a string.')
    return _the_app.confirm(title, message)


def ask(title='Question', message=''):
    """ Ask the user a yes-no question.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool):  Whether the user selected "Yes".
    """
    if not isinstance(title, string_types):
        raise TypeError('ask() title must be a string.')
    if not isinstance(message, string_types):
        raise TypeError('ask() message must be a string.')
    return _the_app.ask(title, message)