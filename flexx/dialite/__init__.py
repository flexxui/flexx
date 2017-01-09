import sys

# We import all modules, to make it easy for tools like cx_Freeze
from ._base import BaseApp, StubApp
from ._windows import WindowsApp
from ._linux import LinuxApp
from ._osx import OSXApp

# Select the app
_the_app = None
if sys.platform.startswith('win'):
    _the_app = WindowsApp()
elif sys.platform.startswith('linux'):
    _the_app = LinuxApp()
elif sys.platform.startswith('darwin'):
    _the_app = OSXApp()
else:
    _the_app = StubApp()

# todo: write a test that verifies that all backends implement each method of BaseApp
# todo: think about fallbacks


def fail(title='Error', message=''):
    """ Show a message to let the user know that we failed in some way.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool): True
    """
    if not isinstance(title, str):
        raise TypeError('fail() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('fail() message must be a string.')
    return _the_app.fail(title, message)


def warn(title='Warning', message=''):
    """ Warn the user about something.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool): True
    """
    if not isinstance(title, str):
        raise TypeError('warn() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('warn() message must be a string.')
    return _the_app.warn(title, message)


def inform(title='Information', message=''):
    """ Inform the user about something.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        result (bool): True
    """
    if not isinstance(title, str):
        raise TypeError('inform() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('inform() message must be a string.')
    return _the_app.inform(title, message)


def ask(title='Question', message=''):
    """ Ask the user a question.
    
    Parameters:
        title (str): the text to show as the window title.
        message (str): the message to show in the body of the dialog.
    
    Returns:
        DONT KNOW YET EXACTLY
    """
    if not isinstance(title, str):
        raise TypeError('ask() title must be a string.')
    if not isinstance(message, str):
        raise TypeError('ask() message must be a string.')
    return _the_app.ask(title, message)


# todo: what kind of questions do we allow asking?
#- Windows supports: ok+cancel, yes+no, yes+no+cancel, abort+retry+ignore, retry+cancel, cancel+tryagain+continue
