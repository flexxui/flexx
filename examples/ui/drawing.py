"""
This example demonstrates a simple drawing app. Useful for testing
canvas and its mouse events.
"""
from flexx import app, ui, event


class Drawing(ui.CanvasWidget):
    
    class JS:
        
        def init(self):
            super().init()
            self.ctx = self.canvas.getContext('2d')
        
        def on_mouse_move(self, *events):
            for ev in events:
                self.ctx.fillStyle = '#ff0'
                self.ctx.fillRect(ev.x-2, ev.y-2, 4, 4)
        
        def on_mouse_down(self, *events):
            for ev in events:
                self.ctx.fillStyle = '#f00'
                self.ctx.fillRect(ev.x-10, ev.y-10, 20, 20)
        
        def on_mouse_up(self, *events):
            for ev in events:
                self.ctx.fillStyle = '#00f'
                self.ctx.fillRect(ev.x-10, ev.y-10, 20, 20)


class Main(ui.Widget):
    """ Embed in larger widget to test offset.
    """
    
    CSS = """
    .flx-Widget { background: #aaf;}
    .flx-Drawing {background: #fff;}
    """
    
    def init(self):
        
        with ui.VBox():
            ui.Widget(flex=1)
            with ui.HBox(flex=2):
                ui.Widget(flex=1)
                Drawing(flex=2)
                ui.Widget(flex=1)
            ui.Widget(flex=1)


m = app.launch(Main, 'xul')
app.run()
