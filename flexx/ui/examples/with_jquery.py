# doc-export: Example
"""
Example to demonstrate a jQuery widget. I'm not that big a fan of
jQuery, but this demonstrates how Flexx can interact wih other JS
frameworks.
"""

from flexx import app, ui
from flexx.pyscript import RawJS


# Associate assets needed by this app.
app.assets.associate_asset(__name__, "http://code.jquery.com/jquery-1.10.2.js")
app.assets.associate_asset(__name__, "http://code.jquery.com/ui/1.11.4/jquery-ui.js")
app.assets.associate_asset(__name__,
    "http://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css")


class DatePicker(ui.Widget):
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('input')
            self.node = self.phosphor.node
            
            RawJS('$')(self.node).datepicker()


class Example(ui.Widget):
    
    def init(self):
        
        with ui.FormLayout():
            self.start = DatePicker(title='Start date')
            self.end = DatePicker(title='End date')
            ui.Widget(flex=1)


if __name__ == '__main__':
    m = app.launch(Example, 'browser')
    app.run()
