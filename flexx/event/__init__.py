"""
Naming in the context of events:

* event: something that has occurred, represented by an event object (a Dict)
* event emitter: an object that can emit events, of a class that
  inherits from EventEmitter.
* handler: an object that can handle events, it wraps a handler function.
* connection: generic term to indicate a connection between a handler
  and an emitter.
* connection-string: a string used to connect a handler to an emitter.
  E.g. 'path.to.emitter.event_type:label'.
* type: a string name indicating the type of event, e.g. 'mouse_down'.
  When type is an argument to a function, the label can also be included,
  e.g. 'mouse_down:foo'.
* label: a string name that can be specified for a connection. It can
  be used to influence the order of event handling, to disconnect handlers,
  and to help identify the source of an event inside a handler.

"""

from ._dict import Dict
from ._handler import connect, loop
from ._properties import prop, readonly, event
from ._hasevents import EventEmitter

from ._hasevents import new_type, with_metaclass
