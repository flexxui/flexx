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
                                     options=('foo', 'bar', 'spaaaaaaaaam', 'eggs'))
            self.label = ui.Label()
        
        class JS:
            
            @event.connect('combo.text')
            def on_combobox_text(self, *events):
                self.label.text = 'Combobox text: ' + self.combo.text
                if self.combo.selected_index is not None:
                    self.label.text += ' (index %i)' % self.combo.selected_index

"""

from collections import OrderedDict

from ...pyscript import window, this_is_js
from ... import event
from .. import Widget


# todo: some form of autocompletetion


class BaseDropdown(Widget):
    """ Base class for drop-down-like widgets.
    """
    
    CSS = """
        
        .flx-BaseDropdown {
            display: inline-block;
            overflow: visible;
            margin: 0;
            padding: 2px;
            border: 1px solid black;
            min-height: 1.7em;
            max-height: 1.7em;
            white-space: nowrap; /* keep label and but on-line */
        }
        
        .flx-BaseDropdown > .flx-dd-edit {
            display: none;
            max-width: 2em;  /* reset silly lineedit sizing */
            min-width: calc(100% - 1.5em - 2px);
            min-height: 1em;
            margin: 0;
            padding: 0;
            border: none;
        }
        
        .flx-BaseDropdown > .flx-dd-label {
            display: inline-block;
            min-width: calc(100% - 1.5em - 2px);
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
            display: inline-block;
            position: static;
            min-width: 1.5em;
            max-width: 1.5em;
            text-align: center;
            margin: 0;
        }
        .flx-BaseDropdown > .flx-dd-button:hover {
            background: rgba(128, 128, 128, 0.1);
        }
        .flx-BaseDropdown > .flx-dd-button::after {
            content: '\\25BE';  /* 2228 1F847 1F83F */
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
            <span></span>
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
            
            f2 = lambda e: self._submit_text() if e.which == 13 else None
            self._edit.addEventListener('keydown', f2, False)
            self._edit.addEventListener('blur', self._submit_text, False)
            
            self._label.addEventListener('click', self._but_click, 0)
            self._button.addEventListener('click', self._but_click, 0)
        
        @event.connect('text')
        def __on_text(self, *events):
            self._label.innerHTML = self.text + '&nbsp;'  # strut it
            self._edit.value = self.text
        
        def _but_click(self):
            if self.node.classList.contains('expanded'):
                self._collapse()
            else:
                self._expand()
        
        def _submit_text(self):
            self.text = self._edit.value
        
        def _expand(self):
            # Expand
            self.node.classList.add('expanded')
            # Collapse when the node changes position (e.g. scroll or layout change)
            rect = self.node.getBoundingClientRect()
            self._rect_to_check = rect
            window.setTimeout(self._check_expanded_pos, 100)
            # Collapse when the mouse is used outside the combobox (or its children)
            window.document.addEventListener('mouseup', self._collapse_maybe, 0)
            # Return rect so subclasses can use it
            return rect
        
        def _collapse_maybe(self, e):
            # Collapse if the given mouse event is outside the combobox.
            # Better version of blur event, sort of,
            t = e.target
            while t is not window.document.body:
                if t is self.node:
                    return
                t = t.parentElement
            window.document.removeEventListener('mouseup', self._collapse_maybe)
            self._collapse()
        
        def _collapse(self):
            self.node.classList.remove('expanded')
        
        def _check_expanded_pos(self):
            if self.node.classList.contains('expanded'):
                rect = self.node.getBoundingClientRect()
                if not (rect.top == self._rect_to_check.top and
                        rect.left == self._rect_to_check.left):
                    self._collapse()
                else:
                    window.setTimeout(self._check_expanded_pos, 100)


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
            box-sizing: border-box;
            border: 1px solid black;
            margin: 0;
            padding: 2px;
            position: fixed;  /* because all our widgets are overflow:hidden */
            background: white;
            z-index: 9999;
            display: none;
        }
        .flx-ComboBox.expanded > ul {
            display: initial;
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
            Can also be programatically set.
            """
            if v is None:
                return None
            return max(0, int(v))
        
        @event.prop
        def selected_key(self, v=None):
            """ The currently selected item key. Can be None if no item has
            been selected or when the text was changed manually (if editable).
            Can also be programatically set.
            """
            if v is None:
                return None
            return str(v)
        
        @event.prop
        def placeholder_text(self, v=''):
            """ The placeholder text to display in editable mode.
            """
            return str(v)
        
        @event.prop
        def options(self, options=[]):
            """ A list of tuples (key, text) representing the options.
            For items that are given as a string, the key and text are the same.
            If a dict is given, it is transformed to key-text pairs.
            """
            # If dict ...
            if isinstance(options, dict):
                keys = options.keys()
                if this_is_js():
                    keys = sorted(keys)  # Sort dict by key
                elif isinstance(options, OrderedDict):
                    # PyScript should not see use of OrderedDict, therefore this
                    # is in the else clause of "if this_is_js():"
                    keys = sorted(keys)
                options = [(k, options[k]) for k in keys]
            # Parse
            options2 = []
            for opt in options:
                if isinstance(opt, (tuple, list)):
                    opt = str(opt[0]), str(opt[1])
                else:
                    opt = str(opt), str(opt)
                options2.append(opt)
            return tuple(options2)
        
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
                key, text = self.options[index]
                self.selected_index = index
                self.selected_key = key
                self.text = text
            self._collapse()
        
        def _expand(self):
            rect = super()._expand()
            self._ul.style.left = rect.left + 'px'
            self._ul.style.top = (rect.bottom - 1) + 'px'
            self._ul.style.width = rect.width + 'px'
        
        def _submit_text(self):
            self.text = self._edit.value
            # todo: select option if text happens to match it?
            self.selected_index = None
            self.selected_key = None
        
        @event.connect('selected_index')
        def __on_selected_index(self, *events):
            if self.selected_index is not None:
                if self.selected_index < len(self.options):
                    key, text = self.options[self.selected_index]
                    self.text = text
                    self.selected_key = key
        
        @event.connect('selected_key')
        def __on_selected_key(self, *events):
            if self.selected_key is not None:
                key = self.selected_key
                if self.options[self.selected_index]:
                    if self.options[self.selected_index][0] == key:
                        return
                for index, option in enumerate(self.options):
                    if option[0] == key:
                        self.selected_index = index
        
        @event.connect('options')
        def __on_options(self, *events):
            while self._ul.firstChild:
                self._ul.removeChild(self._ul.firstChild)
            strud = ''
            for i, option in enumerate(self.options):
                key, text = option
                li = window.document.createElement('li')
                li.innerHTML = text if len(text.strip()) else '&nbsp;'
                li.index = i
                self._ul.appendChild(li)
                strud += text + '&nbsp;&nbsp;<span class="flx-dd-space"></span><br />'
            # Be smart about maintaining item selection
            keys = [key_text[0] for key_text in self.options]
            if self.selected_key in keys:
                self.selected_index = None
                key = self.selected_key
                self.selected_key = None
                self.selected_key = key
            elif self.selected_index < len(self.options):
                self.selected_key = None
                index = self.selected_index
                self.selected_index = None
                self.selected_index = index
            else:
                self.selected_index = None
                self.selected_key = None
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
            position: fixed;
            min-height: 100px;
            max-height: 300px;
            width: 200px;
            background: white;
            z-index: 10001;
            display: none;
        }
        .flx-DropdownContainer.expanded > .flx-Widget {
            display: initial;
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
        
        def _expand(self):
            rect = super()._expand()
            node = self.children[0].node
            node.style.left = rect.left + 'px'
            node.style.top = (rect.bottom - 1) + 'px'
            # node.style.width = (rect.width - 6) + 'px'
