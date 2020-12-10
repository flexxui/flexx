"""
Simple use of a dropdown,
"""

from flexx import app, event, ui, flx

class Example(ui.Widget):

    def init(self):
        # A combobox
        self.combo = ui.ComboBox(editable=True,
                                 options=('foo', 'bar', 'spaaaaaaaaam', 'eggs'))
        self.label = ui.Label()

#         @event.connect('combo.text')
#         def on_combobox_text(self, *events):
#             self.label.text = 'Combobox text: ' + self.combo.text
#             if self.combo.selected_index is not None:
#                 self.label.text += ' (index %i)' % self.combo.selected_index

if __name__ == '__main__':
     m = flx.launch(Example, 'default-browser')
     flx.run()
