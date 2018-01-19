"""
A web app that allows multiple people to colaborate in painting. People
connecting later will not see the "paint" that was added earlier. Each
person is assigned a random color which affects how that person can
best contribute to the painting.

This app might be running at the demo server: http://flexx1.zoof.io
"""

import random
import asyncio

from flexx import app, event, ui

COLORS = ('#eee', '#999', '#555', '#111', 
          '#f00', '#0f0', '#00f', '#ff0', '#f0f', '#0ff',
          '#a44', '#4a4', '#44a', '#aa4', '#afa', '#4aa',
          )


class Relay(event.Component):
    """ Global object to relay paint events to all participants.
    """
    @event.emitter
    def add_paint_for_all(self, pos, color):
        return dict(pos=pos, color=color)


# Create global relay object, shared by all connections
relay = Relay()


class ColabPainting(app.PyComponent):
    """ The Python side of the app. There is one instance per connection.
    """
    
    color = event.StringProp('#000', settable=True, doc="Paint color")
    
    status = event.StringProp('', settable=True, doc="Status text")
    
    def init(self):
        self.set_color(random.choice(COLORS))
        self.widget = ColabPaintingView(self)
        self._update_participants()
    
    @event.action
    def add_paint(self, pos):
        """ Add paint at the specified position.
        """
        relay.add_paint_for_all(pos, self.color)
    
    @relay.reaction('add_paint_for_all')  # note that we connect to relay here
    def _any_user_adds_paint(self, *events):
        """ Receive global paint event from the relay, invoke action on view.
        """
        for ev in events:
            self.widget.add_paint_to_canvas(ev.pos, ev.color)
    
    def _update_participants(self):
        """ Keep track of the number of participants.
        """
        if not self.session.status:
            return  # and dont't invoke a new call
        proxies = app.manager.get_connections(self.__class__.__name__)
        n = len(proxies)
        del proxies
        self.set_status('%i persons are painting' % n)
        asyncio.get_event_loop().call_later(3, self._update_participants)


class ColabPaintingView(ui.Widget):
    """ The part of the app that runs in the browser.
    """
    
    CSS = """
    .flx-ColabPaintingView { background: #ddd; }
    .flx-ColabPaintingView .flx-CanvasWidget {
        background: #fff;
        border: 10px solid #000;
        min-width: 400px; max-width: 400px;
        min-height: 400px; max-height: 400px;
    }
    """
    
    def init(self, model):
        super().init()
        self.model = model
        
        # App layout
        with ui.VBox():
            ui.Label(flex=0, text=lambda: model.status)
            ui.Widget(flex=1)
            with ui.HBox(flex=2):
                ui.Widget(flex=1)
                self.canvas = ui.CanvasWidget(flex=0)
                ui.Widget(flex=1)
            ui.Widget(flex=1)
        
        # Init context to draw to
        self._ctx = self.canvas.node.getContext('2d')

    @event.reaction
    def __update_color(self):
        self.canvas.apply_style('border: 10px solid ' + self.model.color)
    
    @event.reaction('canvas.mouse_down')
    def __on_click(self, *events):
        for ev in events:
            self.model.add_paint(ev.pos)
    
    @event.action
    def add_paint_to_canvas(self, pos, color):
        """ Actually draw a dot on the canvas.
        """
        self._ctx.globalAlpha = 0.8
        self._ctx.beginPath()
        self._ctx.fillStyle = color
        self._ctx.arc(pos[0], pos[1], 5, 0, 6.2831)
        self._ctx.fill()


if __name__ == '__main__':
    a = app.App(ColabPainting)
    a.serve()
    # m = a.launch('browser')  # for use during development
    app.start()
