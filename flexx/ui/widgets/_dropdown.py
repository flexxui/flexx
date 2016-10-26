"""

.. UIExample:: 120

    from flexx import app, ui
    
    class Example(ui.Widget):
        
        def init(self):
        
            ui.ComboBox(text='chooce:', options=['foo', 'bar', 'spaaaam'])


.. UIExample:: 220

    from flexx import app, event, ui
    
    class Example(ui.Widget):
        
        CSS = '''
            .flx-DropdownContainer > .flx-TreeWidget {
                min-height: 150px;
            }
        '''
        
        def init(self):
            
            # A nice and cosy tree view
            with ui.DropdownContainer(text='Scene graph'):
                with ui.TreeWidget(max_selected=1):
                    for i in range(20):
                        ui.TreeItem(text='foo %i' % i, checked=False)
            
            # A combobox
            self.combo = ui.ComboBox(editable=True,
                                     options=('foo', 'bar', 'spaaaaaaaaam', 'egs'))
            self.label = ui.Label()
        
        class JS:
            
            @event.connect('combo.text')
            def on_combobox_text(self, *events):
                self.label.text = 'Combobox text: ' + self.combo.text
                if self.combo.selected_index is not None:
                    self.label.text += ' (index %i)' % self.combo.selected_index

"""


from ... import event
from .. import Widget

window = None


# todo: some form of autocompletetion


class BaseDropdown(Widget):
    """ Base class for drop-down-like widgets.
    """
    
    CSS = """
        
        .flx-BaseDropdown {
            display: inline-block;
            overflow: visible;
            margin: 2px;
            padding: 2px;
            border: 1px solid black;
            height: 1.7em;
        }
        
        .flx-BaseDropdown > .flx-dd-edit {
            display: none;
            max-width: 2em;  /* reset silly lineedit sizing */
            min-width: calc(100% - 1.5em);
            min-height: 1em;
            margin: 0;
            padding: 0;
            border: none;
        }
        
        .flx-BaseDropdown > .flx-dd-label {
            display: inline-block;
            min-width: calc(100% - 1.5em);
            min-height: 1em;
            user-select: none;
            -moz-user-select: none;
            -webkit-user-select: none;
            -ms-user-select: none;
        }
        
        .flx-BaseDropdown.editable-yes > .flx-dd-label {
            display: none;
        }
        .flx-BaseDropdown.editable-yes > .flx-dd-edit {
            display: inline-block;
        }
        
        .flx-BaseDropdown > .flx-dd-button {
            position: absolute;
            right: 0;
            margin: 0;
            border-left: 1px solid rgba(0, 0, 0, 0);
        }
        .flx-BaseDropdown > .flx-dd-button:hover {
            /*border-left: 1px solid black;*/
            background: rgba(128, 128, 128, 0.1);
        }
        .flx-BaseDropdown > .flx-dd-button::after {
            content: '\\23f7';  /* 2228 1F847 1F83F */
        }
        
        .flx-BaseDropdown .flx-dd-space {
            display: inline-block;
            min-width: 1em;
        }
        
        .flx-BaseDropdown > .flx-dd-strud {
            /* The strud allows to give the box a natural minimum size,
               but it should not affect the height. */
            visibility: hidden;
            overflow: hidden;
            max-height: 0;
        }
    """
    
    def init(self):
        self.tabindex = -1
    
    class JS:
        
        _HTML = """
            <span class='flx-dd-label'></span>
            <input type='text' class='flx-dd-edit'></input>
            <span>&nbsp;&nbsp;&nbsp;&nbsp;</span>
            <span class='flx-dd-button'></span>
            <div class='flx-dd-strud'>&nbsp;</span>
            """.replace('  ', '').replace('\n', '')
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('span')
            self.node = self.phosphor.node
            self.node.innerHTML = self._HTML
            
            self._label = self.node.childNodes[0]
            self._edit = self.node.childNodes[1]
            self._button = self.node.childNodes[3]
            self._strud = self.node.childNodes[4]
            
            self._label.addEventListener('click', self._but_click, 0)
            self._button.addEventListener('click', self._but_click, 0)
            self.node.addEventListener('blur', self._collapse, 0)
            
            f2 = lambda e: self._submit_text() if e.which == 13 else None
            self._edit.addEventListener('keydown', f2, False)
            self._edit.addEventListener('blur', self._submit_text, False)
        
        @event.connect('text')
        def __on_text(self, *events):
            self._label.innerHTML = self.text or '&nbsp;'  # strut it
            self._edit.value = self.text
        
        def _but_click(self):
            if self.node.classList.contains('expanded'):
                self._collapse()
            else:
                self._expand()
        
        def _submit_text(self):
            self.text = self._edit.value
        
        def _expand(self):
            self.node.classList.add('expanded')
        
        def _collapse(self):
            self.node.classList.remove('expanded')


class ComboBox(BaseDropdown):
    """
    The Combobox is a combination of a button and a popup list, optionally
    with an editable text. It can be used to select among a set of
    options in a more compact manner than a TreeWidget would.
    Optionally, the text of the combobox can be edited.
    Connect to the ``text`` and/or ``selected_index`` properties to keep
    track of interactions.
    """
        
    CSS = """
        
        .flx-ComboBox {
        }
        
        .flx-ComboBox > ul  {
            list-style-type: none;
            border: 1px solid black;
            margin: 0;
            padding: 2px;
            position: absolute;
            top: calc(1.7em - 3px);  /* matches box height */
            left: -1px;
            right: -1px;
            display: none;
        }
        .flx-ComboBox.expanded > ul {
            display: initial;
            background: white;
            z-index: 999;
        }
        
        .flx-ComboBox.expanded > ul > li:hover {
            background: rgba(128, 128, 128, 0.3);
        }
    """
    
    class Both:
        
        # Note: we don't define text on the base class, because it would be
        # the only common prop, plus we want a different docstring.
        
        @event.prop
        def text(self, v=''):
            """ The text displayed on the widget. This property is set
            when an item is selected from the dropdown menu. When editable,
            the ``text`` is also set when the text is edited by the user.
            This property is settable programatically regardless of the
            value of ``editable``.
            """
            return str(v)
        
        @event.prop
        def selected_index(self, v=None):
            """ The currently selected item index. Can be None if no item has
            been selected or when the text was changed manually (if editable).
            """
            if v is None:
                return None
            return int(v)
        
        @event.prop
        def placeholder_text(self, v=''):
            """ The placeholder text to display in editable mode.
            """
            return str(v)
        
        @event.prop
        def options(self, options=[]):
            """ A list of strings representing the options.
            """
            return tuple([str(option) for option in options])
        
        @event.prop
        def editable(self, v=False):
            """ Whether the combobox's text is editable.
            """
            return bool(v)
            
    class JS:
        
        def _init_phosphor_and_node(self):
            super()._init_phosphor_and_node()
            self._ul = window.document.createElement('ul')
            self.node.appendChild(self._ul)
            
            self._ul.addEventListener('click', self._ul_click, 0)
        
        def _ul_click(self, e):
            index = e.target.index
            if index >= 0:
                self.selected_index = index
                self.text = self.options[index]
            self._collapse()
        
        def _submit_text(self):
            self.text = self._edit.value
            self.selected_index = None
        
        @event.connect('selected_index')
        def __on_selected_index(self, *events):
            if self.selected_index is not None:
                self.text = self.options[self.selected_index]
        
        @event.connect('options')
        def __on_options(self, *events):
            while self._ul.firstChild:
                self._ul.removeChild(self._ul.firstChild)
            strud = ''
            for i, option in enumerate(self.options):
                li = window.document.createElement('li')
                li.innerHTML = option
                li.index = i
                self._ul.appendChild(li)
                strud += option + '&nbsp;&nbsp;<span class="flx-dd-space"></span><br />'
            self._strud.innerHTML = strud
        
        @event.connect('editable')
        def __on_editable(self, *events):
            if self.editable:
                self.node.classList.add('editable-yes')
                self.node.classList.remove('editable-no')
            else:
                self.node.classList.remove('editable-yes')
                self.node.classList.add('editable-no')
        
        @event.connect('placeholder_text')
        def __on_placeholder_text(self, *events):
            self._edit.placeholder = self.placeholder_text


class DropdownContainer(BaseDropdown):
    """
    A dropdown widget that shows its children when expanded. This can be
    used to e.g. make a collapsable tree widget. Some styling may be required
    for the child widget to be sized appropriately.
    """
    
    CSS = """
        .flx-DropdownContainer > .flx-Widget {
            display: none;
            position: absolute;
            top: calc(1.7em - 3px);
            left: -1px;
            right: -1px;
            min-height: 100px;
        }
        .flx-DropdownContainer.expanded > .flx-Widget {
            display: initial;
            background: white;
            z-index: 999;
        }
    """
    
    class Both:
        
        @event.prop
        def text(self, v=''):
            """ The text displayed on the widget.
            """
            return str(v)
    
    class JS:
        
        def _add_child(self, widget):
            self.node.appendChild(widget.node)
        
        def _remove_child(self, widget):
            self.node.removeChild(widget.node)
