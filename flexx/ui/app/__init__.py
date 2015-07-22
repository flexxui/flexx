"""
Flexx app module that implements the connection between Python and JS.

We might move this to flexx/app if people want to be able to use
Mirrored classes without the ui.

"""

from .app import run, stop, call_later, this_is_an_app
#from .mirrored import Mirrored, get_instance_by_id, get_mirrored_classes
from .paired import Paired, get_instance_by_id, get_mirrored_classes
