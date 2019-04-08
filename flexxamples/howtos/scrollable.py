# doc-export: ScrollExample
"""
Example that shows how to make the content of a widget scrollable.
It comes down to setting a style attribute: "overflow-y: auto;".
"""

from flexx import flx


class ScrollExample(flx.Widget):

    CSS = """
    .flx-ScrollExample {
        overflow-y: scroll;  // scroll or auto
    }
    """

    def init(self):

        with flx.Widget():
            for i in range(100):
                flx.Button(text="button " + str(i))


if __name__ == '__main__':
    m = flx.launch(ScrollExample)
    flx.run()
