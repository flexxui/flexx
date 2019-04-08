"""
Implementation of Flexx' event loop based on asyncio.
"""

# Note: there are some unusual constructs here, such as ``if xx is True``.
# These are there to avoid inefficient JS code as this code is transpiled
# using PScript. This code is quite performance crirical.

import asyncio
import threading

from . import logger

def this_is_js():
    return False


class Loop:
    """ The singleton Flexx event loop at ``flexx.event.loop``. This holds
    the queue of pending calls, actions, and reactions. These are queued
    separately to realize a consistent one-way data-flow. Further, this
    object keeps track of (per thread) active components (i.e. the components
    whose context manager is currently active).

    Users typically do not need to be aware of the loop object, as it is
    used internally by Flexx, though it can be useful during debugging.

    This event system integrates with Python's builtin asyncio system,
    configurable via ``Loop.integrate()``. This system can run in a separate
    thread, but there can be only one active flexx event loop per process.

    This object can also be used as a context manager; an event loop
    iteration takes place when the context exits.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._thread_id = threading.get_ident()
        # self._call_soon_func = lambda x: None

        # Keep track of a stack of "active" components for use within Component
        # context manager. We have one list for each thread. Note that we should
        # limit its use to context managers, and execution should never be
        # handed back to the event loop while inside a context.
        self._local = threading.local()
        self.reset()
        self.integrate()

    def reset(self):
        """ Reset the loop, purging all pending calls, actions and reactions.
        This is mainly intended for test-related code.
        """
        self._in_iter = False
        self._scheduled_call_to_iter = False

        self._processing_action = None
        self._processing_reaction = None
        self._prop_access = {}
        self._pending_calls = []
        self._pending_actions = []
        self._pending_reactions = []
        self._pending_reaction_ids = {}

    def has_pending(self):
        """ Get whether there are any pending actions, reactions, or calls.
        """
        return (len(self._pending_reactions) > 0 or
                len(self._pending_actions) > 0 or
                len(self._pending_calls) > 0)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.iter()

    def can_mutate(self, component=None):
        """ Whether mutations can be done to the given component,
        and whether invoked actions on the component are applied directly.
        """
        # When there is an active component, only that one can be mutated
        # (so that behavior of an init() is the same regardless whether a
        # component is instantiated from an action), it must the current one.
        # Otherwise we must be in an action.
        # active = self.get_active_component()
        # if active is not None:
        #     return active is component
        active_components = self._local._active_components
        if active_components:
            return component in active_components
        else:
            return self._processing_action is not None

    ## Active components

    def get_active_components(self):
        """ Get a tuple that represents the stack of "active" components.
        Each thread has its own stack. Should only be used directly inside
        a Component context manager.
        """
        return tuple(self._local._active_components)

    def get_active_component(self):
        """ Get the currently "active" component (for this thread), or None.
        """
        if len(self._local._active_components) > 0:
            return self._local._active_components[-1]

    def _activate_component(self, component):
        """ Friend method of Component. """
        self._local._active_components.append(component)

    def _deactivate_component(self, component):
        """ Friend method of Component. """
        top = self._local._active_components.pop(-1)
        if top is not component:
            raise RuntimeError('loop._deactivate_component: %s is not %s' %
                               (component.id, top and top.id))

    ## Adding to queues

    def _schedule_iter(self):
        # Make sure to call this with the lock
        if self._scheduled_call_to_iter is False:
            self._scheduled_call_to_iter = True
            self._call_soon_func(self._iter_callback)

    def call_soon(self, func, *args):
        """ Arrange for a callback to be called as soon as possible.
        The callback is called after ``call_soon()`` returns, when control
        returns to the event loop.

        This operates as a FIFO queue, callbacks are called in the order in
        which they are registered. Each callback will be called exactly once.

        Any positional arguments after the callback will be passed to
        the callback when it is called.

        This method is thread-safe: the callback will be called in the thread
        corresponding with the loop. It is therefore actually more similar to
        asyncio's ``call_soon_threadsafe()``.

        Also see ``asyncio.get_event_loop().call_soon()`` and
        ``asyncio.get_event_loop().call_later()``.
        """
        # We keep track of pending calls locally to our event system, which
        # gives more control, e.g. during testing.
        with self._lock:
            self._pending_calls.append((func, args))
            self._schedule_iter()

    # def call_later(self, delay, func, *args)
    # This would be nice, but we'd have to implement more sophisticated
    # scheduling. Unless we'd just call asyncio's call_later, but I am
    # reluctant to do that while this code is still more or less independent of
    # asyncio.

    def add_action_invokation(self, action, args):
        """ Schedule the handling of an action. Automatically called when
        an action object is called.
        """
        with self._lock:
            self._pending_actions.append((action, args))
            self._schedule_iter()

    def add_reaction_event(self, reaction, ev):
        """ Schulde the handling of a reaction. Automatically called by
        components.
        """

        # In principal, the mechanics of adding items to the queue is not complex,
        # but this code is performance critical, so we apply several tricks
        # to make this code run fast.
        # _pending_reactions is a list of tuples (reaction, representing event, events)

        pending_reactions = self._pending_reactions

        mode = reaction.get_mode()


        with self._lock:
            self._thread_match(True)

            if mode == 'normal':
                # Normally, we try to consolidate the events by
                # appending the event to the existing item in the queue, but
                # we don't want to break the order, i.e. we can only skip over
                # events that are the same as the current. Each queue item has
                # a reference event to make this skipping more efficient.
                i = len(pending_reactions)
                while i > 0:
                    i -= 1
                    ev2 = pending_reactions[i][1]  # representing event
                    if pending_reactions[i][0] is reaction:
                        # We can simply append the event
                        pending_reactions[i][2].append(ev)
                        if not (ev2['source'] is ev['source'] and
                                ev2['type'] == ev['type']):
                            # Mark that the events are heterogeneous
                            pending_reactions[i][1] = {'source': None}
                        return
                    # Only continue if all events of the next item match the current
                    if not (ev2 is None or
                            (ev2['source'] is ev['source'] and ev2.type == ev.type)):
                        break

            else:
                # For greedy and auto reactions, we consolidate by not adding
                # to the queue if the corresponding reaction is already
                # present. We use _pending_reaction_ids for this.
                # We even omit the event objects themselves when we think they
                # don't matter (when the number of connection strings is zero).
                if reaction._id in self._pending_reaction_ids:
                    if len(reaction._connections) > 0:
                        self._pending_reaction_ids[reaction._id][2].append(ev)
                    return

            # Add new item to queue
            if len(reaction._connections) > 0:
                new_item = [reaction, ev, [ev]]
            else:
                new_item = [reaction, None, []]
            pending_reactions.append(new_item)
            self._pending_reaction_ids[reaction._id] = new_item

            self._schedule_iter()

    def register_prop_access(self, component, prop_name):
        """ Register access of a property, to keep track of automatic reactions.
        """
        # Notes on auto-reactions. Like any reactions, these are
        # connected to events, such that add_reaction_event() will get called
        # for the reaction when a property that the reaction uses changes.
        # This wil always result in the invokation of the reaction.
        #
        # During the invokation of a reaction, the register_prop_access()
        # method is used to track property access by the reaction. That way,
        # connections can be updated as needed.

        # Note that we use a dict here, but for the event reconnecting to
        # be efficient, the order of connections is imporant, so auto
        # reactions have really poor performance on Python < 3.6
        # Make sure not to count access from other threads
        if self._processing_reaction is not None:
            if self._processing_reaction.get_mode() == 'auto':
                if self._thread_match(False):
                    if component._id not in self._prop_access:
                        d = {}
                        self._prop_access[component._id] = component, d
                    else:
                        d = self._prop_access[component._id][1]
                    d[prop_name] = True

    ## Queue processing

    def _thread_match(self, fail):
        # Check that event loop is not run from multiple threads at once
        tid = threading.get_ident()
        if self._thread_id != tid:  # pragma: no cover
            if not fail:
                return False
            raise RuntimeError('Flexx is supposed to run a single event loop a once.')
        return True

    def _iter_callback(self):
        if threading.get_ident() != self._thread_id:
            return  # probably an old pending callback
        self._scheduled_call_to_iter = False
        self.iter()

    # We need a way to run our own little event system, because we cannot do
    # async in JavaScript. Therefore this is public, and therefore call_soon()
    # invokations are queued locally instead of being delegated to asyncio.
    def iter(self):
        """ Do one event loop iteration; process pending calls,
        actions and reactions. These tree types of items are each queued
        in separate queues, and are handled in the aforementioned order.
        """
        with self._lock:
            self._thread_match(True)

        # Guard against inproper use
        if self._in_iter is True:
            raise RuntimeError('Cannot call flexx.event.loop.iter() while it '
                               'is processing.')

        self._in_iter = True
        try:
            self._process_calls()
            self._process_actions()
            self._process_reactions()
        finally:
            self._in_iter = False

    def _process_calls(self):
        """ Process pending function calls.
        """
        # Select pending
        with self._lock:
            self._thread_match(True)
            pending_calls = self._pending_calls
            self._pending_calls = []

        # Process
        for i in range(len(pending_calls)):
            func, args = pending_calls[i]
            try:
                func(*args)
            except Exception as err:
                logger.exception(err)

    def _process_actions(self, n=None):
        """ Process all (or just one) pending actions.
        """
        # Select pending
        with self._lock:
            self._thread_match(True)
            if n is None:
                pending_actions = self._pending_actions
                self._pending_actions = []
            else:
                pending_actions = self._pending_actions[:n]
                self._pending_actions = self._pending_actions[n:]

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

    def _process_reactions(self):
        """ Process all pending reactions.
        """
        # Select pending
        with self._lock:
            self._thread_match(True)
            pending_reactions = self._pending_reactions
            self._pending_reactions = []
            self._pending_reaction_ids = {}

        # Process
        for ir in range(len(pending_reactions)):
            reaction, _, events = pending_reactions[ir]
            # Call reaction
            if len(events) > 0 or reaction.get_mode() == 'auto':
                self._prop_access = {}
                self._processing_reaction = reaction
                try:
                    reaction(*events)
                except Exception as err:
                    logger.exception(err)
                finally:
                    self._processing_reaction = None
            # Reconnect auto reaction. The _update_implicit_connections()
            # method is pretty efficient if connections has not changed.
            try:
                if reaction.get_mode() == 'auto':
                    connections = []
                    for component_names in self._prop_access.values():
                        component = component_names[0]
                        for name in component_names[1].keys():
                            connections.append((component, name))
                    reaction._update_implicit_connections(connections)
            except Exception as err:  # pragma: no cover
                logger.exception(err)
            finally:
                self._prop_access = {}

    ## Integration

    def integrate(self, loop=None, reset=True):
        """ Integrate the Flexx event system with the given asyncio
        event loop (or the default one). Also binds the event system
        to the current thread.

        From this point, any (pending) calls to the iter callback by the
        previous thread will be ignored.

        By calling this without calling reset(), it should be possible
        to hot-swap the system from one loop (and/or thread) to another
        (though this is currently not tested).
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        with self._lock:
            self._thread_id = threading.get_ident()
            self._local._active_components = []
            self._call_soon_func = loop.call_soon_threadsafe
            self._call_soon_func(self._iter_callback)
            if reset:
                self.reset()


    # Below is deprecated, but I leavae it here for a bit; we may want to
    # revive some of it.
    #
    # def integrate(self, call_soon_func=None, raise_on_fail=True):
    #     """ Integrate with an existing event loop system.
    #
    #     Params:
    #         call_soon_func (func): a function that can be called to
    #             schedule the calling of a given function. If not given,
    #             will try to connect to Tornado or Qt event loop, but only
    #             if either library is already imported.
    #         raise_on_fail (bool): whether to raise an error when the
    #             integration could not be performed.
    #     """
    #     if call_soon_func is not None:
    #         if callable(call_soon_func):
    #             self._call_soon_func = call_soon_func
    #             self._call_soon_func(self.iter)
    #         else:
    #             raise ValueError('call_soon_func must be a function')
    #     elif 'tornado' in sys.modules:  # pragma: no cover
    #         self.integrate_tornado()
    #     elif 'PyQt4.QtGui' in sys.modules:  # pragma: no cover
    #         self.integrate_pyqt4()
    #     elif 'PySide.QtGui' in sys.modules:  # pragma: no cover
    #         self.integrate_pyside()
    #     elif raise_on_fail:  # pragma: no cover
    #         raise RuntimeError('Could not integrate flexx.event loop')
    #
    # def integrate_tornado(self):  # pragma: no cover
    #     """ Integrate with tornado.
    #     """
    #     import tornado.ioloop
    #     loop = tornado.ioloop.IOLoop.current()
    #     self._call_soon_func = loop.add_callback
    #     self._call_soon_func(self.iter)
    #     logger.debug('Flexx event loop integrated with Tornado')
    #
    # def integrate_pyqt4(self):  # pragma: no cover
    #     """ Integrate with PyQt4.
    #     """
    #     from PyQt4 import QtCore, QtGui
    #     self._integrate_qt(QtCore, QtGui)
    #     logger.debug('Flexx event loop integrated with PyQt4')
    #
    # def integrate_pyside(self):  # pragma: no cover
    #     """ Integrate with PySide.
    #     """
    #     from PySide import QtCore, QtGui
    #     self._integrate_qt(QtCore, QtGui)
    #     logger.debug('Flexx event loop integrated with PySide')
    #
    # def _integrate_qt(self, QtCore, QtGui):  # pragma: no cover
    #     from queue import Queue, Empty
    #
    #     class _CallbackEventHandler(QtCore.QObject):
    #
    #         def __init__(self):
    #             QtCore.QObject.__init__(self)
    #             self.queue = Queue()
    #
    #         def customEvent(self, event):
    #             while True:
    #                 try:
    #                     callback, args = self.queue.get_nowait()
    #                 except Empty:
    #                     break
    #                 try:
    #                     callback(*args)
    #                 except Exception as why:
    #                     logger.warning('blck failed: {}:\n{}'.format(callback, why))
    #
    #         def postEventWithCallback(self, callback, *args):
    #             self.queue.put((callback, args))
    #             QtGui.qApp.postEvent(self, QtCore.QEvent(QtCore.QEvent.User))
    #
    #     _callbackEventHandler = _CallbackEventHandler()
    #     self._call_soon_func = _callbackEventHandler.postEventWithCallback
    #     self._call_soon_func(self.iter)


loop = Loop()
