# doc-export: Example
"""
Example to demonstrate a jQuery widget.
This demonstrates how Flexx can interact wih other JS frameworks.
"""

from flexx import app, ui
from flexx.pyscript import RawJS


# Associate assets needed by this app.
app.assets.associate_asset(__name__, "http://code.jquery.com/jquery-1.10.2.js")
app.assets.associate_asset(__name__, "http://code.jquery.com/ui/1.11.4/jquery-ui.js")
app.assets.associate_asset(__name__,
    "http://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css")


class DatePicker(ui.Widget):
    
    def _create_dom(self):
        global window
        node = window.document.createElement('input')
        RawJS('$')(node).datepicker()
        return node


class Example(ui.Widget):
    
    def init(self):
        
        with ui.FormLayout():
            self.start = DatePicker(title='Start date')
            self.end = DatePicker(title='End date')
            ui.Widget(flex=1)


if __name__ == '__main__':
    m = app.launch(Example, 'app')
    app.run()
