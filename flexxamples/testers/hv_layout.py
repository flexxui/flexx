# doc-export: TestApp
"""
App that has a lot of HVLayouts and allows toggling their mode and orientation
with key presses. This is very convenient to test these layouts on various
browsers.
"""

from flexx import app, event, ui


class MyWidget(ui.Label):
    """ A Widget that reacts to key presses.
    """

    CSS = """
    .flx-MyWidget {
        min-width: 10px;
        min-height: 10px;
        padding: 5px;
        border: 2px solid black;
        border-radius: 5px;
    }
    """

    def init(self):
        index = self.__class__._count or 1
        self.__class__._count = index + 1

        self._base_text = str(index) + ' ' + self.text
        color = '#77f', '7f7', 'f77', 'ff5', 'f5f', '5ff', '800', '080', '008'
        self.apply_style('background:#' + color[index-1])
        self.set_wrap(1)
        self.set_flex(1)

    @event.reaction('key_down')
    def _on_key(self, *events):
        for ev in events:
            if ev.key == 'ArrowUp':
                self.set_flex(self.flex[0] + 1)
            elif ev.key == 'ArrowDown':
                self.set_flex(max(0, self.flex[0] - 1))
            elif ev.key == 'b':
                self.parent.set_mode('box')
            elif ev.key == 's':
                self.parent.set_mode('split')
            elif ev.key == 'f':
                self.parent.set_mode('fix')
            elif ev.key == 'o':
                ori = {'h': 'v', 'v': 'h'}.get(self.parent.orientation, 'h')
                self.parent.set_orientation(ori)
            elif ev.key == ']':
                with self.parent:
                    MyWidget()
            elif ev.key == '[':
                self.dispose()

    @event.reaction('parent.mode', 'flex')
    def _update_text(self, *events):
        text = self._base_text + '<br>\n'
        text += 'widget with flex (%s) ' % self.flex
        text += 'in %s %s layout.' % (self.parent.orientation, self.parent.mode)
        self.set_html(text)


class MyLayout(ui.HVLayout):
    """ A layout with some good initial values.
    """

    def init(self, ori):
        self.set_flex(1)
        self.set_orientation(ori)
        self.set_padding(8)  # so we can better see the structure

    @event.reaction
    def _track_orientation(self):
        if 'h' in self.orientation:
            self.apply_style('background:#faa;')
        else:
            self.apply_style('background:#afa;')


text = """
This is a hv layout test app. Click a widget and then hit a key to change
the layout:<br>
* Arrow up/down: increase or decrease the flex value<br>
* o: toggle the layout orientation<br>
* b, f, s: set the layout to box, fix, or split mode<br>
"""

class TestApp(ui.Widget):

    def init(self):

        with MyLayout('v') as self.s:
            self.w1 = MyWidget(text=text)

            with MyLayout('h') as self.s:
                self.w2 = MyWidget(text='hello world!')
                with MyLayout('v'):
                    self.w3 = MyWidget(text='hi')
                    self.w4 = MyWidget(text='hello world! ' * 4)
                with MyLayout('v'):
                    self.w5 = MyWidget(text='min-size: 50',
                                       style='min-width:50px; min-height:50px')
                    self.w6 = MyWidget(text='min-size: 100',
                                       style='min-width:100px; min-height:100px')
                    self.w7 = MyWidget(text='min-size: 150',
                                       style='min-width:150px; min-height:150px')

            with ui.Widget(flex=1):
                with MyLayout('h'):
                    self.w8 = MyWidget()
                    self.w9 = MyWidget(style='min-width:250px;')
                    self.w8 = MyWidget()


if __name__ == '__main__':
    m = app.launch(TestApp)
    app.run()
