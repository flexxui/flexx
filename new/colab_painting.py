"""
New version of the colaborative paiting example. The PyModel makes this so simple!
"""

import flexx.ui


class SharedState(flexx.PyComponent):
    
    points = app.array_prop()
    
    @app.action
    def add_point(self, x, y, color):
        self._push_prop('points', (x, y, color))
        too_much = len(self.points) - 10000
        if too_much > 0:
            self._remove_prop('points', 0, too_much)

shared = SharedState()


class ColabPainting(flexx.PyComponent):
    
    def init(self):
        self.view = ColabWidget(shared)


class ColabWidget(flexx.JSComponent):  # ----- This runs in JS

    def init(self, shared):
        self.shared = shared
        self.canvas = flexx.ui.CanvasWidget()
    
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
