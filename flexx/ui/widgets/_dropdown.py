""" Dropdown widgets

.. UIExample:: 120

    from flexx import app, event, ui

    class Example(ui.Widget):

        def init(self):
            self.combo = ui.ComboBox(editable=True,
                                     options=('foo', 'bar', 'spaaaaaaaaam', 'eggs'))
            self.label = ui.Label()

        @event.reaction
        def update_label(self):
            text = 'Combobox text: ' + self.combo.text
            if self.combo.selected_index is not None:
                text += ' (index %i)' % self.combo.selected_index
            self.label.set_text(text)

Also see examples: :ref:`control_with_keys.py`.

"""

from pscript import window

from ... import event, app
from .._widget import Widget, create_element


# todo: some form of autocompletetion?


class BaseDropdown(Widget):
    """ Base class for drop-down-like widgets.
    """

    DEFAULT_MIN_SIZE = 50, 28

    CSS = """

        .flx-BaseDropdown {
            display: inline-block;
            overflow: visible;
            margin: 2px;
            border-radius: 3px;
            padding: 2px;
            border: 1px solid #aaa;
            max-height: 28px; /* overridden by maxsize */
            white-space: nowrap; /* keep label and but on-line */
            background: #e8e8e8
        }

        .flx-BaseDropdown:focus {
            outline: none;
            box-shadow: 0px 0px 3px 1px rgba(0, 100, 200, 0.7);
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

        .flx-BaseDropdown.editable-true {
            background: #fff;
        }
        .flx-BaseDropdown.editable-true > .flx-dd-label {
            display: none;
        }
        .flx-BaseDropdown.editable-true > .flx-dd-edit {
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
        if self.tabindex == -2:
            self.set_tabindex(-1)

    @event.action
    def expand(self):
        """ Expand the dropdown and give it focus, so that it can be used
        with the up/down keys.
        """
        self._expand()
        self.node.focus()

    def _create_dom(self):
        return window.document.createElement('span')

    def _render_dom(self):
        # Render more or less this:
        # <span class='flx-dd-label'></span>
        # <input type='text' class='flx-dd-edit'></input>
        # <span></span>
        # <span class='flx-dd-button'></span>
        # <div class='flx-dd-strud'>&nbsp;</div>
        f2 = lambda e: self._submit_text() if e.which == 13 else None
        return [create_element('span',
                               {'className': 'flx-dd-label',
                                'onclick': self._but_click},
                               self.text + '\u00A0'),
                create_element('input',
                               {'className': 'flx-dd-edit',
                                'onkeypress': f2,
                                'onblur': self._submit_text,
                                'value': self.text}),
                create_element('span'),
                create_element('span', {'className': 'flx-dd-button',
                                        'onclick': self._but_click}),
                create_element('div', {'className': 'flx-dd-strud'}, '\u00A0'),
                ]

    def _but_click(self):
        if self.node.classList.contains('expanded'):
            self._collapse()
        else:
            self._expand()

    def _submit_text(self):
        edit_node = self.outernode.childNodes[1]  # not pretty but we need to get value
        self.set_text(edit_node.value)

    def _expand(self):
        # Expand
        self.node.classList.add('expanded')
        # Collapse when the node changes position (e.g. scroll or layout change)
        rect = self.node.getBoundingClientRect()
        self._rect_to_check = rect
        window.setTimeout(self._check_expanded_pos, 100)
        # Collapse when the mouse is used outside the combobox (or its children)
        self._addEventListener(window.document, 'mousedown', self._collapse_maybe, 1)
        # Return rect so subclasses can use it
        return rect

    def _collapse_maybe(self, e):
        # Collapse if the given pointer event is outside the combobox.
        # Better version of blur event, sort of. Dont use mouseup, as then
        # there's mouse capturing (the event will come from the main widget).
        t = e.target
        while t is not window.document.body:
            if t is self.outernode:
                return
            t = t.parentElement
        window.document.removeEventListener('mousedown', self._collapse_maybe, 1)
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

    It is generally good practive to react to ``user_selected`` to detect user
    interaction, and react to ``text``, ``selected_key`` or ``selected_index``
    to keep track of all kinds of (incl. programatic) interaction .

    When the combobox is expanded, the arrow keys can be used to select
    an item, and it can be made current by pressing Enter or spacebar.
    Escape can be used to collapse the combobox.
    
    The ``node`` of this widget is a
    `<span> <https://developer.mozilla.org/docs/Web/HTML/Element/span>`_
    with some child elements and quite a bit of CSS for rendering.
    """

    CSS = """

        .flx-ComboBox {
        }

        .flx-ComboBox > ul  {
            list-style-type: none;
            box-sizing: border-box;
            border: 1px solid #333;
            border-radius: 3px;
            margin: 0;
            padding: 2px;
            position: fixed;  /* because all our widgets are overflow:hidden */
            background: white;
            z-index: 9999;
            display: none;
        }
        .flx-ComboBox.expanded > ul {
            display: block;
            max-height: 220px;
            overflow-y: auto;
        }

        .flx-ComboBox.expanded > ul > li:hover {
            background: rgba(0, 128, 255, 0.2);
        }
        .flx-ComboBox.expanded > ul > li.highlighted-true {
            box-shadow: inset 0 0 3px 1px rgba(0, 0, 255, 0.4);
        }
    """

    # Note: we don't define text on the base class, because it would be
    # the only common prop, plus we want a different docstring.

    text = event.StringProp('', settable=True, doc="""
        The text displayed on the widget. This property is set
        when an item is selected from the dropdown menu. When editable,
        the ``text`` is also set when the text is edited by the user.
        This property is settable programatically regardless of the
        value of ``editable``.
        """)

    selected_index = event.IntProp(-1, settable=True, doc="""
        The currently selected item index. Can be -1 if no item has
        been selected or when the text was changed manually (if editable).
        Can also be programatically set.
        """)

    selected_key = event.StringProp('', settable=True, doc="""
        The currently selected item key. Can be '' if no item has
        been selected or when the text was changed manually (if editable).
        Can also be programatically set.
        """)

    placeholder_text = event.StringProp('', settable=True, doc="""
        The placeholder text to display in editable mode.
        """)

    editable = event.BoolProp(False, settable=True, doc="""
        Whether the combobox's text is editable.
        """)

    options = event.TupleProp((), settable=True, doc="""
        A list of tuples (key, text) representing the options. Both
        keys and texts are converted to strings if they are not already.
        For items that are given as a string, the key and text are the same.
        If a dict is given, it is transformed to key-text pairs.
        """)

    _highlighted = app.LocalProperty(-1, settable=True, doc="""
        The index of the currently highlighted item.
        """)

    @event.action
    def set_options(self, options):
        # If dict ...
        if isinstance(options, dict):
            keys = options.keys()
            keys = sorted(keys)  # Sort dict by key
            options = [(k, options[k]) for k in keys]
        # Parse
        options2 = []
        for opt in options:
            if isinstance(opt, (tuple, list)):
                opt = str(opt[0]), str(opt[1])
            else:
                opt = str(opt), str(opt)
            options2.append(opt)
        self._mutate_options(tuple(options2))

        # Be smart about maintaining item selection
        keys = [key_text[0] for key_text in self.options]
        if self.selected_key and self.selected_key in keys:
            key = self.selected_key
            self.set_selected_key('')
            self.set_selected_key(key)  # also changes text
        elif 0 <= self.selected_index < len(self.options):
            index = self.selected_index
            self.set_selected_index(-1)
            self.set_selected_index(index)  # also changes text
        elif self.selected_key:
            self.selected_key('')  # also changes text
        else:
            pass  # no selection, leave text alone
    
    @event.action
    def set_selected_index(self, index):
        if index == self.selected_index:
            return
        elif 0 <= index < len(self.options):
            key, text = self.options[index]
            self._mutate('selected_index', index)
            self._mutate('selected_key', key)
            self.set_text(text)
        else:
            self._mutate('selected_index', -1)
            self._mutate('selected_key', '')
            self.set_text('')
    
    @event.action
    def set_selected_key(self, key):
        if key == self.selected_key:
            return
        elif key:
            if key == self.selected_key:
                return  # eraly exit
            for index, option in enumerate(self.options):
                if option[0] == key:
                    self._mutate('selected_index', index)
                    self._mutate('selected_key', key)
                    self.set_text(option[1])
                    return
        # else
        self._mutate('selected_index', -1)
        self._mutate('selected_key', '')
        self.set_text('')
    
    @event.emitter
    def user_selected(self, index):
        """ Event emitted when the user selects an item using the mouse or
        keyboard. The event has attributes ``index``, ``key`` and ``text``.
        """
        options = self.options
        if index >= 0 and index < len(options):
            key, text = options[index]
            self.set_selected_index(index)
            self.set_selected_key(key)
            self.set_text(text)
            return dict(index=index, key=key, text=text)

    def _create_dom(self):
        node = super()._create_dom()
        node.onkeydown=self._key_down
        return node

    def _render_dom(self):
        # Create a virtual node for each option
        options = self.options
        option_nodes = []
        strud = []
        for i in range(len(options)):
            key, text = options[i]
            clsname = 'highlighted-true' if self._highlighted == i else ''
            li = create_element('li',
                                dict(index=i, className=clsname),
                                text if len(text.strip()) else '\u00A0')
            strud += [text + '\u00A0',
                      create_element('span', {'class': "flx-dd-space"}),
                      create_element('br')]
            option_nodes.append(li)

        # Update the list of nodes created by superclass
        nodes = super()._render_dom()
        nodes[1].props.placeholder = self.placeholder_text  # the line edit
        nodes[-1].children = strud  # set strud
        nodes.append(create_element('ul',
                                    dict(onmousedown=self._ul_click),
                                    option_nodes))
        return nodes

    @event.reaction
    def __track_editable(self):
        if self.editable:
            self.node.classList.remove('editable-false')
            self.node.classList.add('editable-true')
        else:
            self.node.classList.add('editable-false')
            self.node.classList.remove('editable-true')

    def _ul_click(self, e):
        if hasattr(e.target, 'index'):  # not when scrollbar is clicked
            self._select_from_ul(e.target.index)

    def _select_from_ul(self, index):
        self.user_selected(index)
        self._collapse()

    def _key_down(self, e):
        # Get key
        key = e.key
        if not key and e.code:
            key = e.code

        # If collapsed, we may want to expand. Otherwise, do nothing.
        # In this case, only consume events that dont sit in the way with
        # the line edit of an editable combobox.
        if not self.node.classList.contains('expanded'):
            if key in ['ArrowUp', 'ArrowDown']:
                e.stopPropagation()
                self.expand()
            return

        # Early exit, be specific about the keys that we want to accept
        if key not in ['Escape', 'ArrowUp', 'ArrowDown', ' ', 'Enter']:
            return

        # Consume the keys
        e.preventDefault()
        e.stopPropagation()

        if key == 'Escape':
            self._set_highlighted(-1)
            self._collapse()

        elif key == 'ArrowUp' or key == 'ArrowDown':
            if key == 'ArrowDown':
                hl = self._highlighted + 1
            else:
                hl = self._highlighted - 1
            self._set_highlighted(min(max(hl, 0), len(self.options)-1))

        elif key == 'Enter' or key == ' ':
            if self._highlighted >= 0 and self._highlighted < len(self.options):
                self._select_from_ul(self._highlighted)

    def _expand(self):
        rect = super()._expand()
        ul = self.outernode.children[len(self.outernode.children) - 1]
        ul.style.left = rect.left + 'px'
        ul.style.width = rect.width + 'px'
        ul.style.top = (rect.bottom - 1) + 'px'
        # Correct position (above, below) as needed
        space_below = window.innerHeight - rect.bottom
        if space_below < ul.clientHeight:
            space_above = rect.top
            if space_above > space_below:
                ul.style.top = (rect.top - 1 - ul.clientHeight) + 'px'

    def _submit_text(self):
        super()._submit_text()
        # todo: should this select option if text happens to match it?
        self.set_selected_index(-1)
        self.set_selected_key('')


class DropdownContainer(BaseDropdown):
    """
    A dropdown widget that shows its children when expanded. This can be
    used to e.g. make a collapsable tree widget. Some styling may be required
    for the child widget to be sized appropriately.

    *Note: This widget is currently broken, because pointer events do not work in the
    contained widget (at least on Firefox).*
    """

    CSS = """
        .flx-DropdownContainer {
            min-width: 50px;
        }
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

    text = event.StringProp('', settable=True, doc="""
        The text displayed on the dropdown widget.
        """)

    def _render_dom(self):
        nodes = super()._render_dom()
        for widget in self.children:
            nodes.append(widget.outernode)
        return nodes

    def _expand(self):
        rect = super()._expand()
        node = self.children[0].outernode
        node.style.left = rect.left + 'px'
        node.style.top = (rect.bottom - 1) + 'px'
        # node.style.width = (rect.width - 6) + 'px'
