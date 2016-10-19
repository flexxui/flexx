
from flexx import app, event, ui

# todo: tooltip
# todo: icons


class TreeWidget(ui.Widget):
    """
    Widget that can be used to structure information in a list or a tree.
    To add items, create TreeItem objects in the context of a TreeWidget.
    Sub items can be created by instantiating TreeItems in the context
    of another TreeItem.
    
    When the items in the tree have no sub items, the TreeWidget is in
    "list mode". Otherwise, items can be collapsed/expanded etc.
    This widget can be fully styled using CSS, see below.
    
    *Style*
    
    Style classes applied to the TreeWidget:
    
    * ``listmode`` is set on the widget's node if no items have sub items.
    
    Style classes for a TreeItem's elements:
    * ``row`` indicates the row of an item (its text, icon, and checkbox).
    * ``collapsebut`` the element used to collapse/expand an item.
    * ``checkbut`` the element used to check/uncheck an item.
    * ``text`` the element that contains the text of the item.
    * ``title`` the element that contains the title of the item.
    
    Style classes applied to the TreeItem, corresponding to its properties:
    
    * ``visible-true`` and ``visible-false`` indicate visibility.
    * ``selected-true`` and ``selected-false`` indicate selection state.
    * ``checked-true``, ``checked-false`` and ``checked-null`` indicate checked
      state, with the ``null`` variant indicating not-checkable.
    * ``collapsed-true``, ``collapsed-false`` and ``collapsed-null`` indicate
      collapse state, with the ``null`` variant indicating not-collapsable.
    
    """
    
    CSS = """
    
    /* ----- Tree Widget Mechanics ----- */
    
    .flx-TreeWidget {
        overflow-y: scroll;
        overflow-x: hidden;
    }
    
    .flx-TreeWidget > ul {
        position: absolute; /* avoid having an implicit width */
        left: 0;
        right: 0;
    }
    
    .flx-TreeWidget .row {
        display: inline-block;
        margin: 0;
        padding-left: 2px;
        width: 100%;
        user-select: none;
        -moz-user-select: none;
        -webkit-user-select: none;
        -ms-user-select: none;
    }
    
    .flx-TreeWidget .text {
        display: inline-block;
        position: absolute;
        padding-top: 0.1em;  /* tweak */
        right: 0;
    }
    .flx-TreeWidget .title:empty + .text {
        position: initial;  /* .text width is not used*/
        padding-top: 0;
    }
    
    .flx-TreeWidget ul {
        list-style-type: none;
        padding: 0;
        margin: 0;
    }
    
    .flx-TreeWidget .visible-false {
        display: none;
    }
    .flx-TreeWidget .collapsed-true ul {
        display: none;
    }
    
    /* collapse button */
    .flx-TreeWidget .collapsebut {
        display: inline-block;
        width: 1.5em;  /* must match with ul padding-left */
        text-align: center;
        margin-left: 1px;  /* aligns better with indentation guide */
    }
    .flx-TreeWidget .collapsed-null > .collapsebut {
        visibility: 'hidden';
    }
    .flx-TreeWidget.listmode .collapsebut {
        display: none;
    }
    
    /* indentation guides */
    .flx-TreeWidget ul {
        padding-left: 0.75em;
    }
    .flx-TreeWidget > ul {
        padding-left: 0em; 
    }
    .flx-TreeWidget.listmode ul {
        padding-left: 0.25em;
    }
    
    /* ----- Tree Widget Style ----- */
    
    .flx-TreeWidget {
        border: 2px groove black;
        padding: 3px;
    }
    
    .flx-TreeWidget .selected-true > .row {
        background: rgba(128, 128, 128, 0.35);
    }
    
    .flx-TreeWidget .collapsed-true > .collapsebut::after {
        content: '\\23f5';
    }
    .flx-TreeWidget .collapsed-false > .collapsebut::after {
        content: '\\23f7';
    }
    
    .flx-TreeWidget .collapsebut {
        color: rgba(128, 128, 128, 0.6);
    }
    .flx-TreeWidget .collapsed-false > ul > li {
        border-left: 1px solid rgba(128, 128, 128, 0.3);
    }
    .flx-TreeWidget .collapsed-false.selected-true > ul > li {
        border-left: 1px solid rgba(128, 128, 128, 0.6);
    }
    
    .flx-TreeWidget .checked-null > .checkbut {
        content: '\\2611\\00a0';
       /* display: none;  /* could also be visibility: hidden */
    }
    .flx-TreeWidget .checked-true > .checkbut::after {
        content: '\\2611\\00a0';
    }
    .flx-TreeWidget .checked-false > .checkbut::after {
        content: '\\2610\\00a0';
    }
    
    .flx-TreeWidget .text {
        width: 50%;
    }
    
    /* ----- End Tree Widget ----- */
    
    """
    
    class Both:
        
        @event.prop
        def items(self, items=[]):
            """ The list of (direct) TreeItem instances for this tree.
            """
            #assert all([isinstance(i, TreeItem) for i in items])
            return tuple(items)
        
        @event.prop
        def max_selected(self, v=1):
            """ The maximum number of selected items. Can be -1 to allow
            any number of selected items. This determines the selection policy.
            """
            return int(v)
        
        def get_all_items(self):
            """ Get a flat list of all TreeItem instances in this Tree
            (including sub items and sub-sub items, etc.).
            """
            items = []
            def collect(x):
                items.extend(x.items)
                for i in x.items:
                    if i:
                        collect(i)
            collect(self)
            return items
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('div')
            self.node = self.phosphor.node
            self._ul = window.document.createElement('ul')
            self.node.appendChild(self._ul)
        
        @event.connect('items')
        def __update(self, *events):
            while self._ul.firstChild:
                self._ul.removeChild(self._ul.firstChild)
            for i in self.items:
                self._ul.appendChild(i.node)
        
        @event.connect('items', 'items*.items')
        def __check_listmode(self, *events):
            listmode = True
            for i in self.items:
                listmode = listmode and len(i.items) == 0
            if listmode:
                self.node.classList.add('listmode')
            else:
                self.node.classList.remove('listmode')
        
        @event.connect('max_selected')
        def __max_selected_changed(self, *events):
            if self.max_selected == 0:
                # Deselect all
                for i in self.get_all_items():
                    i.selected = False
            elif self.max_selected < 0:
                # No action needed
                pass
            else:
                # Deselect all if the count exceeds the max
                count = 0
                for i in self.get_all_items():
                    count += int(i.selected)
                if count > self.max_selected:
                    for i in self.items:
                        i.selected = False
        
        @event.connect('items**.!click')
        def __item_clicked(self, *events):
            if self.max_selected == 0:
                # No selection allowed
                pass
            elif self.max_selected < 0:
                # Select/deselect any
                for ev in events:
                    item = ev.source
                    item.selected = not item.selected
            elif self.max_selected == 1:
                # Selecting one, deselects others
                item = events[-1].source
                item.selected = not item.selected
                if item.selected:
                    for i in self.get_all_items():
                        if i.selected and i is not item:
                            i.selected = False
            else:
                # Select to a certain max
                item = events[-1].source
                if item.selected:
                    item.selected = False
                else:
                    count = 0
                    for i in self.get_all_items():
                        count += int(i.selected)
                    if count < self.max_selected:
                        item.selected = True

    
class TreeItem(app.Model):
    """ An item to put in a TreeWidget. TreeItem objects are Model
    objects, but do not inherit from `ui.Widget`.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        active_model = app.get_active_model()
        if isinstance(active_model, (TreeItem, TreeWidget)):
            active_model.items = active_model.items + (self, )
        else:
            raise RuntimeError('TreeItems can only be created in the context '
                               'of a TreeWidget or TreeItem.')
    
    class Both:
        
        @event.prop
        def items(self, items=[]):
            """ The list of sub items.
            """
            #assert all([isinstance(i, TreeItem) for i in items])
            return tuple(items)
        
        @event.prop
        def text(self, text=''):
            """ The text for this item.
            """
            return str(text)
        
        @event.prop
        def title(self, title=''):
            """ The title for this item that appears before the text. Intended
            for display of key-value pairs. If a title is given, the text is
            positioned in a second (virtual) column of the tree widget.
            """
            return str(title)
        
        @event.prop
        def visible(self, v=True):
            """ Whether this item is visible.
            """
            return bool(v)
        
        @event.prop
        def selected(self, v=False):
            """ Whether this item is selected. Depending on the TreeWidget's
            policy (max_selected), this can be set/unset on clicking the item.
            """
            return bool(v)
        
        @event.prop
        def checked(self, v=None):
            """ Whether this item is checked (i.e. has its checkbox set).
            The value can be None, True or False. None (the default).
            means that the item is not checkable.
            """
            if v is None:
                return None
            return bool(v)
        
        @event.prop
        def collapsed(self, v=None):
            """ Whether this item is expanded (i.e. shows its children).
            The value can be None, True or False. None (the default)
            means that the item is not collapsable (unless it has sub items).
            """
            if v is None:
                return None
            return bool(v)
    
    class JS:
        
        _HTML = ''.join([line.split('#')[0].strip() for line in """
            
            # This is the actual HTML used to generate an item
            <span class='row'>                  # the row that represents the item
                <span class='padder'></span>   # padding
                <span class='collapsebut'></span>   # the collapse button
                <span class='checkbut'></span>  # the check button
                <span class='title'></span>     # the title text for this item
                <span class='text'></span>      # the text for this item
                </span>
            <ul></ul>                           # to hold sub items
            
        """.splitlines()])
        
        def init(self):
            self.node = window.document.createElement('li')
            self.node.innerHTML = self._HTML
            
            self._row = self.node.childNodes[0]
            self._ul = self.node.childNodes[1]
            
            self._collapsebut = self._row.childNodes[1]
            self._checkbut = self._row.childNodes[2]
            self._title = self._row.childNodes[3]
            self._text = self._row.childNodes[4]
            
            #self._collapsebut.addEventListener('click', self._on_click)
            self._row.addEventListener('click', self._on_click)
        
        @event.emitter
        def click(self):
            """ Event emitted when the item is clicked on. Depending
            on the tree's max_selected, this can result in the item
            being selected/deselected.
            """
            return {}
        
        def _on_click(self, e):
            # Handle JS mouse click event
            if e.target is self._collapsebut:
                print('collapsing')
                self.collapsed = not self.collapsed
            elif e.target is self._checkbut:
                self.checked = not self.checked
            else:
                self.click()
        
        @event.connect('items')
        def __update(self, *events):
            while self._ul.firstChild:
                self._ul.removeChild(self._ul.firstChild)
            for i in self.items:
                self._ul.appendChild(i.node)
        
        @event.connect('text')
        def __text_changed(self, *events):
            self._text.innerHTML = self.text
        
        @event.connect('title')
        def __title_changed(self, *events):
            self._title.innerHTML = self.title
        
        @event.connect('visible')
        def __visible_changed(self, *events):
            for node in [self.node, self._row]:
                if self.visible:
                    node.classList.add('visible-true')
                    node.classList.remove('visible-false')
                else:
                    node.classList.remove('visible-true')
                    node.classList.add('visible-false')
        
        @event.connect('selected')
        def __selected_changed(self, *events):
            for node in [self.node, self._row]:
                if self.selected:
                    node.classList.add('selected-true')
                    node.classList.remove('selected-false')
                else:
                    node.classList.remove('selected-true')
                    node.classList.add('selected-false')
        
        @event.connect('checked')
        def __checked_changed(self, *events):
            for node in [self.node, self._row]:
                if self.checked is None:
                    node.classList.add('checked-null')
                    node.classList.remove('checked-true')
                    node.classList.remove('checked-false')
                elif self.checked:
                    node.classList.remove('checked-null')
                    node.classList.add('checked-true')
                    node.classList.remove('checked-false')
                else:
                    node.classList.remove('checked-null')
                    node.classList.remove('checked-true')
                    node.classList.add('checked-false')
        
        @event.connect('collapsed', 'items')
        def __collapsed_changed(self, *events):
            for node in [self.node, self._row]:
                if self.collapsed is None and not self.items:
                    node.classList.add('collapsed-null')
                    node.classList.remove('collapsed-true')
                    node.classList.remove('collapsed-false')
                elif self.collapsed:
                    node.classList.remove('collapsed-null')
                    node.classList.add('collapsed-true')
                    node.classList.remove('collapsed-false')
                else:
                    node.classList.remove('collapsed-null')
                    node.classList.remove('collapsed-true')
                    node.classList.add('collapsed-false')

            
##

class Example(ui.Widget):
    
    CSXCS = """
    .flx-TreeWidget {
        background: #000;
        color: #f00;
    }
    .flx-TreeWidget .title {
        width: 60%;
    }
    """
    def init(self):
        
        with ui.SplitPanel():
            with TreeWidget(flex=2, max_selected=-1) as self.tree1:
                for t in ['foo', 'bar', 'spam', 'eggs']:
                    TreeItem(text=t, checked=False)
            
            ui.Widget(flex=1)
            with TreeWidget(flex=2) as self.tree2:
                for t in ['foo', 'bar', 'spam', 'eggs']:
                    item = TreeItem(text=t, checked=None)
                    with item:
                        for i in range(4):
                            item2 = TreeItem(text=t + str(i), checked=False)
                            if i == 2:
                                with item2:
                                    TreeItem(text='A', title='')
                                    TreeItem(text='B', title='')


m = app.launch(Example, 'xul')
app.run()
