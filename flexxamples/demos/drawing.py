# doc-export: Drawing

"""
This example demonstrates a simple drawing app.
Also useful for testing canvas and its mouse events.
"""

from flexx import flx


class Drawing(flx.CanvasWidget):
    
    CSS = """
    .flx-Drawing {background: #fff; border: 5px solid #000;}
    """

    def init(self):
        super().init()
        self.ctx = self.node.getContext('2d')
        self._last_pos = (0, 0)
        
        # Set mouse capturing mode
        self.set_capture_mouse(1)
        
        # Label to show current mouse position
        self.wpos = flx.Label()
    
    def show_pos(self, ev):
        self.wpos.set_text('pos: %s  buttons: %s' % (ev.pos, ev.buttons))
    
    @flx.reaction('mouse_move')
    def on_move(self, *events):
        for ev in events:
            
            # Effective way to only draw if mouse is down, but disabled for
            # sake of example. Not necessary if capture_mouse == 1.
            # if 1 not in ev.buttons:
            #     return
            
            self.ctx.beginPath()
            self.ctx.strokeStyle = '#080'
            self.ctx.lineWidth = 3
            self.ctx.lineCap = 'round'
            self.ctx.moveTo(*self._last_pos)
            self.ctx.lineTo(*ev.pos)
            self.ctx.stroke()
            self._last_pos = ev.pos
            self.show_pos(ev)
    
    @flx.reaction('mouse_down')
    def on_down(self, *events):
        print('down!')
        for ev in events:
            self.ctx.beginPath()
            self.ctx.fillStyle = '#f00'
            self.ctx.arc(ev.pos[0], ev.pos[1], 3, 0, 6.2831)
            self.ctx.fill()
            self._last_pos = ev.pos
            self.show_pos(ev)
    
    @flx.reaction('mouse_up')
    def on_up(self, *events):
        print('up!')
        for ev in events:
            self.ctx.beginPath()
            self.ctx.fillStyle = '#00f'
            self.ctx.arc(ev.pos[0], ev.pos[1], 3, 0, 6.2831)
            self.ctx.fill()
            self.show_pos(ev)


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
    m = flx.launch(Main, 'app')
    flx.start()
