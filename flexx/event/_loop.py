"""
Implementation of basic event loop object. Can be integrated a real
event loop such as tornado or Qt.
"""

import sys
import threading

from . import logger

def this_is_js():
    return False

# todo: maybe this can be the base class for the tornado loop that we use in flexx.app


class Loop:
    """ The singleton Flexx event loop at ``flexx.event.loop``. This holds
    the queue of pending calls, actions, and reactions. These are queued
    separately to realize a consistent one-way data-flow.
    
    Users typically do not need to be aware of this, though it can be
    useful during debugging.
    
    This loop can integrate with an existing event loop (e.g. of Qt
    or Tornado). If Qt or Tornado is imported at the time that
    ``flexx.event`` gets imported, the loop is integrated automatically.
    
    This object can also be used as a context manager; events get
    processed when the context exits.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._calllaterfunc = lambda x: None
        self.reset()
        
    def reset(self):
        """ Reset the loop, allowing for reuse.
        """
        self._last_thread_id = 0
        self._scheduled_call_to_iter = False
        
        self._processing_action = None
        self._processing_reaction = None
        
        self._prop_access = {}
        self._pending_calls = []
        self._pending_actions = []
        self._pending_reactions = []
        self._pending_reaction_ids = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.iter()
    
    def is_processing_actions(self):
        """ Whether the loop is processing actions right now, i.e.
        whether mutations are allowed to be done now.
        """
        return self._processing_action is not None
    
    ## Adding to queues
    
    def _schedule_iter(self):
        # Make sure to call this with the lock
        if not self._scheduled_call_to_iter:
            self._scheduled_call_to_iter = True
            self._calllaterfunc(self.iter)
    
    def call_later(self, func):
        """ Call the given function in the next iteration of the event loop.
        """
        with self._lock:
            self._pending_calls.append(func)
            self._schedule_iter()
    
    def add_action_invokation(self, action, args):
        """ Schedule the handling of an action.
        """
        with self._lock:
            self._pending_actions.append((action, args))
            self._schedule_iter()
    
    def add_reaction_event(self, reaction, ev):
        """ Schulde the handling of a reaction.
        """
        
        # In principal, the mechanics of adding items to the queue is not complex,
        # but this code is performance critical, so we have apply several tricks
        # to make this code run fast.
        # _pending_reactions is a list of tuples (reaction, representing event, events)
        
        # Allow reaction to discard the event (or rather, consume it by reconnecting)
        # It is important to do the reconnecting before a new event occurs that
        # the reaction might be subscribed to after the reconnect.
        if reaction._filter_event(ev):
            return
        
        with self._lock:
            self._ensure_thread_match()
            
            if reaction.is_explicit():
                # For explicit reactions, we try to consolidate the events by
                # appending the event to the existing item in the queue, but
                # we don't want to break the order, i.e. we can only skip over
                # events that are the same as the current. Each queue item has
                # a reference event to make this skipping more efficient.
                i = len(self._pending_reactions)
                while i > 0:
                    i -= 1
                    ev2 = self._pending_reactions[i][1]  # representing event
                    if self._pending_reactions[i][0] is reaction:
                        # We can simply append the event
                        self._pending_reactions[i][2].append(ev)
                        if not (ev2['source'] is ev['source'] and
                                ev2['type'] == ev['type']):
                            # Mark that the events are heterogeneous
                            self._pending_reactions[i][1] = {'source': None}
                        return
                    # Only continue if all events of the next item match the current
                    if not (ev2 is None or
                            (ev2.source is ev.source and ev2.type == ev.type)):
                        break
            
            else:
                # For implicit reactions, we try to consolidate by not adding
                # to the queue if the correspinding reaction is already
                # present. We use _pending_reaction_ids for this.
                if reaction._id in self._pending_reaction_ids:
                    return
            
            # Add new item to queue
            if reaction.is_explicit():
                self._pending_reactions.append((reaction, ev, [ev]))
            else:
                self._pending_reactions.append((reaction, None, []))
                self._pending_reaction_ids[reaction._id] = True
            
            self._schedule_iter()
    
    def register_prop_access(self, component, prop_name):
        """ Register access of a property, to keep track of implicit reactions.
        """
        # Notes on implicit reactions. Like explicit reactions, these are
        # connected to events, such that add_reaction_event() will get called
        # for the reaction when a property that the reaction uses changes.
        # This wil always result in the invokation of the reaction.
        # 
        # During the invokation of a reaction, the register_prop_access()
        # method is used to track property access by the reaction. That way,
        # connections can be updated as needed.
        
        # Note that we use a dict here, but for the event reconnecting to
        # be efficient, the order of connections is imporant, so implicit
        # reactions have really poor performance on Python 2.7 :)
        # Make sure not to count access from other threads
        if self._processing_reaction is not None:
            if not self._processing_reaction.is_explicit():
                if threading.get_ident() == self._last_thread_id:
                    if component._id not in self._prop_access:
                        self._prop_access[component._id] = component, {prop_name: True}
                    else:
                        self._prop_access[component._id][1][prop_name] = True

    ## Queue processing
    
    def _ensure_thread_match(self):
        # Check that event loop is not run from multiple threads at once
        tid = threading.get_ident()
        if self._last_thread_id == 0:
            self._last_thread_id = tid
        elif self._last_thread_id != tid:  # pragma: no cover
            raise RuntimeError('Flexx is supposed to run a single event loop at once.')
    
    def iter(self):
        """ Do one event loop iteration; process pending calls,
        actions and reactions. These tree types of items are each queued
        in separate queues, and are handled in the aforementioned order.
        """
        with self._lock:
            self._scheduled_call_to_iter = False
            self._ensure_thread_match()
        
        self.process_calls()
        self.process_actions()
        # todo: while len(self._pending_reactions) > 0:
        self.process_reactions()
    
    def process_calls(self):
        """ Process pending function calls.
        """
        # Select pending
        with self._lock:
            self._ensure_thread_match()
            pending_calls = self._pending_calls
            self._pending_calls = []
        
        # Process
        for i in range(len(pending_calls)):
            func = pending_calls[i]
            try:
                func()
            except Exception as err:
                logger.exception(err)
    
    def process_actions(self, process_one=False):
        """ Process all (or just one) pending actions.
        """
        # Select pending
        with self._lock:
            self._ensure_thread_match()
            if process_one:
                pending_actions = [self._pending_actions.pop(0)]
            else:
                pending_actions = self._pending_actions
                self._pending_actions = []
        
        # Process
        for i in range(len(pending_actions)):
            action, args = pending_actions[i]
            self._processing_action = action
            try:
                action(*args)
            except Exception as err:
                logger.exception(err)
            finally:
                self._processing_action = None
    
    def process_reactions(self):
        """ Process all pending reactions.
        """
        # Select pending
        with self._lock:
            self._ensure_thread_match()
            pending_reactions = self._pending_reactions
            self._pending_reactions = []
            self._pending_reaction_ids = {}
        
        # Process
        for i in range(len(pending_reactions)):
            reaction, _, events = pending_reactions[i]
            # Call reaction
            if len(events) > 0 or not reaction.is_explicit():
                self._prop_access = {}
                self._processing_reaction = reaction
                try:
                    reaction(*events)
                except Exception as err:
                    logger.exception(err)
                finally:
                    self._processing_reaction = None
            # Reconnect implicit reaction. The _update_implicit_connections()
            # method is pretty efficient if connections has not changed.
            try:
                if not reaction.is_explicit():
                    connections = []
                    for component_names in self._prop_access.values():
                        component = component_names[0]
                        for name in component_names[1]:
                            connections.append((component, name))
                    reaction._update_implicit_connections(connections)
            except Exception as err:
                logger.exception(err)
            finally:
                self._prop_access = {}
    
    ## Integration
    
    def integrate(self, call_later_func=None, raise_on_fail=True):
        """ Integrate with an existing event loop system.
        
        Params:
            call_later_func (func): a function that can be called to
                schedule the calling of a given function. If not given,
                will try to connect to Tornado or Qt event loop, but only
                if either library is already imported.
            raise_on_fail (bool): whether to raise an error when the
                integration could not be performed.
        """
        if call_later_func is not None:
            if callable(call_later_func):
                self._calllaterfunc = call_later_func
                self._calllaterfunc(self.iter)
            else:
                raise ValueError('call_later_func must be a function')
        elif 'tornado' in sys.modules:
            self.integrate_tornado()
        elif 'PyQt4.QtGui' in sys.modules:  # pragma: no cover
            self.integrate_pyqt4()
        elif 'PySide.QtGui' in sys.modules:  # pragma: no cover
            self.integrate_pyside()
        elif raise_on_fail:  # pragma: no cover
            raise RuntimeError('Could not integrate flexx.event loop')
    
    def integrate_tornado(self):
        """ Integrate with tornado.
        """
        import tornado.ioloop
        loop = tornado.ioloop.IOLoop.current()
        self._calllaterfunc = loop.add_callback
        self._calllaterfunc(self.iter)
        logger.debug('Flexx event loop integrated with Tornado')
    
    def integrate_pyqt4(self):  # pragma: no cover
        """ Integrate with PyQt4.
        """
        from PyQt4 import QtCore, QtGui
        self._integrate_qt(QtCore, QtGui)
        logger.debug('Flexx event loop integrated with PyQt4')
    
    def integrate_pyside(self):  # pragma: no cover
        """ Integrate with PySide.
        """
        from PySide import QtCore, QtGui
        self._integrate_qt(QtCore, QtGui)
        logger.debug('Flexx event loop integrated with PySide')
    
    def _integrate_qt(self, QtCore, QtGui):  # pragma: no cover
        from queue import Queue, Empty
        
        class _CallbackEventHandler(QtCore.QObject):
            
            def __init__(self):
                QtCore.QObject.__init__(self)
                self.queue = Queue()
            
            def customEvent(self, event):
                while True:
                    try:
                        callback, args = self.queue.get_nowait()
                    except Empty:
                        break
                    try:
                        callback(*args)
                    except Exception as why:
                        print('callback failed: {}:\n{}'.format(callback, why))
            
            def postEventWithCallback(self, callback, *args):
                self.queue.put((callback, args))
                QtGui.qApp.postEvent(self, QtCore.QEvent(QtCore.QEvent.User))
        
        _callbackEventHandler = _CallbackEventHandler()
        self._calllaterfunc = _callbackEventHandler.postEventWithCallback
        self._calllaterfunc(self.iter)


loop = Loop()
loop.integrate(None, False)
