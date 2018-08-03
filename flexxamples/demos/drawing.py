# doc-export: Drawing

"""
This example demonstrates a simple drawing app.
Also useful for testing canvas and its mouse / touch events.
"""

from flexx import flx


class Drawing(flx.CanvasWidget):

    CSS = """
    .flx-Drawing {background: #fff; border: 5px solid #000;}
    """

    def init(self):
        super().init()
        self.ctx = self.node.getContext('2d')
        self._last_pos = {}

        # Set mouse capturing mode
        self.set_capture_mouse(1)

        # Label to show info about the event
        self.label = flx.Label()

    def show_event(self, ev):
        if -1 in ev.touches:  # Mouse
            t = 'mouse pos: {:.0f} {:.0f}  buttons: {}'
            self.label.set_text(t.format(ev.pos[0], ev.pos[1], ev.buttons))
        else:  # Touch
            self.label.set_text('Touch ids: {}'.format(ev.touches.keys()))

    @flx.reaction('pointer_move')
    def on_move(self, *events):
        for ev in events:
            self.show_event(ev)

            # Effective way to only draw if mouse is down, but disabled for
            # sake of example. Not necessary if capture_mouse == 1.
            # if 1 not in ev.buttons:
            #     return

            # One can simply use ev.pos, but let's support multi-touch here!
            # Mouse events also have touches, with a touch_id of -1.

            for touch_id in ev.touches:
                x, y, force = ev.touches[touch_id]

                self.ctx.beginPath()
                self.ctx.strokeStyle = '#080'
                self.ctx.lineWidth = 3
                self.ctx.lineCap = 'round'
                self.ctx.moveTo(*self._last_pos[touch_id])
                self.ctx.lineTo(x, y)
                self.ctx.stroke()

                self._last_pos[touch_id] = x, y

    @flx.reaction('pointer_down')
    def on_down(self, *events):
        for ev in events:
            self.show_event(ev)

            for touch_id in ev.touches:
                x, y, force = ev.touches[touch_id]

                self.ctx.beginPath()
                self.ctx.fillStyle = '#f00'
                self.ctx.arc(x, y, 3, 0, 6.2831)
                self.ctx.fill()

                self._last_pos[touch_id] = x, y

    @flx.reaction('pointer_up')
    def on_up(self, *events):
        for ev in events:
            self.show_event(ev)

            for touch_id in ev.touches:
                x, y, force = ev.touches[touch_id]

                self.ctx.beginPath()
                self.ctx.fillStyle = '#00f'
                self.ctx.arc(x, y, 3, 0, 6.2831)
                self.ctx.fill()


class Main(flx.Widget):
    """ Embed in larger widget to test offset.
    """

    CSS = """
    .flx-Main {background: #eee;}
    """

    def init(self):

        with flx.VFix():
            flx.Widget(flex=1)
            with flx.HFix(flex=2):
                flx.Widget(flex=1)
                Drawing(flex=2)
                flx.Widget(flex=1)
            flx.Widget(flex=1)


if __name__ == '__main__':
    a = flx.App(Main)
    m = a.launch('firefox-browser')
    flx.start()
