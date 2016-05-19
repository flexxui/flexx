"""
A web app that allows multiple people to colaborate in painting. People
connecting later will not see the paint that was added earlier. The
paint slowly fades (like memory) as more paint is added, so the
appearance will be more similar as people are connected longer (people
"align" as they work together). Each person is assigned a random color
(his/her "skill") which might affect how that person can best contribute
to the painting.
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
    def new_dot(self, pos, color):
        return dict(pos=pos, color=color)


@app.serve
class ColabPainting(ui.Widget):
    """ Web app for colaborative painting.
    """
    
    CSS = """
    .flx-Widget { background: #ddd; }
    .flx-CanvasWidget {
        background: #fff;
        border: 10px solid #000;
        min-width: 400px; max-width: 400px;
        min-height: 400px; max-height: 400px;
    }
    """
    
    def init(self):
        
        # Select random color
        #rgb = [str(random.randint(0, 200)) for i in range(3)]
        #self.color = 'rgb(%s)' % (', '.join(rgb))
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
        
        # Pipe messages send by the relay into this app
        relay.connect(self._push_info, 'new_dot:' + self.id)
        
        # Start people-count-updater
        self._update_participants()
    
    def _push_info(self, *events):
        if self.session.status:
            for ev in events:
                self.emit('new_dot', ev)
    
    def _update_participants(self):
        if not self.session.status:
            relay.disconnect('new_dot:' + self.id)
            return  # and dont't invoke a new call
        proxies = app.manager.get_connections(self.__class__.__name__)
        n = len(proxies)
        del proxies
        self.people.text = '%i persons are painting' % n
        app.call_later(3, self._update_participants)
    
    @event.connect('canvas.mouse_down')
    def _user_adds_paint(self, *events):
        for ev in events:
            relay.new_dot(ev.pos, self.color)
    
    @event.prop
    def color(self, color='#000'):
        """ Your color.
        """
        return str(color)
    
    class JS:
        
        def init(self):
            super().init()
            self._ctx = self.canvas.node.getContext('2d')
        
        @event.connect('color')
        def _update_color(self, *events):
            self.canvas.style = 'border: 10px solid ' + events[-1].new_value
        
        @event.connect('new_dot')
        def _paint_dot(self, *events):
            for ev in events:
                # Slowly hide old paint
                self._ctx.globalAlpha = 0.01
                self._ctx.fillStyle = '#fff'
                self._ctx.fillRect(0, 0, 400, 400)
                # Add new dot
                self._ctx.globalAlpha = 0.8
                self._ctx.beginPath()
                self._ctx.fillStyle = ev.color
                self._ctx.arc(ev.pos[0], ev.pos[1], 5, 0, 6.2831)
                self._ctx.fill()


# Create global relay
relay = Relay()

if __name__ == '__main__':
    m = app.launch(ColabPainting)  # for use during development
    app.start()
