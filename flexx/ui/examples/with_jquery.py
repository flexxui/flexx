"""
Example to demonstrate a jQuery widget. I'm not that big a fan of
jQuery, but this demonstrates how Flexx can interact wih other JS
frameworks.
"""

from flexx import app, ui


class DatePicker(ui.Widget):
    
    class JS:
        def init(self):
            self.p = phosphor.createWidget('input')  # noqa
            self._make_picker(self.p.node)
        
        def _make_picker(node):
            """ $(node).datepicker(); // we cannot use $ as a variable name in PyScript
            """


class Example(ui.Widget):
    
    def init(self):
        
        # Two ways to add assets
        if True:
            # The client will load these assets from the URL's. Good for web apps.
            ura = self.session.use_remote_asset
            ura("http://code.jquery.com/jquery-1.10.2.js")
            ura("http://code.jquery.com/ui/1.11.4/jquery-ui.js")
            ura("http://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css")
        else:
            # Flexx will download the assets and serve them to the client.
            # Good for desktop/exported apps.
            aga = self.session.add_global_asset
            aga("jquery.js", "http://code.jquery.com/jquery-1.10.2.js")
            aga("jquery-ui.js", "http://code.jquery.com/ui/1.11.4/jquery-ui.js")
            aga("jquery-ui.css", 
                "http://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css")
        
        with ui.FormLayout():
            self.start = DatePicker(title='Start date')
            self.end = DatePicker(title='End date')
            ui.Widget(flex=1)


if __name__ == '__main__':
    app.launch(Example)
    app.run()
