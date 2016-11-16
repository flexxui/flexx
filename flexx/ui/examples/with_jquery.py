# doc-export: Example
"""
Example to demonstrate a jQuery widget. I'm not that big a fan of
jQuery, but this demonstrates how Flexx can interact wih other JS
frameworks.
"""

from flexx import app, ui

# Define assets needed by this app. Creating them here is enough
jquery = app.Asset("http://code.jquery.com/jquery-1.10.2.js")
jquery_ui = app.Asset("http://code.jquery.com/ui/1.11.4/jquery-ui.js")
jq_css = app.Asset("http://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css")

# In the above notation, the assets are "remote assets"; the client will
# load them by itself. They can also be defined in a way that makes Flexx
# load the source and then serve it to the client:
#
# jquery = app.Asset("jquery.js", "http://code.jquery.com/jquery-1.10.2.js")
#
# When exporting an app, one has the option to embed/include remote assets.


class DatePicker(ui.Widget):
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('input')
            self.node = self.phosphor.node
            self._make_picker(self.node)
        
        def _make_picker(node):
            """ $(node).datepicker(); // we cannot use $ as a variable name in PyScript
            """


class Example(ui.Widget):
    
    def init(self):
        
        with ui.FormLayout():
            self.start = DatePicker(title='Start date')
            self.end = DatePicker(title='End date')
            ui.Widget(flex=1)


if __name__ == '__main__':
    m = app.launch(Example, 'firefox')
    app.run()
