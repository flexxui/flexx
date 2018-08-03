"""
This example is intended to test mouse/touch events.
"""

from time import time

from flexx import flx


class Test(flx.Widget):

    def init(self):
        self.t = time()

        with flx.HFix():
            self.label1 = flx.Label(flex=2, style='overflow-y:scroll; font-size:60%;')
            flx.Widget(flex=1)
            with flx.VFix(flex=2):
                flx.Widget(flex=1)
                test_widget1 = flx.Widget(flex=2, style='background: #afa;')
                flx.Widget(flex=1)
                test_widget2 = flx.Widget(flex=2, style='background: #faa;')
                flx.Widget(flex=1)
            flx.Widget(flex=1)
            self.label2 = flx.Label(flex=1, style='overflow-y:scroll; font-size:60%;')

        for name in ['pointerdown', 'pointermove', 'pointerup', 'pointercancel',
                     'mousedown', 'mousemove', 'mouseup', 'click', 'dblclick',
                     'touchstart', 'touchmove', 'touchend', 'touchcancel'
                     ]:
            test_widget1.node.addEventListener(name,
                lambda e: self.show_event1(e.type))

        def reaction(*events):
            for ev in events:
                self.show_event2(ev.type)

        test_widget2.reaction(reaction,
                              'pointer_down', 'pointer_move', 'pointer_up',
                              'pointer_cancel',
                              'pointer_click', 'pointer_double_click',
                              )

    @flx.action
    def show_event1(self, name):
        dt = time() - self.t
        lines = self.label1.html.split('<br>')
        lines = lines[:200]
        lines.insert(0, f'{dt:.1f} {name}')
        self.label1.set_html('<br>'.join(lines))

    @flx.action
    def show_event2(self, name):
        dt = time() - self.t
        lines = self.label2.html.split('<br>')
        lines = lines[:200]
        lines.insert(0, f'{dt:.1f} {name}')
        self.label2.set_html('<br>'.join(lines))


a = flx.App(Test)
m = a.launch()
flx.run()
