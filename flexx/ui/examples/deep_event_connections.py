# doc-export: DeepEventConnections
"""
Example that demonstartes how one can connect to events deep in the
hierachy. Instead of using the star notation to select all children,
one can use a double-star to select also the children's children, and
their children, etc.
"""

from flexx import app, event, ui


class DeepEventConnections(ui.Widget):
    
    def init(self):
        # Put a label and some sliders deep in the hierarchy
        
        with ui.HBox():
            with ui.VBox(flex=1) as self.box:
                self.label = ui.Label()
                for i in range(5):
                    ui.Slider(value=i/5)
    
    class JS:
        
        @event.connect('children**.value')
        def on_slider_change(self, *events):
            # Show sum of slider values in the label
            v = 0
            for s in self.box.children:
                if hasattr(s, 'value'):
                    v += s.value
            self.label.text = 'Sum of slider values is ' + str(v)


if __name__ == '__main__':
    m = app.launch(DeepEventConnections)
    app.run()
