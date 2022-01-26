from ... import event
from .._widget import PyWidget
import threading


class DynamicWidgetContainer(PyWidget):
    """ Widget container to allow dynamic insertion and disposal of widgets.
    """

    DEFAULT_MIN_SIZE = 0, 0

    def init(self, *init_args, **property_values):
        # TODO: figure out if init_args is needed for something
        super(DynamicWidgetContainer, self).init()  # call to _component.py -> Component.init(self)
        # the page
        self.pages = []  # pages are one on top of another

    def _init_events(self):
        pass  # just don't use standard events

    def clean_pages(self):  # remove empty pages from the top
        while self.pages[-1] is None:
            del self.pages[-1]

    @event.reaction("remove")
    def __remove(self, *events):
        if self.pages:
            page = self.pages[events[0]['page_position']]
            page.dyn_stop_event.set()
            page.dyn_id = None
            page.dispose()
            page._jswidget.dispose()  # <-- added
            self.pages[events[0]['page_position']] = None

    @event.emitter
    def remove(self, page_position):
        return dict(page_position=page_position)

    @event.reaction("_emit_instantiate")
    def __instantiate(self, *events):
        with self:
            with events[0]['widget_type'](events[0]['style']) as page:
                page.parent = self
                page.dyn_id = events[0]['page_position']  # TODO use a class attribute to allow non pyWidget
                page.dyn_stop_event = threading.Event()
                task = self.pages[page.dyn_id]  # the location contains a task
                self.pages[page.dyn_id] = page  # record the instance
                task.set()  # set the task as done as the instantiation is done
                self.clean_pages()  # only clean after instanciation so it does not delete future location

    @event.emitter
    def _emit_instantiate(self, widget_type, page_position, options):  # can't put default arguments
        return dict(widget_type=widget_type, page_position=page_position, style=options['style'])

    def instantiate(self, widget_type, options=None):
        """ Send an instantiate command and return the widget instance id.
        This function is thread safe. """
        if options is None:
            options = dict({'style':"width: 100%; height: 100%;"})

            async_task = threading.Event()
            pos = len(self.pages)
            self.pages.append(async_task)  # this is the new location for this instance
            while self.pages[pos] is not async_task:
                pos += 1  # in case some other thread added to the list

        def out_of_thread_call():
            nonlocal pos
            self._emit_instantiate(widget_type, pos, options)

        event.loop.call_soon(out_of_thread_call)
        return pos

    def get_instance(self, page_position):
        """ returns None if not yet instanciated """
        ret = self.pages[page_position]
        if isinstance(ret, threading.Event):
            ret.wait()  # wait until event would be .set()
            return self.pages[page_position]
        else:
            return ret