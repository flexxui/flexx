# doc-export: Example
"""
Example to demonstrate a jQuery widget.
This demonstrates how Flexx can interact wih other JS frameworks.
"""

from pscript import RawJS

from flexx import flx


# Associate assets needed by this app.
flx.assets.associate_asset(__name__, "http://code.jquery.com/jquery-1.10.2.js")
flx.assets.associate_asset(__name__, "http://code.jquery.com/ui/1.11.4/jquery-ui.js")
flx.assets.associate_asset(__name__,
    "http://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css")


class DatePicker(flx.Widget):

    def _create_dom(self):
        global window
        node = window.document.createElement('input')
        RawJS('$')(node).datepicker()
        return node


class Example(flx.Widget):

    def init(self):

        with flx.FormLayout():
            self.start = DatePicker(title='Start date')
            self.end = DatePicker(title='End date')
            flx.Widget(flex=1)


if __name__ == '__main__':
    m = flx.launch(Example, 'app')
    flx.run()
