"""
Simple use of a the markdown widget,
using a custom widget that is populated in its ``init()``.
"""

from flexx import app, event, ui, flx


class Example(flx.Widget):

    def init(self):
        content = "# Welcome\n\n" \
            "This flexx app is now served with flask! "
        ui.Markdown(content=content, style='background:#EAECFF;')

if __name__ == '__main__':
    m = flx.launch(Example, 'default-browser', backend='flask')
    flx.run()
