# doc-export: Split
"""
Splitter widgets are cool!
"""

from flexx import flx


class Split(flx.Widget):

    def init(self):

        with flx.HSplit():
            flx.Widget(style='background:#f00')
            with flx.VSplit():
                flx.Widget(style='background:#0f0')
                with flx.HSplit():
                    flx.Widget(style='background:#ff0')
                    with flx.VSplit():
                        flx.Widget(style='background:#f0f')
                        with flx.HSplit():
                            flx.Widget(style='background:#0ff')
                            flx.Widget(style='background:#00f')


if __name__ == '__main__':
    m = flx.launch(Split)
    flx.run()
