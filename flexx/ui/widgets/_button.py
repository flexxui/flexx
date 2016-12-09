"""

Simple example:

.. UIExample:: 50

    b = ui.Button(text="Push me")


Example with interaction:

.. UIExample:: 200

    from flexx import app, ui, event

    class Example(ui.BoxPanel):

        def init(self):
            with ui.VBox():
                self.b1 = ui.Button(text='apple')
                self.b2 = ui.Button(text='banana')
                self.b3 = ui.Button(text='pear')
                self.buttonlabel= ui.Label(text='...')
            with ui.VBox():
                self.r1 = ui.RadioButton(text='apple')
                self.r2 = ui.RadioButton(text='banana')
                self.r3 = ui.RadioButton(text='pear')
                self.radiolabel = ui.Label(text='...')
            with ui.VBox():
                self.c1 = ui.CheckBox(text='apple')
                self.c2 = ui.CheckBox(text='banana')
                self.c3 = ui.CheckBox(text='pear')
                self.checklabel = ui.Label(text='...')

        class JS:

            @event.connect('b1.mouse_click', 'b2.mouse_click','b3.mouse_click',  )
            def _button_clicked(self, *events):
                ev = events[-1]
                self.buttonlabel.text = 'Clicked on the ' + ev.source.text

            @event.connect('r1.checked', 'r2.checked','r3.checked')
            def _radio_changed(self, *events):
                # There will also be events for radio buttons being unchecked, but
                # Flexx ensures that the last event is for the one being checked
                ev = events[-1]
                self.radiolabel.text = 'Selected the ' + ev.source.text

            @event.connect('c1.checked', 'c2.checked','c3.checked',  )
            def _check_changed(self, *events):
                selected = [c.text for c in (self.c1, self.c2, self.c3) if c.checked]
                if selected:
                    self.checklabel.text = 'Selected: ' + ', '.join(selected)
                else:
                    self.checklabel.text = 'None selected'

"""

from ... import event
from . import Widget


class BaseButton(Widget):
    """ Abstract button class.
    """

    CSS = """

    .flx-BaseButton {
        white-space: nowrap;
    }

    .flx-RadioButton, .flx-CheckBox {
        margin-left: 0.5em;
        margin-right: 0.5em;
    }

    .flx-RadioButton label, .flx-CheckBox label {
        margin-left: 0.2em;
    }

    """

    class Both:

        @event.prop
        def text(self, v=''):
            """ The text on the button.
            """
            return str(v)

        @event.prop
        def checked(self, v=False):
            """ Whether the button is checked. Applicable for CheckBox,
            RadioButton and ToggleButton.
            """
            return bool(v)

        @event.prop
        def disabled(self, v=False):
            """ Whether the button is disabled.
            """
            return bool(v)

    class JS:

        @event.emitter
        def mouse_click(self, e):
            """ Event emitted when the mouse is clicked.

            See mouse_down() for a description of the event object.
            """
            return self._create_mouse_event(e)


class Button(BaseButton):
    """ A push button.
    """
    class JS:
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('button')
            self.node = self.phosphor.node
            self.node.addEventListener('click', self.mouse_click, 0)

        @event.connect('text')
        def __text_changed(self, *events):
            self.node.innerHTML = events[-1].new_value

        @event.connect('disabled')
        def __disabled_changed(self, *events):
            if events[-1].new_value:
                self.node.setAttribute("disabled", "disabled")
            else:
                self.node.removeAttribute("disabled")


class ToggleButton(BaseButton):
    """ A button that can be toggled. It behaves like a checkbox, while
    looking more like a regular button.
    """
    CSS = """
        .flx-ToggleButton-checked {
            color: #00B;
            font-weight: bolder;
        }
    """

    class JS:
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('button')
            self.node = self.phosphor.node
            self.node.addEventListener('click', self.mouse_click, 0)

        @event.connect('text')
        def __text_changed(self, *events):
            self.node.innerHTML = events[-1].new_value

        @event.connect('mouse_click')
        def __toggle_checked(self, *events):
            self.checked = not self.checked

        @event.connect('checked')
        def __check_changed(self, *events):
            if self.checked:
                self.node.classList.add('flx-ToggleButton-checked')
            else:
                self.node.classList.remove('flx-ToggleButton-checked')


class RadioButton(BaseButton):
    """ A radio button. Of any group of radio buttons that share the
    same parent, only one can be active.
    """

    class JS:
        def _init_phosphor_and_node(self):
            self.phosphor = p = self._create_phosphor_widget('div')
            template = '<input type="radio" id="ID"><label for="ID">'
            p.node.innerHTML = template.replace('ID', self.id)
            self.node = p.node.childNodes[0]
            self.text_node = p.node.childNodes[1]

            self.node.addEventListener('click', self._check_radio_click, 0)

        @event.connect('parent')
        def __update_group(self, *events):
            if self.parent:
                self.node.name = self.parent.id

        @event.connect('text')
        def __text_changed(self, *events):
            #self.node.innerHTML = events[-1].new_value
            self.text_node.innerHTML = events[-1].new_value

        @event.connect('checked')
        def __check_changed(self, *events):
            self.node.checked = self.checked

        def _check_radio_click(self, ev):
            """ This method is called on JS a click event. We *first* update
            the checked properties, and then emit the Flexx click event.
            That way, one can connect to the click event and have an
            up-to-date checked props (even on Py).
            """
            # Turn off any radio buttons in the same group
            if self.parent:
                for child in self.parent.children:
                    if isinstance(child, RadioButton) and child is not self:
                        child.checked = child.node.checked
            # Turn on this button (last)
            self.checked = self.node.checked
            # Process actual click event
            self.mouse_click(ev)


class CheckBox(BaseButton):
    """ A checkbox button.
    """

    class JS:
        def _init_phosphor_and_node(self):
            self.phosphor = p = self._create_phosphor_widget('div')
            template = '<input type="checkbox" id="ID"><label for="ID">'
            p.node.innerHTML = template.replace('ID', self.id)
            self.node = p.node.childNodes[0]
            self.text_node = p.node.childNodes[1]

            self.node.addEventListener('click', self.mouse_click, 0)
            self.node.addEventListener('change', self._check_changed_from_dom, 0)

        @event.connect('text')
        def __text_changed(self, *events):
            #self.node.innerHTML = events[-1].new_value
            self.text_node.innerHTML = events[-1].new_value

        @event.connect('checked')
        def __check_changed(self, *events):
            self.node.checked = self.checked

        def _check_changed_from_dom(self, ev):
            self.checked = self.node.checked
