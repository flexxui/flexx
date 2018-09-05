# doc-export: KeyboardControlsTester
"""
The ComboBox can be controlled with the keyboard when it is expanded.

The TreeWidget offers a simple JS-side API to control highlighting of
a "current item". This example demonstrates how this can be used to control
a tree widget with keyboard controls.

The keyboard functionality is not added to the TreeWidget by default, because
its usually not the desired behavior, and its not trivial how to deal with
consuming keys. Further, an application may want to control the tree widget
even when it does not have focus.
"""

from flexx import flx


class TreeWithControls(flx.TreeWidget):
    """ Adds a key press handler to allow controlling the TreeWidget with
    the arrow keys, space, and enter.
    """

    @flx.emitter
    def key_down(self, e):
        """Overload key_down emitter to prevent browser scroll."""
        ev = self._create_key_event(e)
        if ev.key.startswith('Arrow'):
            e.preventDefault()
        return ev

    @flx.reaction('key_down')
    def _handle_highlighting(self, *events):
        for ev in events:
            if ev.modifiers:
                continue
            if ev.key == 'Escape':
                self.highlight_hide()
            elif ev.key == ' ':
                if self.max_selected == 0:  # space also checks if no selection
                    self.highlight_toggle_checked()
                else:
                    self.highlight_toggle_selected()
            elif ev.key == 'Enter':
                self.highlight_toggle_checked()
            elif ev.key == 'ArrowRight':
                item = self.highlight_get()
                if item and item.items:
                    item.collapsed = None
            elif ev.key == 'ArrowLeft':
                item = self.highlight_get()
                if item and item.items:
                    item.collapsed = True
            elif ev.key == 'ArrowDown':
                self.highlight_show(1)
            elif ev.key == 'ArrowUp':
                self.highlight_show(-1)


class KeyboardControlsTester(flx.Widget):

    def init(self):

        combo_options = ['Paris', 'New York', 'Enschede', 'Tokio']

        with flx.HBox():
            self.tree = TreeWithControls(flex=1, max_selected=1)
            with flx.VBox(flex=1):
                self.combo = flx.ComboBox(options=combo_options, editable=True)
                flx.Widget(flex=1)  # combobox needs space below it to show dropdown

        with self.tree:
            for cat in ('foo', 'bar', 'spam'):
                with flx.TreeItem(text=cat):
                    for name in ('Martin', 'Kees', 'Hans'):
                        item = flx.TreeItem(title=name)
                        item.set_checked(cat=='foo' or None)

    @flx.reaction('combo.text')
    def _combo_text_changed(self, *events):
        for ev in events:
            print('combo text is now', ev.new_value)


if __name__ == '__main__':
    m = flx.launch(KeyboardControlsTester)
    flx.run()
