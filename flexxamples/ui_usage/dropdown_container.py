"""
Simple use of a dropdown containing a tree widget
"""

from flexx import flx


class Example(flx.Widget):

    CSS = '''
        .flx-DropdownContainer > .flx-TreeWidget {
            min-height: 150px;
        }
    '''

    def init(self):
        # A nice and cosy tree view
        with flx.DropdownContainer(text='Scene graph'):
            with flx.TreeWidget(max_selected=1):
                for i in range(20):
                    flx.TreeItem(text='foo %i' % i, checked=False)


if __name__ == '__main__':
    m = flx.launch(Example)
    flx.run()
