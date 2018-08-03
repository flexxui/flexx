"""
The flexx.flx module provides a namspace combining all the things from
flexx.app, flexx.event, and flexx.ui.
"""

# flake8: noqa

from . import __version__, config, set_log_level
from .event import *
from .app import *
from .ui import *
