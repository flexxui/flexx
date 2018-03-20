"""
Example that shows animated circles. Note that it would be more efficient
to use a canvas for this sort of thing.
"""

from time import time

from flexx import app, ui


class Circle(ui.Label):
    
    CSS = """
    .flx-Circle {
        background: #f00;
        border-radius: 10px;
        width: 10px;
        height: 10px;
    }
    """

class Circles(ui.Widget):
    
    def init(self):
        with ui.PinboardLayout():
            self._circles = [Circle() for i in range(32)]
        self.tick()
    
    def tick(self):
        global Math, window
        t = time()
        for i, circle in enumerate(self._circles):
            x = Math.sin(i*0.2 + t) * 30 + 50
            y = Math.cos(i*0.2 + t) * 30 + 50
            circle.apply_style(dict(left=x + '%', top=y + '%'))
        window.setTimeout(self.tick, 30)


if __name__ == '__main__':
    m = app.App(Circles).launch('app')
    app.run()
