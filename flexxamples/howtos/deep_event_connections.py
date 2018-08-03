# doc-export: DeepEventConnections
"""
Example that demonstrates how one can connect to events deep in the
hierachy. Instead of using the star notation to select all children,
one can use a double-star to select also the children's children, and
their children, etc.
"""

from flexx import flx


class DeepEventConnections(flx.Widget):

    def init(self):
        # Put a label and some sliders deep in the hierarchy

        with flx.VBox():
            self.label = flx.Label()
            with flx.HFix(flex=1):
                for j in range(2):
                    with flx.VBox(flex=1):
                        for i in range(5):
                            flx.Slider(value=i/5)

    @flx.reaction('!children**.value')
    def on_slider_change(self, *events):
        for ev in events:
            self.label.set_text('Slider %s changed to %f' %
                                (ev.source.id, ev.new_value))


if __name__ == '__main__':
    m = flx.launch(DeepEventConnections)
    flx.run()
