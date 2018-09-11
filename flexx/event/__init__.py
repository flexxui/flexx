"""
The Flexx event system.
"""

import logging
logger = logging.getLogger(__name__)
del logging

import sys
assert sys.version_info > (3, 5), "Flexx.event needs Python 3.5+"
del sys

# flake8: noqa
from ._dict import Dict
from ._loop import Loop, loop
from ._action import Action, action
from ._reaction import Reaction, reaction
from ._emitter import emitter, Emitter
from ._attribute import Attribute
from ._property import *
from ._component import Component, mutate_array, mutate_dict
