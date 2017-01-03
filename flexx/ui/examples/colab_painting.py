"""
A web app that allows multiple people to colaborate in painting. People
connecting later will not see the "paint" that was added earlier. Each
person is assigned a random color which affects how that person can
best contribute to the painting.

This app might be running at the demo server: http://flexx1.zoof.io
"""

import random

from flexx import app, ui, event

COLORS = ('#eee', '#999', '#555', '#111', 
          '#f00', '#0f0', '#00f', '#ff0', '#f0f', '#0ff',
          '#a44', '#4a4', '#44a', '#aa4', '#afa', '#4aa',
          )


class Relay(event.HasEvents):
    """ Global object to relay paint events to all participants.
    """
    @event.emitter
    def global_paint(self, pos, color):
        return dict(pos=pos, color=color)


# Create global relay
relay = Relay()


class ColabPainting(ui.Widget):
    """ Web app for colaborative painting.
    """
    
    CSS = """
    .flx-ColabPainting { background: #ddd; }
    .flx-ColabPainting .flx-CanvasWidget {
        background: #fff;
        border: 10px solid #000;
        min-width: 400px; max-width: 400px;
        min-height: 400px; max-height: 400px;
    }
    """
    
    def init(self):
        
        # Select random color
        self.color = random.choice(COLORS)
        
        # App layout
        with ui.VBox():
            self.people = ui.Label(flex=0)
            ui.Widget(flex=1)
            with ui.HBox(flex=2):
                ui.Widget(flex=1)
                self.canvas = ui.CanvasWidget(flex=0)
                ui.Widget(flex=1)
            ui.Widget(flex=1)
        
        # Start people-count-updater
        self._update_participants()
    
    @event.prop
    def color(self, color='#000'):
        """ The selected color for the current session. """
        return str(color)
    
    @event.connect('canvas.mouse_down')
    def _this_user_adds_paint(self, *events):
        """ Detect mouse down, emit global paint event via the relay. """
        for ev in events:
            relay.global_paint(ev.pos, self.color)
    
    @relay.connect('global_paint')  # note that we connect to relay here
    def _any_user_adds_paint(self, *events):
        """ Receive global paint event from the relay, emit local paint event. """
        # if not self.session.status:
        #     return  I think this is not required anymore. Worst case we get a warning
        for ev in events:
            self.emit('paint', ev)
    
    def _update_participants(self):
        """ Keep track of the number of participants. """
        if not self.session.status:
            return  # and dont't invoke a new call
        proxies = app.manager.get_connections(self.__class__.__name__)
        n = len(proxies)
        del proxies
        self.people.text = '%i persons are painting' % n
        app.call_later(3, self._update_participants)
    
    
    class JS:
        
        def init(self):
            super().init()
            self._ctx = self.canvas.node.getContext('2d')
        
        @event.connect('color')
        def _update_color(self, *events):
            self.canvas.style = 'border: 10px solid ' + events[-1].new_value
        
        @event.connect('!paint')
        def _paint_dot(self, *events):
            for ev in events:
                self._ctx.globalAlpha = 0.8
                self._ctx.beginPath()
                self._ctx.fillStyle = ev.color
                self._ctx.arc(ev.pos[0], ev.pos[1], 5, 0, 6.2831)
                self._ctx.fill()


if __name__ == '__main__':
    app.serve(ColabPainting)
    m = app.launch(ColabPainting)  # for use during development
    app.start()
