"""
Simple use of a dropdown containing a tree widget
"""

from flexx import app, event, ui, flx


class Example(ui.Widget):

    CSS = '''
        .flx-DropdownContainer > .flx-TreeWidget {
            min-height: 150px;
        }
    '''

    def init(self):
        # A nice and cosy tree view
        with ui.DropdownContainer(text='Scene graph'):
            with ui.TreeWidget(max_selected=1):
                for i in range(20):
                    ui.TreeItem(text='foo %i' % i, checked=False)


if __name__ == '__main__':
    m = flx.launch(Example)
    flx.run()
