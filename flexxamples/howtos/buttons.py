# doc-export: Example
"""
Example demonstrating three kinds of buttons.
"""

from flexx import flx


class Example(flx.HFix):

    def init(self):
        with flx.VBox():
            self.b1 = flx.Button(text='apple')
            self.b2 = flx.Button(text='banana')
            self.b3 = flx.Button(text='pear')
            self.buttonlabel= flx.Label(text='...')
        with flx.VBox():
            self.r1 = flx.RadioButton(text='apple')
            self.r2 = flx.RadioButton(text='banana')
            self.r3 = flx.RadioButton(text='pear')
            self.radiolabel = flx.Label(text='...')
        with flx.VBox():
            self.c1 = flx.ToggleButton(text='apple')
            self.c2 = flx.ToggleButton(text='banana')
            self.c3 = flx.ToggleButton(text='pear')
            self.checklabel = flx.Label(text='...')


    @flx.reaction('b1.pointer_click', 'b2.pointer_click', 'b3.pointer_click')
    def _button_clicked(self, *events):
        ev = events[-1]
        self.buttonlabel.set_text('Clicked on the ' + ev.source.text)

    @flx.reaction('r1.checked', 'r2.checked', 'r3.checked')
    def _radio_changed(self, *events):
        # There will also be events for radio buttons being unchecked, but
        # Flexx ensures that the last event is for the one being checked
        ev = events[-1]
        self.radiolabel.set_text('Selected the ' + ev.source.text)

    @flx.reaction('c1.checked', 'c2.checked', 'c3.checked')
    def _check_changed(self, *events):
        selected = [c.text for c in (self.c1, self.c2, self.c3) if c.checked]
        if selected:
            self.checklabel.set_text('Selected: ' + ', '.join(selected))
        else:
            self.checklabel.set_text('None selected')


if __name__ == '__main__':
    m = flx.launch(Example)
    flx.run()
