# doc-export: Drawing

"""
This example demonstrates a simple drawing app. Useful for testing
canvas and its mouse events.
"""

from flexx import app, ui, event


class Drawing(ui.CanvasWidget):
    
    CSS = """
    .flx-Drawing {background: #fff; border: 5px solid #000;}
    """
    
    class JS:
        
        def init(self):
            super().init()
            self.ctx = self.node.getContext('2d')
            self._last_ev = None
        
        @event.connect('mouse_move')
        def on_move(self, *events):
            for ev in events:
                last_ev = self._last_ev
                if 1 in ev.buttons and last_ev is not None:
                    self.ctx.beginPath()
                    self.ctx.strokeStyle = '#080'
                    self.ctx.lineWidth = 3
                    self.ctx.lineCap = 'round'
                    self.ctx.moveTo(*last_ev.pos)
                    self.ctx.lineTo(*ev.pos)
                    self.ctx.stroke()
                    self._last_ev = ev
        
        @event.connect('mouse_down')
        def on_down(self, *events):
            for ev in events:
                self.ctx.beginPath()
                self.ctx.fillStyle = '#f00'
                self.ctx.arc(ev.pos[0], ev.pos[1], 3, 0, 6.2831)
                self.ctx.fill()
                self._last_ev = ev
        
        @event.connect('mouse_up')
        def on_up(self, *events):
            for ev in events:
                self.ctx.beginPath()
                self.ctx.fillStyle = '#00f'
                self.ctx.arc(ev.pos[0], ev.pos[1], 3, 0, 6.2831)
                self.ctx.fill()
            self._last_ev = None


class Main(ui.Widget):
    """ Embed in larger widget to test offset.
    """
    
    CSS = """
    .flx-Drawing {background: #fff; border: 5px solid #000;}
    """
    
    def init(self):
        
        with ui.VBox():
            ui.Widget(flex=1)
            with ui.HBox(flex=2):
                ui.Widget(flex=1)
                Drawing(flex=2)
                ui.Widget(flex=1)
            ui.Widget(flex=1)

if __name__ == '__main__':
    m = app.launch(Main, 'app')
    app.start()
