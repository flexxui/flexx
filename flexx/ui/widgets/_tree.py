""" TreeWidget

A ``TreeWidget`` can contain ``TreeItems``, which in turn can contain
``TreeItems`` to construct a tree.

.. UIExample:: 120

    from flexx import app, ui

    class Example(ui.Widget):

        def init(self):

            with ui.TreeWidget(max_selected=2):

                for t in ['foo', 'bar', 'spam', 'eggs']:
                    ui.TreeItem(text=t, checked=True)

Also see examples: :ref:`tree.py`, :ref:`control_with_keys.py`.

"""

from ... import event
from .._widget import Widget, create_element

loop = event.loop


# todo: icons
# todo: tooltips
# todo: a variant that can load data dynamically from Python, for biggish data


class TreeWidget(Widget):
    """
    A Widget that can be used to structure information in a list or a tree.
    It's items are represented by its children, which may only be TreeItem
    objects. Sub items can be created by instantiating TreeItems in the context
    of another TreeItem.

    When the items in the tree have no sub-items themselves, the TreeWidget is
    in "list mode". Otherwise, items can be collapsed/expanded etc.
    
    The ``node`` of this widget is a
    `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_
    with some child elements and quite a bit of CSS for rendering.
    
    **Style**

    This widget can be fully styled using CSS, using the following CSS classes:

    * ``flx-listmode`` is set on the widget's node if no items have sub items.

    Style classes for a TreeItem's elements:

    * ``flx-TreeItem`` indicates the row of an item (its text, icon, and checkbox).
    * ``flx-TreeItem > collapsebut`` the element used to collapse/expand an item.
    * ``flx-TreeItem > checkbut`` the element used to check/uncheck an item.
    * ``flx-TreeItem > text`` the element that contains the text of the item.
    * ``flx-TreeItem > title`` the element that contains the title of the item.

    Style classes applied to the TreeItem, corresponding to its properties:

    * ``visible-true`` and ``visible-false`` indicate visibility.
    * ``selected-true`` and ``selected-false`` indicate selection state.
    * ``checked-true``, ``checked-false`` and ``checked-null`` indicate checked
      state, with the ``null`` variant indicating not-checkable.
    * ``collapsed-true``, ``collapsed-false`` and ``collapsed-null`` indicate
      collapse state, with the ``null`` variant indicating not-collapsable.
    
    """

    DEFAULT_MIN_SIZE = 100, 50

    CSS = """

    /* ----- Tree Widget Mechanics ----- */

    .flx-TreeWidget {
        height: 100%;
        overflow-y: scroll;
        overflow-x: hidden;
        cursor: default;
    }

    .flx-TreeWidget > ul {
        position: absolute; /* avoid having an implicit width */
        left: 0;
        right: 0;
    }

    .flx-TreeWidget .flx-TreeItem {
        display: inline-block;
        margin: 0;
        padding-left: 2px;
        width: 100%;
        user-select: none;
        -moz-user-select: none;
        -webkit-user-select: none;
        -ms-user-select: none;
    }

    .flx-TreeWidget .flx-TreeItem > .text {
        display: inline-block;
        position: absolute;
        right: 0;
    }
    .flx-TreeWidget .flx-TreeItem > .title:empty + .text {
        position: static;  /* .text width is not used*/
    }

    .flx-TreeWidget ul {
        list-style-type: none;
        padding: 0;
        margin: 0;
    }
    
    .flx-TreeWidget li {
        outline-offset: -1px;
    }
    .flx-TreeWidget li.visible-false {
        display: none;
    }
    .flx-TreeWidget li.collapsed-true ul {
        display: none;
    }

    /* collapse button */
    .flx-TreeWidget .flx-TreeItem > .collapsebut {
        display: inline-block;
        width: 1.5em;  /* must match with ul padding-left */
        text-align: center;
        margin-left: -1px;  /* aligns better with indentation guide */
    }
    .flx-TreeWidget .flx-TreeItem.collapsed-null > .collapsebut {
        visibility: hidden;
    }
    .flx-TreeWidget.flx-listmode .flx-TreeItem > .collapsebut {
        display: none;
    }

    /* indentation guides */
    .flx-TreeWidget ul {
        padding-left: 0.75em;
    }
    .flx-TreeWidget > ul {
        padding-left: 0em;
    }
    .flx-TreeWidget.flx-listmode ul {
        padding-left: 0.25em;
    }

    /* ----- Tree Widget Style ----- */

    .flx-TreeWidget {
        border: 2px groove black;
        padding: 3px;
    }

    .flx-TreeItem.selected-true {
        background: rgba(128, 128, 128, 0.35);
    }
    .flx-TreeItem.highlighted-true {
        box-shadow: inset 0 0 3px 1px rgba(0, 0, 255, 0.4);
    }

    .flx-TreeWidget .flx-TreeItem.collapsed-true > .collapsebut::after {
        vertical-align: top;
        content: '\\25B8';  /* small right triangle */
    }
    .flx-TreeWidget .flx-TreeItem.collapsed-false > .collapsebut::after {
        vertical-align: top;
        content: '\\25BE';  /* small down triangle */
    }

    .flx-TreeWidget .flx-TreeItem > .collapsebut {
        color: rgba(128, 128, 128, 0.6);
    }
    .flx-TreeWidget li.collapsed-false > ul > li {
        border-left: 1px solid rgba(128, 128, 128, 0.3);
    }
    .flx-TreeWidget li.collapsed-false.selected-true > ul > li {
        border-left: 1px solid rgba(128, 128, 128, 0.6);
    }

    .flx-TreeItem.checked-null > .checkbut {
        content: '\\2611\\00a0';
       /* display: none;  /* could also be visibility: hidden */
    }
    .flx-TreeItem.checked-true > .checkbut::after {
        vertical-align: top;
        content: '\\2611\\00a0';
    }
    .flx-TreeItem.checked-false > .checkbut::after {
        vertical-align: top;
        content: '\\2610\\00a0';
    }

    .flx-TreeWidget .flx-TreeItem > .text.hastitle {
        width: 50%;
    }
    /* ----- End Tree Widget ----- */

    """

    max_selected = event.IntProp(0, settable=True, doc="""
        The maximum number of selected items:

        * If 0 (default) there is no selection.
        * If 1, there can be one selected item.
        * If > 1, up to this number of items can be selected by clicking them.
        * If -1, any number of items can be selected by holding Ctrl or Shift.
        """)

    def init(self):
        self._highlight_on = False
        self._last_highlighted_hint = ''
        self._last_selected = None

    def get_all_items(self):
        """ Get a flat list of all TreeItem instances in this Tree
        (including sub children and sub-sub children, etc.), in the order that
        they are shown in the tree.
        """
        items = []
        def collect(x):
            items.append(x)
            for i in x.children:
                if i:
                    collect(i)

        for x in self.children:
            collect(x)
        return items

    def _render_dom(self):
        nodes = [i.outernode for i in self.children if isinstance(i, TreeItem)]
        return [create_element('ul', {}, nodes)]

    @event.reaction('children', 'children*.children')
    def __check_listmode(self, *events):
        listmode = True
        for i in self.children:
            listmode = listmode and len(i.children) == 0 and i.collapsed is None
        if listmode:
            self.node.classList.add('flx-listmode')
        else:
            self.node.classList.remove('flx-listmode')

    @event.reaction('max_selected')
    def __max_selected_changed(self, *events):
        if self.max_selected == 0:
            # Deselect all
            for i in self.get_all_items():
                i.set_selected(False)
        elif self.max_selected < 0:
            # No action needed
            pass
        else:
            # Deselect all if the count exceeds the max
            count = 0
            for i in self.get_all_items():
                count += int(i.selected)
            if count > self.max_selected:
                for i in self.children:
                    i.set_selected(False)

    @event.reaction('!children**.pointer_click', '!children**.pointer_double_click')
    def _handle_item_clicked(self, *events):
        self._last_highlighted_hint = events[-1].source.id
        if self._highlight_on:  # highhlight tracks clicks
            self.highlight_show_item(events[-1].source)

        if self.max_selected == 0:
            # No selection allowed
            pass

        elif self.max_selected < 0:
            # Select/deselect any, but only with CTRL and SHIFT
            for ev in events:
                item = ev.source
                modifiers = ev.modifiers if ev.modifiers else []
                if 'Shift' in modifiers:  # Ctrl can also be in modifiers
                    # Select everything between last selected and current
                    if self._last_selected is not None:
                        if self._last_selected is not item:
                            mark_selected = False
                            for i in self.get_all_items():
                                if mark_selected == True:  # noqa - PScript perf
                                    if i is item or i is self._last_selected:
                                        break
                                    i.user_selected(True)
                                else:
                                    if i is item or i is self._last_selected:
                                        mark_selected = True
                    item.user_selected(True)
                    self._last_selected = item
                elif 'Ctrl' in modifiers:
                    # Toggle
                    select = not item.selected
                    item.user_selected(select)
                    self._last_selected = item if select else None
                else:
                    # Similar as when max_selected is 1
                    for i in self.get_all_items():
                        if i.selected and i is not item:
                            i.user_selected(False)
                    select = not item.selected
                    item.user_selected(select)
                    self._last_selected = item if select else None

        elif self.max_selected == 1:
            # Selecting one, deselects others
            item = events[-1].source
            gets_selected = not item.selected
            if gets_selected:
                for i in self.get_all_items():
                    if i.selected and i is not item:
                        i.user_selected(False)
            item.user_selected(gets_selected)  # set the item last

        else:
            # Select to a certain max
            item = events[-1].source
            if item.selected:
                item.user_selected(False)
            else:
                count = 0
                for i in self.get_all_items():
                    count += int(i.selected)
                if count < self.max_selected:
                    item.user_selected(True)

    # NOTE: this highlight API is currently not documented, as it lives
    # in JS only. The big refactoring will change all that.

    def highlight_hide(self):
        """ Stop highlighting the "current" item.
        """
        all_items = self._get_all_items_annotated()
        self._de_highlight_and_get_highlighted_index(all_items)
        self._highlight_on = False

    def highlight_show_item(self, item):
        """ Highlight the given item.
        """
        classname = 'highlighted-true'
        all_items = self._get_all_items_annotated()
        self._highlight_on = True
        self._de_highlight_and_get_highlighted_index(all_items)
        item._row.classList.add(classname)
        self._last_highlighted_hint = item.id

    def highlight_show(self, step=0):
        """ Highlight the "current" item, optionally moving step items.
        """
        classname = 'highlighted-true'
        all_items = self._get_all_items_annotated()
        self._highlight_on = True

        index1 = self._de_highlight_and_get_highlighted_index(all_items)
        index2 = 0 if index1 is None else index1 + step
        while 0 <= index2 < len(all_items):
            visible, _ = all_items[index2]
            if visible:
                break
            index2 += step
        else:
            index2 = index1
        if index2 is not None:
            _, item = all_items[index2]
            item._row.classList.add(classname)
            self._last_highlighted_hint = item.id
            # Scroll into view when needed
            y1 = item._row.offsetTop - 20
            y2 = item._row.offsetTop + item._row.offsetHeight + 20
            if self.node.scrollTop > y1:
                self.node.scrollTop = y1
            if self.node.scrollTop + self.node.offsetHeight < y2:
                self.node.scrollTop = y2 - self.node.offsetHeight

    def highlight_get(self):
        """ Get the "current" item. This is the currently highlighted
        item if there is one. Otherwise it can be the last highlighted item
        or the last clicked item.
        """
        classname = 'highlighted-true'
        all_items = self._get_all_items_annotated()

        index = self._de_highlight_and_get_highlighted_index(all_items)
        if index is not None:
            _, item = all_items[index]
            item._row.classList.add(classname)
            return item

    def highlight_toggle_selected(self):
        """ Convenience method to toggle the "selected" property of the
        current item.
        """
        item = self.highlight_get()
        if item is not None:
            self._handle_item_clicked(dict(source=item))  # simulate click

    def highlight_toggle_checked(self):
        """ Convenience method to toggle the "checked" property of the
        current item.
        """
        item = self.highlight_get()
        if item is not None:
            if item.checked is not None:  # is it checkable?
                item.user_checked(not item.checked)

    def _de_highlight_and_get_highlighted_index(self, all_items):
        """ Unhighlight all items and get the index of the item that was
        highlighted, or which otherwise represents the "current" item, e.g.
        because it was just clicked.
        """
        classname = 'highlighted-true'
        index = None
        hint = None
        for i in range(len(all_items)):
            visible, item = all_items[i]
            if item._row.classList.contains(classname):
                item._row.classList.remove(classname)
                if index is None:
                    index = i
            if hint is None and item.id == self._last_highlighted_hint:
                hint = i
        if index is not None:
            return index
        else:
            return hint

    def _get_all_items_annotated(self):
        """ Get a flat list of all TreeItem instances in this Tree,
        including visibility information due to collapsed parents.
        """
        items = []
        def collect(x, parent_collapsed):
            visible = x.visible and not parent_collapsed
            items.append((visible, x))
            for i in x.children:
                if i:
                    collect(i, parent_collapsed or x.collapsed)

        for x in self.children:
            collect(x, False)
        return items


class TreeItem(Widget):
    """ An item to put in a TreeWidget. This widget should only be used inside
    a TreeWidget or another TreeItem.

    Items are collapsable/expandable if their ``collapsed`` property
    is set to ``True`` or ``False`` (i.e. not ``None``), or if they
    have sub items. Items are checkable if their ``checked`` property
    is set to ``True`` or ``False`` (i.e. not ``None``). Items are
    selectable depending on the selection policy defined by
    ``TreeWidget.max_selected``.

    If needed, the ``_render_title()`` and ``_render_text()`` methods can
    be overloaded to display items in richer ways. See the documentation
    of ``Widget._render_dom()`` for details.
    
    The ``outernode`` of this widget is a
    `<li> <https://developer.mozilla.org/docs/Web/HTML/Element/li>`_
    (a list-item in the tree or parent item's ``<ul>``.
    The ``node`` of this widget is a
    `<span> <https://developer.mozilla.org/docs/Web/HTML/Element/span>`_
    that represents the row for this item (but not its children).
    """

    text = event.StringProp('', settable=True, doc="""
        The text for this item. Can be used in combination with
        ``title`` to obtain two columns.
        """)

    title = event.StringProp('', settable=True, doc="""
        The title for this item that appears before the text. Intended
        for display of key-value pairs. If a title is given, the text is
        positioned in a second (virtual) column of the tree widget.
        """)

    visible = event.BoolProp(True, settable=True, doc="""
        Whether this item (and its sub items) is visible.
        """)

    selected = event.BoolProp(False, settable=True, doc="""
        Whether this item is selected. Depending on the TreeWidget's
        policy (max_selected), this can be set/unset on clicking the item.
        """)

    checked = event.TriStateProp(settable=True, doc="""
        Whether this item is checked (i.e. has its checkbox set).
        The value can be None, True or False. None (the default)
        means that the item is not checkable.
        """)

    collapsed = event.TriStateProp(settable=True, doc="""
        Whether this item is expanded (i.e. shows its children).
        The value can be None, True or False. None (the default)
        means that the item is not collapsable (unless it has sub items).
        """)

    @event.emitter
    def user_selected(self, selected):
        """ Event emitted when the user (un)selects this item. Has ``old_value``
        and ``new_value`` attributes. One can call this emitter directly to
        emulate a user-selection, but note that this bypasses the max_selected
        policy.
        """
        d = {'old_value': self.selected, 'new_value': selected}
        self.set_selected(selected)
        return d

    @event.emitter
    def user_checked(self, checked):
        """ Event emitted when the user (un)checks this item. Has ``old_value``
        and ``new_value`` attributes.
        """
        d = {'old_value': self.checked, 'new_value': checked}
        self.set_checked(checked)
        return d

    @event.emitter
    def user_collapsed(self, collapsed):
        """ Event emitted when the user (un)collapses this item. Has ``old_value``
        and ``new_value`` attributes.
        """
        d = {'old_value': self.collapsed, 'new_value': collapsed}
        self.set_collapsed(collapsed)
        return d

    @event.action
    def set_parent(self, parent, pos=None):
        # Verify that this class is used correctly
        # Note that this action is already called from the init by Widget.
        if not (parent is None or
                isinstance(parent, TreeItem) or
                isinstance(parent, TreeWidget)):
            raise RuntimeError('TreeItems can only be created in the context '
                               'of a TreeWidget or TreeItem.')
        super().set_parent(parent, pos)

    def _create_dom(self):
        global window
        node = window.document.createElement('li')
        self._row = window.document.createElement('span')  # we need this node
        node.appendChild(self._row)
        self._addEventListener(node, 'click', self._on_click)
        self._addEventListener(node, 'dblclick', self._on_double_click)
        return node, self._row

    def _render_dom(self):
        # We render more or less this:
        # <li>
        #     <span class='flx-TreeItem'>     # the row that represents the item
        #         <span class='padder'></span>    # padding
        #         <span class='collapsebut'></span>   # the collapse button
        #         <span class='checkbut'></span>  # the check button
        #         <span class='title'></span>     # the title text for this item
        #         <span class='text'></span>      # the text for this item
        #         </span>
        #     <ul></ul>                           # to hold sub items
        # </li>

        subnodes = [item.outernode for item in self.children]

        # Get class names to apply to the li and row. We apply the clases to
        # both to allow styling both depending on these values, but strictly
        # speaking visible and collapsed are only needed for the li and
        # selected and checked for the span.
        cnames = []
        collapsed = bool(self.collapsed) if len(self.children) > 0 else self.collapsed
        for name, val in [('visible', self.visible),
                          ('collapsed', collapsed),
                          ('selected', self.selected),
                          ('checked', self.checked),
                          ]:
            cnames.append(name + '-' + str(val))
        cnames = ' '.join(cnames)

        # Get title and text content
        title, text = self._render_title(), self._render_text()

        # Note that the outernode (the <li>) has not flx-Widget nor flx-TreeItem
        text_class = 'text hastitle' if len(title) > 0 else 'text'
        return create_element('li', {'className': cnames},
                    create_element('span', {'className': 'flx-TreeItem ' + cnames},
                        create_element('span', {'className': 'padder'}),
                        create_element('span', {'className': 'collapsebut'}),
                        create_element('span', {'className': 'checkbut'}),
                        create_element('span', {'className': 'title'}, title),
                        create_element('span', {'className': text_class}, text),
                        ),
                    create_element('ul', {}, subnodes),
                    )

    def _render_title(self):
        """ Return a node for title. Can be overloaded to e.g. format with html.
        """
        return self.title

    def _render_text(self):
        """ Return a node for text. Can be overloaded.
        """
        return self.text

    def _on_click(self, e):
        # Handle JS mouse click event
        e.stopPropagation()  # don't click parent items
        if e.target.classList.contains('collapsebut'):
            self.user_collapsed(not self.collapsed)
        elif e.target.classList.contains('checkbut'):
            self.user_checked(not self.checked)
        else:
            self.pointer_click(e)

    def _on_double_click(self, e):
        # Handle JS mouse double click event
        e.stopPropagation()  # don't click parent items
        c1 = e.target.classList.contains('collapsebut')
        c2 = e.target.classList.contains('checkbut')
        if not (c1 or c2):
            self.pointer_double_click(e)
