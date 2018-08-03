"""
Tricky cases for an event system.
"""

from flexx import app, event, ui


## Synced sliders

class SyncedSlidersBase(ui.Widget):

    def init(self):

        with ui.VBox():
            ui.Label(text=self.TITLE)
            self.slider1 = ui.Slider()
            self.slider2 = ui.Slider()

            ui.Widget(flex=1)

    @event.reaction('slider1.value', 'slider2.value')
    def sleep_when_slider_changes(self, *events):
        global time  # time() is a PScript builtin
        for ev in events:
            etime = time() + 0.05
            while time() < etime:
                pass


class SyncedSlidersWrong(SyncedSlidersBase):
    """ This example syncs two sliders by implementing one reaction for each
    slider. This is probably the worst way to do it; if there is some delay
    in your app, you quickly get into a situation where the event system has
    two queued actions: one to set slider 1 to value A and another to set
    slider 2 to value B. And these will keep interchanging.
    """

    TITLE = 'Synced sliders, done wrong'

    @event.reaction('slider1.value')
    def __slider1(self, *events):
        self.slider2.set_value(events[-1].new_value)

    @event.reaction('slider2.value')
    def __slider2(self, *events):
        self.slider1.set_value(events[-1].new_value)


class SyncedSlidersRight(SyncedSlidersBase):
    """ This example syncs two sliders in a much better way, making use of a
    single reaction, which is marked as greedy. This ensures that all events
    to either of the sliders get handled in a single call to the reaction,
    which avoids a ping-pong effect. Only having a single (normal) reaction
    reduced the chance of a ping-pong effect, but does not elliminate it.

    Even better would be to react to ``user_value``  or ``user_done``
    to avoid ping-ping altogether.

    A nice addition would be to add an action that sets both slider
    values at the same time.
    """

    TITLE = 'Synced sliders, done right'

    @event.reaction('slider1.value', 'slider2.value', mode='greedy')
    def __slider1(self, *events):
        value = events[-1].new_value
        self.slider1.set_value(value)
        self.slider2.set_value(value)


## Main

class Tricky(ui.Widget):
    """ A collection of tricky cases.
    """

    def init(self):
        with ui.VBox():

            self.reset = ui.Button(text='Reset event system')
            with ui.HFix(flex=1):
                SyncedSlidersWrong(flex=1)
                SyncedSlidersRight(flex=1)

            ui.Widget(flex=1)  # spacer

    @event.reaction('reset.pointer_click')
    def _reset(self):
        # You probably don't want to ever do this in a normal app.
        # Do via a timeout because reactions get handled by the event system,
        # so the reset will not work correctly.
        global window
        window.setTimeout(event.loop.reset, 0)


m = app.launch(Tricky, 'app')
app.run()
