"""
Flexx app module that implements the connection between Python and JS.

We might move this to flexx/app if people want to be able to use
Pair classes without the ui.

"""

from .proxy import run, stop, call_later, app
from .pair import Pair, get_instance_by_id, get_pair_classes
