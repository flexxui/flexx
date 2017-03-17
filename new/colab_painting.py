"""
New version of the colaborative paiting example. The PyModel makes this so simple!
"""

from flexx import app, ui


class SharedState(app.PyModel):
    
    points = app.array_prop()
    
    @app.action
    def add_point(self, x, y, color):
        self._push_prop('points', (x, y, color))
        too_much = len(self.points) - 10000
        if too_much > 0:
            self._remove_prop('points', 0, too_much)

shared = SharedState()


class ColabPainting(app.Widget):
    
    def init(self):
        self.shared = shared
    
    class JS:
        
        def init(self):
            self.canvas = ui.CanvasWidget()
        
        @app.reaction('canvas.mouse_down')
        def _mouse_down(self, *events):
            for ev in events:
                self.shared.add_point(ev.x, ev.y, 'red')  # invoke action
    
        @app.reaction
        def draw(self):
            ctx = self.canvas.node.getcontext('2d')
            for x, y, color in self.shared.points:
                ctx.fillStyle = color
                ctx.fillRect(x, y, 5, 5)
        
        # todo: when there has been no resizing of the canvas, you could even draw just the newly added points


if __name__ == '__main__':
    app.serve(ColabPainting)
    app.run()
