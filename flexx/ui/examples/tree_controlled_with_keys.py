# doc-export: TreeWithControlsTester
"""
The TreeWidget offers a simple JS-side API to control highlighting of
a "current item". This example demonstrates how this can be used to control
a tree widget with keyboard controls.

This functionality is not added to the TreeWidget itself at the moment, because
its usually not the desired behavior, and its not trivial how to deal with 
consuming keys etc. Until we figure these things out, one can simply use the
code below.
"""

from flexx import event, ui, app


class TreeWithControls(ui.TreeWidget):
    """ Adds a key press handler to allow controlling the TreeWidget with 
    the arrow keys, space, and enter.
    """
    
    class JS:
        
        @event.connect('key_press')
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


class TreeWithControlsTester(ui.Widget):
    
    def init(self):
        
        self.x = TreeWithControls(max_selected=1)
        
        with self.x:
            for cat in ('foo', 'bar', 'spam'):
                with ui.TreeItem(text=cat):
                    for name in ('Martin', 'Kees', 'Hans'):
                        item = ui.TreeItem(title=name)
                        item.checked = cat=='foo' or None


m = app.launch(TreeWithControlsTester)
