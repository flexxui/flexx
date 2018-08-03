# doc-export: Example
"""
An example with a tree widget, demonstrating e.g. theming, checkable items,
sub items.
"""

from flexx import flx


class Example(flx.Widget):

    CSS = '''
    .flx-TreeWidget {
        background: #000;
        color: #afa;
    }
    '''

    def init(self):

        with flx.HSplit():

            self.label = flx.Label(flex=1, style='overflow-y: scroll;')

            with flx.TreeWidget(flex=1, max_selected=1) as self.tree:
                for t in ['foo', 'bar', 'spam', 'eggs']:
                    with flx.TreeItem(text=t, checked=None):
                        for i in range(4):
                            item2 = flx.TreeItem(text=t + ' %i' % i, checked=False)
                            if i == 2:
                                with item2:
                                    flx.TreeItem(title='A', text='more info on A')
                                    flx.TreeItem(title='B', text='more info on B')

    @flx.reaction('tree.children**.checked', 'tree.children**.selected',
                    'tree.children**.collapsed')
    def on_event(self, *events):
        for ev in events:
            id = ev.source.title or ev.source.text
            if ev.new_value:
                text = id + ' was ' + ev.type
            else:
                text = id + ' was ' + 'un-' + ev.type
            self.label.set_html(text + '<br />' + self.label.html)


if __name__ == '__main__':
    m = flx.launch(Example)
    flx.run()
