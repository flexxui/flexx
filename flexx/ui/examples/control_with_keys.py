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

from flexx import app, event, ui


class TreeWithControls(ui.TreeWidget):
    """ Adds a key press handler to allow controlling the TreeWidget with 
    the arrow keys, space, and enter.
    """

    @event.emitter
    def key_down(self, e):
        """Overload key_down emitter to prevent browser scroll."""
        ev = self._create_key_event(e)
        if ev.key.startswith('Arrow'):
            e.preventDefault()
        return ev
    
    @event.reaction('key_down')
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


class KeyboardControlsTester(ui.Widget):
    
    def init(self):
        
        combo_options = ['Paris', 'New York', 'Enschede', 'Tokio']
        
        with ui.HBox():
            self.tree = TreeWithControls(flex=1, max_selected=1)
            self.combo = ui.ComboBox(flex=1, options=combo_options, editable=True)
        
        with self.tree:
            for cat in ('foo', 'bar', 'spam'):
                with ui.TreeItem(text=cat):
                    for name in ('Martin', 'Kees', 'Hans'):
                        item = ui.TreeItem(title=name)
                        item.set_checked(cat=='foo' or None)
    
    @event.reaction('combo.text')
    def _combo_text_changed(self, *events):
        for ev in events:
            print('combo text is now', ev.new_value)


if __name__ == '__main__':
    m = app.launch(KeyboardControlsTester)
    app.run()
