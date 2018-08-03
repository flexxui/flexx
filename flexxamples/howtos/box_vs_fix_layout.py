# doc-export: Boxes
"""
Example that puts box and fix mode HVLayout's side-by-side. You can see how
box mode takes the natural size of content into account, making it
more suited for low-level layout. For higher level layout (e.g. the two
main panels in this example) the fix or split mode is more appropriate.
"""

from flexx import flx


class Panel(flx.Label):
    CSS = '.flx-Panel {background: #66dd88; color: #FFF; padding: 1px;}'


class Boxes(flx.Widget):

    def init(self):

        with flx.HSplit():

            with flx.VBox(flex=1):

                flx.Label(html='<b>Box mode</b> (aware of natural size)')
                flx.Label(text='flex: 1, sub-flexes: 0, 0, 0')
                with flx.HBox(flex=1):
                    Panel(text='A', flex=0)
                    Panel(text='B', flex=0)
                    Panel(text='C is a bit longer', flex=0)
                flx.Label(text='flex: 0, sub-flexes: 1, 1, 1')
                with flx.HBox(flex=0):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=1)
                    Panel(text='C is a bit longer', flex=1)
                flx.Label(text='flex: 1, sub-flexes: 1, 0, 2')
                with flx.HBox(flex=1):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=0)
                    Panel(text='C is a bit longer', flex=2)
                flx.Label(text='flex: 2, sub-flexes: 1, 2, 3')
                with flx.HBox(flex=2):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=2)
                    Panel(text='C is a bit longer', flex=3)

            with flx.VBox(flex=1):

                flx.Label(html='<b>Fix mode</b> (high level layout)')
                flx.Label(text='flex: 1, sub-flexes: 0, 0, 0')
                with flx.HFix(flex=1):
                    Panel(text='A', flex=0)
                    Panel(text='B', flex=0)
                    Panel(text='C is a bit longer', flex=0)
                flx.Label(text='flex: 0 (collapses), sub-flexes: 1, 1, 1')
                with flx.HFix(flex=0):
                    Panel(text='A', flex=1, style='min-height:5px;')
                    Panel(text='B', flex=1)
                    Panel(text='C is a bit longer', flex=1)
                flx.Label(text='flex: 1, sub-flexes: 1, 0, 2')
                with flx.HFix(flex=1):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=0)
                    Panel(text='C is a bit longer', flex=2)
                flx.Label(text='flex: 2, sub-flexes: 1, 2, 3')
                with flx.HFix(flex=2):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=2)
                    Panel(text='C is a bit longer', flex=3)


if __name__ == '__main__':
    m = flx.launch(Boxes)
    flx.run()
